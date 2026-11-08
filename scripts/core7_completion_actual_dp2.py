from core7_completion import add
from core7_completion_actual_math import MOD

add('P1169','棋盘奇偶变换后的同色矩形',
    '将每格颜色异或行列奇偶，交替棋盘就变成全零或全一矩形。分别维护两种颜色的直方图高度，用单调栈求最大矩形，并以 min(高,宽) 求最大正方形。',
    '合法棋盘的相邻格颜色相反，异或 (i+j)%2 后，相邻格便相同。连通矩形内所有格相同，反过来也必然还原为交替棋盘，所以可以完整转化为两个同色矩形问题。\n\n扫描每一行，为零、一各维护每列向上连续相同颜色的高度。对一个高度直方图，递增栈在弹出高度 h 时确定它能延伸的最大宽度 w，贡献矩形面积 hw、正方形面积 min(h,w)²。\n\n所有最大矩形都能以其中最低柱作为限制被枚举，最大正方形也能由同一跨度容纳。行尾加入零高度哨兵清空栈，最后分别输出正方形、矩形面积。',
    '时间 O(nm)，空间 O(nm+m)。','先做行列奇偶异或；两种变换颜色都要处理；输出先正方形后矩形。',r'''
int n,m;cin>>n>>m;vector<vector<int>>a(n,vector<int>(m));for(int i=0;i<n;i++)for(int j=0;j<m;j++){cin>>a[i][j];a[i][j]^=(i+j)&1;}long long square=0,rectangle=0;for(int color=0;color<2;color++){vector<int>h(m+1);for(int i=0;i<n;i++){for(int j=0;j<m;j++)h[j]=a[i][j]==color?h[j]+1:0;vector<int>st;for(int j=0;j<=m;j++){while(!st.empty()&&h[st.back()]>h[j]){int height=h[st.back()];st.pop_back();int width=j-(st.empty()?-1:st.back())-1;rectangle=max(rectangle,1LL*height*width);long long side=min(height,width);square=max(square,side*side);}st.push_back(j);}}}cout<<square<<'\n'<<rectangle<<'\n';
''')

add('P3080','已安抚区间与当前位置两端的 DP',
    '把零位置一起排序，已访问的奶牛总形成一个包含零的区间。状态记录区间和停在左端或右端；向外扩展时，路程乘尚未安抚奶牛数就是增加的损失。',
    '沿数轴走到一个点时，会经过沿途所有奶牛，立即安抚不会变差。因此已安抚点必构成排序后连续区间，只需从当前区间向左或向右扩展一头。\n\n设区间长度为 len，其中一个是起点零，已安抚 len−1 头，仍有 n−len+1 头每分钟造成损失。向新端点移动距离 d，新增损失就是 d·(n−len+1)，无论最终访问顺序如何都应在这段移动中支付。\n\ndp[l][r][0/1] 分别记录停在左右端的最小损失，初始仅零位置为零。按区间长度递增更新，转移只有四种距离计算。全部包含后取两端状态较小值。',
    '时间 O(n²)，空间 O(n²)。','零是虚拟起点，不是奶牛；增加损失乘所有未安抚奶牛；从区间当前端点量路程。',r'''
int n;cin>>n;vector<long long>a(n+1);for(int i=0;i<n;i++)cin>>a[i];a[n]=0;sort(a.begin(),a.end());int N=n+1,start=lower_bound(a.begin(),a.end(),0)-a.begin();const long long INF=1LL<<62;vector<vector<array<long long,2>>>dp(N,vector<array<long long,2>>(N,{INF,INF}));dp[start][start]={0,0};for(int len=1;len<=N;len++)for(int l=0;l+len<=N;l++){int r=l+len-1;if(l>start||r<start)continue;long long remaining=N-len;for(int side=0;side<2;side++)if(dp[l][r][side]<INF){int pos=side?r:l;if(l)dp[l-1][r][0]=min(dp[l-1][r][0],dp[l][r][side]+(a[pos]-a[l-1])*remaining);if(r+1<N)dp[l][r+1][1]=min(dp[l][r+1][1],dp[l][r][side]+(a[r+1]-a[pos])*remaining);}}cout<<min(dp[0][n][0],dp[0][n][1])<<'\n';
''')

add('P5752','矩形切割 DP 最小化分数平方和',
    '所有块的平均分固定，所以最小方差等价于最小块分数平方和。枚举横切或竖切，并按规则让一边直接成为最终块、另一边继续分割。',
    '展开方差平方，σ²=Σx_i²/n−(总分/n)²，第二项固定。只需使 Σx_i² 最小，最后再开方。二维前缀和让任意矩形总分快速可得。\n\n设 solve(rect,k) 是矩形按原题逐次割下一块的规则分成 k 块的最小平方和。k=1 时为矩形总分平方。枚举一条完整横切或竖切，一侧立即结束为一个块，另一侧继续分 k−1 块；两个方向都要尝试。\n\n不能把任意两边分别分配多个块，因为题目限定每次只从剩余矩形割下一块。记忆化避免重复计算，面积不足 k 的状态设不可行。最终浮点运算前先用整数求最小平方和，减少精度误差。',
    '棋盘边长固定为八，状态 O(n·8⁴)，每态 O(8) 转移；空间 O(n·8⁴)。','只递归继续分一侧；平均值固定；最后按三位小数输出。',r'''
int n;cin>>n;long long pre[9][9]{};for(int i=1;i<=8;i++)for(int j=1;j<=8;j++){long long x;cin>>x;pre[i][j]=x+pre[i-1][j]+pre[i][j-1]-pre[i-1][j-1];}memset(memo,-1,sizeof memo);auto sum=[&](int a,int b,int c,int d){return pre[c][d]-pre[a-1][d]-pre[c][b-1]+pre[a-1][b-1];};const long long INF=1LL<<60;function<long long(int,int,int,int,int)>solve=[&](int k,int a,int b,int c,int d)->long long{if((c-a+1)*(d-b+1)<k)return INF;long long&ans=memo[k][a][b][c][d];if(ans>=0)return ans;if(k==1){long long s=sum(a,b,c,d);return ans=s*s;}ans=INF;for(int x=a;x<c;x++){long long s=sum(a,b,x,d),t=sum(x+1,b,c,d);ans=min({ans,s*s+solve(k-1,x+1,b,c,d),t*t+solve(k-1,a,b,x,d)});}for(int y=b;y<d;y++){long long s=sum(a,b,c,y),t=sum(a,y+1,c,d);ans=min({ans,s*s+solve(k-1,a,y+1,c,d),t*t+solve(k-1,a,b,c,y)});}return ans;};long double mean=(long double)pre[8][8]/n;long double variance=(long double)solve(n,1,1,8,8)/n-mean*mean;cout<<fixed<<setprecision(3)<<sqrtl(max(0.0L,variance))<<'\n';
''',r'''long long memo[15][9][9][9][9];''')

add('CF14E','记录高度、上升下降趋势与峰数',
    '峰比谷恰好多一意味着第一段上升、最后一段下降。先枚举上升的前两个高度，随后 DP 记录末高度、趋势和已出现峰数，最后只取下降且有 t 个峰的状态。',
    '相邻高度不能相等，所以每段只有上升或下降。上升转下降形成峰，下降转上升形成谷。二者交替出现，峰数比谷数多一当且仅当起始趋势上升、结束趋势下降。\n\n因此不用同时记录谷数。状态 dp[peaks][lastHeight][trend]，添加一个不同新高度时决定新趋势；若旧上升、新下降，峰数加一，其余不变。高度只有一到四，转移数是常数。\n\n初始两点枚举所有严格上升高度组合，峰数零。最终累加 t 峰、下降趋势的全部末高度，自动保证恰有 t−1 个谷。计数使用六十四位，全部候选至多 4·3^(n−1)。',
    '时间 O(nt·4²)，空间 O(t·4)。','相邻高度不能相等；峰在趋势翻转时计数；必须首升末降。',r'''
int n,t;cin>>n>>t;long long dp[11][4][2]{};for(int a=0;a<4;a++)for(int b=a+1;b<4;b++)dp[0][b][1]++;for(int len=2;len<n;len++){long long next[11][4][2]{};for(int p=0;p<=t;p++)for(int h=0;h<4;h++)for(int up=0;up<2;up++)for(int v=0;v<4;v++)if(v!=h){int newUp=v>h,np=p+(up&&!newUp);if(np<=t)next[np][v][newUp]+=dp[p][h][up];}memcpy(dp,next,sizeof dp);}long long ans=0;for(int h=0;h<4;h++)ans+=dp[t][h][0];cout<<ans<<'\n';
''')

add('CF362C','交换逆序端点时统计中间值域',
    '插入排序交换次数就是逆序对数。交换 i<j 且 a[i]>a[j] 会减少 1+2·count 个逆序，其中 count 是中间位置且值严格夹在两端之间的元素数。二维前缀计数使每对查询为常数时间。',
    '交换两端后，它们自身的逆序消失，减少一。中间某值 x 若在 a[j] 与 a[i] 之间，它原来与两端形成两个逆序，交换后两个都消失，减少二；若在范围外，总逆序贡献不变。数组是排列，不存在相等边界。\n\n原数组有可改善交换，最优必取逆序端点；枚举全部逆序对，最大化这个减少量，并统计达到最大值的端点对数。初始逆序数用平方枚举即可。\n\n预处理 pref[i][v] 表示前 i 个位置中≤v 的元素数，用四个前缀值求中间矩形计数。n≤5000，计数最大五千，用 unsigned short 存表约五十兆字节，避免平方表浪费内存。',
    '时间 O(n²)，空间 O(n²)。','端点和数值边界都严格排除；排列从零开始；输出剩余逆序数和交换方案数。',r'''
int n;cin>>n;vector<int>a(n);for(int&x:a)cin>>x;vector<unsigned short>pref((n+1)*n);for(int i=0;i<n;i++)for(int v=0;v<n;v++)pref[(i+1)*n+v]=pref[i*n+v]+(a[i]<=v);long long inversions=0,ways=0;int best=-1;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(a[i]>a[j]){inversions++;int high=a[i]-1,low=a[j];int inside=pref[j*n+high]-pref[(i+1)*n+high]-pref[j*n+low]+pref[(i+1)*n+low];int reduction=1+2*inside;if(reduction>best){best=reduction;ways=1;}else if(reduction==best)ways++;}cout<<inversions-best<<' '<<ways<<'\n';
''')

add('CF685B','从最大孩子子树的重心向上调整',
    '求子树大小后，若最大孩子不超过子树的一半，当前根就是重心；否则从这个大孩子的重心开始，向上移动到祖先侧大小不超过一半的位置。每个子树答案预先保存。',
    '删去 u 后，若每个孩子子树都不超过 size[u]/2，u 就满足重心定义。否则只有一个孩子 h 超过一半，重心必在 h 子树中。\n\n已知 h 子树的重心 c，它向下的各部分不超过 size[h]/2，也就不超过 size[u]/2。扩大到 u 子树后，唯一可能过大的部分是祖先侧，大小为 size[u]−size[c]。当这个值超过一半时，将 c 移到父亲。移动时原来的下方 c 部分小于一半，其它孩子也不会超过原最大孩子，所以新的唯一潜在问题仍是祖先侧。\n\n这样向上走到第一次满足条件即得到重心。后序处理全部子树，再按询问直接输出保存结点。子树可能有两个重心，任意一个都合法。',
    '预处理 O(n log n) 的保守上界，每问 O(1)，空间 O(n)。','子树大小包括自己；只沿过半孩子进入；两重心均可。',r'''
int n,q;cin>>n>>q;vector<int>parent(n),size(n,1),heavy(n,-1),center(n);vector<vector<int>>g(n);for(int i=1;i<n;i++){cin>>parent[i];parent[i]--;g[parent[i]].push_back(i);}vector<int>order={0};for(int i=0;i<n;i++)for(int u:g[order[i]])order.push_back(u);for(int i=n-1;i>=0;i--){int v=order[i];for(int u:g[v]){size[v]+=size[u];if(heavy[v]<0||size[u]>size[heavy[v]])heavy[v]=u;}int h=heavy[v];if(h<0||size[h]*2<=size[v])center[v]=v;else{int c=center[h];while((size[v]-size[c])*2>size[v])c=parent[c];center[v]=c;}}while(q--){int v;cin>>v;cout<<center[v-1]+1<<'\n';}
''',checker='subtree-centroid')

add('CF54C','首位为一的区间计数与伯努利 DP',
    '首位为一的正整数构成 [1,1]、[10,19]、[100,199]……，求它们与每个输入区间的交长得到概率。再 DP 统计恰有 j 个变量成功，累加达到百分比门槛的概率。',
    '第 i 个变量在区间中均匀选择，成功概率 p[i] 是首位一的整数数除以区间长度。枚举十的幂，取 [10^d,2·10^d−1] 与输入区间交集，最多十九段。\n\n设 dp[j] 为已处理变量中恰好 j 个首位一的概率。新变量失败贡献 dp[j](1−p)，成功贡献 dp[j−1]p。逆序更新 j，保证读到的都是旧状态。\n\n“至少 K%”等价于成功数≥ceil(NK/100)，必须向上取整；K=0 时答案一。使用 long double，最后输出足够小数位。',
    '时间 O(N²+19N)，空间 O(N)。','百分比门槛向上取整；区间两端都计数；十的幂循环避免溢出。',r'''
int n;cin>>n;vector<long double>p(n);for(int i=0;i<n;i++){long long l,r;cin>>l>>r;long long count=0;for(long long power=1;power<=r;){long long left=max(l,power),right=min((__int128)r,(__int128)power*2-1);if(left<=right)count+=right-left+1;if(power>r/10)break;power*=10;}p[i]=(long double)count/(r-l+1);}int K;cin>>K;vector<long double>dp(n+1);dp[0]=1;for(int i=0;i<n;i++)for(int j=i+1;j>=0;j--)dp[j]=dp[j]*(1-p[i])+(j?dp[j-1]*p[i]:0);int need=(n*K+99)/100;long double ans=0;for(int j=need;j<=n;j++)ans+=dp[j];cout<<fixed<<setprecision(12)<<ans<<'\n';
''')

add('CF797E','按小参数分组离线计算跳跃次数',
    '小 k 逐个倒序 DP，计算所有起点的次数；大 k 每步至少前进 k，直接模拟只需 O(n/k) 步。将小 k 的询问分组处理，只保留一份 DP 数组。',
    '位置 i 的下一跳为 i+a[i]+k，严格向右，所以固定 k 后可以从 n 到一递推 dp[i]=1+dp[next]，越界位置为零。\n\n取 B≈sqrt(n)。对出现过的 k≤B，各花 O(n) 计算全部起点；对 k>B，每步至少移动 B+1，直接模拟最多 O(n/B) 次。两部分总量平衡。\n\n先读完询问，将相同小 k 聚在一起。处理一组后即可覆盖旧 dp，无须保存 n×B 的大表。大参数的答案直接存到原询问编号，最后按输入顺序输出。',
    '时间 O(n√n+q√n)，空间 O(n+q)。','下一位置严格更大；倒序 DP；离线分组节省平方根倍内存。',r'''
int n;cin>>n;vector<int>a(n+1);for(int i=1;i<=n;i++)cin>>a[i];int q;cin>>q;int B=sqrt(n)+1;vector<vector<pair<int,int>>>small(B+1);vector<int>ans(q),dp(n+1);for(int i=0;i<q;i++){int p,k;cin>>p>>k;if(k<=B)small[k].push_back({p,i});else{int count=0;for(;p<=n;p+=a[p]+k)count++;ans[i]=count;}}for(int k=0;k<=B;k++)if(!small[k].empty()){for(int i=n;i>=1;i--){long long next=1LL*i+a[i]+k;dp[i]=1+(next<=n?dp[next]:0);}for(auto[p,id]:small[k])ans[id]=dp[p];}for(int x:ans)cout<<x<<'\n';
''')

add('CF1082E','每种源值各自维护带间隔惩罚的最大子段',
    '选择把某个值 x 变成 c 后，区间收益为 x 的个数减 c 的个数。每遇到一个 x，扣去与上次 x 之间的 c 数量，再决定延续旧段或从当前重新开始。',
    '一次加法只能把一种原值 x 变成 c，同时区间中的原 c 会被移走。因此净增加量就是区间内 #x−#c，其它值不影响收益。固定 x 后相当于 +1、−1、零序列的最大子段和。\n\n不能为每个 x 单独扫描全数组。维护全局已见 c 数 C，以及每种 x 的 bestEnding 和上次遇到它时的 C。下次遇到 x 时，间隔里 c 的惩罚为 C−lastC[x]，更新 bestEnding=max(1,bestEnding−惩罚+1)。间隔中的其它值为零，不需处理。\n\n最大净收益加上原数组全部 c 数就是答案。若保持原状最优，可以选择加零，收益下界为零。',
    '期望时间 O(n)，空间 O(n)。','区间内原 c 会减少；不同 x 的状态独立；从当前 x 重新开始的收益为一。',r'''
int n,c;cin>>n>>c;unordered_map<int,pair<int,int>>state;state.reserve(2*n+1);int countC=0,gain=0;for(int i=0;i<n;i++){int x;cin>>x;if(x==c){countC++;continue;}auto&[best,last]=state[x];best=max(1,best-(countC-last)+1);last=countC;gain=max(gain,best);}cout<<countC+gain<<'\n';
''')

add('AT_dp_t','末元素排名与前缀和优化',
    'dp[j] 表示当前排列末元素在已用数中排名 j 的方案数。加入一个新排名时，若要求上升就累加更小旧排名，下降就累加不小于新排名的旧排名；前缀和使每态常数时间。',
    '处理长度 i 的相对大小排列，下一元素最终排名 j 在零到 i 之间。把旧排列插入新排名后，旧末元素若原排名 k<j，它仍排在新元素之前；否则它被挤到新元素之后。\n\n因此符号为 < 时新 dp[j]=Σ(k<j)old[k]，符号为 > 时新 dp[j]=Σ(k≥j)old[k]。旧状态的前缀和能一次性查询这两种区间。\n\n长度一只有一个排列，初值 dp[0]=1。每步只保留上一长度，最终所有末排名相加。相对排名完整确定一到 n 的排列，不需要再乘阶乘。',
    '时间 O(n²)，空间 O(n)。','排名从零开始；下降取旧排名≥j；只维护相对大小即可。',r'''
int n;cin>>n;string s;if(n>1)cin>>s;vector<long long>dp(1,1);for(int len=1;len<n;len++){vector<long long>prefix(len+1),next(len+1);for(int j=0;j<len;j++)prefix[j+1]=(prefix[j]+dp[j])%MOD;for(int j=0;j<=len;j++)next[j]=s[len-1]=='<'?prefix[j]:(prefix[len]-prefix[j]+MOD)%MOD;dp.swap(next);}long long ans=0;for(auto x:dp)ans=(ans+x)%MOD;cout<<ans<<'\n';
''',MOD)

add('CF771C','总距离加按余数补齐的代价',
    '跳跃数为 ceil(dist/k)。先用边贡献统计所有点对距离，再用子树 DP 统计距离模 k 时需补到下一个 k 倍数的数量，最后总和除以 k。',
    'ceil(d/k)=(d+(k−d%k)%k)/k。第一项所有距离之和可按边计算：一条边切开大小为 s、n−s 两部分，恰有 s(n−s) 个无序点对使用它。\n\n第二项只与距离余数有关。cnt[u][r] 记录 u 子树中距 u 余数为 r 的点数。合并孩子时，孩子的余数先加一，和已有分支余数 r 配对，路径经过 u，所以总余数是两者相加模 k；按所需补齐量乘点对数量累计。\n\n每对点在其 LCA 合并两个分支时被统计一次。当前点自身放在余数零状态，覆盖一个端点就是祖先的情形。k≤5，平方余数枚举很小。',
    '时间 O(nk²)，空间 O(nk)。','点对无序，只合并不同已处理分支；余数零无需补；最终总和整除 k。',r'''
int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}vector<int>parent(n,-1),order={0},size(n,1);parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(parent[u]<0){parent[u]=order[i];order.push_back(u);}vector<array<long long,5>>cnt(n);long long distanceSum=0,padding=0;for(int i=n-1;i>=0;i--){int v=order[i];cnt[v][0]=1;for(int u:g[v])if(parent[u]==v){for(int a=0;a<k;a++)for(int b=0;b<k;b++)padding+=cnt[v][a]*cnt[u][b]*((k-(a+b+1)%k)%k);for(int b=0;b<k;b++)cnt[v][(b+1)%k]+=cnt[u][b];size[v]+=size[u];}if(v)distanceSum+=1LL*size[v]*(n-size[v]);}cout<<(distanceSum+padding)/k<<'\n';
''')

add('CF1265E','整段重来使期望递推除以成功概率',
    '设 E[i] 为从头通过前 i 面镜子的期望次数。到第 i 面前平均已经花 E[i−1] 次，再尝试一次；失败就整段重来，因此 E[i]=(E[i−1]+1)/p[i]。',
    '把“到达并尝试第 i 面”看成一次完整尝试周期，周期成本期望为 E[i−1]+1。成功概率 p[i]，失败后返回开头，恢复为同一个问题，所以 E[i]=E[i−1]+1+(1−p[i])E[i]。移项便得到递推。\n\n题目用百分整数输入概率，p[i]=a[i]/100，在模质数下递推为 (E[i−1]+1)·100·inv(a[i])。概率非零保证逆元存在。\n\n必须先给前段期望加一再整体除以成功率，不能只给当前一次尝试乘逆概率。',
    '时间 O(n log MOD)，空间 O(1)。','失败回到第一面；百分数转为 100 的因子；分母非零。',r'''
int n;cin>>n;const long long P=998244353;auto power=[&](long long a,long long b){long long r=1;for(;b;b>>=1,a=a*a%P)if(b&1)r=r*a%P;return r;};long long E=0;for(int i=0;i<n;i++){long long p;cin>>p;E=(E+1)*100%P*power(p,P-2)%P;}cout<<E<<'\n';
''')

add('P3120','全部前驱减同色前驱的二维偏序计数',
    '按行扫描，用全局树状数组统计更早行、较小列的所有路径数，再减去当前颜色的同类统计。同一行先计算完再一起加入，保证行坐标严格增加。',
    'dp[i][j] 是到达该格的方案数，合法前驱必须行、列都更小且颜色不同。因此它等于左上矩形全部 dp 之和减同色 dp 之和。\n\n用扫描行处理第一维，全局 Fenwick 按列维护所有早先行的贡献。每种颜色另有一棵 Fenwick，但只为该颜色出现的列离散化分配空间，全部颜色的节点总数不超过网格大小。\n\n当前行每格只查询列 j−1 之前，计算后暂存；整行全部算完再加入结构，这样不会把同一行当作前驱。起点单独设一，其它首行首列自然为零。',
    '时间 O(RC log C)，空间 O(RC+K)。','行列必须都严格增加；同色贡献相减后规范化；同一行延迟更新。',r'''
int R,C,K;cin>>R>>C>>K;vector<vector<int>>a(R,vector<int>(C)),columns(K+1);for(int i=0;i<R;i++)for(int j=0;j<C;j++){cin>>a[i][j];columns[a[i][j]].push_back(j+1);}vector<Bit>colored;colored.reserve(K+1);for(int c=0;c<=K;c++){auto&v=columns[c];sort(v.begin(),v.end());v.erase(unique(v.begin(),v.end()),v.end());colored.emplace_back(v.size());}Bit all(C);vector<int>row(C);int ans=0;for(int i=0;i<R;i++){for(int j=0;j<C;j++){int c=a[i][j],r=lower_bound(columns[c].begin(),columns[c].end(),j+1)-columns[c].begin();row[j]=(all.sum(j)-colored[c].sum(r)+1000000007)%1000000007;if(i==0&&j==0)row[j]=1;}for(int j=0;j<C;j++){int c=a[i][j],r=lower_bound(columns[c].begin(),columns[c].end(),j+1)-columns[c].begin()+1;all.add(j+1,row[j]);colored[c].add(r,row[j]);}ans=row[C-1];}cout<<ans<<'\n';
''',r'''
struct Bit{vector<int>t;Bit(int n):t(n+1){}void add(int x,int v){for(;x<(int)t.size();x+=x&-x){t[x]+=v;if(t[x]>=1000000007)t[x]-=1000000007;}}int sum(int x)const{int r=0;for(;x;x-=x&-x){r+=t[x];if(r>=1000000007)r-=1000000007;}return r;}};
''')

add('P5694','深度上界 DP，按第一对括号唯一分解',
    '先统计深度不超过 D 的串，再减去不超过 D−1 的串。一个非空表达式唯一拆为第一对完整外括号、其内部表达式、以及后续表达式，并按括号种类限制内部可用类型。',
    '令 F[d][a][b][c] 为深度≤d，三类括号对数分别为 a、b、c 的 SS 串数。空串对任意上界都有一种，d=0 的其它状态为零。\n\n非空串第一字符必是某种左括号，它匹配的右括号位置唯一，将全串分成“外括号包住的内部 A”与“后缀 B”。内部深度≤d−1，后缀深度≤d。若外层是大括号，内部可使用三类；若是中括号，内部不能有大括号；若是小括号，内部只能有小括号。枚举内部各类对数，其余对数自动留给后缀，乘两个状态数。\n\n按 d 递增、各括号对数递增计算。后缀总对数更少，所以同一深度的依赖已经就绪。第一对分解唯一，避免按任意拼接点反复计数。最后 F[D]−F[D−1] 得到深度恰好 D，模 11380。',
    '时间 O(D·(L1+1)²(L2+1)²(L3+1)²)，空间 O(D·(L1+1)(L2+1)(L3+1))。','统计上界后作差；第一完整括号唯一拆分；中小括号对内部类型有限制。',r'''
int A,B,C,D;cin>>A>>B>>C>>D;const int P=11380;int S=(A+1)*(B+1)*(C+1);vector<vector<int>>f(D+1,vector<int>(S));auto id=[&](int a,int b,int c){return (a*(B+1)+b)*(C+1)+c;};for(int d=0;d<=D;d++)f[d][0]=1;for(int d=1;d<=D;d++)for(int a=0;a<=A;a++)for(int b=0;b<=B;b++)for(int c=0;c<=C;c++){if(!a&&!b&&!c)continue;long long ans=0;if(a)for(int x=0;x<a;x++)for(int y=0;y<=b;y++)for(int z=0;z<=c;z++)ans=(ans+1LL*f[d-1][id(x,y,z)]*f[d][id(a-1-x,b-y,c-z)])%P;if(b)for(int y=0;y<b;y++)for(int z=0;z<=c;z++)ans=(ans+1LL*f[d-1][id(0,y,z)]*f[d][id(a,b-1-y,c-z)])%P;if(c)for(int z=0;z<c;z++)ans=(ans+1LL*f[d-1][id(0,0,z)]*f[d][id(a,b,c-1-z)])%P;f[d][id(a,b,c)]=ans;}int ans=f[D][id(A,B,C)];if(D)ans=(ans-f[D-1][id(A,B,C)]+P)%P;cout<<ans<<'\n';
''')

add('UVA1222','森林背包：买下整棵子树或合并孩子',
    '贿赂一个国家会获得其全部后代的票。树上 DP 维护各票数的最低费用：不贿赂当前国就合并孩子，贿赂则直接用当前价格覆盖整棵子树。加虚拟根合并森林。',
    '统属关系无环且每国至多一个上级，因此形成森林。为所有根增加虚拟父亲零，虚拟根不能贿赂，也不提供选票。原题关系可核对[原题 PDF](https://onlinejudge.org/external/12/1222.pdf)。\n\n对国家 u，先把孩子子树的“恰好取得 j 票的最小费用”用背包卷积合并；这表示不直接贿赂 u，只从后代购买。随后将整棵 u 子树的票数状态与 cost[u] 取较小值，表示贿赂 u 后无需再贿赂任何后代。\n\n这两类方案覆盖所有最优选择：一旦贿赂 u，重复购买后代不会增加票数；若不贿赂 u，孩子之间完全独立。最终在虚拟根上对票数≥m 的状态取最小。名字可能先在他国列表中出现，用映射统一编号，不能只按出现行号直接引用。',
    '时间 O(n²)，空间 O(n²)。','要求至少 m 票；虚拟根不计票且不能购买；国家名称按整行解析。',r'''
string line;while(getline(cin,line)){if(line=="#")break;if(line.empty())continue;istringstream header(line);int n,m;header>>n>>m;map<string,int>ids;int used=0;auto get=[&](const string&s){auto it=ids.find(s);if(it!=ids.end())return it->second;return ids[s]=++used;};vector<vector<int>>g(n+1);vector<int>parent(n+1),size(n+1);vector<long long>cost(n+1);for(int i=0;i<n;i++){getline(cin,line);istringstream in(line);string name;long long value;in>>name>>value;int u=get(name);cost[u]=value;while(in>>name){int v=get(name);g[u].push_back(v);parent[v]=u;}}for(int i=1;i<=n;i++)if(!parent[i])g[0].push_back(i);vector<int>order={0};for(int i=0;i<(int)order.size();i++)for(int u:g[order[i]])order.push_back(u);const long long INF=1LL<<60;vector<vector<long long>>dp(n+1);for(int i=n;i>=0;i--){int v=order[i];dp[v]={0};for(int u:g[v]){vector<long long>next(size[v]+size[u]+1,INF);for(int a=0;a<=size[v];a++)for(int b=0;b<=size[u];b++)next[a+b]=min(next[a+b],dp[v][a]+dp[u][b]);size[v]+=size[u];dp[v].swap(next);}if(v){size[v]++;dp[v].resize(size[v]+1,INF);dp[v][size[v]]=min(dp[v][size[v]],cost[v]);}}cout<<*min_element(dp[0].begin()+m,dp[0].end())<<'\n';}
''')

add('P1858','每个容量保留前 K 个有重数的价值',
    '每个容量维护前 K 大方案价值，归并不取与取当前物品的两份有序列表。相同价值、不同清单分别保留。这里求至少存在 K 种装满方案时的最优和；不足 K 种的输出原题未规定，详细题解明确标注。',
    '把方案按是否包含当前物品分成两类。两类清单互不相同，内部仍按价值降序，故可以线性归并出整体前 K 项。只保留前 K 不会丢失未来最优：同一容量的较差旧方案，后续加相同物品集合仍不会超过已保留的 K 个方案。\n\n容量必须倒序，确保每种物品只取一次。初始只有容量零有一个价值零的空方案，其它容量没有方案，不能用零冒充可达状态。价值相等时仍保留两项，因为题目区分物品清单。\n\n原题没有定义“凑满容量的不同清单少于 K 个”时应输出什么。本实现对题目目标可行的输入求完整最优和；不足 K 时不臆造零价值方案或约定答案，相关题面边界单独保留在验证记录中。',
    '时间 O(NVK)，空间 O(VK)。','恰好装满；容量倒序；等值不同清单不去重；不存在的方案不用零填充。',r'''
int K,V,N;cin>>K>>V>>N;vector<vector<long long>>dp(V+1);dp[0]={0};for(int i=0;i<N;i++){int w;long long value;cin>>w>>value;for(int capacity=V;capacity>=w;capacity--){const auto&left=dp[capacity];const auto&right=dp[capacity-w];vector<long long>next;int a=0,b=0;while((int)next.size()<K&&(a<(int)left.size()||b<(int)right.size())){if(b==(int)right.size()||(a<(int)left.size()&&left[a]>=right[b]+value))next.push_back(left[a++]);else next.push_back(right[b++]+value);}dp[capacity].swap(next);}}if((int)dp[V].size()<K)return 0;cout<<accumulate(dp[V].begin(),dp[V].end(),0LL)<<'\n';
''')
