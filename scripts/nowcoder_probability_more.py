"""Expectation recurrences, cyclic equations, tree elimination and subset probabilities."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_euler_support import EULER


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(233106,1900,['期望DP','自环消去'],'随机漏洞同时覆盖全部类型和全部组件的期望天数。',
        'E[i][j]为已见i种漏洞、j个组件时的剩余期望。一天后有四种情况：都旧ij，都新(n−i)(s−j)，仅类型新(n−i)j，仅组件新i(s−j)，总分母ns。把自环ij*E[i][j]移到左侧：E[i][j]=(ns+(n−i)jE[i+1][j]+i(s−j)E[i][j+1]+(n−i)(s−j)E[i+1][j+1])/(ns−ij)。终点E[n][s]=0，按i、j倒序计算，保留两行。',
        r'''int n,s; cin >> n >> s; vector<long double> next(s+2),current(s+2); for (int i=n;i>=0;i--) { fill(current.begin(),current.end(),0); for (int j=s;j>=0;j--) { if (i==n && j==s) continue; current[j]=((long double)n*s+(long double)(n-i)*j*next[j]+(long double)i*(s-j)*current[j+1]+(long double)(n-i)*(s-j)*next[j+1])/((long double)n*s-i*j); } next.swap(current); } cout << fixed << setprecision(10) << next[0];''',
        '组件和类型是同时抽取的一对标签，不能分别求期望后直接取最大或相加。',
        floating_output=True,complexity=r'时间 $O(ns)$，空间 $O(s)$。')
    put(210477,1400,['期望DP'],'重掷越界骰子，向前走至终点，求累计奖励期望。',
        'E[i]含当前位置奖励。越界会重新掷到合法步长，因此合法的1..min(6,n−i)步等概率，E[i]=a[i]+平均(E[i+1..i+limit])。终点E[n]=a[n]，倒序求解，输出E[1]。',
        r'''int n; cin >> n; vector<long double> value(n+1),expected(n+1); for (int i=1;i<=n;i++) cin >> value[i]; for (int i=n;i>=1;i--) { expected[i]=value[i]; int limit=min(6,n-i); if (limit) for (int step=1;step<=limit;step++) expected[i]+=expected[i+step]/limit; } cout << fixed << setprecision(10) << expected[1];''',
        '起点奖励也计入；接近终点时分母是合法步数，不总为6。',
        floating_output=True,complexity=r'时间 $O(6n)$，空间 $O(n)$。')
    put(210481,2000,['期望DP','线性方程'],'三骰指定组合清零，其余加点数，求分数超过n的期望次数。',
        '设E[i]是当前分数i的剩余次数，超过n后为0。一次掷骰后E[i]=1+pReset*E[0]+Σ pSum[s]*E[i+s]。把E[i]表示为A[i]*E[0]+B[i]，倒序计算A[i]=pReset+ΣpSum[s]A[i+s]、B[i]=1+ΣpSum[s]B[i+s]。最后E[0]=B[0]/(1−A[0])。\n\n枚举全部骰子组合，只把非清零组合按点数和归类。若三个骰子都只有1面，则每次必清零，期望无穷；当前题面没有规定此退化情况的输出，代码用inf表达，有限期望数据按公式输出。',
        r'''int n,k1,k2,k3,a,b,c; cin >> n >> k1 >> k2 >> k3 >> a >> b >> c; int maximum=k1+k2+k3; long double total=k1*k2*k3; vector<long double> probability(maximum+1); for (int x=1;x<=k1;x++) for (int y=1;y<=k2;y++) for (int z=1;z<=k3;z++) if (x!=a || y!=b || z!=c) probability[x+y+z]+=1/total; vector<long double> coefficient(n+maximum+1),constant(n+maximum+1); for (int i=n;i>=0;i--) { coefficient[i]=1/total; constant[i]=1; for (int s=3;s<=maximum;s++) { coefficient[i]+=probability[s]*coefficient[i+s]; constant[i]+=probability[s]*constant[i+s]; } } if (k1*k2*k3==1) cout << "inf"; else cout << fixed << setprecision(12) << constant[0]/(1-coefficient[0]);''',
        '目标是严格大于n，i=n仍需继续。清零组合不能同时计入普通点数和。',
        floating_output=True,complexity=r'时间 $O(k_1k_2k_3+n(k_1+k_2+k_3))$，空间 $O(n+k_1+k_2+k_3)$。')
    put(210487,2200,['概率DP','循环方程'],'队首可能等待、排到末尾、离队或关门，求关门时仍在前k位的概率。',
        'f[i][j]表示队长i、自己第j位时事件成功概率，已打饭离队后为0。先消去等待自环，令A=p2/(1−p1)、B=p3/(1−p1)、C=p4/(1−p1)。j>1时，f[i][j]=A*f[i][j−1]+B*f[i−1][j−1]+C*[j≤k]；j=1时，自己没卡会排到末尾，f[i][1]=A*f[i][i]+C。\n\n先把f[i][1]当变量x，递推得到f[i][i]=A^(i−1)*x+t，故x=(A*t+C)/(1−A^i)。求出首项再正序填本行，行间滚动。p4=0时不会发生关门事件，答案为0。',
        r'''int n,m,k; long double p1,p2,p3,p4; cin >> n >> m >> k >> p1 >> p2 >> p3 >> p4; if (p4==0) { cout << "0.00000"; return 0; } long double a=p2/(1-p1),b=p3/(1-p1),c=p4/(1-p1); vector<long double> previous(n+1),current(n+1); for (int size=1;size<=n;size++) { long double t=0; for (int j=2;j<=size;j++) t=a*t+b*previous[j-1]+(j<=k?c:0); current[1]=(a*t+c)/(1-powl(a,size)); for (int j=2;j<=size;j++) current[j]=a*current[j-1]+b*previous[j-1]+(j<=k?c:0); current.swap(previous); } cout << fixed << setprecision(5) << previous[m];''',
        'j=1成功打饭后离队，后续关门不计成功。不能把末尾回流当成上一行状态。',
        floating_output=True,complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(20709,1100,['对称性','期望线性性'],'黑白各1球，每次随机取球后同色净增1，求白球期望。',
        '过程在交换黑白颜色后完全对称，所以两色期望相同。每次总球数净增1，n次后总数确定为n+2；两色期望之和也是n+2，故白球期望为(n+2)/2。',
        r'''long long n; cin >> n; cout << fixed << setprecision(7) << (n+2)/2.0L;''',
        '取出的球被两个同色球替换，净增1，不是净增2。',
        floating_output=True,complexity=r'时间、空间均 $O(1)$。')
    put(14378,2000,['期望DP','双指针','后缀和'],'非负数组随机选择合法下一段，求段数期望。',
        '若某元素>x，该元素无法被任何合法段覆盖，直接无解。否则对每个起点i，用双指针求最远合法右端R[i]；反复均匀随机右端直到合法，相当于在i..R[i]中均匀选一个。\n\nE[i]=1+Σ(j=i..R[i])E[j+1]/(R[i]−i+1)，E[n+1]=0。倒序维护E的后缀和，把转移和化为常数时间。每问重新跑双指针和线性DP即可。',
        r'''int n,m; cin >> n >> m; vector<long long> a(n+1); long long maximum=0; for (int i=1;i<=n;i++) { cin >> a[i]; maximum=max(maximum,a[i]); } cout << fixed << setprecision(2); while (m--) { long long x; cin >> x; if (x<maximum) { cout << "YNOI is good OI!\n"; continue; } vector<int> right(n+1); int r=0; long long sum=0; for (int l=1;l<=n;l++) { while (r<n && sum+a[r+1]<=x) sum+=a[++r]; right[l]=r; sum-=a[l]; } vector<long double> suffix(n+3); long double answer=0; for (int i=n;i>=1;i--) { answer=1+(suffix[i+1]-suffix[right[i]+2])/(right[i]-i+1); suffix[i]=suffix[i+1]+answer; } cout << answer << '\n'; }''',
        '数组允许0，双指针条件仍是≤x。随机失败只是重新选，不增加段数。',
        floating_output=True,complexity=r'每次询问 $O(n)$，总 $O(nm)$，空间 $O(n)$。')
    put(210515,2300,['树上期望','高斯消元思想'],'树上随机游走、传回根或出口，求离开前走边次数期望。',
        '设E[u]为从u出发的剩余期望边数，k、e为传送和出口概率，q=1−k−e，t=q/degree。方程E[u]=kE[root]+q+t*ΣE[v]，传送不算走边。\n\n以1为根消元，把非根子树表示成E[u]=A[u]E[parent]+B[u]E[root]+C[u]。代入儿子表达式，den=1−t*ΣA[child]，A=t/den、B=(k+tΣB)/den、C=(q+tΣC)/den。根没有父项，最终E[root]=C[root]/(1−B[root])。用后序一次完成树形消元。\n\n先标出实际可达节点：只有q>0的节点能继续走向儿子。若可达节点没有任何正出口概率，必定无法离开，输出impossible；不可达子树不参与消元，避免无关方程的奇异性。',
        r'''int n; cin >> n; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } vector<long double> teleport(n+1),exit(n+1),walk(n+1); for (int i=1;i<=n;i++) { long double k,e; cin >> k >> e; teleport[i]=k/100; exit[i]=e/100; walk[i]=(100-k-e)/100; } tree.root(1); vector<bool> active(n+1); active[1]=true; bool possible=false; for (int u:tree.order) if (active[u]) { possible=possible||exit[u]>0; if (walk[u]>0) for (int v:tree.edge[u]) if (tree.parent[v]==u) active[v]=true; } if (!possible) { cout << "impossible"; return 0; } vector<long double> a(n+1),b(n+1),c(n+1); for (int i=n-1;i>=0;i--) { int u=tree.order[i]; if (!active[u]) continue; long double sa=0,sb=0,sc=0,t=walk[u]/tree.edge[u].size(); for (int v:tree.edge[u]) if (tree.parent[v]==u && active[v]) { sa+=a[v]; sb+=b[v]; sc+=c[v]; } long double denominator=1-t*sa; a[u]=u==1?0:t/denominator; b[u]=(teleport[u]+t*sb)/denominator; c[u]=(walk[u]+t*sc)/denominator; } cout << fixed << setprecision(12) << c[1]/(1-b[1]);''',
        '出口和传送不增加边数，只有实际走边事件贡献q。树边是双向，必须保留父项再消元。',
        declarations=EULER,floating_output=True,complexity=r'时间、空间均 $O(n)$。')
    put(205461,1500,['独立事件','补事件','模逆元'],'每个卡池抽一次，求至少抽到一张想要卡的概率。',
        '卡池i不出想要卡的概率为(a[i]−b[i])/a[i]。独立抽取时全部落空概率是这些分数乘积，所以答案为1−Π(a−b)/Πa。分别累乘分子、分母，最后只用一次快速幂求分母逆元。',
        r'''int n; cin >> n; const long long mod=1000000007; vector<long long> a(n); long long denominator=1,numerator=1; for (auto &x:a) { cin >> x; denominator=denominator*x%mod; } for (int i=0;i<n;i++) { long long b; cin >> b; numerator=numerator*(a[i]-b)%mod; } long long inverse=1,exponent=mod-2; while (exponent) { if (exponent&1) inverse=inverse*denominator%mod; denominator=denominator*denominator%mod; exponent>>=1; } cout << (1-numerator*inverse%mod+mod)%mod;''',
        '题意是至少一个池成功，样例也对应补事件；不是所有池都成功。a[i]<P且非零，分母必可逆。',
        complexity=r'时间 $O(n+\log P)$，空间 $O(n)$。')
    put(232848,2100,['概率DP'],'P先抽，D抽黑后会多带出一个球，求P先抽到白球概率。',
        'f[w][b]为轮到P、袋内有w白b黑时P获胜概率。P直接抽白贡献w/(w+b)。若P与D都抽黑，概率b/(w+b)*(b−1)/(w+b−1)，再由D带出一球：带黑转f[w][b−3]，带白转f[w−1][b−2]，按剩余球比例加权。D抽到白则P失败，不加贡献。w=0时恒0，b=0且w>0时恒1。按w、b升序计算。',
        r'''int w,b; cin >> w >> b; vector<vector<long double>> dp(w+1,vector<long double>(b+1)); for (int white=1;white<=w;white++) for (int black=0;black<=b;black++) { long double total=white+black; dp[white][black]=white/total; if (black>=2) { long double reach=black/total*(black-1)/(total-1),remaining=total-2; if (black>=3) dp[white][black]+=reach*(black-2)/remaining*dp[white][black-3]; dp[white][black]+=reach*white/remaining*dp[white-1][black-2]; } } cout << fixed << setprecision(12) << dp[w][b];''',
        '带出白球不算D抽到白球，但会减少下一轮白球数。空袋判D赢，所以dp[0][0]=0。',
        floating_output=True,complexity=r'时间、空间均 $O(wb)$。')
    put(232849,1700,['期望线性性','连续段'],'独立O/X序列，每段连续O长度平方，求分数期望。',
        '设上一位置末尾连续O长度为L，本次成功会把对应段贡献从L²变成(L+1)²，增量2L+1；失败时总分不变、末尾长度清零。只维护末尾长度期望len：本次分数期望增加p*(2len+1)，之后len=p*(len+1)。利用期望线性性，不需要二阶矩。',
        r'''int n; cin >> n; long double length=0,answer=0; while (n--) { long double p; cin >> p; answer+=p*(2*length+1); length=p*(length+1); } cout << fixed << setprecision(12) << answer;''',
        '先用旧len计算分数增量，再更新len。失败不会扣除此前已获得的连续段分数。',
        floating_output=True,complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(232850,2200,['状压DP','全概率公式'],'鱼随机两两相遇并互食，求每条鱼最后存活概率。',
        'dp[mask]为当前存活集合恰是mask的概率，初始全体为1。集合有k条鱼时，每个无序鱼对相遇概率为1/C(k,2)。枚举集合中的i<j，按a[i][j]转移到删j的集合，按a[j][i]转移到删i的集合。删位后掩码严格变小，按掩码倒序即可保证前驱先处理。最终dp[1<<i]就是i独活概率。',
        r'''int n; cin >> n; vector<vector<long double>> a(n,vector<long double>(n)); for (auto &row:a) for (auto &x:row) cin >> x; int size=1<<n; vector<long double> dp(size); dp[size-1]=1; for (int mask=size-1;mask>=1;mask--) { int count=__builtin_popcount((unsigned)mask); if (count<2) continue; long double pairProbability=dp[mask]*2/(count*(count-1)); for (int bits=mask;bits;bits&=bits-1) { int i=__builtin_ctz((unsigned)bits); int others=mask&~((1<<(i+1))-1); for (;others;others&=others-1) { int j=__builtin_ctz((unsigned)others); dp[mask^(1<<j)]+=pairProbability*a[i][j]; dp[mask^(1<<i)]+=pairProbability*a[j][i]; } } } cout << fixed << setprecision(10); for (int i=0;i<n;i++) cout << dp[1<<i] << (i+1==n?'\n':' ');''',
        '相遇的是无序对，不能再次乘2。只从当前存活鱼中选择；n=1初始状态就是最终状态。',
        floating_output=True,complexity=r'时间 $O(n^2 2^n)$，空间 $O(2^n+n^2)$。')


if __name__ == '__main__': run()
