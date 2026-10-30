"""Real, flushed pipe interactions followed by independently checked replays.

No hidden input is passed to a competitor process. The checker validates any
legal query strategy, and never regenerates the editorial algorithm's choices.
"""
import hashlib
import itertools
import json
from pathlib import Path
import queue
import random
import shutil
import subprocess
import threading
import time


def pairs01(text):
    zero=answer=0
    for c in text:
        if c=='0':zero+=1
        else:answer+=zero
    return answer


class Conversation:
    def __init__(self,kind,secrets):
        self.kind=kind;self.secrets=secrets;self.at=0;self.queries=0;self.counts=[];self.finished=False

    def start(self):
        if self.kind=='weighing':return str(self.secrets[0]['n'])+'\n'
        return str(len(self.secrets))+'\n'+str(len(self.secrets[0]))+'\n'

    def step(self,line):
        assert not self.finished,'Output after final answer'
        tokens=line.split();assert tokens,'Empty protocol line'
        if self.kind=='weighing':
            secret=self.secrets[0];n=secret['n'];light=set(secret['light'])
            if tokens[0]=='1':
                data=list(map(int,tokens[1:]));p=data[0];assert p>=1 and len(data)>=p+2
                left=data[1:p+1];q=data[p+1];right=data[p+2:]
                assert q>=1 and len(right)==q and p+q<=n
                assert len(set(left+right))==p+q and all(1<=x<=n for x in left+right)
                self.queries+=1;assert self.queries<=secret['cap'],'Query budget exceeded'
                # Legal masses: normal four, both light three; 3+3>4.
                mass_left=sum(3 if x in light else 4 for x in left)
                mass_right=sum(3 if x in light else 4 for x in right)
                return ('<' if mass_left<mass_right else '>' if mass_left>mass_right else '=')+'\n'
            assert tokens[0]=='2' and len(tokens)==3,'Malformed final answer'
            x,y=map(int,tokens[1:]);assert x<y and {x,y}==light,'Incorrect light pair'
            self.counts.append(self.queries);self.finished=True;return None
        secret=self.secrets[self.at];n=len(secret)
        if tokens[0]=='?':
            assert len(tokens)==3;l,r=map(int,tokens[1:]);assert 1<=l<r<=n
            self.queries+=1;assert self.queries<=n,'Query budget exceeded'
            return str(pairs01(secret[l-1:r]))+'\n'
        assert tokens[0]=='!' and len(tokens)==2,'Malformed final answer'
        expected=secret if pairs01(secret)>0 else 'IMPOSSIBLE'
        assert tokens[1]==expected,('Incorrect binary-string answer',secret,tokens[1])
        self.counts.append(self.queries);self.queries=0;self.at+=1
        if self.at==len(self.secrets):self.finished=True;return None
        return str(len(self.secrets[self.at]))+'\n'


def check_transcript(kind,inp,got,other):
    try:
        secrets=json.loads(other);game=Conversation(kind,secrets)
        supplied=iter(inp.split())
        def check_input(message):
            if message:
                for token in message.split():assert next(supplied)==token,'Replay response mismatch'
        check_input(game.start())
        for line in got.splitlines():check_input(game.step(line))
        assert game.finished,'Missing final answer'
        assert next(supplied,None) is None,'Unconsumed replay input'
        return True
    except (AssertionError,ValueError,IndexError,StopIteration,TypeError) as error:
        return False,str(error)


def weighing_transcript(inp,got,other=None):return check_transcript('weighing',inp,got,other)
def kachina_transcript(inp,got,other=None):return check_transcript('kachina',inp,got,other)


def scenario_groups(kind):
    rng=random.Random(75792037)
    if kind=='weighing':
        cases=[{'n':6,'light':[3,6],'cap':13}]
        for n in range(5,16):
            cases.extend({'n':n,'light':list(pair),'cap':13} for pair in itertools.combinations(range(1,n+1),2))
        for n in [16,17,31,32,63,64,127,128,255,256,257,499,500]:
            cap=12 if n&(n-1)==0 else 13
            choices={(1,2),(1,n),(n-1,n),(n//2,n//2+1)}
            choices.update(tuple(sorted(rng.sample(range(1,n+1),2))) for _ in range(25))
            cases.extend({'n':n,'light':list(pair),'cap':cap} for pair in sorted(choices))
        return [[case] for case in cases]
    secrets=['01001','00']
    for n in range(2,11):secrets.extend(''.join(t) for t in itertools.product('01',repeat=n))
    secrets.extend(''.join(rng.choice('01') for _ in range(rng.randrange(2,201))) for _ in range(100))
    groups=[];batch=[];length=0
    for secret in secrets:
        if batch and (length+len(secret)>10000 or len(batch)==1000):groups.append(batch);batch=[];length=0
        batch.append(secret);length+=len(secret)
    if batch:groups.append(batch)
    groups.extend([[secret] for secret in ['01'*5000,'0'*9999+'1','1'+'0'*9999,'1'*10000,'0'*10000]])
    return groups


def run_live(exe,kind,secrets):
    game=Conversation(kind,secrets);messages=[game.start()];lines=[];received=queue.Queue()
    process=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1)
    def reader():
        try:
            for line in process.stdout:received.put(line)
        finally:received.put(None)
    threading.Thread(target=reader,daemon=True).start()
    try:
        process.stdin.write(messages[0]);process.stdin.flush()
        while not game.finished:
            try:line=received.get(timeout=3)
            except queue.Empty:raise AssertionError('No flushed output within three seconds')
            assert line is not None,'Program exited before final answer'
            lines.append(line);reply=game.step(line)
            if reply:messages.append(reply);process.stdin.write(reply);process.stdin.flush()
        process.stdin.close();process.wait(timeout=3)
        assert process.returncode==0,process.stderr.read()
        while True:
            try:extra=received.get(timeout=.05)
            except queue.Empty:break
            if extra is None:break
            assert not extra.strip(),'Output after final answer'
        inp=''.join(messages);expected=json.dumps(secrets,ensure_ascii=False)
        verdict=check_transcript(kind,inp,''.join(lines),expected);assert verdict is True,verdict
        return inp,expected,game.counts
    finally:
        if process.poll() is None:process.kill();process.wait(timeout=3)
        process.stdout.close();process.stderr.close()


def prepare(spec,folder,logs):
    """Compile exact source, run actual judges, return replay edges and proof."""
    started=time.monotonic();exe=logs/'live-competitor.exe'
    result=subprocess.run([shutil.which('g++'),'-std=c++17','-O2',str(folder/'a.cpp'),'-o',str(exe)],capture_output=True,text=True,encoding='utf-8',timeout=90)
    assert result.returncode==0,result.stderr
    edges=[];counts=[]
    for index,secrets in enumerate(scenario_groups(spec.interactive)):
        inp,expected,queries=run_live(exe,spec.interactive,secrets);counts.extend(queries)
        edges.append((f'真实交互转录 {index+1}',inp,expected))
    proof={'kind':spec.interactive,'liveScenarios':len(counts),'liveProcesses':len(edges),
           'maxQueries':max(counts),'programSha256':hashlib.sha256(spec.code.encode()).hexdigest(),
           'judgeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'checkedFlush':True,'checkedQueryBudget':True,'passed':True,'elapsedSeconds':round(time.monotonic()-started,3)}
    (logs/'interactive-live.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return edges,proof
