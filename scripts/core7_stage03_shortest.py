"""Problem-specific path models and ordered enumeration in the third stage."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
G=A+['graphs','shortest-path','heap']

add('CF910A','每次落到当前能到达的最右荷叶',
    '青蛙从一号位置出发，只能向右跳一至 d 格，并且只能落在标为一的位置。求到 n 号位置的最少跳数，无法到达输出 -1。',
    r'''从当前位置往右查看至多 d 格，选择其中最右的一片荷叶。更右的落点不会妨碍后续：它已跳过的较左位置不再需要，前方任一原本可达的位置离它只会更近。重复至终点；若前方 d 格内没有荷叶，任何方案都不能继续。''',
    r'''例如荷叶在一、四、六、八号，最大跳四格。从一号可选四号，接着直接到八号，只用两次。若刻意停在更靠左的位置，不会换来更远的下一跳。

把论证落到第 t 次跳跃结束后的最远位置。假设贪心此时的位置 g 不小于任意另一方案的位置 p。另一方案下一次落在 q：若 q 不超过 g，贪心已经至少走到那里；若 q 大于 g，那么 q-g 不超过 q-p，也就不超过 d，且 q 本身有荷叶，所以贪心下一跳所选的最右荷叶至少为 q。初始两者都在一号，归纳可知同样跳数下贪心总能达到最右的位置。

因此，一旦某个方案能在 t 次内到终点，贪心也不晚于它到达，得到最少跳数。若贪心在当前位置前方 d 格内找不到落点，则所有不超过它的位置都无法越过这段空隙。

实现用字符串的零下标，起点为零，终点为 n-1。从 min(n-1,current+d) 向左找第一个字符一；如果退回 current，输出 -1。每成功跳一次才加一，不把起点计为一次跳跃。''',
    r'''int n,d;cin>>n>>d;string s;cin>>s;int current=0,jumps=0;
// 同样跳数下保持位置最靠右。
while(current<n-1){
    int next=min(n-1,current+d);while(next>current&&s[next]=='0')--next;
    if(next==current){cout<<-1<<'\n';return 0;}
    current=next;++jumps;
}cout<<jumps<<'\n';''',
    '只能向右；最远位置必须确有荷叶；原地不计一次跳跃；找不到新落点立即输出 -1。',
    r'至多 n-1 次跳跃，每次检查至多 d 个位置，时间 $O(nd)$，字符串外空间 $O(1)$。',tags=['贪心'],lessons=A+['strings'])

add('CF910A','按位置递推到达每片荷叶的最少跳数',
    '只能向右跳一至 d 格并落在荷叶上，求从一号到 n 号的最少跳数；不能到达时输出 -1。',
    r'''设 best[i] 为到达 i 的最少跳数，起点为零次。只有 i 有荷叶时才检查前方转移的来源 j，其中 max(0,i-d)≤j<i；对可达的 j 取 best[j]+1 的最小值。所有来源都在左侧，按位置递增即可。''',
    r'''先看最后一次跳跃。若它从 j 跳到 i，则 j<i、i-j≤d，且 i 有荷叶。最后这一跳花一次，此前至少需要 best[j] 次，所以最佳答案是在所有合法 j 中取 best[j]+1 的最小值。

初始化 best[0]=0，其余为不可达的哨兵值。逐个考察 i，有荷叶才计算；没有荷叶的位置保持不可达，也就不能成为后续跳跃来源。来源都小于 i，故计算时它们的结果已确定。

任一可达路径都有上述最后一跳，因此没有漏掉合法方案；任一转移又确实能在到达 j 后跳到 i，因此不会产生虚假的更小跳数。代码只在来源可达时加一，最后检查终点是否仍为哨兵。

这份递推直接枚举所有可能的最后一步，不依赖最远落点的贪心性质，便于独立核对贪心实现。两者都适合 n≤100 的范围，原题只要求跳数，无需恢复路线。''',
    r'''int n,d;cin>>n>>d;string s;cin>>s;const int INF=1000000000;
vector<int>best(n,INF);best[0]=0;
// 枚举最后一跳的来源，只允许落在荷叶。
for(int i=1;i<n;++i)if(s[i]=='1'){
    for(int j=max(0,i-d);j<i;++j)if(best[j]!=INF)best[i]=min(best[i],best[j]+1);
}cout<<(best[n-1]==INF?-1:best[n-1])<<'\n';''',
    '没有荷叶的位置不能落脚或转出；起点跳数为零；仅从可达来源加一。',
    r'时间 $O(nd)$，空间 $O(n)$。',tags=['线性 DP'],lessons=A+['strings','dp'],key='position-dp')

add('P1339','正权无向道路上的单源最短路',
    '无向图的每条道路有正长度，求 s 到 t 的最短路。存在平行边时仍按各自道路处理。',
    r'''以 s 为起点做 Dijkstra：dist[s]=0，其余未确定；小根堆每次取出当前距离最小的点。沿 u→v 尝试用 dist[u]+w 缩短 dist[v]，更新后入堆。跳过与当前 dist 不同的旧堆条目，最终读取 dist[t]。''',
    r'''道路经过多少条不重要，总长度才是目标。例如一条长度十的直达路可能不如两条各长三的路，普通 BFS 按边数分层不能用于任意正权道路。

dist[v] 保存目前找到的从 s 到 v 的最短长度，是某条实际路径的长度，因而不会小于真正最短路。小根堆中取出尚未过期的最小距离 u 时，这个长度已经无法再改小：若有更短路线，从已经确定的部分第一次进入未确定部分的那一步，会给某个未确定点提供不大于这条路线总长的候选；它本应先于 u 被取出，矛盾。这里用到所有后续边长非负。

确定 u 后，检查每条邻边。若经 u 到 v 更短，就把新长度写入 dist[v]，再把这份候选放入堆。C++ priority_queue 默认先取最大值，本题用 greater 的 pair 小根堆，pair 第一项保存距离，第二项保存编号。

同一点可能多次改善，堆里旧条目不会自动删除。取出 (du,u) 后若 du!=dist[u] 就跳过，避免反复扫描过时状态。无向边必须双向存储；平行边可全部保留，更短的一条自然生效。程序用 long long 存路径和；若把方法用于没有 s-t 路径的图，INF 只表示不可达，不能当作一段真实距离。''',
    r'''int n,m,s,t;cin>>n>>m>>s>>t;vector<vector<pair<int,int>>>g(n+1);
for(int i=0;i<m;++i){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}
const long long INF=(1LL<<62);vector<long long>dist(n+1,INF);
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;
// 堆条目保存这次入堆时的距离，旧条目稍后跳过。
dist[s]=0;pq.push({0,s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}if(dist[t]==INF)cout<<-1<<'\n';else cout<<dist[t]<<'\n';''',
    '无向边双向存；堆按距离排序；跳过过时条目；不能按道路条数使用普通 BFS。题面未约定无路时的数值，-1 仅为通用防御分支。',
    r'保留平行边的二叉堆实现时间 $O(n+m\log(m+1))$，空间 $O(n+m)$。',tags=['最短路'],lessons=G)

add('P1828','从有牛的牧场出发，累加各目的地的路程',
    '无向道路上有 N 头牛，同一牧场可以有多头。选一处放糖，让所有牛各走最短路到达，要求总路程最小。',
    r'''统计 count[u]。每个有牛的牧场 u 做一次 Dijkstra，向每个可达牧场 v 的总费用加 count[u]·dist(u,v)。最后只在所有牛都可到达的 v 中取最小值。相同出发牧场只算一次最短路。''',
    r'''候选地点的费用是每头牛到它的最短距离之和，而不是图的最小生成树长度；不同牛可以重复经过同一条路，并不会把那条路只付一次。

若某个牧场住了三头牛，它们到候选 v 的最短距离都是五，就应贡献十五。先统计牛的数量，再从每个非空牧场求最短路，这样不需要为每头同住的牛重复计算。

对一次起点 u 的结果，将 count[u]·dist[v] 加到 total[v]。同时记录 reached[v]，加上本次能够到达的 count[u] 头牛。只有 reached[v]==N 的地点才是共同可达地点，不能把不可达的 INF 乘牛数后加入费用。

每一次 Dijkstra 正确求得这组牛到所有目的地的最短距离。累加之后，total[v] 恰好按每头牛计算一次，因此逐个候选取最小值就是全局最优。答案不要求候选原先住着牛，也不要求某头牛的路程单独最短。

牧场至多八百、道路至多一千四百五十，用稀疏图的堆最短路很合适。以 K 表示有牛的牧场数，K≤min(N,P)。total 用 long long，独立检查共同可达条件，保留平行道路即可。''',
    r'''int N,P,C;cin>>N>>P>>C;vector<int>count(P+1);
for(int i=0,u;i<N;++i){cin>>u;++count[u];}
vector<vector<pair<int,int>>>g(P+1);for(int i=0;i<C;++i){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}
const long long INF=(1LL<<62);vector<long long>total(P+1);vector<int>reached(P+1);
using State=pair<long long,int>;
// 同住的牛共享一次最短路，再乘头数累加。
for(int s=1;s<=P;++s)if(count[s]){
    vector<long long>dist(P+1,INF);priority_queue<State,vector<State>,greater<State>>pq;// 堆条目保存这次入堆时的距离，旧条目稍后跳过。
dist[s]=0;pq.push({0,s});
    while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
        for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
    }
    for(int v=1;v<=P;++v)if(dist[v]!=INF){total[v]+=count[s]*dist[v];reached[v]+=count[s];}
}long long answer=INF;for(int v=1;v<=P;++v)if(reached[v]==N)answer=min(answer,total[v]);
cout<<(answer==INF?-1:answer)<<'\n';''',
    '同住的多头牛要乘数量；候选遍历全部牧场；不可达不能参与加法；道路总长和最小生成树均不是本题目标。无共同可达地点时的 -1 是防御分支。',
    r'设 K 为有牛的牧场数，时间 $O(K(P+C\log(C+1)))$，空间 $O(P+C)$。',tags=['最短路'],lessons=G)

add('P3905','完好道路记零，损坏道路记修复长度',
    '道路网络中一部分道路被破坏，只需恢复 A 与 B 的连通；最小化实际修复的道路总长度，不要求修复整个王国。',
    r'''把完好道路的费用设为零，把损坏道路的费用设为原长度，不存在的道路仍不可走。在这个非负费用图上求 A 到 B 的最短路，即为最小修复费用。n≤100，可以直接用矩阵 Dijkstra。''',
    r'''原本长一百但仍完好的道路不需要修复，费用是零；原本长三且已损坏的道路需要付三。我们最小化的是修复支出，而非最终行程长度，因此两类道路必须重新赋权。

任何把 A、B 连通的修复方案中，都能找出一条 A 到 B 的简单路径。只修复这条路径上的损坏道路，不会失去 A-B 连通，也不会增加费用。因此最优方案可以缩成一条路径，无需最小生成树来连接全部城市。

反过来，任选一条 A-B 路径，只需按新边权的和修好其中受损部分，就能沿路径通行。所以任意可行修复费用不小于新图最短路，而新图最短路又确实能实现，两者相等。

先保存原道路长度，将存在的道路费用初始化成零，再读损坏列表，把这些位置恢复成原长度。不存在的边保持 INF，不能因为矩阵默认零而被当成免费路。

矩阵 Dijkstra 每次扫描全部顶点，取未确定点中 dist 最小者，再扫描这一行更新其它点。零费用边也合法，不影响非负边权的正确性。A、B 相同时无需任何修复。''',
    r'''int n,m;cin>>n>>m;const long long INF=(1LL<<60);
vector<vector<long long>>length(n+1,vector<long long>(n+1,INF)),cost=length;
for(int i=1;i<=n;++i)length[i][i]=cost[i][i]=0;
for(int i=0;i<m;++i){int u,v,w;cin>>u>>v>>w;length[u][v]=length[v][u]=w;cost[u][v]=cost[v][u]=0;}
// 完好路费用已经是零，只有损坏路恢复为修复长度。
int d;cin>>d;while(d--){int u,v;cin>>u>>v;cost[u][v]=cost[v][u]=length[u][v];}
int A,B;cin>>A>>B;vector<long long>dist(n+1,INF);vector<char>used(n+1);dist[A]=0;
for(int step=0;step<n;++step){int u=-1;for(int v=1;v<=n;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    if(u==-1||dist[u]==INF)break;used[u]=true;
    for(int v=1;v<=n;++v)if(cost[u][v]!=INF)dist[v]=min(dist[v],dist[u]+cost[u][v]);
}cout<<(dist[B]==INF?-1:dist[B])<<'\n';''',
    '只给完好且实际存在的道路赋零；损坏道路保留原长度；目标只连 A、B，不是全图生成树。',
    r'时间与空间均为 $O(n^2)$。',tags=['最短路'],lessons=G)

add('P11966','从学校做一次最短路，回答所有同学',
    '无向带正长度道路上，一秒走一米。学校固定，多个同学住在不同结点，分别求走到学校的最少秒数。官方原题保证图连通。',
    r'''无向图中从家到学校的最短距离等于从学校到家的距离。只以学校 s 为起点执行一次堆优化 Dijkstra，之后每个 h_i 直接输出 dist[h_i]。路径和用 long long。''',
    r'''若给每位同学分别跑最短路，最多二十万次查询会使工作量过大。所有查询的终点都是同一所学校，而且道路双向：将任意家到学校的路线倒过来，长度保持不变，也是一条合法的学校到家路线。两边的最优长度因此相等。

从学校一次求出 dist[v]，便同时得到全部家庭的答案。堆里按距离取最小候选，非负路长保证当前最小的未过期距离可以确定；随后沿每条邻边尝试缩短到相邻城市的距离。

例如样例中，学校在三号。它到四号为一，到一号可以经四号走三，到五号经四号走四；按家庭输入的五、一、四号依次输出四、三、一，不能按城市编号重排查询。

二十万个点的一条长链，边长可达一百万，最短路可能接近二千亿，int 不够。边长可以暂存 int，候选计算必须由 long long 的 du+w 进行。小根堆的第一项也要是 long long。

洛谷缓存的范围段没有收录连通保证；官方 GESP 2025 年三月八级原卷的数据范围明确保证图连通，因此这里不另造不可达的输出约定。[官方原卷](https://gesp.ccf.org.cn/101/attach/1669257026863136.pdf)。''',
    r'''int n,m,s,q;cin>>n>>m>>s>>q;vector<vector<pair<int,int>>>g(n+1);
for(int i=0;i<m;++i){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});g[v].push_back({u,w});}
const long long INF=(1LL<<62);vector<long long>dist(n+1,INF);
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;// 堆条目保存这次入堆时的距离，旧条目稍后跳过。
dist[s]=0;pq.push({0,s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}while(q--){int home;cin>>home;cout<<dist[home]<<'\n';}''',
    '学校是固定起点；输入是无向边；查询保持输入次序；一米一秒无需额外换算；距离与堆键使用 long long。',
    r'时间 $O(n+m\log(m+1)+q)$，空间 $O(n+m)$。',tags=['最短路'],lessons=G)

add('AT_arc064_c','把圆内的免费移动缩成一个结点',
    '从给定起点走到终点，速度为一。任意圆形屏障内部不会受辐射，圆外的行走时间才计入费用；圆可以相交、包含。求最小辐射时间。',
    r'''将每个圆视为一个结点，起终点视为半径为零的圆。两个结点之间的费用是 max(0,圆心距-两半径和)。圆内移动免费，重叠圆之间也免费。这个完全图边权非负，做矩阵式 Dijkstra，按需计算边权即可。''',
    r'''计费的是在屏障外的时间，走过的总路长可以更长。进入一个圆后，可以在圆内走到任意出发位置而不再增加辐射时间，因此只需记录当前处于哪个圆，不必记录进入圆周的精确位置。

两圆圆心距为 D，半径分别为 r、R。若互不相交，两圆之间最短的暴露间隙是 D-r-R，沿圆心连线便可走到；若相交或包含，可以在它们的并集内转移，费用为零。统一写成

$$w(i,j)=\max(0,\operatorname{distance}(i,j)-r_i-r_j).$$

起点和终点是没有面积的免费位置，把它们作为半径零的圆，便能用同一公式表示起点到圆、圆到终点以及直接步行。

为什么这样的缩点没有漏掉更好的曲线路线？沿任意实际路线，记录依次利用的屏障；相邻两块屏障之间的暴露长度至少是它们的最小间隙，所以图上的最短费用不大于这条实际路线的费用。反过来，图中的一串圆可以通过免费圆内移动及最短间隙逐段连接。若途中又经过其它屏障，只会进一步减小暴露，故实际最优也不大于图最短路。两边夹住，结果相等。

圆最多一千个，完全图有平方级边。用每次线性选最小距离的 Dijkstra，只保存圆与 dist，每次处理 u 时现算 u 与其它圆之间的费用，不建立庞大的边表。坐标差、平方根与距离均使用 long double，输出足够小数位；不能把相交圆的负间隙作为负权边。''',
    r'''long double sx,sy,tx,ty;cin>>sx>>sy>>tx>>ty;int n;cin>>n;
vector<long double>x(n+2),y(n+2),radius(n+2);x[0]=sx;y[0]=sy;x[n+1]=tx;y[n+1]=ty;
for(int i=1;i<=n;++i)cin>>x[i]>>y[i]>>radius[i];
const long double INF=1e100L;vector<long double>dist(n+2,INF);vector<char>used(n+2);dist[0]=0;
for(int step=0;step<n+2;++step){int u=-1;for(int v=0;v<n+2;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    used[u]=true;for(int v=0;v<n+2;++v){
        // 重叠或包含时不存在暴露间隙。
        long double gap=max(0.0L,hypotl(x[u]-x[v],y[u]-y[v])-radius[u]-radius[v]);
        dist[v]=min(dist[v],dist[u]+gap);
    }
}cout<<fixed<<setprecision(18)<<dist[n+1]<<'\n';''',
    '圆内免费并非圆是障碍；相交和包含时费用截成零；起终点半径为零；先用浮点类型作坐标差；不要把结果四舍五入成整数。',
    r'时间 $O(N^2)$，空间 $O(N)$。',tags=['最短路','计算几何'],lessons=G+['geometry'],checker='path_decimal')

add('P1608','先去掉重复边信息，再统计最短点序列',
    '正权有向图中，求一号到 N 号的最短长度和最短路线数。两条方案只有经过的点编号序列不同才算不同，重复道路记录不应重复计数。',
    r'''先用矩阵保存每对有向端点的最小边权，合并所有重复信息。Dijkstra 维护 dist 与 ways：更短时替换距离并令 ways[v]=ways[u]，同样短时加 ways[u]。边权严格为正，最短路前驱都先于后继确定。无路输出 No answer。''',
    r'''一到二的长度一如果被输入两次，点序列一、二仍只有一种。若同一对端点还输入长度五，只需留下长度一：更长的平行道路不可能属于最短方案。因此应先按有向端点去重并取最小权值，不能一读到边就把它当作独立路线。

dist[u] 是从一号到 u 的最短长度，ways[u] 是达到这个长度的不同点序列数。初始 dist[1]=0、ways[1]=1，表示只有一条空行程。处理已确定的 u 时，候选长度为 dist[u]+w(u,v)。候选更短说明原来的全部路线都不再最优，计数必须替换成 ways[u]；候选相等，则把这些以 u 为倒数第二个点的路线加入 ways[v]。

每条最短路线有唯一的倒数第二个点，去重之后，不同前驱产生的序列也不会重复。正边权使 dist[u]<dist[v]，所以任何最短前驱一定先被 Dijkstra 处理，ways[u] 已完整。若允许零权边，这个计数顺序不再自动成立，不能照搬本实现。

用矩阵 Dijkstra 匹配 N≤2000、边信息最多平方级的范围，既方便去重，也避免保存数百万份重复条目。输入时间为 O(E)，选择与松弛为 O(N²)。

题目只保证最终答案不超过  $2^{30}$ ，中间无关城市的路线数仍可能很大。代码把计数截在  $2^{30}$ +1：这是超过合法最终答案的标记，避免溢出，距离计算不受影响。若一个截断的点能沿最短边继续到终点，终点也至少有这么多方案，与保证矛盾；因此合法终点答案仍精确。''',
    r'''int n,E;cin>>n>>E;const int ABSENT=1000000000;
vector<vector<int>>weight(n+1,vector<int>(n+1,ABSENT));
// 同端点的多份信息不能产生不同点序列。
for(int i=0;i<E;++i){int u,v,w;cin>>u>>v>>w;weight[u][v]=min(weight[u][v],w);}
const long long INF=(1LL<<60),CAP=(1LL<<30)+1;vector<long long>dist(n+1,INF),ways(n+1);vector<char>used(n+1);
dist[1]=0;ways[1]=1;
for(int step=0;step<n;++step){int u=-1;for(int v=1;v<=n;++v)if(!used[v]&&(u==-1||dist[v]<dist[u]))u=v;
    if(u==-1||dist[u]==INF)break;used[u]=true;
    for(int v=1;v<=n;++v)if(weight[u][v]!=ABSENT){long long candidate=dist[u]+weight[u][v];
        if(candidate<dist[v]){dist[v]=candidate;ways[v]=ways[u];}
        else if(candidate==dist[v])ways[v]=min(CAP,ways[v]+ways[u]);
    }
}if(dist[n]==INF)cout<<"No answer\n";else cout<<dist[n]<<' '<<ways[n]<<'\n';''',
    '边有方向；同端点边只留最短的一份；更短覆盖计数，相等才累加；没有路径只输出 No answer。',
    r'时间 $O(N^2+E)$，空间 $O(N^2)$。',tags=['最短路','线性 DP'],lessons=G+['dp'])

add('P2737','每个余数只保留最小可组成总量',
    '给定若干正包装容量，每种可以使用任意多个。求不能组成的最大正整数；若全部可组成或不能组成的数无上界，输出零。',
    r'''取最小容量 m，建立 m 个余数状态。加入容量 b 相当于从余数 u 到 (u+b)%m，边权为 b。Dijkstra 从余数零求每个余数的最小可组成值 dist[r]。若某余数不可达，缺失值无穷多；否则每类最大缺失值为 dist[r]-m，整体取最大并与零比较。''',
    r'''最小容量 m 本身可以无限使用。若已经能组成某个数 x，就一定能组成 x+m、x+2m 等同余的更大数。因此，同一余数类只需找出最早能组成的数，其后不会再出现空洞。

以容量三、六、十为例，对三取余，余数零的最小值为零，余数一的最小值为十，余数二的最小值为二十。余数二里的十七尚不能组成，再加三得到二十后，该类全部可行，所以它给出全局答案十七。

怎样求每类的最小值？状态 u 表示当前总数模 m 为 u，选择一个包装 b 令总数增加 b，余数变为 (u+b)%m。以增加的总数为边权，任意从零出发的路径恰好是一串包装选择，路径长度就是组合总量；反过来任意包装组合也对应一条路径。故 dist[r] 正是所需最小值。

若某个余数从未可达，这类正整数就全都不可组成，最大缺失值没有上界，按题意输出零。若全部可达，对每个 r，dist[r]-m 是该类最后一个尚不可组成的整数；它之前的数都更小，它之后的同余数可通过加最小包装得到。取各类最大值即可。若结果为负，说明所有正整数均可组成，仍输出零。

不需要猜一个足够大的完全背包上限，也不用先知道最大答案。m≤256，隐式余数图很小，边在松弛时逐个枚举容量即可。零号的距离为零表示不选任何包装，这是合法的起始组合。''',
    r'''int n;cin>>n;vector<int>b(n);for(int &v:b)cin>>v;int m=*min_element(b.begin(),b.end());
const long long INF=(1LL<<60);vector<long long>dist(m,INF);dist[0]=0;
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;pq.push({0,0});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    // 加一个包装，状态只记录总量的余数。
    for(int value:b){int v=(u+value)%m;if(du+value<dist[v]){dist[v]=du+value;pq.push({dist[v],v});}}
}long long answer=0;for(long long d:dist){if(d==INF){cout<<0<<'\n';return 0;}answer=max(answer,d-m);}
cout<<answer<<'\n';''',
    '包装可以重复；不可达余数意味着无上界而非忽略它；全部正整数可组成时输出零；零组合用于初始化。',
    r'以 m 为最小容量，时间 $O(nm\log(nm+1))$，距离数组空间 $O(m)$，含堆的总空间上界 $O(nm)$。',tags=['最短路','取模与同余'],lessons=G+['modular'])

add('P5195','先避开骑士找灌木，再从灌木走回骑士',
    '四邻格子移动每步一天。必须先拿到任意一处灌木再到骑士格，拿到前不能经过骑士。求最短总天数，地图保证任务可完成。',
    r'''从起点 BFS，禁止进入障碍及骑士格，得到到每片灌木的最短距离 d1。再从骑士 BFS，只禁止障碍，得到灌木到骑士的距离 d2。枚举所有灌木格，取两边均可达的 d1+d2 最小值。''',
    r'''一条合法路线总会先在某处取得灌木，再最终到骑士处。将路线在第一次取得灌木的位置分成两段：前段不能经过骑士，后段已经有灌木，可以按普通可走格移动。

第一遍 BFS 从 Bessie 的起点出发，只通过非障碍、非骑士格，正确求出第一段的最短步数。第二遍从骑士出发，通过全部非障碍格。因为格子邻接双向，它到某灌木的距离等于拿到该灌木后走回骑士的最短距离。

对每个灌木格 c，将两个距离相加。一方面，任意合法路线在首次取灌木处分段后，其两段长度都不小于对应 BFS 距离，不能优于所取最小值。另一方面，第一遍的路径不会提前经过骑士，把它接上第二遍反向路径就能完成任务，所以该最小值可实现。

第一段可能途中经过其它灌木，这并不会使路线非法；拿到更早的灌木后继续走也是允许的。最优解的首次灌木仍在枚举范围内，故不会因此漏解。

输入 W 是列数、H 是行数。用 char 连续读取 W·H 个数字，可以同时处理数字间有空格和多行折行的形式；cin 对 char 会跳过空白。将格子压成 row·W+column 存队列和距离，邻居仍须检查行列边界，不能使一行末尾绕到下一行开头。''',
    r'''int W,H;cin>>W>>H;int cells=W*H,start=-1,knight=-1;vector<char>land(cells);
for(int i=0;i<cells;++i){cin>>land[i];if(land[i]=='2')start=i;if(land[i]=='3')knight=i;}
auto bfs=[&](int source,bool blockKnight){vector<int>dist(cells,-1);queue<int>q;dist[source]=0;q.push(source);
    const int dr[4]={-1,1,0,0},dc[4]={0,0,-1,1};
    while(!q.empty()){int u=q.front();q.pop();int r=u/W,c=u%W;
        for(int k=0;k<4;++k){int nr=r+dr[k],nc=c+dc[k];if(nr<0||nr>=H||nc<0||nc>=W)continue;int v=nr*W+nc;
            if(land[v]=='1'||(blockKnight&&land[v]=='3')||dist[v]!=-1)continue;
            dist[v]=dist[u]+1;q.push(v);
        }
    }return dist;
};
// 找到灌木之前，骑士格不可通过。
auto first=bfs(start,true),second=bfs(knight,false);int answer=INT_MAX;
for(int i=0;i<cells;++i)if(land[i]=='4'&&first[i]!=-1&&second[i]!=-1)answer=min(answer,first[i]+second[i]);
cout<<(answer==INT_MAX?-1:answer)<<'\n';''',
    'W 列、H 行；第一遍骑士格不能通过；枚举全部灌木而非离起点最近的一片；两个距离都可达才相加。',
    r'时间与空间均为 $O(WH)$。',tags=['BFS'],lessons=A+['graphs','queue-stack','lambda-local'])

add('P7100','用集合中转点替代两两相连的团',
    '每个集合包含带权成员 (t,w)，同一集合任意两名成员之间形成费用为两权之和的无向边。求一号到全部原顶点的最短路；不可达输出题目指定的长整数。',
    r'''为每个集合新增一个中转点，成员 (t,w) 与它连接一条权为 w 的无向边。经中转点从 u 到 v 的费用恰为 w_u+w_v，用线性条边代替集合内平方条边。新图权非负，Dijkstra 后仅输出原顶点的距离。''',
    r'''集合有一万个成员时，两两建边约需五千万条，而输入只给了一万份成员信息。边权能够拆成出发成员费用加到达成员费用，正好可以通过同一个中转点拆开支付。

给集合 i 建虚拟结点 n+i。每个成员 (t,w) 与它连接权 w 的双向边。从原顶点 u 走到中转点支付 w_u，再走到 v 支付 w_v，总费用与原团边相同。不同集合的中转点不能合并，因为同一原顶点在不同集合里可以有不同权值。

任意原图路径中的一条团边都能替换成两步，中间费用保持不变。反向看，新图从原顶点到原顶点的路径交替经过成员和中转点，每个两步段都能还原成同一集合内的边。返回原成员的无用往返可以删除；全部权非负，即使存在零权环，也能去环得到费用不增加的简单路径。因此原顶点间最短距离完全相同。

用 n+k 个顶点、两倍成员总数条邻接记录做堆优化 Dijkstra。零权成员合法，不能用“距离非零”表示访问状态。对过时堆条目直接跳过。

不可达值必须按原题输出 4557430888798830399，不能自行换成 -1。将 INF 设成这个值，只有已取出的可达状态才参与加法；最大简单路径费用远小于这个哨兵，使用 long long 即可。输出只遍历一到 n，不把中转点也列入答案。''',
    r'''int n,k;cin>>n>>k;vector<vector<pair<int,long long>>>g(n+k+1);
// 集合 i 的中转点为 n+i，一份成员信息仅建两条邻接记录。
for(int i=1;i<=k;++i){int size;cin>>size;while(size--){int u;long long w;cin>>u>>w;g[u].push_back({n+i,w});g[n+i].push_back({u,w});}}
const long long INF=4557430888798830399LL;vector<long long>dist(n+k+1,INF);
using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;dist[1]=0;pq.push({0,1});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}for(int u=1;u<=n;++u)cout<<dist[u]<<(u==n?'\n':' ');''',
    '一个集合一个中转点；成员权值按其所属集合读取；允许零权；只输出原点；不可达使用题目指定的整数。',
    r'设 M 为成员总数，时间 $O(n+k+M\log(M+1))$，空间 $O(n+k+M)$。',tags=['最短路','图论'],lessons=G)

add('P10726','挡板端点决定下一次下落，落到目标立即结束',
    '从 s 号水平挡板左端出发，在板上行走和竖直下落都按距离计时。只能从左右端点离开，并落到下方遇到的第一块挡板；求首次到 t 号挡板的最短时间。',
    r'''每块挡板建左右端点两个状态，板内两端互连，费用为板长。对每个端点找竖直方向首先接住它的其它挡板 j：连到 j 的两端，费用为落差加落点到相应端点的水平距离；若 j 为目标，另连终点，费用只取落差。非负图 Dijkstra 即可。''',
    r'''落到挡板内部后，如果还要继续下落，下一次只能选择左端或右端。到指定端点最短的做法就是沿板直接走过去，中途折返不会变得更短。于是非目标挡板的内部落点可以省略，把下落与走到端点合成一条边。

对挡板 i 的端点 x，在所有覆盖 x、且高度不高于当前端点的其它挡板中找最高者。它正是会先接住人的挡板，不能跳过它直接选择更低但更有利的一块。覆盖范围包含端点，接触同高端点时落差为零；这一边界与官方原卷参考建图一致。无其它板覆盖时，这次下落无法再回到挡板系统，不建边。

若首先落到 j，落差为 h_i-h_j。从落点 x 到它左、右两端分别再花 x-l_j 和 r_j-x。因此两条合并边的费用为落差加对应水平距离。图中还保留每块板两端互走的边，允许先横穿当前板再决定从另一端离开。

目标只要求到达 t 号挡板，不要求走到它的端点。为此建立独立终点：落到 t 的每次下落额外连一条只花落差的边；t 的两个端点也以零费用连终点。若 s=t，起点已经在目标上，答案自然为零。省略这一终点会把落在目标内部之后不需要的步行误计进去。

任意实际路线都能删去板上的往返，变成这些端点边；反过来，每条边也能实际走出，所以最短时间相同。所有费用非负，零费用接触也适用 Dijkstra。找首块挡板使用平方枚举，n≤1000 足够。官方[原卷与边界依据](https://gesp.ccf.org.cn/101/attach/1621071654551584.pdf)保存在核对材料中。''',
    r'''int n,s,t;cin>>n>>s>>t;--s;--t;vector<int>l(n),r(n),h(n);for(int i=0;i<n;++i)cin>>l[i]>>r[i]>>h[i];
int finish=2*n;vector<vector<pair<int,int>>>g(finish+1);
for(int i=0;i<n;++i){g[2*i].push_back({2*i+1,r[i]-l[i]});g[2*i+1].push_back({2*i,r[i]-l[i]});}
// 目标挡板的任意落点都可以结束，无需再走到端点。
g[2*t].push_back({finish,0});g[2*t+1].push_back({finish,0});
for(int i=0;i<n;++i)for(int side=0;side<2;++side){int x=side?r[i]:l[i],level=-1;
    for(int j=0;j<n;++j)if(j!=i&&l[j]<=x&&x<=r[j]&&h[j]<=h[i])level=max(level,h[j]);
    if(level==-1)continue;
    for(int j=0;j<n;++j)if(j!=i&&h[j]==level&&l[j]<=x&&x<=r[j]){
        int fall=h[i]-h[j];g[2*i+side].push_back({2*j,fall+x-l[j]});g[2*i+side].push_back({2*j+1,fall+r[j]-x});
        if(j==t)g[2*i+side].push_back({finish,fall});
    }
}
const long long INF=(1LL<<60);vector<long long>dist(finish+1,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[2*s]=0;pq.push({0,2*s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}cout<<(dist[finish]==INF?-1:dist[finish])<<'\n';''',
    '只落到首先接住的板；端点接触按覆盖处理；目标内部首次落地即可结束；同高接触费用为零；不能向更高处跳。',
    r'查找挡板时间 $O(n^2)$；设实际边数为 E，最短路时间 $O(n+E\log(E+1))$，总空间 $O(n+E)$。任意退化接触均按代码保留时 E 至多为平方级。',tags=['最短路'],lessons=G)

add('UVA658','整个缺陷集合才是最短路状态',
    '程序初始具有全部 n 个缺陷。每个补丁有使用前提、耗时和对缺陷的增删作用，可重复使用。求消除全部缺陷的最短时间；无方案按原格式输出。',
    r'''用 n 位二进制数表示当前存在的缺陷。补丁的必有集合 need、必无集合 absent 决定它是否可用；可用时删去 remove，加入 added，得到新状态。以补丁耗时为边权，在最多 2^n 个状态上从全一做 Dijkstra，到全零即完成。''',
    r'''只记录“还剩几个缺陷”不够：同样剩两个缺陷，具体是哪两个会影响哪些补丁可以使用。n≤20，记录每一位是否存在，一共有至多 2^n 个状态，可以完整表示未来操作所需信息。

把补丁的第一串字符分成两个掩码：加号对应必有 need，减号对应必无 absent，零表示不限制。当前状态 mask 可以使用它，当且仅当

$$ (mask\mathbin{\&}need)=need,\qquad(mask\mathbin{\&}absent)=0.$$

第二串独立描述效果：减号位置要清零，加号位置要置一，零位置保持原值。于是 next=(mask & ~remove)|added。由于 mask 只有低 n 位，清位时的按位取反不会凭空增加高位。

补丁可能产生新的缺陷，不能按缺陷数量从少到多递推，也不能贪心选一次消除最多的补丁。状态图可能有环，用非负耗时的最短路求最优；邻边在取出状态时枚举所有补丁，不显式建立指数规模边表。

初始状态为 (1<<n)-1，目标为零。重复使用补丁自然对应再次经过它的转移，不应给补丁加“使用过”标记。过时的堆条目跳过，到零状态被正式取出后可以停止。

多组产品读到 n=m=0 结束。严格保留 Product 编号、成功／失败文本以及组间空行。代码中的时间和距离使用 long long，位移使用无符号整数。[原站 PDF](https://onlinejudge.org/external/6/658.pdf)明确补丁允许重复使用。''',
    r'''int n,m,product=0;while(cin>>n>>m&&(n||m)){
    struct Patch{long long cost;unsigned need,absent,remove,added;};vector<Patch>patches;
    for(int i=0;i<m;++i){long long cost;string before,after;cin>>cost>>before>>after;Patch p{cost,0,0,0,0};
        for(int j=0;j<n;++j){unsigned bit=1u<<j;if(before[j]=='+')p.need|=bit;if(before[j]=='-')p.absent|=bit;
            if(after[j]=='-')p.remove|=bit;if(after[j]=='+')p.added|=bit;
        }patches.push_back(p);
    }
    unsigned count=1u<<n,initial=count-1;const long long INF=(1LL<<62);vector<long long>dist(count,INF);
    using State=pair<long long,unsigned>;priority_queue<State,vector<State>,greater<State>>pq;dist[initial]=0;pq.push({0,initial});
    while(!pq.empty()){auto [du,mask]=pq.top();pq.pop();if(du!=dist[mask])continue;if(mask==0)break;
        for(const auto &p:patches)if((mask&p.need)==p.need&&(mask&p.absent)==0){// 先清除，再加入；其它低位保持原样。
            unsigned next=(mask&~p.remove)|p.added;
            if(du+p.cost<dist[next]){dist[next]=du+p.cost;pq.push({dist[next],next});}
        }
    }
    cout<<"Product "<<++product<<'\n';if(dist[0]==INF)cout<<"Bugs cannot be fixed.\n\n";
    else cout<<"Fastest sequence takes "<<dist[0]<<" seconds.\n\n";
}''',
    '前提和效果是两串不同信息；零表示保持或不限制，不能当成清除；缺陷可以重新出现；补丁可以重复使用；输出空行与标点保持原格式。',
    r'设 V=2^n，隐式枚举至多 mV 条转移；二叉堆时间上界 $O(mV\log(mV+1))$，距离空间 $O(V)$，含候选堆的总上界 $O(mV)$。',tags=['最短路','位运算'],lessons=G+['bitwise'])

add('CF938D','所有票价同时入堆，让便宜演出向外传播',
    '每座城市有一场演出及票价。道路双向且有费用，对每座出发城市求到任意城市听演出并返回的最小总费用，也可以留在本城。',
    r'''把每条道路费用乘二。初始 dist[i]=a[i]，所有城市同时入小根堆，做多源 Dijkstra。沿边传播相当于到更远的演出支付往返路费，最终 dist[i]=min_j(a[j]+2·d(i,j))。''',
    r'''选择城市 j 听演出时，从 i 去 j 再返回的最小交通费用为 2·d(i,j)：两段都至少为最短距离，走同一条最短路往返即可达到。因此只需最小化票价加双倍最短距离。

若每座城市分别跑一次最短路，最多二十万次无法承受。改建一个虚拟起点，向每个城市 j 连费用为 a[j] 的边，原道路费用翻倍。虚拟起点到 i 的一条路先支付某场演出的票价，再沿双倍费用道路传播，总费用正好是一个候选答案。无向性使 d(j,i)=d(i,j)，即得到全部城市的答案。

实现不必真的建立虚拟点。直接令每个 dist[j]=a[j]，把全部初值加入堆，等价于虚拟起点已经完成第一次松弛。后续 Dijkstra 按最便宜的总费用继续传播，而不是只从最低票价城市出发；遥远的廉价演出未必胜过近处稍贵的演出。

例如城市间路费四，本地票价二十，邻城票价六。到邻城往返加票只要十四，可以改善本地答案。没有道路通向别处的城市仍保留自己的票价，不能被当作无解。

单边与票价均可到 10^12，边权翻倍及候选和都用 long long。所有城市初始有限，不需要额外不可达值；从堆取出旧条目时仍要检查 du==dist[u]。''',
    r'''int n,m;cin>>n>>m;vector<vector<pair<int,long long>>>g(n+1);
for(int i=0;i<m;++i){int u,v;long long w;cin>>u>>v>>w;g[u].push_back({v,2*w});g[v].push_back({u,2*w});}
vector<long long>dist(n+1);using State=pair<long long,int>;priority_queue<State,vector<State>,greater<State>>pq;
// 所有城市同时作为带有各自初始票价的源。
for(int i=1;i<=n;++i){cin>>dist[i];pq.push({dist[i],i});}
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}for(int i=1;i<=n;++i)cout<<dist[i]<<(i==n?'\n':' ');''',
    '往返路费乘二；所有城市以各自票价入堆；不只选全局最低票价；无路的城市可在本城听演出；使用 long long。',
    r'时间 $O((n+m)\log(n+m+1))$，空间 $O(n+m)$。',tags=['最短路','图论'],lessons=G)

add('CF912D','先算每格被覆盖次数，再取最大的 k 个乘积',
    'n×m 池塘中放 k 条鱼，每格最多一条。r×r 网的位置在所有合法放法中等概率选择，要求最大化一次捕获数量的期望。',
    r'''一行位置 x 被合法行区间覆盖的次数为 min(x,r,n-x+1,n-r+1)，列同理。格子的覆盖次数是行次数乘列次数，期望是所选 k 格覆盖次数和除以网的总放法数。两组次数分别降序，按每行乘积列表用大根堆合并，取前 k 大即可。''',
    r'''先固定一条鱼所在的格子。它是否被抓到，只取决于网的位置是否覆盖这个格子。把每条鱼的被捕概率相加，就是总捕获数量的期望，鱼之间不需要互相独立。

对一维长 n、区间长 r 的情形，覆盖位置 x 的区间左端点 p 必须同时满足 1≤p≤n-r+1 和 x-r+1≤p≤x。相交整数区间的长度给出覆盖次数，化简为

$$c_n(x)=\min(x,r,n-x+1,n-r+1).$$

网的横向、纵向位置可以独立选择，因此格子 (x,y) 被覆盖 c_n(x)·c_m(y) 次。所有合法网位置共 (n-r+1)(m-r+1) 个，分母固定，所以只需挑覆盖次数最大的 k 个不同格子。

不能枚举至多 10^10 个格子。把行次数 a、列次数 b 分别降序。固定行 i 后，a[i]·b[0],a[i]·b[1],… 是一个从大到小的列表。先把每行的首项入大根堆，每次取出最大项，累加后推进这一行的列下标，再放入它的下一项。这是多个有序列表的合并，每个格子最多入堆一次，不用额外维护二维访问集合。

排序只改变格子的枚举次序，不合并相同覆盖次数的格子；相同乘积仍要按其出现次数保留，因为每个格子都可以放一条鱼。n、m、k 各最多十万，直接为全部 n 行建立堆也可承受。

乘积和可到约 10^15，用 long long 累加；分母乘法也先转 long long，最后才转 long double 相除，输出十八位小数。不要把行列次数相加，也不要把相同概率去重。''',
    r'''int n,m,r,k;cin>>n>>m>>r>>k;vector<int>a(n),b(m);
for(int i=1;i<=n;++i)a[i-1]=min({i,r,n-i+1,n-r+1});
for(int j=1;j<=m;++j)b[j-1]=min({j,r,m-j+1,m-r+1});
sort(a.rbegin(),a.rend());sort(b.rbegin(),b.rend());
using State=tuple<long long,int,int>;priority_queue<State>pq;
for(int i=0;i<n;++i)pq.push({1LL*a[i]*b[0],i,0});
// 每次只推进刚弹出的那一行乘积列表。
long long sum=0;for(int take=0;take<k;++take){auto [value,i,j]=pq.top();pq.pop();sum+=value;
    if(j+1<m)pq.push({1LL*a[i]*b[j+1],i,j+1});
}long long positions=1LL*(n-r+1)*(m-r+1);cout<<fixed<<setprecision(18)<<(long double)sum/positions<<'\n';''',
    '每格一次，重复覆盖次数不能去重；先最大化分子；所有整数乘法使用 long long；网必须完全在池内；最后才作浮点除法。',
    r'时间 $O(n\log n+m\log m+(n+k)\log(n+1))$，空间 $O(n+m)$。',tags=['堆','期望与概率'],lessons=A+['heap','probability'],checker='path_decimal')

add('P2371','余数最小可达值确定整条等差数列',
    '给定非负系数 a_i，求区间 [l,r] 内有多少整数能表示为这些系数的非负整数倍之和。每个系数可使用任意次数。',
    r'''删去零系数，取最小正系数 m。余数图上加一次 a 就从 u 到 (u+a)%m、费用 a，求 dist[t] 为每类的最小可表示值。该类全部可表示数恰为 dist[t]+km。用前缀计数 F(r)-F(l-1)；若系数全零，因 l≥1，答案为零。''',
    r'''系数为零不会产生新的总数，先删掉。剩下的最小正系数 m 可以任意使用，所以一个数可表示后，加任意个 m 仍可表示。这让同一余数类中的可行数成为从某个最小值开始的等差数列。

令 dist[t] 是能表示且模 m 余 t 的最小数。使用一次系数 a，相当于总量增加 a、余数变成 (t+a)%m。零组合从余数零、总量零出发；包装选择与图路径逐步一一对应，故非负边权最短路给出各 dist。

对有限的 dist[t]，全部可表示数恰好是 dist[t],dist[t]+m,…：这些数可通过加 m 构造；任何同余且不小于最小值的整数，差值本来就是非负 m 的倍数，也在这串数中。不小于最小值之前的同余数则由最小性的定义排除。

因此不超过 X 的这一类贡献为零（X<dist[t]）或者

$$\left\lfloor\frac{X-dist[t]}m\right\rfloor+1.$$

把所有余数类贡献相加得到 F(X)，不同类互不重叠。区间答案为 F(r)-F(l-1)，自然将零组合从正数区间中扣除。不可达类贡献零，不把 INF 放进减法。

所有 a_i 都是零时，只有零能表示，而 l≥1，所以直接输出零，不能对零取模。m 最大五十万，n 最大十二，显式建出所有边没有必要，取出状态时枚举系数即可。总量上界和区间端点可到 10^12，dist、计数与候选和均使用 long long。''',
    r'''int n;long long l,r;cin>>n>>l>>r;vector<int>a;for(int i=0;i<n;++i){int v;cin>>v;if(v)a.push_back(v);}
// 零系数全被删掉时，只有零可表示。
if(a.empty()){cout<<0<<'\n';return 0;}int m=*min_element(a.begin(),a.end());
const long long INF=(1LL<<62);vector<long long>dist(m,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[0]=0;pq.push({0,0});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(int value:a){int v=(u+value)%m;if(du+value<dist[v]){dist[v]=du+value;pq.push({dist[v],v});}}
}auto count=[&](long long X){long long answer=0;for(long long d:dist)if(d!=INF&&d<=X)answer+=(X-d)/m+1;return answer;};
cout<<count(r)-count(l-1)<<'\n';''',
    '零系数先删；全部为零单独处理；使用最小正系数作模数；不可达类不计；区间前缀差要用 l-1；每类需加一计入最小值本身。',
    r'以 m 为最小正系数，时间 $O(nm\log(nm+1))$，距离空间 $O(m)$，含候选堆总空间上界 $O(nm)$。',tags=['最短路','取模与同余'],lessons=G+['modular','lambda-local'])

add('P3831','同一个站拆成横向、纵向两种乘车状态',
    'n 横 n 纵的地铁网每站间运行两分钟，只有给定换乘站可花一分钟切换方向。起终点可以在任意站，求不中途出站的最短时间。',
    r'''只保留换乘站、起点和终点，每个点拆成横向乘车、纵向乘车两层；换乘站两层互连费用一。同一横线按列坐标排序后，只连相邻保留点的横向状态，费用为两倍列差；纵线同理。起点两层都为零，终点取两层最小值。''',
    r'''仅记录所在站不足以判断下一步能往哪走。经过一个普通交叉站，并不意味着能从横向车换到纵向车，所以必须把乘车方向放进状态。

每个需要保留的站拆成 H、V 两个结点，分别代表处于横向列车与纵向列车上。只有原题允许换乘的站，才加 H↔V、费用一的边。起点上车尚未选方向，给它两层都设零；终点可以从任意方向下车，答案取两层较小值，不强加一次换乘。

网格全部 n² 个站没有必要建图。两个相邻换乘机会之间，没有任何影响路线选择的事件，直接把中间普通站合并成一次连续乘车。将所有换乘站及起终点放在一起，同一横线上按纵坐标排序，只连接相邻保留点的 H 层，费用为坐标差乘二；纵线类似。

为什么只连相邻点够用？同一条线上，从一个保留点到更远点，可以经过若干相邻边，距离差会逐段相加为两端的总距离；没有额外换乘费，也不强迫在中间点换车。反过来，这些边都对应真实列车行程，因此既不会多算也不会凭空创造捷径。

同坐标的起终点或换乘站输入可以保留为多个记录，相同层之间的相邻距离为零；横纵换乘仍只通过指定的一分钟边，不会因为重复坐标免费换乘。代码把普通起终点的两层保持分离，仅通过初值和答案选择方向。

图规模与 m 成正比。n 只用于坐标范围，不申请 n² 数组。建图后做非负边权 Dijkstra，不可达输出 -1；起终点同站时自然得到零。''',
    r'''int n,m;cin>>n>>m;struct Point{int x,y;};int K=m+2;vector<Point>p(K);
for(int i=0;i<m;++i)cin>>p[i].x>>p[i].y;cin>>p[m].x>>p[m].y>>p[m+1].x>>p[m+1].y;
vector<vector<pair<int,int>>>g(2*K);auto edge=[&](int u,int v,int w){g[u].push_back({v,w});g[v].push_back({u,w});};
// 两层之间只有指定换乘站的一分钟边。
for(int i=0;i<m;++i)edge(2*i,2*i+1,1);
vector<int>order(K);iota(order.begin(),order.end(),0);
sort(order.begin(),order.end(),[&](int a,int b){return tie(p[a].x,p[a].y)<tie(p[b].x,p[b].y);});
for(int i=1;i<K;++i){int u=order[i-1],v=order[i];if(p[u].x==p[v].x)edge(2*u,2*v,2*(p[v].y-p[u].y));}
sort(order.begin(),order.end(),[&](int a,int b){return tie(p[a].y,p[a].x)<tie(p[b].y,p[b].x);});
for(int i=1;i<K;++i){int u=order[i-1],v=order[i];if(p[u].y==p[v].y)edge(2*u+1,2*v+1,2*(p[v].x-p[u].x));}
const long long INF=(1LL<<60);vector<long long>dist(2*K,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[2*m]=dist[2*m+1]=0;pq.push({0,2*m});pq.push({0,2*m+1});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,w]:g[u])if(du+w<dist[v]){dist[v]=du+w;pq.push({dist[v],v});}
}long long answer=min(dist[2*(m+1)],dist[2*(m+1)+1]);cout<<(answer==INF?-1:answer)<<'\n';''',
    '普通交叉点不能免费转弯；同线相邻保留点之间只付运行时间；换乘费一而非两次；起终点允许任选方向；不建整个网格。',
    r'时间 $O((m+1)\log(m+2))$，空间 $O(m+1)$。',tags=['最短路','图论'],lessons=G+['sort','lambda-local'])

add('P6096','先分乘车次数层，再在线路上取最长乘坐段',
    '每次上车付一元，同线换方向也重新付费。在最低总票价下尽量多坐地铁；同一站名可在线路中出现多次，路线不可达输出 -1 和零。',
    r'''先在“站—线路”关联图上 BFS：一条线路首次遇到时，整条线的站都能用一次新上车到达，求最少票价 d，并记录线路的首次发现顺序。再按该顺序处理线路。票价层 c 的线，只从 d=c-1 的站上车、更新 d=c 的站；时间转移为 best[u]+|位置差|，分别维护 best[u]-位置和 best[u]+位置的最大值，两次扫描即处理整条线。''',
    r'''票价优先于时间，不能把“走得更久”直接写成普通最短路的负边权再套 Dijkstra。先把最低票价独立求出，之后只在保持这份票价的路线中最大化时间。

从任意一站上车后，同一条直线型线路的任意站都可以选一个方向直接到达，只花一次票价。于是求票价时，可将一条线路看作一个中转点。BFS 初始 d[A]=0；第一次由 d[u] 层遇到尚未扫描的线路，把这条线的层数记为 c=d[u]+1，并将所有尚未到达的站赋值 c、入队。每条线路只展开一次，重复站名的出现仍保留在位置数组中。

BFS 的站按 d 递增出队，线路的首次发现顺序也按 c 递增。接着令 best[v] 表示用恰好 d[v] 次上车到 v 的最长时间，best[A]=0。任何全局最低票价路线在每次下车时，都必定已经用最少票价到该站；否则替换其前缀，就能减少最终票价，与最优性矛盾。

因此处理层 c 的线路时，只能从 d[u]=c-1 的站上车，并只更新 d[v]=c 的站。若在更少票价就能到达的站下车，这个多花钱的前缀不会出现在最低总票价方案中；列车经过这类站而不停留换乘却完全允许，位置差仍包含它们。

假设上车站在当前线的位置 i，下车站在 j，实际乘车时间是 |j-i|。同一站在线路里出现多次时，每个出现位置都可能上车或下车，不能先去重。最长时间转移为 best[u]+|j-i|，拆成

$$\max\bigl((best[u]-i)+j,\ (best[u]+i)-j\bigr).$$

先扫描整条线所有 d=c-1 的出现位置，求两个括号内的最大值，再扫描所有 d=c 的位置更新 best。两个方向分别对应上述两项，无需枚举站点对，也没有在中途免费掉头。每次乘坐的起终位置可以选择，最终下车站相同也按真实位置差计时。

逐层处理时，上一层 best 已经完整；同层线路只更新下一层站，不会互相依赖。归纳得到全部最低票价下的最长时间。每条线路在 BFS 扫一次、时间 DP 扫两次，适应成员总数八十万的范围。站名映射使用 unordered_map，先登记给定站表；相同站名对应同一站点，但在线路中的各个位置仍分别保留。''',
    r'''int N,S;cin>>N>>S;unordered_map<string,int>id;id.reserve(2*S+1);
for(int i=0;i<S;++i){string name;cin>>name;id.emplace(name,i);}
vector<vector<int>>line(N),contains(S);
for(int i=0;i<N;++i){int length;cin>>length;line[i].reserve(length);
    for(int j=0;j<length;++j){string name;cin>>name;int v=id.at(name);line[i].push_back(v);contains[v].push_back(i);}
}
string from,to;cin>>from>>to;int A=id.at(from),B=id.at(to);vector<int>d(S,-1),level(N,-1),order;queue<int>q;d[A]=0;q.push(A);
while(!q.empty()){int u=q.front();q.pop();for(int route:contains[u])if(level[route]==-1){
    level[route]=d[u]+1;order.push_back(route);
    for(int v:line[route])if(d[v]==-1){d[v]=level[route];q.push(v);}
}}
if(d[B]==-1){cout<<"-1\n0\n";return 0;}
const long long NEG=-(1LL<<60);vector<long long>best(S,NEG);best[A]=0;
// BFS 发现顺序按票价层递增；上一层时间此时已经完整。
for(int route:order){int c=level[route];long long minus=NEG,plus=NEG;
    for(int i=0;i<(int)line[route].size();++i){int u=line[route][i];if(d[u]==c-1&&best[u]!=NEG){minus=max(minus,best[u]-i);plus=max(plus,best[u]+i);}}
    if(minus==NEG)continue;
    for(int j=0;j<(int)line[route].size();++j){int v=line[route][j];if(d[v]==c)best[v]=max({best[v],minus+j,plus-j});}
}
cout<<d[B]<<'\n'<<best[B]<<'\n';''',
    '先最小票价再最大时间；重复站名要保留出现位置；一条线只在 BFS 首次遇到时展开；同线掉头要再次付费，不能在一次乘车中来回刷时间；不可达第二行仍输出零。',
    r'设 L 为所有线路长度之和，站名字长至多四十。站名哈希按通常期望复杂度计，时间与空间均为 $O(N+S+L)$。',tags=['BFS','线性 DP'],lessons=A+['graphs','queue-stack','maps','dp'])

add('UVA11997','每次只合并并保留最小的 k 个部分和',
    '有 k 个数组，每个含 k 个正整数。从每个数组各选一个数，输出全部 k^k 种选择中最小的 k 个和，重复的和按方案次数保留。多组输入读至文件结束。',
    r'''先排序首行作为当前 k 个最小部分和。读入并排序下一行 b，将每个当前值 a[i] 与 b 的和视为一条升序列表。用小根堆多路合并，只弹出最小 k 项作为新的部分和，重复至最后一行。''',
    r'''不能把每行最小的数各取一次后，再简单拼出其它答案，因为多次改变同一行和改变不同的行可能以不同顺序产生更小的和。需要在每次加入一行时完整比较候选。

设 a 已包含前几行选择的最小 k 个部分和，下一行排序为 b。固定 a[i]，有序列表为 a[i]+b[0],a[i]+b[1],…；各列表都升序。小根堆先放每条列表首项，弹出当前最小值后，只向同一列表推进一个位置，即可按顺序合并所有 k² 个候选的前 k 项。

为什么前面只留 k 个部分和足够？任何被舍弃的部分和 x，前面已有至少 k 个不大于 x 的部分和。对它未来选择的同一组后续数，这 k 个更小部分和都能加上同样的后续总量，得到至少 k 个不大于它的完整方案。因此 x 不会是取得前 k 项所必需的；有相等值时，保留其中 k 个方案已经足够产生正确的重复数值。

初始一行只有 k 个选择，全都保留。逐行使用上面的截断与合并，归纳得到最后的 k 个最小完整和。相同数值不是同一方案，不能用 set 去重，例如两行 [1,1]、[1,2] 的前两个和都是二。

堆条目保存 sum、旧部分和下标 i、新行下标 j，弹出后推进到 j+1。每轮只处理 k 个出堆项，空间只保存两行和堆，不存整个 k×k 矩阵。多组输入没有结束零，使用 while(cin>>k)，每组重建状态。[原站 PDF](https://onlinejudge.org/external/119/11997.pdf)。''',
    r'''int k;while(cin>>k){vector<long long>a(k);for(auto &v:a)cin>>v;sort(a.begin(),a.end());
    for(int row=1;row<k;++row){vector<long long>b(k),next;for(auto &v:b)cin>>v;sort(b.begin(),b.end());next.reserve(k);
        using State=tuple<long long,int,int>;priority_queue<State,vector<State>,greater<State>>pq;
        for(int i=0;i<k;++i)pq.push({a[i]+b[0],i,0});
        // 相同数值保留出现次数，只取出当前最小的 k 个方案。
        for(int take=0;take<k;++take){auto [sum,i,j]=pq.top();pq.pop();next.push_back(sum);if(j+1<k)pq.push({a[i]+b[j+1],i,j+1});}
        a.swap(next);
    }
    for(int i=0;i<k;++i)cout<<a[i]<<(i+1==k?'\n':' ');
}''',
    '每行恰选一个；重复和按次数保留；每次推进刚弹出的那条列表；只截断部分和数量，不删相等数值；输入读至 EOF。',
    r'k 轮排序与堆合并，时间 $O(k^2\log k)$，额外空间 $O(k)$。',tags=['堆'],lessons=A+['heap','sort'])
