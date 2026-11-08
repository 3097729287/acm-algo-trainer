"""Inclusion-exclusion and matrix transitions, with every original input reviewed."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_matrix_support import MATRIX, FIB

POWER = r'''
constexpr long long mod = 1000000007;
long long power(long long a,long long b) {
    long long result = 1;
    while (b) { if (b & 1) result = result * a % mod; a = a * a % mod; b >>= 1; }
    return result;
}
'''


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(15079,1300,['容斥原理'],'求1到n中不被2、5、11、13整除的数的数量，多组至10^18。',
        '从全部n个数出发，对非空质数子集做容斥。子集中每个质数都整除的数，共有floor(n/子集乘积)个。奇数大小子集减去，偶数大小子集加回；只有15个子集，所有乘积至1430。',
        r'''long long n; const int prime[] = {2,5,11,13}; while (cin >> n) { long long answer = n; for (int mask = 1; mask < 16; mask++) { int product = 1; for (int i = 0; i < 4; i++) if (mask >> i & 1) product *= prime[i]; if (__builtin_popcount((unsigned)mask) & 1) answer -= n / product; else answer += n / product; } cout << answer << '\n'; }''',
        '输入一直读到EOF。n及答案使用64位，不能只减四种倍数而忽略交集。',
        complexity=r'每组时间 $O(2^4\cdot4)$，空间 $O(1)$。')
    put(16513,1700,['容斥原理','溢出判断'],'求[L,R]内不被集合中任一素数整除的数的数量。',
        '定义F(x)统计1..x内没有任何给定素因子的数，答案F(R)−F(L−1)。枚举质数子集并按奇偶容斥，交集大小为x/子集乘积。递归增加下标，若当前乘积已经大于x/下一个质数，则新交集及其全部扩展都为空，直接跳过，并避免64位乘法溢出。',
        r'''long long l,r; int k; cin >> l >> r >> k; vector<long long> prime(k); for (auto &p : prime) cin >> p; sort(prime.begin(),prime.end()); auto count = [&](long long x) { long long result = x; auto dfs = [&](auto &&self,int start,long long product,int sign) -> void { for (int i = start; i < k; i++) { if (product > x / prime[i]) break; long long next = product * prime[i]; result += sign * (x / next); self(self,i+1,next,-sign); } }; dfs(dfs,0,1,-1); return result; }; cout << count(r) - count(l-1);''',
        '集合元素保证是不同素数，交集的最小公倍数才等于乘积。L=1时F(0)=0，递归自然不进入。',
        complexity=r'最坏时间 $O(2^k)$，递归空间 $O(k)$。')
    put(20189,1900,['容斥原理','隔板法'],'多种同类物品不可区分，分给n名有区别同学，人人至少一个。',
        '先允许空手。若只给s名指定同学，第j种a[j]件的非负分配数由隔板法得到C(a[j]+s−1,s−1)，不同种相乘。容斥选择k名空手者：答案Σ(-1)^k*C(n,k)*ΠC(a[j]+n−k−1,n−k−1)。对s≥1枚举，s=0仅当所有物品总数为0时有1种；n≥1且物品全0直接答案0。预处理不超过1999的阶乘、逆阶乘。',
        r'''int n,m; cin >> n >> m; vector<int> amount(m); long long total = 0; int maximum = 0; for (int &a : amount) { cin >> a; total += a; maximum = max(maximum,a); } if (!total) { cout << 0; return 0; } int limit = n + maximum; vector<long long> factorial(limit + 1,1), inverse(limit + 1); for (int i = 1; i <= limit; i++) factorial[i] = factorial[i-1] * i % mod; inverse[limit] = power(factorial[limit],mod-2); for (int i = limit; i >= 1; i--) inverse[i-1] = inverse[i] * i % mod; auto choose = [&](int a,int b) { return factorial[a] * inverse[b] % mod * inverse[a-b] % mod; }; long long answer = 0; for (int empty = 0; empty < n; empty++) { int students = n - empty; long long ways = choose(n,empty); for (int a : amount) ways = ways * choose(a+students-1,students-1) % mod; answer = (answer + (empty % 2 ? mod - ways : ways)) % mod; } cout << answer;''',
        '同类特产不可区分，不应给每件物品贴编号。容斥选的是同学集合，必须乘C(n,k)。',
        declarations=POWER,complexity=r'时间 $O(nm+n+\max a+\log P)$，空间 $O(n+m+\max a)$。')
    if 'nowcoder-global::251592' not in existing:
        reviewed_clone(251592,124160,'逐段核对圆上青蛙的步长、占领并集、编号之和、T≤20和全部三组样例，确认与已修复原PDF为同一题。')
    put(19857,2200,['容斥原理','递推','圆排列'],'n对情侣围圆桌而坐，任何一对不相邻，旋转视为相同，n至三千万。',
        'n≥2时，容斥选k对必须相邻，把每对合成块并考虑两种方向，得到c[n]=Σ(-2)^k*C(n,k)*(2n−k−1)!。直接算组合数会使用大数组，下面把此式化为常数空间递推。\n\n同时定义直线排列计数l[n]=Σ(-2)^k*C(n,k)*(2n−k)!。为推导，记q=t(t−2)，用∫₀∞e^(−t)t^r dt=r!将两式分别写成c[n]=∫e^(−t)q^n/t、l[n]=∫e^(−t)q^n。对q^n及t*q^n分部积分，令B[n]=∫e^(−t)t*q^n，得到l[n]=2n*(B[n−1]−l[n−1])、B[n]=(2n+1)l[n]+2n*B[n−1]。再用c[n]=B[n−1]−2l[n−1]消去B，便有：\n\nl[n]=2n*(c[n]+l[n−1])；c[n+1]=4n²*c[n]+2n(2n+1)*l[n−1]。\n\n从形式容斥值c[1]=−1、l[0]=1开始滚动。c[1]只是递推初值；真实n=1仅两个人，必然相邻，答案单独输出0。每步都在模数下计算系数，再乘旧状态。',
        r'''int n; cin >> n; if (n == 1) { cout << 0; return 0; } constexpr long long mod = 1000000007; long long circle = mod - 1, previousLine = 1; for (long long i = 1; i < n; i++) { long long coefficientA = (4 * i % mod) * i % mod; long long coefficientB = (2 * i % mod) * ((2 * i + 1) % mod) % mod; long long nextCircle = (coefficientA * circle + coefficientB * previousLine) % mod; long long line = (2 * i % mod) * ((circle + previousLine) % mod) % mod; circle = nextCircle; previousLine = line; } cout << circle;''',
        '圆桌只把旋转视为相同，镜像仍不同。初值−1是代数辅助量，不是n=1的实际方案数。4n²先取模，再乘状态，避免溢出。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(15069,2100,['Burnside引理','欧拉函数','快速幂'],'n种颜色长度m的环，旋转和翻转等价，求不同方案数。',
        '对二面体群的2m种对称使用Burnside：答案为所有对称操作固定的着色数之和除以2m。旋转i格有gcd(i,m)个循环，贡献n^gcd(i,m)。按d=m/gcd(i,m)分组，旋转贡献Σ(d|m)phi(d)*n^(m/d)。\n\nm为奇数时，每个翻转有1个不动点和(m−1)/2对位置，共m*n^((m+1)/2)。m为偶数时，一半翻转穿过两个位置，另一半穿过两条缝，贡献(m/2)*(n^(m/2+1)+n^(m/2))。最后乘(2m)的模逆元。预筛phi至10000，每组只枚举m的约数。',
        r'''const int limit = 10000; vector<int> phi(limit + 1); iota(phi.begin(),phi.end(),0); for (int p = 2; p <= limit; p++) if (phi[p] == p) for (int x = p; x <= limit; x += p) phi[x] = phi[x] / p * (p-1); int tests; cin >> tests; while (tests--) { long long n,m; cin >> n >> m; long long sum = 0; auto addDivisor = [&](int d) { sum = (sum + phi[d] * power(n,m/d)) % mod; }; for (int d = 1; d * d <= m; d++) if (m % d == 0) { addDivisor(d); if (d * d != m) addDivisor(m/d); } if (m & 1) sum = (sum + m * power(n,(m+1)/2)) % mod; else sum = (sum + (m/2) * ((power(n,m/2)+power(n,m/2+1)) % mod)) % mod; cout << sum * power(2*m,mod-2) % mod << '\n'; }''',
        '偶数长度的两类翻转不能合并成同一指数。m=1或2时，仍按群操作计重平均，公式照常成立。',
        declarations=POWER,complexity=r'预筛 $O(U\log\log U)$；每组 $O(\sqrt m+\tau(m)\log m+\log P)$，空间 $O(U)$。')
    put(14607,1600,['递推','待定系数','快速幂'],'a[0]=0，a[n]=2a[n−1]+n²，n至10^18。',
        '寻找二次多项式特解P(n)=An²+Bn+C，代入P(n)=2P(n−1)+n²，比较系数得P(n)=−n²−4n−6。齐次项为K*2^n，代入a[0]=0得K=6。所以a[n]=6*2^n−n²−4n−6。先把n模P，快速幂求2^n，再计算公式。',
        r'''const long long mod = 1000000009; long long n; while (cin >> n) { long long exponent = n, base = 2, value = 1; while (exponent) { if (exponent & 1) value = value * base % mod; base = base * base % mod; exponent >>= 1; } long long x = n % mod; long long answer = (6 * value % mod - x * x % mod - 4 * x % mod - 6) % mod; if (answer < 0) answer += mod; cout << answer << '\n'; }''',
        '指数使用完整n，不能把指数直接模P；n²则应先把n模P，避免原n平方溢出。',
        complexity=r'每组时间 $O(\log n)$，空间 $O(1)$。')
    put(25354,1700,['矩阵快速幂','非齐次递推'],'f[n]=3f[n−1]+2f[n−2]+2，求第n项。',
        '把常数1也放入状态列向量[f[i],f[i−1],1]，一步转移矩阵为[[3,2,2],[1,0,0],[0,0,1]]。从i=2的状态[1,1,1]出发，乘矩阵的n−2次幂即可。二进制快速幂遇到1位时直接把矩阵作用到当前向量。',
        r'''unsigned long long n; cin >> n; if (n <= 2) { cout << 1; return 0; } Matrix transition = {{3,2,2},{1,0,0},{0,0,1}}; vector<long long> state = {1,1,1}; n -= 2; while (n) { if (n & 1) state = applyMatrix(transition,state); transition = multiply(transition,transition); n >>= 1; } cout << state[0];''',
        '常数项2应乘状态中的1。初始状态是第2项，指数为n−2。',
        declarations=MATRIX,complexity=r'时间 $O(3^3\log n)$，空间 $O(3^2)$。')
    put(15666,2000,['矩阵快速幂','多项式递推'],'斐波那契递推再加i³+i²+i+1，多组n至10^18。',
        '使用状态[F[i],F[i−1],i³,i²,i,1]。下一项额外多项式按(i+1)展开为i³+4i²+6i+4，所以转移矩阵第一行是[1,1,1,4,6,4]。其余各行分别表示旧F、(i+1)³、(i+1)²、i+1和1。\n\n预先一次算出转移矩阵的2^b次幂，所有测试共用。每组从i=1的[1,0,1,1,1,1]开始，按n−1的二进制位做矩阵乘向量，避免1000组重复矩阵平方。',
        r'''Matrix transition = {{1,1,1,4,6,4},{1,0,0,0,0,0},{0,0,1,3,3,1},{0,0,0,1,2,1},{0,0,0,0,1,1},{0,0,0,0,0,1}}; vector<Matrix> powers(64); powers[0] = transition; for (int b = 1; b < 64; b++) powers[b] = multiply(powers[b-1],powers[b-1]); int tests; cin >> tests; while (tests--) { unsigned long long n; cin >> n; vector<long long> state = {1,0,1,1,1,1}; unsigned long long exponent = n - 1; for (int b = 0; exponent; b++,exponent >>= 1) if (exponent & 1) state = applyMatrix(powers[b],state); cout << state[0] << '\n'; }''',
        '矩阵加入的是下一时刻的多项式，不能直接沿用i³+i²+i+1。每次乘加及时取模。',
        declarations=MATRIX,complexity=r'预处理 $O(6^3\log U)$，每组 $O(6^2\log n)$，空间 $O(6^2\log U)$。')
    put(18987,1500,['斐波那契','快速倍增','前缀和'],'每次新花瓣替换旧花瓣，求树上和地上的总数。',
        '第i次新长花瓣数为1+Σ(j=1..i−1)F[j]=F[i+1]。旧花瓣落地后仍计入，所以k次后总数是初始1加Σ(i=1..k)F[i+1]=F[k+3]−1。用快速倍增求F[k+3]：由(F[t],F[t+1])得到F[2t]=F[t]*(2F[t+1]−F[t])、F[2t+1]=F[t]²+F[t+1]²。',
        r'''unsigned long long k; cin >> k; const long long mod = 998244353; cout << (fibonacci(k+3,mod).first + mod - 1) % mod;''',
        '初始花瓣也在总数内，不能只加各次净增长。减1后规范到非负余数。',
        declarations=FIB,complexity=r'时间、递归空间均为 $O(\log k)$。')


if __name__ == '__main__': run()
