"""Run the unchanged DSH verifier, then compare both article programs with disk."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from core7_authoring import ROOT, OUT, CONTENT, load_all, source_hash, statement_path
from core7_cases import cases_for


def validate_one(spec):
    folder = CONTENT / spec.pid / spec.key
    logs = OUT / 'verification' / spec.pid / spec.key
    logs.mkdir(parents=True, exist_ok=True)
    statement = json.loads(statement_path(spec.pid).read_text('utf-8'))
    samples = [('A '+s.get('name',str(i)), s['input'], s['output']) for i,s in enumerate(statement.get('samples',[]))]
    edges = cases_for(spec.pid) + [(f'手工边界 {i+1}',x,y) for i,(x,y) in enumerate(spec.cases)]
    (folder/'samples.py').write_text('SAMPLES = '+repr(samples)+'\n', encoding='utf-8')
    (folder/'cases.json').write_text(json.dumps(edges,ensure_ascii=False,indent=2)+'\n', encoding='utf-8')
    probe = '''from pathlib import Path
import json, sys
sys.path.insert(0, str(Path.home()/'.dsh/tools'))
from verify import main
HERE = Path(__file__).resolve().parent
EDGES = json.loads((HERE/'cases.json').read_text('utf-8'))
if __name__ == '__main__':
    main(solution=str(HERE/'a.cpp'), edges=EDGES, letter='A', samples_file=str(HERE/'samples.py'),
         log_file=str(HERE/'verify.log'))
    # This corpus uses precomputed independent oracles as edges. Unconfigured
    # brute/debug/timing modes stay explicitly unverified in the original log.
    report = (HERE/'verify.log').read_text('utf-8')
    assert '编译：通过' in report
    assert '官方样例：SAMPLE_COUNT 组全过' in report
    if EDGES:
        assert '边界用例：EDGE_COUNT 条全过' in report
'''
    probe=probe.replace('SAMPLE_COUNT',str(len(samples))).replace('EDGE_COUNT',str(len(edges)))
    if spec.checker:
        probe=probe.replace('from verify import main',f'from verify import main\nsys.path.insert(0, {str(ROOT/"scripts")!r})\nfrom core7_checkers import {spec.checker}')
        probe=probe.replace("log_file=str(HERE/'verify.log'))",f"log_file=str(HERE/'verify.log'), checker={spec.checker})")
    (folder/'verify_a.py').write_text(probe, encoding='utf-8')
    env = {**os.environ, 'PYTHONIOENCODING':'utf-8', 'TB_OFFLINE':'1', 'TB_STATE_DIR':str(OUT/'isolated-state')}
    started=time.monotonic()
    result=subprocess.run([sys.executable,str(folder/'verify_a.py')],capture_output=True,text=True,encoding='utf-8',env=env,timeout=240)
    (logs/'verify.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    successful_log=('编译：通过' in result.stdout and f'官方样例：{len(samples)} 组全过' in result.stdout
                    and (not edges or f'边界用例：{len(edges)} 条全过' in result.stdout))
    if result.returncode or not successful_log:
        return {'pid':spec.pid,'method':spec.key,'passed':False,'phase':'program','log':str(logs/'verify.log'),'tail':result.stdout[-2200:]+result.stderr[-1000:]}
    if spec.exact:
        # The old verifier collapses all whitespace. Check actual line structure
        # independently for pictures and fixed decimal output.
        for name,inp,expected in samples+edges:
            ran=subprocess.run([str(folder/'a.exe')],input=inp,capture_output=True,text=True,encoding='utf-8',timeout=4)
            norm=lambda s:'\n'.join(line.rstrip() for line in s.replace('\r\n','\n').rstrip('\n').split('\n'))
            if ran.returncode or norm(ran.stdout)!=norm(expected):
                return {'pid':spec.pid,'method':spec.key,'passed':False,'phase':'exact-output','case':name,'input':inp,'expected':expected,'actual':ran.stdout}
    records=[]
    for name in ['default','detailed']:
        path=folder/(name+'.md')
        data=path.read_text('utf-8').split('\n## 实测记录')[0]
        data+='\n## 实测记录\n\n'
        data+=f'本地 C++17 编译、{len(samples)} 组原站样例与 {len(edges)} 组独立边界/小域校验通过。\n'
        data+='正文参考程序与源码逐字核对；没有向原站提交。\n'
        path.write_text(data,encoding='utf-8')
        compare=subprocess.run([sys.executable,str(Path.home()/'.dsh/tools/md_full.py'),str(path),'A'],capture_output=True,text=True,encoding='utf-8',env=env,timeout=90)
        (logs/(name+'-md-full.log')).write_text(compare.stdout+compare.stderr,encoding='utf-8')
        if compare.returncode:
            return {'pid':spec.pid,'method':spec.key,'passed':False,'phase':'md-full','tail':compare.stdout[-2000:]+compare.stderr[-1000:]}
        records.append(source_hash(data))
    return {'pid':spec.pid,'method':spec.key,'passed':True,'samples':len(samples),'independentCases':len(edges),
            'programSha256':source_hash(spec.code),'articleFileSha256':records,'elapsedSeconds':round(time.monotonic()-started,3)}


def main():
    selected=load_all()
    previous={(r['pid'],r['method']):r for r in json.loads((OUT/'verification.json').read_text('utf-8'))} if (OUT/'verification.json').exists() else {}
    report=[];run=[]
    for spec in selected:
        old=previous.get((spec.pid,spec.key))
        logpath=OUT/'verification'/spec.pid/spec.key/'verify.log'
        log=logpath.read_text('utf-8') if logpath.exists() else ''
        audited_log=bool(old and '编译：通过' in log and f'官方样例：{old.get("samples",0)} 组全过' in log
                         and (not old.get('independentCases') or f'边界用例：{old["independentCases"]} 条全过' in log))
        if '--only-new' in sys.argv and old and old['passed'] and old['programSha256']==source_hash(spec.code) and audited_log:
            report.append(old)
        else:run.append(spec)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for future in as_completed([pool.submit(validate_one,s) for s in run]):
            result=future.result();report.append(result)
            print(json.dumps(result,ensure_ascii=False),flush=True)
    report.sort(key=lambda v:(v['pid'],v['method']))
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return int(any(not r['passed'] for r in report))


if __name__=='__main__':
    raise SystemExit(main())
