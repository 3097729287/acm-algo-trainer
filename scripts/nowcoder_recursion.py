"""Number representation, recursion and high precision, from full statements."""
from nowcoder_editorials import add, CONTENT, read, register


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(14742, 900, ['查表', '模拟'], '按题面七段数码图，分别统计每个数字的水平与竖直火柴数。',
        '图中只有七种固定段位，逐个数字核对后保存两张表：水平数为 2,0,3,3,1,3,3,1,3,3；竖直数为 4,2,2,2,3,2,3,2,4,3。查询时直接按数字下标取两项。',
        r'''int horizontal[] = {2, 0, 3, 3, 1, 3, 3, 1, 3, 3};
        int vertical[] = {4, 2, 2, 2, 3, 2, 3, 2, 4, 3};
        int t; cin >> t; while (t--) { char c; cin >> c; int x = c - '0'; cout << horizontal[x] << ' ' << vertical[x] << '\n'; }''',
        '零的上下各一根水平火柴、左右各两根竖直火柴。按原图计算，不按手写字体猜测。', complexity='每组时间与额外空间均为 $O(1)$。')
    put(16599, 800, ['枚举', '数位'], '统计闭区间 L 到 R 的所有整数中数字二的出现总次数。',
        '区间上界只有一万，直接逐数检查。每次取最低十进制位，等于二就计数，再整除十移去这位。一个数中的多个二分别贡献。',
        r'''int l, r; cin >> l >> r; int ans = 0;
        for (int x = l; x <= r; x++) for (int n = x; n > 0; n /= 10) if (n % 10 == 2) ans++; cout << ans;''',
        '二十二贡献两次，不是只判断每个数是否含二。', complexity=r'时间 $O((R-L+1)\log R)$，额外空间 $O(1)$。')
    put(13584, 1000, ['日期', '枚举'], '按四位年份、两位月份、两位日期的形式，统计指定月份所有日期中目标数字的次数。',
        '先按公历闰年规则求该月天数。枚举每一天，用 setw 和补零写成 YYYY-MM-DD，再统计目标数字字符。连字符不会等于任何数字，直接忽略即可。',
        r'''int y, m, digit; while (cin >> y >> m >> digit) { int days[] = {0,31,28,31,30,31,30,31,31,30,31,30,31};
            if (y % 400 == 0 || (y % 4 == 0 && y % 100 != 0)) days[2] = 29; int ans = 0;
            for (int d = 1; d <= days[m]; d++) { ostringstream out; out << setfill('0') << setw(4) << y << '-' << setw(2) << m << '-' << setw(2) << d;
                string s = out.str(); ans += count(s.begin(), s.end(), char('0' + digit)); } cout << ans << '\n';
        }''', '年份和月份每天都会重新出现一次，不能只统计日期部分。补出的零也要计数。', complexity='每组最多三十一条八数字日期，时间与额外空间均为常数。')
    put(14703, 1900, ['素数', '高精度模乘'], '把给定素数除最后一位外的前缀倒序接到末尾，判断构造出的奇数长度回文数是否为素数。',
        '先按定义构造，如 127 变为 12721。原数可有九位，回文数最多十七位，逐因子试除到平方根可能太慢。使用六十四位范围内确定的 Miller–Rabin 检测：分解 n-1=d·2^s，对固定底数先算 a^d，再逐次平方检查是否出现 n-1；模乘用 unsigned __int128 保证中间积精确。固定七个底数的适用范围可核对 [KACTL 的原始算法说明](https://raw.githubusercontent.com/kth-competitive-programming/kactl/main/content/number-theory/MillerRabin.h)。',
        r'''string s; cin >> s; int originalLength = s.size(); for (int i = originalLength - 2; i >= 0; i--) s += s[i];
        unsigned long long n = 0; for (char c : s) n = n * 10 + c - '0'; cout << (isPrime(n) ? "prime" : "noprime");''',
        '中间那一位不能重复，如十三对应一三一而不是一三三一。普通 long long 直接相乘后再取模可能溢出。',
        complexity=r'固定七个底数，每个进行 $O(\log n)$ 次常数宽整数模乘，额外空间 $O(\log n)$ 个输入字符。',
        declarations=r'''using ull = unsigned long long;
        ull multiply(ull a, ull b, ull mod) { return (unsigned __int128)a * b % mod; }
        ull power(ull a, ull b, ull mod) { ull result = 1; while (b) { if (b & 1) result = multiply(result, a, mod); a = multiply(a, a, mod); b >>= 1; } return result; }
        bool isPrime(ull n) {
            if (n < 2) return false;
            for (ull p : {2ULL,3ULL,5ULL,7ULL,11ULL,13ULL,17ULL,19ULL,23ULL,29ULL,31ULL,37ULL}) { if (n == p) return true; if (n % p == 0) return false; }
            ull d = n - 1; int s = 0; while ((d & 1) == 0) { d >>= 1; s++; }
            for (ull a : {2ULL,325ULL,9375ULL,28178ULL,450775ULL,9780504ULL,1795265022ULL}) {
                a %= n; if (a == 0) continue; ull x = power(a, d, n); if (x == 1 || x == n - 1) continue;
                bool passed = false; for (int r = 1; r < s; r++) { x = multiply(x, x, n); if (x == n - 1) { passed = true; break; } }
                if (!passed) return false;
            } return true;
        }''', cases=[{'input': '19', 'output': 'prime'}, {'input': '23', 'output': 'noprime'}])
    put(22168, 900, ['枚举', '数位'], '统计闭区间中数位和为五的倍数的非负整数个数。',
        '逐数提取十进制数位并求和，再检查和对五的余数。零的数位和为零，也是五的倍数，需要正常计入。',
        r'''int l, r; cin >> l >> r; if (l > r) swap(l, r); int ans = 0;
        for (int x = l; x <= r; x++) { int sum = 0; for (int y = x; y > 0; y /= 10) sum += y % 10; if (sum % 5 == 0) ans++; } cout << ans;''',
        '条件是数位之和能被五整除，不是原数能被五整除。', complexity=r'时间 $O((r-l+1)\log(r+1))$，额外空间 $O(1)$。', cases=[{'input': '0 0', 'output': '1'}])
    put(15756, 1200, ['高精度', '乘法'], '计算两个长度最多五十的十进制整数串的乘积。',
        '按竖式乘法，让 a 的第 i 位与 b 的第 j 位乘积累加到结果第 i+j+1 位。先累加所有乘积，再从右往左统一进位。最后跳过结果开头的零，并输出剩余数位。一般高精度乘法已经足以处理五十位，无须利用 233 的特殊模式。',
        r'''int t; cin >> t; while (t--) { string a, b; cin >> a >> b; int n = a.size(), m = b.size(); vector<int> c(n + m);
            for (int i = n - 1; i >= 0; i--) for (int j = m - 1; j >= 0; j--) c[i + j + 1] += (a[i] - '0') * (b[j] - '0');
            for (int i = n + m - 1; i > 0; i--) { c[i - 1] += c[i] / 10; c[i] %= 10; }
            int start = 0; while (start + 1 < n + m && c[start] == 0) start++; for (int i = start; i < n + m; i++) cout << c[i]; cout << '\n';
        }''', '五十位不能放进任何常用整数类型；每个结果位置会收到多个乘积，进位要考虑全部累加量。',
        complexity='两个串长度为 $n,m$ 时，时间 $O(nm)$，结果空间 $O(n+m)$。')
    put(15902, 1100, ['高精度', '加法'], '对最多五千位的正整数做加法，并去掉答案的前导零。',
        '从两串末尾开始逐位相加，加上上一位进位。把和的个位加入结果，十位作为下一轮进位；两边都读完后仍有进位就继续。暂存的结果从低位到高位，先去掉高位多余零，再反转。',
        r'''int t; cin >> t; while (t--) { string a, b, answer; cin >> a >> b; int i = (int)a.size() - 1, j = (int)b.size() - 1, carry = 0;
            while (i >= 0 || j >= 0 || carry) { int sum = carry; if (i >= 0) sum += a[i--] - '0'; if (j >= 0) sum += b[j--] - '0'; answer += char('0' + sum % 10); carry = sum / 10; }
            while (answer.size() > 1 && answer.back() == '0') answer.pop_back(); reverse(answer.begin(), answer.end()); cout << answer << '\n';
        }''', '两个整数可以长度不同，也可能含很多前导零，不能按相同下标直接从左往右加。',
        complexity='时间与结果空间均为 $O(\max(|A|,|B|))$。', cases=[{'input': '2\n00099\n001\n9999\n1', 'output': '100\n10000'}])
    put(20858, 900, ['枚举', '平方根'], '输出序列中最大的非完全平方数。',
        '对每个数求整数平方根 r，若 r*r 不等于原数，它就是候选，维护最大候选即可。输入不超过一千，普通 sqrt 的结果转整数足够，最后仍用平方检验。',
        r'''int n; cin >> n; int ans = 0; for (int i = 0; i < n; i++) { int x; cin >> x; int r = sqrt(x); if (r * r != x) ans = max(ans, x); } cout << ans;''',
        '一是完全平方数。题目保证至少存在一个非平方数。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(208815, 1300, ['筛法', '扫描'], '从区间内连续素数里找至少三项的等差段，已经输出的素数不得再用于后一段。',
        '先筛出区间中的递增素数表。从左往右检查相邻三项，若前两段差不相同就推进起点；若相同，就尽量延长当前差值的等差段并输出，随后把起点移到这整段之后。这样不会让前后两段共享端点。',
        r'''int a, b; cin >> a >> b; vector<bool> prime(b + 1, true); prime[0] = prime[1] = false;
        for (int p = 2; p <= b / p; p++) if (prime[p]) for (int x = p * p; x <= b; x += p) prime[x] = false;
        vector<int> values; for (int x = max(2, a); x <= b; x++) if (prime[x]) values.push_back(x);
        int i = 0; while (i + 2 < (int)values.size()) { int d = values[i + 1] - values[i];
            if (values[i + 2] - values[i + 1] != d) { i++; continue; } int j = i + 2;
            while (j + 1 < (int)values.size() && values[j + 1] - values[j] == d) j++;
            for (int k = i; k <= j; k++) { if (k > i) cout << ' '; cout << values[k]; } cout << '\n'; i = j + 1;
        }''', '本题明确禁止相邻等差段共享一个素数，输出后必须从末项的下一项继续。',
        complexity=r'筛法 $O(b\log\log b)$，扫描 $O(\pi(b))$，空间 $O(b)$。')
    put(16130, 1200, ['计算几何', '叉积'], '按顺时针或逆时针给定凸多边形顶点，求面积并四舍五入为整数。',
        '用鞋带公式累加 x[i]y[i+1]-y[i]x[i+1]，其绝对值等于面积的两倍。坐标是整数，所以两倍面积是整数；取 (abs(sum)+1)/2 就实现非负面积的四舍五入。用 __int128 保存乘积与累加，最后按十进制输出。',
        r'''int n; cin >> n; vector<long long> x(n), y(n); for (int i = 0; i < n; i++) cin >> x[i] >> y[i]; __int128 area2 = 0;
        for (int i = 0; i < n; i++) { int j = (i + 1) % n; area2 += (__int128)x[i] * y[j] - (__int128)y[i] * x[j]; }
        if (area2 < 0) area2 = -area2; __int128 ans = (area2 + 1) / 2; string out;
        do { out += char('0' + ans % 10); ans /= 10; } while (ans); reverse(out.begin(), out.end()); cout << out;''',
        '最后一个点还要连接第一个点。顶点顺序可能相反，应在总和之后取绝对值。', complexity='时间与坐标数组空间均为 $O(n)$。',
        cases=[{'input': '3\n0 0\n1 0\n0 1', 'output': '1'}])
    put(15173, 800, ['数位', '模拟'], '不断将整数替换成其各位数字之和，直到只剩一位。',
        '只要 n≥十，就用一个临时变量逐位求和，并把结果作为下一轮的 n。每轮结束后数值明显缩小，给定范围内很快会成为个位数。',
        r'''long long n; cin >> n; while (n >= 10) { long long next = 0; while (n) { next += n % 10; n /= 10; } n = next; } cout << n;''',
        '不是只求一次数位和，例如三十八第一次变十一，还要继续变二。', complexity=r'各轮处理的总数位量为 $O(\log n)$，额外空间 $O(1)$。')
    put(15979, 1200, ['位运算', '构造'], '求递推数列 f[n]，并找出这个值最早出现的下标。',
        '递推每次将 n 整除二，并加上 n 的最低二进制位，所以 f[n] 就是二进制一的个数 c。包含 c 个一的最小非负整数，是把这些一全部放在最低位的 2^c-1。n=0 时 c=0，最早下标仍为零。',
        r'''int t; cin >> t; while (t--) { unsigned long long n; cin >> n; int count = 0;
            for (auto x = n; x; x >>= 1) count += x & 1ULL; cout << count << ' ' << ((1ULL << count) - 1) << '\n'; }''',
        '不能按输入 n 的大小建立数组，n 可以接近十的十八次方；只检查最多六十个二进制位。',
        complexity=r'每组时间 $O(\log(n+1))$，额外空间 $O(1)$。', cases=[{'input': '1\n15', 'output': '4 15'}])
    put(16660, 1200, ['分治', '二叉树遍历'], '对二进制串递归二分，以全零 B、全一 I、混合 F 标记结点，输出后序。',
        '递归函数返回当前子串的类型，并在左右递归完成后输出本结点类型。单字符直接判为 B 或 I；若两个子结点同为 B 或同为 I，父结点同类，其余情况为 F。两个子结点都是 F 时父结点仍为 F。每个结点只处理一次。',
        r'''int n; string s; cin >> n >> s;
        function<char(int,int)> solve = [&](int l, int r) { char result;
            if (l == r) result = s[l] == '0' ? 'B' : 'I'; else { int mid = (l + r) / 2; char left = solve(l, mid), right = solve(mid + 1, r); result = left == right ? left : 'F'; }
            cout << result; return result;
        };
        solve(0, (int)s.size() - 1);''', '后序必须先左、再右、最后父结点。不要在进入递归时就输出父结点。',
        complexity=r'串长 $L=2^N$ 时，时间 $O(L)$，输入空间 $O(L)$，递归栈 $O(\log L)$。')
    put(16681, 1700, ['区间 DP', '二叉树'], '在中序编号固定的二叉树中，最大化左右子树加分的乘积加根分数，并输出一种最优先序。',
        '一棵子树的中序编号必然是连续区间 [l,r]。枚举根 k，左右两边独立取最优，候选为 dp[l][k-1]·dp[k+1][r]+score[k]。空区间加分为一，单个叶子加分直接等于自身分数，不能套成分数加一。按区间长度计算，并记录取得最大值的根，用它递归输出先序。',
        r'''int n; cin >> n; vector<long long> value(n + 1); for (int i = 1; i <= n; i++) cin >> value[i];
        vector<vector<long long>> dp(n + 2, vector<long long>(n + 2, 1)); vector<vector<int>> root(n + 2, vector<int>(n + 2));
        for (int i = 1; i <= n; i++) { dp[i][i] = value[i]; root[i][i] = i; }
        for (int length = 2; length <= n; length++) for (int l = 1; l + length - 1 <= n; l++) { int r = l + length - 1; dp[l][r] = 0;
            for (int k = l; k <= r; k++) { long long candidate = dp[l][k - 1] * dp[k + 1][r] + value[k]; if (candidate > dp[l][r]) { dp[l][r] = candidate; root[l][r] = k; } } }
        cout << dp[1][n] << '\n'; bool first = true;
        function<void(int,int)> output = [&](int l, int r) { if (l > r) return; int k = root[l][r]; if (!first) cout << ' '; first = false; cout << k; output(l, k - 1); output(k + 1, r); };
        output(1, n);''', '最高分可能超过有符号 32 位范围，dp 与乘积使用 long long。根编号就是中序下标，不是输入分数。',
        complexity='时间 $O(n^3)$，DP 与根记录空间 $O(n^2)$。', cases=[{'input': '1\n9', 'output': '9\n1'}])
    put(21241, 1800, ['二叉树', '枚举', '剪枝'], '在最多一百万结点的有权二叉树中，求最大的镜像对称完整子树。',
        '先用迭代遍历得到从父到子的顺序，逆序计算每棵子树大小。只有左右子树大小相等，根才可能对称；对这些候选，用栈成对检查“左的左与右的右、左的右与右的左”，要求空位和权值都匹配。若候选大小不超过当前答案，可直接跳过。全过程不用深递归，也不依赖可能碰撞的树哈希。',
        r'''int n; cin >> n; vector<int> value(n + 1), left(n + 1), right(n + 1), size(n + 1), order; for (int i = 1; i <= n; i++) cin >> value[i];
        for (int i = 1; i <= n; i++) { cin >> left[i] >> right[i]; if (left[i] < 0) left[i] = 0; if (right[i] < 0) right[i] = 0; }
        order.push_back(1); for (size_t i = 0; i < order.size(); i++) { int u = order[i]; if (left[u]) order.push_back(left[u]); if (right[u]) order.push_back(right[u]); }
        for (int i = (int)order.size() - 1; i >= 0; i--) { int u = order[i]; size[u] = 1 + size[left[u]] + size[right[u]]; }
        int answer = 1; vector<pair<int,int>> pending;
        for (int u : order) { if (size[u] <= answer || size[left[u]] != size[right[u]]) continue;
            bool same = true; pending.clear(); pending.emplace_back(left[u], right[u]);
            while (!pending.empty() && same) { auto [a,b] = pending.back(); pending.pop_back();
                if (a == 0 || b == 0) { if (a != b) same = false; continue; }
                if (value[a] != value[b]) { same = false; break; }
                pending.emplace_back(left[a], right[b]); pending.emplace_back(right[a], left[b]);
            }
            if (same) answer = size[u];
        }
        cout << answer;''', '相同权值不代表结构相同；两个对应位置若只有一边为空，必须判不对称。百万长链要避免递归栈溢出。',
        complexity=r'时间上界 $O(n\log n)$：只有左右等大的结点才向下检查；沿任一后代路径，每经过一次这种被检查的祖先，所属子树至少减半，因此每个点最多被检查 $O(\log n)$ 次。数组与显式栈空间 $O(n)$。')
    put(14585, 1300, ['递推', '汉诺塔'], '只允许相邻柱移动，将 n 个盘从最左柱搬到最右柱，求最少步数。',
        '为了让最大盘从左经中到右，较小 n-1 个盘必须依次完成三次左右端柱之间的搬运；最大盘本身移动两次。所以 T[n]=3T[n-1]+2，T[0]=0，解得 T[n]=3^n-1。按整数循环乘三，避免浮点 pow。',
        r'''int n; while (cin >> n) { long long power = 1; for (int i = 0; i < n; i++) power *= 3; cout << power - 1 << '\n'; }''',
        '普通汉诺塔的 2^n-1 不适用，因为最大盘不能从左柱直接移到右柱。', complexity='每组时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '0\n2', 'output': '0\n8'}])
    put(16539, 1200, ['表达式', '取模与同余'], '按乘法优先于加法求值，只输出结果最后四位且不补前导零。',
        '把表达式看成若干乘法段的和。扫描一个整数后，将它乘入当前段；遇到加号或表达式结束，就把该段加入答案并将乘积重置为一。数字解析、乘法、加法都对一万取模，既保留最后四位又避免大整数。',
        r'''string s; cin >> s; long long answer = 0, product = 1; size_t i = 0;
        while (i < s.size()) { int value = 0; while (i < s.size() && isdigit(static_cast<unsigned char>(s[i]))) { value = (value * 10 + s[i] - '0') % 10000; i++; }
            product = product * value % 10000; if (i == s.size() || s[i] == '+') { answer = (answer + product) % 10000; product = 1; } i++; }
        cout << answer;''', '当前乘法段初始值是一，不能是零。余数四应输出 4 而不是 0004。', complexity='时间与输入字符串空间均为 $O(|S|)$。')


if __name__ == '__main__':
    run()
    print('Registered number, high-precision and recursion editorials.')
