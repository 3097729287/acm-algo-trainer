"""Circles: feasible centers, signed polygon integrals and support functions."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY
from nowcoder_geometry_templates import CIRCLE

CIRCLE_INTERSECTIONS=r'''
vector<Point> circleIntersections(Point a,long double r,Point b,long double s){
    Point e=b-a;long double d=norm(e);
    if(d<EPS || d>r+s+EPS || d<fabsl(r-s)-EPS)return {};
    long double x=(r*r-s*s+d*d)/(2*d),h2=r*r-x*x;
    if(h2<-EPS)return {};Point center=a+e*(x/d),offset=rotate90(e)*(sqrtl(max(0.0L,h2))/d);
    if(norm(offset)<EPS)return {center};return {center+offset,center-offset};
}
'''
DISC_AREA=r'''
long double intersectionArea(long double r,long double s,long double d){
    if(r<=0 || s<=0 || d>=r+s)return 0;
    const long double pi=acosl(-1.0L);
    if(d<=fabsl(r-s))return pi*min(r,s)*min(r,s);
    long double a=acosl(clamp((r*r+d*d-s*s)/(2*r*d),-1.0L,1.0L));
    long double b=acosl(clamp((s*s+d*d-r*r)/(2*s*d),-1.0L,1.0L));
    return r*r*(a-sinl(2*a)/2)+s*s*(b-sinl(2*b)/2);
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(234011,1900,['几何概率','圆相交面积'],'正方形能旋转进入两个圆时，求同时获奖的条件概率。',
        r'先确定可得分的正方形中心区域。中心距圆心为d时，旋转正方形，使一条边平行于中心连线，能使最远顶点距离最小，其平方为$(d+a/2)^2+(a/2)^2$。所以允许中心距为$\rho=\sqrt{r^2-a^2/4}-a/2$，可行中心区域是半径ρ的圆盘。'
        '\n\n两次只要求“各自存在一个转角”，无需同一转角同时进入两个圆。因此条件概率是两个可行中心圆盘交面积除以第一圆盘面积。奖金圆若r≤a/√2，可行中心区域没有正面积，概率为0。相交面积分别处理相离、包含和相交两扇形减三角形。',
        r'''int tests;cin >> tests;while(tests--){long double r,s,a;Point p,q;cin >> r >> p.x >> p.y >> s >> q.x >> q.y >> a;auto available=[&](long double radius){if(2*radius*radius<=a*a)return 0.0L;return sqrtl(radius*radius-a*a/4)-a/2;};r=available(r);s=available(s);cout << fixed << setprecision(6) << intersectionArea(r,s,distance(p,q))/(acosl(-1.0L)*r*r) << '\n';}''',
        '不能直接把大圆半径减去正方形外接圆半径：允许旋转时可行中心更大。严格内含只排除边界，对连续概率无影响。',
        declarations=GEOMETRY+DISC_AREA,floating_output=True)
    put(234865,2000,['阿波罗尼斯圆','圆与多边形交面积'],'求简单多边形内满足|PB|≤k|PA|的区域面积。',
        r'将距离平方展开配方，干扰区域是圆盘，圆心$C=(B-k^2A)/(1-k^2)$，半径$R=k|A-B|/(1-k^2)$。平移C到原点，按多边形边AB求有向三角形OAB与圆盘交面积，最后取总和绝对值。'
        '\n\n把线段AB与圆的交点参数加入0、1并排序。每段的中点在圆内时，贡献cross(P,Q)/2；在圆外时，贡献R²*atan2(cross(P,Q),dot(P,Q))/2，即有向扇形面积。各边相加自动抵消内部射线，凹多边形和任意输入方向都能处理。',
        r'''int n,t=0;long double k;while(cin >> n >> k){vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;Point a,b;cin >> a.x >> a.y >> b.x >> b.y;Point center=(b-a*(k*k))/(1-k*k);long double radius=k*distance(a,b)/(1-k*k),answer=0;for(int i=0;i<n;i++){Point u=p[i]-center,v=p[(i+1)%n]-center,e=v-u;vector<long double> cut={0,1};long double A=dot(e,e),B=2*dot(u,e),C=dot(u,u)-radius*radius,discriminant=B*B-4*A*C;if(A>0 && discriminant>0){long double root=sqrtl(discriminant);for(long double x:{(-B-root)/(2*A),(-B+root)/(2*A)})if(x>0 && x<1)cut.push_back(x);}sort(cut.begin(),cut.end());for(int j=1;j<(int)cut.size();j++){Point x=u+e*cut[j-1],y=u+e*cut[j],mid=(x+y)/2;if(dot(mid,mid)<=radius*radius)answer+=cross(x,y)/2;else answer+=radius*radius*atan2l(cross(x,y),dot(x,y))/2;}}cout << "Case " << ++t << ": " << fixed << setprecision(12) << fabsl(answer) << '\n';}''',
        'A、B塔不是多边形顶点。圆心分母是1−k²；面积累加有符号贡献，不能对每条边先取绝对值。',
        declarations=GEOMETRY,floating_output=True,complexity=r'每组时间 $O(n)$，空间 $O(n)$。')
    put(201836,2100,['支撑函数','圆凸包','分段积分'],'求多个圆盘凸包的周长，圆之间可包含或相交。',
        r'方向$u=(\cos\theta,\sin\theta)$上的支撑值是$h(\theta)=\max_i(x_i\cos\theta+y_i\sin\theta+r_i)$。凸体周长等于$\int_0^{2\pi}h(\theta)\,d\theta$；平移产生的正弦、余弦积分恰抵消。'
        '\n\n两圆支撑值相等时满足Δx*cosθ+Δy*sinθ=Δr，最多两个解。枚举所有这样的角，再加0和2π排序；相邻事件间最外圆固定，用中点找它并精确积分：x(sin右−sin左)−y(cos右−cos左)+r(右−左)。被包含的圆从不成为严格最大，自然不贡献；相同圆也不影响结果。',
        r'''int tests;cin >> tests;const long double pi=acosl(-1.0L);while(tests--){int n;cin >> n;struct Disc{Point c;long double r;};vector<Disc> p(n);for(auto &d:p)cin >> d.c.x >> d.c.y >> d.r;vector<long double> event={0,2*pi};auto normalize=[&](long double a){a=fmodl(a,2*pi);if(a<0)a+=2*pi;return a;};for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){Point d=p[i].c-p[j].c;long double length=norm(d),value=p[j].r-p[i].r;if(length>0 && fabsl(value)<=length){long double base=atan2l(d.y,d.x),delta=acosl(clamp(value/length,-1.0L,1.0L));event.push_back(normalize(base+delta));event.push_back(normalize(base-delta));}}sort(event.begin(),event.end());long double answer=0;for(int j=1;j<(int)event.size();j++){long double l=event[j-1],r=event[j],mid=(l+r)/2;int best=0;auto support=[&](int i){return p[i].c.x*cosl(mid)+p[i].c.y*sinl(mid)+p[i].r;};for(int i=1;i<n;i++)if(support(i)>support(best))best=i;auto d=p[best];answer+=d.c.x*(sinl(r)-sinl(l))-d.c.y*(cosl(r)-cosl(l))+d.r*(r-l);}cout << fixed << setprecision(12) << answer << '\n';}''',
        '仅对圆心求凸包再加某个统一半径，只适用于所有半径相同。这里每个圆的半径都参与支撑值比较。',
        declarations=GEOMETRY,floating_output=True,complexity=r'每组时间 $O(n^3+n^2\log n)$，空间 $O(n^2)$。')
    put(234840,2200,['圆弧','凸包直径','极值位置'],'互不相交的圆形切割之后，求原圆剩余部分的直径。',
        '剩余区域的凸包由原大圆上未被切掉的圆弧及连接弧端点的弦组成：每个切割造成向内的凹口，凹口圆弧不是凸包极点。直径因此可以只在剩余的大圆圆弧上寻找。'
        '\n\n若存在一对保留的对径点，直径为2R。若不存在，对固定端点Q，与它距离最远的保留圆弧点，只能是Q的对径点或某个圆弧端点；前者不可用，所以最远点对都可取圆弧端点。端点就是切割圆与大圆的交点，最多2n个。'
        '\n\n如何检查连续圆弧上有无对径点：保留角度集合与其平移π后的交集若非空，除整圆情形外，一定有一个交集端点来自某个圆弧端点。因此逐个检查端点的对径点是否在所有切割圆外即可；若大圆没有交点，整段大圆边界仍保留，直接2R。其余情况枚举端点两两距离。切口边界是否保留不影响直径的上确界。',
        r'''int tests;cin >> tests;for(int t=1;t<=tests;t++){int n;long double R;cin >> n >> R;vector<Point> c(n),endpoint;vector<long double> radius(n);for(int i=0;i<n;i++){cin >> c[i].x >> c[i].y >> radius[i];auto points=circleIntersections({0,0},R,c[i],radius[i]);endpoint.insert(endpoint.end(),points.begin(),points.end());}bool diameterExists=endpoint.empty();for(Point p:endpoint){Point opposite=p*(-1);bool valid=true;for(int i=0;i<n;i++)if(dot(opposite-c[i],opposite-c[i])<radius[i]*radius[i]-1e-12L){valid=false;break;}if(valid){diameterExists=true;break;}}long double answer=0;if(diameterExists)answer=2*R;else for(int i=0;i<(int)endpoint.size();i++)for(int j=i+1;j<(int)endpoint.size();j++)answer=max(answer,distance(endpoint[i],endpoint[j]));cout << "Case #" << t << ": " << fixed << setprecision(15) << answer << '\n';}''',
        '利用了切割圆两两不相交、没有切割圆包含整个原圆这两个保证。必须先检查连续圆弧上的对径点，不能只枚举有限个交点。',
        declarations=GEOMETRY+CIRCLE_INTERSECTIONS,floating_output=True,complexity=r'每组时间 $O(n^2)$，空间 $O(n)$。')
    put(243173,1700,['相切圆','Descartes定理','曲率'],'三个等半径外切圆之间不断插入小圆，求第k个半径整数部分。',
        r'以大圆曲率1/R为单位，两个固定圆的曲率均为1，尚未插圆时第三个大圆也是1。Descartes定理的两个解满足新旧曲率和为两倍其余三个圆曲率和，因此相邻插入圆的曲率满足$q_k=4+2q_{k-1}-q_{k-2}$。首项$q_0=1$、$q_1=3+2\sqrt3$，解得$q_k=2k^2+2\sqrt3k+1$，所以$R_k=R/q_k$。k最多10，直接代入并向下取整。',
        r'''int tests;long double R;cin >> tests >> R;while(tests--){int k;cin >> k;long double curvature=2.0L*k*k+2*sqrtl(3.0L)*k+1;cout << k << ' ' << (long long)floorl(R/curvature) << '\n';}''',
        '这里输出整数部分，不是四舍五入。输入末尾−1是结束标志，不属于T个询问。π并不参与相切圆半径公式。')
    put(243148,2100,['相切圆链','曲率','尾项误差界'],'两个内切圆之间按图示顺序填圆，求前N个小圆面积之和。',
        r'先令大半径R、小半径r，d=R−r。第一个填圆半径为d，之后上、下两侧对称地各形成一条相切圆链。固定两个大圆的带符号曲率为−1/R、1/r；由Descartes定理，圆链曲率的二阶差分为$2(1/r-1/R)$，对称性给出$q_k=1/d+k^2d/(Rr)$，半径$\rho_k=dRr/(Rr+k^2d^2)$。'
        '\n\n顺序是k=0一个，k=1两个，k=2两个……因此成对计入前floor((N−1)/2)层；若N为偶数，还需加下一层的一个。N可达10^7，不能对所有层逐个求和。'
        r'当k>K时有$\rho_k\le A/k^2$，其中$A=Rr/d\le9900$，两条链剩余总面积不超过$2\pi A^2/(3K^3)$。取K=30000，此界小于$8\times10^{-6}$，严格低于允许的$10^{-4}$。所以只算到该层即可，舍弃有明确误差界的尾项。',
        r'''int tests;cin >> tests;const long double pi=acosl(-1.0L);while(tests--){long double R,r;long long n;cin >> R >> r >> n;if(R<r)swap(R,r);long double d=R-r;if(d==0){cout << "0.000000000000\n";continue;}auto radius=[&](long long k){return d*R*r/(R*r+(long double)k*k*d*d);};long long pairs=(n-1)/2;long double answer=pi*d*d;for(int k=1;k<=min(30000LL,pairs);k++){long double value=radius(k);answer+=2*pi*value*value;}if(n%2==0 && n/2<=30000){long double value=radius(n/2);answer+=pi*value*value;}cout << fixed << setprecision(12) << answer << '\n';}''',
        'R1、R2大小顺序没有保证，应先交换。圆2和圆3半径相等，不能按同一侧链把每个编号都当成新层。截断由尾项积分界保证精度。',
        floating_output=True,complexity=r'每组时间 $O(\min(N,30000))$，额外空间 $O(1)$。')
    put(243145,2100,['圆反演','公外切线'],'构造经过给定点且与两个已知圆外切的全部圆。',
        '以给定点P为反演中心，反演半径取1。将P平移到原点，已知圆(c,r)变成(c/(|c|²−r²), r/(|c|²−r²))。未知圆经过原点，反演后变成一条直线；原先与两个圆外切，等价于这条线是两反演圆的公外切线，且原点与两圆位于线的同一侧。'
        '\n\n把切线写成单位法向量n·x=d，两圆在线的≤侧，则n·(c1−c2)=r2−r1。设e为两圆心连线单位向量，t=(r2−r1)/|c1−c2|，两个候选法向量是t*e±sqrt(1−t²)*rotate90(e)。d=n·c1+r1，只有d>0满足原点在线的同侧。反演回去得到圆心n/(2d)、半径1/(2d)，再平移P。'
        '\n\n本题允许任意答案顺序，验证同时检查解数、过点以及与两圆的外切等式。',
        r'''int tests;cin >> tests;while(tests--){Point a,b,p;long double r,s;cin >> a.x >> a.y >> r >> b.x >> b.y >> s >> p.x >> p.y;a=a-p;b=b-p;long double da=dot(a,a)-r*r,db=dot(b,b)-s*s;a=a/da;r/=da;b=b/db;s/=db;Point e=a-b;long double length=norm(e),t=(s-r)/length;vector<array<long double,3>> answer;if(fabsl(t)<=1+EPS){e=e/length;long double h=sqrtl(max(0.0L,1-t*t));for(int sign:{-1,1}){Point normal=e*t+rotate90(e)*(sign*h);long double d=dot(normal,a)+r;if(d<=1e-18L)continue;Point center=p+normal/(2*d);long double radius=1/(2*d);if(!answer.empty() && distance(center,{answer[0][0],answer[0][1]})<1e-10L)continue;answer.push_back({center.x,center.y,radius});}}cout << answer.size() << '\n';for(auto q:answer)cout << fixed << setprecision(12) << q[0] << ' ' << q[1] << ' ' << q[2] << '\n';}''',
        '反演中心严格在两个已知圆外，两个分母均为正。只解公切线还不够，必须检查d>0，否则反演得到的圆会包住已知圆。',
        declarations=GEOMETRY,checker='apollonius-two-circles',complexity=r'每组时间与空间均为 $O(1)$。')


if __name__=='__main__':run()
