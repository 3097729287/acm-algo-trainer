"""Original CF1687B protocol: independent forests, flushed live I/O and replay."""
import hashlib
import heapq
import itertools
import json
from pathlib import Path
import queue
import random
import shutil
import subprocess
import threading
import time


def forest_value(n,edges,selection,maximize):
    chosen=[e for e,bit in zip(edges,selection) if bit=='1']
    if n<=5 and len(chosen)<=8:
        adjacency=[[] for _ in range(n)]
        for u,v,w in chosen:adjacency[u].append(v);adjacency[v].append(u)
        seen=set();components=0
        for root in range(n):
            if root in seen:continue
            components+=1;todo=[root];seen.add(root)
            for u in todo:
                for v in adjacency[u]:
                    if v not in seen:seen.add(v);todo.append(v)
        rank=n-components;answer=None
        for ids in itertools.combinations(range(len(chosen)),rank):
            parent=list(range(n));total=0
            def root(u):
                while parent[u]!=u:u=parent[u]
                return u
            for i in ids:
                u,v,w=chosen[i];u,v=root(u),root(v)
                if u==v:break
                parent[u]=v;total+=w
            else:
                if answer is None or (total>answer if maximize else total<answer):answer=total
        assert answer is not None
        return answer
    # Large graphs use Prim on all original components, not the query strategy.
    graph=[[] for _ in range(n)]
    for u,v,w in chosen:graph[u].append((v,w));graph[v].append((u,w))
    seen=[False]*n;total=0;sign=-1 if maximize else 1
    for start in range(n):
        if seen[start]:continue
        pending=[(0,start)]
        while pending:
            weight,u=heapq.heappop(pending)
            if seen[u]:continue
            seen[u]=True;total+=sign*weight
            for v,w in graph[u]:
                if not seen[v]:heapq.heappush(pending,(sign*w,v))
    return total


class Conversation:
    def __init__(self,secret):
        self.secret=secret;self.n=secret['n'];self.edges=secret['edges'];self.m=len(self.edges)
        self.queries=0;self.finished=False;self.cache={}
        self.answer=forest_value(self.n,self.edges,'1'*self.m,False)
    def start(self):return f'{self.n} {self.m}\n'
    def step(self,line):
        assert not self.finished,'Output after final answer'
        tokens=line.split();assert len(tokens)==2,'Malformed protocol line'
        if tokens[0]=='?':
            mask=tokens[1];assert len(mask)==self.m and set(mask)<={'0','1'},'Malformed edge selection'
            self.queries+=1;assert self.queries<=2*self.m,'Query budget exceeded'
            if mask not in self.cache:self.cache[mask]=forest_value(self.n,self.edges,mask,True)
            return str(self.cache[mask])+'\n'
        assert tokens[0]=='!' and int(tokens[1])==self.answer,'Incorrect minimum spanning forest'
        self.finished=True;return None


def railway_transcript(inp,got,other=None):
    try:
        game=Conversation(json.loads(other));supplied=iter(inp.split())
        def consume(reply):
            for token in (reply or '').split():assert next(supplied)==token,'Replay reply differs from secret graph'
        consume(game.start())
        for line in got.splitlines():
            if line.strip():consume(game.step(line))
        assert game.finished and next(supplied,None) is None,'Missing answer or unconsumed replay input'
        return True
    except (AssertionError,ValueError,TypeError,KeyError,IndexError,StopIteration) as error:return False,str(error)


def scenarios():
    for n in [2,3,4]:
        pairs=list(itertools.combinations(range(n),2))
        for labels in itertools.product(range(3),repeat=len(pairs)):
            edges=[(u,v,w) for (u,v),w in zip(pairs,labels) if w]
            if edges:yield {'n':n,'edges':edges}
    rng=random.Random(168720261030)
    for _ in range(110):
        n=rng.randint(2,18);edges=[]
        for i in range(rng.randint(1,40)):
            u,v=rng.sample(range(n),2);edges.append((u,v,rng.randint(1,1000000)))
        yield {'n':n,'edges':edges}
    yield {'n':5,'edges':[(0,1,1),(1,2,2),(0,2,3),(3,4,4)]}
    for kind in range(6):
        n=200 if kind!=5 else 2;edges=[]
        if kind==0:edges=[(u,u+1,1000000-u) for u in range(n-1)]
        for i in range(500-len(edges)):
            domain=range(100) if kind==1 else range(n)
            u,v=rng.sample(list(domain),2)
            edges.append((u,v,1 if kind==2 else 1000000 if kind==5 else rng.randint(1,1000000)))
        yield {'n':n,'edges':edges}


def process_io(exe):
    process=subprocess.Popen([str(exe)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding='utf8',bufsize=1,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    received=queue.Queue()
    def reader():
        try:
            for line in process.stdout:received.put(line)
        finally:received.put(None)
    thread=threading.Thread(target=reader,daemon=True);thread.start()
    return process,received,thread


def close_process(process,thread):
    if process.poll() is None:process.kill();process.wait(timeout=3)
    if not process.stdin.closed:process.stdin.close()
    thread.join(3);process.stdout.close();process.stderr.close()


def run_live(exe,secret):
    game=Conversation(secret);process,received,thread=process_io(exe);messages=[game.start()];lines=[]
    try:
        process.stdin.write(messages[0]);process.stdin.flush()
        while not game.finished:
            try:line=received.get(timeout=3)
            except queue.Empty:raise AssertionError('No flushed query within three seconds')
            assert line is not None,'Competitor exited before its answer';lines.append(line)
            if not line.strip():continue
            reply=game.step(line)
            if reply:messages.append(reply);process.stdin.write(reply);process.stdin.flush()
        process.stdin.close();process.wait(timeout=3);assert process.returncode==0,process.stderr.read()
        while True:
            extra=received.get(timeout=3)
            if extra is None:break
            assert not extra.strip(),'Output after the final answer'
        inp=''.join(messages);expected=json.dumps(secret,separators=(',',':'))
        assert railway_transcript(inp,''.join(lines),expected) is True
        return inp,expected,game.queries
    finally:close_process(process,thread)


def check_rejection_exit(exe,reply):
    process,received,thread=process_io(exe)
    try:
        process.stdin.write('2 1\n');process.stdin.flush();line=received.get(timeout=3)
        assert line and line.split()==['?','1']
        if reply is None:process.stdin.close()
        else:process.stdin.write(reply);process.stdin.flush()
        process.wait(timeout=3);assert process.returncode==0
        while True:
            line=received.get(timeout=3)
            if line is None:break
            assert not line.strip(),'Output after rejected/closed interaction'
    finally:close_process(process,thread)


def selftest():
    secret=json.dumps({'n':3,'edges':[(0,1,1),(1,2,2),(0,2,3)]})
    assert railway_transcript('3 3\n5\n','? 111\n! 3\n',secret) is True
    for inp,output in [('3 3\n','! 4\n'),('3 3\n','? 11\n! 3\n'),('3 3\n'+'0\n'*7,'? 000\n'*7+'! 3\n'),('3 3\n5\n5\n','? 111\n! 3\n')]:
        assert railway_transcript(inp,output,secret)[0] is False


def prepare(spec,folder,logs):
    selftest();started=time.monotonic();exe=logs/'live-competitor.exe'
    compiled=subprocess.run([shutil.which('g++'),'-std=c++17','-O2',str(folder/'a.cpp'),'-o',str(exe)],capture_output=True,text=True,encoding='utf8',timeout=90)
    assert compiled.returncode==0,compiled.stderr
    edges=[];counts=[]
    for i,secret in enumerate(scenarios()):
        inp,expected,queries=run_live(exe,secret);counts.append(queries);edges.append((f'真实铁路交互转录 {i+1}',inp,expected))
    check_rejection_exit(exe,'-1\n');check_rejection_exit(exe,None)
    proof={'kind':'railway','liveScenarios':len(counts),'liveProcesses':len(edges),'maxQueries':max(counts),
        'programSha256':hashlib.sha256(spec.code.encode()).hexdigest(),'judgeSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'checkedFlush':True,'checkedQueryBudget':True,'negativeReplyExit':True,'eofExit':True,'passed':True,
        'oracle':'all full spanning forests for tiny graphs; Prim over all components for larger graphs',
        'elapsedSeconds':round(time.monotonic()-started,3)}
    (logs/'interactive-live.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return edges,proof
