"""Winding, line-order swaps, reflected trajectories and longest polygon chords."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(232546,1200,['IEEE浮点数','NaN'],'无输入，给a,b让错误浮点SPJ对任意标准值接受。',
        '输出0 0。按该SPJ使用的常见IEEE浮点语义，浮点0/0得到NaN，fabs(NaN−ans)仍为NaN，而NaN与阈值做“>”比较结果为false，于是程序不会进入WA分支。这是该题给定裁判缺少有限性检查的演示；健全实现应先拒绝b=0及非有限值。',
        r'''cout << "0 0\n";''',
        '必须是浮点0/0；整数除0没有这个语义。题目要求输出两个整数，无需读入任何数据。',
        checker='nan-quotient-hack',cases=[{'input':'','output':'0 0'}],complexity=r'时间、空间均 $O(1)$。')
    put(232714,2000,['绕数','叉积'],'有向闭折线对查询点的逆时针绕数，路径上输出EDGE。',
        '先用叉积为0且点在线段包围范围内判断边界。否则沿查询点向右发射射线，边从点下方上穿时，若点在边左侧就把绕数加1；从上方向下穿且点在边右侧时减1。纵坐标端点采用半开条件，避免射线经过顶点重复计数。各边贡献相加可得到负数和绝对值大于1的绕数。',
        r'''int n;cin >> n;using P=pair<long long,long long>;vector<P> point(n);for(auto &[x,y]:point)cin >> x >> y;int q;cin >> q;while(q--){long long x,y;cin >> x >> y;int winding=0;bool boundary=false;for(int i=0;i<n;i++){auto [ax,ay]=point[i];auto [bx,by]=point[(i+1)%n];__int128 cross=(__int128)(bx-ax)*(y-ay)-(__int128)(by-ay)*(x-ax);if(cross==0 && min(ax,bx)<=x && x<=max(ax,bx) && min(ay,by)<=y && y<=max(ay,by)){boundary=true;break;}if(ay<=y && by>y && cross>0)winding++;if(ay>y && by<=y && cross<0)winding--;}if(boundary)cout << "EDGE\n";else cout << winding << '\n';}''',
        '这不是只输出内外的奇偶规则，自交折线可绕多圈。坐标达10^9，叉积中间使用128位。',
        complexity=r'时间 $O(nm)$，空间 $O(n)$。')
    put(220444,2000,['直线交点','离线排序'],'沿线坐火车，问某风车第k次与别风车交换视角顺序时的位置。',
        '两个风车在视角中交换顺序，当且仅当观察者经过它们连线与火车路线的交点。对每对风车求交点在S+t(T−S)上的参数t，只保留0<t<1的事件，分别加入两个风车事件表，排序后第k项就是答案。所有风车在路线同侧，避免经过观察方向反面等额外顺序变化；无三点共线保证同一风车的交换时刻不重合。',
        r'''int n,m;cin >> n >> m;Point start,finish;cin >> start.x >> start.y >> finish.x >> finish.y;Point direction=finish-start;vector<Point> point(n);for(auto &p:point)cin >> p.x >> p.y;vector<vector<long double>> event(n);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){Point edge=point[j]-point[i];long double denominator=cross(direction,edge);if(fabsl(denominator)<EPS)continue;long double t=cross(point[i]-start,edge)/denominator;if(t>0 && t<1){event[i].push_back(t);event[j].push_back(t);}}for(auto &row:event)sort(row.begin(),row.end());cout << fixed << setprecision(12);while(m--){int h,k;cin >> h >> k;h--;if(k>(int)event[h].size())cout << -1 << '\n';else{Point answer=start+direction*event[h][k-1];cout << answer.x << ' ' << answer.y << '\n';}}''',
        '直线交点必须位于实际行程线段内。平行风车连线不会交换顺序。',
        declarations=GEOMETRY,floating_output=True,complexity=r'时间 $O(n²\log n+m)$，空间 $O(n²)$。')
    put(232575,2300,['简单多边形','直线截面','扫描线'],'简单多边形内最长直线段，允许沿边界。',
        '最优跑道所在直线可取经过两个多边形顶点，但两端不一定是顶点。理由是先延长到边界，再平移或旋转，在尚未碰到新顶点的局部区间中，总能朝不缩短的一侧推进，直至由两个顶点限制方向。因此枚举所有顶点对所定的完整直线，求它与闭多边形交集的最长连通区间。\n\n对固定直线，将所有顶点投影成参数t，并按叉积正负区分直线两侧。边两端是否严格在正侧不同，就产生一次半开穿越事件；排序后两两配对得到内部区间。与直线共线的多边形边另作为边界区间加入，最后合并相交或相接区间，保留最长真实长度。这既处理穿过顶点，也允许在凹顶点只接触边界。\n\n候选直线性质参见[2017 ICPC官方题解](https://icpc.global/worldfinals/problems/2017-ICPC-World-Finals/finals2017solutions.pdf)。',
        r'''int n;cin >> n;vector<Point> point(n);for(auto &p:point)cin >> p.x >> p.y;long double answer=0;for(int a=0;a<n;a++)for(int b=a+1;b<n;b++){Point origin=point[a],direction=point[b]-origin;long double squared=dot(direction,direction);vector<long double> parameter(n),side(n),events;vector<pair<long double,long double>> interval;for(int i=0;i<n;i++){parameter[i]=dot(point[i]-origin,direction)/squared;side[i]=cross(direction,point[i]-origin);}for(int i=0;i<n;i++){int j=(i+1)%n;if((side[i]>0)!=(side[j]>0)){long double t=(parameter[i]*side[j]-parameter[j]*side[i])/(side[j]-side[i]);events.push_back(t);}if(side[i]==0 && side[j]==0)interval.push_back(minmax(parameter[i],parameter[j]));}sort(events.begin(),events.end());for(int i=1;i<(int)events.size();i+=2)interval.push_back({events[i-1],events[i]});sort(interval.begin(),interval.end());bool active=false;long double left=0,right=0;for(auto [l,r]:interval){if(!active || l>right+1e-12L){if(active)answer=max(answer,(right-left)*sqrtl(squared));left=l;right=r;active=true;}else right=max(right,r);}if(active)answer=max(answer,(right-left)*sqrtl(squared));}cout << fixed << setprecision(12) << answer;''',
        '不能只求顶点间合法对角线，最长段的端点可能都落在边内部。凹多边形截面可不连通，不能直接取最外两个交点。',
        declarations=GEOMETRY,floating_output=True,complexity=r'时间 $O(n³\log n)$，空间 $O(n)$。')
    put(209385,1800,['几何不变量','叉积','镜像判别'],'固定20点手掌多边形可旋转平移且正反序输入，判左右手。',
        '图形不缩放，掌底有唯一长度9的边，它的一端邻边长8，另一端邻边长6。把长9边规范定向为“朝长8邻边端”，再看该端转向长8边的叉积。给定右手模板中从(1,0)到(10,0)，再到(10,8)，叉积为正；镜像左手为负。旋转平移保留这个符号，反序输入通过规范定向消除。',
        r'''int tests;cin >> tests;while(tests--){vector<Point> p(20);for(auto &v:p)cin >> v.x >> v.y;bool right=false;for(int i=0;i<20;i++){int j=(i+1)%20;if(fabsl(dot(p[j]-p[i],p[j]-p[i])-81)>1e-3L)continue;int after=(j+1)%20,before=(i+19)%20;if(fabsl(dot(p[after]-p[j],p[after]-p[j])-64)<1e-3L)right=cross(p[j]-p[i],p[after]-p[j])>0;else right=cross(p[i]-p[j],p[before]-p[i])>0;break;}cout << (right?"right\n":"left\n");}''',
        '仅计算多边形有向面积会受输入顺逆时针影响，不能直接据此判断左右。长度比较用容差应对六位小数坐标。',
        declarations=GEOMETRY,complexity=r'每组时间、空间均 $O(20)$。')
    put(232545,2300,['反射展开','三角网格','二分时间'],'等边三角形内弹性反射，小球第k次撞边的时间。',
        '把每次反射改为把三角形沿边镜像展开，小球便始终沿原速度直线走。平面铺成等边三角网格，撞边对应穿越三族平行网格线。设H=√3L/2，三个归一化坐标为u=y/H、v=x/L+y/(√3L)+1/2、w=−x/L+y/(√3L)+1/2；它们各自等于整数时位于相应族网格线。\n\n每个坐标都是a+b*t。若b<0先整体取反，使b为正，则t时刻前穿线数为floor(a+b*t)−floor(a)。三族相加就是撞击数，题目保证前k次没有顶点重合事件，故不重复计数。倍增时间上界，再二分最小使穿线数≥k的时间，避免逐次模拟百万次碰撞。',
        r'''int tests;cin >> tests;cout << fixed << setprecision(12);while(tests--){long double length,x,y,vx,vy;long long k;cin >> length >> x >> y >> vx >> vy >> k;long double root=sqrtl(3.0L);array<long double,3> initial={2*y/(root*length),x/length+y/(root*length)+0.5L,-x/length+y/(root*length)+0.5L};array<long double,3> speed={2*vy/(root*length),vx/length+vy/(root*length),-vx/length+vy/(root*length)};for(int i=0;i<3;i++)if(speed[i]<0){speed[i]=-speed[i];initial[i]=-initial[i];}auto count=[&](long double t){long long result=0;for(int i=0;i<3;i++)if(speed[i]>0){long double value=floorl(initial[i]+speed[i]*t)-floorl(initial[i]);if(value>=k)return k;result+=(long long)value;if(result>=k)return k;}return result;};long double low=0,high=1;while(count(high)<k)high*=2;for(int iteration=0;iteration<100;iteration++){long double mid=(low+high)/2;if(count(mid)>=k)high=mid;else low=mid;}cout << high << '\n';}''',
        '横向撞线只是一族，必须加上两族斜线。小球半径10^−1000在此精度下按点处理；前k次无双边同时碰撞是计数前提。',
        floating_output=True,complexity=r'每组时间 $O(\log T+100)$，空间 $O(1)$。')
    put(232532,1500,['凸组合','点在三角形内'],'三瓶浓度按非负比例混合，查询能否得到目标两维浓度。',
        '混合浓度是三个浓度点按体积比例的凸组合，因此目标能配出当且仅当在三点凸包中。非共线时用三条边叉积同号或0判断三角形内部含边界；共线时凸包为线段，检查点是否在任意一对端点的闭线段上，也支持三瓶完全相同。',
        r'''array<Point,3> a;for(auto &p:a)cin >> p.x >> p.y;long double area=cross(a[1]-a[0],a[2]-a[0]);int n;cin >> n;while(n--){Point p;cin >> p.x >> p.y;bool ok=false;if(area==0){for(int i=0;i<3;i++){Point x=a[i],y=a[(i+1)%3];if(cross(y-x,p-x)==0 && dot(p-x,p-y)<=0)ok=true;}}else{long double x=cross(a[1]-a[0],p-a[0]),y=cross(a[2]-a[1],p-a[1]),z=cross(a[0]-a[2],p-a[2]);ok=(x>=0 && y>=0 && z>=0)||(x<=0 && y<=0 && z<=0);}cout << (ok?"YES\n":"NO\n");}''',
        '可以不使用某瓶，故边界可行。不能随意加入纯水；只有给定三瓶的凸组合可用。',
        declarations=GEOMETRY,complexity=r'每问时间 $O(1)$，空间 $O(1)$。')
    put(232808,1700,['极角排序','叉积'],'按arg从−π到π排序，负x轴算π，原点算0。',
        '先按四个连续角区分组：y<0；y=0且x≥0（含原点）；y>0；y=0且x<0。组内非共线时叉积>0者在前，同方向用输入编号打破平局。这样完全避免atan2精度，并把负x轴放在最后、原点与正x轴放在0角。',
        r'''int n;cin >> n;struct P{long long x,y;int id;};vector<P> point(n);for(int i=0;i<n;i++){cin >> point[i].x >> point[i].y;point[i].id=i;}auto part=[](const P &p){if(p.y<0)return 0;if(p.y==0 && p.x>=0)return 1;if(p.y>0)return 2;return 3;};sort(point.begin(),point.end(),[&](auto a,auto b){int x=part(a),y=part(b);if(x!=y)return x<y;__int128 value=(__int128)a.x*b.y-(__int128)a.y*b.x;if(value)return value>0;return a.id<b.id;});for(auto p:point)cout << p.x << ' ' << p.y << '\n';''',
        '原点没有天然方向，题目指定arg=0，不能让它参与一般半平面叉积比较而破坏严格弱序。',
        checker='argument-order',complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')


if __name__=='__main__':run()
