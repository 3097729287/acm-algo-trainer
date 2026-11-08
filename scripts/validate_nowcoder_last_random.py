"""Independent finite definitions for the final continuous-geometry algorithms."""
from fractions import Fraction as F
from itertools import product,combinations
import heapq,math,random,subprocess,time
from nowcoder_editorials import OUT,write
from validate_nowcoder_optimized_random import check,COUNTS
from validate_nowcoder_geometry_random import hull,cross,points_text,near
RNG=random.Random(2026110817)
PERFORMANCE=[]


def clip(p,a,b,c): # ax+by>=c
    if not p:return []
    q=[]
    for u,v in zip(p,p[1:]+p[:1]):
        x=a*u[0]+b*u[1]-c;y=a*v[0]+b*v[1]-c
        if x>=0:q.append(u)
        if (x<0<y) or (y<0<x):
            t=x/(x-y);q.append((u[0]+t*(v[0]-u[0]),u[1]+t*(v[1]-u[1])))
    return q


def polygon_area(p):return abs(sum(cross(u,v) for u,v in zip(p,p[1:]+p[:1])))/2 if p else 0


def spark():
    for _ in range(90):
        X,Y=RNG.randint(1,6),RNG.randint(1,6);n=RNG.randint(1,6);strips=[]
        for i in range(n):
            while True:
                a,b=RNG.randint(-3,3),RNG.randint(-3,3)
                if a or b:break
            c,d=sorted([RNG.randint(-8,8),RNG.randint(-8,8)]);strips.append((a,b,c,d))
        possible=False
        for signs in product([False,True],repeat=n):
            p=[(F(0),F(0)),(F(X),F(0)),(F(X),F(Y)),(F(0),F(Y))]
            for (a,b,c,d),sign in zip(strips,signs):
                p=clip(p,a if sign else -a,b if sign else -b,d if sign else -c)
                if not p:break
            if polygon_area(p)>0:possible=True;break
        check(238005,f'1\n{X} {Y} {n}\n'+'\n'.join(' '.join(map(str,s)) for s in strips),'1' if possible else '0')


def series():
    for _ in range(45):
        m=RNG.randint(1,150);v=[RNG.randint(1,30) for i in range(RNG.randint(1,30))];dp=[1]+[0]*m
        for x in v:
            for j in range(x,m+1):dp[j]=(dp[j]+dp[j-x])%19260817
        check(17528,f'{len(v)} {m}\n'+'\n'.join(map(str,v)),sum(dp[1:])%19260817)


def stars_and_manhattan():
    for _ in range(55):
        p=RNG.sample(list(product(range(16),repeat=2)),RNG.randint(1,30))
        angles=sorted(RNG.sample(range(180),RNG.randint(2,10)))
        if len(angles)%2:angles.pop()
        interval=list(zip(angles[::2],angles[1::2]));expected=[]
        for x,y in p:
            count=0
            for a,b in p:
                if (x,y)==(a,b):continue
                angle=math.degrees(math.atan2(b-y,x-a))%360
                count+=any(l-1e-10<=angle<=r+1e-10 for l,r in interval)
            expected.append(count)
        check(236505,f'{len(p)} {len(interval)}\n'+points_text(p)+'\n'+points_text(interval),expected)
        original=RNG.sample(list(product(range(21),repeat=2)),RNG.randint(1,10));current=original.copy();ops=[];answers=[]
        for j in range(35):
            x,y=RNG.randint(0,20),RNG.randint(0,20);kind=RNG.randint(1,2);ops.append((kind,x,y))
            if kind==1:current.append((x,y))
            else:answers.append(min(abs(a-x)+abs(b-y) for a,b in current))
        check(243845,f'{len(original)} {len(ops)}\n'+points_text(original)+'\n'+'\n'.join(' '.join(map(str,q)) for q in ops),answers)


def circle_union(discs):
    answer=0
    for i,(x,r) in enumerate(discs):
        covered=[];hidden=False
        for j,(y,s) in enumerate(discs):
            if i==j:continue
            d=abs(x-y)
            if d+r<=s and (d+r<s or j<i):hidden=True;break
            if d>=r+s or d+s<=r or not d:continue
            delta=math.acos(max(-1,min(1,(d*d+r*r-s*s)/(2*d*r))))
            middle=0 if y>x else math.pi;l=middle-delta;h=middle+delta
            for shift in [-2*math.pi,0,2*math.pi]:
                a,b=max(0,l+shift),min(2*math.pi,h+shift)
                if a<b:covered.append((a,b))
        if hidden:continue
        covered.sort();at=0
        for a,b in covered+[(2*math.pi,2*math.pi)]:
            if a>at:answer+=(r*r*(a-at)+r*x*(math.sin(a)-math.sin(at)))/2
            at=max(at,b)
    return answer


def plates():
    for _ in range(65):
        discs=[(RNG.randint(-20,20),RNG.randint(1,20)) for i in range(RNG.randint(1,15))]
        near(230850,str(len(discs))+'\n'+points_text(discs),[circle_union(discs[:i]) for i in range(1,len(discs)+1)],3e-9)
    # Rectangle pixel union independently verifies exposed-edge integration.
    for _ in range(55):
        rect=[]
        for i in range(RNG.randint(1,8)):
            x,y=RNG.randint(0,12),RNG.randint(0,12);rect.append((x,y,x+RNG.randint(1,6),y+RNG.randint(1,6)))
        cells=set();polygons=[];paint=0
        for a,b,c,d in rect:
            paint+=(c-a)*(d-b);cells.update(product(range(a,c),range(b,d)))
            q=[(a,b),(c,b),(c,d),(a,d)]
            if RNG.randrange(2):q.reverse()
            polygons.append(q)
        near(233174,str(len(polygons))+'\n'+'\n'.join('4 '+points_text(q).replace('\n',' ') for q in polygons),[paint,len(cells)],1e-8)


def point_segment(p,a,b):
    e=(b[0]-a[0],b[1]-a[1]);t=max(0,min(1,sum((p[i]-a[i])*e[i] for i in range(2))/sum(v*v for v in e)))
    return math.dist(p,(a[0]+t*e[0],a[1]+t*e[1]))


def sweep_decisions():
    for _ in range(75):
        # Distinct x-strips guarantee disjoint segments, with horizontal/vertical cases.
        segments=[]
        for i in range(RNG.randint(2,18)):
            x=i*10;y=RNG.randint(-20,20)
            a=(x,y);b=(x+RNG.randint(0,5),y+RNG.choice([-4,-1,1,4]));segments.append((a,b))
        RNG.shuffle(segments)
        expected=min(min(point_segment(p,*other) for p in current) for current,other in combinations(segments,2))
        expected=min(expected,min(min(point_segment(p,*current) for p in other) for current,other in combinations(segments,2)))
        near(230839,'1\n'+str(len(segments))+'\n'+'\n'.join(points_text(s).replace('\n',' ') for s in segments),expected)
    for _ in range(80):
        count=RNG.randint(2,15);positions=RNG.sample(list(product(range(-8,9),repeat=2)),count);cars=[]
        for x,y in positions:cars.append((x,y,RNG.choice([-3,-2,-1,1,2,3]),RNG.choice([-3,-2,-1,1,2,3]),RNG.randint(1,8)))
        best=math.inf
        for a,b in combinations(cars,2):
            x,y=b[0]-a[0],b[1]-a[1];u=a[2:4];v=b[2:4];den=cross(u,v)
            if den:
                alpha=F(cross((x,y),v),den);beta=F(cross((x,y),u),den)
                if alpha>=0 and beta>=0:best=min(best,max(float(alpha)*math.hypot(*u)/a[4],float(beta)*math.hypot(*v)/b[4]))
            elif cross((x,y),u)==0:
                z=(x*u[0]+y*u[1])/math.hypot(*u)
                if sum(i*j for i,j in zip(u,v))>0:best=min(best,z/a[4] if z>=0 else -z/b[4])
                elif z>=0:best=min(best,z/(a[4]+b[4]))
        data=str(count)+'\n'+'\n'.join(' '.join(map(str,a)) for a in cars)
        if math.isinf(best):check(238004,data,'No show :(')
        else:near(238004,data,best)
    for _ in range(45):
        n=RNG.randint(1,9);walls=[]
        for i in range(n):
            x=3*i;y=RNG.randint(-6,6);walls.append(((x,y),(x,y+RNG.randint(1,4))))
        point=[q for s in walls for q in s]+[(-2,0),(3*n+1,RNG.randint(-5,5))]
        penalty=RNG.randint(0,10);V=len(point);distance=[math.inf]*V;distance[-2]=0;heap=[(0,V-2)]
        while heap:
            d,v=heapq.heappop(heap)
            if d!=distance[v]:continue
            for u in range(V):
                if u==v:continue
                a,b=point[v],point[u]
                count=sum(cross(b,c,a)*cross(b,e,a)<0 and cross(e,a,c)*cross(e,b,c)<0 for c,e in walls)
                new=d+math.dist(a,b)+penalty*count
                if new<distance[u]:distance[u]=new;heapq.heappush(heap,(new,u))
        data=f'1\n{n} {penalty}\n'+'\n'.join(points_text(s).replace('\n',' ') for s in walls)+'\n'+points_text(point[-2:])
        near(232803,data,distance[-1])


def insets():
    for _ in range(45):
        p=hull(RNG.sample(list(product(range(1,30),repeat=2)),12))
        if len(p)<3:continue
        a,b,c=RNG.sample(p,3)
        triangle=hull([a,b,c])
        expected=abs(cross(b,c,a))/(math.dist(a,b)+math.dist(b,c)+math.dist(c,a))
        near(233170,'3\n'+points_text(triangle)+'\n0',expected)
        n=len(p);best=1
        for step in range(1,(n+1)//2):
            q=[tuple(map(float,v)) for v in p]
            for i in range(n):
                a,b=p[i],p[(i+step)%n];e=(b[0]-a[0],b[1]-a[1])
                q=clip(q,-e[1],e[0],e[0]*a[1]-e[1]*a[0])
            if polygon_area(q)>1e-8:best=step
        check(234015,str(n)+'\n'+points_text(list(reversed(p))),best)


def performance():
    for number,data,timeout in [
        (17528,'50000 50000\n'+'\n'.join(str(RNG.randint(1,50000)) for i in range(50000)),30),
        (236487,'1000\n'+'\n'.join(f'{i*0.998:.6f} {i*0.997:.6f}' for i in range(1,1001)),20),
        (230850,'100000\n'+'\n'.join(f'{RNG.randint(-100000,100000)} {RNG.randint(1,1000000)}' for i in range(100000)),20),
        (243845,'1 300000\n0 0\n'+'\n'.join(f'{1 if i%2 else 2} {RNG.randint(0,1000000)} {RNG.randint(0,1000000)}' for i in range(300000)),30),
    ]:
        start=time.perf_counter();run=subprocess.run([str(OUT/'compiled'/str(number)/'main.exe')],input=data,text=True,capture_output=True,timeout=timeout)
        assert run.returncode==0 and run.stdout.strip(),(number,run.returncode,run.stderr)
        assert 'nan' not in run.stdout.lower(),number
        PERFORMANCE.append({'id':number,'seconds':time.perf_counter()-start,'outputLines':len(run.stdout.splitlines())})


def continuous_optima():
    # Exhaust all active-pair equality angles, independent of width-event bisection.
    for _ in range(14):
        p=RNG.sample(list(product(range(-8,9),repeat=2)),RNG.randint(4,7))
        vectors=[(b[0]-a[0],b[1]-a[1]) for a,b in combinations(p,2)]
        angles={0.0}
        for d in vectors:angles.add(math.atan2(d[1],d[0])%(math.pi/2))
        for d,e in product(vectors,repeat=2):
            for sign in [-1,1]:
                a=d[0]-sign*e[1];b=d[1]+sign*e[0]
                if a or b:angles.add(math.atan2(-a,b)%(math.pi/2))
        best=math.inf
        for angle in angles:
            c,s=math.cos(angle),math.sin(angle)
            q=sorted((x*c+y*s,-x*s+y*c) for x,y in p)
            for l in range(len(q)):
                for r in range(l,len(q)):
                    outside=[q[i][1] for i in range(len(q)) if not l<=i<=r]
                    width=max(q[r][0]-q[l][0],max(outside)-min(outside) if outside else 0)
                    best=min(best,width)
        near(232786,str(len(p))+'\n'+points_text(p),best,2e-7)
    # Single straight hill: exact unit rolls followed by a ground arc.
    for _ in range(70):
        x,y=RNG.uniform(.05,20),RNG.uniform(.05,20)
        x,y=round(x,6),round(y,6)
        length=math.hypot(x,y);phi=math.atan2(y,x);steps=int(length)
        if length-steps<.001:continue
        if steps==0:expected=math.pi/2+math.asin(y)
        else:
            expected=phi+math.pi/2+((steps-1)//2)*math.pi
            gamma=math.asin((length-steps)*math.sin(phi))
            expected+=math.pi-gamma if steps%2 else math.pi+gamma-phi
        near(236487,f'1\n{x:.6f} {y:.6f}',expected,2e-7)


if __name__=='__main__':
    spark();series();stars_and_manhattan();plates();sweep_decisions();insets();continuous_optima();performance()
    report={'passed':True,'cases':sum(COUNTS.values()),'counts':COUNTS,'performance':PERFORMANCE,'officialSubmissionsSent':False}
    write(OUT/'last-independent-validation.json',report);print(report)
