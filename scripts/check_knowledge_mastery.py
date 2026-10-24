"""Compare Python and JavaScript estimates using reproducible, private-free fixtures."""
from pathlib import Path
import json,random,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from knowledge_mastery import estimate,MODEL

rng=random.Random(143)
cases=[[],[dict(id='one',difficulty=None,rated=False,solved=True,weight=1)]]
for count in [1,2,4,5,10,30,100,1000]:
 for _ in range(8):
  cases.append([dict(id=f'p{i}',difficulty=rng.randrange(800,3501,50),rated=True,
                     solved=rng.random()<.65,weight=rng.choice([1,.65,.25,.5])) for i in range(count)])
node=shutil.which('node')
if not node:
 fallback=Path('D:/Software/Other/nodejs/node-v24.18.1-win-x64/node.exe')
 if fallback.is_file():node=str(fallback)
assert node,'Node.js is required for cross-language parity'
module=(ROOT/'frontend/src/lib/knowledgeMastery.js').as_uri()
script=f"import {{combineKnowledgeEvidence}} from {json.dumps(module)};let s='';for await(const c of process.stdin)s+=c;const cases=JSON.parse(s);process.stdout.write(JSON.stringify(cases.map(items=>combineKnowledgeEvidence(items.map(i=>i.id),new Map(items.map(i=>[i.id,i]))))));"
result=json.loads(subprocess.check_output([node,'--input-type=module','-e',script],input=json.dumps(cases).encode(),cwd=ROOT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
for index,(case,actual) in enumerate(zip(cases,result)):
 expected=estimate(case)
 for field in ['value','interval','participated','rated','officialAccepted']:
  assert actual[field]==expected[field],(index,field,actual[field],expected[field])
print(f'MASTERY PARITY OK: {len(cases)} cases; sparse, mixed outcomes and large samples; model v{MODEL["version"]}')
