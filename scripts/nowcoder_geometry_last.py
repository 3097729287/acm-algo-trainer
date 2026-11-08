"""Six circle constructions, general polygon union and downhill contact events."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY
from nowcoder_geometry_templates import CIRCLE
from nowcoder_geometry_circles import CIRCLE_INTERSECTIONS

CONSTRUCTIONS=r'''
Point lineIntersection(Point a,Point u,Point b,Point v){return a+u*(cross(b-a,v)/cross(u,v));}
vector<Point> lineCircle(Point a,Point d,Point center,long double radius){
    Point projection=a+d*(dot(center-a,d)/dot(d,d));long double h2=radius*radius-dot(projection-center,projection-center);
    if(h2<-1e-9L)return {};if(fabsl(h2)<1e-14L*max(1.0L,radius*radius))h2=0;Point offset=d*(sqrtl(max(0.0L,h2))/norm(d));
    if(norm(offset)<1e-10L)return {projection};return {projection-offset,projection+offset};
}
long double clean(long double x){return fabsl(x)<0.000049999L?0:x;}
void pointOutput(Point p){cout << '(' << clean(p.x) << ',' << clean(p.y) << ')';}
void pointsOutput(vector<Point> points){
    sort(points.begin(),points.end(),[](Point a,Point b){return fabsl(a.x-b.x)>1e-9L?a.x<b.x:a.y<b.y;});
    points.erase(unique(points.begin(),points.end(),[](Point a,Point b){return distance(a,b)<1e-9L;}),points.end());
    cout << '[';for(int i=0;i<(int)points.size();i++){if(i)cout << ',';pointOutput(points[i]);}cout << "]\n";
}
'''
POLYGON_UNION=r'''
int location(const vector<Point> &polygon,Point p,int &edge){
    int winding=0,n=polygon.size();
    for(int i=0;i<n;i++){
        Point a=polygon[i],b=polygon[(i+1)%n];long double side=cross(b-a,p-a);
        if(fabsl(side)<1e-9L && dot(p-a,p-b)<=1e-9L){edge=i;return 2;}
        if(a.y<=p.y){if(b.y>p.y && side>0)winding++;}else if(b.y<=p.y && side<0)winding--;
    }
    return winding!=0;
}
long double signedArea(const vector<Point> &p){long double result=0;for(int i=0;i<(int)p.size();i++)result+=cross(p[i],p[(i+1)%p.size()]);return result/2;}
'''
ROLLING=r'''
Point rotated(Point p,long double angle){return {p.x*cosl(angle)-p.y*sinl(angle),p.x*sinl(angle)+p.y*cosl(angle)};}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(243843,2100,['圆的几何构造','交点','切线'],'处理六种圆相关构造命令，严格按列表与元组格式输出。',
        '把六个命令统一成“圆心在哪里”的交点问题。外接圆：解到三个顶点等距的两条线性方程；内切圆：三个顶点按对边长度加权，半径=二倍面积/周长。'
        '\n\n过点切线：点在圆内无解，在圆上一条切线，在圆外两条，方向角为圆心到点方向±asin(r/d)，按无向直线归一到[0,180)。'
        '\n\n过点且与直线相切、半径固定：圆心在过该点的半径r圆上，同时在给定直线两侧各平移r的直线上，求圆线交点。与两条不平行直线相切：分别平移±r，两两相交得到4个圆心。与两不相交圆外切：圆心到两已知圆心的距离分别为r+r1、r+r2，求两圆交点。'
        '\n\n将几何计算与输出分开：点列表按x、y排序并去重，切线角排序并去重，统一4位小数，不添加空格，消除−0.0000。相切时只输出一个交点。',
        r'''string command;cout << fixed << setprecision(4);const long double pi=acosl(-1.0L);while(cin >> command){if(command=="CircumscribedCircle" || command=="InscribedCircle"){Point a,b,c;cin >> a.x >> a.y >> b.x >> b.y >> c.x >> c.y;Circle result;if(command=="CircumscribedCircle")result=throughThree(a,b,c);else{long double x=distance(b,c),y=distance(a,c),z=distance(a,b),sum=x+y+z;result={(a*x+b*y+c*z)/sum,fabsl(cross(b-a,c-a))/sum};}cout << '(' << clean(result.center.x) << ',' << clean(result.center.y) << ',' << clean(result.radius) << ")\n";}
        else if(command=="TangentLineThroughPoint"){Point c,p;long double r;cin >> c.x >> c.y >> r >> p.x >> p.y;Point d=p-c;long double length=norm(d);vector<long double> angle;if(length>=r-1e-10L){long double base=atan2l(d.y,d.x),delta=asinl(clamp(r/length,-1.0L,1.0L));for(long double a:{base-delta,base+delta}){a=fmodl(a,pi);if(a<0)a+=pi;if(a>pi-1e-12L)a=0;angle.push_back(a*180/pi);}sort(angle.begin(),angle.end());angle.erase(unique(angle.begin(),angle.end(),[](auto a,auto b){return fabsl(a-b)<1e-8L;}),angle.end());}cout << '[';for(int i=0;i<(int)angle.size();i++){if(i)cout << ',';cout << clean(angle[i]);}cout << "]\n";}
        else if(command=="CircleThroughAPointAndTangentToALineWithRadius"){Point p,a,b;long double r;cin >> p.x >> p.y >> a.x >> a.y >> b.x >> b.y >> r;Point d=b-a,n=rotate90(d)*(r/norm(d));vector<Point> answer;for(int sign:{-1,1}){auto points=lineCircle(a+n*sign,d,p,r);answer.insert(answer.end(),points.begin(),points.end());}pointsOutput(answer);}
        else if(command=="CircleTangentToTwoLinesWithRadius"){Point a,b,c,d;long double r;cin >> a.x >> a.y >> b.x >> b.y >> c.x >> c.y >> d.x >> d.y >> r;Point u=b-a,v=d-c,n=rotate90(u)*(r/norm(u)),m=rotate90(v)*(r/norm(v));vector<Point> answer;for(int x:{-1,1})for(int y:{-1,1})answer.push_back(lineIntersection(a+n*x,u,c+m*y,v));pointsOutput(answer);}
        else{Point a,b;long double r,s,t;cin >> a.x >> a.y >> r >> b.x >> b.y >> s >> t;pointsOutput(circleIntersections(a,r+t,b,s+t));}}''',
        '这版要求4位小数，原UVA题的6位不能照搬。圆心列表只输出(x,y)，前两个三角形命令输出(x,y,r)。切线角是无向直线角，180度要归零。',
        declarations=GEOMETRY+CIRCLE+CIRCLE_INTERSECTIONS+CONSTRUCTIONS,complexity=r'每条命令时间、额外空间均为 $O(1)$。')
    put(233174,2300,['多边形面积并','边界积分','区间覆盖'],'多个可凹简单多边形涂满后，求颜料总面积与画布覆盖面积。',
        '颜料总量是各多边形面积之和。覆盖面积使用Green公式：并集边界上有向线段AB的积分贡献是cross(A,B)/2。把每个多边形统一为逆时针，逐条边找没有被其他多边形覆盖的部分，只对这些外露边积分。'
        '\n\n固定一条边AB，将它与另一个多边形所有边的交点参数，以及共线重叠段端点，加入0、1并排序。每两个相邻参数间不会再跨越边界，用中点绕数判断是否在另一多边形内；若在内部，该区间被覆盖。若正好落在重合边界上，同向边只保留编号较小多边形的一份，反向边两侧都是内部，应两份都去掉。'
        '\n\n把所有其他多边形产生的覆盖参数区间求并，外露比例为1减覆盖总长。整条AB的积分乘这个比例，最后将所有边相加。即使一条边被切成多段，它们的积分仍按参数长度线性缩放。此方法直接支持凹多边形、包含以及并集中的洞。',
        r'''int n;cin >> n;vector<vector<Point>> polygon(n);long double paint=0;for(auto &p:polygon){int m;cin >> m;p.resize(m);for(auto &q:p)cin >> q.x >> q.y;long double a=signedArea(p);paint+=fabsl(a);if(a<0)reverse(p.begin(),p.end());}long double coveredArea=0;for(int id=0;id<n;id++)for(int at=0;at<(int)polygon[id].size();at++){Point a=polygon[id][at],b=polygon[id][(at+1)%polygon[id].size()],e=b-a;vector<pair<long double,long double>> covered;for(int other=0;other<n;other++)if(other!=id){const auto &p=polygon[other];vector<long double> cut={0,1};for(int j=0;j<(int)p.size();j++){Point u=p[j],v=p[(j+1)%p.size()],f=v-u;long double den=cross(e,f);if(fabsl(den)>1e-12L){long double t=cross(u-a,f)/den,s=cross(u-a,e)/den;if(t>0 && t<1 && s>=-1e-12L && s<=1+1e-12L)cut.push_back(t);}else if(fabsl(cross(e,u-a))<1e-9L){for(Point q:{u,v}){long double t=dot(q-a,e)/dot(e,e);if(t>0 && t<1)cut.push_back(t);}}}sort(cut.begin(),cut.end());for(int j=1;j<(int)cut.size();j++){long double l=cut[j-1],r=cut[j];if(r-l<1e-15L)continue;int edge=-1,where=location(p,a+e*((l+r)/2),edge);bool hide=where==1;if(where==2){Point f=p[(edge+1)%p.size()]-p[edge];hide=dot(e,f)<0 || other<id;}if(hide)covered.push_back({l,r});}}sort(covered.begin(),covered.end());long double length=0,reach=0;for(auto [l,r]:covered){if(r>reach){length+=r-max(l,reach);reach=r;}}long double exposed=clamp(1-length,0.0L,1.0L);coveredArea+=cross(a,b)*exposed/2;}cout << fixed << setprecision(12) << paint << ' ' << fabsl(coveredArea);''',
        '不能把每两个多边形交面积直接做一次容斥，多重覆盖需要更高阶项。只有最终有向边积分求和后才取绝对值。重合边要按方向和编号处理。',
        declarations=GEOMETRY+POLYGON_UNION,floating_output=True,complexity=r'设总边数E、每个多边形最多M=20条边，时间 $O(E^2M+E^2\log E)$，空间 $O(E)$。')
    put(236487,2300,['事件模拟','刚体转动','圆线段交点'],'长1线段沿单调山坡逆时针滚动，遇到更低接触点更换支点，求头端总路程。',
        '两次接触事件之间，线段绕当前最低支点O做纯旋转，头部走一段半径|OH|的圆弧，路程=半径×转角。下一接触只有两类：山坡顶点碰到线段内部，或线段某个端点碰到山坡边内部。第一类枚举支点左下方、距离不超过相应半臂长度的山坡顶点；第二类求以O为圆心、头臂/尾臂长度为半径的圆与每条山坡边的交点。'
        '\n\n对每个候选接触，把从当前线段朝向转到候选朝向的逆时针角归一到[0,2π)，取最小。新接触点必须严格低于O；同一时刻有多个接触时选最低的那个。头端朝向候选点，尾端则朝向其反方向。除此以外，单独求头部圆轨迹与y=0的交会角，若它更早发生就结束。'
        '\n\n转过事件角后同时旋转头和尾，累加头弧长，再换支点。半臂长度并非总为1：支点可能在身体内部，头臂为0时头暂时不动。山坡还包括从(0,0)向左的水平地面。每个坡顶最多成为一次更低支点，两次坡顶接触之间的端点滚动每步沿坡推进一个单位，所以事件数受n与坡线长度共同限制。',
        r'''int n;cin >> n;vector<Point> mountain={{-10000,0},{0,0}};for(int i=0;i<n;i++){Point p;cin >> p.x >> p.y;mountain.push_back(p);}Point pivot=mountain.back(),tail=pivot,head=pivot+Point{0,1};long double answer=0,pi=acosl(-1.0L);while(head.y>1e-11L){Point body=head-tail;long double h=distance(head,pivot),t=distance(tail,pivot),best=2*pi;Point contact;bool stop=false;auto angleTo=[&](Point d){long double angle=atan2l(cross(body,d),dot(body,d));if(angle<-1e-12L)angle+=2*pi;return max(0.0L,angle);};auto candidate=[&](Point p,bool headSide){if(p.y>=pivot.y-1e-11L)return;Point d=headSide?p-pivot:pivot-p;long double angle=angleTo(d);if(angle<best-1e-12L || (fabsl(angle-best)<=1e-12L && p.y<contact.y)){best=angle;contact=p;stop=false;}};if(h>1e-14L && pivot.y<=h+1e-12L){long double a=asinl(clamp(-pivot.y/h,-1.0L,1.0L));for(long double angle:{a,pi-a}){Point d={cosl(angle),sinl(angle)};long double turn=angleTo(d);if(turn<best){best=turn;stop=true;}}}for(int i=1;i<(int)mountain.size();i++){Point p=mountain[i];if(p.y<pivot.y-1e-11L){long double d=distance(p,pivot);if(d<=h+1e-12L)candidate(p,true);if(d<=t+1e-12L)candidate(p,false);}}for(int i=0;i+1<(int)mountain.size();i++){Point a=mountain[i],e=mountain[i+1]-a;for(auto [radius,headSide]:{pair<long double,bool>{h,true},{t,false}}){if(radius<1e-14L)continue;Point offset=a-pivot;long double A=dot(e,e),B=2*dot(e,offset),C=dot(offset,offset)-radius*radius,discriminant=B*B-4*A*C;if(discriminant<-1e-12L)continue;long double root=sqrtl(max(0.0L,discriminant));for(long double u:{(-B-root)/(2*A),(-B+root)/(2*A)})if(u>=-1e-12L && u<=1+1e-12L)candidate(a+e*clamp(u,0.0L,1.0L),headSide);}}answer+=h*best;head=pivot+rotated(head-pivot,best);tail=pivot+rotated(tail-pivot,best);if(stop)break;pivot=contact;}cout << fixed << setprecision(15) << answer;''',
        '不能只在山坡顶点换支点，身体端点落在边中间也会触发事件。不能把整条身体的转动角直接累加成头路程，必须乘当前头臂长度。题目保证端点接触远离坡顶，可避免端点与坡顶数值重合。',
        declarations=GEOMETRY+ROLLING,floating_output=True,complexity=r'设坡线总长L<2000，事件数 $O(n+L)$，总时间 $O(n(n+L))$，空间 $O(n)$。')


if __name__=='__main__':run()
