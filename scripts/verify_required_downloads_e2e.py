"""Real native ZIP, disposable account/backend/server and production Workbench.

Requires an explicit new workspace. No release, account, source catalogue or
normal installation is modified. The staged source endpoint is interrupted
once, then physically stopped before the second browser/cache verification.
"""
import argparse
import copy
import hashlib
import http.client
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tracemalloc

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT)]


def start_node(script,*args):
    process=subprocess.Popen(['node',str(ROOT/script),*map(str,args)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    line=process.stdout.readline()
    if not line:
        process.wait(timeout=5)
        raise RuntimeError(process.stderr.read()[-2000:])
    return process,json.loads(line)['endpoint']


def stop_node(process):
    if process is None:return
    if process.poll()is None:process.terminate();process.wait(timeout=10)
    process.stdout.close();process.stderr.close()


def registered_fixture(item,repository_root=ROOT):
    """Read the activated public authoring source, never a personal/live DB."""
    from statement_seed import load_statements,checksum
    from statement_integrity import content_complete,statement_type
    from statement_asset_store import references
    source=Path(repository_root)/'data/library';catalogue=source/'problems.json'
    raw=catalogue.read_bytes();rows=json.loads(raw);identity=item['problemId']
    matches=[row for row in rows if row.get('id')==identity]
    if len(matches)!=1:raise ValueError('Expected one registered public original ID')
    row=matches[0];encoded=row.get('encoded')or{}
    if (encoded.get('id')!=identity or encoded.get('statementRetired',False)is not False
        or encoded.get('catalogHidden',False)is not False or encoded.get('catalogStatementReady')is not True
        or encoded.get('catalogReplayReady')is not False or encoded.get('problemType')!='output-only'
        or encoded.get('url')!=item['sourceUrl']):
        raise ValueError('Registered source must be visible, unretired, statement-ready output-only and not replay-ready')
    selected=[entry['content']for entry in load_statements(source)if entry['problem_id']==identity]
    if len(selected)!=1:raise ValueError('Expected one guarded registered original statement')
    content=selected[0];integrity=content.get('integrity')or{}
    if (content.get('id')!=identity or content.get('url')!=item['sourceUrl']
        or statement_type(content)!='output-only' or content.get('localJudgeSupported')is not False
        or content.get('statementAvailable')is not True or integrity.get('status')!='complete'
        or integrity.get('sourceVerified')is not True or not content_complete(content)):
        raise ValueError('Registered statement must have complete verified output-only integrity')
    markdown_sha=hashlib.sha256(content['markdown'].encode()).hexdigest()
    if markdown_sha not in item['statementSha256']or item['originalDownloadUrl']not in content['markdown']:
        raise ValueError('Registered statement does not match the immutable required-input source binding')
    # This native text has no ordinary inline assets. Refuse to silently omit
    # any future added assets from this intentionally single-task fixture.
    if references(content):raise ValueError('Registered fixture has ordinary asset references that must not be silently dropped')
    return (copy.deepcopy(row['raw']),copy.deepcopy(encoded),None,copy.deepcopy(content)),{
        'mode':'registered-catalogue-source','realRegisteredSourceRead':True,
        'catalogue':'data/library/problems.json','catalogueSha256':hashlib.sha256(raw).hexdigest(),
        'originalId':identity,'registeredRowSha256':checksum(row),'registeredStatementSha256':checksum(content),
        'markdownSha256':markdown_sha,'limits':content.get('limits'),
        'samplePairs':len(content['samples']),'sampleSha256':checksum(content['samples']),
        'guardedLoadStatementsUsed':True,'originalRowAndBodyCopiedWithoutSynthesis':True,
        'catalogueRetirementChanged':False}


def main(workspace,deployment=None,catalogue_source=False):
    workspace=Path(workspace).resolve()
    if workspace.exists():raise ValueError('Choose a new isolated E2E workspace')
    workspace.mkdir(parents=True)
    os.environ['TB_STATE_DIR']=str(workspace/'state')
    from prepare_required_downloads import prepare
    from required_downloads import RequiredDownloads,load_manifest
    from library import LibraryDatabase
    from test_library import record
    from test_training import Judge
    import backend

    manifest=load_manifest();item=next(iter(manifest.values()));identity=item['problemId'];sha=item['sha256']
    source_record=json.loads((ROOT/item['reviewRecord']).read_text('utf8'))
    if catalogue_source:
        row,source_evidence=registered_fixture(item)
        content=row[3]
    else:
        content={'id':identity,'title':'「MCOI-04」Dream SMP','url':item['sourceUrl'],
        'markdown':(ROOT/'content-updates/20261109-P7351-required-inputs/P7351.pending.md').read_text('utf8'),
        'samples':[{'name':'样例 '+str(i),'input':s[0],'output':s[1]}for i,s in enumerate(source_record['nativeSource']['samples'],1)],
        'limits':{'timeMs':5000,'memoryMb':512},
        'problemType':'output-only','localJudgeSupported':False,'statementAvailable':True,'attachments':{},'images':{},
        'integrity':{'status':'incomplete','sourceVerified':True,'issues':['required-download-distribution-pending']}}
        row=list(record(identity,title=content['title']));row[0].update(_url=item['sourceUrl'],_platform='洛谷',_remote=True)
        row[1].update(url=item['sourceUrl'],platform='洛谷',problemType='output-only',catalogReplayReady=False)
        row[3]=content
        source_evidence={'mode':'manual-pending-source','realRegisteredSourceRead':False,'catalogueRetirementChanged':False}
    assert hashlib.sha256(content['markdown'].encode()).hexdigest()in item['statementSha256']
    staged=Path(deployment).resolve(strict=True)if deployment else workspace/'deployment'
    if not deployment:prepare(staged)
    public=LibraryDatabase(workspace/'fixture-public-library.sqlite3')
    public.import_records([tuple(row)],{}, {})
    actual=public.statement(identity)
    assert actual['markdown']==content['markdown']and actual['samples']==content['samples']and actual['limits']==content['limits']
    assert actual['attachments'][item['originalDownloadUrl']]['data']=='/api/required-downloads/'+sha
    account=source=None;server=None;thread=None;judge=Judge();reports=[]
    try:
        account,account_origin=start_node(Path('server/leaderboard/tests/local-server.mjs'))
        metrics=workspace/'source-requests.json'
        source,source_origin=start_node(Path('server/leaderboard/tests/required-download-server.mjs'),staged,metrics,'--interrupt-once')
        server=backend.create_server(training_file=workspace/'fixture-personal.sqlite3',library_file=public.path,
            data_root=workspace/'data',data_file=workspace/'absent.md',integration_auto_start=False,
            judge=judge,account_endpoint=account_origin,backup_dir=workspace/'backups')
        server.required_downloads=RequiredDownloads(cache_root=workspace/'cache',origin=source_origin)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        origin='http://127.0.0.1:'+str(server.server_port)
        def api(route,body=None):
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=30)
            connection.request('GET'if body is None else'POST','/api/'+route,
                body=None if body is None else json.dumps(body).encode(),
                headers={'Content-Type':'application/json','X-TB-Token':server.store.token})
            response=connection.getresponse();raw=response.read();status=response.status;connection.close()
            return status,json.loads(raw)
        assert api('required-downloads/'+sha+'/status')[0]==401,'Downloads retain the real login gate'
        assert api('account/register',{'loginId':'required_fixture','nickname':'输入附件验证夹具','password':'fixture-password'})[0]==200
        status,answer=api('account/login',{'loginId':'required_fixture','password':'fixture-password'})
        assert status==200,answer
        server.training.save_draft(identity,'// durable P7351 fixture draft; do not replace')
        with server.training.lock:
            server.training.connection.execute("""INSERT INTO submissions
              (id,problem_id,mode,code,submitted_at,finished_at,verdict,scope)
              VALUES('required-history-fixture',?,'run','// previous fixture source','2026-11-01T00:00:00Z','2026-11-01T00:00:01Z','RUN_OK','local')""",(identity,))
        # Warm ordinary app metadata before tracing the transfer allocations.
        server.training.problem(identity)
        status,opened=api('problem?id='+identity)
        assert status==200,opened
        environment=dict(os.environ,TB_REQUIRED_FIXTURE_ORIGIN=origin,TB_REQUIRED_FIXTURE_TOKEN=server.store.token)
        tracemalloc.start();started=time.monotonic()
        for phase in ['online-resume','offline-cache']:
            if phase=='offline-cache':
                stop_node(source);source=None
                os.environ['TB_OFFLINE']='1'
            output=workspace/(phase+'.json')
            result=subprocess.run(['node',str(ROOT/'frontend/tests/required-downloads.mjs'),str(output)],cwd=ROOT,
                env=environment,text=True,capture_output=True,timeout=60,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode:raise RuntimeError(result.stdout+'\n'+result.stderr)
            reports.append(json.loads(output.read_text('utf8')))
        _,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        requests=json.loads(metrics.read_text('utf8'))['requests']
        transfers=[r for r in requests if r['method']=='GET']
        assert len(transfers)>=2 and transfers[0]['range'].startswith('bytes=0-')
        assert any(int(r['range'].split('=',1)[1].split('-',1)[0])>0 for r in transfers[1:]),'Interrupted transfer must resume after its durable verified prefix'
        assert all(not r['authorizationForwarded']and not r['cookieForwarded']for r in requests)
        cached=workspace/'cache'/(sha+'.zip')
        with cached.open('rb')as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha
        assert not(workspace/'cache'/(sha+'.part')).exists()
        assert api('required-downloads/'+'a'*64+'/status')[0]==404
        assert api('required-downloads/'+sha+'?url=https://untrusted.example')[0]==404
        assert peak<16*1024*1024,('Archive-size buffer allocation detected',peak)
        report={'schema':1,'artificialAccountsAndHistoryOnly':True,'ordinary32MiBLimitUnchanged':True,
            'sourceFixture':source_evidence,
            'requiredInputMarkedOptional':False,'originalId':identity,'zipBytes':item['bytes'],'sha256':sha,
            'realSourceRouteInterruptedThenResumed':True,'distributionPhysicallyStoppedBeforeOfflineBrowser':True,
            'sourceRequests':requests,'workbenchPhases':reports,'pythonTracedTransferPeakBytes':peak,
            'seconds':round(time.monotonic()-started,3),'completeCacheHasExactOriginalSha256':True,
            'unknownShaAndArbitrarySourceRejected':True,'productionCatalogueRetirementChanged':False,
            'frozen1610Changed':False,'domesticDistributionDeployed':False}
        (workspace/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
        print(json.dumps({'phases':len(reports),'sourceMode':source_evidence['mode'],'zipBytes':item['bytes'],'resumedSourceRequests':len(transfers),'pythonTracedTransferPeakBytes':peak,'productionCatalogueRetirementChanged':False}))
        return report
    finally:
        os.environ.pop('TB_OFFLINE',None)
        if tracemalloc.is_tracing():tracemalloc.stop()
        judge.release.set()
        if server:server.shutdown();server.server_close()
        if thread:thread.join(5)
        stop_node(source);stop_node(account)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workspace',type=Path,required=True);parser.add_argument('--deployment',type=Path)
    parser.add_argument('--catalogue-source',action='store_true',help='Read the activated original row and guarded statement from this ROOT public authoring catalogue; refuse hidden/retired/incomplete sources')
    args=parser.parse_args();main(args.workspace,args.deployment,args.catalogue_source)
