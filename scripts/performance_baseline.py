"""Offline measurements with bundled public content and disposable private state."""
from contextlib import closing
import argparse
import cProfile
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import statistics
import pstats
import sys
import tempfile
import threading
import time
from urllib.request import build_opener, ProxyHandler, Request

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--code-directory',type=Path,help='Optional original backend files for an identical-environment comparison')
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ToBe-performance-') as directory:
        state=Path(directory)
        os.environ.update(TB_OFFLINE='1',TB_STATE_DIR=str(state),TB_BACKUP_DIR=str(state/'backups'))
        sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
        if args.code_directory:sys.path.insert(0,str(args.code_directory.resolve()))
        from backend import create_server
        from store import Store
        from statement_cleanup import clean_statement_markdown
        target=state/'tb-library.sqlite3'
        shutil.copy2(ROOT/'data/library.sqlite3',target)
        timings=[]
        for _ in range(4):
            start=time.perf_counter();Store(data_file=state/'absent.md',library_file=target)
            timings.append((time.perf_counter()-start)*1000)
        start=time.perf_counter()
        server=create_server(port=0,data_file=state/'absent.md',library_file=target,
                             training_file=state/'tb-personal.sqlite3',integration_state_dir=state,
                             dist_dir=ROOT/'frontend/dist',integration_auto_start=False,require_account=False)
        startup=(time.perf_counter()-start)*1000
        worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        base=f'http://127.0.0.1:{server.server_address[1]}'
        opener=build_opener(ProxyHandler({}))
        def get(route,**headers):
            with opener.open(Request(base+route,headers=headers),timeout=120) as response:
                raw=response.read()
                return gzip.decompress(raw) if response.headers.get('Content-Encoding')=='gzip' else raw
        def measure(function,count=7):
            values=[];result=None
            for _ in range(count):
                start=time.perf_counter();result=function();values.append((time.perf_counter()-start)*1000)
            return {'firstMs':round(values[0],6),'medianMs':round(statistics.median(values),6),'minMs':round(min(values),6)},result
        try:
            catalogue,data=measure(lambda:get('/api/data?compact=1',**{'Accept-Encoding':'gzip'}))
            decoded=json.loads(data)
            identity=next(row['id'] for row in decoded['rows'] if row.get('statementAvailable') and row.get('url','').startswith('https://atcoder.jp/'))
            problem,answer=measure(lambda:server.training.problem(identity,background=True))
            profile=cProfile.Profile();profile.enable()
            for _ in range(3):server.store.data_response_bytes(compact=True);server.training.problem(identity,background=True)
            profile.disable()
            with args.output.with_suffix('.profile.txt').open('w',encoding='utf-8') as stream:pstats.Stats(profile,stream=stream).sort_stats('cumulative').print_stats(25)
            with closing(sqlite3.connect(target)) as db:
                document=db.execute('SELECT content FROM statements ORDER BY length(content) DESC LIMIT 1').fetchone()[0]
            markdown=json.loads(document)['markdown']
            cleaning,_=measure(lambda:clean_statement_markdown(markdown))
            semantic={key:value for key,value in decoded.items() if key not in {'token','today'}}
            result={'ok':True,'offline':True,'personalState':'disposable','rows':len(decoded['rows']),
                    'storeStartupMs':[round(value,3) for value in timings],'serverStartupMs':round(startup,3),
                    'catalogueGzipHttp':catalogue,'bundledStatement':problem,'statementCleanup':cleaning,
                    'catalogueContentSha256':hashlib.sha256(json.dumps(semantic,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                    'statementContentSha256':hashlib.sha256(json.dumps({key:answer.get(key) for key in ['title','markdown','samples','limits','url']},ensure_ascii=False,sort_keys=True).encode()).hexdigest(),
                    'statementIdentity':identity,'catalogueBytes':len(data),'compressionEntries':len(getattr(getattr(server,'catalogue_compression',None),'_items',{})),
                    'python':sys.version.split()[0],
                    'networkFetches':0,'originalSiteNetworkMs':None}
            args.output.parent.mkdir(parents=True,exist_ok=True)
            args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps(result,ensure_ascii=False),flush=True)
        finally:
            server.shutdown();worker.join(10);server.server_close()

if __name__=='__main__':main()
