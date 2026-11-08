from core7_completion import add

MANACHER=r'''
pair<vector<int>,vector<int>>manacher(const string&s){int n=s.size();vector<int>odd(n),even(n);for(int i=0,l=0,r=-1;i<n;i++){int k=i>r?1:min(odd[l+r-i],r-i+1);while(i-k>=0&&i+k<n&&s[i-k]==s[i+k])k++;odd[i]=k;if(i+k-1>r){l=i-k+1;r=i+k-1;}}for(int i=0,l=0,r=-1;i<n;i++){int k=i>r?0:min(even[l+r-i+1],r-i+1);while(i-k-1>=0&&i+k<n&&s[i-k-1]==s[i+k])k++;even[i]=k;if(i+k-1>r){l=i-k;r=i+k-1;}}return {move(odd),move(even)};}
'''
ZFUNCTION=r'''
vector<int>zfunction(const string&s){int n=s.size();vector<int>z(n);z[0]=n;for(int i=1,l=0,r=0;i<n;i++){if(i<=r)z[i]=min(r-i+1,z[i-l]);while(i+z[i]<n&&s[z[i]]==s[i+z[i]])z[i]++;if(i+z[i]-1>r){l=i;r=i+z[i]-1;}}return z;}
'''

add('P3805','奇偶两组 Manacher 半径',
    '分别计算字符为中心的奇回文半径和字符间隙为中心的偶回文半径。利用当前最右回文的对称位置初始化，只扩展尚未确定的部分，最终取最大长度。',
    'odd[i] 包含中心字符，代表区间 i−odd[i]+1 到 i+odd[i]−1；even[i] 的中心在 i−1 与 i 之间，代表 i−even[i] 到 i+even[i]−1。因此对应长度分别为 2odd[i]−1 与 2even[i]。\n\n维护已经求出的、右端最远的回文 [l,r]。若中心 i 在它内部，可以从镜像中心继承半径，但最多继承到 r；超出范围的部分再逐个比较。若 i 在外部，则从最小半径开始。\n\n每次成功扩展到未知区域都会推动最右端，失败比较每个中心最多一次，所以总比较次数为线性。使用两套半径避免构造长度翻倍的带分隔符字符串，适合千万字符输入。',
    '时间 O(n)，空间 O(n)。','奇半径含中心，偶半径不含；偶回文镜像下标与奇回文不同；不要逐个中心从零扩展。',r'''
string s;cin>>s;auto[odd,even]=manacher(s);int ans=0;for(int i=0;i<(int)s.size();i++)ans=max({ans,2*odd[i]-1,2*even[i]});cout<<ans<<'\n';
''',MANACHER)

add('P1659','按奇回文长度从大到小累积数量',
    'Manacher 求每个中心的最大奇回文长度。某中心也贡献所有更短的正奇数长度，因此从大到小扫描奇数长度并累加中心数，取前 K 个长度做快速幂乘积。',
    '若中心最大回文长度为 L，它恰好提供长度 L、L−2、……、一的各一个回文。先用 count[L] 统计最大长度正好为 L 的中心个数。\n\n降序扫描所有正奇数长度，累加 count 后的 running 就是当前长度的回文数量。需要的前 K 个一定先取较长长度；这一批取 min(K,running) 个，把长度的相应次方乘到答案，继续减少 K。\n\n每个中心贡献的不同长度对应不同位置子串，不会重复统计。扫描结束仍有 K 未满足则回文总数不足，输出 −1。模数不必是质数，快速幂仅用乘法。',
    '时间 O(n+n log K)，空间 O(n)。','只统计奇回文；频次要向短长度累加；K 可能达到万亿。',r'''
int n;long long K;string s;cin>>n>>K>>s;auto[odd,even]=manacher(s);vector<long long>cnt(n+1);for(int r:odd)cnt[2*r-1]++;const long long P=19930726;auto power=[&](long long a,long long b){long long r=1;for(;b;b>>=1,a=a*a%P)if(b&1)r=r*a%P;return r;};long long active=0,ans=1;for(int length=n%2?n:n-1;length>=1;length-=2){active+=cnt[length];long long take=min(K,active);ans=ans*power(length,take)%P;K-=take;if(!K)break;}cout<<(K?-1:ans)<<'\n';
''',MANACHER)

add('UVA10298','前缀函数确定最短完整循环节',
    '设 p=n−pi[n−1]。若 n 能被 p 整除，原串由 n/p 个循环节组成；否则只能看成自身重复一次。逐个处理直到读到点号。',
    '末尾的最长真前后缀长度为 b 时，字符串以位移 n−b 对齐的部分相等，所以 p=n−b 是最小周期。若长度恰好是周期的整数倍，就能完整切成相同的 p 长块。\n\n若最小周期不能整除 n，不存在另一个更短且能整除 n 的完整重复块，否则它会诱导一个可完整覆盖的最小循环节，与当前周期不整除矛盾。也可由 KMP 周期定理得到这一结论。\n\n前缀函数失配时沿 pi 回退，匹配时长度增加，所有回退总计线性。点号是结束标记，不参与计算。',
    '每串时间 O(n)，空间 O(n)。','必须检查 n%p；前后缀不能等于整个串；点号停止。',r'''
string s;while(cin>>s&&s!="."){int n=s.size();vector<int>pi(n);for(int i=1;i<n;i++){int j=pi[i-1];while(j&&s[i]!=s[j])j=pi[j-1];if(s[i]==s[j])j++;pi[i]=j;}int p=n-pi.back();cout<<(n%p?1:n/p)<<'\n';}
''')

add('P5446','折叠无限串的周期与镜面对称条件',
    '初始长度 m>1 时，反复翻转得到周期 2(m−1) 的无限镜像串。候选 m 必须满足这个周期，并且以 m−1 为中心的可见部分是回文；用 Z 函数与 Manacher 常数时间检查每个 m。',
    '令 L=m−1。翻转后的字符按原串下标零、一、……、L、L−1、……、一不断循环，所以周期是 2L；继续翻转只会延长同一无限串的前缀。\n\n候选 m 对应的初始串必是 S 的 m 长前缀。先检查周期：若 2L<n，要求 Z[2L]≥n−2L。再检查第一次折返：以 L 为中心，当前可见范围内必须对称，要求奇回文半径至少 min(L+1,n−L)。\n\n周期保证后续每块都与第一周期一致，回文条件保证第一周期确实是前缀的镜像，因此两个条件充分；它们也显然必要。m=1 时无限串只能是单一字符，单独判断整串是否相同。枚举 m 递增输出。',
    '时间 O(n)，空间 O(n)。','镜像不重复末字符；周期是 2(m−1)；长度一单独处理。',r'''
int T;cin>>T;while(T--){string s;cin>>s;int n=s.size();auto z=zfunction(s);auto[odd,even]=manacher(s);vector<int>ans;if(all_of(s.begin(),s.end(),[&](char c){return c==s[0];}))ans.push_back(1);for(int m=2;m<=n;m++){int L=m-1;if(odd[L]<min(L+1,n-L))continue;if(2*L<n&&z[2*L]<n-2*L)continue;ans.push_back(m);}for(int i=0;i<(int)ans.size();i++)cout<<ans[i]<<(i+1==(int)ans.size()?'\n':' ');}
''',MANACHER+ZFUNCTION)

add('P5451','共模攻击：将两个指数线性组合成一',
    '扩展欧几里得求 a·e1+b·e2=1，则 m≡c1^a·c2^b mod N。负指数改用密文的模逆元，所有模乘用 __int128。',
    '题目保证 e1、e2 互质，存在整数 a、b 使 ae1+be2=1。密文代入后，c1^a c2^b≡m^(ae1+be2)≡m，因此不需要分解模数，也不需要求私钥。\n\na、b 中可能有负数。由于 m 与 N 互质，两份密文也与 N 互质，所以负指数可以改为逆元的正指数。再用扩展欧几里得求密文模 N 的逆元，并规范化到非负余数。\n\nN 接近有符号六十四位上限，两个模内数相乘会超出 long long，模乘必须先转 __int128。扩展欧几里得的系数运算同样使用 __int128，避免中间减乘溢出。',
    '每组时间 O(log N+log e1+log e2)，空间 O(log N) 递归栈。','负指数先求逆；所有余数规范化；不能用普通 long long 乘法直接取模。',r'''
int T;cin>>T;while(T--){long long c1,c2,e1,e2,N;cin>>c1>>c2>>e1>>e2>>N;__int128 a,b;egcd(e1,e2,a,b);auto inverse=[&](long long x){__int128 u,v;egcd(x,N,u,v);u%=N;if(u<0)u+=N;return (long long)u;};auto power=[&](long long x,__int128 exponent){if(exponent<0){x=inverse(x);exponent=-exponent;}long long r=1;for(;exponent;exponent>>=1,x=(__int128)x*x%N)if(exponent&1)r=(__int128)r*x%N;return r;};cout<<(long long)((__int128)power(c1,a)*power(c2,b)%N)<<'\n';}
''',r'''
long long egcd(long long a,long long b,__int128&x,__int128&y){if(!b){x=1;y=0;return a;}__int128 u,v;long long g=egcd(b,a%b,u,v);x=v;y=u-(__int128)(a/b)*v;return g;}
''')

add('UVA11732','排序后用相邻 LCP 的区间最小值统计比较',
    '两串比较次数为 2·LCP+1，相同字符串再多一次结束判断。排序后任意两串 LCP 等于其间相邻 LCP 的最小值，用单调栈求所有区间最小值之和。',
    '按原题 strcmp 伪代码，每个相同的非空字符要做字符相等与是否结束两次比较，第一次不同只做一次；完全相同还要对结束符做两次。因此每对贡献 2LCP+1，再对完全相同的一对补一。伪代码可核对[原题 PDF](https://onlinejudge.org/external/117/11732.pdf)。\n\n将所有字符串字典序排序，令 h[i] 为相邻两串的 LCP。排序后第 l、r 两串的 LCP 恰好是 h[l+1..r] 的最小值。因此全部 LCP 之和等价于 h 所有非空子数组的最小值之和。\n\n单调递增栈按“以当前元素结尾的子数组”维护最小值与数量。弹出不小于新 h 的栈项，将这些项的数量合并给新值，同时更新当前结尾的最小值总和。最后答案为 n(n−1)/2+2·LCP总和+同串对数。这个方法避免为长字母数字串建立巨大字符表。',
    '设输入总长度为 S，时间 O(S log n+n)，空间 O(S+n)。','相同串额外补一次；输入含大小写字母和数字；答案六十四位。',r'''
int n,caseNo=0;while(cin>>n&&n){vector<string>a(n);for(auto&s:a)cin>>s;sort(a.begin(),a.end());long long same=0;for(int l=0;l<n;){int r=l+1;while(r<n&&a[r]==a[l])r++;same+=1LL*(r-l)*(r-l-1)/2;l=r;}vector<pair<int,int>>st;long long ending=0,totalLcp=0;for(int i=1;i<n;i++){int h=0;while(h<(int)min(a[i].size(),a[i-1].size())&&a[i][h]==a[i-1][h])h++;int count=1;while(!st.empty()&&st.back().first>=h){ending-=1LL*st.back().first*st.back().second;count+=st.back().second;st.pop_back();}st.push_back({h,count});ending+=1LL*h*count;totalLcp+=ending;}cout<<"Case "<<++caseNo<<": "<<1LL*n*(n-1)/2+2*totalLcp+same<<'\n';}
''')

add('UVA1401','字典前缀树上的分词 DP',
    'dp[i] 表示后缀 i..末尾的分词数。从每个 i 沿字典 Trie 向右匹配，遇到一个完整单词就把后面的 dp 加进来，模 20071027。',
    '每个划分有唯一第一个单词。若 s[i..j] 是字典词，则这个选择的方案数为 dp[j+1]；对所有可行单词求和即可。空后缀有一种划分，设 dp[n]=1。\n\n从右向左计算 i，Trie 从根开始逐字走，若无对应边立即停止，若到达单词结点便加 dp[j+1]。这样避免为每个字典词重复比较相同前缀。\n\n字典表示可用词集合，相同单词只应标为同一个终止结点，不能因重复输入虚增方案。每组读一个目标串和词数，直到文件结束，按 Case 编号输出。',
    '设最长词长 L、字典总长 S，时间 O(S+nL)，空间 O(S+n)。','空后缀为一；词与词可以相接；每次累加取模。',r'''
string s;int caseNo=0;while(cin>>s){int count;cin>>count;struct Node{array<int,26>next{};bool terminal=false;};vector<Node>trie(1);int maxLength=0;while(count--){string word;cin>>word;maxLength=max(maxLength,(int)word.size());int v=0;for(char c:word){int x=c-'a';if(!trie[v].next[x]){trie[v].next[x]=trie.size();trie.emplace_back();}v=trie[v].next[x];}trie[v].terminal=true;}const int P=20071027;int n=s.size();vector<int>dp(n+1);dp[n]=1;for(int i=n-1;i>=0;i--){int v=0;for(int j=i;j<n&&j<i+maxLength;j++){v=trie[v].next[s[j]-'a'];if(!v)break;if(trie[v].terminal){dp[i]+=dp[j+1];if(dp[i]>=P)dp[i]-=P;}}}cout<<"Case "<<++caseNo<<": "<<dp[0]<<'\n';}
''')

add('UVA11022','区间拼接或整段重复压缩',
    'dp[l][r] 为子串的最小字符权重。枚举切成两段的拼接，也枚举能完整重复构成该子串的较短周期，把它压缩成一个周期的最优表示。',
    '表示式的最外层要么是两个表示式拼接，要么是一个表示式重复。前者枚举分割点，代价为左右区间 dp 之和；后者需要某个长度 p 整除区间长，且整段每隔 p 个字符一致，代价就是第一个周期的 dp。\n\n原题权重只计字母，不计括号与指数，因此重复压缩不额外加数字长度或括号长度。重复单位内部还能继续压缩，这正是使用 dp 而非直接用 p 的原因。\n\n按区间长度递增，所有依赖的区间更短，归纳得到最优值。可以用预处理的任意两后缀 LCP 常数时间检查某个 p 是否为完整周期。详见[原题权重定义](https://onlinejudge.org/external/110/11022.pdf)。',
    '每串时间 O(n³)，空间 O(n²)。','权重不计括号和指数；重复单位可再次分解；星号停止输入。',r'''
string s;while(cin>>s&&s!="*"){int n=s.size();vector<vector<int>>lcp(n+1,vector<int>(n+1)),dp(n,vector<int>(n));for(int i=n-1;i>=0;i--)for(int j=n-1;j>=0;j--)if(s[i]==s[j])lcp[i][j]=lcp[i+1][j+1]+1;for(int len=1;len<=n;len++)for(int l=0;l+len<=n;l++){int r=l+len-1;dp[l][r]=len;for(int mid=l;mid<r;mid++)dp[l][r]=min(dp[l][r],dp[l][mid]+dp[mid+1][r]);for(int p=1;p<len;p++)if(len%p==0&&lcp[l][l+p]>=len-p)dp[l][r]=min(dp[l][r],dp[l][l+p-1]);}cout<<dp[0][n-1]<<'\n';}
''')

add('CF526D','Z 函数确定重复段，再批量标记可延伸前缀',
    '对每个块长 p，若前 kp 个字符由 k 个相同块组成，再允许附加最多 p 个与首块前缀相同的字符。用差分数组标记这一整段合法前缀长度。',
    '题目要求的 ABAB…A 可写为 k 个同长块 AB 加一个不超过整块长的前缀 A。A、B 可以为空，因此块长 p 只要至少一，额外长度可从零到 p。\n\n若 Z[p]≥(k−1)p，则前 kp 个字符是 k 次重复。接下来与开头相同的长度为 Z[kp]，所以合法总长度是区间 [kp,kp+min(p,Z[kp])]，并截断到 n。当 kp=n，额外只能为零。\n\n枚举 p≤n/k，将每个区间加到差分数组，最后前缀和大于零的位置输出一。k=1 时所有前缀都合法，也由同一公式得到。',
    '时间 O(n+n/k)，空间 O(n)。','允许 A 或 B 为空；kp 本身也合法；Z[n] 按零处理。',r'''
int n,k;string s;cin>>n>>k>>s;auto z=zfunction(s);z.push_back(0);vector<int>diff(n+2);for(int p=1;1LL*k*p<=n;p++)if(z[p]>=(k-1)*p){int l=k*p,r=min(n,l+min(p,z[l]));diff[l]++;diff[r+1]--;}int active=0;for(int i=1;i<=n;i++){active+=diff[i];cout<<(active?'1':'0');}cout<<'\n';
''',ZFUNCTION)

add('P7469','贪心子序列匹配与后缀排序去重',
    '枚举 t 的每个起点，贪心匹配 s 中最靠前位置，得到能作为子序列的最大长度。随后按 t 后缀的字典序，用相邻 LCP 扣除已经出现的相同字符串。',
    '这里按最后剩下的字符序列区分情况，同一个字符串的多种选取位置不另算。直接统计子序列匹配方式会超过题目答案。\n\n为 s 建 next[pos][c]，表示 pos 及之后第一个字符 c。对 t 的每个起点向右扫描，始终匹配 s 中最早可用位置，这会为后续字符留下最多空间；第一次无法匹配后，更长前缀也不可能匹配。得到 valid[i]，表示后缀 t[i..] 的前 valid[i] 个前缀字符串合法。\n\n把 t 的后缀排序。当前后缀与之前任一后缀共享的最长前缀，等于它与紧邻前驱的 LCP。凡共享且在当前合法长度内的字符串，在前驱处也合法，因为它们内容完全相同。因此当前新增数为 max(0,valid[i]−LCP)。\n\nn≤3000，可直接用平方 LCP 表，使后缀比较为常数时间，整个过程确定性去重，不依赖字符串哈希。',
    '时间 O(n²+n log n)，空间 O(n²)。','按剩余字符串去重；子序列贪心取最早位置；valid 不计空串。',r'''
int n;string s,t;cin>>n>>s>>t;vector<array<int,26>>next(n+1);next[n].fill(n);for(int i=n-1;i>=0;i--){next[i]=next[i+1];next[i][s[i]-'a']=i;}vector<int>valid(n),sa(n);for(int i=0;i<n;i++){int pos=0;for(int j=i;j<n;j++){pos=next[pos][t[j]-'a'];if(pos==n)break;valid[i]++;pos++;}sa[i]=i;}vector<vector<unsigned short>>lcp(n+1,vector<unsigned short>(n+1));for(int i=n-1;i>=0;i--)for(int j=n-1;j>=0;j--)if(t[i]==t[j])lcp[i][j]=lcp[i+1][j+1]+1;sort(sa.begin(),sa.end(),[&](int a,int b){int same=lcp[a][b];if(a+same==n||b+same==n)return n-a<n-b;return t[a+same]<t[b+same];});long long ans=0;for(int i=0;i<n;i++)ans+=max(0,valid[sa[i]]-(i?lcp[sa[i]][sa[i-1]]:0));cout<<ans<<'\n';
''')

add('P2638','加入未使用区后的两次隔板法',
    '把没有使用的零也看成放在一个额外储存区，分配 a 个相同零到 n+1 区有 C(n+a,n) 种。一的分配独立，答案为 C(n+a,n)·C(n+b,n)。',
    '每个实际储存区可以存任意多个零与一，因此两种信号的数量选择没有相互限制。对零额外设置一个“未使用区”，原来最多使用 a 个的方案就与把恰好 a 个零分配到 n+1 个有标号区一一对应。\n\n非负整数方程 x0+x1+…+xn=a 的解数由隔板法为 C(n+a,n)，一同理。两者独立相乘。\n\nn+a、n+b 都不超过五十，单个组合数能放在六十四位，但两者乘积可能远超六十四位。用 __int128 做 Pascal 递推与最终乘积，再手动输出十进制。',
    '时间 O(50²)，空间 O(50²)。','未用信号也参与一一对应；两种信号独立；答案不能只用 unsigned long long。',r'''
int n,a,b;cin>>n>>a>>b;__int128 C[51][51]{};for(int i=0;i<=50;i++){C[i][0]=C[i][i]=1;for(int j=1;j<i;j++)C[i][j]=C[i-1][j-1]+C[i-1][j];}__int128 ans=C[n+a][n]*C[n+b][n];string out;do{out+=char('0'+ans%10);ans/=10;}while(ans);reverse(out.begin(),out.end());cout<<out<<'\n';
''')

add('P10253','九倍回声和附近的线性候选扫描',
    '设 S(x) 为十进制数位和，则 10x−S(x)=9y。x 从 ceil(9y/10) 起只需尝试 O(位数) 个值；大整数加一时顺便维护数位和，得到总线性时间。',
    '把 x 的每位贡献展开，数字 d 在十的 j 次方位贡献 d(10^(j+1)−1)/9，因此 9f(x)=10x−S(x)。若 f(x)=y，就有 10x−9y=S(x)。\n\n因为零≤S(x)≤9·digits(y)，候选 x 位于 ceil(9y/10) 到 (9y+9digits(y))/10 之间，只有线性多个。先以十进制数组计算 9y，去掉末位得到除十商，并按余数向上取整；同时维护 delta=10x−9y 与数位和。\n\n每次 x 加一，delta 加十。数位和通过进位更新：每个被清零的九减九，最后进位位置加一。连续加一时所有进位总次数为候选数的常数倍，加上最初可能的一次长进位，总时间线性。若数位和等于 delta 即找到答案。\n\nf(x) 严格递增，因为 x 本身递增且各个向下整除项都不减，所以找到的解必唯一；超过数位和上界仍无解则输出 −1。',
    '设输入十进制位数 d，时间 O(d)，空间 O(d)。','输入可以有五十万位；不能转固定整数；零的答案为零；维护的是 x 的数位和。',r'''
int T;cin>>T;while(T--){string y;cin>>y;vector<int>d;int carry=0;for(int i=(int)y.size()-1;i>=0;i--){int z=(y[i]-'0')*9+carry;d.push_back(z%10);carry=z/10;}if(carry)d.push_back(carry);int rem=d[0];d.erase(d.begin());if(d.empty())d.push_back(0);int sum=accumulate(d.begin(),d.end(),0);auto increment=[&](){int i=0;while(i<(int)d.size()&&d[i]==9){d[i]=0;sum-=9;i++;}if(i==(int)d.size())d.push_back(0);d[i]++;sum++;};int delta=0;if(rem){increment();delta=10-rem;}bool found=false;int bound=9*y.size();for(;delta<=bound;delta+=10){if(sum==delta){found=true;break;}increment();}if(!found){cout<<-1<<'\n';continue;}while(d.size()>1&&!d.back())d.pop_back();for(int i=(int)d.size()-1;i>=0;i--)cout<<d[i];cout<<'\n';}
''')

add('P11749','按周期中心汇总有限和无限回文半径',
    '在 sss 上做 Manacher。每个中心相位若向两侧匹配满一个周期，就能在无限周期串中一直匹配；否则半径已固定。将同一相位在 k 块中的边界截断半径用等差数列求和。',
    '所有回文按中心计数，一个中心贡献的回文数就是它的半径。周期串中，同一相位的两边字符比较以 n 为周期；连续一个周期都相等后，后续比较永远相等，否则最大半径在这个周期内已经确定。\n\n对 sss 的中间一份求奇偶半径。奇半径包含中心，达到 n+1 即确认无限；偶半径达到 n 即确认无限。这些阈值在中间一份各中心都不会被字符串边界阻止。其它半径为有限 R。\n\n设相位 r 的第 j 个中心在 i=r+jn，总长 L=nk。奇中心实际贡献 min(R,i+1,L−i)，偶中心为 min(R,i,L−i)。有限 R 不超过一个周期，k≥2 时中间 k−2 块直接各贡献 R，首尾分别截断；k=1 单独取三者最小。\n\n无限 R 时，只需求 min(r+offset+jn,L−r−jn) 的和，offset 奇时为一、偶时为零。两项一个递增一个递减，在唯一交点处分开，两边各是等差数列，常数时间计算。遍历 n 个相位相加，避免构造长度可能达三千万亿的 t。',
    '时间 O(n)，空间 O(n)。','奇偶中心的左边界差一；中间 s 的半径才够完整；等差乘积使用 __int128。',r'''
int T;cin>>T;const long long P=998244353;while(T--){int n;long long k;string s;cin>>n>>k>>s;string triple=s+s+s;auto[odd,even]=manacher(triple);long long length=1LL*n*k,ans=0;auto contribution=[&](int r,int R,int offset,bool infinite)->long long{if(!infinite){if(k==1)return min({R,r+offset,n-r});return (((k-2)%P)*R+min(R,r+offset)+min(R,n-r))%P;}long long threshold=length-2LL*r-offset;long long left=threshold<0?0:min(k,threshold/(2LL*n)+1);long long right=k-left;__int128 total=(__int128)left*(r+offset)+(__int128)n*left*(left-1)/2+(__int128)right*(length-r)-(__int128)n*(left+k-1)*right/2;return total%P;};for(int r=0;r<n;r++){ans=(ans+contribution(r,odd[n+r],1,odd[n+r]>=n+1))%P;ans=(ans+contribution(r,even[n+r],0,even[n+r]>=n))%P;}cout<<ans<<'\n';}
''',MANACHER)
