"""Prime factors, semiprime bit ranks and divisor-lattice inversion."""
from nowcoder_editorials import CONTENT, add, read

EXGCD = r'''
long long extendedGcd(long long a,long long b,long long &x,long long &y) {
    if (!b) { x = 1; y = 0; return a; }
    long long previousX,previousY;
    long long g = extendedGcd(b,a%b,previousX,previousY);
    x = previousY; y = previousX-(a/b)*previousY;
    return g;
}
'''


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(14399,1200,['质因数分解','素数筛'],'判断是否为素数，并按升序输出全部不同质因子。',
        '先筛出不超过sqrt(10^9)的素数。每次用素数p试除当前剩余数，若整除就记录p一次，再反复除尽其全部幂次。p²超过剩余数后停止，剩余值若大于1则本身为最后的质因子。若得到的唯一质因子就是原数，原数为素数，否则为合数。',
        r'''const int limit = 31623; vector<bool> composite(limit + 1); vector<int> primes; for (int p = 2; p <= limit; p++) if (!composite[p]) { primes.push_back(p); if (1LL * p * p <= limit) for (int x = p * p; x <= limit; x += p) composite[x] = true; } int tests; cin >> tests; while (tests--) { long long x; cin >> x; long long remaining = x; vector<long long> factors; for (int p : primes) { if (1LL * p * p > remaining) break; if (remaining % p == 0) { factors.push_back(p); while (remaining % p == 0) remaining /= p; } } if (remaining > 1) factors.push_back(remaining); cout << (factors.size() == 1 && factors[0] == x ? "isprime\n" : "noprime\n"); for (int i = 0; i < (int)factors.size(); i++) cout << factors[i] << (i + 1 == (int)factors.size() ? '\n' : ' '); }''',
        '例如9只输出质因子3一次。试除后剩余的大质因子也要输出，乘方比较先用64位。',
        complexity=r'预筛上界 $U=31623$，时间 $O(U\log\log U)$；每次至多 $O(\pi(\sqrt x)+\log x)$ 次运算，空间 $O(U)$。')
    put(53079,1600,['素数筛','最小质因子'],'求1到n每个数的最小质因子之和，n至三千万，1的贡献为0。',
        '所有偶数的最小质因子都是2。奇数只需存一个16位最小质因子：奇合数的最小质因子≤sqrt(n)<5500，未填表示奇素数。按递增奇素数p，从p²起每隔2p给尚未填的奇合数记录p，第一次填入就是最小质因子。最后逐数求和，奇数未填时加它自身。只为奇数开数组，约三千万字节，避免每个数用32位因子的内存。',
        r'''int n; cin >> n; vector<uint16_t> smallest(n / 2 + 1); for (int p = 3; 1LL * p * p <= n; p += 2) if (!smallest[p / 2]) for (int x = p * p; x <= n; x += 2 * p) if (!smallest[x / 2]) smallest[x / 2] = p; long long answer = 2LL * (n / 2); for (int x = 3; x <= n; x += 2) answer += smallest[x / 2] ? smallest[x / 2] : x; cout << answer;''',
        '未填的奇数是素数，其贡献不是0。1单独跳过；总和用64位。',
        complexity=r'时间 $O(n\log\log n)$，存约 $n/2$ 个16位数，空间 $O(n)$ 字节。')
    put(224933,2100,['素数筛','位集','前缀计数'],'多次统计闭区间中恰好分解为两个素数乘积的数，包括素数平方。',
        '先读全部询问，只预处理到最大右端N。漂亮数可唯一写为p*q且p≤q，所以只需生成至N/2的全部素数，再枚举p≤sqrt(N)、q从p到N/p，把乘积的位标记为1。素数平方自然包含，三个及以上素因子的数不会被标记。\n\nN至一亿，逐整数32位前缀和会占四亿字节。用64位字打包标记，每个字再存一个“此前整字置一总数”。查询前缀t时，整字计数加本字低t%64+1位的popcount，即可常数时间求数量。每次区间用rank(r)−rank(l−1)。',
        r'''int tests; cin >> tests; vector<pair<int,int>> query(tests); int maximum = 0; for (auto &[l,r] : query) { cin >> l >> r; maximum = max(maximum,r); } int limit = maximum / 2; vector<bool> composite(limit + 1); for (int p = 2; 1LL * p * p <= limit; p++) if (!composite[p]) for (int x = p * p; x <= limit; x += p) composite[x] = true; vector<int> primes; for (int p = 2; p <= limit; p++) if (!composite[p]) primes.push_back(p); vector<bool>().swap(composite); size_t words = ((size_t)maximum + 64) / 64; vector<unsigned long long> bits(words); for (size_t i = 0; i < primes.size() && 1LL * primes[i] * primes[i] <= maximum; i++) for (size_t j = i; j < primes.size(); j++) { long long value = 1LL * primes[i] * primes[j]; if (value > maximum) break; bits[value / 64] |= 1ULL << (value % 64); } vector<int> prefix(words + 1); for (size_t i = 0; i < words; i++) prefix[i + 1] = prefix[i] + __builtin_popcountll(bits[i]); auto rank = [&](int x) { if (x < 0) return 0; int word = x / 64, bit = x % 64; unsigned long long mask = bit == 63 ? ~0ULL : (1ULL << (bit + 1)) - 1; return prefix[word] + __builtin_popcountll(bits[word] & mask); }; for (auto [l,r] : query) cout << rank(r) - rank(l - 1) << '\n';''',
        '重复素因子允许，如4=2²。构造64位掩码时，移位64是未定义行为，末位为63时直接用全一掩码。乘积先转64位再判断上界。',
        complexity=r'枚举素数对数为 $P$，时间 $O(N\log\log N+P+T)$，空间为 $O(N/64+\pi(N/2)+T)$ 个机器字。')
    put(17247,1700,['素数筛','计数'],'统计有序数对(i,j)，二者除以gcd后均为素数，i、j不超过N。',
        '令i=g*p、j=g*q，其中p、q为素数。它们已除去最大公约数，故p、q必须不同。固定较大的素数q，较小素数p有π(q)−1个，g有floor(N/q)个，再乘2表示两种顺序。筛出素数后按从小到大扫描，用计数器记录q之前的素数个数，累加2*count*floor(N/q)，无需枚举g或素数对。',
        r'''int n; cin >> n; vector<bool> composite(n + 1); for (int p = 2; 1LL * p * p <= n; p++) if (!composite[p]) for (int x = p * p; x <= n; x += p) composite[x] = true; long long earlier = 0, answer = 0; for (int q = 2; q <= n; q++) if (!composite[q]) { answer += 2 * earlier * (n / q); earlier++; } cout << answer;''',
        '不能令p=q，否则约掉gcd后会得到1而不是素数。数对有序，最后乘2。',
        complexity=r'时间 $O(N\log\log N)$，空间 $O(N)$ 位。')
    put(20812,2200,['约数枚举','莫比乌斯反演','快速幂'],'每次先把x加入多重集，再求所有gcd(x,y)的k次方模p，k和p可每次变化。',
        '维护count[d]为已加入数中d的倍数个数，加入x只更新它的全部约数。对本次x，gcd只能是x的约数。设ways[d]为gcd恰等于d的次数，count[d]等于所有倍约数的ways之和。\n\n在x的约数格上做反演：先复制ways[d]=count[d]，对x的每个不同质因子q，按约数d递增执行ways[d]−=ways[d*q]（仅d*q仍整除x时）。这相当于在该质因子的指数方向做相邻差分，各方向依次相消后得到精确gcd频次。约数必须递增，避免同一轮读到已差分的更高指数值。最后用快速幂算Σways[d]*d^k mod p。预处理十万内全部约数和最小质因子，避免每问扫描所有旧元素。',
        r'''constexpr int limit = 100000; vector<vector<int>> divisors(limit + 1); vector<int> smallest(limit + 1), count(limit + 1), position(limit + 1); for (int d = 1; d <= limit; d++) for (int x = d; x <= limit; x += d) divisors[x].push_back(d); for (int p = 2; p <= limit; p++) if (!smallest[p]) for (int x = p; x <= limit; x += p) if (!smallest[x]) smallest[x] = p; auto power = [](long long a,int exponent,int mod) { long long result = 1 % mod; a %= mod; while (exponent) { if (exponent & 1) result = result * a % mod; a = a * a % mod; exponent >>= 1; } return result; }; int n; cin >> n; while (n--) { int x,k,p; cin >> x >> k >> p; const auto &d = divisors[x]; vector<int> ways(d.size()); for (int i = 0; i < (int)d.size(); i++) { count[d[i]]++; ways[i] = count[d[i]]; position[d[i]] = i; } int value = x; while (value > 1) { int prime = smallest[value]; for (int i = 0; i < (int)d.size(); i++) { long long higher = 1LL * d[i] * prime; if (higher <= x && x % higher == 0) ways[i] -= ways[position[higher]]; } while (value % prime == 0) value /= prime; } long long answer = 0; for (int i = 0; i < (int)d.size(); i++) answer = (answer + ways[i] * power(d[i],k,p)) % p; cout << answer << '\n'; }''',
        '当前x先加入再查询，故包括gcd(x,x)=x。集合可重复，计数不能去重。模数p不保证素数，也无需对模数做除法。',
        complexity=r'预处理上界 $U=10^5$，时间和空间 $O(U\log U)$；单次约数数 $D$、不同质因子数 $r$，时间 $O(D(r+\log k))$、临时空间 $O(D)$。')
    put(16710,1000,['最大公约数','整数运算'],'求两个unsigned long long范围正整数的最小公倍数，保证答案也在该范围。',
        'gcd(a,b)*lcm(a,b)=a*b。先用欧几里得求g，然后输出(a/g)*b。必须先除再乘，虽然最终最小公倍数装得下，原a*b仍可能溢出。全程使用unsigned long long读取、计算、输出，不能用有符号long long装输入。',
        r'''unsigned long long a,b; cin >> a >> b; auto g = gcd(a,b); cout << (a / g) * b;''',
        '原题2026年10月更新数据后已覆盖完整无符号64位范围。unsigned long long最大值不能先读入有符号类型再转换。',
        complexity=r'时间 $O(\log\min(a,b))$，空间 $O(1)$。',
        cases=[{'input':'18446744073709551615 18446744073709551615','output':'18446744073709551615'}])
    put(50565,1300,['扩展欧几里得','乘法逆元'],'保证有解，求a*x模b等于1的最小正整数x。',
        '扩展欧几里得求a*x+b*y=gcd(a,b)。题目保证逆元存在，即gcd为1，所以所得x就是一组解；全部解相差b的整数倍，归一化到[0,b)后就是最小正解。b≥2且互质，结果不会为0。',
        r'''long long a,b,x,y; cin >> a >> b; extendedGcd(a,b,x,y); cout << (x % b + b) % b;''',
        '系数可以为负，要归一化两次取模。参数至二十亿，系数更新使用64位。',declarations=EXGCD,
        complexity=r'时间 $O(\log\min(a,b))$，递归栈空间同阶。')
    put(229005,1400,['扩展欧几里得','乘法逆元'],'多组求a模b的乘法逆元，不存在时输出负一。',
        '扩展欧几里得给出a*x+b*y=g。只有g=1时才能模b得到a*x=1；否则任何a*x+b*y都是g的倍数，无法等于1。存在时将x归一化到[0,b)，输出最小正解。',
        r'''int tests; cin >> tests; while (tests--) { long long a,b,x,y; cin >> a >> b; long long g = extendedGcd(a,b,x,y); if (g != 1) cout << "-1\n"; else cout << (x % b + b) % b << '\n'; }''',
        '本题没有互质保证，必须检查gcd，不能照搬只保证有解的单组版本。',declarations=EXGCD,
        complexity=r'每组时间、递归栈空间均为 $O(\log\min(a,b))$。')


if __name__ == '__main__': run()
