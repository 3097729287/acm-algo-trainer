from core7_completion import add, FENWICK
from core7_completion_actual_math import MOD

add('P6568','长度为 k+1 的最大区间和',
    '要把连续 s 个水壶的水集中到最右侧，至少且只需 s−1 次倾倒。最多 k 次操作能汇集最多 k+1 个连续水壶，非负水量下取长度恰为 k+1 的最大窗口和。',
    '水只能向右流。最终选中某个水壶时，能流入的初始水壶一定来自它左侧的一个连续区间；要跨过区间中每条边，至少执行一次对应倾倒。区间长度 s 需要至少 s−1 次。\n\n从左到右把水逐次倒向下一壶，恰好 s−1 次即可汇集整个区间，所以这个下界可达。由于 A 非负，较短区间可以扩充到 k+1 长度而不变差，问题变为定长最大区间和。\n\n先算首个窗口，每次向右移动时减去离开的数、加上新数，维护最大值。',
    '时间 O(n)，空间 O(n)。','操作次数比壶数少一；只能向右汇集；k=0 时取最大单项。',r'''
int n,k;cin>>n>>k;vector<long long>a(n);for(auto&x:a)cin>>x;long long sum=accumulate(a.begin(),a.begin()+k+1,0LL),ans=sum;for(int r=k+1;r<n;r++){sum+=a[r]-a[r-k-1];ans=max(ans,sum);}cout<<ans<<'\n';
''')

add('P13278','只累计自己首次死亡之前的攻击',
    '先找敌方攻击第一次累计达到 m 的时刻。在它之前，我方原始伤害为 D、攻击次数为 c。道具 x 能赢当且仅当 D+cx≥m；不能赢时，存在死亡时刻则输，否则平局。',
    '道具只增加我方伤害，不影响我方的死亡时刻，因此可以先只看负数攻击，确定敌人最早什么时候会打败我。\n\n在这一时刻之前的正数攻击，总原始伤害 D、次数 c 都固定。加成后敌人受到的累计伤害为 D+cx，且随战斗推进单调不减。所以它达到 m，当且仅当某次我方攻击已经提前击败敌人。敌方造成死亡的那一次是负数攻击，不存在双方同时死亡的平局问题。\n\n如果所有负数攻击都不致死，最后仍未击败敌人就为 Tie；否则为 No。预处理之后每个道具只需一次乘加判断。',
    '时间 O(n+q)，空间 O(1)。','死亡之后的攻击不再累计；负数攻击没有加成；总伤害使用 long long。',r'''
int n,q;long long m;cin>>n>>m>>q;long long taken=0,damage=0,count=0;bool dead=false;for(int i=0;i<n;i++){long long a;cin>>a;if(dead)continue;if(a<0){taken-=a;if(taken>=m)dead=true;}else{damage+=a;count++;}}while(q--){long long x;cin>>x;cout<<(damage+count*x>=m?"Yes":dead?"No":"Tie")<<'\n';}
''')

add('P11965','前缀字母奇偶状态相同即能消除',
    '任意两个相同字符都可以删除，所以子串能被清空当且仅当每种字母出现偶数次。用二十六位掩码记录前缀奇偶，统计相同掩码的前缀对。',
    '一次删除让同一字母出现次数减少二，不改变奇偶性，因此每个字母偶数次是必要条件；每种字母自行两两删除又证明它充分。题目没有要求被删除字符相邻。\n\n设前缀状态 mask 的第 c 位为字母 c 出现次数的奇偶。子串 l..r 的状态是 prefix[r] xor prefix[l−1]，为零等价于两个前缀状态相同。\n\n初始空前缀状态零出现一次。每读一个字母就翻转对应位，将之前相同状态的次数加到答案，再将当前状态次数加一。答案最多 n(n+1)/2，使用 long long。',
    '平均时间 O(n)，空间 O(n)。','删除字符不要求相邻；空前缀要预先加入；查询计数后再增加当前频次。',r'''
int n;string s;cin>>n>>s;unordered_map<int,long long>cnt;cnt.reserve(2*n+1);cnt[0]=1;int mask=0;long long ans=0;for(char c:s){mask^=1<<(c-'a');ans+=cnt[mask];cnt[mask]++;}cout<<ans<<'\n';
''')

add('P14253','最大前缀和频次减一',
    '子段内的一个前缀和为零，等价于原数组两个前缀和相等。选择某个前缀和值第一次出现之后作为起点，就能把它所有后续出现计入，因此答案是全部前缀和的最大频次减一。',
    '令 S[0]=0、S[i]=a1+…+ai。对起点 l，子段的零前缀恰好对应 S[j]=S[l−1] 的后续位置 j。固定 l 后，延长右端不会减少零的个数，因此可以一直取到 n。\n\n若某个前缀和值共出现 f 次，从它第一次出现的位置之后开始，恰好能得到 f−1 个零前缀；其它起点不可能得到更多。对所有前缀和值取最大频次即可，S[0] 也必须计入。\n\n代码使用带随机混合的整数哈希，避免简单整型哈希在特殊构造输入上退化。前缀和可能达到万亿，使用 long long。',
    '每组期望时间 O(n)，空间 O(n)。','包含 S[0]=0；答案是频次减一；每组重新清空。',r'''
int T;cin>>T;while(T--){int n;cin>>n;unordered_map<long long,int,Hash>cnt;cnt.reserve(2*n+1);cnt[0]=1;long long sum=0;int ans=0;for(int i=0;i<n;i++){long long x;cin>>x;sum+=x;ans=max(ans,++cnt[sum]-1);}cout<<ans<<'\n';}
''',r'''
struct Hash{static uint64_t mix(uint64_t x){x+=0x9e3779b97f4a7c15ULL;x=(x^(x>>30))*0xbf58476d1ce4e5b9ULL;x=(x^(x>>27))*0x94d049bb133111ebULL;return x^(x>>31);}size_t operator()(long long x)const{static const uint64_t seed=chrono::steady_clock::now().time_since_epoch().count();return mix(x+seed);}};
''')

add('P5686','按右端点展开两个前缀和的乘积',
    '设前缀和为 A、B。固定右端 r，所有左端贡献为 rArBr−ArΣBl−BrΣAl+ΣAlBl，其中 l 从零到 r−1。维护这三个前缀统计量即可线性求和。',
    '区间和积为 (A[r]−A[l−1])(B[r]−B[l−1])。将前一个前缀下标记为 j，并展开乘积：ArBr−ArBj−BrAj+AjBj。\n\n固定 r 时，j 有 r 个取值零到 r−1，因此第一项累加为 rArBr，其余三项只需要之前 A 的和、B 的和、A·B 的和。计算本次贡献后再把当前前缀加入统计，避免把空区间混入。\n\n输入先给完整 a 再给 b，可先存 A 前缀，读取 b 时递推 B 并累计答案。每一步取模，负项统一加模数规范化。',
    '时间 O(n)，空间 O(n)。','前缀零也在历史中；先计贡献再插入；乘积及时取模。',r'''
int n;cin>>n;vector<long long>A(n+1);for(int i=1;i<=n;i++){long long x;cin>>x;A[i]=(A[i-1]+x)%MOD;}long long B=0,sumA=0,sumB=0,sumAB=0,ans=0;for(int r=1;r<=n;r++){long long x;cin>>x;B=(B+x)%MOD;long long term=(r*A[r]%MOD*B-A[r]*sumB%MOD-B*sumA%MOD+sumAB)%MOD;ans=(ans+term+2*MOD)%MOD;sumA=(sumA+A[r])%MOD;sumB=(sumB+B)%MOD;sumAB=(sumAB+A[r]*B)%MOD;}cout<<ans<<'\n';
''',MOD)

add('P1314','二分单调检验值并检查分界两侧',
    '阈值 W 增大时，每个区间的合格数量与价值和都不增，检验值单调不增。每次用两组前缀和计算检验值，二分跨过 s 的位置，并保留搜索中最小差值。',
    '固定 W 后，令 count 前缀统计 w≥W 的矿石个数，sum 前缀统计它们的价值和。一个区间的检验值就是两段前缀差的乘积，因此一次评估为 O(n+m)。\n\nW 增大只会移走一些正价值矿石，个数与和都不会增，所以 y(W) 单调不增。若 y>s，就需要增大 W；若 y<s，就需要减小 W。在搜索过程中更新最小绝对差，最后必覆盖跨越 s 的两个相邻阈值；阶梯函数的其它值不可能更接近。\n\n搜索范围包括 maxWeight+1，它使所有区间检验值为零。累加检验值可能远超六十四位，使用 __int128；答案初始 s，因为全空方案已保证差值不超过 s。',
    '时间 O((n+m) log max w)，空间 O(n+m)。','比较的是总检验值；区间可以重复；中间乘积和总和用 __int128。',r'''
int n,m;long long target;cin>>n>>m>>target;vector<int>w(n+1),v(n+1);int maximum=0;for(int i=1;i<=n;i++){cin>>w[i]>>v[i];maximum=max(maximum,w[i]);}vector<pair<int,int>>ranges(m);for(auto&[l,r]:ranges)cin>>l>>r;vector<long long>cnt(n+1),sum(n+1);auto value=[&](int W){for(int i=1;i<=n;i++){bool take=w[i]>=W;cnt[i]=cnt[i-1]+take;sum[i]=sum[i-1]+(take?v[i]:0);}__int128 y=0;for(auto[l,r]:ranges)y+=(__int128)(cnt[r]-cnt[l-1])*(sum[r]-sum[l-1]);return y;};long long ans=target;int lo=0,hi=maximum+1;while(lo<=hi){int mid=lo+(hi-lo)/2;__int128 y=value(mid),diff=y-target;if(diff<0)diff=-diff;if(diff<ans)ans=diff;if(y>target)lo=mid+1;else hi=mid-1;}cout<<ans<<'\n';
''')

add('P1259','固定四对棋子的收尾与规模递减',
    'n>4 时，把中间的白黑一对移到末尾空位，再用右端两黑补上空位，就留下 n−1 对的同类问题，末尾多一对白黑。递归至四对后使用五步固定收尾。',
    '将棋子按一开始的白区、黑区记为 o^n*^n--。先把第 n、n+1 位的 o* 移到末尾空位，再把第 2n−1、2n 位的 ** 移到新空位，可得到 o^(n−1)*^(n−1)--o*。已经完成的末尾 o* 不再移动，前面恰好缩成 n−1 的原问题。\n\n当 n=4，依次得到：\n\n```text\noooo****--\nooo--***o*\nooo*o**--*\no--*o**oo*\no*o*o*--o*\n--o*o*o*o*\n```\n\n每步都移动两个相邻棋子到连续空位，保持两者顺序且跨过其它棋子。代码统一用交换两格来执行，并在每次操作后输出完整棋盘，包括已经处理好的后缀。',
    '共有 O(n) 次移动，输出长度 O(n)，总时间 O(n²)，空间 O(n)。','先打印初始状态；移动一对的左右顺序不变；递归只处理前缀。',r'''
int n;cin>>n;string a(n,'o');a+=string(n,'*');a+="--";cout<<a<<'\n';auto move=[&](int from,int to){from--;to--;swap(a[from],a[to]);swap(a[from+1],a[to+1]);cout<<a<<'\n';};function<void(int)>solve=[&](int k){if(k==4){move(4,9);move(8,4);move(2,8);move(7,2);move(1,7);return;}move(k,2*k+1);move(2*k-1,k);solve(k-1);};solve(n);
''')

add('P2163','矩形拆四个前缀，横坐标扫描',
    '将闭矩形计数拆为四个左下无穷前缀。按横坐标排序查询事件和树木，扫描时用树状数组维护已加入点的纵坐标数量，按符号累加答案。',
    '记 F(x,y) 为横坐标≤x、纵坐标≤y 的点数，则闭矩形答案为 F(c,d)−F(a−1,d)−F(c,b−1)+F(a−1,b−1)。减一处理整数边界，不会漏算边上的点。\n\n把所有四倍查询按 x 排序。处理事件前，将横坐标≤x 的点全部加入树状数组；树状数组按离散化纵坐标存频次，upper_bound(y) 给出需查询的前缀长度。重合树木会各加一次，正确保留重数。\n\n只有点的纵坐标需要离散化，查询纵坐标通过二分转换；即使没有树木，也能自然返回零。按原查询编号累加，最后依输入顺序输出。',
    '时间 O((n+m) log(n+m))，空间 O(n+m)。','闭区间使用 a−1、b−1；同横坐标的点先加入；重复点分别计数。',r'''
int n,m;cin>>n>>m;vector<pair<int,int>>points(n);vector<int>ys;for(auto&[x,y]:points){cin>>x>>y;ys.push_back(y);}sort(points.begin(),points.end());sort(ys.begin(),ys.end());ys.erase(unique(ys.begin(),ys.end()),ys.end());struct E{int x,y,id,sign;};vector<E>events;for(int i=0;i<m;i++){int a,b,c,d;cin>>a>>b>>c>>d;events.push_back({c,d,i,1});events.push_back({a-1,d,i,-1});events.push_back({c,b-1,i,-1});events.push_back({a-1,b-1,i,1});}sort(events.begin(),events.end(),[](E a,E b){return a.x<b.x;});Fenwick bit(ys.size());vector<long long>ans(m);int p=0;for(auto e:events){while(p<n&&points[p].first<=e.x){int r=lower_bound(ys.begin(),ys.end(),points[p].second)-ys.begin()+1;bit.add(r,1);p++;}int r=upper_bound(ys.begin(),ys.end(),e.y)-ys.begin();ans[e.id]+=e.sign*bit.sum(r);}for(auto x:ans)cout<<x<<'\n';
''',FENWICK)

add('P1854','按花束数和花瓶前缀 DP 并回溯',
    'dp[i][j] 表示前 i 束花放进前 j 个花瓶的最大价值。第 j 瓶可以空着，也可以放第 i 束花。记录取舍后从 dp[F][V] 回溯方案。',
    '由于花束必须保持顺序，第 j 个花瓶若被使用，它只能承接当前最后一束花 i，前 i−1 束必须放在前 j−1 瓶中。因此 dp[i][j]=max(dp[i][j−1],dp[i−1][j−1]+a[i][j])。\n\n初始 dp[0][j]=0，i>j 等不可能状态设为负无穷。所有花都必须放，不能把负价值状态误初始化成零。\n\n记录每次是否使用当前花瓶，回溯时若使用就保存 j 并让 i、j 同时减一，否则只减 j。回溯结果逆序输出，恰好得到递增花瓶下标；相同最大值可以选择任意一个方案。',
    '时间 O(FV)，空间 O(FV)。','必须放完所有花；价值可能为负；输出方案也需核对最优值。',r'''
int F,V;cin>>F>>V;vector<vector<int>>a(F+1,vector<int>(V+1));for(int i=1;i<=F;i++)for(int j=1;j<=V;j++)cin>>a[i][j];const int NEG=-1000000000;vector<vector<int>>dp(F+1,vector<int>(V+1,NEG));vector<vector<char>>take(F+1,vector<char>(V+1));for(int j=0;j<=V;j++)dp[0][j]=0;for(int i=1;i<=F;i++)for(int j=1;j<=V;j++){dp[i][j]=dp[i][j-1];if(dp[i-1][j-1]!=NEG&&dp[i-1][j-1]+a[i][j]>dp[i][j]){dp[i][j]=dp[i-1][j-1]+a[i][j];take[i][j]=1;}}cout<<dp[F][V]<<'\n';vector<int>path;for(int i=F,j=V;i;){if(take[i][j]){path.push_back(j);i--;}j--;}reverse(path.begin(),path.end());for(int i=0;i<F;i++)cout<<path[i]<<(i+1==F?'\n':' ');
''',checker='flower-arrangement')

add('P2858','两端出售的区间动态规划',
    '剩余区间长度确定今天是第几天。每次只能卖左端或右端，取两种选择的较大收益。按区间长度递增计算，可压缩为一维。',
    '设 dp[l][r] 是只剩区间 l..r 时还能得到的最大收益。已经卖掉 n−(r−l+1) 个，所以今天是 day=n−长度+1。转移取 a[l]·day+dp[l+1][r] 与 a[r]·day+dp[l][r−1] 的较大值。\n\n单个点最后在第 n 天卖出，初值为 a[i]n。按长度从二到 n 枚举，左右端选择正好覆盖所有合法出售次序。\n\n一维 dp[l] 保存上一长度的结果。对固定长度从左向右更新，dp[l+1] 尚未改变，dp[l] 也仍是旧值，因此两项都能正确读取。',
    '时间 O(n²)，空间 O(n)。','年龄从一开始增加；单点是在第 n 天卖；一维左端必须递增枚举。',r'''
int n;cin>>n;vector<long long>a(n),dp(n);for(int i=0;i<n;i++){cin>>a[i];dp[i]=a[i]*n;}for(int len=2;len<=n;len++){long long day=n-len+1;for(int l=0;l+len<=n;l++){int r=l+len-1;dp[l]=max(a[l]*day+dp[l+1],a[r]*day+dp[l]);}}cout<<dp[0]<<'\n';
''')

add('P14075','无重复子段最长二十六，枚举最后一段',
    '合法子串不含重复小写字母，长度最多二十六。令 dp[i] 为前 i 字符的最大划分价值，向左枚举不重复的最后一段，更新 dp[i]=max(dp[j]+a[i−j])。',
    '任意最优划分都有最后一段。若最后一段是 j..i，前面必须采用前 j−1 字符的最优划分，否则可以替换使总价值更高。因此枚举所有合法最后段即可得到完备转移。\n\n从 i 向左扫描，用二十六位 mask 记录已经出现的字母；遇到重复就停止，更长的段必然也含重复。最多查看二十六个字符，时间不再是平方。\n\n价值并不保证随长度增长，不能贪心尽量切长或尽量切短。动态规划会同时比较全部可能长度，答案使用六十四位。',
    '时间 O(26n)，空间 O(n)。','长度价值无单调性；重复时立即停止；答案可超过三十二位。',r'''
int n;string s;cin>>n>>s;vector<long long>a(n+1),dp(n+1);for(int i=1;i<=n;i++)cin>>a[i];for(int i=1;i<=n;i++){int mask=0;for(int j=i;j>=1;j--){int bit=1<<(s[j-1]-'a');if(mask&bit)break;mask|=bit;dp[i]=max(dp[i],dp[j-1]+a[i-j+1]);}}cout<<dp[n]<<'\n';
''')

add('P1043','断环枚举起点，分组 DP 同时求最小最大',
    '复制一份环形数组，枚举长度 n 的线性窗口。每个窗口按组数和前缀长度 DP，枚举最后一组起点，以该组和模十后的值相乘，分别维护最小值和最大值。',
    '任意环形划分都可以从某个分组边界切开变成线性划分；枚举全部 n 个起点就不会漏掉最优方案。复制数组并做前缀和，任意一组的值可常数时间计算。\n\n令 low[g][i]、high[g][i] 为前 i 个数恰分 g 个非空组的最小、最大乘积。枚举前 g−1 组结束位置 j，最后一组值 v 是区间和对十的非负余数，再分别更新 low[g−1][j]·v 与 high[g−1][j]·v。\n\nv 始终非负，所以乘积最小值只需前态最小值、最大值只需最大值。初始零组零元素乘积为一，不可能状态单独标记。最终在所有起点的结果中取最小与最大。',
    '时间 O(mn³)，空间 O(mn)。','每组非空；负数取模要加十；零组的空乘积是一。',r'''
int n,m;cin>>n>>m;vector<long long>pre(2*n+1),a(n);for(auto&x:a)cin>>x;for(int i=1;i<=2*n;i++)pre[i]=pre[i-1]+a[(i-1)%n];long long answerMin=LLONG_MAX,answerMax=0;for(int start=0;start<n;start++){const long long INF=LLONG_MAX/4;vector<vector<long long>>lo(m+1,vector<long long>(n+1,INF)),hi(m+1,vector<long long>(n+1,-1));lo[0][0]=hi[0][0]=1;for(int g=1;g<=m;g++)for(int i=g;i<=n;i++)for(int j=g-1;j<i;j++)if(hi[g-1][j]>=0){long long v=((pre[start+i]-pre[start+j])%10+10)%10;lo[g][i]=min(lo[g][i],lo[g-1][j]*v);hi[g][i]=max(hi[g][i],hi[g-1][j]*v);}answerMin=min(answerMin,lo[m][n]);answerMax=max(answerMax,hi[m][n]);}cout<<answerMin<<'\n'<<answerMax<<'\n';
''')

add('P10725','维护向下最远的黑点与白点',
    '每个点分别记录子树内到黑点、白点的最长向下距离。合并孩子时，把已有白分支与孩子黑分支、已有黑分支与孩子白分支相接，更新答案。',
    '任意一条树路径有唯一最高点。只要在这个点处理连接两条不同分支的路径，就能覆盖所有候选。\n\n令 down[u][c] 是 u 到子树中颜色 c 的最远距离，不存在则为负无穷。当前点自身给对应颜色距离零。逐个合并孩子 v：用 down[u][0]+down[v][1]+1 和 down[u][1]+down[v][0]+1 更新答案，再将孩子距离加一并入 down[u]。\n\n必须先计算跨分支贡献再合并，避免把同一个孩子中的两条路线错误拼成经过 u 的路径。孩子内部的最优路径已经在处理孩子时计算。按迭代遍历顺序逆序处理，可避免长链递归溢出。',
    '时间 O(n)，空间 O(n)。','两端颜色不同；距离按边数；不存在颜色用负无穷。',r'''
int n;cin>>n;vector<int>a(n);for(int&x:a)cin>>x;vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),order={0};parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(parent[u]<0){parent[u]=order[i];order.push_back(u);}const int NEG=-1000000000;vector<array<int,2>>down(n,{NEG,NEG});int ans=0;for(int i=n-1;i>=0;i--){int v=order[i];down[v][a[v]]=0;for(int u:g[v])if(parent[u]==v){ans=max({ans,down[v][0]+down[u][1]+1,down[v][1]+down[u][0]+1});for(int c=0;c<2;c++)down[v][c]=max(down[v][c],down[u][c]+1);}}cout<<ans<<'\n';
''')

add('CF1101D','按公共质因子合并树上最长链',
    '路径 gcd 大于一等价于所有点含某个共同质因子。每个点只为自己的不同质因子维护最长向下链，合并相同质因子的两条分支，得到答案。',
    '合法路径至少存在一个质因子 p，使路径上所有值均被 p 整除。反过来，只要这个条件成立，路径 gcd 就至少为 p。\n\n为每个点分解出不同质因子列表，令 down[u][p] 为从 u 向子树延伸且全部被 p 整除的最长链，长度按顶点数。初始化为一，合并孩子时只有双方都含 p 才能连接；先以当前链长加孩子链长更新跨分支答案，再将当前链长更新为孩子链长加一。\n\n一个不超过二十万的数不同质因子数量很小，直接双重遍历两个短列表即可。值为一的点没有任何状态，不能出现在合法路径里；若全部为一，答案为零。',
    '设每数不同质因子个数最多为 F，时间 O(V+nF²)，空间 O(V+nF)。','链长按顶点计数；一没有质因子；同质因子才能拼接。',r'''
int n;cin>>n;vector<int>a(n);int V=1;for(int&x:a){cin>>x;V=max(V,x);}vector<int>spf(V+1);for(int p=2;p<=V;p++)if(!spf[p])for(int j=p;j<=V;j+=p)if(!spf[j])spf[j]=p;vector<vector<int>>f(n),dp(n);for(int i=0;i<n;i++){int x=a[i];while(x>1){int p=spf[x];f[i].push_back(p);while(x%p==0)x/=p;}dp[i].assign(f[i].size(),1);}vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}vector<int>parent(n,-1),order={0};parent[0]=0;for(int i=0;i<n;i++)for(int u:g[order[i]])if(parent[u]<0){parent[u]=order[i];order.push_back(u);}int ans=0;for(int i=n-1;i>=0;i--){int v=order[i];for(int x:dp[v])ans=max(ans,x);for(int u:g[v])if(parent[u]==v)for(int j=0;j<(int)f[v].size();j++)for(int k=0;k<(int)f[u].size();k++)if(f[v][j]==f[u][k]){ans=max(ans,dp[v][j]+dp[u][k]);dp[v][j]=max(dp[v][j],dp[u][k]+1);}}cout<<ans<<'\n';
''')

add('P1272','树上保留连通块的背包',
    'dp[u][s] 表示在 u 子树内保留含 u 的 s 个点，需切断多少向下边。初始只保留 u 时切掉所有孩子边；接纳孩子的 j 个点就加入其代价并恢复一条父子边。',
    '目标连通块有唯一最高点 u。若不保留某个孩子子树，切断 u 与该孩子的边；若保留，就必须接纳一个包含孩子根的连通块。\n\n初始 dp[u][1]=孩子数，相当于暂时切断所有孩子边。合并孩子 v 的 j 个点时，用 dp[u][s]+dp[v][j]−1 更新 dp[u][s+j]，减一是恢复预先切掉的 u—v。保持原状态则表示继续切掉该子树。\n\n全部合并后，若 u 不是全树根，还要切断其父边，才能使这个块独立。因此答案是所有 u 的 dp[u][P]+[u非根] 最小值。每个合法块都以它的最高点被枚举，且每条边的去留被准确计费。',
    '时间 O(NP²)，空间 O(NP)。','块必须含状态根；接纳孩子减掉一条预切边；非根答案补父边。',r'''
int n,P;cin>>n>>P;vector<vector<int>>g(n);for(int i=1;i<n;i++){int u,v;cin>>u>>v;g[u-1].push_back(v-1);}const int INF=1000000;vector<vector<int>>dp(n,vector<int>(P+1,INF));vector<int>size(n);function<void(int)>dfs=[&](int v){size[v]=1;dp[v][1]=g[v].size();for(int u:g[v]){dfs(u);vector<int>next=dp[v];for(int s=1;s<=min(P,size[v]);s++)for(int j=1;j<=min(size[u],P-s);j++)next[s+j]=min(next[s+j],dp[v][s]+dp[u][j]-1);dp[v].swap(next);size[v]+=size[u];}};dfs(0);int ans=INF;for(int v=0;v<n;v++)ans=min(ans,dp[v][P]+(v!=0));cout<<ans<<'\n';
''')

add('P5521','按“计算峰值减保留花数”排序孩子',
    '设 f[v] 为完成孩子 v 的最少花数，完成后只需保留 w[v]。按 f[v]−w[v] 从大到小处理孩子，维护已保留花数；最后还要同时放上当前点的 w[u]。',
    '完成一个孩子后，除了该孩子根上的 w[v]，它子树内的花都可以收回。若此前其它孩子已经留下 S 朵，处理 v 的资源峰值为 S+f[v]，完成后保留量增加 w[v]。所有孩子完成后，放当前点需要 Σw[v]+w[u]。\n\n相邻孩子 a、b 交换顺序时，两种峰值为 max(f[a],w[a]+f[b]) 与 max(f[b],w[b]+f[a])，其它已保留量相同。若 f[a]−w[a]≥f[b]−w[b]，前一种不大于后一种。因此按这个差降序可以不断交换到最优顺序。\n\n每个点的答案只涉及自己子树，先在其它子树摆花不能创造额外花朵，也不会改善目标。父编号小于子编号，可以从大到小计算 f；不必递归访问十万层树。',
    '时间 O(n log n)，空间 O(n)。','先完成孩子且保留其根；最终要同时拥有孩子与当前点的花；按 f−w 而非 f 排序。',r'''
int n;cin>>n;vector<vector<int>>g(n);for(int i=1;i<n;i++){int p;cin>>p;g[p-1].push_back(i);}vector<long long>w(n),f(n);for(auto&x:w)cin>>x;for(int v=n-1;v>=0;v--){sort(g[v].begin(),g[v].end(),[&](int a,int b){return f[a]-w[a]>f[b]-w[b];});long long saved=0,best=0;for(int u:g[v]){best=max(best,saved+f[u]);saved+=w[u];}f[v]=max(best,saved+w[v]);}for(int i=0;i<n;i++)cout<<f[i]<<(i+1==n?'\n':' ');
''')
