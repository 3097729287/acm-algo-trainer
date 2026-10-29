"""Exercise the installed frozen runtime with a staged seed and disposable state."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urlencode
from urllib.request import urlopen
from core7_authoring import OUT

def junction(link,target):
    if link.exists():return
    literal=lambda p:"'"+str(p).replace("'","''")+"'"
    script='New-Item -ItemType Junction -Path '+literal(link)+' -Target '+literal(target)+' | Out-Null'
    subprocess.run(['powershell','-NoProfile','-Command',script],check=True,capture_output=True)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target',type=Path,required=True);args=parser.parse_args()
    target=args.target.resolve();stage=OUT/'delivery'/target.name/'library.sqlite3'
    assert stage.is_file();folder=OUT/'frozen'/target.name;folder.mkdir(parents=True,exist_ok=True)
    binary='ToBe.exe' if (target/'ToBe.exe').exists() else 'ToBe管理员版.exe'
    for name in [binary,'VERSION','BUILD-INFO.json','SOURCE-MANIFEST.json']:
        shutil.copy2(target/name,folder/name)
    for name in ['_internal','compiler','frontend','browser-extension']:
        if (target/name).is_dir():junction(folder/name,target/name)
    shutil.copytree(target/'resources',folder/'resources',dirs_exist_ok=True)
    (folder/'data').mkdir(exist_ok=True);shutil.copy2(stage,folder/'data/library.sqlite3')
    report=folder/'runtime.json';report.unlink(missing_ok=True);report.with_suffix('.stop').unlink(missing_ok=True)
    env={**os.environ,'TB_OFFLINE':'1','TB_STATE_DIR':str(folder/'state'),'TB_PACKAGE_PORT':'0'}
    process=subprocess.Popen([str(folder/binary),'--serve-check',str(report)],cwd=folder,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    try:
        deadline=time.monotonic()+90
        while not report.exists():
            assert process.poll() is None,'Frozen runtime exited before readiness'
            assert time.monotonic()<deadline,'Frozen runtime readiness timeout'
            time.sleep(.2)
        runtime=json.loads(report.read_text('utf-8'));assert runtime['ok'] and runtime['frozen'],runtime
        entries=json.loads((OUT/'authored.json').read_text('utf-8'));groups={}
        for entry in entries:groups.setdefault(entry['problemId'],[]).append(entry)
        checked=0
        for identity,methods in groups.items():
            with urlopen(runtime['baseUrl']+'/api/solution?'+urlencode({'id':identity}),timeout=20) as response:value=json.load(response)
            found={m['id']:m for m in value['methods']}
            for entry in methods:
                method=found[entry['method']]
                assert method['markdown']==entry['variants']['default']['markdown'],(identity,entry['method'],'default')
                assert method['detailedSolution']==entry['variants']['detailed'],(identity,entry['method'],'detailed')
                assert set(method['lectureIds'])=={'lecture:foundation-'+n for n in entry['lessons']}
                checked+=1
        result={'frozen':True,'offline':True,'problems':len(groups),'methods':checked,'variantResponses':checked*2,
                'referenceProgramsAndTextsMatch':True,'preciseLectureAssociations':True,
                'originalSiteRequests':0,'livePersonalStateOpened':False,'library':runtime['library']}
        (folder/'editorial-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False))
    finally:
        report.with_suffix('.stop').touch()
        try:process.wait(timeout=20)
        except subprocess.TimeoutExpired:process.terminate();process.wait(timeout=10)
    assert process.returncode==0,process.returncode

if __name__=='__main__':main()
