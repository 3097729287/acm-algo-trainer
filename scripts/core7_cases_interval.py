"""Complete deletion/merge orders, operation strings and literal query triples."""
from collections import Counter,deque
from functools import lru_cache
from itertools import combinations,permutations,product
from math import comb
import random

IDS={'P1435','P1775','P2734','P17015','P1063','P1388','P1880','P3205','P4290',
     'P10236','P13439','UVA1362','UVA10003','P1070','P6006','P7129','UVA1626','CF1336C'}


def palindrome_subsequences(s):
    longest=0
    for mask in range(1<<len(s)):
        word=''.join(c for i,c in enumerate(s) if mask>>i&1)
        if word==word[::-1]:longest=max(longest,len(word))
    return len(s)-longest


def merge_orders(values,circular=False):
    def canonical(a):return min(a[i:]+a[:i] for i in range(len(a))) if circular else a
    @lru_cache(None)
    def search(a):
        if len(a)==1:return 0,0
        minimum=10**30;maximum=0
        for i in range(len(a) if circular else len(a)-1):
            if i+1<len(a):weight=a[i]+a[i+1];nxt=a[:i]+(weight,)+a[i+2:]
            else:weight=a[-1]+a[0];nxt=(weight,)+a[1:-1]
            low,high=search(canonical(nxt));minimum=min(minimum,low+weight);maximum=max(maximum,high+weight)
        return minimum,maximum
    return search(canonical(tuple(values)))


def game_tree(a,turn=0):
    if not a:return 0,0
    possibilities=[]
    for value,remaining in [(a[0],a[1:]),(a[-1],a[:-1])]:
        score=list(game_tree(remaining,1-turn));score[turn]+=value;possibilities.append(tuple(score))
    return max(possibilities,key=lambda score:score[turn])


def deletion_orders(values):
    @lru_cache(None)
    def all_orders(a):
        if not a:return 0
        return max((a[i-1] if i else 0)+(a[i+1] if i+1<len(a) else 0)+all_orders(a[:i]+a[i+1:]) for i in range(len(a)))
    return all_orders(tuple(values))


def bead_orders(heads):
    def canonical(a):return min(a[i:]+a[:i] for i in range(len(a)))
    @lru_cache(None)
    def all_orders(a):
        if len(a)==1:return 0
        best=0
        for i in range(len(a)):
            j=(i+1)%len(a);gain=a[i][0]*a[i][1]*a[j][1];merged=(a[i][0],a[j][1])
            nxt=a[:i]+(merged,)+a[i+2:] if j else (merged,)+a[1:-1]
            best=max(best,gain+all_orders(canonical(nxt)))
        return best
    return all_orders(canonical(tuple((x,heads[(i+1)%len(heads)]) for i,x in enumerate(heads))))


@lru_cache(None)
def binary_shapes(n):
    if n==1:return (None,)
    return tuple((left,right) for k in range(1,n) for left in binary_shapes(k) for right in binary_shapes(n-k))


@lru_cache(None)
def leaves(shape):return 1 if shape is None else leaves(shape[0])+leaves(shape[1])


def expression_trees(a,multiplications):
    def evaluate(shape,mask,offset=0):
        if shape is None:return a[offset]
        left,right=shape;count=leaves(left);x=evaluate(left,mask,offset);y=evaluate(right,mask,offset+count)
        return x*y if mask>>(offset+count-1)&1 else x+y
    masks=[sum(1<<i for i in chosen) for chosen in combinations(range(len(a)-1),multiplications)]
    return max(evaluate(tree,mask) for mask in masks for tree in binary_shapes(len(a)))


@lru_cache(None)
def choir_permutations(n):
    result=Counter()
    for initial in permutations(range(n)):
        line=deque([initial[0]])
        for old,new in zip(initial,initial[1:]):
            if new<old:line.appendleft(new)
            else:line.append(new)
        result[tuple(line)]+=1
    return result


def grammar_reductions(rules,s):
    parent={pair:[] for pair in map(''.join,product('WING',repeat=2))}
    for c,choices in zip('WING',rules):
        for pair in choices:parent[pair].append(c)
    layer={s}
    while layer and len(next(iter(layer)))>1:
        layer={word[:i]+c+word[i+2:] for word in layer for i in range(len(word)-1) for c in parent[word[i:i+2]]}
    possible=set(layer)
    return ''.join(c for c in 'WING' if c in possible) or 'The name is wrong!'


def endpoint_operations(a):
    best=0;mod=998244353
    for bits in product((0,1),repeat=len(a)):
        todo=deque(a);chosen=[todo.pop() if bit else todo.popleft() for bit in bits]
        value=sum(0 if x==y==0 else pow(x,y,mod) for x,y in zip(chosen,chosen[1:]))
        best=max(best,value)
    return best


def cutting_orders(length,positions,prison=False):
    best=10**30
    for order in permutations(positions):
        boundaries=[0,length+1 if prison else length];price=0
        for p in order:
            left=max(x for x in boundaries if x<p);right=min(x for x in boundaries if x>p)
            price+=right-left-(2 if prison else 0);boundaries.append(p)
        best=min(best,price)
    return best


@lru_cache(None)
def dyck_words(pairs):
    if pairs==0:return ('',)
    return tuple('('+left+')'+right for first in range(pairs) for left in dyck_words(first) for right in dyck_words(pairs-1-first))


@lru_cache(None)
def cave_shapes(nodes):
    visits=[]
    for shape in dyck_words(nodes-1):
        stack=[0];order=[0];next_id=1
        for c in shape:
            if c=='(':stack.append(next_id);next_id+=1
            else:stack.pop()
            order.append(stack[-1])
        visits.append(tuple(order))
    return tuple(visits)


def cave_colorings(s):
    if len(s)%2==0:return 0
    count=0
    for visits in cave_shapes((len(s)+1)//2):
        color={};valid=True
        for node,c in zip(visits,s):
            if node in color and color[node]!=c:valid=False;break
            color[node]=c
        count+=valid
    return count


def road_schedules(a,cost,limit):
    n=len(a);m=len(a[0])
    @lru_cache(None)
    def search(t):
        if t==m:return 0
        best=-10**30
        for start in range(n):
            coins=-cost[start]
            for length in range(1,min(limit,m-t)+1):
                coins+=a[(start+length-1)%n][t+length-1];best=max(best,coins+search(t+length))
        return best
    return search(0)


def triples(a,l,r):
    return sum(a[i]+a[j]+a[k]==0 for i,j,k in combinations(range(l,r+1),3))


def ice_plays(values,center):
    def literal(l,r,score):
        if l==0 and r==len(values)-1:return score
        step=r-l+2;answers=[]
        if l:answers.append(literal(l-1,r,score+step*values[l-1]))
        if r+1<len(values):answers.append(literal(l,r+1,score+step*values[r+1]))
        return max(answers)
    return literal(center,center,values[center])


def ice_stage_counts(stages,budget):
    gains=[ice_plays(y,c) for s,m,y,c in stages];best=0
    for counts in product(*(range(m+1) for s,m,y,c in stages)):
        stopped=False;valid=True;spent=score=0
        for x,(s,m,y,c),g in zip(counts,stages,gains):
            if x and stopped:valid=False;break
            if x==0:stopped=True
            spent+=x*s;score+=x*g
        if valid and spent<=budget:best=max(best,score)
    return best


@lru_cache(None)
def regular_brackets(pairs):
    answer=[]
    for shape in dyck_words(pairs):
        for types in product((0,1),repeat=pairs):
            stack=[];word=[];next_id=0
            for c in shape:
                if c=='(':t=types[next_id];next_id+=1;stack.append(t);word.append('[' if t else '(')
                else:word.append(']' if stack.pop() else ')')
            answer.append(''.join(word))
    return tuple(answer)


def subsequence(s,t):
    i=0
    for c in t:
        if i<len(s) and s[i]==c:i+=1
    return i==len(s)


def bracket_enumeration(s):
    for pairs in range((len(s)+1)//2,len(s)+1):
        if any(subsequence(s,word) for word in regular_brackets(pairs)):return 2*pairs
    raise AssertionError(s)


def spell_operations(s,t):
    answer=0
    for length in range(len(t),len(s)+1):
        for bits in product((0,1),repeat=length):
            word=deque()
            for c,bit in zip(s,bits):
                if bit:word.append(c)
                else:word.appendleft(c)
            answer+=''.join(word).startswith(t)
    return answer%998244353


def cases_for(pid):
    rng=random.Random(20261101+sum(map(ord,pid)));result=[]
    def put(inp,out):result.append((f'{pid}-independent-{len(result)+1}',inp,str(out).rstrip()+'\n'))
    def row(a):return ' '.join(map(str,a))+'\n'
    if pid=='P1435':
        for _ in range(230):
            s=''.join(rng.choice('aAb3') for i in range(rng.randint(1,12)));put(s+'\n',palindrome_subsequences(s))
        put('a'*500+'b'*500+'\n',500);put('a'*1000+'\n',0)
    elif pid=='P1775':
        for _ in range(230):
            a=[rng.randint(1,1000) for i in range(rng.randint(1,8))];put(f'{len(a)}\n'+row(a),merge_orders(a)[0])
        put('300\n'+row([1000]*300),2488000)
    elif pid=='P2734':
        for _ in range(210):
            a=[rng.randint(1,200) for i in range(rng.randint(2,11))];put(f'{len(a)}\n'+row(a),row(game_tree(a)))
        put('100\n'+row([200]*100),'10000 10000')
        put('100\n'+row([1,200]*50),'10000 50')
    elif pid=='P17015':
        for _ in range(260):
            a=[rng.randint(0,1000) for i in range(rng.randint(1,9))];put(f'{len(a)}\n'+row(a),deletion_orders(a))
        put('100\n'+row([10**9]*100),197*10**9);put('100\n'+row([0]*100),0)
    elif pid=='P1063':
        for _ in range(200):
            a=[rng.randint(1,15) for i in range(rng.randint(4,7))];put(f'{len(a)}\n'+row(a),bead_orders(a))
        put('100\n'+row([200]*100),792000000)
    elif pid=='P1388':
        for _ in range(180):
            n=rng.randint(2,7);a=[rng.randint(0,9) for i in range(n)];k=rng.randrange(n);put(f'{n} {k}\n'+row(a),expression_trees(a,k))
        for k,a,expected in [(0,[9]*15,135),(14,[1]*15,1),(7,[0]*15,0),(1,[1]*15,56)]:put(f'15 {k}\n'+row(a),expected)
    elif pid=='P1880':
        for _ in range(220):
            a=[rng.randint(0,20) for i in range(rng.randint(1,8))];low,high=merge_orders(a,True);put(f'{len(a)}\n'+row(a),f'{low}\n{high}')
        put('100\n'+row([20]*100),'13440\n100980');put('100\n'+row([0]*100),'0\n0')
    elif pid=='P3205':
        for n in range(1,7):
            all_counts=choir_permutations(n)
            for a in permutations(range(n)):put(f'{n}\n'+row([x+1000 for x in a]),all_counts[a])
        for n in [7,8]:
            all_counts=choir_permutations(n)
            for _ in range(120):
                a=list(range(n));rng.shuffle(a);put(f'{n}\n'+row([x+1000 for x in a]),all_counts[tuple(a)])
        put('1000\n'+row(range(1000,2000)),pow(2,999,19650827));put('1000\n'+row(range(1999,999,-1)),0)
    elif pid=='P4290':
        pairs=list(map(''.join,product('WING',repeat=2)))
        for _ in range(240):
            rules=[rng.sample(pairs,rng.randrange(5)) for i in range(4)];s=''.join(rng.choice('WING') for i in range(rng.randint(1,7)))
            put(row(map(len,rules))+''.join('\n'.join(rule)+'\n' if rule else '' for rule in rules)+s+'\n',grammar_reductions(rules,s))
        put('16 16 16 16\n'+('\n'.join(pairs)+'\n')*4+'W'*200+'\n','WING')
        put('0 0 0 0\nWI\n','The name is wrong!')
    elif pid=='P10236':
        for _ in range(20):
            arrays=[[rng.randint(0,30) for i in range(rng.randint(2,10))] for j in range(18)]
            put(f'{len(arrays)}\n'+''.join(f'{len(a)}\n'+row(a) for a in arrays),'\n'.join(map(str,map(endpoint_operations,arrays))))
        put('1\n1000\n'+row([998244352,1]*500),500*998244352+499)
        put('1\n1000\n'+row([0]*1000),0)
    elif pid=='P13439':
        for _ in range(12):
            cases=[];answers=[]
            for i in range(25):
                p=rng.randint(1,35);positions=sorted(rng.sample(range(1,p+1),rng.randint(1,min(7,p))))
                cases.append(f'{p} {len(positions)}\n'+row(positions));answers.append(f'Case #{i+1}: {cutting_orders(p,positions,True)}')
            put('25\n'+''.join(cases),'\n'.join(answers))
        put('100\n'+('10000 100\n'+row(range(1,101)))*100,'\n'.join(f'Case #{i}: 10473' for i in range(1,101)))
    elif pid=='UVA1362':
        strings=[''.join(word) for length in range(1,10) for word in product('AB',repeat=length)]
        strings += [''.join(rng.choice('ABC') for i in range(rng.randint(1,13))) for j in range(240)]
        for start in range(0,len(strings),40):
            group=strings[start:start+40];put('\n'.join(group)+'\n','\n'.join(str(cave_colorings(s)) for s in group))
        count=comb(298,149)//150%10**9;put('A'*299+'\n'+'AB'*149+'A\n'+'A'*300+'\n',f'{count}\n{count}\n0')
    elif pid=='UVA10003':
        for _ in range(15):
            cases=[];answer=[]
            for j in range(20):
                length=rng.randint(2,50);positions=sorted(rng.sample(range(1,length),rng.randint(0,min(7,length-1))))
                cases.append(f'{length}\n{len(positions)}\n'+row(positions));answer.append(f'The minimum cutting is {cutting_orders(length,positions)}.')
            put(''.join(cases)+'0\n','\n'.join(answer))
        put('950\n49\n'+row(range(19,950,19))+'0\n','The minimum cutting is 5434.')
    elif pid=='P1070':
        for _ in range(400):
            n=rng.randint(2,5);m=rng.randint(1,8);limit=rng.randint(1,m);a=[[rng.randint(1,100) for j in range(m)] for i in range(n)];cost=[rng.randint(1,100) for i in range(n)]
            put(f'{n} {m} {limit}\n'+''.join(map(row,a))+row(cost),road_schedules(a,cost,limit))
        put('1000 1000 1\n'+row([1]*1000)*1000+row([100]*1000),-99000)
        put('1000 1000 1000\n'+row([100]*1000)*1000+row([1]*1000),99999)
    elif pid=='P6006':
        for _ in range(200):
            n=rng.randint(1,17);a=[rng.choice([rng.randint(-20,20),-1000000,1000000,0]) for i in range(n)];queries=[(l,r) for l in range(n) for r in range(l,n)]
            put(f'{n} {len(queries)}\n'+row(a)+''.join(f'{l+1} {r+1}\n' for l,r in queries),'\n'.join(str(triples(a,l,r)) for l,r in queries))
        n=5000;queries=[];answers=[]
        for i in range(100000):
            l=1+i%2500;r=5000-i%2500;length=r-l+1;queries.append(f'{l} {r}\n');answers.append(str(comb(length,3) if length>=3 else 0))
        put('5000 100000\n'+row([0]*5000)+''.join(queries),'\n'.join(answers))
    elif pid=='P7129':
        for _ in range(260):
            stages=[];budget=rng.randint(1,40)
            for i in range(rng.randint(1,4)):
                k=rng.randint(1,7);stages.append((rng.randint(1,15),rng.randint(1,3),[rng.randint(1,500) for j in range(k)],rng.randrange(k)))
            put(f'{len(stages)} {budget}\n'+''.join(f'{s} {m} {len(y)} {c+1}\n'+row(y) for s,m,y,c in stages),ice_stage_counts(stages,budget))
        put('200 100000\n'+('1 500 500 250\n'+row([500]*500))*200,6262500000000)
        put('2 1\n2 1 1 1\n1\n1 500 1 1\n500\n',0)
    elif pid=='UVA1626':
        strings=[''.join(word) for length in range(5) for word in product('()[]',repeat=length)]
        strings += [''.join(rng.choice('()[]') for i in range(rng.randint(5,7))) for j in range(140)]
        for start in range(0,len(strings),18):
            group=strings[start:start+18];put(f'{len(group)}\n\n'+'\n\n'.join(group)+'\n','\n'.join(str(bracket_enumeration(s)) for s in group))
        group=['','('*100,'['*50+']'*50,')'*50+'('*50,'']
        put('5\n\n'+'\n\n'.join(group)+'\n','0\n200\n100\n200\n0')
    elif pid=='CF1336C':
        for _ in range(300):
            s=''.join(rng.choice('abc') for i in range(rng.randint(1,11)));t=''.join(rng.choice('abc') for i in range(rng.randint(1,len(s))))
            put(s+'\n'+t+'\n',spell_operations(s,t))
        put('a'*3000+'\na\n',(pow(2,3001,998244353)-2)%998244353)
        put('a'*3000+'\n'+'a'*3000+'\n',pow(2,3000,998244353))
        put('a'*3000+'\nb\n',0)
    else:raise KeyError(pid)
    return result
