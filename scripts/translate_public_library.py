"""Prepare resumable built-in Chinese statements, never editorials or private data.

API settings stay in their existing protected store. Successful output is tied
to the exact original Markdown/PDF and exported as guarded public seed patches.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from contextlib import closing
import hashlib,json,re,sqlite3,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from statement_cleanup import clean_statement
from statement_seed import checksum
from translation import (TranslationService,DeepSeekProvider,TRANSLATION_FORMAT,
                         bundled_translation,needs_translation,english_prose,translation_chunks)
from translation_config import ProviderSettings
from translation_config import PROVIDERS
from insights import canonical_url

def sha(text):return hashlib.sha256(text.encode()).hexdigest()

def connect(work):
    work.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(work/'translations.sqlite3',timeout=30)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,before_sha TEXT NOT NULL,content TEXT NOT NULL,input TEXT NOT NULL,input_kind TEXT NOT NULL,language TEXT NOT NULL,input_sha TEXT NOT NULL,result TEXT,error TEXT,attempts INTEGER NOT NULL DEFAULT 0)')
    return db

def seed(library,work):
    counts={};counts['unavailable']=0;counts['existingChinese']=0
    with closing(sqlite3.connect(library.as_uri()+'?mode=ro',uri=True)) as source,closing(connect(work)) as db,db:
        tables={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if tables&{'accounts','drafts','submissions','training','documents'}:raise ValueError('Use a public seed, never a personal database')
        for identity,raw in source.execute('SELECT problem_id,content FROM statements'):
            content=json.loads(raw);value=clean_statement(content);existing=value.get('translation') or {}
            if existing.get('markdown') and (existing.get('kind')!='bundled' or bundled_translation(value)):
                db.execute('DELETE FROM jobs WHERE id=? AND result IS NULL',(identity,))
                counts['existingChinese']+=1;continue
            candidate={**value,'translation':None,'translationAvailable':True,'statementAvailable':True}
            text=value.get('markdown') or '';kind='markdown'
            if not needs_translation(candidate) and len(re.findall('[\u3040-\u30ff]',english_prose(text)))<12:
                text=value.get('sourceText') or '';kind='pdf-text'
                if not text or not (needs_translation({**candidate,'markdown':text}) or len(re.findall('[\u3040-\u30ff]',english_prose(text)))>=12):
                    if not value.get('statementAvailable'):counts['unavailable']+=1
                    continue
            language='en' if needs_translation({**candidate,'markdown':text}) else 'ja'
            old=db.execute('SELECT before_sha FROM jobs WHERE id=?',(identity,)).fetchone();before=checksum(content)
            if old and old[0]!=before:raise ValueError('Original changed since checkpoint: '+identity)
            db.execute('INSERT OR IGNORE INTO jobs(id,before_sha,content,input,input_kind,language,input_sha) VALUES(?,?,?,?,?,?,?)',(identity,before,json.dumps(content,ensure_ascii=False),text,kind,language,sha(text)))
        counts.update({state:count for state,count in db.execute("SELECT CASE WHEN result IS NOT NULL THEN 'done' WHEN error IS NOT NULL THEN 'failed' ELSE 'pending' END,COUNT(*) FROM jobs GROUP BY 1")})
    return counts

def bind(content,text,kind,language,translated,provider):
    value={'kind':'bundled','format':TRANSLATION_FORMAT,'markdown':translated,
           'sourceLanguage':language,'targetLanguage':'zh-CN','sourceHash':sha(clean_statement(content).get('markdown') or ''),
           'provider':provider,'inputKind':kind,'notice':'机器翻译仅供理解；原题、公式、代码、样例与资源保留。'}
    if kind=='pdf-text':
        value.update(sourceTextHash=sha(text),sourcePdfSha256=(content.get('statementPdf') or {}).get('sha256') or content.get('sourcePdfSha256'))
    candidate=clean_statement(dict(content,translation=value))
    if not bundled_translation(candidate):raise ValueError('Translation failed completeness or immutable-span validation')
    return value

def run(work,state,workers,limit):
    pending=stats(work)
    if not pending.get('pending',0) and not pending.get('failed',0):return
    settings=ProviderSettings(state);provider=DeepSeekProvider(settings=settings)
    # Fail once on invalid credentials/subscription before scheduling a corpus.
    pilot=provider('Translate into Simplified Chinese: Given an integer, output its value.')
    if not re.search('[\u3400-\u9fff]',pilot):raise ValueError('Provider did not return Chinese')
    stop=threading.Event();local=threading.local()
    def translate(row):
        identity,raw,text,kind,language=row
        if stop.is_set():return identity,None,'cancelled'
        if not hasattr(local,'service'):
            local.service=TranslationService(None,work/'provider-cache',provider=DeepSeekProvider(settings=settings))
        content=json.loads(raw)
        try:
            translated=''.join(local.service._translate_chunk(chunk) for chunk in translation_chunks(text))
            return identity,bind(content,text,kind,language,translated,provider.name),None
        except Exception as error:
            message=str(error)
            if any(code in message for code in ['API Key','余额','额度不足','HTTP 400','拒绝访问']):stop.set()
            return identity,None,message[:300]
    with closing(connect(work)) as db:
        sql='SELECT id,content,input,input_kind,language FROM jobs WHERE result IS NULL ORDER BY attempts,id'+(' LIMIT ?' if limit else '')
        rows=iter(db.execute(sql,(limit,) if limit else ()).fetchall())
        with ThreadPoolExecutor(max_workers=workers) as pool:
            pending={}
            def schedule():
                if stop.is_set():return
                try:row=next(rows)
                except StopIteration:return
                pending[pool.submit(translate,row)]=row[0]
            for _ in range(workers):schedule()
            while pending:
                completed,_=wait(pending,timeout=10,return_when=FIRST_COMPLETED)
                for future in completed:
                    pending.pop(future);identity,value,error=future.result()
                    if error!='cancelled':
                        db.execute('UPDATE jobs SET result=?,error=?,attempts=attempts+1 WHERE id=?',(json.dumps(value,ensure_ascii=False) if value else None,error,identity));db.commit()
                    schedule()
                summary=stats(work)
                (work/'progress.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
                print(json.dumps(summary,ensure_ascii=False),flush=True)
        if stop.is_set():raise RuntimeError('Provider configuration/quota needs correction; successful translations are retained')

def stats(work):
    with closing(connect(work)) as db:
        return {state:count for state,count in db.execute("SELECT CASE WHEN result IS NOT NULL THEN 'done' WHEN error IS NOT NULL THEN 'failed' ELSE 'pending' END,COUNT(*) FROM jobs GROUP BY 1")}

def ingest(work,path):
    if path.stat().st_size>2*1024**2:raise ValueError('Authored batch exceeds its bound')
    packet=json.loads(path.read_text('utf8'))
    if packet.get('schema')!=1 or not isinstance(packet.get('records'),list) or len(packet['records'])>100:raise ValueError('Invalid authored translation batch')
    accepted=0
    with closing(connect(work)) as db:
        for value in packet['records']:
            identity=value['id'];row=db.execute('SELECT content,input,input_kind,language,input_sha,result FROM jobs WHERE id=?',(identity,)).fetchone()
            if not row or row[4]!=value.get('inputSha256') or sha(row[1])!=row[4]:raise ValueError('Authored translation source changed: '+identity)
            try:result=bind(json.loads(row[0]),row[1],row[2],row[3],value['markdown'],'Codex 直接翻译（无外部翻译 API）')
            except ValueError as error:raise ValueError(identity+': '+str(error)) from None
            if row[5]:
                if json.loads(row[5])['markdown']!=value['markdown']:raise ValueError('A different translation already exists: '+identity)
                continue
            db.execute('UPDATE jobs SET result=?,error=NULL,attempts=attempts+1 WHERE id=? AND result IS NULL',(json.dumps(result,ensure_ascii=False),identity));db.commit();accepted+=1
    return {'ingested':accepted,**stats(work)}

def reuse(work,libraries,caches,state=None,shared_files=()):
    accepted=[]
    configured=ProviderSettings(state).status() if state else {}
    with closing(connect(work)) as db:
        jobs={row[0]:row for row in db.execute('SELECT id,content,input,input_kind,language FROM jobs WHERE result IS NULL')}
        def accept(identity,value,provenance):
            if identity not in jobs or not isinstance(value,dict) or not value.get('markdown'):return
            row=jobs[identity];content=json.loads(row[1])
            try:prepared=bind(content,row[2],row[3],row[4],value['markdown'],'已有同源机器译文')
            except ValueError:return
            db.execute('UPDATE jobs SET result=?,error=NULL WHERE id=?',(json.dumps(prepared,ensure_ascii=False),identity))
            jobs.pop(identity);accepted.append({'id':identity,'source':provenance});db.commit()
        for path in libraries:
            if not path.is_file():continue
            with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as source:
                for identity,raw in source.execute('SELECT problem_id,content FROM statements'):
                    if identity not in jobs:continue
                    previous=clean_statement(json.loads(raw));current=clean_statement(json.loads(jobs[identity][1]));value=previous.get('translation') or {}
                    if previous.get('markdown')!=current.get('markdown'):continue
                    if value.get('kind') not in ('bundled','site','shared') and not value.get('format'):continue
                    if jobs[identity][3]=='pdf-text' and (previous.get('sourceText')!=current.get('sourceText') or (previous.get('statementPdf') or {}).get('sha256')!=(current.get('statementPdf') or {}).get('sha256')):continue
                    accept(identity,value,str(path))
        for path in caches:
            if not path.is_file():continue
            with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True)) as source:
                for raw, in source.execute('SELECT value FROM documents'):
                    try:value=json.loads(raw)
                    except (ValueError,TypeError):continue
                    if not isinstance(value,dict) or value.get('id') not in jobs or not value.get('format'):continue
                    identity=value['id'];row=jobs[identity];content=json.loads(row[1]);original=clean_statement(content).get('markdown') or '';format=value['format'];provider=value.get('provider','')
                    hashes={sha(format+'\n'+original),sha(original)}
                    choices=[(None,None,None)]
                    for code,spec in PROVIDERS.items():
                        if code=='custom':continue
                        if provider.startswith(spec['name']+' · '):choices.append((code,provider.split(' · ',1)[1],spec['baseUrl']))
                    if provider.startswith('自定义 OpenAI 兼容 API · ') and configured.get('provider')=='custom':choices.append(('custom',provider.split(' · ',1)[1],configured['baseUrl']))
                    for code,model,base in choices:hashes.add(sha('\n'.join([format,identity,content.get('url',''),original,provider,str(code),str(model),str(base)])))
                    if value.get('sourceHash') in hashes:accept(identity,value,str(path))
        for path in shared_files:
            for value in json.loads(path.read_text('utf8')):
                if value.get('target_language')!='zh-CN' or value.get('source_format')!=TRANSLATION_FORMAT:continue
                for identity,row in list(jobs.items()):
                    content=clean_statement(json.loads(row[1]));original=content.get('markdown') or ''
                    if row[3]!='markdown' or canonical_url(content.get('url',''))!=canonical_url(value.get('source_url','')):continue
                    if value.get('source_hash')!=sha(TRANSLATION_FORMAT+'\n'+original):continue
                    accept(identity,{'markdown':value.get('markdown')},str(path))
    (work/'reuse-audit.json').write_text(json.dumps({'reused':len(accepted),'records':accepted},ensure_ascii=False,indent=2),encoding='utf8')
    return {'reused':len(accepted),**stats(work)}

def export(work,destination):
    destination.mkdir(parents=True,exist_ok=True)
    with closing(connect(work)) as db:
        rows=db.execute('SELECT id,before_sha,content,input,input_kind,language,result FROM jobs WHERE result IS NOT NULL ORDER BY id').fetchall()
        for index in range(0,len(rows),100):
            packet={'schema':1,'statements':[]}
            for identity,before,raw,text,kind,language,result in rows[index:index+100]:
                content=json.loads(raw);value=json.loads(result)
                bind(content,text,kind,language,value['markdown'],value['provider'])
                packet['statements'].append({'problem_id':identity,'beforeSha256':before,'content':dict(content,translation=value)})
            data=json.dumps(packet,ensure_ascii=False,indent=2)+'\n';target=destination/f'zz-chinese-corpus-{sha(data)[:20]}.json'
            if target.exists() and target.read_text('utf8')!=data:raise ValueError('Export destination changed; use a fresh patch directory')
            target.write_text(data,encoding='utf8',newline='\n')
    return {'exported':len(rows),'directory':str(destination)}

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['inventory','reuse','run','stats','ingest','export']);p.add_argument('--library',type=Path);p.add_argument('--work',type=Path,required=True);p.add_argument('--settings-state',type=Path);p.add_argument('--workers',type=int,default=8,choices=range(1,17));p.add_argument('--limit',type=int);p.add_argument('--output',type=Path);p.add_argument('--input-file',type=Path);p.add_argument('--reuse-library',type=Path,action='append',default=[]);p.add_argument('--reuse-cache',type=Path,action='append',default=[]);p.add_argument('--reuse-shared',type=Path,action='append',default=[]);a=p.parse_args()
    if a.action=='inventory':result=seed(a.library.resolve(),a.work)
    elif a.action=='reuse':result=reuse(a.work,a.reuse_library,a.reuse_cache,a.settings_state,a.reuse_shared)
    elif a.action=='run':
        if not a.settings_state:p.error('--settings-state is required for run')
        run(a.work,a.settings_state,a.workers,a.limit);result=stats(a.work)
    elif a.action=='export':result=export(a.work,a.output)
    elif a.action=='ingest':
        if not a.input_file:p.error('--input-file is required for ingest')
        result=ingest(a.work,a.input_file)
    else:result=stats(a.work)
    print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
