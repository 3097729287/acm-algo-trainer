"""Divisor sums, permutations, reflection and independent coordinate choices."""
from nowcoder_editorials import CONTENT, add, add_python, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(23048,1800,['欧拉函数','约数求和'],'对每个N不超过n，求Σi/gcd(i,N)。',
        '按d=N/gcd(i,N)分类，令i=(N/d)*j，则1≤j≤d且gcd(j,d)=1，贡献变为j。d>1时，互质数j和d−j配对，所以这一组的和是d*phi(d)/2；d=1单独贡献1。令g(N)=Σ(d|N)d*phi(d)，统一答案为(g(N)+1)/2。先筛phi，再枚举约数d向它的所有倍数加d*phi(d)，最后逐行输出。',
        r'''int n; cin >> n; vector<int> phi(n + 1); iota(phi.begin(),phi.end(),0); for (int p = 2; p <= n; p++) if (phi[p] == p) for (int x = p; x <= n; x += p) phi[x] = phi[x] / p * (p - 1); vector<long long> sum(n + 1); for (int d = 1; d <= n; d++) for (int x = d; x <= n; x += d) sum[x] += 1LL * d * phi[d]; for (int x = 1; x <= n; x++) cout << (sum[x] + 1) / 2 << '\n';''',
        'd=1的互质和为1，不能也按d*phi(d)/2做整数除法。先累加再统一除二，使用64位。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(18985,1200,['望远镜求和','快速幂'],'首位非零的n位数，其相邻位差之和为K，求方案数。',
        '所有中间项消去，相邻位差之和恰为末位减首位。枚举首位a=1..9，只要0≤a+K≤9，就确定了合法末位。其余n−2位完全自由，各有10种选择，因此答案是合法首位数乘10^(n−2)。指数至10^13，用快速幂。',
        r'''long long n,k; cin >> n >> k; const long long mod = 1000000007; long long count = 0; for (int first = 1; first <= 9; first++) if (0 <= first + k && first + k <= 9) count++; long long power = 1, base = 10, exponent = n - 2; while (exponent) { if (exponent & 1) power = power * base % mod; base = base * base % mod; exponent >>= 1; } cout << count * power % mod;''',
        'K可以为负数，最高位不能为0。n=2时中间没有位置，幂应为1。',
        complexity=r'时间 $O(\log n)$，空间 $O(1)$。')
    put(19872,1800,['置换','快速幂','逆向推导'],'偶数张牌进行M次交错洗牌，求最终第L张的原编号。',
        '原位置i在前半叠时进入2i，后半叠时进入2i−N−1，统一为2i mod(N+1)。因此M次后原位置乘2^M。题目反查最终位置L的来源，应乘逆置换：N+1为奇数，2的逆元是(N+2)/2。答案L*((N+2)/2)^M mod(N+1)。N+1未必为素数，这个显式逆元仍成立。',
        r'''long long n,m,l; cin >> n >> m >> l; long long mod = n + 1, base = (n + 2) / 2, inversePower = 1; while (m) { if (m & 1) inversePower = (__int128)inversePower * base % mod; base = (__int128)base * base % mod; m >>= 1; } cout << (long long)((__int128)l * inversePower % mod);''',
        '问的是最终位置的牌面，方向要取逆。乘积可达10^20，使用128位中间乘法。M=0自然输出L。',
        complexity=r'时间 $O(\log(M+1))$，空间 $O(1)$。')
    put(19989,1600,['乘法原理','快速幂','去重'],'各位置可取1到n并排除指定值，求全部合法序列的乘积之和。',
        '由乘法分配律，所有序列的乘积之和等于各位置“允许值之和”的乘积。无约束位置的值和S=n(n+1)/2，共有m−不同受限位置数个，用S的快速幂一次处理。受限位置则从S减掉所有不同禁用值。把(x,y)排序去重，按x分组计算，避免重复限制重复扣减。',
        r'''long long n,m; int k; cin >> n >> m >> k; vector<pair<long long,long long>> forbidden(k); for (auto &[x,y] : forbidden) cin >> x >> y; sort(forbidden.begin(),forbidden.end()); forbidden.erase(unique(forbidden.begin(),forbidden.end()),forbidden.end()); const long long mod = 1000000007; long long total = n * (n + 1) / 2 % mod, answer = 1, groups = 0; for (int i = 0; i < (int)forbidden.size();) { int j = i; long long allowed = total; while (j < (int)forbidden.size() && forbidden[j].first == forbidden[i].first) { allowed = (allowed - forbidden[j].second % mod + mod) % mod; j++; } answer = answer * allowed % mod; groups++; i = j; } long long exponent = m - groups, base = total; while (exponent) { if (exponent & 1) answer = answer * base % mod; base = base * base % mod; exponent >>= 1; } cout << answer;''',
        '同一条限制可重复出现。某位置允许值之和模P为0时，直接让总乘积变0，无需做除法。',
        complexity=r'时间 $O(k\log k+\log m)$，空间 $O(k)$。')
    if 'nowcoder-global::19999' not in existing:
        add_python(19999,1400,['错位排列','递推','大整数'],'每行每列各有一个障碍，放n个棋子且每行每列一个，求精确方案数。',
            '障碍在每行、每列各出现一次，所以它们本身是一个排列。重新排列列号，让第i行障碍位于第i列，不改变合法方案数。问题便是求没有任何固定点的排列数D[n]。\n\n看第1行选中列j≠1，有n−1种。若第j行选列1，剩下是D[n−2]；否则把第j行对列1的选择改记为对列j的选择，得到n−1个元素的错排，数量D[n−1]。于是D[n]=(n−1)*(D[n−1]+D[n−2])，D[0]=1、D[1]=0。题目没有取模，使用Python大整数。',
            '''import sys

values = list(map(int, sys.stdin.buffer.read().split()))
n = values[0]
previous, current = 1, 0
if n == 0:
    print(1)
else:
    for length in range(2, n + 1):
        previous, current = current, (length - 1) * (current + previous)
    print(current)
''',
            '矩阵需要读入，但答案仅取决于n，因为题目保证障碍在不同行、不同列。不要把精确答案取模或存入64位整数。',
            complexity=r'读矩阵 $O(n^2)$；递推 $O(n)$ 次大整数运算，保存输入 $O(n^2)$。')
    put(20277,1700,['反射原理','组合数'],'n个1和m个0组成串，任意前缀中1不少于0，求数量模20100403。',
        '所有串有C(n+m,m)个。把1看成向上、0看成向下，非法串第一次到达高度−1前的步骤全部翻转，就得到含n+1个1、m−1个0的串；反过来也能唯一恢复第一次越界段。因此非法数是C(n+m,m−1)，答案为二者之差。模数20100403为素数，且n+m≤2000000小于模数，可预处理阶乘并用快速幂求逆阶乘。',
        r'''int n,m; cin >> n >> m; const long long mod = 20100403; int limit = n + m; vector<long long> factorial(limit + 1,1), inverse(limit + 1); for (int i = 1; i <= limit; i++) factorial[i] = factorial[i - 1] * i % mod; auto power = [&](long long a,long long b) { long long result = 1; while (b) { if (b & 1) result = result * a % mod; a = a * a % mod; b >>= 1; } return result; }; inverse[limit] = power(factorial[limit],mod - 2); for (int i = limit; i >= 1; i--) inverse[i - 1] = inverse[i] * i % mod; auto choose = [&](int k) { if (k < 0 || k > limit) return 0LL; return factorial[limit] * inverse[k] % mod * inverse[limit-k] % mod; }; cout << (choose(m) - choose(m-1) + mod) % mod;''',
        '非法串的反射是在第一次到达−1处，不是任意负前缀。最后做减法后加模数。',
        complexity=r'时间 $O(n+m+\log P)$，空间 $O(n+m)$。')
    put(16596,1200,['二项式定理','组合数'],'计算(ax+by)^k中x^n*y^m项的系数。',
        '从k个因子中选n个提供ax，其余m个提供by，系数就是C(k,n)*a^n*b^m。用一维Pascal递推求第k行组合数，内层倒序，随后分别乘n次a和m次b，始终模10007。',
        r'''int a,b,k,n,m; cin >> a >> b >> k >> n >> m; const int mod = 10007; vector<int> choose(k + 1); choose[0] = 1; for (int i = 1; i <= k; i++) for (int j = i; j >= 1; j--) choose[j] = (choose[j] + choose[j-1]) % mod; long long answer = choose[n]; for (int i = 0; i < n; i++) answer = answer * (a % mod) % mod; for (int i = 0; i < m; i++) answer = answer * (b % mod) % mod; cout << answer;''',
        '组合数的一维更新必须倒序；0次幂按1处理，包括底数为0的情况。',
        complexity=r'时间 $O(k^2)$，空间 $O(k)$。')
    put(16525,1100,['快速幂','循环位移'],'每轮位置加m，求10^k轮后x的位置。',
        '每轮所有人顺时针移动m，轮数为t时位置就是(x+m*t) mod n。只需要10^k mod n，用二进制快速幂计算，再代入即可，不需要模拟或求循环节。',
        r'''long long n,m,k,x; cin >> n >> m >> k >> x; long long turns = 1 % n, base = 10 % n; while (k) { if (k & 1) turns = turns * base % n; base = base * base % n; k >>= 1; } cout << (x + m * turns) % n;''',
        '位置从0编号。10^k是轮数，不是k轮；乘法使用64位。',
        complexity=r'时间 $O(\log k)$，空间 $O(1)$。')


if __name__ == '__main__': run()
