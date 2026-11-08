"""Validate state invariants and run each example against its unchanged C++ reference."""
import argparse,base64,concurrent.futures,hashlib,itertools,json,re,subprocess
from pathlib import Path
from build_editorial_motion import all_clips
from editorial_motion_assets import ROOT,PREFIX

def states():
 clips=all_clips();models={c.key:[s['facts'] for s in c.steps] for c in clips}
 for s in models['window-deques']:
  if s['phase']!='insert':continue
  a=[1,3,-1,-3,5,3,6,7];i=s['i']
  for name,reverse in [('low',False),('high',True)]:
   indices=s[name];values=[a[j] for j in indices]
   assert indices==sorted(indices) and all(i-2<=j<=i for j in indices)
   assert values==sorted(set(values),reverse=reverse)
   assert values[0]==(max if reverse else min)(a[max(0,i-2):i+1])
 for s in models['previous-window']:
  if s['phase']=='query':assert all(j<s['i'] for j in s['queue'])
 for s in models['bounded-prefix-queue']:
  if s['phase']=='query':
   i,j,p=s['i'],s['j'],s['prefix'];assert j<i and i-j<=3
   assert s['value']==max(p[i]-p[k] for k in range(max(0,i-3),i))
 for s in models['stable-letter-swaps']:assert s['tokens'].index('A₁')<s['tokens'].index('A₂')
 for s in models['weighted-parent-compression']:
  values=[0,4,2,0]
  assert all(s['offset'][i]==values[i]-values[s['parent'][i]] for i in range(4))
 for s in models['fleet-root-and-head']:
  position={ship:i for group in s['groups'] for i,ship in enumerate(group)}
  for group in s['groups']:
   for a,b in itertools.combinations(group,2):assert s['offset'][a]-s['offset'][b]==position[a]-position[b]
 for s in models['signed-weight-layers']:
  if 'weight' in s:assert set(s['new'])=={x+d for x in s['old'] for d in [-s['weight'],0,s['weight']]}
 for s in models['subsequence-descending']:
  if 'j' in s:assert s['source'] not in s['updated']
 assert min(sum(a!=b for a,b in zip('AAB',t)) for t in ['ABB'])==1
 for s in models['bracket-prefix-affine']:
  if s['phase']>=3:assert s['prefix']==[v if i<3 else 4-v if i<=5 else v+2 for i,v in enumerate([0,1,2,3,2,1,2,1])]
 for s in models['successor-wrap-and-compress']:
  occupied=set(s['occupied']);parent=s['parent']
  for i in range(1,8):
   node=i;seen=set()
   while parent[node]!=node:assert node not in seen;seen.add(node);node=parent[node]
   assert node==next((j for j in range(i,7) if j not in occupied),7)
 for s in models['forbidden-triple-state']:
  path=s['path'];assert not any(tuple(path[i:i+3]) in {(1,2,3),(1,3,4)} for i in range(len(path)-2))
 for s in models['invader-history-query']:
  x,y,z=[(0,4,28),(2,9,11),(4,5,26)][s['index']-1]
  assert s['newG']==min(g+(x-a)**2+(y-b)**2 for a,b,g,j in s['history'])-z
 for clip in clips:
  for step in clip.steps:
   source=base64.b64decode(step['image'][len(PREFIX):]).decode()
   assert source.startswith('<svg ') and '<script' not in source and '<foreignObject' not in source
 return clips

def run_references(compiler,work,clips):
 rows={r['problem_id']:r for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf8'))};work.mkdir(parents=True,exist_ok=True)
 def check(clip):
  body=rows[clip.pid]['markdown'];blocks=[m[1] for m in re.finditer(r'^```(?:cpp|cxx)\n(.*?)^```\s*$',body,re.M|re.S) if re.search(r'\bint\s+main\s*\(',m[1])]
  assert blocks,clip.key
  code=blocks[-1];source=work/(clip.key+'.cpp');binary=work/(clip.key+'.exe');source.write_text(code,encoding='utf8')
  compile=subprocess.run([compiler,'-std=c++17','-O1',str(source),'-o',str(binary)],capture_output=True,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  if compile.returncode:return {'id':clip.key,'ok':False,'phase':'compile','error':compile.stderr.decode('utf8','replace')[:700]}
  try:result=subprocess.run([str(binary)],input=clip.input.encode(),capture_output=True,timeout=8,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
  except subprocess.TimeoutExpired:return {'id':clip.key,'ok':False,'phase':'run','error':'Timed out'}
  actual=result.stdout.decode('utf8','replace');ok=result.returncode==0 and actual.split()==clip.expected.split()
  if clip.key=='odd-cycle-reconstruction' and result.returncode==0:
   out=list(map(int,actual.split()));cycle=out[1:];edges={frozenset(e) for e in [(1,2),(1,3),(2,4),(3,5),(4,5)]}
   ok=out[0]==len(cycle) and len(cycle)%2==1 and len(cycle)==len(set(cycle)) and all(frozenset(e) in edges for e in zip(cycle,cycle[1:]+cycle[:1]))
  return {'id':clip.key,'ok':ok,'programSha256':hashlib.sha256(code.encode()).hexdigest(),'actual':actual,'expected':clip.expected}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,clips))
 return results

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compiler',required=True);args=parser.parse_args();clips=states()
 work=ROOT/'.backups/editorial-motion-20261108';results=run_references(args.compiler,work/'references',clips)
 report={'ok':all(r['ok'] for r in results),'cases':len(clips),'frames':sum(len(c.steps) for c in clips),'stateInvariants':True,'results':results}
 (work/'reference-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps({k:v for k,v in report.items() if k!='results'},ensure_ascii=False));print(json.dumps([r for r in results if not r['ok']],ensure_ascii=False))
 return int(not report['ok'])

if __name__=='__main__':raise SystemExit(main())
