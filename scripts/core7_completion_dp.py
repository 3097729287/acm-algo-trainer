from core7_completion import add

add('CF1882D','按边贡献计算全部根的代价',
    '根为 r 时，一条边的异或权值要乘它远离根一侧的点数。先求根 1 的答案与子树大小，再换根：跨边 u−v 时，答案变化为 (a[u] xor a[v])·(n−2size[v])。',
    '操作可使一整棵子树的数值统一异或，沿边两侧的差异代价只由端点的异或值决定。固定根以后，这条边的代价影响子树内每个点，因此贡献为边权 w=a[u] xor a[v] 乘子树大小。各边贡献相加得到根的总代价。\n\n任选 1 为根，用遍历顺序的倒序计算子树大小，并求 Σw·size。把根从父 u 移到子 v 时，只有这条边的两侧归属改变：原来乘 size[v]，现在乘 n−size[v]，其余边的分割方向不变。所以 answer[v]=answer[u]+w(n−2size[v])。\n\n按父先子的顺序传播答案，每条边只处理常数次。所有乘积与答案用 long long，避免大型星形树溢出。',
    '每组时间 O(n)，空间 O(n)。','边权是端点值异或；换根差为 n−2size；使用六十四位。',r'''
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<long long>a(n),ans(n);for(auto&x:a)cin>>x;vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),size(n,1),order={0};parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(u!=parent[order[i]]){parent[u]=order[i];order.push_back(u);}for(int i=n-1;i>0;i--){int v=order[i],p=parent[v];size[p]+=size[v];ans[0]+=(a[v]^a[p])*size[v];}for(int i=1;i<n;i++){int v=order[i],p=parent[v];ans[v]=ans[p]+(a[v]^a[p])*(n-2LL*size[v]);}for(long long x:ans)cout<<x<<' ';cout<<'\n';}
''')

add('P3047','按精确距离做树上换根',
    '先求每个点子树内距离恰为 d 的牛数，再向下换根。孩子距离 d 的外部贡献来自父亲距离 d−1 的总量，并扣掉重复落在孩子子树中的距离 d−2 部分。',
    '设 down[u][d] 为 u 子树内与 u 距离恰好 d 的牛数。down[u][0] 是本点牛数，孩子 v 的 down[v][d−1] 可加入 down[u][d]。先按子先父顺序计算。\n\n再令 all[u][d] 为整棵树中与 u 距离 d 的牛数。根的 all 等于 down。对父子 u、v，孩子外部的点到 v 的距离等于到 u 的距离加一，所以候选是 all[u][d−1]。但其中包含 v 子树内距离 u 为 d−1 的点，即 down[v][d−2]，必须扣掉。\n\n因此 all[v][d]=down[v][d]+all[u][d−1]−down[v][d−2]，d=1 时没有扣除项。把 d=0 到 K 累加即可得到范围内总牛数。两个阶段分别使用 down 和 all，避免换根后污染子树原始量。',
    '时间 O(nK)，空间 O(nK)。','距离是边数；d<2 不减子树项；子树数组和全树数组分开。',r'''
int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}int width=k+1;vector<int>down(n*width),all(n*width),parent(n,-1),order={0};for(int i=0;i<n;i++)cin>>down[i*width];parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(u!=parent[order[i]]){parent[u]=order[i];order.push_back(u);}for(int i=n-1;i>0;i--){int v=order[i],p=parent[v];for(int d=1;d<=k;d++)down[p*width+d]+=down[v*width+d-1];}all=down;for(int i=1;i<n;i++){int v=order[i],p=parent[v];for(int d=1;d<=k;d++)all[v*width+d]+=all[p*width+d-1]-(d>=2?down[v*width+d-2]:0);}for(int v=0;v<n;v++){long long ans=0;for(int d=0;d<=k;d++)ans+=all[v*width+d];cout<<ans<<'\n';}
''')

add('P3177','树形背包统计每条边的同色点对',
    '一条边下方有 size 个点，其中 j 个黑点，它对同色点对距离的贡献是 w·[j(k−j)+(size−j)(n−k−size+j)]。树形背包决定每棵子树的黑点数，并累加各边贡献。',
    '两点距离可以拆成路径上各边权值的和。固定一条父子边，只有分居两侧的同色点对会经过它。若孩子子树大小为 s、黑点数为 j，全树恰有 k 个黑点，则跨边黑点对为 j(k−j)，白点对为 (s−j)(n−k−s+j)。\n\n令 dp[u][b] 表示 u 子树恰染 b 个黑点时，已经处理的子树内部各边能取得的最大贡献。初始只含根 u，可选白或黑。合并孩子 v 时枚举它分配的 j，把 dp[u][b]+dp[v][j] 加上 u−v 这条边按 j 计算的贡献。\n\n该贡献中使用的是全树固定黑白总数，因此虽然在子树内计算，也已经准确统计所有跨边点对，不需要知道外部具体染色。每条边只结算一次，根的 dp[k] 即为答案。不可行状态设负无穷，并限制状态不超过实际子树大小与 k。',
    '时间 O(n²)，空间 O(nk)，实现中按实际子树大小限制状态。','计无序同色点对；白点外侧数是 n−k−s+j；不可行状态不参与转移。',r'''
int n,k;cin>>n>>k;vector<vector<pair<int,int>>>g(n);for(int i=1;i<n;i++){int u,v,w;cin>>u>>v>>w;u--;v--;g[u].push_back({v,w});g[v].push_back({u,w});}vector<int>parent(n,-1),size(n,1),weight(n),order={0};parent[0]=0;for(int i=0;i<n;i++)for(auto [u,w]:g[order[i]])if(u!=parent[order[i]]){parent[u]=order[i];weight[u]=w;order.push_back(u);}const long long neg=LLONG_MIN/4;vector<vector<long long>>dp(n);for(int i=n-1;i>=0;i--){int v=order[i];if(dp[v].empty()){dp[v]={0};if(k)dp[v].push_back(0);}if(v==0)break;int p=parent[v];if(dp[p].empty()){dp[p]={0};if(k)dp[p].push_back(0);}vector<long long>next(min(k,size[p]+size[v])+1,neg);for(int a=0;a<(int)dp[p].size();a++)if(dp[p][a]!=neg)for(int b=0;b<(int)dp[v].size()&&a+b<=k;b++)if(dp[v][b]!=neg){long long outsideWhite=n-k-size[v]+b;if(outsideWhite<0)continue;long long pairs=1LL*b*(k-b)+1LL*(size[v]-b)*outsideWhite;next[a+b]=max(next[a+b],dp[p][a]+dp[v][b]+pairs*weight[v]);}size[p]+=size[v];dp[p].swap(next);vector<long long>().swap(dp[v]);}cout<<dp[0][k]<<'\n';
''')

add('P9437','同时换根维护拼接值与十进制倍率',
    '每个点维护从它出发的路径值总和，以及各路径十进制倍率总和。先自底向上合并子树，再扣除孩子分支得到外部量，向孩子换根，最后累加所有起点的路径值。',
    '在数字 x 前拼接 a，会得到 a·10^(x的位数)+x。因此只存路径值和不够，还要存路径总位数对应的 10 的幂之和。记 P[u]=10^(a[u]位数)，F[u] 为从 u 到子树各终点的拼接值之和，G[u] 为这些路径的倍率之和。\n\n初始 F[u]=a[u]、G[u]=P[u]。合并孩子 v 时，加入 F[v]+a[u]G[v] 到 F[u]，加入 P[u]G[v] 到 G[u]。这是把 a[u] 统一拼在每条孩子路径前面。\n\n换根时，父亲全树结果中先扣去通向 v 的分支：外部路径值 A=全F[u]−F[v]−a[u]G[v]，外部倍率 B=全G[u]−P[u]G[v]。在这些路径前拼接 a[v] 后，全F[v]=F[v]+A+a[v]B，全G[v]=G[v]+P[v]B。\n\n输入保证父编号更小，可以直接倒序做子树合并、正序做换根，不需要邻接表。数字零的位数仍是一，倍率为十。所有运算对 998244353 规范取模。',
    '时间 O(n log A)，空间 O(n)。','0 的十进制长度为 1；保留子树量供扣除；减法取模防负数；计有向路径及单点。',r'''
int n;cin>>n;const long long mod=998244353;vector<long long>a(n+1),p(n+1),f(n+1),g(n+1),allf,allg;for(int i=1;i<=n;i++){cin>>a[i];p[i]=10;for(long long x=a[i];x>=10;x/=10)p[i]=p[i]*10%mod;f[i]=a[i]%mod;g[i]=p[i];}vector<int>parent(n+1);for(int i=2;i<=n;i++)cin>>parent[i];for(int v=n;v>=2;v--){int u=parent[v];f[u]=(f[u]+f[v]+a[u]*g[v])%mod;g[u]=(g[u]+p[u]*g[v])%mod;}allf=f;allg=g;long long ans=allf[1];for(int v=2;v<=n;v++){int u=parent[v];long long outsideF=(allf[u]-f[v]-a[u]*g[v]%mod+2*mod)%mod,outsideG=(allg[u]-p[u]*g[v]%mod+mod)%mod;allf[v]=(f[v]+outsideF+a[v]*outsideG)%mod;allg[v]=(g[v]+p[v]*outsideG)%mod;ans=(ans+allf[v])%mod;}cout<<ans<<'\n';
''')

add('AT_dp_j','按一盘一、二、三个寿司计数',
    '状态只记录分别剩一、二、三个寿司的盘数 a,b,c。选到空盘会原地停留，把这部分期望移到等式左边，得到 E=(n+aE1+bE2+cE3)/(a+b+c)。',
    '盘子编号不影响之后的随机选择，只需要知道三类非空盘的数量。设 E(a,b,c) 为从当前状态吃完所需的期望操作数。选中一寿司盘后变为 (a−1,b,c)，二寿司盘变为 (a+1,b−1,c)，三寿司盘变为 (a,b+1,c−1)。\n\n每次无论选中什么都花费一步，另有 (n−a−b−c)/n 的概率选中空盘并保持原状态。因此 E=1+[aE1+bE2+cE3+(n−a−b−c)E]/n。把自身项移到左边，便得到实现中的除式。\n\n空状态 E(0,0,0)=0。按 c、b、a 依次递增枚举，二寿司转移用到更小的 b，三寿司转移用到更小的 c，都已计算。只存 a+b+c<=n 的状态。使用 double 输出足够精度。',
    '时间 O(n³)，空间 O(n³)。','分子常数是总盘数 n；分母是非空盘数；不能忽略选到空盘的操作。',r'''
int n;cin>>n;int count[4]={};for(int i=0;i<n;i++){int x;cin>>x;count[x]++;}int side=n+2;vector<double>dp((size_t)side*side*side);auto at=[&](int a,int b,int c)->double&{return dp[((size_t)c*side+b)*side+a];};for(int c=0;c<=n;c++)for(int b=0;b+c<=n;b++)for(int a=0;a+b+c<=n;a++){if(a+b+c==0)continue;double value=n;if(a)value+=a*at(a-1,b,c);if(b)value+=b*at(a+1,b-1,c);if(c)value+=c*at(a,b+1,c-1);at(a,b,c)=value/(a+b+c);}cout<<fixed<<setprecision(12)<<at(count[1],count[2],count[3])<<'\n';
''')
