from core7_completion import add, BIG, DSU

POW = r'''
long long power(long long a,long long b,long long mod){long long r=1;for(;b;b>>=1,a=a*a%mod)if(b&1)r=r*a%mod;return r;}
'''

HULL=r'''
struct Point{long long x,y;bool operator==(const Point&o)const{return x==o.x&&y==o.y;}};
__int128 cross(Point a,Point b,Point c){return (__int128)(b.x-a.x)*(c.y-a.y)-(__int128)(b.y-a.y)*(c.x-a.x);}
vector<Point>hull(vector<Point>a,bool keep=false){sort(a.begin(),a.end(),[](Point a,Point b){return tie(a.x,a.y)<tie(b.x,b.y);});a.erase(unique(a.begin(),a.end()),a.end());if(a.size()<3)return a;if(keep){bool line=true;for(auto p:a)if(cross(a[0],a[1],p)!=0)line=false;if(line)return a;}vector<Point>h;for(auto p:a){while(h.size()>=2&&(keep?cross(h[h.size()-2],h.back(),p)<0:cross(h[h.size()-2],h.back(),p)<=0))h.pop_back();h.push_back(p);}int lower=h.size();for(int i=(int)a.size()-2;i>=0;i--){auto p=a[i];while((int)h.size()>lower&&(keep?cross(h[h.size()-2],h.back(),p)<0:cross(h[h.size()-2],h.back(),p)<=0))h.pop_back();h.push_back(p);}h.pop_back();return h;}
'''

add('UVA675','严格凸包与原输入中的首个凸包顶点',
    '按坐标排序求严格凸包，再在原输入顺序中寻找第一个凸包顶点，把凸包旋转到这里开始，逆时针输出并重复起点闭合。',
    '单调链先构造上下凸壳：若加入新点使最后一次转向不是逆时针，就删除中间点，直到恢复凸性。叉积为零的中间点也删除，确保输出转角严格小于一百八十度。\n\n凸包构造后的起点通常是坐标最小点，但本题要求使用原输入序列中第一个属于凸包顶点的点。保留原顺序，逐个查找它是否出现在凸包顶点列表，再旋转列表，保持原有逆时针方向。\n\n输入以空行分隔多组，坐标带逗号；每组末尾可能重复起点，排序去重时自然消除。输出再次在末尾重复起点，多组之间留空行。格式按 [UVA 原始题面](https://onlinejudge.org/external/6/675.pdf) 核对。',
    '时间 O(n log n+n·h)，空间 O(n)，h 为凸包点数。','按原输入挑起点；逆时针；重复首点闭合；组间空行。',r'''
vector<Point>points;bool first=true;auto output=[&](){if(points.empty())return;auto h=hull(points);int start=0;for(auto p:points){auto it=find(h.begin(),h.end(),p);if(it!=h.end()){start=it-h.begin();break;}}rotate(h.begin(),h.begin()+start,h.end());if(!first)cout<<'\n';first=false;for(int i=0;i<=(int)h.size();i++){auto p=h[i%h.size()];cout<<p.x<<", "<<p.y<<'\n';}points.clear();};string line;while(getline(cin,line)){if(line.find_first_not_of(" \t\r")==string::npos){output();continue;}for(char &c:line)if(c==',')c=' ';stringstream input(line);Point p;if(input>>p.x>>p.y)points.push_back(p);}output();
''',HULL)

add('UVA681','凸包后旋转到最低最左点',
    '用单调链求严格凸包，旋转到 y 最小、并列时 x 最小的点，逆时针输出。计数包括末尾重复起点，组间按输入协议输出 -1。',
    '原轮廓可能凹陷，但最小凸围栏只保留凸包顶点。按坐标排序后分别扫描下壳与上壳，利用叉积弹掉非凸和共线中间点，得到逆时针边界。\n\n本题起点选择与普通按 x 排序的凸包不同：必须取 y 最小、并列 x 最小者，所以在凸包上再找这个点并旋转列表。旋转不改变顺序和凸性。\n\n原始每组点数已经包含闭合重复点，构造时去重；输出点数则为真正顶点数加一，并再次打印首点。首行输出总组数，组间使用 −1 分隔。详见 [UVA 原始格式](https://onlinejudge.org/external/6/681.pdf)。',
    '时间 O(n log n)，空间 O(n)。','最低 y 优先；点数含闭合重复点；仅组间有 -1。',r'''
int tests;cin>>tests;cout<<tests<<'\n';for(int test=0;test<tests;test++){int n;cin>>n;vector<Point>a(n);for(auto &p:a)cin>>p.x>>p.y;auto h=hull(a);int start=min_element(h.begin(),h.end(),[](Point a,Point b){return tie(a.y,a.x)<tie(b.y,b.x);})-h.begin();rotate(h.begin(),h.begin()+start,h.end());cout<<h.size()+1<<'\n';for(int i=0;i<=(int)h.size();i++)cout<<h[i%h.size()].x<<' '<<h[i%h.size()].y<<'\n';if(test+1<tests){int delimiter;cin>>delimiter;cout<<-1<<'\n';}}
''',HULL)

add('UVA1303','凸包平行边加一整圈圆弧',
    '先求城堡顶点凸包的周长，再加上安全距离 L 的一整圈圆周长 2πL。凸包每条边平移不改变长度，各拐角圆弧的转角之和为 2π。',
    '围墙需要围住城堡且保持至少 L 的距离，最短围墙可看成凸包向外扩张 L 后的边界。原来凹陷处无需跟着凹进去，直接拉直只会更短且仍满足包围。\n\n沿凸包每条边向外平移 L，平移后的直线段长度与原边相同。在相邻边之间，用半径为 L 的圆弧连接；所有外转角之和正好为一整圈，所以圆弧总长为 2πL。于是答案是凸包周长加上这个圆周长。\n\n采用单调链求凸包后闭合累加边长，最后按要求四舍五入为整数。输入开头有测试组数，组间输出空行；格式由 [UVA 原始 PDF](https://onlinejudge.org/external/13/1303.pdf) 核对。',
    '时间 O(n log n)，空间 O(n)。','不能直接使用凹多边形原周长；圆弧加一整圈；输出整数并保留组间空行。',r'''
int tests;cin>>tests;for(int test=0;test<tests;test++){int n;long long radius;cin>>n>>radius;vector<Point>a(n);for(auto &p:a)cin>>p.x>>p.y;auto h=hull(a);long double perimeter=2*acosl(-1.0L)*radius;for(int i=0;i<(int)h.size();i++){auto a=h[i],b=h[(i+1)%h.size()];perimeter+=hypotl(a.x-b.x,a.y-b.y);}if(test)cout<<'\n';cout<<llround(perimeter)<<'\n';}
''',HULL)

add('UVA11626','保留凸包边上的全部指定点',
    '筛出标记 Y 的点，构造保留共线边界点的凸包。叉积为负才弹出，等于零时保留，按最左且最低点开始逆时针输出。',
    '输入已给出点是否属于凸包边界的标记，N 点无需保留；Y 点即使位于一条边中间，也必须全部输出。\n\n普通严格凸包会在叉积为零时弹出中间点，本题应把这个条件改为仅在叉积为负时弹出。这样同一条边上的点按行进方向依次出现。上下壳连接时去掉重复端点，起点自然是 x 最小、并列 y 最小者。\n\n如果全部 Y 点共线，通用上下壳会把中间点重复打印，故单独检测并直接输出排序后的点。其它情况，每个边界点恰好出现在一侧凸壳中。',
    '时间 O(n log n)，空间 O(n)。','保留共线边界点；先过滤 N；全共线时只输出一次。',r'''
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<Point>a;for(int i=0;i<n;i++){Point p;char c;cin>>p.x>>p.y>>c;if(c=='Y')a.push_back(p);}auto h=hull(a,true);cout<<h.size()<<'\n';for(auto p:h)cout<<p.x<<' '<<p.y<<'\n';}
''',HULL)

add('P2180','压缩为满矩形加一条未满边',
    '行列压缩后，同一列的石子可以尽量对齐。最优形状可取一个满矩形，再在一行或一列上放剩余石子。枚举满列高度 h，令 q=K/h、r=K%h，贡献为 C(h,2)C(q,2)+qC(r,2)，再交换两维检查。',
    '任意两列贡献的矩形数等于它们共有石子行中任取两行的数量。把各列石子向同一侧对齐，会使共有行数达到两列高度的较小值，矩形数不会减少；行方向也可做同样压缩。\n\n压缩后的边界呈阶梯。对相邻未满部分进行石子转移时，矩形数随转移量是凸的二次式，因此极值可以向端点推进，直至某一部分填满或清空。反复整理，最优可在“满矩形加一行或一列”的形状中取得。两个方向都要枚举。\n\n固定满列高度 h，q 个满列各有 h 枚石子，另有 r 枚在一个短列。两个满列选两行贡献 C(h,2)，满列对数为 C(q,2)；短列与每个满列共有 r 行，额外贡献 qC(r,2)。检查 q 不超过可用列数，若 r>0 还须有多余一列。\n\nK=0 或不足组成一个矩形时，公式自然得到零。枚举 h 不超过相应维度，矩形计数使用 long long。',
    '时间 O(N+M)，空间 O(1)。','两个方向都检查；短列需要额外列位置；取两行两列，使用组合数。',r'''
long long n,m,k;cin>>n>>m>>k;auto choose2=[](long long x){return x*(x-1)/2;};long long answer=0;for(int direction=0;direction<2;direction++){for(long long h=1;h<=n;h++){long long q=k/h,r=k%h;if(q>m||(r&&q==m))continue;answer=max(answer,choose2(h)*choose2(q)+q*choose2(r));}swap(n,m);}cout<<answer<<'\n';
''')

add('P2924','最左顶点固定后的凸链 DP',
    '枚举凸多边形最左最低顶点，把右侧点按极角排序。dp[i][j] 记录凸链最后两点时的最多顶点数；转移要求下一次转向严格逆时针。对固定中点，将前驱方向排序，半圆窗口维护最大 dp，避免逐个枚举三元组。',
    '任何凸多边形都有唯一的字典序最小顶点，枚举它作为起点后，其它顶点都在右半平面，可以按相对起点的极角依次访问。凸性只需检查连续三点严格左转；首尾与起点处的转向由极角次序自动保证。\n\n令 dp[i][j] 表示从起点出发，以 i、j 为最后两点的最长凸链顶点数。要接上 k，要求 cross(j−i,k−j)>0，等价于从 j 看，前驱 i 的方向位于后继 k 方向逆时针旋转零到一百八十度之间。起点作为特殊前驱时，当前链有两个顶点。\n\n固定中间点 j，把所有前驱方向按角度排序并复制一圈，再将后继查询也按方向排序。每个查询需要在一个长度为半圈的开区间中取最大链长。随着查询角度递增，区间两端单调移动，用单调队列维护最大值，每个前驱只加入、删除常数次。\n\n由此每个起点的每个中点处理 O(n log n)，总计 O(n³ log n)，而非直接四重枚举。原题保证无三点共线，所以半圆端点没有需要猜测的共线取舍。每次成功扩展都形成一条更长凸链，同时更新全局答案。',
    '时间 O(n³ log n)，空间 O(n²)。','按最左最低点枚举且只取其后点；转向必须严格为正；角度区间复制一圈处理跨零。',r'''
int n;cin>>n;vector<Point>points(n);for(auto &p:points)cin>>p.x>>p.y;sort(points.begin(),points.end(),[](Point a,Point b){return tie(a.x,a.y)<tie(b.x,b.y);});const long double pi=acosl(-1.0L);auto angle=[&](Point a,Point b){long double v=atan2l(b.y-a.y,b.x-a.x);if(v<0)v+=2*pi;return v;};int answer=min(n,2);for(int start=0;start+2<n;start++){Point root=points[start];vector<Point>a(points.begin()+start+1,points.end());sort(a.begin(),a.end(),[&](Point x,Point y){return cross(root,x,y)>0;});int count=a.size();vector<vector<int>>dp(count,vector<int>(count));for(int middle=0;middle+1<count;middle++){vector<pair<long double,int>>previous={{angle(a[middle],root),2}};for(int i=0;i<middle;i++)if(dp[i][middle])previous.push_back({angle(a[middle],a[i]),dp[i][middle]});sort(previous.begin(),previous.end());int size=previous.size();for(int i=0;i<size;i++)previous.push_back({previous[i].first+2*pi,previous[i].second});vector<pair<long double,int>>queries;for(int k=middle+1;k<count;k++)queries.push_back({angle(a[middle],a[k]),k});sort(queries.begin(),queries.end());deque<int>queue;int l=0,r=0;for(auto [theta,k]:queries){while(r<(int)previous.size()&&previous[r].first<theta+pi){while(!queue.empty()&&previous[queue.back()].second<=previous[r].second)queue.pop_back();queue.push_back(r++);}while(l<r&&previous[l].first<=theta)l++;while(!queue.empty()&&queue.front()<l)queue.pop_front();if(!queue.empty()){dp[middle][k]=previous[queue.front()].second+1;answer=max(answer,dp[middle][k]);}}}}cout<<answer<<'\n';
''',HULL)

add('CF1151E','每个区间的连通块数等于点数减边数',
    '把保留下来的位置看作原路径图的顶点，连续段数等于保留点数减相邻保留边数。交换对值域区间的求和，值 x 的点贡献 x(n−x+1)，相邻值 u,v 的边贡献 min(u,v)(n−max(u,v)+1)。',
    '固定值域区间 [l,r]，只保留值落在其中的位置，原下标相邻且都保留的位置之间连边。这是路径图的一个森林，每个连通块恰好是一段，块数等于顶点数减边数。\n\n对所有 [l,r] 求和时，固定一个值为 x 的位置。要保留它，l 可以从 1 到 x 选择，r 可以从 x 到 n 选择，贡献 x(n−x+1)。\n\n固定两个相邻位置，值为 u、v。要同时保留，左界不超过较小值，右界不小于较大值，因此这条边被计入 min(u,v)(n−max(u,v)+1) 个区间。把所有点贡献加上、边贡献减去，就是答案。重复值与同一值出现多段都自然处理。',
    '时间 O(n)，空间 O(n)，也可只保存前一个值降为空间 O(1)。','相邻关系来自原下标；点减边；乘积与总答案用 long long。',r'''
int n;cin>>n;vector<long long>a(n);long long ans=0;for(auto&x:a){cin>>x;ans+=x*(n-x+1);}for(int i=1;i<n;i++)ans-=min(a[i-1],a[i])*(n-max(a[i-1],a[i])+1);cout<<ans<<'\n';
''')

add('P1409','消去一整圈的自依赖概率',
    '令 P[n][m] 表示胜率。m>1 时，P[n][m]=P[n][m−1]/2+P[n−1][m−1]/3；队首胜率满足 P[n][1]=1/6+P[n][n]/2。把后一条代入整行递推，解出首项后顺次计算。',
    '你不在队首时，队首掷一的情况会使别人获胜，贡献零；他离队概率为三分之一，你变成 n−1 人中第 m−1 位；他转到队尾概率二分之一，你变成同一人数中第 m−1 位。于是得到行内递推。\n\n你在队首时，掷一立即获胜，概率六分之一；转到队尾后胜率为同一行的末项，乘二分之一；自己出队则贡献零。因此 P1=1/6+Pn/2。\n\n将各位置写成 Pm=am·P1+bm，初始 a1=1、b1=0，am=a(m−1)/2，bm=b(m−1)/2+上一人数行的 P(m−1)/3。先算出 an、bn，得到 P1=(1/6+bn/2)/(1−an/2)，再求整行。只有一个人时按题意必胜，不能继续投骰子。',
    '时间 O(n²)，空间 O(n)。','单人胜率为 1；转队尾不减少人数；出队与轮转概率分别为 1/3 和 1/2。',r'''
int n,m;cin>>n>>m;vector<double>previous(n+1),current(n+1),constant(n+1);previous[1]=1;for(int size=2;size<=n;size++){constant[1]=0;double coefficient=1;for(int position=2;position<=size;position++){coefficient*=0.5;constant[position]=constant[position-1]*0.5+previous[position-1]/3.0;}current[1]=(1.0/6+constant[size]*0.5)/(1-coefficient*0.5);for(int position=2;position<=size;position++)current[position]=current[position-1]*0.5+previous[position-1]/3.0;previous.swap(current);}cout<<fixed<<setprecision(9)<<previous[m]<<'\n';
''')

add('CF1768E','按至少需要几次操作累加',
    '每个排列至多需三次排序。总和等于 3(3n)!−1−A1−A2，其中 A1、A2 分别是至多一次、至多两次可排好的排列数。用两个排序次序的并集计数求 A2。',
    '设 f 是最少操作数，f∈{0,1,2,3}。把每个 f 写成三个阈值指示变量之和，则总和为 ((3n)!−1)+((3n)!−A1)+((3n)!−A2)。\n\n至多一次时，要么最后 n 个数已经固定，要么最前 n 个数已经固定，各有 (2n)! 种；交集仅中间 n 个数可排列，有 n! 种。所以 A1=2(2n)!−n!。\n\n连续两次相同操作没有意义，只需考虑先左后右与先右后左。先左后右成功，当且仅当最小 n 个数全在最初的前 2n 个位置，数量为 C(2n,n)·n!·(2n)!；反向同数。\n\n交集中，第一段 n 个位置不能含最大 n 个数，最后一段不能含最小 n 个数。设第一段含 x 个最小数，其余 n−x 个来自中间值，选择方式 C(n,x)²，第一段排列 n!。剩下的 n−x 个最小数必须在中段，中段还要从剩余 x 个中间值与 n 个大值中选 x 个，共 C(n+x,x) 种；中段与末段各有 n! 种排列。\n\n因此交集为 (n!)³Σ(x=0..n)C(n,x)²C(n+x,x)。两类数量相加减交集即 A2。三个交替排序确实足以排好所有排列，故阈值计数完整。阶乘预处理到 3n，所有运算使用输入的质数 M。',
    '时间 O(n+log M)，空间 O(n)。','A1、A2 都包含已经有序的排列；模数是输入 M；不是固定 998244353。',r'''
int n;long long mod;cin>>n>>mod;vector<long long>fact(3*n+1,1),inv(3*n+1,1);for(int i=1;i<=3*n;i++)fact[i]=fact[i-1]*i%mod;inv[3*n]=power(fact[3*n],mod-2,mod);for(int i=3*n;i;i--)inv[i-1]=inv[i]*i%mod;auto choose=[&](int a,int b){return fact[a]*inv[b]%mod*inv[a-b]%mod;};long long one=(2*fact[2*n]-fact[n]+mod)%mod,sum=0;for(int x=0;x<=n;x++){long long value=choose(n,x);sum=(sum+value*value%mod*choose(n+x,x))%mod;}long long intersection=fact[n]*fact[n]%mod*fact[n]%mod*sum%mod;long long two=(2*choose(2*n,n)%mod*fact[n]%mod*fact[2*n]%mod-intersection+mod)%mod;cout<<(3*fact[3*n]%mod-1-one-two+3*mod)%mod<<'\n';
''',POW)

add('P2789','按平行类大小划分直线',
    '没有三线共点时，每对不平行直线产生唯一交点。将直线按斜率分组，添加 k 条新平行线到已有 i 条线时增加 ik 个交点。布尔 DP 记录每种线数可达到的交点数。',
    '交点数量只受哪些线平行影响。不同平行类中的任意两线相交，且没有三线共点保证这些交点各不相同；同类内不相交。\n\n设 dp[i][s] 表示 i 条直线可以得到 s 个交点。再加入一组 k 条相互平行、且与已有所有线均不平行的新线，它们内部不产生交点，与原图增加 i·k 个交点，所以更新 dp[i+k][s+i·k]。\n\n每一种平行类划分都能按某个组序生成，所有生成结果也都能选择不同斜率实现；不必统计生成次数，只记录是否可达，重复划分不会影响答案。n<=25，最大交点数为 C(n,2)，直接枚举状态和新组大小即可。',
    '时间 O(n⁴)，空间 O(n³)，n<=25。','只问不同交点数量有几种；新组内部平行；不能把三线共点计为一种压缩方式。',r'''
int n;cin>>n;int maximum=n*(n-1)/2;vector<vector<char>>dp(n+1,vector<char>(maximum+1));dp[0][0]=1;for(int i=0;i<n;i++)for(int s=0;s<=maximum;s++)if(dp[i][s])for(int k=1;i+k<=n;k++)dp[i+k][s+i*k]=1;cout<<count(dp[n].begin(),dp[n].end(),1)<<'\n';
''')

add('CF1909I','交替插入 DP 与空隙分配卷积',
    '令 L=m−1，先交替插入 [1,L] 内的大小元素，使每次新数与此前所有数的和要么全部达标、要么全部不达标。两种奇偶插入序列共用 DP；剩余 n−L 个大数按空隙分配计数，转成一次卷积，得到每个 k 的答案。',
    '称相邻和至少为 m 的边为好边。[官方题解](https://codeforces.com/blog/entry/123584) 给出的关键是按大小交替插入，使新元素相对于已插入元素具有统一的好坏关系。下面推导本文使用的剩余元素公式。\n\n固定 m，令 L=m−1。m 为偶数时按 m/2,m/2−1,m/2+1,… 插入 1 到 L；m 为奇数时按 (m−1)/2,(m+1)/2,(m−3)/2,… 插入。两种序列都以一个大元素结束，之后 L+1 到 n 全是大元素。只需维护“第二个插入大元素”与“第二个插入小元素”两份交替 DP。\n\n已有 i 个元素、j 条好边。插入大元素时，两个端点与 j 个好边空隙产生 j+1 条好边，共 j+2 个位置；其余 i−1−j 个坏边空隙产生 j+2 条好边。插入小元素时，两个端点与坏边空隙保持 j，共 i+1−j 个位置；j 个好边空隙则把好边数减一。逐项更新即可。\n\n接下来固定前 L 个元素的一种排列，设它有 b 条坏边，还要插入 r=n−L 个互不相同的大元素。最终恰留 t 条坏边，须从 b 条中选 t 条不放新元素，其余 b−t 条必须至少放一个；其它空隙任意。隔板法给出填入数目的方案 C(n−b,L−t)，新元素在这些空隙中的排列有 r! 种。因此贡献系数为 C(b,t)·r!·C(n−b,L−t)。\n\n设 D[b] 为初始有 b 条坏边的排列数。令 A[b]=D[b]·b!·(n−b)!，B[d]=1/(d!·(r−d)!)，则最终 t 条坏边的数目为 r!/(t!(L−t)!) 乘 Σ(d=0..r)A[t+d]B[d]。把 A 反转，这个相关和就是卷积在 L−1−t 处的系数。使用模 998244353 的 NTT 求出所有 t，最后 k=n−1−t。\n\n各 a(m,k) 必须先在 998244353 下规范成非负代表，再当普通整数参与模 1000000007 的哈希。两种模数不能混算，也不能直接对未取第一个模的真实计数计算第二个模。',
    '时间 O(n² log n)，空间 O(n)。','奇偶 m 对应两种交替序列；最终 k=n−1−t；两种模数按题意分开。',r'''
int n;long long x;cin>>n>>x;const int mod=998244353;const long long hashMod=1000000007;vector<int>fact(n+1,1),inv(n+1,1);for(int i=1;i<=n;i++)fact[i]=1LL*fact[i-1]*i%mod;inv[n]=modPower(fact[n],mod-2);for(int i=n;i;i--)inv[i-1]=1LL*inv[i]*i%mod;int size=1;while(size<n+1)size*=2;Transform transform(size);vector<int>even(n+1),odd(n+1);even[0]=odd[0]=1;vector<long long>xp(n+1,1);x%=hashMod;for(int i=1;i<=n;i++)xp[i]=xp[i-1]*x%hashMod;long long rowFactor=1;for(int i=0;i<3;i++)rowFactor=rowFactor*xp[n]%hashMod;long long answer=0;
auto step=[&](const vector<int>&dp,int length,bool big){vector<int>next(n+1);int old=length-1;for(int j=0;j<old;j++)if(dp[j]){if(big){next[j+1]=(next[j+1]+1LL*dp[j]*(j+2))%mod;if(j+2<=n)next[j+2]=(next[j+2]+1LL*dp[j]*(old-1-j))%mod;}else{next[j]=(next[j]+1LL*dp[j]*(old+1-j))%mod;if(j)next[j-1]=(next[j-1]+1LL*dp[j]*j)%mod;}}return next;};
for(int length=2;length<=n;length++){even=step(even,length,length%2==0);odd=step(odd,length,length%2==1);const auto &dp=length%2==0?even:odd;int remaining=n-length;vector<int>a(size),b(size);for(int bad=0;bad<length;bad++)a[length-1-bad]=1LL*dp[length-1-bad]*fact[bad]%mod*fact[n-bad]%mod;for(int d=0;d<=remaining;d++)b[d]=1LL*inv[d]*inv[remaining-d]%mod;if(remaining){transform.apply(a);transform.apply(b);for(int i=0;i<size;i++)a[i]=1LL*a[i]*b[i]%mod;transform.inverse(a);}else{int multiplier=b[0];for(int &v:a)v=1LL*v*multiplier%mod;}long long row=0;for(int bad=0;bad<length;bad++){int value=1LL*a[length-1-bad]*fact[remaining]%mod*inv[bad]%mod*inv[length-bad]%mod;int good=n-1-bad;row=(row+value*xp[good])%hashMod;}answer=(answer+row*rowFactor)%hashMod;rowFactor=rowFactor*xp[n]%hashMod;}cout<<answer<<'\n';
''',r'''
const int NTT_MOD=998244353;
int modPower(int a,int b){int answer=1;for(;b;b>>=1,a=1LL*a*a%NTT_MOD)if(b&1)answer=1LL*answer*a%NTT_MOD;return answer;}
struct Transform{int n;vector<int>rev,roots;Transform(int n):n(n),rev(n),roots(n){for(int i=1;i<n;i++)rev[i]=(rev[i>>1]>>1)|((i&1)*(n/2));roots[1]=1;for(int length=2;length<n;length*=2){int z=modPower(3,(NTT_MOD-1)/(2*length));for(int i=length/2;i<length;i++){roots[2*i]=roots[i];roots[2*i+1]=1LL*roots[i]*z%NTT_MOD;}}}
void apply(vector<int>&a){for(int i=0;i<n;i++)if(i<rev[i])swap(a[i],a[rev[i]]);for(int length=1;length<n;length*=2)for(int start=0;start<n;start+=2*length)for(int j=0;j<length;j++){int x=a[start+j],y=1LL*a[start+j+length]*roots[length+j]%NTT_MOD;int sum=x+y;if(sum>=NTT_MOD)sum-=NTT_MOD;int difference=x-y;if(difference<0)difference+=NTT_MOD;a[start+j]=sum;a[start+j+length]=difference;}}
void inverse(vector<int>&a){reverse(a.begin()+1,a.end());apply(a);int inverseN=modPower(n,NTT_MOD-2);for(int &v:a)v=1LL*v*inverseN%NTT_MOD;}};
''')

add('UVA1390','连通块大小分拆上的期望递推',
    '道路的具体形状只影响当前连通块。把状态压成排序后的各块大小，随机选中不同块的概率为 size[i]·size[j]/C(n,2)，合并这两块；选中同一块的原地项移到等式左边。',
    '一条新道路是否推进连通性，只取决于两端属于哪些连通块，而与块内道路无关。大小相同的连通块也可互换，因此用排序后的大小列表作为记忆化状态。\n\n设全部城市对数量为 total=C(n,2)，跨块对数 cross=Σ(i<j)size[i]size[j]。从状态 s 选中跨块 i、j 后合并为新状态 s′；选中同块则原地不动。期望满足 E=1+(total−cross)E/total+Σsize[i]size[j]E(s′)/total。\n\n移项得 E=(total+Σsize[i]size[j]E(s′))/cross。只剩一个块时 E=0。每次有效转移都减少块数，不会形成递归环；n<=30 时不同整数分拆状态数量足够小。初始块用并查集求出，重复道路不重复合并。',
    '状态数至多整数分拆 p(n)，每状态 O(n³) 内处理合并与排序，空间 O(n·p(n))。','随机选的是不同城市，不是不同连通块；同块新路仍耗一年；输入到 EOF。',r'''
int n,m;while(cin>>n>>m){DSU d(n);while(m--){int a,b;cin>>a>>b;d.join(a-1,b-1);}vector<int>state;for(int i=0;i<n;i++)if(d.find(i)==i)state.push_back(d.size[i]);sort(state.begin(),state.end());map<vector<int>,double>memo;function<double(vector<int>)>solve=[&](vector<int>s)->double{if(s.size()==1)return 0;auto found=memo.find(s);if(found!=memo.end())return found->second;double cross=0,numerator=1.0*n*(n-1)/2;for(int i=0;i<(int)s.size();i++)for(int j=i+1;j<(int)s.size();j++){double weight=s[i]*s[j];cross+=weight;vector<int>next;for(int k=0;k<(int)s.size();k++)if(k!=i&&k!=j)next.push_back(s[k]);next.push_back(s[i]+s[j]);sort(next.begin(),next.end());numerator+=weight*solve(next);}return memo[s]=numerator/cross;};cout<<fixed<<setprecision(9)<<solve(state)<<'\n';}
''',DSU)

add('P6046','随机删边次序与最近更强者',
    '相邻决斗等价于随机删除原数组中的一条剩余分界，合并两段并留下较大者。对每个位置，只需看左右最近更强者的距离，利用随机排列中指定边集合全部出现的概率求存活期望。',
    '把每个存活容器看成它已经击败的连续段的最大值。相邻两者决斗就是删除这两段之间的一条原始分界边，并把两段合并。每轮所有剩余分界等概率被选，因此等价于将 n−1 条原始分界随机排列，依次删除。\n\n位置 i 被淘汰，当且仅当它的连通段首次包含一个更强者。只需考虑左右最近更强者：若要连到更远的强者，途中也必先连到最近的。设左、右距离分别为 L、R，连接到一侧要求该侧路径上的全部分界已经被删除。\n\n经过 t 轮后，一组固定 k 条边全部出现的概率为 C(t,k)/C(n−1,k)。存活概率用左右两个“已经连到强者”事件容斥；两侧路径不重叠，同时发生要求 L+R 条边全部出现。\n\n整数存活轮数 X 的期望为 Σ(t=1..n−1)P(X>=t)。由组合恒等式 Σ(t=k..n−1)C(t,k)=C(n,k+1)，每个长度 k 的路径项求和后等于 n/(k+1)。所以 E=n−1−n/(L+1)−n/(R+1)+n/(L+R+1)，不存在的一侧及其交集项不加入。\n\n最近更大位置用单调栈求出。分数在模 998244353 下用分母逆元表示；全局最大者没有任何更强者，期望正好为 n−1。',
    '时间 O(n+log MOD)，空间 O(n)。','存活轮数比被击倒的轮次少一；缺少一侧时去掉对应项；点值互不相同。',r'''
int n;cin>>n;const long long mod=998244353;vector<int>a(n),left(n,-1),right(n,n),st;for(int &x:a)cin>>x;for(int i=0;i<n;i++){while(!st.empty()&&a[st.back()]<a[i])st.pop_back();if(!st.empty())left[i]=st.back();st.push_back(i);}st.clear();for(int i=n-1;i>=0;i--){while(!st.empty()&&a[st.back()]<a[i])st.pop_back();if(!st.empty())right[i]=st.back();st.push_back(i);}vector<long long>inv(2*n+2);inv[1]=1;for(int i=2;i<(int)inv.size();i++)inv[i]=(mod-mod/i)*inv[mod%i]%mod;for(int i=0;i<n;i++){long long ans=n-1;if(left[i]>=0)ans=(ans-n*inv[i-left[i]+1]%mod+mod)%mod;if(right[i]<n)ans=(ans-n*inv[right[i]-i+1]%mod+mod)%mod;if(left[i]>=0&&right[i]<n)ans=(ans+n*inv[right[i]-left[i]+1])%mod;cout<<ans<<(i+1==n?'\n':' ');}
''')

add('P1652','比较起终点位于每个圆的哪一侧',
    '对每个圆，若起终点一个在内部、一个在外部，则任何连续曲线都必须穿过它的边界一次；两点在同一侧时可以避开。统计内外状态不同的圆数。',
    '圆周把平面分成内部与外部。若两点分处两侧，连续曲线必须跨过边界，至少一次；若在同侧，这个圆本身不强制跨越。\n\n题目保证各圆互不相交也不相切，它们只能分离或相互包含，因此这些圆周形成无交叉的层次边界。可以沿圆形成的区域层次从起点所在区域走到终点区域，恰好跨过内外状态不同的那些圆，达到上述下界。\n\n判断是否在内部只比较距离平方与半径平方，无需开方。输入的所有 x、所有 y、所有 r 分三行给出，不能错读成逐圆的三元组。',
    '时间 O(n)，空间 O(n)。','圆参数按三组数组读取；用平方比较；起终点保证不在圆周上。',r'''
int n;cin>>n;vector<long long>x(n),y(n),r(n);for(auto &v:x)cin>>v;for(auto &v:y)cin>>v;for(auto &v:r)cin>>v;long long x1,y1,x2,y2;cin>>x1>>y1>>x2>>y2;int ans=0;for(int i=0;i<n;i++){bool a=(x1-x[i])*(x1-x[i])+(y1-y[i])*(y1-y[i])<r[i]*r[i];bool b=(x2-x[i])*(x2-x[i])+(y2-y[i])*(y2-y[i])<r[i]*r[i];ans+=a!=b;}cout<<ans<<'\n';
''')

add('P1325','把雷达覆盖转成区间选点',
    '雷达位于 x 轴。能覆盖岛屿 (x,y) 的雷达横坐标区间为 [x−sqrt(d²−y²),x+sqrt(d²−y²)]。按右端排序，若上个雷达不在当前区间内，就在当前右端再放一个。',
    '雷达到岛屿的距离不超过 d，设雷达横坐标 t，由 (t−x)²+y²<=d² 得到一个允许 t 的闭区间。若 |y|>d，根本不存在可覆盖它的 x 轴位置，整题无解。\n\n现在要求最少点，使每个区间都至少包含一个点。把区间按右端从小到大排列。当前最早结束的未覆盖区间必须选一个点，将它放在右端不会比更左的位置覆盖更少的后续区间，因为后续右端都不小于它。\n\n若上一个选点已经位于当前区间内，无需新增；否则在当前右端放点。这个交换论证保证每次选择都能保留某个最优解。注意区间是闭合的，边界相等时已覆盖。',
    '时间 O(n log n)，空间 O(n)。','先检查 |y|<=d；区间按右端排序；相等端点算覆盖。',r'''
int n;double d;cin>>n>>d;vector<pair<double,double>>intervals;bool possible=true;for(int i=0;i<n;i++){double x,y;cin>>x>>y;if(abs(y)>d){possible=false;continue;}double radius=sqrt(max(0.0,d*d-y*y));intervals.push_back({x-radius,x+radius});}if(!possible){cout<<-1<<'\n';return 0;}sort(intervals.begin(),intervals.end(),[](auto a,auto b){return a.second<b.second;});int ans=0;double last=-numeric_limits<double>::infinity();for(auto [l,r]:intervals)if(last<l){last=r;ans++;}cout<<ans<<'\n';
''')

add('P1355','叉积判断三角形内外与边界',
    '先判断是否与顶点重合，再判断是否在线段上。其它点若始终位于三条有向边的同一侧，就在三角形内部，否则在外部。',
    '有向边 A→B 与向量 A→P 的叉积，正负表示 P 在边的左侧或右侧，零表示共线。按三角形顶点顺序，内部点必须对三条边都在同一侧；顶点为顺时针或逆时针都能用“全正或全负”判断。\n\n边界情况要先处理。点与任一顶点坐标相等，输出四。叉积为零还不够，因为点可能落在边的延长线上；同时要求横纵坐标均在两端的闭范围内，才在线段上，输出三。\n\n剩余点的三个叉积若全正或全负输出一，否则输出二。输入坐标带括号和逗号，先把非数字且非负号字符替换为空格，再按整数读入。',
    '时间 O(输入长度)，空间 O(输入长度)。','顶点先于边界判断；共线还要检查在线段范围；输出编号按题面。',r'''
string all,line;while(getline(cin,line))all+=line+' ';for(char &c:all)if(!isdigit((unsigned char)c)&&c!='-')c=' ';stringstream input(all);array<Point,4>p;for(auto &v:p)input>>v.x>>v.y;Point q=p[3];for(int i=0;i<3;i++)if(p[i].x==q.x&&p[i].y==q.y){cout<<4<<'\n';return 0;}long long value[3];for(int i=0;i<3;i++){auto a=p[i],b=p[(i+1)%3];value[i]=cross(a,b,q);if(value[i]==0&&min(a.x,b.x)<=q.x&&q.x<=max(a.x,b.x)&&min(a.y,b.y)<=q.y&&q.y<=max(a.y,b.y)){cout<<3<<'\n';return 0;}}bool inside=(value[0]>0&&value[1]>0&&value[2]>0)||(value[0]<0&&value[1]<0&&value[2]<0);cout<<(inside?1:2)<<'\n';
''',r'''
struct Point{long long x,y;};long long cross(Point a,Point b,Point c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
''')

add('P2181','每四个顶点对应一对相交对角线',
    '凸多边形中任取四个顶点，其两条对角线在内部相交；每个交点又由唯一一组四顶点确定，因此答案是 C(n,4)。',
    '两条在多边形内部相交的对角线，必须拥有四个不同端点；这些端点沿凸多边形边界交错出现，恰好组成一个凸四边形，两条所选线就是它的两条对角线。\n\n反过来，任取四个顶点，得到的凸四边形两条对角线必定相交。按题目对交点位置的约定，这样每组选出的四顶点贡献一个内部交点，所以只需计算组合数 n(n−1)(n−2)(n−3)/24。\n\n中间四个数的乘积可能先溢出六十四位，因此用 __int128 完成乘法和除法，再十进制输出。少于四个顶点时答案为零。',
    '时间 O(1)，空间 O(1)。','只数内部对角线交点；先用宽整数计算；n<4 输出 0。',r'''
long long n;cin>>n;if(n<4){cout<<0<<'\n';return 0;}__int128 value=(__int128)n*(n-1)*(n-2)*(n-3)/24;string s;do{s.push_back('0'+value%10);value/=10;}while(value);reverse(s.begin(),s.end());cout<<s<<'\n';
''')

add('P2742','单调链求凸包周长',
    '按坐标排序，分别维护下凸壳和上凸壳。新点使末尾转向不再凸时弹出中间点。合并得到凸包，循环累加相邻点距离。',
    '最短围住全部点的绳子只会接触凸包边界，凹进去的折线可以直接拉直并缩短，所以只需求凸包的周长。\n\n坐标字典序排序后，从左到右维护下壳。若最后两个壳点与新点不构成逆时针转向，当前中间点不可能位于下凸壳上，弹出再判断。反向扫描得到上壳，去掉重复端点并拼接。\n\n叉积为零的中间共线点也可弹出，因为保留直线段两端不影响周长。最后包括末点回到首点的边。距离用 hypot 计算，结果按两位小数输出。',
    '时间 O(n log n)，空间 O(n)。','先排序并去重；周长包含闭合边；共线中间点不影响长度。',r'''
int n;cin>>n;vector<Point>a(n);for(auto &v:a)cin>>v.x>>v.y;sort(a.begin(),a.end(),[](Point a,Point b){return tie(a.x,a.y)<tie(b.x,b.y);});a.erase(unique(a.begin(),a.end(),[](Point a,Point b){return a.x==b.x&&a.y==b.y;}),a.end());vector<Point>h;for(auto p:a){while(h.size()>=2&&cross(h[h.size()-2],h.back(),p)<=0)h.pop_back();h.push_back(p);}int lower=h.size();for(int i=(int)a.size()-2;i>=0;i--){auto p=a[i];while((int)h.size()>lower&&cross(h[h.size()-2],h.back(),p)<=0)h.pop_back();h.push_back(p);}if(h.size()>1)h.pop_back();double ans=0;for(int i=0;i<(int)h.size();i++){auto p=h[i],q=h[(i+1)%h.size()];ans+=hypot(p.x-q.x,p.y-q.y);}cout<<fixed<<setprecision(2)<<ans<<'\n';
''',r'''
struct Point{double x,y;};double cross(Point a,Point b,Point c){return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);}
''')

add('P3194','斜率排序后维护直线上包络',
    '同斜率只保留最高一条。按斜率递增加入直线，维护每条线开始成为最高线的横坐标；新交点不在上条线可见区间右侧时弹掉上条线。',
    '从上方看到的正是所有直线的逐点最大值，也叫上包络。斜率越大的线越可能在更右侧占优，因此按斜率从小到大处理，可见区间也按横坐标递增。\n\n平行线中截距较小者永远被覆盖，先去掉。对新线与栈顶线求交点 x；如果 x 不大于栈顶开始可见的位置，那么栈顶线还没获得正长度的可见区间就被新线压住，必须弹出，并继续与更前一条比较。\n\n最终保留的直线各自拥有一个非空开区间可见。三线恰在一点交会时，中间线若只在一个点达到最大，不算看见一段线，因此相等时也要弹出。输出原始编号并按编号排序。',
    '时间 O(n log n)，空间 O(n)。','同斜率保留最高截距；只在单个交点出现不算可见；输出原编号。',r'''
int n;cin>>n;vector<Line>a(n);for(int i=0;i<n;i++){cin>>a[i].k>>a[i].b;a[i].id=i+1;}sort(a.begin(),a.end(),[](Line a,Line b){if(a.k!=b.k)return a.k<b.k;return a.b>b.b;});vector<Line>h;vector<long double>start;for(auto line:a){if(!h.empty()&&line.k==h.back().k)continue;long double x=-numeric_limits<long double>::infinity();while(!h.empty()){x=(long double)(h.back().b-line.b)/(line.k-h.back().k);if(x>start.back())break;h.pop_back();start.pop_back();}if(h.empty())x=-numeric_limits<long double>::infinity();h.push_back(line);start.push_back(x);}vector<int>ans;for(auto line:h)ans.push_back(line.id);sort(ans.begin(),ans.end());for(int id:ans)cout<<id<<' ';cout<<'\n';
''',r'''
struct Line{long long k,b;int id;};
''')

add('P1641','反射原理扣掉首次越界的路径',
    '全部字符串数为 C(n+m,m)。把首次出现 0 多于 1 的前缀反转，可将非法串与含 n+1 个 1、m−1 个 0 的串一一对应，所以答案为 C(n+m,m)−C(n+m,m−1)。',
    '把 1 看作向上一步、0 看作向下一步，要求所有前缀高度非负。全部安排有 C(n+m,m) 种，直接扣去走到负高度的安排。\n\n对一条非法路径，找到第一次到达 −1 的位置，把此前所有上、下步互换。这个前缀原来下步比上步多一个，互换后总的上步增加一、下步减少一，得到 n+1 个上步和 m−1 个下步的任意路径。\n\n反变换是找到第一次到达 +1 的位置并再次反转，因此这是双射，非法路径数恰为 C(n+m,m−1)。阶乘与逆阶乘预处理到 n+m，模数 20100403 为质数且比范围大，可以用费马小定理求逆。',
    '时间 O(n+m+log MOD)，空间 O(n+m)。','非法数对应 m−1；模减法加模数；不是只要求最终 1 不少于 0。',r'''
int n,m;cin>>n>>m;const long long mod=20100403;int total=n+m;vector<long long>fact(total+1,1),inv(total+1,1);for(int i=1;i<=total;i++)fact[i]=fact[i-1]*i%mod;inv[total]=power(fact[total],mod-2,mod);for(int i=total;i;i--)inv[i-1]=inv[i]*i%mod;auto choose=[&](int k){if(k<0||k>total)return 0LL;return fact[total]*inv[k]%mod*inv[total-k]%mod;};cout<<(choose(m)-choose(m-1)+mod)%mod<<'\n';
''',POW)

add('P2532','按最高台阶分解得到 Catalan 递推',
    '阶梯最外层的一块钢材把剩余阶梯分成左右两个独立部分，方案数满足 C_n=Σ C_iC_(n−1−i)，即 Catalan 数。用等价的相邻项乘除递推高精度计算。',
    '总高为 n 的阶梯中，考察与对角阶梯边界接触并分隔两侧的那块钢材，它的位置把其余结构分成规模 i 与 n−1−i 的两个更小阶梯。选定分界后，两侧可以独立搭建，贡献 C_i·C_(n−1−i)，所有分界互不重复。\n\n因此 C_0=1，C_n=Σ(i=0..n−1)C_iC_(n−1−i)，是 Catalan 递推。闭式 C_n=C(2n,n)/(n+1) 进一步给出 C_i=C_(i−1)·(4i−2)/(i+1)。\n\nn 可到五百，固定六十四位整数不够。程序用十亿进制大整数，只需乘小整数和除小整数；先乘后除，每一步都精确整除。样例 n=3 对应 5 种。',
    'O(n) 次高精度小整数乘除，空间 O(答案位数)。','初始 C_0=1；不能用浮点近似；除法必须在乘法之后。',r'''
int n;cin>>n;Big answer(1);for(int i=1;i<=n;i++){answer.multiply(4*i-2);answer.divide(i+1);}cout<<answer<<'\n';
''',BIG)

add('P3802','对每个七连窗口应用期望线性性',
    '总晶体数为 S，每个连续七次施法成为七重奏的概率相同，为 7!∏a_i/[S(S−1)…(S−6)]。共有 S−6 个窗口，乘起来就是期望。',
    '把全部晶体随机排列，每一步从剩余晶体中等概率选一个，等价于读取这个随机排列。对任意固定的七个连续位置，七种属性各出现一次的概率相同。\n\n固定一种属性排列，概率为 ∏a_i 除以 S(S−1)…(S−6)，因为每种属性只取一次；七种属性有 7! 种顺序。令每个窗口的指示变量表示是否触发，其期望就是这个概率。即使窗口互相重叠，期望仍可直接相加，不要求事件独立。\n\n窗口总数为 S−6，因此乘上这个数。S<7 时没有窗口，答案为零。使用 long double 逐项乘除，避免先计算巨大整数乘积。',
    '时间 O(1)，空间 O(1)。','重叠窗口都计数；不足七个时为零；某属性数量为零时概率自然为零。',r'''
long long a[7],sum=0;for(auto &x:a){cin>>x;sum+=x;}long double ans=0;if(sum>=7){ans=5040.0L*(sum-6);for(int i=0;i<7;i++)ans=ans*a[i]/(sum-i);}cout<<fixed<<setprecision(3)<<ans<<'\n';
''')

add('P1291','集齐新名字所需时间的调和级数',
    '已经收集 k 个名字时，下次拿到新名字的概率为 (n−k)/n，等待期望为 n/(n−k)。相加得到 n·(1+1/2+…+1/n)，用有理数精确累加并按题意排版。',
    '把收集过程分成从 k 种到 k+1 种的 n 个阶段。每瓶独立等概率出现一个名字，尚未拥有的名字有 n−k 种，所以成功概率为 (n−k)/n。几何分布的等待期望为概率的倒数。\n\n由期望线性性，总期望为 Σ(k=0..n−1)n/(n−k)=nH_n。逐项用最大公约数通分、加分子并约分，避免小数损失。n<=33 时这些约分后的整数能用 long long 保存。\n\n最后把分子除以分母得到整数部分和余数。余数为零就只输出整数；否则分子和分母前补与整数部分位数相同的空格，中间分数线长度等于分母位数。',
    '时间 O(n log 分母)，空间 O(1)。','用精确分数；每次约分；分数线与上下两行起点对齐。',r'''
long long n;cin>>n;long long numerator=0,denominator=1;for(long long i=1;i<=n;i++){long long g=gcd(denominator,i);numerator=numerator*(i/g)+n*(denominator/g);denominator*=i/g;g=gcd(numerator,denominator);numerator/=g;denominator/=g;}long long whole=numerator/denominator,rem=numerator%denominator;if(!rem)cout<<whole<<'\n';else{string pad(to_string(whole).size(),' ');cout<<pad<<rem<<'\n'<<whole<<string(to_string(denominator).size(),'-')<<'\n'<<pad<<denominator<<'\n';}
''')

add('CF388C','两半归属固定，奇数中点轮流争夺',
    '每堆上半归先手、下半归后手；奇数堆多出的中间牌拿出来，按数值从大到小由两人轮流分配。把这三部分分别累加。',
    '偶数堆的前后两半可以通过配对回应保证：对手从某堆拿一张后，自己从该堆另一端回应，就能守住本方的一半。偏离这种配对不能迫使对方放弃它能够保证的牌。\n\n奇数堆在两侧各取相同数量后，还会剩一张中间牌。它属于谁是唯一未确定的部分；各堆中点之间没有其它相互限制，争夺者总应优先拿当前最大中点。若先拿更小中点而把更大留给对手，交换选择只会提高自己的最终总分。\n\n所以每堆前 floor(s/2) 张累加给 Ciel，后 floor(s/2) 张给 Jiro；所有奇数中点降序排列，从 Ciel 开始交替累加。',
    '时间 O(总牌数+n log n)，空间 O(n)。','输入按从顶到底顺序；偶数堆没有中点；先手先拿最大中点。',r'''
int n;cin>>n;long long first=0,second=0;vector<int>middle;while(n--){int size;cin>>size;vector<int>a(size);for(int &x:a)cin>>x;for(int i=0;i<size/2;i++){first+=a[i];second+=a[size-1-i];}if(size%2)middle.push_back(a[size/2]);}sort(middle.rbegin(),middle.rend());for(int i=0;i<(int)middle.size();i++)if(i%2)second+=middle[i];else first+=middle[i];cout<<first<<' '<<second<<'\n';
''')

add('SP30919','最小可用整数一定是质数',
    '若一个合数与所有输入互质，它的任一质因数也与所有输入互质且更小，所以最优一定是质数。筛最小质因数并标记输入中出现过的全部质因数，取最小未标记者。',
    '设最优 x 为合数，取它的一个质因数 p<x。若某个输入能被 p 整除，则它与 x 的 gcd 也至少为 p，与 x 合法矛盾；所以 p 本身也合法，违背 x 最小。因此只需考虑质数。\n\n预处理至最大输入值范围的最小质因数，读取每个数后不断按最小质因数剥除，并把出现过的质数标记。一个质数 p 合法，当且仅当没有任何输入含 p 这个因子。按质数递增找第一个未标记者即可。\n\n同一数的一个质因子出现多次只需标一次；输入为一不带任何质因子。筛到 10000010，包含超过全部允许输入的下一个质数，保证能找到未出现的候选。',
    '预处理 O(A)，每组分解 O(n log A)，空间 O(A)。','寻找 x>1；质因子去重标记；不要只计算所有数的 gcd。',r'''
const int limit=10000010;vector<int>least(limit+1),primes;for(int i=2;i<=limit;i++){if(!least[i]){least[i]=i;primes.push_back(i);}for(int p:primes){if(p>least[i]||1LL*i*p>limit)break;least[i*p]=p;}}int tests;cin>>tests;vector<int>stamp(limit+1);for(int test=1;test<=tests;test++){int n;cin>>n;while(n--){int x;cin>>x;while(x>1){int p=least[x];stamp[p]=test;while(x%p==0)x/=p;}}for(int p:primes)if(stamp[p]!=test){cout<<p<<'\n';break;}}
''')

add('CF1614D1','在约数链上安排 gcd 降低的时机',
    '统计每个 d 有多少输入是其倍数。令 dp[d] 为先处理所有 d 倍数的最优贡献；从更大的倍数 j 转移：dp[d]=max(dp[j]+d(cnt[d]−cnt[j]))。倒序枚举 d。',
    '一个排列的前缀 gcd 只能保持或变成自己的约数。若当前 gcd 仍至少含 d，那么所有 d 的倍数都可以先加入，它们不会使 gcd 跌到 d 以下；将这些数尽量提前只会增加或保持前缀 gcd 总和。\n\n设 cnt[d] 为数组中 d 的倍数数量。若不利用更高 gcd，就先按 gcd=d 的下界给出 d·cnt[d]。若先处理 j 的倍数，其中 j 是 d 的真倍数，可以获得 dp[j]；接着把其余 d 的倍数加入，每个至少贡献 d，新增 d(cnt[d]−cnt[j])。枚举所有 j 得到最优。\n\n按 d 从大到小计算，所有依赖已完成。cnt 可由值域频数按倍数求和，转移也按倍数枚举。最终 dp[1] 已包含全部数，即所求最大值。',
    '时间 O(A log A)，空间 O(A)。','输入重复值按次数计；dp 用 long long；倒序计算因数状态。',r'''
int n;cin>>n;vector<int>a(n);int maximum=0;for(int &x:a){cin>>x;maximum=max(maximum,x);}vector<int>frequency(maximum+1),count(maximum+1);for(int x:a)frequency[x]++;for(int d=1;d<=maximum;d++)for(int j=d;j<=maximum;j+=d)count[d]+=frequency[j];vector<long long>dp(maximum+1);for(int d=maximum;d>=1;d--){dp[d]=1LL*d*count[d];for(int j=d+d;j<=maximum;j+=d)dp[d]=max(dp[d],dp[j]+1LL*d*(count[d]-count[j]));}cout<<dp[1]<<'\n';
''')

BSGS=r'''
long long multiply(long long a,long long b,long long mod){return (__int128)a*b%mod;}
long long modularPower(long long a,long long b,long long mod){long long ans=1;for(;b;b>>=1,a=multiply(a,a,mod))if(b&1)ans=multiply(ans,a,mod);return ans;}
long long logarithm(long long base,long long target,long long mod){long long block=sqrt((long double)mod)+1;unordered_map<long long,int>baby;baby.reserve(2*block);long long value=1;for(int j=0;j<block;j++){baby.emplace(value,j);value=multiply(value,base,mod);}long long inverse=modularPower(value,mod-2,mod);value=target;for(long long i=0;i<=block;i++){auto it=baby.find(value);if(it!=baby.end())return i*block+it->second;value=multiply(value,inverse,mod);}return -1;}
'''
add('P3846','BSGS 分解指数为大步和小步',
    '把指数写成 l=iB+j。预存 b^j，枚举 n·b^(−iB) 是否在表中，命中得到候选 iB+j；按 i 递增，表中保留最小 j，即得到最小非负解。',
    '模数 p 为质数且 b 非零，因此 b 存在逆元。取 B≈sqrt(p)，任何可能的最小指数都可分为大步 iB 与小步 j，其中 0<=j<B。\n\n等式 b^(iB+j)=n 可以改写为 b^j=n·(b^B)^(−i)。先将所有小步值 b^j 放入表，重复值只保留最小 j。再从 n 开始，每轮乘 b^B 的逆元，查找对应小步。\n\n同一个大步内最小 j 最优，不同大步按 i 递增互不交叠，所以首次命中就是最小非负指数。模 p 的非零乘法群大小为 p−1，搜索范围足够覆盖全部可能。未命中时按原题输出 no solution。',
    '平均时间 O(sqrt p)，空间 O(sqrt p)。','允许指数 0；重复 baby 值保留最小指数；逆元依赖 p 为质数。',r'''
long long p,b,n;cin>>p>>b>>n;long long answer=logarithm(b,n,p);if(answer<0)cout<<"no solution\n";else cout<<answer<<'\n';
''',BSGS)

add('P4884','把全一数转为十的离散对数',
    '全一数 R_N=(10^N−1)/9，因质数 m≥7，9 在模 m 下可逆，所以原式等价于 10^N≡9K+1(mod m)。用 BSGS 求最小指数。',
    'N 位全一数乘九后等于 10^N−1，因此原条件推出 10^N≡9K+1。反过来，因为 m 是至少七的质数，与九互质，可以消去九，所以两条件完全等价。这里若随意对合数模数消去九就可能出错。\n\n用 BSGS 将 N 拆成 iB+j，预存 10^j，再枚举 (9K+1)·(10^B)^(−i)。表中保留每个余数最小的小步指数，首次命中得到最小解。\n\nK 在 1 到 m−1 内，9K+1 不可能模 m 等于一，所以不会错误地取到 N=0；原题保证有解。m 可达十的十一次方，两个余数相乘会超出六十四位，中间乘法使用 __int128。',
    '平均时间 O(sqrt m)，空间 O(sqrt m)。','利用质数保证九可逆；模乘使用 __int128；答案要求正整数。',r'''
long long k,m;cin>>k>>m;cout<<logarithm(10,(9*k+1)%m,m)<<'\n';
''',BSGS)

add('UVA11426','欧拉函数预处理每个右端点的贡献',
    '固定右端点 j，按 gcd(i,j)=d 分组，其和为 Σ(d|j,d<j)d·φ(j/d)。用倍数枚举一次加入所有 j，再前缀求和，回答多组 n。',
    '目标是所有 1<=i<j<=n 的 gcd 和。固定较大的 j，若 gcd(i,j)=d，写 i=dt、j=dk，那么 1<=t<k 且 gcd(t,k)=1。k>1 时满足条件的 t 有 φ(k) 个，因此这组贡献 dφ(k)。\n\n预处理欧拉函数后，枚举 d，再枚举 k>=2，把 dφ(k) 加到 j=d·k 的单点贡献中。每一对 (i,j) 按其唯一 gcd 恰好计一次。\n\n最后对 j 的贡献做前缀和，预处理到所有输入的最大 n。输入以零结束，结果可能很大，使用 long long。筛 phi 时先将 phi[i]=i，再对每个质数的倍数应用乘法公式。',
    '时间 O(A log A)，空间 O(A)。','只统计 i<j，倍数系数从 2 起；先求单个右端贡献，再做前缀和。',r'''
vector<int>queries;int n,maximum=0;while(cin>>n&&n){queries.push_back(n);maximum=max(maximum,n);}vector<int>phi(maximum+1);iota(phi.begin(),phi.end(),0);for(int p=2;p<=maximum;p++)if(phi[p]==p)for(int j=p;j<=maximum;j+=p)phi[j]=phi[j]/p*(p-1);vector<long long>sum(maximum+1);for(int d=1;d<=maximum/2;d++)for(int j=d+d;j<=maximum;j+=d)sum[j]+=1LL*d*phi[j/d];for(int i=1;i<=maximum;i++)sum[i]+=sum[i-1];for(int x:queries)cout<<sum[x]<<'\n';
''')

add('P6210','gcd 周期上的大整数商与余数',
    'gcd(x,n) 以 n 为周期，先预处理一个周期中合法数的前缀个数。第 f 个数由 (f−1) 除以周期合法数得到周期编号与周期内排名；区间个数也用整周期加剩余前缀计算。',
    '因为 gcd(x+n,n)=gcd(x,n)，合法性每 n 个数重复一次。预处理 prefix[i] 表示 1 到 i 中 gcd 不超过 c 的个数，令 total=prefix[n]。\n\n第 f 小的数，先对 f−1 做 total 的除法。商 q 表示前面完整经过多少个周期，余数 r 表示本周期中从零开始的排名。二分找到 prefix[pos]>=r+1 的最小 pos，答案为 qn+pos。计数 F(X) 则把 X 除以 n，得到商 q 与余数 r，返回 q·total+prefix[r]。最终第二问为 F(R)−F(L−1)。\n\n为避免对一千万个数逐个求 gcd，使用线性筛递推 g[i·p]=g[i]·gcd(p,n/g[i])。p 为质数，最后的 gcd 只有一或 p 两种，常数时间即可；筛完把 g 原地改成合法前缀计数，节省内存。\n\n超长的 f、L、R 用十亿进制大整数表示，仅需除小整数、乘小整数和减法，时间与输入位数成正比，不把十万位数字转换为固定整数。',
    '时间 O(n+输入总位数+log n)，空间 O(n+输入总位数)。','第 f 项先用 f−1 分周期；周期内二分第一个达到排名的位置；L−1 用高精度减法。',r'''
int n,c;string sf,sl,sr;cin>>n>>c>>sf>>sl>>sr;vector<int>least(n+1),g(n+1),primes;g[1]=1;for(int i=2;i<=n;i++){if(!least[i]){least[i]=i;primes.push_back(i);g[i]=(n%i==0?i:1);}for(int p:primes){if(p>least[i]||1LL*i*p>n)break;least[i*p]=p;g[i*p]=g[i]*((n/g[i])%p==0?p:1);}}for(int i=1;i<=n;i++)g[i]=g[i-1]+(g[i]<=c);int total=g[n];Big f(sf);f.subtract(Big(1));int rank=f.divide(total)+1;int position=lower_bound(g.begin()+1,g.end(),rank)-g.begin();f.multiply(n);f.add(position);cout<<f<<'\n';auto count=[&](Big value){int rem=value.divide(n);value.multiply(total);value.add(g[rem]);return value;};Big left(sl);left.subtract(Big(1));Big answer=count(Big(sr));answer.subtract(count(left));cout<<answer<<'\n';
''',BIG)

add('UVA11181','枚举购买集合并做条件概率归一化',
    '枚举恰好 R 个人购买的所有集合，累加集合概率得到条件事件概率；同时把概率加入集合内每个人的分子。各分子除以总概率即为条件购买概率。',
    '每个人独立购买，给定一个购买集合 S，其发生概率为购买者的 p 连乘与未购买者的 (1−p) 连乘。只保留大小恰为 R 的集合，正好组成已知条件事件。\n\n这些集合互斥，因此总概率等于各集合概率之和。对于第 i 人，他购买且总共 R 人购买的联合事件，只需累加所有含 i 的合法集合概率。根据条件概率公式，再除以总事件概率即可。\n\n人数较少，可以用二进制掩码枚举所有集合，先按位数筛掉不符合数量的掩码，再计算概率。每组输出 Case 编号和每人的六位小数。原题保证条件事件可用于查询，不应把不可能条件随意解释为某个概率分布。',
    '时间 O(n·2^n)，空间 O(n)。','独立概率相乘；未购买者用 1−p；最后按条件总概率归一化。',r'''
int n,r,test=0;while(cin>>n>>r&&(n||r)){vector<double>p(n),numerator(n);for(auto&x:p)cin>>x;double denominator=0;for(int mask=0;mask<(1<<n);mask++)if(__builtin_popcount((unsigned)mask)==r){double probability=1;for(int i=0;i<n;i++)probability*=((mask>>i)&1)?p[i]:1-p[i];denominator+=probability;for(int i=0;i<n;i++)if((mask>>i)&1)numerator[i]+=probability;}cout<<"Case "<<++test<<":\n";for(double x:numerator)cout<<fixed<<setprecision(6)<<x/denominator<<'\n';}
''')

add('CF559C','按首个障碍扣除的组合路径 DP',
    '把障碍和终点按坐标排序。到每个点的总单调路径是组合数，再减去经过此前各障碍的路径；其中以“首次遇到的障碍”分类，避免重复扣除。',
    '没有障碍时，从 (1,1) 到 (x,y) 需要 x−1 次向下和 y−1 次向右，路径数为 C(x+y−2,x−1)。\n\n把障碍坐标排序并将终点放在最后。令 dp[i] 表示到第 i 个特殊点、且没有经过其它较早障碍的路径数。先赋总路径数，再对每个坐标不大于它的此前障碍 j，减去 dp[j]·C(dx+dy,dx)。\n\n被扣掉的路径按首次到达的障碍 j 分组，dp[j] 已保证到它之前没有其它障碍，所以不同 j 的类别互不重复。乘上的组合数负责障碍之后到当前点的任意单调走法。终点的 dp 就是完全避开障碍的答案。',
    '时间 O(H+W+n²)，空间 O(H+W+n)。','只有坐标可达的障碍才转移；先前 dp 已排除更早障碍；模数为 1000000007。',r'''
int h,w,n;cin>>h>>w>>n;vector<pair<int,int>>points(n);for(auto &[x,y]:points)cin>>x>>y;points.push_back({h,w});sort(points.begin(),points.end());const long long mod=1000000007;int limit=h+w;vector<long long>fact(limit+1,1),inv(limit+1,1);for(int i=1;i<=limit;i++)fact[i]=fact[i-1]*i%mod;inv[limit]=power(fact[limit],mod-2,mod);for(int i=limit;i;i--)inv[i-1]=inv[i]*i%mod;auto choose=[&](int a,int b){return fact[a]*inv[b]%mod*inv[a-b]%mod;};vector<long long>dp(n+1);for(int i=0;i<=n;i++){auto [x,y]=points[i];dp[i]=choose(x+y-2,x-1);for(int j=0;j<i;j++)if(points[j].first<=x&&points[j].second<=y){int dx=x-points[j].first,dy=y-points[j].second;dp[i]=(dp[i]-dp[j]*choose(dx+dy,dx)%mod+mod)%mod;}}cout<<dp[n]<<'\n';
''',POW)

add('P6162','阶梯棋盘的车数等于第二类 Stirling 数',
    '填数字相当于在第 i 列的前 i 行放一辆车，且每列每行至多一辆。阶梯棋盘放 k 辆车的方案数是 S(n,n−k)，用容斥公式求这个第二类 Stirling 数。',
    '把格子编号看作列，填入的数看作行。每列至多填一个数，对应每列至多一辆车；数字互不相同对应每行至多一辆车。允许区域正好是列高依次为 1 到 n−1 的阶梯棋盘。\n\n其车数递推满足 R(n,k)=R(n−1,k)+(n−k)R(n−1,k−1)：最后一列不放，或放在未占用的行。代换 m=n−k 后，正是第二类 Stirling 数递推 S(n,m)=S(n−1,m−1)+mS(n−1,m)，边界也一致，故答案为 S(n,n−k)。\n\n令 m=n−k，使用满射容斥：m!S(n,m)=Σ(i=0..m)(−1)^(m−i)C(m,i)i^n。将组合数约去 m!，每项是 (−1)^(m−i)i^n/(i!(m−i)!)，预处理阶乘逆元后快速幂求和即可。',
    '时间 O((n−k) log n)，空间 O(n−k)。','是 S(n,n−k)；容斥正负按 m−i；k=0 时答案为 1。',r'''
int n,k;cin>>n>>k;const long long mod=998244353;if(k==0){cout<<1<<'\n';return 0;}int m=n-k;vector<long long>fact(m+1,1),inv(m+1,1);for(int i=1;i<=m;i++)fact[i]=fact[i-1]*i%mod;inv[m]=power(fact[m],mod-2,mod);for(int i=m;i;i--)inv[i-1]=inv[i]*i%mod;long long ans=0;for(int i=0;i<=m;i++){long long term=power(i,n,mod)*inv[i]%mod*inv[m-i]%mod;if((m-i)&1)ans=(ans-term+mod)%mod;else ans=(ans+term)%mod;}cout<<ans<<'\n';
''',POW)

add('P6561','按奇偶选择数量使用双二项式',
    '不相邻选择中，a 个奇数与 b 个偶数的方案数为 C(m−b,a)·C(m−a,b)。预处理阶乘与逆阶乘后，每组常数时间计算。',
    '把相邻的一奇一偶位置分成 m 对。选出的奇数不能与它右侧和左侧的偶数相邻，限制只发生在相邻对之间。\n\n可以按奇数选择形成的连续段计数，再为偶数在未被封锁的位置中选点，用两次 Vandermonde 卷积整理，得到 C(m−b,a)C(m−a,b)。这个式子也可解释为删除所选偶数占用的 b 个间隙后选 a 个奇位、对称地删除 a 个间隙后选 b 个偶位，两组压缩坐标唯一还原原来的不相邻排列。\n\n例如 m=4,a=2,b=1，结果为 C(3,2)C(2,1)=6，与样例六个集合一致。约束 a+b<=m 保证组合数下标合法。全部询问共用到最大 m 的阶乘与逆阶乘，模数为 998244353。',
    '预处理 O(max m)，每组 O(1)，空间 O(max m+T)。','a、b 区分奇偶；组合数是 m−b 选 a 与 m−a 选 b；乘法及时取模。',r'''
int tests;cin>>tests;vector<array<int,3>>queries(tests);int limit=0;for(auto &q:queries){cin>>q[0]>>q[1]>>q[2];limit=max(limit,q[0]);}const long long mod=998244353;vector<long long>fact(limit+1,1),inv(limit+1,1);for(int i=1;i<=limit;i++)fact[i]=fact[i-1]*i%mod;inv[limit]=power(fact[limit],mod-2,mod);for(int i=limit;i;i--)inv[i-1]=inv[i]*i%mod;auto choose=[&](int n,int k){if(k<0||k>n)return 0LL;return fact[n]*inv[k]%mod*inv[n-k]%mod;};for(auto q:queries){auto [m,a,b]=q;cout<<choose(m-b,a)*choose(m-a,b)%mod<<'\n';}
''',POW)

add('P1069','比较质因子指数所需倍增次数',
    '分解目标数量 m1^m2。对于每种细胞的单次分裂倍率 s，分解同一批质因子，所需时间是各个目标指数除以 s 中对应指数的向上取整最大值；缺少目标质因子的细胞不可行。',
    '经过 t 次分裂后，细胞总数为 s^t。能平均装进目标数量的试管，等价于 m1^m2 整除 s^t。\n\n设 m1 中质因子 p 的指数为 e，目标就需要 e·m2 个 p；若 s 中 p 的指数为 c，那么 t 轮提供 c·t 个，要求 t>=ceil(e·m2/c)。所有质因子同时满足，所以对每种细胞取这些下界的最大值。某个所需质因子完全不在 s 中，则无论多久都不行。\n\n在全部可行细胞中选最小时间。m1=1 时目标为一，初始一个细胞已经能满足，时间为零。不必实际计算巨大的幂。',
    '时间 O(sqrt m1+n·质因子数·log s)，空间 O(质因子数)。','目标指数要乘 m2；每个细胞独立计算；没有可行细胞输出 -1。',r'''
int n;long long m1,m2;cin>>n>>m1>>m2;vector<pair<long long,long long>>factors;long long x=m1;for(long long p=2;p<=x/p;p++)if(x%p==0){long long e=0;while(x%p==0){x/=p;e++;}factors.push_back({p,e*m2});}if(x>1)factors.push_back({x,m2});long long answer=LLONG_MAX;while(n--){long long s;cin>>s;long long time=0;bool ok=true;for(auto [p,need]:factors){long long c=0;while(s%p==0){s/=p;c++;}if(c==0&&need){ok=false;break;}if(need)time=max(time,(need+c-1)/c);}if(ok)answer=min(answer,time);}cout<<(answer==LLONG_MAX?-1:answer)<<'\n';
''')

add('P1414','按可能的 gcd 统计倍数数量',
    '若至少 k 个输入是 d 的倍数，就能选 k 个使 gcd 至少为 d。统计每个 d 的倍数出现数，把 d 更新到对应人数的答案，再按人数从大到小传播最大值。',
    '某 k 个数的 gcd 为 g，就说明这 k 个数全是 g 的倍数；反过来，若 d 的倍数至少有 k 个，任选 k 个后 gcd 至少为 d。因此最大可能 gcd 就是满足倍数数量不少于 k 的最大 d。\n\n先统计原值频数，然后枚举 d 的所有倍数累加，得到 cnt[d]。把 d 放到 answer[cnt[d]]，表示至少这么多人可以共享这个公因子。因为能选更多人时也能只选其中 k 人，人数从大到小做后缀最大值即可得到每个 k 的答案。\n\n重复数对应不同学生，按频数累加。无需枚举学生子集，也不必判断选出的数 gcd 是否恰好为 d，因为我们取所有可行 d 的最大值。',
    '时间 O(A log A+n)，空间 O(A+n)。','按次数统计；答案对人数做后缀最大值；k 从 1 到 n 输出。',r'''
int n;cin>>n;vector<int>a(n);int limit=0;for(int &x:a){cin>>x;limit=max(limit,x);}vector<int>frequency(limit+1),answer(n+2);for(int x:a)frequency[x]++;for(int d=1;d<=limit;d++){int c=0;for(int j=d;j<=limit;j+=d)c+=frequency[j];if(c)answer[c]=max(answer[c],d);}for(int k=n-1;k>=1;k--)answer[k]=max(answer[k],answer[k+1]);for(int k=1;k<=n;k++)cout<<answer[k]<<'\n';
''')

add('CF119A','按回合计算最大公约数',
    '轮到某人时，用他的固定数字与剩余石子数求 gcd，移走对应数量。当前不能移走的玩家输，逐回合模拟即可。',
    '每一步移走的数量由当前剩余石子数唯一决定，没有可以优化的策略。令 turn=0 表示 Simon，turn=1 表示 Antisimon；按对应固定数字计算 gcd，并从石堆中扣除。\n\n石子数为正时 gcd 至少为一且不会超过石子数，因此总会向结束推进。石子数为零时 gcd(a,0)=a，当前玩家无法移动，所以另一人获胜。代码在取走最后一颗后切换回合，最后输出当前回合的另一方。\n\n求 gcd 使用欧几里得算法，它利用 gcd(a,b)=gcd(b,a%b)，直到余数为零。',
    '时间 O(n log max(a,b,n))，空间 O(1)。','取完石子后换手，再判另一方获胜；gcd(a,0) 不为零。',r'''
int a,b,n;cin>>a>>b>>n;int turn=0;while(n){n-=gcd(turn?b:a,n);turn^=1;}cout<<(turn^1)<<'\n';
''',cases=[('1 1 1\n','0\n'),('1 1 2\n','1\n')])

add('UVA11388','由 gcd 与 lcm 的整除关系构造',
    '若给出的最小公倍数不能被最大公约数整除，就无解。否则直接取这两个数本身，它们的 gcd 与 lcm 恰好符合要求。',
    '对于任意两个正整数，最大公约数一定整除最小公倍数，因此 L%G!=0 是不可能条件。\n\n这个条件也是充分的：当 G 整除 L 时，选择 a=G、b=L，就有 gcd(a,b)=G、lcm(a,b)=L。并且任何合法 a 都是 G 的倍数，所以 G 已经是第一个数能够取得的最小值。无需分解质因数，也无需逐个寻找其它数对。\n\n每组测试只做一次取余，成功时输出 G L，失败时按原题输出 -1。',
    '每组时间 O(1)，空间 O(1)。','输入顺序是 gcd、lcm；不要计算可能溢出的乘积。',r'''
int t;cin>>t;while(t--){long long g,l;cin>>g>>l;if(l%g)cout<<-1<<'\n';else cout<<g<<' '<<l<<'\n';}
''')

add('P1029','约去最大公约数后枚举互质因子',
    '设两个数为 x·a、x·b，则需要 a·b=y/x 且 gcd(a,b)=1。枚举 y/x 的因子 a，检查互补因子是否互质；不相同的一对贡献两个有序数对。',
    '若最大公约数是 x，两个数都含有公共因子 x。约去它后，剩下的 a、b 必须互质；此时最小公倍数为 xab，因此 ab=y/x。若 y 不能被 x 整除，立即无解。\n\n枚举 a 从 1 到 sqrt(y/x)，只在它整除乘积时检查 b=(y/x)/a。gcd(a,b)=1 时得到合法数对。题目把先后顺序不同算成不同方案，所以 a!=b 时贡献二；a=b 时只贡献一，这只会在乘积为一的情况下通过互质检查。\n\n循环用 a<=product/a 判断边界，避免直接计算 a² 溢出。',
    '时间 O(sqrt(y/x)·log(y/x))，空间 O(1)。','有序数对需计交换；x 不整除 y 时为零。',r'''
long long x,y;cin>>x>>y;if(y%x){cout<<0<<'\n';return 0;}long long p=y/x,ans=0;for(long long a=1;a<=p/a;a++)if(p%a==0&&gcd(a,p/a)==1)ans+=a==p/a?1:2;cout<<ans<<'\n';
''')

add('P5436','相邻两个最大整数互质',
    'n=1 时答案为 1；否则选 n 和 n−1。它们互质，最小公倍数为 n(n−1)，且任何两个不同的合法数的乘积都不超过这个值。',
    '若选的两个整数相等，最小公倍数就是它们本身，不超过 n。若不同，把较大者记为 a、较小者记为 b，则 a<=n、b<=n−1，且 lcm(a,b)<=ab<=n(n−1)。\n\n相邻整数的任何公因数都必须整除它们的差 1，所以 gcd(n,n−1)=1。取这一对时，最小公倍数正好等于乘积，达到了刚才的上界。\n\n唯一特例 n=1，只有 (1,1) 可选，答案为 1。n 可达十亿，乘积要用 long long 保存。',
    '每组时间 O(1)，空间 O(1)。','n=1 单独处理；乘法用六十四位。',r'''
int t;cin>>t;while(t--){long long n;cin>>n;cout<<(n==1?1:n*(n-1))<<'\n';}
''',cases=[('3\n1\n2\n1000000000\n','1\n2\n999999999000000000\n')])

add('CF757B','按共同质因数计数',
    '一组数的 gcd 大于 1，当且仅当存在一个质数整除组内所有数。统计每个质数的倍数在数组中出现多少次，取最大值即可；全为 1 时仍可选一个数。',
    '若某个合法组的 gcd 大于一，这个 gcd 至少有一个质因数 p，组内每个数都被 p 整除。因此任何合法组的大小，都不超过某个质数倍数的总出现次数。\n\n反过来，把数组中所有 p 的倍数选出来，gcd 至少含因子 p，是合法组。所以逐个质数统计其倍数出现次数便能达到最优。重复的值代表不同位置，出现几次就应计几次。\n\n先建立值域频数，再用筛法找质数并按倍数累加。没有任何可共享的质因数时，题目仍允许保留单个元素，答案至少为一。',
    '时间 O(A log log A)，空间 O(A)，A 为最大值。','统计出现次数而非不同值数；答案至少为 1。',r'''
int n;cin>>n;vector<int>a(n);int limit=1;for(int &x:a){cin>>x;limit=max(limit,x);}vector<int>freq(limit+1);for(int x:a)freq[x]++;vector<char>composite(limit+1);int ans=1;for(int p=2;p<=limit;p++)if(!composite[p]){int total=0;for(int j=p;j<=limit;j+=p){total+=freq[j];if(j>p)composite[j]=1;}ans=max(ans,total);}cout<<ans<<'\n';
''')

add('P4549','所有数的 gcd 决定最小正线性组合',
    '裴蜀定理说明，整数系数线性组合能得到的最小正整数就是所有输入数绝对值的最大公约数。逐项求 gcd 即可。',
    '两个整数 a、b 的所有整数线性组合 ax+by 都是 gcd(a,b) 的倍数；扩展欧几里得算法又保证 gcd(a,b) 本身能被某组整数系数表示。所以最小正值就是这个 gcd。\n\n对多个数，可以先把前两个数能形成的组合压缩为它们的 gcd，再与第三个数合并，依次进行，最终得到全部数的 gcd。负号不改变公约数，因此统一取绝对值。\n\n累积变量初始化为零，利用 gcd(0,a)=|a| 自然处理第一个数。题目允许零时，它不会影响其余数的 gcd。',
    '时间 O(n log A)，空间 O(1)。','系数可为负数；输入取绝对值；累积 gcd 从 0 开始。',r'''
int n;cin>>n;long long g=0;while(n--){long long x;cin>>x;g=gcd(g,llabs(x));}cout<<g<<'\n';
''')

add('P10031','只保留出现奇数次的 gcd',
    'gcd(i,n)=d 的次数为 φ(n/d)。欧拉函数只有在参数为 1 或 2 时为奇数，因此 n 为奇数时答案为 n，n 为偶数时答案为 n 异或 n/2。',
    '异或中相同的值出现两次就抵消，因此只需知道每个 gcd 值的出现次数是奇数还是偶数。固定 n 的因数 d，令 i=d·j，那么 gcd(i,n)=d 等价于 gcd(j,n/d)=1，满足条件的 j 恰有 φ(n/d) 个。\n\n当整数 k>2 时，与 k 互质的剩余类可以按 j 与 k−j 两两配对，且不会是同一个数，所以 φ(k) 为偶数。只有 φ(1)=1、φ(2)=1 为奇数。\n\n对应 n/d=1 得到 d=n，始终保留；当 n 为偶数时，n/d=2 对应 d=n/2，也保留。其它全部抵消。整个过程不需要分解 n，适用于十的十八次方。',
    '每组时间 O(1)，空间 O(1)。','偶数分支使用按位异或 ^，不是幂；n=1 输出 1。',r'''
int t;cin>>t;while(t--){long long n;cin>>n;cout<<(n%2?n:n^(n/2))<<'\n';}
''')

add('CF687B','检查所有模数能否确定 k 的余数',
    '所有给定余数把原数确定到它们最小公倍数的同余类。能确定模 k 的余数，当且仅当 k 整除这个最小公倍数。只累积 gcd(a_i,k) 的 lcm，避免大整数。',
    '两个整数对所有给定模数取余相同，当且仅当它们之差被所有模数整除，也就是被这些模数的最小公倍数 L 整除。要进一步保证它们模 k 相同，就必须且只须 k 整除 L。\n\n实际 L 可能极大，但只关心 k 所含的质因数及指数。把每个 a_i 替换为 gcd(a_i,k) 后，所有因子都来自 k，不影响判断 k 是否被最终 lcm 覆盖。累积 lcm 永远是 k 的因数，不会爆炸。\n\n更新时写 current/gcd(current,g)*g，先除再乘。读完全部数后，current==k 就输出 Yes，否则 No。',
    '时间 O(n log A)，空间 O(1)。','不要直接累乘所有数；只保留 k 的因数；lcm 先除后乘。',r'''
int n;long long k;cin>>n>>k;long long value=1;while(n--){long long x;cin>>x;long long g=gcd(x,k);value=value/gcd(value,g)*g;}cout<<(value==k?"Yes":"No")<<'\n';
''')

add('P2424','交换求和顺序后整除分块',
    '约数 d 在 1 到 N 中出现 floor(N/d) 次，因此前缀约数和为 Σ d·floor(N/d)。同一商对应一段连续的 d，用等差数列求和，区间答案是 F(y)−F(x−1)。',
    '直接对每个整数枚举约数会重复大量工作。反过来固定约数 d：在 1 到 N 中，它整除 d、2d、…，共 floor(N/d) 个数，所以贡献 d·floor(N/d)。\n\n设当前左端为 l，商 q=N/l。这个商保持不变的最远右端为 r=N/q；区间 [l,r] 内的贡献就是 q·(l+r)(r−l+1)/2。结算后令 l=r+1。不同整商只有 O(sqrt N) 种。\n\n定义 F(0)=0，闭区间 [x,y] 的答案为 F(y)−F(x−1)。中间乘积使用 __int128，最终同样用十进制输出，避免先乘后除时溢出。',
    '时间 O(sqrt y)，空间 O(1)。','右端是 N/(N/l)；x=1 时前缀为 0；乘积先转宽整数。',r'''
long long x,y;cin>>x>>y;auto solve=[](long long n){__int128 ans=0;for(long long l=1,r;l<=n;l=r+1){long long q=n/l;r=n/q;ans+=(__int128)(l+r)*(r-l+1)/2*q;}return ans;};__int128 v=solve(y)-solve(x-1);string s;do{s.push_back('0'+v%10);v/=10;}while(v);reverse(s.begin(),s.end());cout<<s<<'\n';
''')

add('P2303','按 gcd 的取值分组',
    '若 gcd(i,n)=d，约去 d 后共有 φ(n/d) 个合法 i，所以答案为 Σ(d|n) d·φ(n/d)。成对枚举约数并计算欧拉函数即可。',
    '要求所有 gcd 的和，可以把产生同一个 gcd 的整数放在一起。固定 n 的因数 d，令 i=dj，则 gcd(i,n)=d 等价于 j 与 n/d 互质。在 1 到 n/d 中有 φ(n/d) 个这样的 j，每个贡献 d。\n\n因此答案是所有因数 d 对应的 d·φ(n/d) 之和。先分解 n 得到不同质因数。计算某个因数的欧拉函数时，仅检查这些质因数，按 φ(x)=x·∏(1−1/p) 依次先除 p 再乘 p−1。\n\n枚举到平方根时，同时处理 d 和 n/d，二者相等时只处理一次。乘法和答案使用 long long。',
    '时间 O(sqrt n + τ(n)·ω(n))，空间 O(ω(n))，τ 是约数数，ω 是不同质因数数。','平方因数只算一次；φ(1)=1；先除再乘。',r'''
long long n;cin>>n;long long x=n;vector<long long>primes;for(long long p=2;p<=x/p;p++)if(x%p==0){primes.push_back(p);while(x%p==0)x/=p;}if(x>1)primes.push_back(x);auto phi=[&](long long x){long long r=x;for(long long p:primes)if(x%p==0)r=r/p*(p-1);return r;};long long ans=0;for(long long d=1;d<=n/d;d++)if(n%d==0){ans+=d*phi(n/d);if(d!=n/d)ans+=(n/d)*phi(d);}cout<<ans<<'\n';
''')

add('P4132','矩形格点被斜线分成两侧',
    '当 p、q 为不同奇质数时，两段求和分别数出矩形格点在直线两侧的数量，总和为 ((p−1)/2)((q−1)/2)。若两质数相等，直接求两份 1+…+(p−1)/2。',
    '在横坐标 1 到 (p−1)/2、纵坐标 1 到 (q−1)/2 的整数格点矩形中，固定横坐标 k，floor(kq/p) 数出直线 y=qx/p 下方的格点；交换两轴后，另一段求和数出直线上方的格点。\n\n若 p、q 是不同质数，它们互质，矩形内部没有落在直线上的整数格点，因为 px=qy 会要求 p 整除 x，而 x<p。于是两部分不重不漏地覆盖整个矩形，答案就是长乘宽。\n\n原题只说两个奇质数，没有要求不同。p=q 时，两份 floor(kq/p) 都等于 k，答案为 h(h+1)，其中 h=(p−1)/2。这个分支不能误用无对角格点的公式。',
    '时间 O(1)，空间 O(1)。','不能遗漏 p=q；使用 unsigned long long 保存乘积。',r'''
unsigned long long p,q;cin>>p>>q;auto a=(p-1)/2,b=(q-1)/2;cout<<(p==q?a*(a+1):a*b)<<'\n';
''',cases=[('3 3\n','2\n')])

add('P2911','枚举三个骰子的点数',
    '逐个枚举三个骰子的所有点数组合，累计和的出现次数，再从小到大找出现次数最多的和。',
    '三个骰子的每一面等概率，任意点数组合的概率相同，所以和的概率与产生这个和的组合数成正比。\n\n开一个长度为三个最大点数之和加一的频数数组。三层循环枚举 x、y、z，把 freq[x+y+z] 加一。然后按和递增扫描，仅在频数严格更大时更新答案。这样出现次数相同时，自动保留较小的和。\n\n没有必要使用浮点概率，也不能仅凭骰子平均值四舍五入，因为多个和可能并列最高。',
    '时间 O(s1·s2·s3)，空间 O(s1+s2+s3)。','点数从 1 开始；并列时选择最小和。',r'''
int a,b,c;cin>>a>>b>>c;vector<int>cnt(a+b+c+1);for(int x=1;x<=a;x++)for(int y=1;y<=b;y++)for(int z=1;z<=c;z++)cnt[x+y+z]++;int ans=0;for(int i=1;i<(int)cnt.size();i++)if(cnt[i]>cnt[ans])ans=i;cout<<ans<<'\n';
''')

add('CF1178C','边界选择唯一确定内部',
    '合法铺法由第一行与第一列的二元选择决定，共有 h+w 个独立二元自由度，因此答案是 2^(h+w)，对 998244353 取模。',
    '可以从每块砖在横向和纵向边界上的相位来描述摆放。相邻位置需要一致拼接，选好首行与首列的相位后，其余位置的选择都被左侧和上侧确定。\n\n边界总共提供 h+w 个独立的二元选择，每一种边界配置恰好扩展为一份合法铺法，不同边界配置得到不同铺法。因此方案数为 2 的 h+w 次方。\n\n使用快速幂：把指数按二进制拆开，当前位为一时乘入对应的 2^(2^k)，每轮底数平方、指数右移。每次乘法立即取模。',
    '时间 O(log(h+w))，空间 O(1)。','指数是 h+w；模数为 998244353。',r'''
long long h,w;cin>>h>>w;cout<<power(2,h+w,998244353)<<'\n';
''',POW)

add('P1754','零钱前缀约束对应 Catalan 数',
    '手持五十元的球迷让零钱加一张，手持一百元的球迷需要消耗一张。任意队列前缀中五十元人数不少于一百元人数，恰好对应合法括号序列，答案为第 n 个 Catalan 数。',
    '把五十元球迷记为左括号，一百元球迷记为右括号。售票处初始没有零钱，每位一百元球迷都要找回五十元，所以任意前缀中左括号数必须不少于右括号数；最终两者各 n 个。这与合法括号序列一一对应。\n\n由反射原理，全部 C(2n,n) 个等量括号序列中，不合法的有 C(2n,n−1) 个，相减得到 Catalan(n)=C(2n,n)/(n+1)。相邻项约分可得 C_i=C_(i−1)·(4i−2)/(i+1)，C_0=1，每次先乘后除且精确整除。\n\n原题把同面值球迷视为同类，不再乘 n!。n≤20，答案最大 6564120420，超出三十二位但能放入 long long；递推乘法的中间值也在六十四位范围内，无需高精度结构。',
    '时间 O(n)，空间 O(1)。','同面值视作同类；C_0=1；先乘后整除；使用 long long。',r'''
int n;cin>>n;long long ans=1;for(int i=1;i<=n;i++)ans=ans*(4*i-2)/(i+1);cout<<ans<<'\n';
''')

add('P3197','全部染色减去相邻不同的方案',
    '全部安排有 m^n 种。没有相邻同教派的安排中，第一个人有 m 种选择，后面每个人有 m−1 种，所以答案为 m^n−m(m−1)^(n−1)。',
    '直接统计至少一对相邻者相同，会让同时出现多对相同的方案被重复计算。改为统计补集：所有相邻位置都不同。\n\n第一人可以属于任意一个教派，有 m 种。固定前一个人的教派后，当前人只能避开这一种，因此始终有 m−1 种，不受更早位置影响。由乘法原理，补集大小为 m·(m−1)^(n−1)。\n\n所有安排为 m^n，两者相减就是至少存在一对相邻相同的方案数。分别快速幂取模，最后加上模数再取余，避免负数。',
    '时间 O(log n)，空间 O(1)。','模数为 100003；减法规范化；n=1 时答案为 0。',r'''
long long m,n;cin>>m>>n;const long long mod=100003;cout<<(power(m%mod,n,mod)-(m%mod)*power((m-1)%mod,n-1,mod)%mod+mod)%mod<<'\n';
''',POW)

add('P6075','单个元素的阶梯边界独立选择',
    '对一个固定元素，只看它在哪些子集中出现。包含关系把出现区域约束为阶梯形，其边界对应 k 次二元选择，共 2^k 种。n 个元素独立，答案为 2^(nk)。',
    '集合包含关系可以逐元素检查：某个元素若出现在右侧或下侧的子集中，就必须同时出现在它的前驱中。因此每个元素的出现位置构成从左上角扩张的阶梯区域。\n\n在边长为 k 的三角格中，这样的阶梯区域与从 {1,…,k} 中选择若干互不相同的阶梯长度一一对应：依次取边界的严格下降长度即可恢复整个区域。每个长度可选或不选，所以一个元素有 2^k 种合法出现模式。k=2 时四种模式为全不出现、只在顶格出现、在前两格出现、全部出现。\n\n不同元素是否出现在某个集合中互不干涉，选择好每个元素的合法模式即可确定全部子集。由乘法原理得到 (2^k)^n。代码先算 2^k，再对 n 快速幂，避免直接计算 n·k 时超出输入类型。',
    '时间 O(log n+log k)，空间 O(1)。','空子集允许；元素彼此独立；模数为 1000000007。',r'''
long long n,k;cin>>n>>k;const long long mod=1000000007;cout<<power(power(2,k,mod),n,mod)<<'\n';
''',POW)
