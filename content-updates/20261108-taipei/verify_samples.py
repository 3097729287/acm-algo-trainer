"""Independently verify the recovered small A/B/D examples and exact E grids."""
from fractions import Fraction
import itertools
import json
from pathlib import Path

FOLDER=Path(__file__).resolve().parent


def frame(text):
    values=list(map(int,text.split()));width,height=values[:2];position=2
    def parse(kind):
        nonlocal position
        count=values[position];position+=1
        if not count:
            w,h=values[position:position+2];position+=2
            return 'photo',[],Fraction(w,h),Fraction(0)
        children=[parse('vertical' if kind=='horizontal' else 'horizontal') for _ in range(count)]
        if kind=='horizontal':
            slope=sum(c[2] for c in children);offset=sum(c[3] for c in children)+count-1
        else:
            inverse=sum(1/c[2] for c in children)
            intercept=-sum(c[3]/c[2] for c in children)+count-1
            slope=1/inverse;offset=-intercept/inverse
        return kind,children,slope,offset
    layout=parse('horizontal');assert position==len(values),'Incomplete or extra cross-page input'
    canvas=[['*' if y in (0,height-1) or x in (0,width-1) else ' ' for x in range(width)] for y in range(height)]
    def draw(node,x,y,w,h):
        kind,children,slope,offset=node
        if min(w,h)<=0 or Fraction(w)!=slope*h+offset:raise ValueError('Incompatible frame ratio')
        if kind=='photo':return
        cursor=0
        for i,child in enumerate(children):
            extent=child[2]*h+child[3] if kind=='horizontal' else (Fraction(w)-child[3])/child[2]
            if extent.denominator!=1 or extent<=0:raise ValueError('Noninteger photo dimensions')
            extent=int(extent)
            if kind=='horizontal':
                draw(child,x+cursor,y,extent,h);cursor+=extent
                if i<len(children)-1:
                    for yy in range(y,y+h):canvas[yy][x+cursor]='*'
            else:
                draw(child,x,y+cursor,w,extent);cursor+=extent
                if i<len(children)-1:
                    for xx in range(x,x+w):canvas[y+cursor][xx]='*'
            if i<len(children)-1:cursor+=1
        assert cursor==(w if kind=='horizontal' else h)
    try:draw(layout,1,1,width-2,height-2)
    except ValueError:return 'Impossible'
    return '\n'.join(''.join(row) for row in canvas)


def verify():
    counts={}
    for letter in ['A','B','D','E']:
        samples=json.loads((FOLDER/(letter+'.samples.json')).read_text('utf8'))['samples']
        for sample in samples:
            if letter=='E':actual=frame(sample['input'])
            elif letter=='A':
                values=list(map(int,sample['input'].split()));assert len(values)==1+3*values[0]
                out=[]
                for x,y,n in zip(values[1::3],values[2::3],values[3::3]):
                    paid=min(p for p in range(n+1) if p+p//x*y>=n);out.append(str(3*paid))
                actual='\n'.join(out)
            elif letter=='D':
                values=list(map(int,sample['input'].split()));n,modulus=values[:2];assert len(values)==n+2
                candidates=[int(''.join(map(str,p))) for p in itertools.permutations(values[2:])]
                actual=str(max(candidates,key=lambda value:(value%modulus,value)))
            else:
                words=iter(sample['input'].split());count=int(next(words));out=[]
                for _ in range(count):
                    n=int(next(words));a,b=next(words),next(words);assert len(a)==len(b)==n
                    original=sum(x==y for x,y in zip(a,b));best=None
                    for left in range(n):
                        for right in range(left,n):
                            candidate=b[:left]+b[left:right+1][::-1]+b[right+1:]
                            score=sum(x==y for x,y in zip(a,candidate));rank=(-score,right-left,left)
                            if best is None or rank<best[0]:best=(rank,score,left+1,right+1)
                    out.append(f'{original} {best[1]} {best[2]} {best[3]}')
                assert next(words,None) is None;actual='\n'.join(out)
            assert actual==sample['output'],letter+' recovered sample differs from independent result'
        counts[letter]=len(samples)
    print(json.dumps({'verifiedSamplePairs':counts,'exactAsciiOutput':True,'actualProblemSiteSubmissions':0}))


if __name__=='__main__':verify()
