"""Convex enclosure, integer diameter, support queries and Minkowski sums."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY,HULL,INTEGER,SUPPORT,MINKOWSKI_REAL


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(233135,1700,['凸包','周长'],'最短围栏包含所有点，支持单点及共线退化。',
        '包含全部点的最短闭合围栏就是凸包边界。按x、y排序，用单调链维护连续左转，删除内点和边上中间点，得到逆时针凸包。累加环上相邻距离。单点周长0，两点或全共线时凸包只剩两端，闭合周长为线段往返长度。',
        r'''int n;cin >> n;vector<Point> p(n);for(auto &a:p)cin >> a.x >> a.y;auto hull=convexHull(p);long double answer=0;for(int i=0;i<(int)hull.size();i++)answer+=distance(hull[i],hull[(i+1)%hull.size()]);cout << fixed << setprecision(12) << answer;''',
        '输入是实数，不能截断成整数。点重复先去重；两点答案是距离的2倍，与题目样例一致。',
        declarations=GEOMETRY+HULL,floating_output=True,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(233136,2100,['凸包直径','旋转卡壳'],'求最远点对距离平方，坐标可达2^31。',
        '最远点对都在凸包上。对每条凸包边，沿凸包移动对踵点j，直到它到该边的有向面积不再增大；j全程单调绕行，每条边只检查两端与j的距离，再在面积相等时检查j+1。两点退化直接求平方。\n\n坐标差可能达到2^32，两个平方相加可达2^65，连无符号64位也不够。叉积、平方距离及输出全部使用128位整数。',
        r'''int n;cin >> n;vector<IPoint> p(n);for(auto &a:p)cin >> a.x >> a.y;auto h=integerHull(p);int m=h.size();Wide answer=0;auto squared=[](IPoint a,IPoint b){return dot(a-b,a-b);};if(m==2)answer=squared(h[0],h[1]);else if(m>2){int j=1;for(int i=0;i<m;i++){int next=(i+1)%m;auto area=[&](int k){return absolute(cross(h[next]-h[i],h[k]-h[i]));};while(area((j+1)%m)>area(j))j=(j+1)%m;answer=max({answer,squared(h[i],h[j]),squared(h[next],h[j])});if(area((j+1)%m)==area(j))answer=max({answer,squared(h[i],h[(j+1)%m]),squared(h[next],h[(j+1)%m])});}}printWide(answer);''',
        '输出平方，无需开方。求凸包时也使用128位叉积，否则极大坐标的边界就可能先算错。',
        declarations=INTEGER,cases=[{'input':'2\n-2147483648 -2147483648\n2147483648 2147483648','output':'36893488147419103232'}],
        complexity=r'时间 $O(n\log n)$，卡壳 $O(n)$，空间 $O(n)$。')
    put(232791,2300,['凸包','旋转卡壳','最小外接矩形'],'求覆盖全部点的最小矩形面积。',
        '最优矩形至少一边与凸包边平行，枚举凸包边方向e。沿e投影的最大最小差为长，沿垂线投影差为宽。凸包都在有向边左侧，垂线最小投影为该边所在直线，只需最远点；另外维护沿e投影最大、最小的两个支撑点。\n\n边方向绕凸包旋转时三支撑点都单调前进，用旋转卡壳求投影差，面积=(maxDot−minDot)*maxCross/|e|²。无需归一化向量，也不输出此页未要求的矩形顶点。',
        r'''int n;cin >> n;vector<Point> p(n);for(auto &a:p)cin >> a.x >> a.y;auto h=convexHull(p);int m=h.size();if(m<3){cout << "0.000000000000";return 0;}int high=0,maximum=0,minimum=0;Point first=h[1]-h[0];for(int j=1;j<m;j++){if(cross(first,h[j]-h[0])>cross(first,h[high]-h[0]))high=j;if(dot(first,h[j])>dot(first,h[maximum]))maximum=j;if(dot(first,h[j])<dot(first,h[minimum]))minimum=j;}long double answer=1e100L;for(int i=0;i<m;i++){Point e=h[(i+1)%m]-h[i];auto area=[&](int j){return cross(e,h[j]-h[i]);};while(area((high+1)%m)>area(high)+EPS)high=(high+1)%m;while(dot(e,h[(maximum+1)%m])>dot(e,h[maximum])+EPS)maximum=(maximum+1)%m;while(dot(e,h[(minimum+1)%m])<dot(e,h[minimum])-EPS)minimum=(minimum+1)%m;long double value=(dot(e,h[maximum])-dot(e,h[minimum]))*area(high)/dot(e,e);answer=min(answer,value);}cout << fixed << setprecision(12) << answer;''',
        '矩形可任意旋转，不是轴平行包围盒。全共线时面积为0。',
        declarations=GEOMETRY+HULL,floating_output=True,complexity=r'时间 $O(n\log n)$，卡壳 $O(n)$，空间 $O(n)$。')
    put(233166,1800,['凸包','最小宽度'],'物体可旋转后直线通过，求最小平行带宽。',
        '所需是点集的最小宽度，只由凸包决定。最优一侧支撑线可沿凸包某条边；对每条边，宽度为所有凸包点到其所在直线的最大距离。n≤100，直接枚举边和点，取各宽度最小即可。',
        r'''int n;while(cin >> n && n){vector<Point> p(n);for(auto &a:p)cin >> a.x >> a.y;auto h=convexHull(p);long double answer=0;if(h.size()>2){answer=1e100L;for(int i=0;i<(int)h.size();i++){Point e=h[(i+1)%h.size()]-h[i];long double width=0;for(auto q:h)width=max(width,fabsl(cross(e,q-h[i]))/norm(e));answer=min(answer,width);}}cout << fixed << setprecision(12) << answer << '\n';}''',
        '此页修改版只输出高精度宽度，没有原WF版本的Case编号和向上取两位小数要求。',
        declarations=GEOMETRY+HULL,floating_output=True,complexity=r'每组时间 $O(n²+n\log n)$，空间 $O(n)$。')
    put(233137,2100,['凸多边形','运动相对坐标'],'公交车向左，行人只沿竖线以至多u速度过路，求最短安全时间。',
        '把车固定，行人相对位置为(vt,y)。若立刻全速走，轨迹满足t−y/u=0。对车每个顶点算r=x/v−y/u，凸性使整车的r范围为[minR,maxR]。若0不在开区间内，立刻走就安全，时间w/u；否则必须等到从车后绕过，至少补足maxR的延迟。\n\n等maxR后再全速即可实现总时间maxR+w/u。允许途中变速也不能更短：相对量t−y/u只能非减，要从凸障碍的后侧通过最终至少达到其最大r。边界接触不算撞，端点等号允许。',
        r'''int n;long double w,v,u;cin >> n >> w >> v >> u;long double minimum=1e100L,maximum=-1e100L;for(int i=0;i<n;i++){long double x,y;cin >> x >> y;long double r=x/v-y/u;minimum=min(minimum,r);maximum=max(maximum,r);}long double answer=w/u;if(minimum<0 && maximum>0)answer+=maximum;cout << fixed << setprecision(12) << answer;''',
        '车向负x移动，相对坐标要加vt。不能简单等车所有点都经过x=0，允许根据高度提前开始或贴边。',
        floating_output=True,complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(233186,2200,['闵可夫斯基和','凸多边形距离'],'两个分离凸岛，求边界最短距离。',
        '两集合距离=min|a−b|，所有差向量组成凸多边形C=A+(−B)，即闵可夫斯基和。将两多边形统一成逆时针凸包，从最低顶点开始，按边方向合并；同向边相加，线性构造差多边形。若原点在C内则距离0，否则取原点到C各边线段的最短距离。\n\n点到线段用投影参数t=−a·(b−a)/|b−a|²，截到[0,1]后求|a+t(b−a)|。',
        r'''int n,m;while(cin >> n >> m && (n||m)){vector<Point> a(n),b(m);for(auto &p:a)cin >> p.x >> p.y;for(auto &p:b){cin >> p.x >> p.y;p=p*(-1);}auto c=minkowski(convexHull(a),convexHull(b));long double answer=1e100L;bool inside=c.size()>=3;for(int i=0;i<(int)c.size();i++){Point x=c[i],y=c[(i+1)%c.size()],e=y-x;if(cross(e,x*(-1))<-EPS)inside=false;long double t=dot(e,e)>0?-dot(x,e)/dot(e,e):0;t=max(0.0L,min(1.0L,t));answer=min(answer,norm(x+e*t));}if(inside)answer=0;cout << fixed << setprecision(12) << answer << '\n';}''',
        '岛屿顶点输入可能顺时针，先重新求凸包统一方向。点间最短距离不一定发生在两个顶点，必须考虑点到边。',
        declarations=GEOMETRY+HULL+MINKOWSKI_REAL,floating_output=True,complexity=r'含规范化凸包时间 $O(n\log n+m\log m)$，和及距离扫描 $O(n+m)$，空间 $O(n+m)$。')
    put(233737,1900,['凸多边形点包含','二分'],'任意简单多边形B是否严格在凸多边形A内。',
        '凸集包含所有顶点就包含连接它们的全部边与内部，所以只需检查B每个顶点严格在A内。把A改成逆时针，从A[0]扇形划分三角形：先检查两端射线，再二分定位查询点所在扇区，最后检查扇区外边的叉积严格为正。碰到任何边或顶点均返回否。',
        r'''int n;cin >> n;vector<IPoint> a(n);for(auto &p:a)cin >> p.x >> p.y;reverse(a.begin(),a.end());int m;cin >> m;bool ok=true;while(m--){IPoint p;cin >> p.x >> p.y;if(!insideConvex(a,p,true))ok=false;}cout << (ok?"YES":"NO");''',
        'A严格凸而B不一定凸；无需给B再做复杂边相交检查。严格包含时叉积0也不合格。',
        declarations=INTEGER+SUPPORT,complexity=r'时间 $O(n+m\log n)$，空间 $O(n)$。')
    put(233738,2200,['凸包支撑点','在线查询'],'每条直线是否把所有房屋分成两非空侧，要求读下条前输出。',
        '线段方向e，法向量d=(−e.y,e.x)，房屋侧别由dot(d,P)−dot(d,A)决定。极值只需在凸包上求最大、最小投影。为逆时针凸包每条边计算外法向量，按极角排序；查询d在法向量序中lower_bound，对应边的起点就是最大投影顶点，−d同理求最小。\n\n比较投影范围是否跨过直线常数，跨过输出BAD，否则GOOD。全部比较用128位，不通过atan2判断近乎平行方向。每问用endl刷新，满足在线输出要求。',
        r'''int n;cin >> n;vector<IPoint> p(n);for(auto &a:p)cin >> a.x >> a.y;auto hull=integerHull(p);Support support(hull);IPoint a,b;while(cin >> a.x >> a.y >> b.x >> b.y){if(hull.empty()){cout << "GOOD" << endl;continue;}IPoint e=b-a,d={-e.y,e.x},negative={-d.x,-d.y};Wide high=dot(hull[support.index(d)],d),low=dot(hull[support.index(negative)],d),constant=dot(a,d);cout << ((low>constant || high<constant)?"GOOD":"BAD") << endl;}''',
        '题目保证道路不经过房屋，因此不需给等号指定其他语义。n=0时无两侧分割，输出GOOD。',
        declarations=INTEGER+SUPPORT,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n)$。')
    put(233985,2200,['闵可夫斯基和','凸多边形点包含'],'三凸城各选一祭坛，其等质量重心能否在查询山丘。',
        '重心q=(a+b+c)/3可行，当且仅当3q属于三个城市的闵可夫斯基和A+B+C。凸多边形和可按边向量极角线性合并，同方向向量相加；从各自最低顶点之和出发即可得到新凸包。先合并三城，再对3倍山丘坐标做含边界的凸多边形二分包含判断。',
        r'''vector<IPoint> sum;for(int t=0;t<3;t++){int n;cin >> n;vector<IPoint> p(n);for(auto &a:p)cin >> a.x >> a.y;if(!t)sum=p;else sum=minkowski(sum,p);}int m;cin >> m;while(m--){IPoint q;cin >> q.x >> q.y;q.x*=3;q.y*=3;cout << (insideConvex(sum,q,false)?"YES\n":"NO\n");}''',
        '祭坛可位于城市边界，包含判断允许叉积0。用3q避免除3产生浮点误差，坐标与叉积分别用64/128位。',
        declarations=INTEGER+SUPPORT,complexity=r'合并 $O(n_1+n_2+n_3)$，每问 $O(\log(n_1+n_2+n_3))$，空间同总顶点数。')
    put(233165,2300,['凸包切线','旋转投影','面积前缀和'],'已有k个点，加入一个候选点后最大凸包面积。',
        '先求已有点逆时针凸包及各边叉积前缀和。内点不改变面积；外点q会替换一段连续可见边，其中可见条件cross(edge,q−start)<0。用扇形二分找到一条可见边e。\n\n以e的内法向量求最远支撑顶点，它的两条相邻边至少一条不可见：若q在两边外侧，沿此支撑方向的投影必超过最远顶点，和q位于e外侧矛盾。于是得到一个可见、一个不可见边。可见边在环上连续，分别沿两条弧二分找可见段首尾，得到两切点A、B。\n\n新二倍面积=旧二倍面积−可见边叉积和+cross(A,q)+cross(q,B)。前缀和使面积替换常数完成，每个候选只做对数次支撑与侧别判断。全部面积用128位，精确输出.0或.5。',
        r'''int n,k;cin >> n >> k;vector<IPoint> p(n);for(auto &a:p)cin >> a.x >> a.y;auto hull=integerHull(vector<IPoint>(p.begin(),p.begin()+k));int h=hull.size();Support support(hull);vector<Wide> prefix(2*h+1);for(int i=0;i<2*h;i++)prefix[i+1]=prefix[i]+cross(hull[i%h],hull[(i+1)%h]);Wide base=prefix[h],answer=base;for(int i=k;i<n;i++){IPoint q=p[i];int visible=visibleEdge(hull,q);if(visible<0)continue;auto side=[&](int edge){return cross(hull[(edge+1)%h]-hull[edge],q-hull[edge]);};IPoint e=hull[(visible+1)%h]-hull[visible],normal={-e.y,e.x};int vertex=support.index(normal),hidden=side(vertex)>0?vertex:(vertex+h-1)%h;int distance=(hidden-visible+h)%h,low=0,high=distance;while(high-low>1){int mid=(low+high)/2;if(side((visible+mid)%h)<0)low=mid;else high=mid;}int end=(visible+low)%h;distance=(visible-hidden+h)%h;low=0;high=distance;while(high-low>1){int mid=(low+high)/2;if(side((hidden+mid)%h)>0)low=mid;else high=mid;}int start=(hidden+high)%h,count=(end-start+h)%h+1;Wide removed=prefix[start+count]-prefix[start];Wide area=base-removed+cross(hull[start],q)+cross(q,hull[(end+1)%h]);answer=max(answer,area);}printWide(answer/2);cout << (answer%2?".5":".0");''',
        '无三点共线保证候选不会恰好落在某凸包边延长线上，侧别二分无零值歧义。不能只取离某一个点最远的候选。',
        declarations=INTEGER+SUPPORT,complexity=r'时间 $O(k\log k+(n-k)\log k)$，空间 $O(n+k)$。')
    put(233145,2300,['期望线性性','凸多边形截线','周长前缀和'],'外凸多边形边界随机放灯，内凸多边形被照亮周长期望。',
        '固定内多边形的一条逆时针边AB，外部光源在其右侧时这条边整条可见，在左侧时被内多边形挡住。因此该边期望贡献=边长*外边界位于其右半平面的长度/外周长，各边线性相加。\n\nAB所在直线穿过外多边形内部，边界恰分为左右两条连续弧。用法向量支撑查询找到正侧、负侧极值顶点，再分别在两条顶点链上二分符号变化，得到两个交点所在边及线性插值位置。外周长前缀和将交点间右侧弧长化为常数求和。整数叉积判断侧别，只有交点比例与周长用long double。',
        r'''int n,m;cin >> n >> m;vector<IPoint> outer(n),inner(m);for(auto &p:outer)cin >> p.x >> p.y;for(auto &p:inner)cin >> p.x >> p.y;Support support(outer);vector<long double> length(n),prefix(n+1);for(int i=0;i<n;i++){auto e=outer[(i+1)%n]-outer[i];length[i]=sqrtl((long double)dot(e,e));prefix[i+1]=prefix[i]+length[i];}long double perimeter=prefix[n],answer=0;for(int i=0;i<m;i++){IPoint a=inner[i],e=inner[(i+1)%m]-a,normal={-e.y,e.x},negative={e.y,-e.x};int positive=support.index(normal),minus=support.index(negative);auto side=[&](int vertex){return cross(e,outer[vertex]-a);};auto crossing=[&](int start,int finish,bool sign){int low=0,high=(finish-start+n)%n;while(high-low>1){int mid=(low+high)/2;if((side((start+mid)%n)>=0)==sign)low=mid;else high=mid;}int u=(start+low)%n,v=(u+1)%n;Wide su=side(u),sv=side(v);long double ratio=(long double)su/(long double)(su-sv);return prefix[u]+ratio*length[u];};long double enter=crossing(positive,minus,true),leave=crossing(minus,positive,false),arc=leave-enter;if(arc<0)arc+=perimeter;answer+=sqrtl((long double)dot(e,e))*arc/perimeter;}cout << fixed << setprecision(15) << answer;''',
        '光源按外边界弧长均匀，不是外顶点均匀。内边整条可见与否由其支撑直线侧别决定，无需逐点数值积分。',
        declarations=INTEGER+SUPPORT,floating_output=True,complexity=r'预处理 $O(n\log n)$，全部内边 $O(m\log n)$，空间 $O(n+m)$。')


if __name__=='__main__':run()
