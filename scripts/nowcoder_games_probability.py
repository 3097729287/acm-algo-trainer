"""Game invariants, capped probability DP and independent matrix applications."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_matrix_support import MATRIX


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(19832,2000,['动态规划','相邻交换'],'两种颜色各含1到n的球，最少相邻交换让各自编号递增。',
        '合法结果是白球递增序列和黑球递增序列的任意交错。构造最终顺序，每次只能选下一白球或下一黑球。将它从原序列尚未取出的部分移到最前，需要交换的次数就是它前面剩余球数；逐次这样抽取恰好计算该最终顺序相对原序列的逆序数。\n\ndp[i][j]为取走前i个白球、前j个黑球的最小代价。白i的同色贡献固定为“原来在它前面且编号更大的白球数”，异色贡献为前面编号大于j的黑球数。黑球同理。外层递增i时，维护每个黑球前仍未取的球数；内层递增j时滚动扣除已取黑球对白i的贡献。于是每个状态常数时间，dp只保留一行。',
        r'''int n; cin >> n; vector<int> white(n+1), black(n+1); for (int p = 0; p < 2*n; p++) { char color; int label; cin >> color >> label; (color == 'W' ? white : black)[label] = p; } vector<int> fixedWhite(n+1), blackCost(n+1); for (int i = 1; i <= n; i++) { for (int j = i+1; j <= n; j++) { fixedWhite[i] += white[j] < white[i]; blackCost[i] += black[j] < black[i]; } for (int j = 1; j <= n; j++) blackCost[i] += white[j] < black[i]; } vector<long long> dp(n+1); for (int j = 1; j <= n; j++) dp[j] = dp[j-1] + blackCost[j]; for (int i = 1; i <= n; i++) { int whiteCost = fixedWhite[i]; for (int j = 1; j <= n; j++) { whiteCost += black[j] < white[i]; if (white[i] < black[j]) blackCost[j]--; } long long old = dp[0]; dp[0] = old + whiteCost; for (int j = 1; j <= n; j++) { whiteCost -= black[j] < white[i]; old = dp[j]; dp[j] = min(old + whiteCost,dp[j-1] + blackCost[j]); } } cout << dp[n];''',
        '同色编号顺序固定，只有两色之间的交错可选。向右更新时dp[j]仍是上一行，dp[j−1]已经是当前行。',
        complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(20661,1900,['矩阵快速幂','递推前缀和'],'同时维护二阶非齐次递推f和累加f及n²的g。',
        '状态用[g[i],f[i],f[i−1],i²,i,1]。f[i+1]=2f[i]+3f[i−1]+i+1；g[i+1]=g[i]+f[i+1]+(i+1)²，故第一行系数为[1,2,3,1,3,2]。其余行表示新f、旧f、(i+1)²、i+1、1。i=2时f=2、f[1]=1、g=2+2+4=8。预处理64个矩阵幂，每组按n−2作用到初始向量。',
        r'''Matrix transition = {{1,2,3,1,3,2},{0,2,3,0,1,1},{0,1,0,0,0,0},{0,0,0,1,2,1},{0,0,0,0,1,1},{0,0,0,0,0,1}}; vector<Matrix> powers(32); powers[0] = transition; for (int b = 1; b < 32; b++) powers[b] = multiply(powers[b-1],powers[b-1]); unsigned long long n; while (cin >> n && n) { if (n == 1) { cout << 2 << '\n'; continue; } vector<long long> state = {8,2,1,4,2,1}; unsigned long long exponent = n-2; for (int b = 0; exponent; b++,exponent >>= 1) if (exponent & 1) state = applyMatrix(powers[b],state); cout << state[0] << '\n'; }''',
        '输入0表示终止，不能输出第0项。f的给定初始项不满足一般递推，必须从第2项启动。',
        declarations=MATRIX,complexity=r'预处理 $O(6^3\log U)$；每组 $O(6^2\log n)$，空间 $O(6^2\log U)$。')
    put(20909,1900,['矩阵快速幂','有向图路径计数'],'给定朋友有向图，批量询问恰好m次传球从a到b的方案数。',
        '邻接矩阵A[i][j]表示一步从i到j的方案数。矩阵乘法按中间接球者k枚举，故A^m[i][j]恰好是走m条边的方案数。m对所有询问相同，先用快速幂计算整个矩阵，再每问常数时间取值。m=0时单位矩阵表示不传球。',
        r'''int q,n; unsigned long long m; cin >> q >> n >> m; Matrix base(n,vector<long long>(n)), answer(n,vector<long long>(n)); for (auto &row : base) for (auto &x : row) { cin >> x; x = x != 0; } for (int i = 0; i < n; i++) answer[i][i] = 1; while (m) { if (m & 1) answer = multiply(answer,base); m >>= 1; if (m) base = multiply(base,base); } while (q--) { int a,b; cin >> a >> b; cout << answer[a-1][b-1] << '\n'; }''',
        '朋友关系有向，不能对称补边；恰好m步与至多m步不同。每人每轮必须传球，不额外加入自环。',
        declarations=MATRIX,complexity=r'时间 $O(n^3\log(m+1)+Q)$，空间 $O(n^2)$。')
    put(223888,1700,['对称策略','博弈'],'交替给网格空格染两色，相邻同色禁止，不能染色者输。',
        '若n、m均为奇数，先手先染中心格；此后把后手的每次落点绕中心旋转180度，在对应格染相同颜色。成对格不相邻，既有图案保持同色中心对称，所以回应始终合法。\n\n否则没有固定中心格，后手始终在先手落点的中心对称格染相反颜色。已有图案保持反色中心对称，相邻约束也被保持；即便这一对格互相相邻，反色仍合法。故只有n、m均奇数时先手赢。',
        r'''long long n,m; cin >> n >> m; cout << ((n % 2 && m % 2) ? "akai" : "yukari");''',
        '奇数尺寸时中心格必须先占，否则对称回应缺少起点。偶数情形使用反色，兼顾对称格恰好相邻。',
        complexity=r'时间、空间均 $O(1)$。')
    put(26212,1800,['策略窃取','反常博弈'],'取x后连续取其二分祖先直到缺失，拿走最后一个数者输。',
        'n=1时只能取最后一个，先手输。n>1时考虑先取1后的非空局面S：若S是必败局面，先取1就能赢；若S是必胜局面，设S中某个获胜首步选x。原局面直接选同一个x，沿祖先链到1后也恰好得到相同后继，因为S只是预先拿掉了1。因此原局面仍有一步通向必败局面。\n\n反常规则下取空是输，这个论证仍成立：S的获胜步不会直接取空，所以原局面的对应步也不会直接取空。于是所有n>1均先手胜。',
        r'''long long n; cin >> n; cout << (n == 1 ? "Yang" : "Shi");''',
        '不能把“取最后一个输”误当普通Nim。证明依赖1属于所有祖先链，并且n>1时取1后仍非空。',
        complexity=r'时间、空间均 $O(1)$。')
    put(18388,2000,['SG函数','Nim和','约数枚举'],'每次从某堆取其当前石子数的一个约数，统计先手获胜首步数。',
        '一堆m的SG值为v₂(m)+1，空堆为0。证明按m归纳：令r=v₂(m)。取约数d时，若v₂(d)<r，剩余数的二进赋值恰为v₂(d)，产生SG值1..r；取d=m得到0。若v₂(d)=r且未取空，剩余数赋值大于r，SG值大于r+1。因此0..r都可达，r+1不可达，mex正好是r+1。\n\n所有堆的SG异或为X。枚举每种堆大小m的每个约数d，如果X xor SG(m) xor SG(m−d)=0，这一取法获胜，贡献该大小堆的出现次数。按d的倍数枚举m就能遍历全部约数对。',
        r'''int n; cin >> n; const int limit = 100000; vector<int> frequency(limit+1), sg(limit+1); for (int m = 1; m <= limit; m++) sg[m] = __builtin_ctz((unsigned)m) + 1; int total = 0, maximum = 0; while (n--) { int x; cin >> x; frequency[x]++; total ^= sg[x]; maximum = max(maximum,x); } long long answer = 0; for (int d = 1; d <= maximum; d++) for (int m = d; m <= maximum; m += d) if (frequency[m] && (total ^ sg[m] ^ sg[m-d]) == 0) answer += frequency[m]; cout << answer;''',
        '不同堆即使大小相同也算不同首步，所以乘出现次数。不能对0调用ctz，sg[0]单独保留0。',
        complexity=r'时间 $O(U\log U+n)$，空间 $O(U)$。')
    put(15065,1600,['对称策略'],'圆上取一个或原本相邻两个石子，取完者胜。',
        'n≤2时先手直接取光。n≥3时先手取一个或两个后，剩下的一定是一条长度至少1的链。后手取链中心的一个（奇长）或两个（偶长），使两侧成为等长的两条链。之后把对方每一步在另一侧镜像重复，始终有合法回应并拿到最后的石子。因此n≥3后手胜。',
        r'''long long n; while (cin >> n) cout << (n <= 2 ? "XiaoNiu\n" : "XiaoKe\n");''',
        '取走石子后留下的空位不会让原本不相邻的石子变相邻，所以两条链可独立镜像。',
        complexity=r'每组时间、空间均 $O(1)$。')
    put(18993,1800,['博弈','贪心'],'双方轮流选同一组列位置，各取自己那一行硬币，比较得到的二进制串。',
        '把每列分成UU、UD、DU、DD。当前位优先取U；同为U时优先UU，因为还能阻止对手获得一个U。自己没有U时优先拿走对手的U。这三条优先级可通过交换首个不同选择证明：不降低自己的当前位，同时只减少对手未来可取的1。\n\n设UU有c个、UD有a个、DU有b个。双方先轮流消耗UU。c为偶数时回到先手轮，双方再各自取独有U：a>b先手胜；a=b平局；a<b时先手先耗尽，但还能取走对手一个DU，所以b=a+1也平局，b≥a+2才后手胜。\n\nc为奇数时，后手必须先取一个DU来匹配先手刚取得的最后一个UU，否则立刻输；取后等价于偶数情况中把b减1。统一令d=a−b+(c mod 2)：d>0先手胜，d=0或−1平局，d<−1后手胜。',
        r'''int n; string a,b; cin >> n >> a >> b; int both = 0, first = 0, second = 0; for (int i = 0; i < 2*n; i++) { if (a[i] == 'U' && b[i] == 'U') both++; else if (a[i] == 'U') first++; else if (b[i] == 'U') second++; } int difference = first - second + (both % 2); if (difference > 0) cout << "clccle trl!"; else if (difference < -1) cout << "sarlendy tql!"; else cout << "orz sarlendy!";''',
        '每选一列就同时占用双方对应位置，不是从两行任取一枚。相等时输出指定平局字符串。',
        complexity=r'时间 $O(n)$，空间 $O(n)$ 存输入。')
    put(19156,1700,['不变量','操作次数奇偶'],'奇堆可分成两堆，偶堆两堆可合并，不能操作者输。',
        '奇数分裂后恰有一奇一偶，奇堆的总数不变；每次分裂新增一个偶堆，每次合并减少一个偶堆。终局所有奇堆都是1，偶堆至多一个。若最初至少有偶堆，或存在大于1的奇堆，过程中必出现偶堆，终局恰剩一个。\n\n设初始偶堆E，分裂S次，则合并E+S−1次，总步数2S+E−1，奇偶仅由E决定。E为偶数时总步数奇，先手胜；E为奇数时后手胜。若所有堆都是1，则没有任何操作，直接后手胜。',
        r'''int n; cin >> n; int even = 0; bool activeOdd = false; while (n--) { int x; cin >> x; if (x % 2 == 0) even++; else if (x > 1) activeOdd = true; } cout << ((even % 2 == 0 && (even > 0 || activeOdd)) ? "Alice" : "Bob");''',
        '分裂次数可以不同，但总步数奇偶固定。全是1时不能套用终局存在一个偶堆的公式。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(50614,1000,['巴什博弈'],'一堆N石子，每步取1到K，取完者胜。',
        '0是必败态。若剩余量是K+1的倍数，任何一步都会离开倍数；否则可取余数使对手面对倍数。之后对手取x，就取K+1−x回应。因此N mod(K+1)=0时后手胜，其余先手胜。',
        r'''int n,k; cin >> n >> k; cout << (n % (k+1) ? 1 : 2);''',
        '这是最后取者胜的规则，取值范围包含K。',
        complexity=r'时间、空间均 $O(1)$。')
    put(50615,1200,['Nim博弈'],'每次从一堆取任意正数石子，判断先手胜负。',
        '全部堆大小的异或X为0时，改变任一堆都会使异或非0；X非0时，取最高置位所在的一堆a，把它减为a xor X，该数小于a，且使总异或变0。故先手胜当且仅当异或非0。',
        r'''int n; cin >> n; int total = 0; while (n--) { int x; cin >> x; total ^= x; } cout << (total ? "win" : "lose");''',
        '每次只能改一堆，不能用总石子数奇偶判断。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(19325,1800,['不变量','三进制势能'],'三人轮流把左上矩形按R→G→B→R变色，选点必须非B，求最终不能操作的人。',
        '每次操作必包含左上角，所以它每步都沿R→G→B→R变化。终局全B，因此总操作数L模3仅由初始左上角决定：R需2步、G需1步、B需0步。下一位即失败者，分别为dreagonm、fengxunling、BLUESKY007。\n\n还需确认不会无限循环：把格子按从右下到左上的行优先顺序作为三进制位，令R=2、G=1、B=0，越靠右下权越高。选中格是本次影响范围内权最高的格，它从2降1或1降0，所有更高位不变，因此整个势能严格下降。游戏必结束，策略不影响失败者。',
        r'''int tests; cin >> tests; while (tests--) { int n,m; cin >> n >> m; string row; char first = 'B'; for (int i = 0; i < n; i++) { cin >> row; if (i == 0) first = row[0]; } if (first == 'R') cout << "dreagonm\n"; else if (first == 'G') cout << "fengxunling\n"; else cout << "BLUESKY007\n"; }''',
        '左上角一开始为B并不表示立即结束，但最终总步数必为3的倍数。',
        complexity=r'读入时间 $O(nm)$，空间 $O(m)$。')
    put(18389,2100,['概率DP','期望线性性'],'客户独立决定是否投资，筹足L才赚M并支付分红，求期望净利润模P。',
        '将筹资金额压到0..L，L代表已筹足。f[j]是金额状态概率，g[j]是该状态下“分红总额乘概率”的和。客户投资概率p、分红c=m*r时，不投转移(f,g)*(1−p)，投资转移到min(L,j+m)，增加(p*f,p*(g+c*f))。每人使用新数组，避免同一客户重复选择。\n\n最后只有L状态产生收益，期望为M*f[L]−g[L]。概率和利率都用整数乘100的模逆元表示，不用浮点。',
        r'''int n,l; long long profit; cin >> n >> l >> profit; constexpr long long mod = 1000000007, inv100 = 570000004; vector<long long> probability(l+1), payout(l+1); probability[0] = 1; while (n--) { int money,rate,percent; cin >> money >> rate >> percent; long long p = percent * inv100 % mod, q = (1-p+mod)%mod, cost = 1LL * money * rate % mod * inv100 % mod; vector<long long> nextProbability(l+1), nextPayout(l+1); for (int j = 0; j <= l; j++) { int to = min(l,j+money); nextProbability[j] = (nextProbability[j]+probability[j]*q)%mod; nextPayout[j] = (nextPayout[j]+payout[j]*q)%mod; nextProbability[to] = (nextProbability[to]+probability[j]*p)%mod; nextPayout[to] = (nextPayout[to]+(payout[j]+cost*probability[j]%mod)%mod*p)%mod; } probability.swap(nextProbability); payout.swap(nextPayout); } cout << (profit*probability[l]%mod-payout[l]+mod)%mod;''',
        '筹资超额仍应支付全部投资者分红，所以只能压缩金额，不能截断分红。失败筹资不产生题目指定的成功分红。',
        complexity=r'时间 $O(nL)$，空间 $O(L)$。')
    put(19777,1400,['几何分布','期望'],'N种卡中M种稀有，已抽过的稀有从池中移除，求集齐K种的期望次数。',
        '已收集i种稀有时，抽卡池剩N−i种，稀有剩M−i种，下一次获得新稀有的概率为(M−i)/(N−i)。几何分布等待次数期望是其倒数，所以总期望Σ(i=0..K−1)(N−i)/(M−i)。普通卡会重复，不能从抽卡池删掉。',
        r'''int tests; cin >> tests; cout << fixed << setprecision(10); for (int tc = 1; tc <= tests; tc++) { int n,m,k; cin >> n >> m >> k; long double answer = 0; for (int i = 0; i < k; i++) answer += (long double)(n-i)/(m-i); cout << "Case #" << tc << ": " << answer << '\n'; }''',
        '分母随已收集稀有卡数量变化，分子也变化；不是固定池的优惠券模型。',
        floating_output=True,complexity=r'每组时间 $O(K)$，空间 $O(1)$。')
    put(15532,1700,['几何概率'],'从随机起点顺时针依次打两个随机点，求总路程至少k的概率。',
        '以起点为0，两个打卡点距离为独立均匀变量u、v∈(0,x)。若u<v，路程为v；否则先走到u再绕圈到v，路程为x+v。在正方形(u,v)中按v积分：k≤x时，不达标区域面积为k²/2，概率1−k²/(2x²)；x<k<2x时，达标区域面积为(2x−k)²/2，概率为该面积除x²；k≥2x为0。',
        r'''int tests; cin >> tests; cout << fixed << setprecision(2); while (tests--) { long double k,x; cin >> k >> x; long double answer; if (k <= x) answer = 1-k*k/(2*x*x); else if (k < 2*x) answer = (2*x-k)*(2*x-k)/(2*x*x); else answer = 0; cout << answer << '\n'; }''',
        '经过第二点不算完成第二次打卡，必须先到第一点。计算平方前转浮点，最后按题意保留两位。',
        floating_output=True,complexity=r'每组时间、空间均 $O(1)$。')
    put(16610,1800,['质因数分解','指数约束'],'统计gcd(x,a0)=a1且lcm(x,b0)=b1的正整数x。',
        'x必为b1约数。分解b1，对每个质因子p枚举x的指数e=0..v_p(b1)，只保留min(e,v_p(a0))=v_p(a1)、max(e,v_p(b0))=v_p(b1)的指数。各素因子独立，可选指数数相乘。若a1不整除b1，直接无解；如此a0中不在b1里的质因子必不在a1中，不会产生额外约束。',
        r'''const int limit = 44722; vector<bool> composite(limit+1); vector<int> primes; for (int p = 2; p <= limit; p++) if (!composite[p]) { primes.push_back(p); if (1LL*p*p <= limit) for (int x = p*p; x <= limit; x += p) composite[x] = true; } int tests; cin >> tests; while (tests--) { long long a0,a1,b0,b1; cin >> a0 >> a1 >> b0 >> b1; if (b1 % a1) { cout << 0 << '\n'; continue; } long long remaining = b1, answer = 1; auto consume = [&](long long p) { auto exponent = [&](long long x) { int result = 0; while (x % p == 0) { result++; x /= p; } return result; }; int aa = exponent(a0), ab = exponent(a1), ba = exponent(b0), bb = exponent(b1), choices = 0; for (int e = 0; e <= bb; e++) if (min(e,aa) == ab && max(e,ba) == bb) choices++; answer *= choices; while (remaining % p == 0) remaining /= p; }; for (int p : primes) { if (1LL*p*p > remaining) break; if (remaining % p == 0) consume(p); } if (remaining > 1) consume(remaining); cout << answer << '\n'; }''',
        '不用逐个枚举x或b1的全部因子。最后残留的大素因子也要处理；题目已保证a1|a0、b0|b1。',
        complexity=r'预筛 $O(U\log\log U)$；每组 $O(\pi(\sqrt {b1})+\log(a0b1))$，空间 $O(U)$。')
    put(16414,1500,['裴蜀定理','数论'],'互素面值a、b，求非负组合无法表示的最大金额。',
        '答案ab−a−b。若它能写成ax+by，移项得a(x+1)=b(a−y−1)，互素迫使x+1为b倍数，从而ax≥a(b−1)>ab−a−b，矛盾。\n\n对任意N>ab−a−b，由于b在模a下可逆，存在y∈[0,a−1]使by≡N(mod a)。令x=(N−by)/a，它是整数；又N−by>ab−a−b−b(a−1)=−a，所以x>−1，必有x≥0。于是所有更大金额可表示。',
        r'''long long a,b; cin >> a >> b; cout << a*b-a-b;''',
        '互素是公式前提，原题保证；乘积需64位。若面值1存在则没有无法支付金额，原题的存在性保证已排除。',
        complexity=r'时间、空间均 $O(1)$。')
    put(16429,1600,['组合数','二维前缀和'],'批量统计矩形范围内被k整除的组合数C(i,j)。',
        '先用Pascal递推模k得到C(i,j)余数，余数为0就标记1。只在j≤i处标记，三角形外无组合数，不能当成0计入。对标记做二维前缀和，询问[0,n]×[0,m]直接取prefix[n][m]，前缀表自动只包含合法三角区。',
        r'''int tests,k; cin >> tests >> k; const int limit = 2000; vector<vector<int>> prefix(limit+1,vector<int>(limit+1)); vector<int> row(limit+1); row[0] = 1 % k; for (int i = 0; i <= limit; i++) { if (i) for (int j = i; j >= 1; j--) row[j] = (row[j]+row[j-1])%k; for (int j = 0; j <= limit; j++) { int flag = j <= i && row[j] == 0; prefix[i][j] = flag + (i ? prefix[i-1][j] : 0) + (j ? prefix[i][j-1] : 0) - (i && j ? prefix[i-1][j-1] : 0); } } while (tests--) { int n,m; cin >> n >> m; cout << prefix[n][m] << '\n'; }''',
        'k可能为合数，不能用阶乘逆元计算组合数。Pascal内层倒序。',
        complexity=r'预处理 $O(U^2)$，每问 $O(1)$，空间 $O(U^2)$。')
    put(17873,1400,['裴蜀定理','循环群'],'可反复加给定正整数，求模m后可达余数数量。',
        '令g=gcd(m,a1,...,an)。任何组合都是g倍数，因此只有m/g个候选余数。裴蜀定理保证整数线性组合能得到g；负系数在模m下也能改为非负，因为加a共m次回到同一余数。因此所有g倍数余数都可达，答案m/g，包括初始余数0。',
        r'''int n; long long m; cin >> n >> m; long long g = m; while (n--) { long long a; cin >> a; g = gcd(g,a); } cout << m/g;''',
        '可达余数包含0，操作次数允许为0。不是只求a之间的gcd，还要把模数m加入。',
        complexity=r'时间 $O(n\log m)$，空间 $O(1)$。')


if __name__ == '__main__': run()
