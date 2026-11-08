"""Number identities, exact CRT for small moduli and multiplicative sieving."""
from nowcoder_editorials import CONTENT, add, add_python, read, reviewed_clone
from nowcoder_factor_support import FACTOR


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    if 'nowcoder-global::16563' not in existing:
        reviewed_clone(16563,50565,'完整核对NOIP2012同余方程，单组、互质保证、二十亿范围、最小正逆元与样例均相同。')
    put(23050,1200,['最大公约数','不变量'],'类斐波那契数列初值A、B，N可有十万位，求相邻两项gcd。',
        '欧几里得性质gcd(x+y,y)=gcd(x,y)说明相邻两项gcd始终不变：gcd(F[N+1],F[N])=gcd(F[N],F[N−1])，一路退回gcd(A,B)。因此无需生成大数，也不用把N转成整数，只读成字符串后计算初值gcd。',
        r'''unsigned long long a,b; string n; cin >> a >> b >> n; cout << gcd(a,b);''',
        'N很长但完全不影响答案。A、B至10^17，需64位读取。',complexity=r'读入时间 $O(|N|)$，gcd时间 $O(\log A)$；存N的空间 $O(|N|)$。')
    if 'nowcoder-global::16559' not in existing:
        add_python(16559,1500,['递推','博弈','奇偶性'],'聪明的鱼按顺序决定是否捕食前鱼，第一条鱼每天可吃饭的安全天数最多多少。',
            '固定当天有k条鱼，从末尾倒推：一条鱼吃前鱼后，若后面那条会继续捕食，它就不会吃；最后一条总敢吃，因此第一条能安全吃食物当且仅当k为奇数。奇数时第二条选择不吃，偶数时第一条自己不吃，所以理性策略下没有鱼被吃掉，繁殖数量不受影响。\n\n按出生后成长两天再繁殖，头两天鱼数为1、1，此后每天的新增鱼是前两天已有的鱼，鱼数满足斐波那契递推。模2依次为1、1、0，每三天循环，因此只有3的倍数日不能喂TbGx，答案n−floor(n/3)。原站补充说明n不超过10^18，用Python整数直接计算。',
            '''import sys

if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)

for token in sys.stdin.buffer.read().split():
    n = int(token)
    print(n - n // 3)
''',
            '只需鱼数的奇偶，无需计算增长极快的鱼数量。输入多组读至EOF，没有开头测试组数。',
            complexity='每组只做常数次大整数运算，时间包含十进制读写的开销，空间与输入数字位数相关。',
            cases=[{'input':'1\n2\n3\n4\n5\n6','output':'1\n2\n2\n3\n4\n4'}])
    put(200184,1500,['斐波那契','快速倍增'],'n至10^18，求前n项斐波那契平方和模十亿加七。',
        '由F[i+1]−F[i−1]=F[i]，有F[i]²=F[i]F[i+1]−F[i−1]F[i]，相加后中间项抵消，平方和恰为F[n]F[n+1]。快速倍增同时求(F[k],F[k+1])：F[2k]=F[k]*(2F[k+1]−F[k])，F[2k+1]=F[k]²+F[k+1]²，再按n奇偶返回相邻两项，递归每次减半。',
        r'''unsigned long long n; cin >> n; const long long mod = 1000000007; auto fibonacci = [&](auto &&self,unsigned long long index) -> pair<long long,long long> { if (index == 0) return {0,1}; auto [a,b] = self(self,index / 2); long long c = a * ((2 * b - a + mod) % mod) % mod, d = (a * a + b * b) % mod; if (index % 2) return {d,(c + d) % mod}; return {c,d}; }; auto [a,b] = fibonacci(fibonacci,n); cout << a * b % mod;''',
        '斐波那契从F1=F2=1开始，公式中F0=0。模减法先加模数，乘法使用64位。',complexity=r'时间、递归栈空间均为 $O(\log n)$。')
    if 'nowcoder-global::15068' not in existing:
        add_python(15068,2200,['中国剩余定理','质因数分解','大整数'],'十万条小模数同余约束，求最小非负共同解，无解输出负一。',
            '每个模数a小于十万，分解成互质的质数幂。x≡r mod a等价于对每个完整质数幂q都有x≡r mod q。对同一个质数，只保留目前最大的幂次约束；两个幂互相整除，用较小模数检查两个余数是否一致，不一致就无解。这一步先将十万条输入压缩成每个质数至多一条。\n\n剩余模数两两互质，逐个做CRT。已有x≡answer mod M，新约束x≡r mod q，令x=answer+M*t，求t=(r−answer)*inverse(M mod q) mod q，再更新answer和M。使用Python任意精度，防止最终模数的最小公倍数远超64位。每次把t归一化后，answer自动处在[0,M)内。输出描述要求非负最小值，所以所有余数为0时输出0。',
            '''import sys

if hasattr(sys, 'set_int_max_str_digits'):
    sys.set_int_max_str_digits(0)


def inverse(a, mod):
    old_r, r = a, mod
    old_x, x = 1, 0
    while r:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_x, x = x, old_x - quotient * x
    return old_x % mod


data = list(map(int, sys.stdin.buffer.read().split()))
k = data[0]
bound = max(data[1::2], default=1)
smallest = [0] * (bound + 1)
for p in range(2, bound + 1):
    if smallest[p] == 0:
        for value in range(p, bound + 1, p):
            if smallest[value] == 0:
                smallest[value] = p

constraints = {}
valid = True
for i in range(k):
    a, residue = data[1 + 2 * i:3 + 2 * i]
    while a > 1:
        p = smallest[a]
        power = 1
        while a % p == 0:
            a //= p
            power *= p
        remainder = residue % power
        old_power, old_remainder = constraints.get(p, (1, 0))
        if (remainder - old_remainder) % min(power, old_power):
            valid = False
        if power > old_power:
            constraints[p] = power, remainder

if not valid:
    print(-1)
else:
    answer, modulus = 0, 1
    for q, remainder in constraints.values():
        multiplier = (remainder - answer % q) * inverse(modulus % q, q) % q
        answer += modulus * multiplier
        modulus *= q
    print(answer)
''',
            'a不保证两两互质，不能对原模数直接套普通CRT。模数为1只约束余数0；相同质数的幂次只保留最强且兼容的一条。',
            complexity=r'预筛上界 $U<10^5$，时间 $O(U\log\log U+k\log U)$ 加至多 $\pi(U)$ 次大整数CRT合并；空间 $O(U+k)$ 加最终大整数位数。',
            cases=[{'input':'2\n4 0\n6 0','output':'0'},{'input':'2\n4 1\n6 2','output':'-1'},{'input':'3\n8 3\n4 3\n9 2','output':'11'}])
    put(20667,2200,['欧拉函数','质因数分解','Pollard-Rho'],'求1到n中与n不互质的整数之和，模十亿加七，n至10^14。',
        r'原图公式为 $\sum_{i=1}^n i[\gcd(i,n)\ne1]$。n>1时，互质数在i与n−i间配对，和为n*phi(n)/2；全部整数和n(n+1)/2，故答案为n*(n+1−phi(n))/2。n=1单独为0。分解n后按phi=n*Π(1−1/p)求欧拉函数，模意义下乘2的逆元500000004。' + '\n\n' +
        '为了应对多组较大的素数或半素数，先用确定性64位Miller–Rabin判断素数，再用Pollard–Rho找非平凡因子。后者沿x²+c模n迭代，用Floyd快慢指针及gcd找出在某个质因子模数下先碰撞的位置；若只得到n则换参数重试。只影响分解耗时，不把随机结果直接当成正确因子。七个固定底数覆盖64位，乘法用128位取模。',
        r'''U64 n; constexpr U64 mod = 1000000007; while (cin >> n) { if (n == 1) { cout << "0\n"; continue; } vector<U64> factors; factor(n,factors); sort(factors.begin(),factors.end()); factors.erase(unique(factors.begin(),factors.end()),factors.end()); U64 phi = n; for (U64 p : factors) phi = phi / p * (p - 1); U64 value = n % mod * ((n + 1 - phi) % mod) % mod; cout << value * 500000004ULL % mod << '\n'; }''',
        'n本身与n不互质（n>1），要包含在和中。不要在取模后用普通整数除二；使用2的模逆元。',declarations=FACTOR,
        complexity=r'Miller–Rabin每次 $O(\log n)$ 次模乘；Rho寻找最小质因子 $p$ 的期望迭代约 $O(\sqrt p)$，即常用 $O(n^{1/4})$ 分解估计，随机重试无确定最坏界。空间 $O(\log n)$。')
    put(20313,1600,['欧拉函数','格点可见性'],'从方阵左下角观察，求不被同一直线上前方同学挡住的人数。',
        '以观察角为(0,0)，其余坐标0到N−1。正坐标点(x,y)可见当且仅当gcd(x,y)=1；否则沿同一射线先看到约去gcd后的格点。对x>y≥1按x分组，数量为phi(x)，关于对角线对称乘二；再加(1,1)及两个坐标轴上的首点。等价写成1+2*Σ(i=1..N−1)phi(i)。N=1没有其他人，答案0。用筛法初始化phi[i]=i，每个素数p对其倍数更新phi=phi/p*(p−1)。',
        r'''int n; cin >> n; if (n == 1) { cout << 0; return 0; } vector<int> phi(n); iota(phi.begin(),phi.end(),0); for (int p = 2; p < n; p++) if (phi[p] == p) for (int x = p; x < n; x += p) phi[x] = phi[x] / p * (p - 1); long long answer = 1; for (int i = 1; i < n; i++) answer += 2LL * phi[i]; cout << answer;''',
        '实际坐标最大是N−1，不能把phi[N]也累加。phi[1]=1，已经把两条坐标轴的首个可见点计入公式。',complexity=r'时间 $O(N\log\log N)$，空间 $O(N)$。')
    put(23047,2000,['线性筛','完全积性函数','快速幂'],'求所有i的i^N模十亿加七后再异或，N至一千三百万。',
        '对固定指数N，f(x)=x^N mod P是完全积性函数，f(a*b)=f(a)*f(b) mod P。在线性筛里，每个素数用一次快速幂求f(p)，每个合数按其唯一线性筛生成方式用一次模乘求值，避免对一千多万个数各做一次快速幂。\n\n所有i<P且P为素数，所以f(i)不可能为0；数组值0便可兼作“尚未筛到”的素数标记，不另存最小质因子表。每生成一个i的f值就异或进答案。',
        r'''int n; cin >> n; const long long mod = 1000000007; auto power = [&](long long a) { long long result = 1; int exponent = n; while (exponent) { if (exponent & 1) result = result * a % mod; a = a * a % mod; exponent >>= 1; } return (int)result; }; vector<int> value(n + 1), primes; value[1] = 1; int answer = 1; for (int i = 2; i <= n; i++) { if (value[i] == 0) { primes.push_back(i); value[i] = power(i); } answer ^= value[i]; for (int p : primes) { long long composite = 1LL * i * p; if (composite > n) break; value[composite] = 1LL * value[i] * value[p] % mod; if (i % p == 0) break; } } cout << answer;''',
        '每项先取模再做异或，不能把指数、底数或最后异或结果另外取模替代。0作标记依赖N小于模数，不能无条件搬到其他完全积性函数。',
        complexity=r'时间 $O(N+\pi(N)\log N)$，空间 $O(N+\pi(N))$，主要为32位函数值表。')


if __name__ == '__main__': run()
