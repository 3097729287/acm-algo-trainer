"""Large, structurally known public cases; not a substitute for judge acceptance."""
import hashlib,json,random,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'.backups/core7-complete-20261108';records=[]
def run(pid,label,inp,expected=None,timeout=30):
    raw=inp.encode();started=time.perf_counter();result=subprocess.run([str(OUT/'programs'/pid/'main.exe')],input=raw,capture_output=True,timeout=timeout);elapsed=time.perf_counter()-started
    passed=result.returncode==0 and (expected is None or result.stdout.split()==expected.encode().split())
    record={'pid':pid,'case':label,'seconds':round(elapsed,3),'inputSha256':hashlib.sha256(raw).hexdigest(),'outputSha256':hashlib.sha256(result.stdout).hexdigest(),'inputBytes':len(raw),'outputBytes':len(result.stdout),'expectedCompared':expected is not None,'passed':passed};records.append(record);print(json.dumps(record),flush=True)
    (OUT/'performance.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
    assert passed,pid

n=1000000;run('P13790','million-char shifted palindrome','abbb'+'ab'*((n-4)//2),str(n-2))
n=3000000;k=1000000000;length=n*k;run('P11749','three-million-char periodic palindrome',f'1\n{n} {k}\n'+'a'*n,str(length*(length+1)//2%998244353))
n=3000000;run('P16943','three-million-vertex star',str(n)+'\n'+'1 '*(n-1),' '.join(str(v-2) for v in range(2,n+1)))
run('P3383','hundred-million sieve','100000000 1\n1','2')
n=30000;m=30000;rng=random.Random(20261108);dogs=['0 2',f'{n-1} 2']+[f'{2*rng.randrange(n//2)} {2*rng.randrange(1,87)}' for _ in range(m-2)];run('P3645','unreachable odd target with many small jump layers',f'{n} {m}\n'+'\n'.join(dogs),'-1')
n=200000;q=200000;x=166320;answer=str(pow(x,n,1000000007));run('P6217','dense prime-power position queries',f'{n} {q}\n'+(str(x)+' ')*n+'\n'+f'1 {n} {x}\n'*q,'\n'.join([answer]*q))
