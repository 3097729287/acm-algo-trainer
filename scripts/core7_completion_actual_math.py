from core7_completion import add, FENWICK

MOD=r'''
const long long MOD=1000000007;
long long power(long long a,long long b){long long r=1;for(;b;b>>=1,a=a*a%MOD)if(b&1)r=r*a%MOD;return r;}
'''
EXGCD=r'''
long long exgcd(long long a,long long b,long long&x,long long&y){if(!b){x=1;y=0;return a;}long long u,v;long long g=exgcd(b,a%b,u,v);x=v;y=u-a/b*v;return g;}
'''

add('B3969','筛去含过大质因子的整数',
    '筛出 n 以内的质数，将所有大于 B 的质数的倍数标为不合法。剩下的正整数恰好没有过大的质因子，统计即可。',
    '一个数不满足 B-smooth，当且仅当它有一个大于 B 的质因子。先用埃氏筛判断质数，再枚举所有 p>B 的质数，把 p 的倍数标为不合法。\n\n不合法数一定会被它的过大质因子标记；被标记的数也确实含这个质因子，所以筛法既不遗漏也不误删。注意一没有任何质因子，应当计入。B≥n 时全部一到 n 都合法。',
    '时间 O(n log log n)，空间 O(n)。','一也算；不能只判断数本身是否大于 B；标记所有倍数。',r'''
int n,B;cin>>n>>B;vector<bool>composite(n+1),bad(n+1);for(int p=2;p<=n;p++)if(!composite[p]){if(1LL*p*p<=n)for(int j=p*p;j<=n;j+=p)composite[j]=1;if(p>B)for(int j=p;j<=n;j+=p)bad[j]=1;}int ans=0;for(int i=1;i<=n;i++)ans+=!bad[i];cout<<ans<<'\n';
''')

add('P3383','线性筛保存升序质数表',
    '从小到大扫描，未被标记的数加入质数表。每个合数只由它的最小质因子标记一次，最后第 k 个质数直接访问 primes[k−1]。',
    '处理整数 i 时，按升序枚举已发现质数 p，标记 i·p。当 p 整除 i 后立即停止：之后更大的质数不再是 i·p 的最小质因子，应交由其它整数处理。\n\n每个合数 x 唯一对应 p=最小质因子、i=x/p，且这对会在停止条件之前被枚举，所以每个合数恰好标记一次。未标记数就是质数，扫描顺序保证质数表递增。\n\n范围达到一亿，标记使用位压缩的 vector<bool>，质数表仍保存整数。乘积用六十四位判断边界，查询使用一开始的序号。',
    '预处理 O(n)，每问 O(1)，空间 O(n) 位加 O(π(n)) 个整数。','一不是质数；整除时立即 break；先判断六十四位乘积是否越界。',r'''
int n,q;cin>>n>>q;vector<bool>composite(n+1);vector<int>primes;for(int i=2;i<=n;i++){if(!composite[i])primes.push_back(i);for(int p:primes){long long x=1LL*i*p;if(x>n)break;composite[x]=1;if(i%p==0)break;}}while(q--){int k;cin>>k;cout<<primes[k-1]<<'\n';}
''')

add('P3811','利用余数的逆元线性递推',
    '由 p=(p/i)·i+p%i，在模 p 下整理得到 inv[i]=(p−p/i)·inv[p%i] mod p。从 inv[1]=1 递推即可。',
    '设 q=floor(p/i)、r=p%i，则 qi+r≡0。因为一到 n 均小于质数 p，i 与 r 都有逆元；对 i>1 有 r>0。两侧乘以 inv[i]inv[r]，得到 inv[i]≡−q·inv[r]。\n\n余数 r<i，因此扫描 i 递增时 inv[r] 已经求出。用 p−q 表示负系数，先做六十四位乘法再取模。这样不用对每个数单独做快速幂。',
    '时间 O(n)，空间 O(n)。','质数且 n<p 保证逆元存在；inv[1]=1；乘法用 long long。',r'''
int n,p;cin>>n>>p;vector<int>inv(n+1);inv[1]=1;cout<<1<<'\n';for(int i=2;i<=n;i++){inv[i]=1LL*(p-p/i)*inv[p%i]%p;cout<<inv[i]<<'\n';}
''')

add('P7960','含七因子筛与合法数后继',
    '从小到大扫描，若一个尚未禁用的数含数字七，就禁用它的所有倍数。筛完后倒序记录每个位置之后的首个合法数，回答询问。',
    '一个整数不合法，当且仅当能被某个含七的数整除。扫描到含七且未禁用的 i 时，筛掉它的倍数；若 i 早已被筛掉，它的所有倍数也已被某个更小含七因子筛掉，无须重复操作。\n\n每个不合法数都有含七因子，该因子自身被处理或已经被更小因子覆盖，因此筛法完整。之后倒序扫描，维护最近的合法数 next：先保存当前数的严格后继，再在当前合法时更新 next。\n\n预处理范围必须超过最大询问，直到确认其中存在比最大询问更大的合法数。代码采用可扩大的上界，若尾部全被禁用就翻倍重筛，避免依赖未经证明的固定余量。',
    '设最终预处理上界为 L，时间 O(L log L)，空间 O(L)。','倍数不一定含七；后继必须严格更大；非法询问输出 −1。',r'''
int T;cin>>T;vector<int>queries(T);int maximum=0;for(int&x:queries){cin>>x;maximum=max(maximum,x);}int limit=max(128,maximum+128);vector<bool>bad;vector<int>next;for(;;){bad.assign(limit+1,false);for(int i=1;i<=limit;i++)if(!bad[i]){int x=i;bool seven=false;while(x){if(x%10==7)seven=true;x/=10;}if(seven)for(int j=i;j<=limit;j+=i)bad[j]=true;}int last=0;next.assign(limit+1,0);for(int i=limit;i>=1;i--){next[i]=last;if(!bad[i])last=i;}if(next[maximum])break;limit*=2;}for(int x:queries)cout<<(bad[x]?-1:next[x])<<'\n';
''')

add('AT_abc269_f','按行列奇偶分解矩形和',
    '保留的格子满足行列同奇偶。对奇行奇列、偶行偶列两类，分别用等差数列求行号减一之和、列号之和，再组合 (行号−1)·M+列号。',
    '矩形内有效格可以拆为奇行×奇列与偶行×偶列，两个笛卡尔积不相交。设某类有 nr 行、nc 列，行号减一之和为 sr，列号之和为 sc，则该类总和为 M·sr·nc+sc·nr。\n\n同奇偶的行列是公差为二的等差数列。将起点调整到所需奇偶，算出项数和末项，用“首末项之和乘项数除二”求和；模数为奇质数，可用二的逆元。\n\n每次询问直接处理两个奇偶类，不必枚举格子，也不必存储巨大网格。先将各因子取模再乘，避免原始矩形总和溢出。',
    '每问 O(1)，额外空间 O(1)。','保留行列同奇偶；列公式使用原始 M；乘法中间及时取模。',r'''
long long N,M;int Q;cin>>N>>M>>Q;const long long P=998244353,INV2=(P+1)/2;auto range=[&](long long l,long long r,int parity){if(l%2!=parity)l++;if(l>r)return pair<long long,long long>{0,0};long long count=(r-l)/2+1,last=l+2*(count-1);long long sum=(l+last)%P*(count%P)%P*INV2%P;return pair<long long,long long>{count%P,sum};};while(Q--){long long A,B,C,D;cin>>A>>B>>C>>D;long long ans=0;for(int parity=0;parity<2;parity++){auto[nr,sr]=range(A,B,parity);auto[nc,sc]=range(C,D,parity);sr=(sr-nr+P)%P;ans=(ans+(M%P)*sr%P*nc+sc*nr)%P;}cout<<ans<<'\n';}
''')

add('P6523','相邻不同乘积的最大公约数确定中间质数',
    '找到一对不同的相邻 A，它们的 gcd 恰好是共同的中间质数。以此向左右逐项相除还原全部 B，最后检查是否均不超过 M。',
    '若 A[i]=B[i]B[i+1]、A[i+1]=B[i+1]B[i+2] 且两者不等，那么两侧质数 B[i] 与 B[i+2] 不同，故 gcd(A[i],A[i+1])=B[i+1]。这一位置唯一确定后，利用相邻乘积依次反推出所有其它质数。\n\n题目保证忽略 M 时存在合法质数序列，且至少有两个 A 不同，因此必然能找到一对相邻不同值；无须为可能达到十八位的数做质因数分解或质性测试。\n\n还原后若存在 B[i]>M，则唯一序列不满足限制，输出 −1；否则输出该序列。所有计算都在六十四位范围内，不要直接相乘两个十八位输入。',
    '时间 O(n+log max A)，空间 O(n)。','使用相邻且不同的乘积；gcd 对应中间位置；依赖题目保证的质数分解存在性。',r'''
int T;cin>>T;while(T--){int n;long long M;cin>>n>>M;vector<long long>a(n-1),b(n);for(auto&x:a)cin>>x;int k=0;while(a[k]==a[k+1])k++;b[k+1]=gcd(a[k],a[k+1]);for(int i=k;i>=0;i--)b[i]=a[i]/b[i+1];for(int i=k+1;i<n-1;i++)b[i+1]=a[i]/b[i];bool ok=all_of(b.begin(),b.end(),[&](long long x){return x<=M;});if(!ok)cout<<-1<<'\n';else for(int i=0;i<n;i++)cout<<b[i]<<(i+1==n?'\n':' ');}
''')

add('CF632D','筛每个候选公倍数能容纳多少元素',
    '若最小公倍数为 L，选中的数都必须整除 L，而且所有整除 L 的输入数都可以选。按倍数枚举累加频次，找到可容纳最多元素的 L，再输出所有整除它的下标。',
    '任何 LCM≤m 的子序列，必然包含在“所有能整除该 LCM 的输入元素”中，补上这些元素不会让 LCM 超出 L。因此只要对每个 L≤m 计算输入中有多少个 L 的因数。\n\n统计 cnt[v] 后，枚举每个 v≤m，把 cnt[v] 加到所有倍数 v、2v、3v……的得分。得分最大的候选 L 对应最优长度；大于 m 的输入数无法加入任何合法非空子序列，可直接略过。\n\n输出这些元素的下标，并实际累积它们的 LCM 作为输出值，保证输出与子序列完全一致。若一个都选不到，空序列的 LCM 按题意为一。',
    '时间 O(n+m log m)，空间 O(n+m)。','超过 m 的数忽略；下标保持递增；空序列的 LCM 为一。',r'''
int n,m;cin>>n>>m;vector<int>a(n),cnt(m+1),score(m+1);for(int&x:a){cin>>x;if(x<=m)cnt[x]++;}for(int v=1;v<=m;v++)if(cnt[v])for(int L=v;L<=m;L+=v)score[L]+=cnt[v];int best=1;for(int L=2;L<=m;L++)if(score[L]>score[best])best=L;vector<int>indices;long long L=1;for(int i=0;i<n;i++)if(best%a[i]==0){indices.push_back(i+1);L=L/gcd(L,(long long)a[i])*a[i];}cout<<L<<' '<<indices.size()<<'\n';for(int i=0;i<(int)indices.size();i++)cout<<indices[i]<<(i+1==(int)indices.size()?'\n':' ');if(indices.empty())cout<<'\n';
''',checker='lcm-subsequence')

add('P1516','扩展欧几里得解相遇同余方程',
    '跳 t 次后相遇等价于 (m−n)t≡y−x mod L。用扩展欧几里得判断是否有解，再将一个解规范化到模 L/gcd(m−n,L) 的最小非负剩余。',
    '两只青蛙位置分别为 x+mt、y+nt，首尾相接表示两者相差 L 的整数倍，所以得到线性同余方程。记 a=m−n、b=y−x，g=gcd(|a|,L)。只有 g 整除 b 时有解。\n\n扩展欧几里得求出 |a|u+Lv=g；若 a 为负，将 u 取反。乘上 b/g 得到一个 t 解。所有解相差 L/g，将它规范化到零至 L/g−1 就得到首次相遇的非负次数。\n\n若步长相同，方程左边恒为零：初始位置模 L 相同则答案零，否则不可能。代码统一处理为 g=L。乘解系数时用 __int128，避免中间乘积溢出。',
    '时间 O(log L)，空间 O(log L) 的递归栈。','相对速度可能为负；按 L/g 取模；无解输出 Impossible。',r'''
long long x,y,m,n,L;cin>>x>>y>>m>>n>>L;long long a=m-n,b=y-x,u,v,g=exgcd(llabs(a),L,u,v);if(b%g){cout<<"Impossible\n";return 0;}if(a<0)u=-u;long long mod=L/g;long long t=(__int128)u*(b/g)%mod;if(t<0)t+=mod;cout<<t<<'\n';
''',EXGCD)

add('P2568','枚举素数 gcd，欧拉函数统计互质点对',
    '若 gcd(x,y)=p，令 x=pa、y=pb，则 a、b 在一到 floor(n/p) 中互质。这个范围的有序互质对数为 2·Σφ(i)−1，筛出欧拉函数前缀和后对所有质数求和。',
    '按 gcd 的素数值 p 分类，各类互不重叠。除去 p 后，需要统计一到 t=floor(n/p) 的有序互质对。\n\n最大值为 i>1 时，小于 i 且与 i 互质的数有 φ(i) 个，它们可放在两个位置，贡献 2φ(i)。最大值为一只有 (1,1) 一对，所以总数为 1+2Σ(i=2..t)φ(i)=2Σ(i=1..t)φ(i)−1。\n\n用线性筛同时求质数表和 φ。若 p|i，则 φ(ip)=pφ(i)；否则 φ(ip)=(p−1)φ(i)。把 φ 数组原地改成六十四位前缀和，再枚举质数 p≤n 累加公式。',
    '时间 O(n)，空间 O(n)。','统计有序点对；φ(1)=1；前缀和和答案用 long long。',r'''
int n;cin>>n;vector<long long>phi(n+1);vector<bool>composite(n+1);vector<int>primes;phi[1]=1;for(int i=2;i<=n;i++){if(!composite[i]){primes.push_back(i);phi[i]=i-1;}for(int p:primes){long long x=1LL*i*p;if(x>n)break;composite[x]=true;if(i%p==0){phi[x]=phi[i]*p;break;}phi[x]=phi[i]*(p-1);}}for(int i=1;i<=n;i++)phi[i]+=phi[i-1];long long ans=0;for(int p:primes)ans+=2*phi[n/p]-1;cout<<ans<<'\n';
''')

add('P6217','按质数幂层数统计区间 gcd 乘积',
    '将 lcm(a,x) 写成 ax/gcd(a,x)。预处理 a 的区间乘积，并为每个质数幂保存能被它整除的位置。分解 x 后，用这些位置表统计 gcd 中每个质因子的总指数，再乘逆元消去。',
    '区间答案为 product(a)·x^len / product(gcd(a,x))。若 x 中 p 的指数为 e，分母中 p 的总指数是 Σ_i min(vp(a_i),e)。\n\n把最小值按层展开：min(v,e)=Σ(j=1..e)[v≥j]，所以总指数等于“区间内被 p 整除的个数”加“被 p² 整除的个数”……直到 p^e。对每个出现过的质数幂，预存能被它整除的下标，查询时两次二分就得到区间个数。\n\n所有 a 和 x 小于模数，区间乘积与质因子均可取逆元。前缀乘积用一次逆元加倒推得到全部逆前缀；每次查询只分解 x、按质数幂二分，再做快速幂。',
    '设值域 V、最大质因子指数和为 E=O(log V)，预处理 O(V+nE)，每问 O(E log n+E log n)；空间 O(V+nE)。','每一层质数幂都要计入；区间包括两端；除法转为模逆元。',r'''
int n,q;cin>>n>>q;const int V=200000;vector<int>spf(V+1),primes;for(int i=2;i<=V;i++){if(!spf[i]){spf[i]=i;primes.push_back(i);}for(int p:primes){if(p>spf[i]||1LL*i*p>V)break;spf[i*p]=p;}}vector<vector<int>>positions(V+1);vector<int>a(n+1);vector<long long>pref(n+1,1),invPref(n+1,1),inv(V+1);inv[1]=1;for(int i=2;i<=V;i++)inv[i]=(MOD-MOD/i)*inv[MOD%i]%MOD;for(int i=1;i<=n;i++){cin>>a[i];pref[i]=pref[i-1]*a[i]%MOD;int x=a[i];while(x>1){int p=spf[x],pw=1;while(x%p==0){x/=p;pw*=p;positions[pw].push_back(i);}}}invPref[n]=power(pref[n],MOD-2);for(int i=n;i>=1;i--)invPref[i-1]=invPref[i]*a[i]%MOD;while(q--){int l,r,x;cin>>l>>r>>x;long long ans=pref[r]*invPref[l-1]%MOD*power(x,r-l+1)%MOD;while(x>1){int p=spf[x],pw=1;long long exponent=0;while(x%p==0){x/=p;pw*=p;auto&v=positions[pw];exponent+=upper_bound(v.begin(),v.end(),r)-lower_bound(v.begin(),v.end(),l);}ans=ans*power(inv[p],exponent)%MOD;}cout<<ans<<'\n';}
''',MOD)

add('AT_arc145_c','最优相邻数配对与不嵌套匹配',
    '全局最大得分必须配对 (1,2)、(3,4)、……。这些配对在排列中的两个端点不能相互嵌套；不嵌套匹配由 Catalan 数计数，再乘 N! 种配对标签排列及 2^N 种内部方向。',
    '对 a<b<c<d，ab+cd 比 ac+bd 和 ad+bc 都大，交换论证说明最大乘积和唯一使用相邻数配对。因此问题变为：这些固定配对能否按相同次序出现在两个子序列中。\n\n若两个配对的端点次序为 XYYX，外层 X 在一个子序列中早于 Y，在另一个中却晚于 Y，不能实现。反之，没有这种嵌套时，把每对先出现者放 A、后出现者放 B；各对的开始次序与结束次序相同，便能逐项配对。\n\n将每对的先出现记左括号，后出现记右括号，得到合法括号序列。给定这个序列，不嵌套匹配必须按先进先出连接，恰好一种；合法括号序列共有 Catalan(N) 种。再为 N 对分配标签 N! 种、每对决定两个数的先后 2^N 种。答案为 Catalan(N)·N!·2^N=(2N)!·2^N/(N+1)!，在质数模下用逆元计算。',
    '时间 O(N+log MOD)，空间 O(1)。','禁止的是端点嵌套，允许交错；两侧子序列都要保持顺序；N! 不能遗漏。',r'''
int n;cin>>n;const long long P=998244353;auto powmod=[&](long long a,long long b){long long r=1;for(;b;b>>=1,a=a*a%P)if(b&1)r=r*a%P;return r;};long long factorial=1,denominator=1;for(int i=1;i<=2*n;i++){factorial=factorial*i%P;if(i<=n+1)denominator=denominator*i%P;}cout<<factorial*powmod(denominator,P-2)%P*powmod(2,n)%P<<'\n';
''')

add('P1297','错位相邻答案相同的概率',
    '选项数为 u、v 的两题答案独立均匀，相同概率为 min(u,v)/(uv)=1/max(u,v)。将循环相邻两题的概率相加，得到期望。',
    '第 i 题的答案被抄到下一题。只有两个正确选项编号相同，下一题才会答对。可相同的编号有 min(a[i],a[next]) 个，每一对答案等概率，因此正确概率为其除以 a[i]a[next]，化简为较大选项数的倒数。\n\n期望具有线性性，各题是否正确即使有相关性也能直接相加。首尾循环的一对不能遗漏。\n\n生成序列分两步：先用原始递推值生成下一原始值，再将当前值对 C 取模加一作为选项数。不能把已转成选项数的值带回生成器。只保留原始前值、前一个选项数、首项，即可常数空间累加。',
    '时间 O(n)，空间 O(1)。','生成器用转换前的值；包含末题到首题；保留三位小数。',r'''
int n;long long A,B,C,raw;cin>>n>>A>>B>>C>>raw;long long first=raw%C+1,previous=first;long double ans=0;for(int i=2;i<=n;i++){raw=(raw*A+B)%100000001;long long current=raw%C+1;ans+=1.0L/max(previous,current);previous=current;}ans+=1.0L/max(previous,first);cout<<fixed<<setprecision(3)<<ans<<'\n';
''')

add('P4071','选择不动点后对剩余位置错排',
    '先选择 m 个不动点，再让其余 n−m 个元素全部错位。答案是 C(n,m)·D[n−m]，其中错排数满足 D[k]=(k−1)(D[k−1]+D[k−2])。',
    '恰好 m 个位置保持原值时，这些位置有 C(n,m) 种选法。删除已固定元素后，其余元素不能出现在自己的位置，正是 n−m 个标号的错排。两步选择独立。\n\n错排递推可按元素一的去向 j 分类。若 j 回到一的位置，两者组成二元环，剩下 D[k−2] 种；否则把一接入 j 所在循环，相当于剩下 k−1 个元素错排，有 D[k−1] 种。j 有 k−1 种选择，所以得到递推。初值 D[0]=1、D[1]=0。\n\n预处理阶乘、逆阶乘与错排数，所有查询常数时间。m>n 时直接为零。',
    '预处理 O(max n)，每问 O(1)，空间 O(max n+T)。','空错排有一种；一个元素不能错排；m>n 输出零。',r'''
int T;cin>>T;vector<pair<int,int>>queries(T);int N=0;for(auto&[n,m]:queries){cin>>n>>m;N=max(N,n);}vector<long long>f(N+1,1),inv(N+1,1),d(N+1);d[0]=1;for(int i=1;i<=N;i++)f[i]=f[i-1]*i%MOD;for(int i=2;i<=N;i++)d[i]=(i-1)*(d[i-1]+d[i-2])%MOD;inv[N]=power(f[N],MOD-2);for(int i=N;i>=1;i--)inv[i-1]=inv[i]*i%MOD;for(auto[n,m]:queries)cout<<(m>n?0:f[n]*inv[m]%MOD*inv[n-m]%MOD*d[n-m]%MOD)<<'\n';
''',MOD)

add('P6146','按每个连通块的最左端点计贡献',
    '每个连通块恰有一个最左端点。扫描端点，若某线段左端点前有 c 条线段覆盖该位置，那么让它成为新块起点的子集有 2^(N−1−c) 个。',
    '固定线段 i，若它的左端点是某个并集连通块的最左点，i 必须被选择，所有覆盖这个左端点的其它线段都不能选择；剩下线段任意选。\n\n端点两两不同，因此覆盖其左端点的其它线段恰好是扫描时已开始且未结束的 c 条线段。自由选择的线段有 N−1−c 条，贡献为二的该次方。\n\n每个子集的每个连通块都由唯一最左端点计一次，总贡献正好是所有复杂度之和。端点范围是一到二 N，可以直接建立起终事件数组，线性扫描。',
    '时间 O(N)，空间 O(N)。','贡献在将当前线段加入活跃集合之前计算；空集贡献零；端点不重复是题目保证。',r'''
int n;cin>>n;vector<int>event(2*n+2);for(int i=0;i<n;i++){int l,r;cin>>l>>r;event[l]=1;event[r]=-1;}vector<long long>two(n+1,1);for(int i=1;i<=n;i++)two[i]=two[i-1]*2%MOD;int active=0;long long ans=0;for(int x=1;x<=2*n;x++){if(event[x]==1){ans=(ans+two[n-1-active])%MOD;active++;}else if(event[x]==-1)active--;}cout<<ans<<'\n';
''',MOD)

add('CF1267K','阶乘进制数位的受限排列',
    '依次除以二、三、四所得余数，正是各位上界分别为一、二、三的阶乘进制。统计同一数位多重集合的合法排列，减去最高位为零的排列，再减去原数字。',
    '连续整除可唯一反向还原原数，所以每个满足“第 i 位小于 i+2、最高位非零”的数位序列对应一个密钥。指纹只保留数位多重集合，任务就是给这些数位重新安排位置。\n\n从大数位到小数位放置。若长度为 L，数位 d 可放入容量至少 d 的位置，共 L−max(1,d)+1 个；再减去已经放过的大数位数量，得到当前选择数。乘起来先把相同数位当成不同对象，最后除以每种数位频次的阶乘。上界限制是嵌套的，因此这个乘法直接计完全部安排。\n\n最高位为零会使实际除法提前结束，必须减去。固定最高位零后，去掉一个零，用长度 L−1 的容量重新计算。最后减一排除原密钥。十八位范围的数位不足二十位，中间使用 __int128 保证精确。',
    '每组 O(L log L)，空间 O(L)，L=O(log k/log log k)。','最高位不能为零；相同余数要除重；最后减去原数。',r'''
int T;cin>>T;while(T--){long long k;cin>>k;vector<int>d;for(int base=2;k;base++){d.push_back(k%base);k/=base;}auto countWays=[&](vector<int>a){int L=a.size();sort(a.rbegin(),a.rend());__int128 ways=1;vector<int>cnt(22);for(int i=0;i<L;i++){int choices=L-max(1,a[i])+1-i;if(choices<=0)return (long long)0;ways*=choices;cnt[a[i]]++;}for(int c:cnt)for(int i=2;i<=c;i++)ways/=i;return (long long)ways;};long long ans=countWays(d);auto it=find(d.begin(),d.end(),0);if(it!=d.end()){d.erase(it);ans-=countWays(d);}cout<<ans-1<<'\n';}
''')

add('P6834','层连通块公式与滑动窗口期望',
    '固定树的最少次数为 a1+Σmax(ai−a[parent],0)。对每个 i 平均枚举允许的父亲，窗口内用树状数组求小于 ai 的值的个数与和，得到这一项的期望。',
    '把果实按高度分层，第 h 层保留所有 a[i]≥h 的点，每个连通块用一次魔法即可。所有层的连通块总数等于 Σa[i]−Σ边min(a[u],a[v])，也就是 a1+Σ(i>1)max(a[i]−a[parent],0)。\n\n这个构造也是最优的。记上式为势能，一次对连通块减一时，点和减少块大小，内部边最小值减少块大小减一，边界的变化只会进一步降低势能的减少量，因此势能每次最多下降一。要降到零，至少需要初始势能次，按层构造恰好达到它。\n\n利用期望线性性，第 i 项对最近 min(k,i−1) 个值取平均。若其中小于 a[i] 的数有 c 个、总和为 s，则正差之和为 a[i]c−s。离散化数值，用两棵树状数组在滑动窗口中维护数量与总和，再乘窗口长度的模逆元。',
    '时间 O(n log n)，空间 O(n)。','差取正部后再求平均；旧父亲离开窗口时删除；a 可以为零。',r'''
int n,k;cin>>n>>k;const long long P=998244353;vector<long long>a(n),values;for(auto&x:a)cin>>x;values=a;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());Fenwick count(values.size()),sum(values.size());vector<long long>inv(k+1);inv[1]=1;for(int i=2;i<=k;i++)inv[i]=(P-P/i)*inv[P%i]%P;auto rank=[&](long long x){return int(lower_bound(values.begin(),values.end(),x)-values.begin())+1;};auto change=[&](int i,int delta){int r=rank(a[i]);count.add(r,delta);sum.add(r,a[i]*delta);};long long ans=a[0];change(0,1);for(int i=1;i<n;i++){if(i-k-1>=0)change(i-k-1,-1);int r=rank(a[i]);long long positive=(a[i]*count.sum(r-1)-sum.sum(r-1))%P;ans=(ans+positive*inv[min(k,i)])%P;change(i,1);}cout<<ans<<'\n';
''',FENWICK)

add('P5335','前缀树记录首次达到每个历史新高的时间',
    '维护每个前缀当前学生数。人数第一次升到 h 时，记录事件编号。查询人数曾经超过 v 的最早时间，直接取第一次达到 v+1 的记录；退课只改当前人数。',
    '查询问的是过去任何事件之后的首次越界，不仅是当前人数。人数每次只能增加或减少一，因此首次超过 v 就是首次达到 v+1。为每个前缀保存一组按人数递增的首次到达时间，永远不删除历史。\n\n姓名插入或删除时沿前缀树逐层加减当前人数。只有超过历史最高人数时，才追加当前事件编号。查询沿名字找到对应前缀，阈值用上次答案解码后，按人数直接索引历史；没有该记录则输出 −1。\n\n长姓名可能形成大量只达到一次的节点。代码将首次达到一的时间直接放在节点里，只为达到二及以上的前缀分配额外历史数组；孩子采用兄弟链，字母只有十种，每层最多检查十项。',
    '设所有操作字符串总长为 S，时间 O(10S)，空间 O(S)。','查询也占事件编号；退课保留历史；解码用上次答案绝对值；同名学生分别计数。',r'''
int n;cin>>n;struct Node{int child=-1,next=-1,letter=0,count=0,first=0,history=-1;};vector<Node>trie(1);trie.reserve(60LL*n+1);vector<vector<int>>history;long long last=0;for(int event=1;event<=n;event++){int type;string s;cin>>type>>s;int v=0;bool found=true;for(char c:s){int u=trie[v].child;while(u>=0&&trie[u].letter!=c-'a')u=trie[u].next;if(u<0){if(type==3){found=false;break;}u=trie.size();Node node;node.letter=c-'a';node.next=trie[v].child;trie.push_back(node);trie[v].child=u;}v=u;if(type!=3){trie[v].count+=type==1?1:-1;if(trie[v].count==1&&!trie[v].first)trie[v].first=event;else if(trie[v].count>=2){int h=trie[v].history;if(h<0){h=history.size();history.push_back({});trie[v].history=h;}if(trie[v].count>(int)history[h].size()+1)history[h].push_back(event);}}}if(type==3){long long a,b,c;cin>>a>>b>>c;long long threshold=((__int128)a*llabs(last)+b)%c;last=-1;if(found){if(threshold==0&&trie[v].first)last=trie[v].first;else if(threshold>=1&&trie[v].history>=0){auto&h=history[trie[v].history];if(threshold-1<(long long)h.size())last=h[threshold-1];}}cout<<last<<'\n';}}
''')
