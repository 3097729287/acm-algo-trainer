"""Package and validate a local frontend/template update against installed runtimes.

The public seed and every personal database stay in place during application.
Fresh/upgrade probes use copied databases and the real frozen desktop programs.
"""
import argparse
import base64
from contextlib import closing
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
from urllib.request import build_opener,ProxyHandler
import zipfile

ROOT=Path(__file__).resolve().parents[1]
NO_WINDOW=getattr(subprocess,'CREATE_NO_WINDOW',0)
OPENER=build_opener(ProxyHandler({}))

def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf8').strip()
def files(root):return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file()}
def backup_db(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as src,closing(sqlite3.connect(target)) as dest:
        src.backup(dest);assert dest.execute('PRAGMA quick_check').fetchone()[0]=='ok'
def state_files(app):
    for relative in ['state','admin-workspace/state']:
        folder=app/relative
        if folder.is_dir():
            for path in folder.glob('*.sqlite3'):yield path
def snapshot(app,target):
    paths=[]
    for path in state_files(app):
        relative=path.relative_to(app);backup_db(path,target/relative);paths.append(relative.as_posix())
    return paths
def table_digests(path,exclude_catalog_cache=False):
    result={}
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        for (name,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
            quoted='"'+name.replace('"','""')+'"'
            query='SELECT * FROM '+quoted
            if exclude_catalog_cache and name=='documents':
                cursor=db.execute(query+' WHERE key<>?',('tb-catalog-cache.json',))
            else:cursor=db.execute(query)
            rows=sorted(repr(tuple(row)) for row in cursor)
            result[name]=dict(rows=len(rows),sha256=hashlib.sha256('\n'.join(rows).encode()).hexdigest())
    return result
def ps(script):
    encoded=base64.b64encode(script.encode('utf-16le')).decode('ascii')
    return subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded],creationflags=NO_WINDOW).decode('utf-8-sig').strip()
def junction(target,source):
    quote=lambda p:"'"+str(p).replace("'","''")+"'"
    ps('New-Item -ItemType Junction -Path '+quote(target)+' -Target '+quote(source)+' | Out-Null')
def request(url):
    with OPENER.open(url,timeout=35) as response:return json.load(response)
def baseline(app):
    return dict(buildInfo=sha(app/'BUILD-INFO.json'),seed=sha(app/'data/library.sqlite3'),
                frontend=files(app/'frontend/dist'),templates=sha(app/'resources/code-templates.json'))

def prepare(installation,stage):
    assert not git('status','--porcelain'),'Commit the exact source before packaging'
    assert not (stage/'package.json').exists(),'Use a fresh stage'
    commit=git('rev-parse','HEAD');baseline_info={};packages={}
    for edition,folder,exe in [('user','程序','ToBe.exe'),('admin','管理员程序','ToBe管理员版.exe')]:
        app=installation/folder;package=stage/('release' if edition=='user' else 'private-admin')/folder
        package.mkdir(parents=True);baseline_info[edition]=baseline(app)
        for path in app.iterdir():
            if path.is_file() and not path.name.startswith('unins'):shutil.copy2(path,package/path.name)
        for name in ['_internal','compiler']:
            if (app/name).is_dir():junction(package/name,app/name)
        shutil.copytree(app/'resources',package/'resources')
        shutil.copytree(ROOT/'frontend/dist',package/'frontend/dist')
        (package/'data').mkdir();shutil.copy2(app/'data/library.sqlite3',package/'data/library.sqlite3')
        for name in ['code-templates.json','algorithm-learning.json']:shutil.copy2(ROOT/'backend/resources'/name,package/'resources'/name)
        info=read(app/'BUILD-INFO.json');info.update(commit=commit,sourceCommit=commit,sourceBranch=git('branch','--show-current'),frontendSourceCommit=commit,templateSourceCommit=commit,
            learningOrganizationSourceCommit=commit,localRevision='algorithm-learning-20261030',sourcePushed=False,
            status='local frontend/template teaching update; existing executable and public content retained; unpublished',
            algorithmLearning=dict(templates=28,topics=8,movedLectures=15),frontendSourceBranch=git('branch','--show-current'))
        info['frontendBuildSha256']=hashlib.sha256(json.dumps(files(package/'frontend/dist'),sort_keys=True,separators=(',',':')).encode()).hexdigest()
        manifest=read(app/'SOURCE-MANIFEST.json')
        manifest={k:v for k,v in manifest.items() if not k.startswith('frontend/dist/')}
        manifest.update({'frontend/dist/'+k:v for k,v in files(package/'frontend/dist').items()})
        manifest.update({'frontend/src/'+k:v for k,v in files(ROOT/'frontend/src').items()})
        manifest.update({'backend/resources/'+name:sha(ROOT/'backend/resources'/name) for name in ['code-templates.json','algorithm-learning.json']})
        write(package/'SOURCE-MANIFEST.json',manifest);info['sourceManifestSha256']=sha(package/'SOURCE-MANIFEST.json')
        write(package/'BUILD-INFO.json',info)
        for name in ['BUILD-INFO.json','SOURCE-MANIFEST.json']:shutil.copy2(package/name,package/'resources'/name)
        packages[edition]=dict(path=str(package),executable=exe,original=str(app))
    archive=stage/'algorithm-learning.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in (ROOT/'frontend/dist').rglob('*'):
            if p.is_file():z.write(p,'frontend/dist/'+p.relative_to(ROOT/'frontend/dist').as_posix())
        for name in ['code-templates.json','algorithm-learning.json']:z.write(ROOT/'backend/resources'/name,'resources/'+name)
    write(stage/'package.json',dict(commit=commit,baseline=baseline_info,packages=packages,payloadSha256=sha(archive),installation=str(installation),publicRelease=False))
    print(json.dumps(dict(prepared=True,commit=commit,templates=28,topics=8)))

def validate(stage):
    package=read(stage/'package.json');assert git('rev-parse','HEAD')==package['commit']
    reports=[]
    for edition,p in package['packages'].items():
        app=Path(p['path']);original=Path(p['original'])
        for mode in ['fresh','upgrade']:
            folder=stage/'validation'/f'{edition}-{mode}';state=folder/'state';folder.mkdir(parents=True)
            before={}
            if mode=='upgrade':
                for db in state_files(original):
                    # The real runtime's state override has a flat active state.
                    if db.parent!=original/'state':continue
                    backup_db(db,state/db.name)
                    if 'library' not in db.name:before[db.name]=table_digests(state/db.name,db.name=='tb-documents.sqlite3')
            output=folder/'probe.json'
            env=dict(os.environ,TB_STATE_DIR=str(state),TB_OFFLINE='1',TB_BACKUP_DIR=str(folder/'backups'),TB_PACKAGE_PORT='0')
            with (folder/'stdout.log').open('wb') as out,(folder/'stderr.log').open('wb') as err:
                process=subprocess.Popen([str(app/p['executable']),'--serve-check',str(output)],cwd=app,env=env,stdout=out,stderr=err,creationflags=NO_WINDOW)
                try:
                    deadline=time.monotonic()+80
                    while not output.exists() and process.poll() is None and time.monotonic()<deadline:time.sleep(.2)
                    assert output.exists(),f'Frozen probe failed: {folder}'
                    result=read(output);assert result['ok'] and result['frozen'],result
                    base=result['baseUrl'];catalog=request(base+'/api/templates')['templates']
                    assert len([x for x in catalog if x['builtin']])==28
                    basis=next(x for x in catalog if x['id']=='builtin:linear-basis');assert 'kth' in basis['code'] and basis['explanation']
                    with OPENER.open(base+'/',timeout=20) as response:html=response.read().decode()
                    assert 'assets/index-' in html
                    for name,expected in before.items():assert table_digests(state/name,name=='tb-documents.sqlite3')==expected,(edition,mode,name)
                    reports.append(dict(edition=edition,mode=mode,ok=True,templates=28,publicSeedUnchanged=sha(app/'data/library.sqlite3')==package['baseline'][edition]['seed'],personalTablesUnchanged=True,derivedCatalogCacheMayRefresh=True,baseUrl=base,publicLibrary=result['library']))
                finally:
                    output.with_suffix('.stop').write_text('stop',encoding='ascii')
                    try:process.wait(timeout=30)
                    except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
    write(stage/'validation.json',dict(ok=True,commit=package['commit'],reports=reports,officialSubmissions=0));print(json.dumps(dict(validated=True,modes=len(reports))))

def apply(stage):
    package=read(stage/'package.json');assert read(stage/'validation.json')['ok']
    assert not git('status','--porcelain') and git('rev-parse','HEAD')==package['commit']
    for edition,p in package['packages'].items():assert baseline(Path(p['original']))==package['baseline'][edition],f'{edition} installation changed; repackage against the new baseline'
    # Only this installation is closed, through its normal window-close handler.
    project=Path(package['installation']).resolve();assert project==ROOT.parents[1]/'版本/最新版'
    recovery=stage.parent/'recovery';recovery.mkdir(exist_ok=True)
    for edition,p in package['packages'].items():snapshot(Path(p['original']),recovery/'before-close'/edition)
    paths=[str(Path(p['original'])/p['executable']) for p in package['packages'].values()]
    script="[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new($false); $targets=@("+','.join("'"+s.replace("'","''")+"'" for s in paths)+"); $found=Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -in $targets}; foreach($entry in $found){$process=Get-Process -Id $entry.ProcessId; if(-not $process.CloseMainWindow()){throw 'Normal close request failed'}}"
    ps(script)
    for _ in range(150):
        count=ps("$targets=@("+','.join("'"+s.replace("'","''")+"'" for s in paths)+"); @(Get-CimInstance Win32_Process | Where-Object {$_.ExecutablePath -in $targets}).Count")
        if count=='0':break
        time.sleep(.2)
    else:raise RuntimeError('Application deferred normal close; installation left unchanged')
    rows={};state_manifest={}
    for edition,p in package['packages'].items():
        app=Path(p['original']);dbs=snapshot(app,recovery/'final'/edition);state_manifest[edition]=dbs
        rows[edition]={relative:table_digests(app/relative) for relative in dbs}
        assert baseline(app)==package['baseline'][edition],'Another installer changed the baseline during close'
    changes=[]
    for edition,p in package['packages'].items():
        app=Path(p['original']);payload=Path(p['path']);old_frontend=app/'frontend/dist';saved=recovery/'program-before'/edition
        saved.mkdir(parents=True);assert not (saved/'dist').exists()
        assert old_frontend.resolve().is_relative_to(project)
        assert saved.resolve().is_relative_to(ROOT/'.backups')
        pending=app/'frontend/dist.algorithm-learning-next';assert not pending.exists()
        shutil.copytree(payload/'frontend/dist',pending)
        assert files(pending)==files(payload/'frontend/dist')
        # Rename stays in the same volume and keeps a complete rollback frontend.
        old_frontend.rename(saved/'dist');pending.rename(old_frontend)
        for name in ['resources/code-templates.json','resources/algorithm-learning.json','BUILD-INFO.json','SOURCE-MANIFEST.json','resources/BUILD-INFO.json','resources/SOURCE-MANIFEST.json']:
            target=app/name
            if target.exists():(saved/name).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(target,saved/name)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(payload/name,target)
            assert sha(target)==sha(payload/name)
        assert sha(app/'data/library.sqlite3')==package['baseline'][edition]['seed']
        assert files(old_frontend)==files(payload/'frontend/dist')
        for relative,expected in rows[edition].items():assert table_digests(app/relative)==expected,(edition,relative)
        changes.append(dict(edition=edition,frontendFiles=len(files(old_frontend)),publicSeedUnchanged=True,personalTablesUnchanged=True))
    write(recovery/'state-manifest.json',state_manifest)
    write(stage.parent/'installed.json',dict(ok=True,commit=package['commit'],changes=changes,recovery=str(recovery),onlineDatabases=sum(map(len,state_manifest.values())),sourcePushed=False))
    user=Path(package['packages']['user']['original'])
    subprocess.Popen([str(user/'ToBe.exe')],cwd=user,env={k:v for k,v in os.environ.items() if not k.startswith('TB_')},creationflags=NO_WINDOW)
    print(json.dumps(dict(installed=True,commit=package['commit'],onlineDatabases=sum(map(len,state_manifest.values())))))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','validate','apply']);parser.add_argument('--installation',type=Path);parser.add_argument('--stage',type=Path,required=True);args=parser.parse_args()
    stage=args.stage.resolve()
    assert stage.is_relative_to(ROOT/'.backups'),'Keep private verification in the local backup workspace'
    if args.action=='prepare':prepare(args.installation.resolve(),stage)
    elif args.action=='validate':validate(stage)
    else:apply(stage)
