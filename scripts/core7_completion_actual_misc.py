from core7_completion import add
from core7_completion_actual_math import MOD

add('P7942','单串内部贡献与相邻两串的跨界贡献',
    '每串至少含两种字符，所以同字母连续段最多跨一个串边界。内部长度 k 窗口乘 n!；跨界窗口按相邻有序串对统计，乘 (n−1)!，并扣除把同一串与自己配对的情况。',
    '一段同字母若跨过两个边界，中间完整字符串就必须全部相同字母，与 easy version 保证矛盾。因此只有串内与跨一个边界两类。\n\n串内每个长度 L 的连续段贡献 max(0,L−k+1)，它会在所有 n! 个排列中出现。对跨界情况，设左串后缀长 s、右串前缀长 p，且字母同为 c。窗口从左取 u 个、右取 k−u 个，要求 max(1,k−p)≤u≤min(s,k−1)，区间整数数量就是跨界贡献。\n\n按字母及长度统计后缀频次、前缀频次，枚举 s、p 的乘积得到有序对数量；若同一个串同时属于两类，需要减去它与自己配对的计数。每个不同串的有序相邻关系在排列中出现 (n−1)! 次。m≤100，可直接枚举二十六种字母和两种长度。',
    '时间 O(nm+26m²)，空间 O(26m²+n)。','仅针对每串非单字母的 easy 保证；跨界两串必须不同编号；相同内容不同编号仍是不同串。',r'''
int n,m,k;cin>>n>>m>>k;const long long P=998244353;vector<vector<long long>>suffix(26,vector<long long>(m+1)),prefix=suffix;vector<vector<vector<int>>>self(26,vector<vector<int>>(m+1,vector<int>(m+1)));long long inside=0;for(int i=0;i<n;i++){string s;cin>>s;for(int l=0;l<m;){int r=l+1;while(r<m&&s[r]==s[l])r++;inside+=max(0,r-l-k+1);l=r;}int p=1,t=1;while(p<m&&s[p]==s[0])p++;while(t<m&&s[m-1-t]==s[m-1])t++;prefix[s[0]-'a'][p]++;suffix[s.back()-'a'][t]++;if(s[0]==s.back())self[s[0]-'a'][t][p]++;}vector<long long>fact(n+1,1);for(int i=1;i<=n;i++)fact[i]=fact[i-1]*i%P;long long cross=0;for(int c=0;c<26;c++)for(int s=1;s<=m;s++)for(int p=1;p<=m;p++){int ways=max(0,min(s,k-1)-max(1,k-p)+1);long long pairs=(suffix[c][s]*prefix[c][p]-self[c][s][p])%P;cross=(cross+pairs*ways)%P;}cout<<((inside%P)*fact[n]+cross*fact[n-1])%P<<'\n';
''')

add('P9087','等号覆盖无重音窗口的分段线性优化',
    '相邻相同的一处最多覆盖 k−1 个长度 k 窗口。若设置 c 处重音，最少仍有 max(0,n−k+1−c(k−1)) 个干净窗口。代价分段线性，只需检查零、整除点及再多一处。',
    '把相邻字符是否相同视为边。一个长度 k 子串有重音，当且仅当它内部 k−1 条边至少一条被选中。总窗口数 W=n−k+1，一条重音边最多覆盖 k−1 个窗口，所以 c 处至少留下 max(0,W−c(k−1)) 个干净窗口。\n\n这个下界可以达到：把重音边放在 k−1、2(k−1)、……处，它们覆盖的窗口连续且不重复，最后一处允许覆盖不足 k−1 个。其它边让相邻字符不同，只用 a、b 两个字母就能实现任意边选择。\n\n总费用 c·a+max(0,W−c(k−1))·b，在最后一次覆盖前后分别线性，所以只需 c=0、floor(W/(k−1))、ceil(W/(k−1)) 三种候选。k>n 时没有长度 k 窗口，直接输出交替串、费用零。',
    '每组时间 O(n)，额外空间 O(n) 用于输出。','重音按相邻一对计数；末次覆盖可以不满；所有乘积六十四位。',r'''
int T;cin>>T;while(T--){int n,k;long long a,b;cin>>n>>k>>a>>b;if(k>n){cout<<0<<'\n';for(int i=0;i<n;i++)cout<<(i%2?'b':'a');cout<<'\n';continue;}long long W=n-k+1,width=k-1,best=LLONG_MAX,count=0;for(long long c:{0LL,W/width,(W+width-1)/width}){long long value=c*a+max(0LL,W-c*width)*b;if(value<best){best=value;count=c;}}string s(n,'a');for(int i=1;i<n;i++){bool accent=i%width==0&&i/width<=count;s[i]=accent?s[i-1]:(s[i-1]=='a'?'b':'a');}cout<<best<<'\n'<<s<<'\n';}
''',checker='music')

add('P6748','父边是否超标的两状态树形 DP',
    '每点最多允许 floor((度数−1)/2) 条边大于忍耐度。DP 记录父边是否已经占用一个超标名额；对孩子边比较 ai、aChild、m 三个候选，把选择超标的收益排序后取允许数量。',
    '上中位数不超过 a[u]，等价于至少 floor(deg/2)+1 条边≤a[u]，也就是超标边最多 H=floor((deg−1)/2)。\n\n令 dp[u][state] 为 u 子树边权和最优值，state 表示父边是否>a[u]，父边本身的权值由父亲计入。处理孩子 v 时，子树费用只取决于边权是否>a[v]。因此该边最优值只可能是 a[u]、a[v] 或 m：两处阈值之间提高权值不改变状态，直到下一个阈值或上界。\n\n对这三个候选，分别求“不超 u 阈值”的最好 L 与“超 u 阈值”的最好 R。先全部选 L，再将正收益 R−L 降序排列；父边状态零可取前 H 个，状态一可取前 H−1 个。某状态名额为负就不可行。\n\n给定 a≥1 时全边权一已经可行，但代码仍保留不可行状态。后序计算采用迭代遍历，避免五十万点递归溢出。',
    '时间 O(n log n)，空间 O(n)。','中位数为上中位数；父边也占超标名额；候选值按两端阈值分类。',r'''
int n;long long m;cin>>n>>m;vector<long long>a(n);for(auto&x:a)cin>>x;vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),order={0};parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(parent[u]<0){parent[u]=order[i];order.push_back(u);}const long long NEG=-(1LL<<60);vector<array<long long,2>>dp(n,{NEG,NEG});for(int i=n-1;i>=0;i--){int v=order[i],H=((int)g[v].size()-1)/2;long long base=0;vector<long long>gains;for(int u:g[v])if(parent[u]==v){long long low=NEG,high=NEG;for(long long w:{a[v],a[u],m}){long long sub=dp[u][w>a[u]];if(sub==NEG)continue;if(w<=a[v])low=max(low,w+sub);else high=max(high,w+sub);}base+=low;if(high>low)gains.push_back(high-low);}sort(gains.rbegin(),gains.rend());vector<long long>prefix(gains.size()+1);for(int j=0;j<(int)gains.size();j++)prefix[j+1]=prefix[j]+gains[j];for(int state=0;state<2;state++)if(H>=state)dp[v][state]=base+prefix[min((int)gains.size(),H-state)];}cout<<(dp[0][0]==NEG?-1:dp[0][0])<<'\n';
''')

add('P7480','只向左右最近的更便宜油站转移',
    '允许折返找便宜油，不能只按向右贪心。最优路线的下一次有效加油一定可选为某方向遇到的第一个更便宜站；单调栈求左右候选，建线性边数图跑 Dijkstra。',
    '油箱无限，若下一次购买的油价不更低，可以直接在当前站购买这部分油而不增加费用，因此有效加油价格严格下降。向某方向走时，若先遇到更便宜站，就可以先在这里改用更便宜的油，再继续后面的路线，不会变差。故只需向左右最近的严格更便宜站建边，边权为当前价乘距离。\n\n把终点当作价格零的特殊站，到了就结束。排序位置，用两个单调栈分别找到左右严格更便宜的站；同位置合并为最低价格。每点至多两条边，Dijkstra 求起点到终点最短费用。\n\n这个模型保留起点左侧站，也允许左右折返。例如起点油价一百、左一格油价一、终点右一百格，先向左加油费用二百零一，远好于一直向右的一万。这样的反例说明不能删掉左侧站。',
    '时间 O(n log n)，空间 O(n)。','起点左侧油站可能有用；下一站价格严格降低；同坐标取最低价；费用六十四位。',r'''
int n;long long s,t;cin>>n>>s>>t;vector<pair<long long,long long>>points;for(int i=0;i<n;i++){long long c,x;cin>>c>>x;points.push_back({x,c});}points.push_back({t,0});sort(points.begin(),points.end());vector<long long>x,c;for(auto[pos,price]:points){if(!x.empty()&&x.back()==pos)c.back()=min(c.back(),price);else{x.push_back(pos);c.push_back(price);}}int N=x.size(),start=lower_bound(x.begin(),x.end(),s)-x.begin(),goal=lower_bound(x.begin(),x.end(),t)-x.begin();vector<array<int,2>>to(N,{-1,-1});vector<int>st;for(int i=0;i<N;i++){while(!st.empty()&&c[st.back()]>=c[i])st.pop_back();if(!st.empty())to[i][0]=st.back();st.push_back(i);}st.clear();for(int i=N-1;i>=0;i--){while(!st.empty()&&c[st.back()]>=c[i])st.pop_back();if(!st.empty())to[i][1]=st.back();st.push_back(i);}const long long INF=4000000000000000000LL;vector<long long>d(N,INF);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[start]=0;q.push({0,start});while(!q.empty()){auto[dist,v]=q.top();q.pop();if(dist!=d[v])continue;if(v==goal){cout<<dist<<'\n';return 0;}for(int u:to[v])if(u>=0){long long nd=dist+c[v]*llabs(x[v]-x[u]);if(nd<d[u]){d[u]=nd;q.push({nd,u});}}}
''')

add('P9035','按最大值是否超过一半分类的组合数',
    '令 h=floor((k+1)/2)。全部元素≤h 时是多重组合 C(n+h−1,n)；若最大值>h，它只能出现一次，枚举它后用曲棍球杆恒等式合并为 C(n+k−h−1,n)。',
    '序列不降，只要最大的两个数之和≤k+1，其它任意两数也满足。若最大值≤h，限制自动成立，从 h 种值中可重复选 n 个，共 C(n+h−1,n)。\n\n若最大值 x>h，不能出现两次，其余 n−1 个数都≤k+1−x=y。它们有 C(n+y−2,n−1) 种选择。x 从 h+1 到 k，等价于 y 从一到 k−h，求和由组合恒等式变为 C(n+k−h−1,n)。\n\n两类互斥且覆盖所有序列。n=1 同一公式仍给出 h+(k−h)=k；组合数上标小于下标时定义为零。先读全部询问，按实际最大上标预处理阶乘和逆阶乘。',
    '设最大组合数上标为 V，预处理 O(V)，每组 O(1)，空间 O(V+T)。','最大值大于一半时只能一次；组合数越界返回零；单元素也适用。',r'''
int T;cin>>T;vector<pair<int,int>>queries(T);int V=0;for(auto&[n,k]:queries){cin>>n>>k;int h=(k+1)/2;V=max({V,n+h-1,n+k-h-1});}vector<int>f(V+1,1),inv(V+1,1);for(int i=1;i<=V;i++)f[i]=1LL*f[i-1]*i%MOD;inv[V]=power(f[V],MOD-2);for(int i=V;i>=1;i--)inv[i-1]=1LL*inv[i]*i%MOD;auto C=[&](int n,int k)->long long{if(n<k||k<0)return 0;return 1LL*f[n]*inv[k]%MOD*inv[n-k]%MOD;};for(auto[n,k]:queries){int h=(k+1)/2;cout<<(C(n+h-1,n)+C(n+k-h-1,n))%MOD<<'\n';}
''',MOD)

add('CF1408F','两段二次幂区间分别归并为单值',
    '取不超过 n 的最大二次幂 L，对前 L 个、后 L 个位置分别进行分治配对。二次幂区间能变成同一个表达式；第二次覆盖后，全数组最多保留两种值。',
    '长度二的区间直接配对后相等。归纳地，先把左右半区各处理成一致值 A、B，再将对应位置按同样方向逐对操作，每对都变成 f(A,B)，所以整个区间一致，不要求 f 有任何交换或结合性质。\n\nL 是最大二次幂，有 2L≥n。先处理前 L 个使它们成为 A，再处理后 L 个成为 B。第二次操作之后，后 L 个全为 B，前面未被覆盖的部分仍全为 A，故至多两值。重叠部分旧值如何并不影响第二次分治的归纳结论。\n\n每段操作数为 (L/2)log2 L，两段总计 Llog2 L，远低于五十万。输出顺序要先递归两半，再逐对归并，不能倒过来。',
    '时间与输出 O(n log n)，递归空间 O(log n)，保存操作 O(n log n)。','函数可能不交换，配对方向保持一致；两段允许重叠；先分后合。',r'''
int n;cin>>n;int L=1;while(2*L<=n)L*=2;vector<pair<int,int>>ops;function<void(int,int)>solve=[&](int l,int length){if(length==1)return;int half=length/2;solve(l,half);solve(l+half,half);for(int i=0;i<half;i++)ops.push_back({l+i,l+half+i});};solve(1,L);solve(n-L+1,L);cout<<ops.size()<<'\n';for(auto[a,b]:ops)cout<<a<<' '<<b<<'\n';
''',checker='universal-pairs')

add('P5426','枚举跨中线的净转移数',
    '不跨中线时用两半逆序数差的绝对值补齐。跨中线只需考虑同一方向，把左侧最靠右的一类字符与右侧最靠左的另一类字符依次交换，维护必要代价和新的逆序差。',
    '内部相邻交换使两半逆序数之差 Δ 改变正负一；中线交换 10→01 则固定使 Δ 增加 totalOnes−n，反向取相反数。最优方案中同类字符不交叉移动，跨线同向交换即可覆盖所有净转移数。这个枚举思路可对照[出题者分析](https://usaco.org/current/data/sol_balance_gold_open19.html)。\n\n下面推导可直接实现的下标公式。第 t 次把左侧字符 bit 移到右侧，取左侧尚未搬走的最右 bit，下标 q；同时取右侧最左的 1−bit，右半局部下标 z。必要相邻交换数增加 n−q+z。\n\n对于 bit=1，最少搬运后的左半相当于删除右侧选出的这些一并末尾补零，右半相当于删除选出的零并前端补一。用“逆序数=一数乘(n−1)−所有一的位置和−一数的二项式”展开，得到 Δ 增量 q+z−2n+1+totalOnes；bit=0 时取相反数。\n\n对每个净转移数，强制搬运后再用内部交换消去剩余 |Δ|，候选为累计搬运代价+|Δ|。任何额外内部操作都只能每次改变 Δ 一，因此这个补齐代价既是下界也可达到。两种 bit 分别枚举，取最小。',
    '时间 O(n)，空间 O(n)。','z 使用右半局部下标；两种跨线方向均枚举；代价和逆序差用 long long。',r'''
int n;cin>>n;vector<int>a(2*n);int ones=0;for(int&x:a){cin>>x;ones+=x;}auto inversions=[&](int l,int r){long long count=0,answer=0;for(int i=l;i<r;i++)if(a[i])count++;else answer+=count;return answer;};long long initial=inversions(0,n)-inversions(n,2*n),ans=llabs(initial);for(int bit=0;bit<2;bit++){vector<int>left,right;for(int i=n-1;i>=0;i--)if(a[i]==bit)left.push_back(i);for(int i=0;i<n;i++)if(a[n+i]!=bit)right.push_back(i);long long delta=initial,cost=0;int sign=bit?1:-1;for(int i=0;i<(int)min(left.size(),right.size());i++){long long q=left[i],z=right[i];cost+=n-q+z;delta+=sign*(q+z-2*n+1+ones);ans=min(ans,cost+llabs(delta));}}cout<<ans<<'\n';
''')

add('P16943','维护最高两度数与最高度点的非邻居证据',
    '删去 u、v 的连通块数是 deg[u]+deg[v]−1−[相邻]。最高两度数决定答案最多只差一；维护最高度点的次高度非邻居，普通加叶只更新这个证据，度数并列结束时才扫描度数桶重建。',
    '树删去两点后，用剩余点数减剩余边数，得到 deg[u]+deg[v]−1−[u,v相邻]。\n\n若最高度 D 至少三点达到，其中必有不相邻一对，否则形成三角形，答案为 2D−1。只有两点达到时检查两点是否相邻。若最高度点唯一为 u，次高度为 S，最优一定包含 u：不含 u 的得分至多 2S−1，而 u 配次高度点至少 D+S−2≥2S−1。因此只需判断是否存在度数 S 且不邻接 u 的点，答案为 D+S−1 或 D+S−2。\n\n每次加叶只增加父亲度数，并新增度一节点。用链表度数桶和两个候选编号维护最高两度数。最高点 u 连续保持唯一时，若次高度不变，旧非邻居证据仍有效，只需检查新入桶的父亲或新叶；若次高度升高，新次高桶只包含本次增度的父亲，直接判断。\n\n只有从并列最高变成唯一最高时才扫描次高度桶寻找证据。此时 S=D−1，扫描至多 min(桶大小,D+1) 个点；桶大小又受树度数和限制为 O(n/(D−1))。这样的重建每个全局最大度至多一次，合计 O(n log n)。相邻关系可直接用创建时父亲数组判断，后续不会改变。',
    '总时间 O(n log n) 摊还，空间 O(n)。','两点相邻额外减一；最高度至少三点必有非邻居；只有旧节点父亲度数增加。',r'''
int n;cin>>n;vector<int>parent(n+1),degree(n+1),head(n+1),next(n+1),previous(n+1),count(n+1);head[0]=1;count[0]=1;auto insert=[&](int v,int d){degree[v]=d;previous[v]=0;next[v]=head[d];if(head[d])previous[head[d]]=v;head[d]=v;count[d]++;};auto increase=[&](int v){int d=degree[v],p=previous[v],q=next[v];if(p)next[p]=q;else head[d]=q;if(q)previous[q]=p;count[d]--;insert(v,d+1);};auto adjacent=[&](int a,int b){return parent[a]==b||parent[b]==a;};int top=1,second=0,previousUnique=0,cachedSecond=0,witness=0;string output;output.reserve(8LL*n);for(int v=2;v<=n;v++){int p;cin>>p;parent[v]=p;increase(p);insert(v,1);if(p!=top){if(degree[p]>degree[top]){second=top;top=p;}else if(p!=second&&degree[p]>degree[second])second=p;}if(!second||degree[v]>degree[second])second=v;int D=degree[top],S=degree[second],answer;if(D==S){answer=2*D-1-(count[D]==2&&adjacent(top,second));previousUnique=0;}else{if(previousUnique!=top){witness=0;for(int u=head[S];u;u=next[u])if(!adjacent(top,u)){witness=u;break;}}else if(S!=cachedSecond){witness=p!=top&&degree[p]==S&&!adjacent(top,p)?p:0;}else if(!witness){if(p!=top&&degree[p]==S&&!adjacent(top,p))witness=p;if(S==1&&!adjacent(top,v))witness=v;}answer=D+S-1-(witness==0);previousUnique=top;cachedSecond=S;}output+=to_string(answer);output+=v==n?'\n':' ';}cout<<output;
''')
