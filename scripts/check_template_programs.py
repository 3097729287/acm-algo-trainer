"""Compile both C++ editions, then run every original template drill case.

The drill expected results come from independent Python oracles in
template_drills, including structural checkers for nonunique answers.
All generated programs and executables live in a temporary directory.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/common')]
from template_drills import definitions,bundle,check
from template_drill_references import WRAPPERS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--compiler',required=True,type=Path)
    parser.add_argument('--report',type=Path)
    args=parser.parse_args()
    templates={p['id'].split(':')[1]:p for p in json.loads((ROOT/'backend/resources/code-templates.json').read_text(encoding='utf8'))['templates']}
    with tempfile.TemporaryDirectory(prefix='tb-template-programs-') as tmp:
        directory=Path(tmp)
        jobs=[]
        for key,item in templates.items():
            for edition in ('teaching','contest'):
                code=item['code' if edition=='teaching' else 'contestCode']
                example=item['example' if edition=='teaching' else 'contestExample']
                jobs.append((key+'-'+edition,code+'\n'+example,None))
        for task in definitions().values():
            key,var=task['templateKey'],task['variant']
            code=templates[key]['contestCode']+'\nint main(){ios::sync_with_stdio(false);cin.tie(nullptr);'+WRAPPERS[key][var-1]+'\n}\n'
            jobs.append((key+'-drill-'+str(var),code,task['id']))
        def verify(job):
            name,code,identity=job;src=directory/(name+'.cpp');exe=directory/(name+'.exe')
            try:
                src.write_text(code,encoding='utf8')
                compiled=subprocess.run([str(args.compiler),'-std=c++17','-O2','-Wall','-Wextra','-Werror=multichar',str(src),'-o',str(exe)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=90)
                if compiled.returncode:return {'id':name,'passed':False,'error':compiled.stderr[-3000:]}
                cases=bundle(identity)['cases'] if identity else [{'input':''}]
                for index,case in enumerate(cases):
                    ran=subprocess.run([str(exe)],input=case['input'],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=10)
                    if ran.returncode or identity and not check(identity,case['input'],ran.stdout,case['output']):
                        return {'id':name,'passed':False,'case':index,'error':ran.stderr[-1000:],'actual':ran.stdout,'expected':case.get('output')}
                return {'id':name,'passed':True,'cases':len(cases),'drill':bool(identity)}
            except (OSError,subprocess.TimeoutExpired) as error:return {'id':name,'passed':False,'error':str(error)}
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(verify,jobs))
    report={'programs':len(results),'drillCases':sum(p.get('cases',0) for p in results if p.get('drill')),
            'failed':[p for p in results if not p['passed']],'results':results}
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False,indent=2))
    return bool(report['failed'])

if __name__=='__main__':raise SystemExit(main())
