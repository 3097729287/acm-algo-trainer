"""Small exact definitions independent of support-query and sweep implementations."""
from itertools import combinations,product
import math,random,subprocess
from validate_nowcoder_optimized_random import check,COUNTS
from nowcoder_editorials import OUT,write
RNG=random.Random(2026110816)


def cross(a,b,c=(0,0)):
    return (a[0]-c[0])*(b[1]-c[1])-(a[1]-c[1])*(b[0]-c[0])


def hull(points):
    p=sorted(set(points))
    if len(p)<2:return p
    a=[];b=[]
    for q in p:
        while len(a)>1 and cross(a[-1],q,a[-2])<=0:a.pop()
        a.append(q)
    for q in reversed(p):
        while len(b)>1 and cross(b[-1],q,b[-2])<=0:b.pop()
        b.append(q)
    return a[:-1]+b[:-1]


def inside(p,q):
    if len(p)==1:return p[0]==q
    if len(p)==2:return cross(p[0],p[1],q)==0 and sum((q[i]-p[0][i])*(q[i]-p[1][i]) for i in range(2))<=0
    return all(cross(p[(i+1)%len(p)],q,p[i])>=0 for i in range(len(p)))


def points_text(p):return '\n'.join(f'{x} {y}' for x,y in p)
def area(p):return abs(sum(cross(p[i],p[(i+1)%len(p)]) for i in range(len(p))))


def near(number,data,expected,tolerance=2e-7):
    run=subprocess.run([str(OUT/'compiled'/str(number)/'main.exe')],input=data,text=True,capture_output=True,timeout=20)
    assert run.returncode==0,(number,run.stderr)
    values=list(map(float,run.stdout.split()))
    expected=expected if isinstance(expected,list) else [expected]
    assert len(values)==len(expected) and all(math.isclose(a,b,rel_tol=tolerance,abs_tol=tolerance) for a,b in zip(values,expected)),(number,data,expected,run.stdout)
    COUNTS[str(number)]=COUNTS.get(str(number),0)+1


def triangles():
    for _ in range(80):
        p=[(RNG.randint(0,30),RNG.randint(0,30)) for i in range(RNG.randint(3,15))]
        values=[abs(cross(b,c,a)) for a,b,c in combinations(p,3)]
        check(232792,str(len(p))+'\n'+' '.join(str(x) for x,y in p)+'\n'+' '.join(str(y) for x,y in p),[min(values),max(values)])
        q=[(x*2,y*2) for x,y in set(p)]
        # The original guarantees no collinear triples.
        if len(q)>=3 and all(cross(b,c,a) for a,b,c in combinations(q,3)):
            count=0
            for a,b,c in combinations(q,3):
                twice=abs(cross(b,c,a));boundary=sum(math.gcd(abs(x[0]-y[0]),abs(x[1]-y[1])) for x,y in [(a,b),(b,c),(c,a)])
                count+=((twice-boundary+2)//2)%2==1
            check(250563,str(len(q))+'\n'+points_text(q),count)


def supports():
    for _ in range(90):
        p=RNG.sample(list(product(range(-15,16),repeat=2)),RNG.randint(3,20))
        check(233136,str(len(p))+'\n'+points_text(p),max((a[0]-b[0])**2+(a[1]-b[1])**2 for a,b in combinations(p,2)))
        near(233135,str(len(p))+'\n'+points_text(p),sum(math.dist(a,b) for a,b in zip(hull(p),hull(p)[1:]+hull(p)[:1])))
        queries=[];answers=[]
        for j in range(40):
            a,b=RNG.sample(list(product(range(-20,21),repeat=2)),2)
            side=[cross(b,q,a) for q in p]
            queries.append(points_text([a,b]));answers.append('GOOD' if min(side)>0 or max(side)<0 else 'BAD')
        check(233738,str(len(p))+'\n'+points_text(p)+'\n'+'\n'.join(queries),answers)
        minimum=math.inf
        h=hull(p)
        if len(h)<3:minimum=0
        for a,b in zip(h,h[1:]+h[:1]):
            e=(b[0]-a[0],b[1]-a[1]);d2=sum(x*x for x in e)
            dot=[e[0]*q[0]+e[1]*q[1] for q in h]
            perpendicular=[cross(e,q) for q in h]
            minimum=min(minimum,(max(dot)-min(dot))*(max(perpendicular)-min(perpendicular))/d2)
        near(232791,str(len(p))+'\n'+points_text(p),minimum)
    for _ in range(65):
        p=[]
        while len(p)<16:
            q=(RNG.randrange(-50,51),RNG.randrange(-50,51))
            if q not in p and all(cross(b,q,a) for a,b in combinations(p,2)):p.append(q)
        k=RNG.randint(3,12)
        best=max(area(hull(p[:k]+[q])) for q in p[k:])
        near(233165,f'{len(p)} {k}\n'+points_text(p),best/2)


def illumination():
    for _ in range(80):
        outer=hull([(RNG.randint(-100,-40),RNG.randint(-100,-40)),(RNG.randint(40,100),RNG.randint(-100,-40)),(RNG.randint(40,100),RNG.randint(40,100)),(RNG.randint(-100,-40),RNG.randint(40,100))])
        inner=hull(RNG.sample(list(product(range(-15,16),repeat=2)),8))
        perimeter=sum(math.dist(a,b) for a,b in zip(outer,outer[1:]+outer[:1]))
        answer=0
        for a,b in zip(inner,inner[1:]+inner[:1]):
            illuminated=0
            for u,v in zip(outer,outer[1:]+outer[:1]):
                su,sv=cross(b,u,a),cross(b,v,a)
                portion=1 if su<=0 and sv<=0 else 0
                if (su<0<sv) or (sv<0<su):portion=abs(su if su<0 else sv)/abs(su-sv)
                illuminated+=math.dist(u,v)*portion
            answer+=math.dist(a,b)*illuminated/perimeter
        near(233145,f'{len(outer)} {len(inner)}\n'+points_text(outer)+'\n'+points_text(inner),answer)
    for _ in range(60):
        polygons=[hull(RNG.sample(list(product(range(-10,11),repeat=2)),RNG.randint(3,8))) for i in range(3)]
        q=RNG.sample(list(product(range(-10,11),repeat=2)),30)
        sums=hull([(a[0]+b[0]+c[0],a[1]+b[1]+c[1]) for a,b,c in product(*polygons)])
        data='\n'.join(str(len(p))+'\n'+points_text(p) for p in polygons)+'\n'+str(len(q))+'\n'+points_text(q)
        check(233985,data,['YES' if inside(sums,(x*3,y*3)) else 'NO' for x,y in q])


def dominance_circle():
    for _ in range(60):
        p=[tuple(RNG.randint(1,8) for i in range(3)) for j in range(RNG.randint(1,25))]
        result=[0]*len(p)
        for a in p:
            count=sum(all(x<=y for x,y in zip(b,a)) for b in p)-1
            result[count]+=1
        check(243846,f'{len(p)} 8\n'+'\n'.join(' '.join(map(str,q)) for q in p),result)
        points=RNG.sample(list(product(range(-15,16),repeat=2)),RNG.randint(2,15))
        check(249607,f'1\n{len(points)}\n'+points_text(points),min(sum((x-y)**2 for x,y in zip(a,b)) for a,b in combinations(points,2)))
    for _ in range(50):
        p=RNG.sample(list(product(range(-15,16),repeat=2)),RNG.randint(1,10))
        circles=[(float(x),float(y),0) for x,y in p]
        for a,b in combinations(p,2):
            x,y=(a[0]+b[0])/2,(a[1]+b[1])/2
            circles.append((x,y,math.dist(a,b)/2))
        for a,b,c in combinations(p,3):
            u=(b[0]-a[0],b[1]-a[1]);v=(c[0]-a[0],c[1]-a[1]);den=2*cross(u,v)
            if not den:continue
            du=sum(x*x for x in u);dv=sum(x*x for x in v)
            x=a[0]+(du*v[1]-dv*u[1])/den;y=a[1]+(u[0]*dv-v[0]*du)/den
            circles.append((x,y,math.dist((x,y),a)))
        best=min((c for c in circles if all(math.dist(c[:2],q)<=c[2]+1e-9 for q in p)),key=lambda c:c[2])
        near(243848,str(len(p))+'\n'+points_text(p),[best[2],best[0],best[1]],2e-9)


if __name__=='__main__':
    triangles();supports();illumination();dominance_circle()
    report={'passed':True,'cases':sum(COUNTS.values()),'counts':COUNTS,'officialSubmissionsSent':False}
    write(OUT/'geometry-independent-validation.json',report);print(report)
