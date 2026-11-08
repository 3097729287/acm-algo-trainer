"""Remaining curated arithmetic, graph states and value-heavy knapsacks."""
from nowcoder_editorials import CONTENT, add, add_python, read, reviewed_clone
from nowcoder_range_more import BIT
from nowcoder_graph_support import DIJKSTRA
from nowcoder_number_basics import EXGCD
from nowcoder_combinatorics_primes import SIEVE
from nowcoder_euler_support import EULER,LCA


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(235903,2100,['Dijkstra','状态压缩'],'按顺序拿钥匙，蛇首次经过多耗一分钟，最短救师时间。',
        '状态(position,keys,mask)中keys是已集齐的连续钥匙种数，mask是已击败蛇的集合（最多5只）。走到数字keys+1时keys加1；提前路过更大数字不会取得钥匙。经过尚未击败的蛇，费用2并设置其位，之后再经过费用1。所有边权1或2，用Dijkstra。取到全部钥匙并到达T的状态首次出堆时即最优。',
        r'''int n,m; cin >> n >> m; vector<string> grid(n); for (auto &s:grid) cin >> s; int cells=n*n,start=0,target=0,snakes=0; vector<int> snake(cells,-1); for (int u=0;u<cells;u++) { char c=grid[u/n][u%n]; if (c=='K') start=u; if (c=='T') target=u; if (c=='S') snake[u]=snakes++; } int masks=1<<snakes; auto encode=[&](int u,int keys,int mask) { return (keys*masks+mask)*cells+u; }; const int inf=1000000000; vector<int> distance((m+1)*masks*cells,inf); priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> heap; int initial=encode(start,0,0); distance[initial]=0; heap.push({0,initial}); const int dr[]={-1,1,0,0},dc[]={0,0,-1,1}; while (!heap.empty()) { auto [d,state]=heap.top(); heap.pop(); if (d!=distance[state]) continue; int u=state%cells,temporary=state/cells,mask=temporary%masks,keys=temporary/masks; if (u==target && keys==m) { cout << d; return 0; } for (int direction=0;direction<4;direction++) { int r=u/n+dr[direction],c=u%n+dc[direction]; if (r<0 || r>=n || c<0 || c>=n || grid[r][c]=='#') continue; int v=r*n+c,nextKeys=keys,nextMask=mask,cost=1; if (grid[r][c]>='1' && grid[r][c]<='9' && grid[r][c]-'0'==keys+1) nextKeys++; if (snake[v]>=0 && !(mask>>snake[v]&1)) { nextMask|=1<<snake[v]; cost++; } int next=encode(v,nextKeys,nextMask); if (d+cost<distance[next]) { distance[next]=d+cost; heap.push({d+cost,next}); } } } cout << "impossible";''',
        '同一坐标但钥匙进度或蛇状态不同，不能合并。T也可以提前经过，只在keys=m时完成。',
        complexity=r'状态数V=n²(m+1)2^S，时间 $O(V\log V)$，空间 $O(V)$。')
    put(231128,2200,['差值背包','有限次数状态'],'选择卡牌分两组点数相等，可将至多k张点数翻倍，最大总价值。',
        '用差值D=两组点数差，维度j表示已经翻倍的张数。每张卡有五种有效去向：不选、正常放左/右、翻倍后放左/右；只要选中，不论哪组都加同一个v。用旧表转移到新表，防止重复使用。点数每张至13，全部翻倍后绝对差至2600，数组范围固定；最后在D=0、j≤k中取最大，空集给0。',
        r'''int n,k; cin >> n >> k; vector<pair<long long,int>> card(n); int total=0; for (auto &[v,t]:card) { cin >> v >> t; total+=2*t; } int width=2*total+1; const long long negative=LLONG_MIN/4; vector<long long> dp((k+1)*width,negative); dp[total]=0; int processed=0; for (auto [value,point]:card) { auto next=dp; for (int doubled=0;doubled<=min(k,processed);doubled++) for (int d=-total;d<=total;d++) { long long old=dp[doubled*width+d+total]; if (old==negative) continue; for (int sign:{-1,1}) { int normal=d+sign*point; if (abs(normal)<=total) next[doubled*width+normal+total]=max(next[doubled*width+normal+total],old+value); int large=d+sign*2*point; if (doubled<k && abs(large)<=total) next[(doubled+1)*width+large+total]=max(next[(doubled+1)*width+large+total],old+value); } } dp.swap(next); processed++; } long long answer=0; for (int j=0;j<=k;j++) answer=max(answer,dp[j*width+total]); cout << answer;''',
        '负价值卡可能帮助点数平衡，不能直接删掉。翻倍的是点数t，价值v不翻倍。',
        complexity=r'总翻倍点数和B≤2600，时间 $O(nkB)$，空间 $O(kB)$。')
    put(235951,2200,['分支限界','0/1背包'],'n≤100但容量与价值至10^9的精确0/1背包。',
        '这些约束不能直接开O(S)容量DP，价值和DP也可能过大。采用精确分支限界：按价值/时间降序排，搜索取或不取。对每个搜索节点，暂时允许剩余草药按比例分割，贪心装满得到分数背包上界；若上界不超过已有整数最优值，整棵分支可剪。所有剩余草药都能装下时直接全部选取。\n\n比例比较用128位交叉乘，分数上界只在最后不能完整装入的一件上向下取整；最优值为整数，向下取整仍是合法上界。先搜索取当前物品，尽早得到较好下界。\n\n通用0/1背包的精确求解最坏仍为指数级；按当前题面的大容量界，不能声称这个搜索有多项式最坏时间。这里给出不丢正确性的精确算法，并明确此性能限制。',
        r'''int n; long long capacity; cin >> n >> capacity; struct Item { long long weight,value; }; vector<Item> a; for (int i=0;i<n;i++) { long long w,v; cin >> w >> v; if (w<=capacity) a.push_back({w,v}); } sort(a.begin(),a.end(),[](auto x,auto y) { return (__int128)x.value*y.weight>(__int128)y.value*x.weight; }); n=a.size(); vector<long long> suffixWeight(n+1),suffixValue(n+1); for (int i=n-1;i>=0;i--) { suffixWeight[i]=suffixWeight[i+1]+a[i].weight; suffixValue[i]=suffixValue[i+1]+a[i].value; } long long answer=0; auto dfs=[&](auto &&self,int i,long long remaining,long long value)->void { answer=max(answer,value); if (i==n) return; if (suffixWeight[i]<=remaining) { answer=max(answer,value+suffixValue[i]); return; } long long bound=value,space=remaining; for (int j=i;j<n;j++) { if (a[j].weight<=space) { space-=a[j].weight; bound+=a[j].value; } else { bound+=(long long)((__int128)space*a[j].value/a[j].weight); break; } } if (bound<=answer) return; if (a[i].weight<=remaining) self(self,i+1,remaining-a[i].weight,value+a[i].value); self(self,i+1,remaining,value); }; dfs(dfs,0,capacity,0); cout << answer;''',
        '不要按单位价值直接贪心输出，那只对可分割物品成立。本代码仅把分数贪心用于安全上界，搜索仍精确。',
        complexity=r'最坏 $O(n2^n)$ 时间，空间 $O(n)$；实际剪枝量依数据而定。')
    put(236172,1800,['位集','0/1背包'],'十万件货物，容量十万，求最大可装总重量。',
        '用位集possible表示可达到的重量集合，初始仅0。加入重量w时possible |= possible<<w，移位后的每一位对应在旧方案上选当前货物；整条位集一次更新，避免O(nA)逐状态。重量>A的货物无法选，直接忽略。最后从A向下找第一个置位。',
        r'''int n,capacity; cin >> n >> capacity; bitset<100001> possible; possible[0]=1; while (n--) { int w; cin >> w; if (w<=capacity) possible|=possible<<w; } for (int x=capacity;x>=0;x--) if (possible[x]) { cout << x; break; }''',
        '每件只有一份，右侧移位基于操作前位集，不能改成完全背包。bitset上界覆盖题目最大容量。',
        complexity=r'时间 $O(nU/机器字长+U)$，空间 $O(U/机器字长)$，U=100000。')
    put(236175,1900,['拓扑排序','关键路径'],'依赖任务并行执行，求最短总工期内可以拖延的任务。',
        '拓扑排序计算最早开始early[v]=max(early[u]+time[u])，所有任务最早完成时间最大值即总工期T。若拓扑点数不足n，存在环而无法完成。\n\n再逆拓扑计算最迟开始：所有任务初始latest[u]=T−time[u]，对每条u→v用latest[v]−time[u]缩小latest[u]。early[u]<latest[u]说明存在正松弛，可以拖延；相等则位于某条关键路径。',
        r'''int n,m; cin >> n >> m; vector<long long> duration(n),early(n),latest(n); for (auto &x:duration) cin >> x; vector<vector<int>> edge(n); vector<int> indegree(n); while (m--) { int u,v; cin >> u >> v; u--;v--;edge[u].push_back(v);indegree[v]++; } queue<int> queue; for (int u=0;u<n;u++) if (!indegree[u]) queue.push(u); vector<int> order; long long total=0; while (!queue.empty()) { int u=queue.front();queue.pop();order.push_back(u);total=max(total,early[u]+duration[u]);for (int v:edge[u]) { early[v]=max(early[v],early[u]+duration[u]);if (--indegree[v]==0) queue.push(v); } } if ((int)order.size()!=n) { cout << -1;return 0; } for (int u=0;u<n;u++) latest[u]=total-duration[u]; for (int i=n-1;i>=0;i--) { int u=order[i];for (int v:edge[u]) latest[u]=min(latest[u],latest[v]-duration[u]); } vector<int> answer;for(int u=0;u<n;u++) if (early[u]<latest[u]) answer.push_back(u+1);cout << answer.size() << '\n';for(int i=0;i<(int)answer.size();i++) cout << answer[i] << (i+1==(int)answer.size()?'\n':' ');if(answer.empty())cout << '\n';''',
        '多个终点都受同一个总工期约束，不能只从任意一个终点反推。',
        complexity=r'时间、空间均 $O(n+m)$。')
    put(236176,2000,['虚拟节点','Dijkstra'],'邻层任意点付C移动，另有特殊边，同层不能免费互达。',
        '为每层建立入口汇集点hub[l]，让hub[l]到本层每个原点有0边；原点u只向hub[layer[u]−1]与hub[layer[u]+1]连C边，不能连向本层hub。这样恰好实现一次付费到相邻层任意原点，不引入同层免费通道。再加入特殊双向边，Dijkstra求1到n。',
        r'''int n,m; long long cost; cin >> n >> m >> cost; vector<int> layer(n); for (int &x:layer) cin >> x; vector<vector<pair<int,long long>>> graph(2*n); for (int u=0;u<n;u++) { int l=layer[u]-1; graph[n+l].push_back({u,0}); if (l) graph[u].push_back({n+l-1,cost}); if (l+1<n) graph[u].push_back({n+l+1,cost}); } while (m--) { int u,v; long long w; cin >> u >> v >> w; graph[u-1].push_back({v-1,w}); graph[v-1].push_back({u-1,w}); } auto distance=dijkstra(graph,0); cout << (distance[n-1]>=(1LL<<59)?-1:distance[n-1]);''',
        '原点到本层hub若也连0，会误把同层任意两点免费连接。空层hub没有出边，无法作为中转通道。',
        declarations=DIJKSTRA,complexity=r'时间 $O((n+m)\log n)$，空间 $O(n+m)$。')
    put(236210,1900,['超边建图','Dijkstra'],'两人通过同类传送门付费移动，最早相遇时间与全部相遇点。',
        '每类传送门建一个虚拟点，原点到该类虚点费用t，虚点到其全部原点费用0，避免把S个点完全连边。分别从1与n跑Dijkstra。两人可等候，因此在点u相遇时间为max(d1[u],dn[u])，对原始点取最小，再升序输出全部达到该时间者。',
        r'''int n,m; cin >> n >> m; vector<vector<pair<int,long long>>> graph(n+m); for (int i=0;i<m;i++) { long long t;int count;cin >> t >> count;while(count--) { int u;cin >> u;u--;graph[u].push_back({n+i,t});graph[n+i].push_back({u,0}); } } auto first=dijkstra(graph,0),second=dijkstra(graph,n-1);long long best=(1LL<<60);for(int u=0;u<n;u++)best=min(best,max(first[u],second[u]));if(best>=(1LL<<59)){cout << -1;return 0;}cout << best << '\n';bool space=false;for(int u=0;u<n;u++)if(max(first[u],second[u])==best){if(space)cout << ' ';space=true;cout << u+1;}cout << '\n';''',
        '虚拟点不是可相遇地点，最后只枚举原始n点。两人并行，取最大到达时间而非距离和。',
        declarations=DIJKSTRA,complexity=r'令L为传送门出现总数，时间 $O((n+m+L)\log(n+m))$，空间 $O(n+m+L)$。')
    put(208252,1900,['按边数DP','有向无环图'],'多次查询DAG两点间最小平均边权。',
        'DAG路径至多n−1条边。对每个起点s，dp[k][v]表示恰走k条边到v的最短总长，按边数逐层沿所有边松弛。对每个终点枚举k=1..n−1，取dp[k][v]/k最小。这样无需对每个询问做浮点二分，预处理全部起终答案即可。',
        r'''int n,m; cin >> n >> m; struct Edge { int u,v,w; };vector<Edge> edge(m);for(auto &e:edge){cin >> e.u >> e.v >> e.w;e.u--;e.v--;}const long long inf=LLONG_MAX/4;vector<vector<long double>> answer(n,vector<long double>(n,1e100L));for(int source=0;source<n;source++){vector<long long> previous(n,inf);previous[source]=0;for(int count=1;count<n;count++){vector<long long> current(n,inf);for(auto e:edge)if(previous[e.u]<inf)current[e.v]=min(current[e.v],previous[e.u]+e.w);for(int v=0;v<n;v++)if(current[v]<inf)answer[source][v]=min(answer[source][v],(long double)current[v]/count);previous.swap(current);}}int q;cin >> q;cout << fixed << setprecision(8);while(q--){int u,v;cin >> u >> v;if(answer[u-1][v-1]>1e90L)cout << "OMG!\n";else cout << answer[u-1][v-1] << '\n';}''',
        '0条边没有可定义的平均值，不把同点空路径当0。最短总长路径未必平均值最小。',
        floating_output=True,complexity=r'预处理 $O(n^2m+n^3)$，每问 $O(1)$，空间 $O(n^2+m)$。')
    put(235228,1600,['分段筛'],'统计大端点短区间的素数个数。',
        '先筛出不超过sqrt(R)的素数，对每个p只标记[L,R]中的合数倍数，从max(p²,ceil(L/p)*p)开始。最后数未标记位置。L≥2，无需额外处理1。',
        r'''long long l,r;cin >> l >> r;auto primes=sieve(46341);vector<bool> composite(r-l+1);for(long long p:primes){if(p*p>r)break;for(long long x=max(p*p,(l+p-1)/p*p);x<=r;x+=p)composite[x-l]=true;}long long answer=0;for(bool x:composite)answer+=!x;cout << answer;''',
        '从p²起防止把区间内的素数p自身划掉。扫描与乘法用64位。',
        declarations=SIEVE,complexity=r'时间 $O((R-L+1)\log\log R+\sqrt R\log\log R)$，空间 $O(R-L+\sqrt R)$。')
    put(236190,2100,['扩展中国剩余定理','有界解'],'合并糖果余数，最小正解保证小于2^31。',
        '按扩展CRT合并x≡R(mod M)，每次解M*t≡r−R(mod p)。但这里只保证解小，未保证所有模数最小公倍数小。利用解界B=2^31：一旦合并周期M≥B，区间[1,B)里至多剩一个候选R，后续只检查它是否满足每条同余，无需继续扩大周期。\n\n进入冻结前M<B且p≤10^9，一步新周期至约2×10^18，64位可存，乘法中间用128位。若最终R=0且M<B，最小正解应取M；若冻结后R=0，界内无正解。',
        r'''int n;cin >> n;const long long bound=1LL<<31;long long remainder=0,period=1;bool possible=true,frozen=false;while(n--){long long p,r;cin >> p >> r;if(!possible)continue;if(frozen){if(remainder%p!=r)possible=false;continue;}long long u,v,g=extendedGcd(period,p,u,v),delta=r-remainder;if(delta%g){possible=false;continue;}long long reduced=p/g,step=(long long)(((__int128)(delta/g)*u%reduced+reduced)%reduced),nextPeriod=period*reduced;remainder=(long long)(((__int128)remainder+(__int128)period*step)%nextPeriod);period=nextPeriod;if(period>=bound){frozen=true;if(remainder==0 || remainder>=bound)possible=false;}}long long answer=remainder?remainder:period;if(answer>=bound)possible=false;cout << (possible?answer:-1);''',
        '原题要求糖果数是正数，零余数系统的最小正解是周期，不是0。小解不意味着模数乘积小。',
        declarations=EXGCD,complexity=r'时间 $O(n\log U)$，空间 $O(\log U)$。')
    if 'nowcoder-global::236191' not in existing:
        reviewed_clone(236191,124160,'已核对原Frogs与本题样例；本题“两只及以上”文字与两样例冲突，按来源原题和样例的至少一只口径，并在正文突出说明。',replacements={
            '## 题意':'## 题面口径核对\n\n此页文字写“两只及以上”，但与给定样例冲突：m=12、步长9和10时，两只都能到的只有0、6，编号和是6；页面却输出42，它是至少一只可到的并集之和。两组样例及来源Frogs均对应并集。下文参考代码采用与样例一致的至少一只口径。若确实要求至少两只，应按每个gcd类别累计覆盖青蛙数，再以覆盖数≥2判断，而不能只做存在性标记。\n\n## 题意',
            'int tests;':'int tests = 1;','cin >> tests;':'' ,
            'cout << "Case #" << tc << ": " <<':'cout <<'
        })
    if 'nowcoder-global::236214' not in existing:
        reviewed_clone(236214,50615,'核对普通Nim，改为Alice/Bob输出，堆数和值扩大但32位异或仍覆盖。',replacements={'"win"':'"Alice"','"lose"':'"Bob"'})
    put(236262,1500,['操作奇偶性'],'每次删除一棵完美二叉子树，判断胜负。',
        '题目定义的“完全二叉”实际是每层全满的完美二叉树，节点数为2^h−1，永远为奇数。因此每步删除奇数个节点，节点总数奇偶每步翻转。只要还剩节点就有叶子，单节点子树可以删除，游戏必在空树结束。总操作次数与初始n同奇偶，所以n奇数先手胜，偶数后手胜。',
        r'''int n;cin >> n;for(int i=1;i<n;i++){int u,v;cin >> u >> v;}cout << (n%2?"Alice":"Bob");''',
        '按题目给出的“所有叶同深度且非叶都有两儿子”定义，不能套用通常仅最后一层可缺的完全二叉树。',
        complexity=r'读入时间 $O(n)$，额外空间 $O(1)$。')
    if 'nowcoder-global::236236' not in existing:
        add_python(236236,1900,['几何概率','圆周覆盖','大整数分数'],'随机圆周方位点能被一块等分扇形包含的概率。',
            '随机点落在圆盘内，其极角独立均匀。有r个点、分成p等份（p>2）时，若它们能被一个角宽2π/p的扇形包含，则覆盖扇形顺时针的首个点唯一；指定该点后，其余r−1点均落在它后方1/p圆周，概率(1/p)^(r−1)。r种首点情形互斥，答案r/p^(r−1)，用最大公约数约分。\n\n当前页面把输入n、m的角色写反：若按“n草莓、m份”理解，样例3 4应为3/16；实际样例是4/27，对应3份、4草莓。参考代码按两组样例及来源模型采用第一个数为份数p、第二个数为草莓数r，并明确记录此题面矛盾。',
            '''import math
import sys

parts, points = map(int, sys.stdin.buffer.read().split())
numerator = points
denominator = parts ** (points - 1)
g = math.gcd(numerator, denominator)
print(f'{numerator // g}/{denominator // g}')
''',
            '大整数分母可超过64位，不用浮点约分。若平台修正输入含义，应对应交换parts和points。',
            complexity=r'大整数幂与gcd时间依位数而定，结果位数 $O(r\log p)$，空间同结果位数。')
    put(17450,1600,['整除分块'],'多次求1..x的约数个数和。',
        '交换求和，每个约数d贡献它在1..x中的倍数个数floor(x/d)。相同商q=floor(x/l)持续到r=floor(x/q)，整段贡献q*(r−l+1)。每次跳到r+1，只有O(sqrt x)段。',
        r'''int q;cin >> q;while(q--){long long x;cin >> x;long long answer=0;for(long long l=1,r;l<=x;l=r+1){long long quotient=x/l;r=x/quotient;answer+=quotient*(r-l+1);}cout << answer << '\n';}''',
        '这是约数个数和，不是约数值之和。答案使用64位。',
        complexity=r'每问时间 $O(\sqrt x)$，空间 $O(1)$。')
    put(218398,1700,['整除分块','约数和'],'G(n)为前n个数约数和之和，求G(G(n))。',
        '每个约数d对其floor(n/d)个倍数贡献d，所以G(n)=Σd*floor(n/d)。整除分块后，每段商q固定，贡献q*(l+r)*(r−l+1)/2。先求一次G(n)，再对这个结果求同样的函数。n≤50000时第二次参数约2×10^9，结果仍在64位内。',
        r'''auto sumDivisors=[](long long n){long long answer=0;for(long long l=1,r;l<=n;l=r+1){long long quotient=n/l;r=n/quotient;long long count=r-l+1,ends=l+r;if(count%2==0)count/=2;else ends/=2;answer+=quotient*count*ends;}return answer;};long long n;cin >> n;cout << sumDivisors(sumDivisors(n));''',
        '先把等差求和的偶数因子除2，再乘商，降低中间乘积。不要混成约数个数函数。',
        complexity=r'时间 $O(\sqrt n+\sqrt{G(n)})$，空间 $O(1)$。')
    put(204916,1700,['整除分块'],'求Σfloor(n/i)模998244353，n至10^13。',
        '相同商q=n/l对应右端r=n/q，区间[l,r]统一贡献q*(r−l+1)。枚举O(sqrt n)段，两个因子先取模再相乘，避免原始乘积溢出。',
        r'''long long n;cin >> n;const long long mod=998244353;long long answer=0;for(long long l=1,r;l<=n;l=r+1){long long quotient=n/l;r=n/quotient;answer=(answer+(quotient%mod)*((r-l+1)%mod))%mod;}cout << answer;''',
        'n不是模数内整数，分块边界要用完整n做整数除法，不能先取模。',
        complexity=r'时间 $O(\sqrt n)$，空间 $O(1)$。')
    put(15164,1200,['树状数组'],'单点加、区间和。',
        '树状数组维护原数组值。单点加沿下标不断增加lowbit，前缀和沿下标减少lowbit。区间[l,r]用prefix(r)−prefix(l−1)。',
        r'''int n,m;cin >> n >> m;Fenwick bit(n);for(int i=1;i<=n;i++){long long x;cin >> x;bit.add(i,x);}while(m--){int op,x;long long y;cin >> op >> x >> y;if(op==1)bit.add(x,y);else cout << bit.sum((int)y)-bit.sum(x-1) << '\n';}''',
        '位置从1开始。区间和可能超过32位，Fenwick节点用64位。',
        declarations=BIT,complexity=r'初始化 $O(n\log n)$，操作 $O(\log n)$，空间 $O(n)$。')


if __name__=='__main__':run()
