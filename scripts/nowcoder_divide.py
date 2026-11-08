"""Reviewed divide-and-conquer problems, including iterative deep-tree code."""
import re

from nowcoder_editorials import CONTENT, ROOT, add, program, read, reviewed_clone


FAST = r'''
class FastInput {
    static const int size = 1 << 16;
    char buffer[size]; int position = 0, available = 0;
    int get() { if (position == available) { available = fread(buffer, 1, size, stdin); position = 0; if (!available) return EOF; } return buffer[position++]; }
public:
    int next() { int c = get(), sign = 1; while (c != '-' && (c < '0' || c > '9')) c = get(); if (c == '-') { sign = -1; c = get(); } long long x = 0; while (c >= '0' && c <= '9') { x = x * 10 + c - '0'; c = get(); } return (int)(x * sign); }
};
'''


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(287775, 900, ['数学', '数位'], '反复求各位数字之和，直到只剩一位。',
        '直接按定义模拟即可：数至少为十时，不断除十、取余求各位和，再替换原数。每轮都会缩小，输入最多十位，很快就会剩一位。也可利用同余九得到正整数的数根 (n-1)%9+1。',
        r'''int n; cin >> n; while (n >= 10) { int sum = 0; while (n) { sum += n % 10; n /= 10; } n = sum; } cout << n;''',
        '停止条件是小于十；不能把九的倍数输出为零。', complexity=r'时间为各轮处理的十进制位数总和，额外空间 $O(1)$。')
    put(285771, 1100, ['位运算', '递推'], '求二进制拆位递推值，以及该值第一次出现的下标。',
        '递推每次去掉最低二进制位，并加上这一位的零或一，因此 f(n) 就是二进制一的个数 k。具有 k 个一的最小整数，要把这些一放在最低的 k 位，得到 2^k-1。零的一数为零，最早下标也为零，统一公式仍成立。',
        r'''int tests; cin >> tests; while (tests--) { unsigned long long n; cin >> n; int ones = __builtin_popcountll(n); cout << ones << ' ' << ((1ULL << ones) - 1) << '\n'; }''',
        '题面正数范围与含零样例不完全一致，代码一并支持零。n 最大 10^18，一的数量小于六十四，移位安全。', complexity=r'每组在固定 64 位字长上计数，时间、空间均为 $O(1)$。')
    put(285781, 1500, ['二叉树', '深度优先搜索', '栈'], '根据左右儿子关系找到不固定的根，输出前、中、后序遍历。',
        '给每个儿子标记有父亲，唯一未被标记的点就是根。用显式栈模拟递归的三个阶段：阶段零先记录前序，再访问左子树；阶段一记录中序，再访问右子树；阶段二记录后序。栈里的阶段表示从相应子树返回后应继续做什么，因此顺序与递归一致。输入允许二十万结点长链，显式栈避免系统调用栈溢出。',
        r'''int n; cin >> n; vector<array<int,2>> child(n + 1); vector<bool> hasParent(n + 1); for (int i = 1; i < n; i++) { int u, v, side; cin >> u >> v >> side; child[u][side] = v; hasParent[v] = true; }
        int root = 1; while (hasParent[root]) root++; vector<int> orders[3]; vector<pair<int,int>> stack{{root, 0}};
        while (!stack.empty()) { auto [u, stage] = stack.back(); stack.pop_back(); orders[stage].push_back(u); if (stage < 2) { stack.push_back({u, stage + 1}); int v = child[u][stage]; if (v) stack.push_back({v, 0}); } }
        for (const auto &order : orders) { for (int i = 0; i < n; i++) { if (i) cout << ' '; cout << order[i]; } cout << '\n'; }''',
        '根不一定是一，不能按无向邻接表随意确定左右儿子。输入 o=0 为左、o=1 为右。', complexity=r'时间、空间均为 $O(n)$。')
    source = existing['nowcoder-global::204382']
    tree_code = program((ROOT / source['articles']['default']).read_text(encoding='utf-8'))
    tree_code = re.sub(r'#include[^\n]*\n|using namespace std;\n', '', tree_code)
    put(285877, 1700, ['二叉树', '栈', '构造'], '给前序、后序恢复中序，单儿子约定为左儿子。',
        '按前序逐个创建结点，用栈保存尚未完成的祖先路径。每次新结点到来前，若栈顶值等于当前后序值，说明这棵子树已完成，就弹栈并推进后序；新结点接到剩下栈顶的第一个空儿子位置，先左后右。遍历结束后，再用显式栈输出中序。前序决定进入顺序，后序决定返回时机，单儿子自然先接左边。',
        r'''int n; cin >> n; vector<int> pre(n), post(n); for (int &x : pre) cin >> x; for (int &x : post) cin >> x;
        auto answer = Solution().solve(n, pre, post); for (int i = 0; i < n; i++) { if (i) cout << ' '; cout << answer[i]; }''',
        '前序、后序一般不能唯一恢复左右单儿子，本题明确把单儿子放左边。用迭代构造与遍历兼容十万结点长链。', declarations=tree_code,
        complexity=r'每个结点进出各栈一次，时间、空间均为 $O(n)$。')
    if 'nowcoder-global::285769' not in existing:
        reviewed_clone(285769, 16660, '完整核对为同一FBI后序树，n从零到十、2^n位输入与F/B/I分类一致；单字符边界也覆盖。', cases=[{'input': '0\n0', 'output': 'B'}])
    if 'nowcoder-global::285786' not in existing:
        reviewed_clone(285786, 50999, '完整核对同源表达式计算4；新题面明确括号成对、无直接负数字面量、无小数，均是已验证解析器支持的子集，长度不超过30。')
    put(207028, 1400, ['分治', '快速选择'], '多组整数序列中求第 k 小元素，重复值按出现次数计数。',
        '使用 nth_element 把下标 k-1 的元素放到排序后应在的位置，并让左边元素不大于它、右边不小于它。无需把两边内部都排好，因此平均只需线性工作量。输入可达五百万个数，使用分块 fread 快读；累计单个整数时先用 long long，兼容 int 最小值的绝对值。',
        r'''FastInput input; int tests = input.next(); while (tests--) { int n = input.next(), k = input.next(); vector<int> a(n); for (int &x : a) x = input.next(); nth_element(a.begin(), a.begin() + k - 1, a.end()); cout << a[k - 1] << '\n'; }''',
        '第 k 小用零基下标 k-1。不能去重后求第 k 小；各组输入没有排序保证。', declarations=FAST,
        complexity=r'平均选择时间 $O(n)$，标准库可能采用退化保护；保存数组空间 $O(n)$。',
        cases=[{'input': '1\n3 1\n-2147483648 0 2147483647', 'output': '-2147483648'}])
    merge = r'''long long countInversions(vector<int> &a, vector<int> &buffer, int l, int r) {
        if (r - l <= 1) return 0; int mid = (l + r) / 2; long long answer = countInversions(a, buffer, l, mid) + countInversions(a, buffer, mid, r);
        int i = l, j = mid, k = l; while (i < mid && j < r) { if (a[i] <= a[j]) buffer[k++] = a[i++]; else { answer += mid - i; buffer[k++] = a[j++]; } }
        while (i < mid) buffer[k++] = a[i++]; while (j < r) buffer[k++] = a[j++]; copy(buffer.begin() + l, buffer.begin() + r, a.begin() + l); return answer;
    }'''
    put(15163, 1500, ['归并排序', '逆序对'], '统计严格满足前面值大于后面值的下标对。',
        '归并排序分别求左右半段逆序数。合并两个有序半段时，若左端 a[i] 不大于右端 a[j]，先取左端，不增加逆序；否则右端 a[j] 小于左段剩下的全部 mid-i 个元素，这些对一起加入答案。每个跨中点逆序恰在该次合并中计数一次。',
        r'''int n; cin >> n; vector<int> a(n), buffer(n); for (int &x : a) cin >> x; cout << countInversions(a, buffer, 0, n);''',
        '值相等不是逆序，合并时使用小于等于。最多约 n²/2 对，答案用 long long。', declarations=merge,
        complexity=r'时间 $O(n\log n)$，额外空间 $O(n)$。')
    put(20861, 1700, ['排列', '奇偶性'], '不断反转排列区间，只输出每次后的逆序数奇偶性。',
        '排列的逆序奇偶性等于把它变成恒等排列所需交换次数的奇偶性。一个长度 s 的置换环要 s-1 次交换，因此初始奇偶为 (n-置换环数)%2，可在线性时间得到。反转长度 len 的区间恰是 floor(len/2) 次两端交换，每次翻转奇偶，故仅需异或 (len/2)%2。无需真的反转数组或重算逆序。',
        r'''FastInput input; int n = input.next(); vector<int> a(n + 1); for (int i = 1; i <= n; i++) a[i] = input.next(); vector<bool> visited(n + 1); int cycles = 0;
        for (int i = 1; i <= n; i++) if (!visited[i]) { cycles++; for (int j = i; !visited[j]; j = a[j]) visited[j] = true; }
        int parity = (n - cycles) % 2, m = input.next(); string output; output.reserve((size_t)m * 8); while (m--) { int l = input.next(), r = input.next(); parity ^= ((r - l + 1) / 2) % 2; output += parity ? "dislike\n" : "like\n"; } cout << output;''',
        '奇数逆序输出 dislike，偶数输出 like。利用环计数的前提是输入确为一到 n 的排列。', declarations=FAST,
        complexity=r'时间 $O(n+m)$，空间 $O(n+m)$（含批量输出缓冲）。')
    closest = r'''struct Point { long long x, y; };
    vector<Point> points, buffer;
    long long closest(int l, int r) {
        if (r - l <= 1) return LLONG_MAX;
        int mid = (l + r) / 2; long long dividingX = points[mid].x;
        long long best = min(closest(l, mid), closest(mid, r));
        merge(points.begin() + l, points.begin() + mid, points.begin() + mid, points.begin() + r, buffer.begin() + l,
              [](const Point &a, const Point &b) { return a.y < b.y; });
        copy(buffer.begin() + l, buffer.begin() + r, points.begin() + l);
        vector<Point> strip; strip.reserve(r - l);
        for (int i = l; i < r; i++) { auto p = points[i]; if ((p.x - dividingX) * (p.x - dividingX) >= best) continue;
            for (int j = (int)strip.size() - 1; j >= 0; j--) { long long dy = p.y - strip[j].y; if (dy * dy >= best) break; long long dx = p.x - strip[j].x; best = min(best, dx * dx + dy * dy); }
            strip.push_back(p);
        }
        return best;
    }'''
    put(15052, 2200, ['分治', '最近点对', '前缀和'], '最小化 (i-j)² 加上两下标之间按题意求和的平方。',
        '令 prefix[i] 为前 i 个 a 的和，则 g(i,j) 的绝对值是 |prefix[i]-prefix[j]|，式子就是平面点 (i,prefix[i]) 的欧氏距离平方。注意只建立 i=1 到 n 的点，不建立零号点。按横坐标分治求最近点对：递归处理左右两半，设已知最小平方距离 d，只检查到分界线横向距离小于 sqrt(d) 的点。每半内任意两点至少相距 sqrt(d)，将窄条按纵坐标排序后，一个点在纵差小于 sqrt(d) 的范围内只有常数个候选（可由小方格装箱证明）。归并维护纵序，使每层线性。全程比较整数平方。',
        r'''int n; cin >> n; points.resize(n); buffer.resize(n); long long prefix = 0; for (int i = 0; i < n; i++) { long long x; cin >> x; prefix += x; points[i] = {i + 1, prefix}; } cout << closest(0, n);''',
        '递归后数组改成纵坐标顺序，因此必须先保存 dividingX，再递归两半。每层只新建自己的窄条，不按浮点开根号筛选。', declarations=closest,
        complexity=r'时间 $O(n\log n)$，峰值额外空间 $O(n)$。',
        cases=[{'input': '2\n10000 -10000', 'output': '100000001'}])
    put(14731, 1500, ['组合数学', '快速幂'], '累计全部长度 n 的零一串中，前一后一零的下标对总数。',
        '先固定一对位置 i<j，它们必须分别是一、零，其余 n-2 位任意，所以每对贡献 2^(n-2) 个串。位置对有 n(n-1)/2 个，答案为该组合数乘 2^(n-2)，模 10^9+7。n<2 时没有位置对，单独输出零。组合数中的除二用模逆元 500000004。',
        r'''const long long mod = 1000000007; long long n; cin >> n; if (n < 2) { cout << 0; return 0; } long long power = 1, base = 2, exponent = n - 2;
        while (exponent) { if (exponent & 1) power = power * base % mod; base = base * base % mod; exponent >>= 1; }
        cout << (n % mod) * ((n - 1) % mod) % mod * 500000004 % mod * power % mod;''',
        'n 可达 10^18，不能直接先算 n(n-1)。指数保存原始值，不能无条件先对模数取余。',
        complexity=r'时间 $O(\log n)$，额外空间 $O(1)$。')
    put(23046, 1400, ['快速幂', '模运算'], '多次计算 A 的 B 次幂模 P，三者最大 10^18。',
        '按指数二进制做快速幂：若最低位为一就把当前底数乘入结果，再把底数平方、指数右移。每步结果都取模。两个小于 P 的数相乘仍可能接近 10^36，所以乘法先提升到 unsigned __int128，再取模转回 64 位。',
        r'''int tests; cin >> tests; while (tests--) { unsigned long long a, b, p; cin >> a >> b >> p; a %= p; unsigned long long answer = 1 % p;
            while (b) { if (b & 1) answer = (unsigned __int128)answer * a % p; a = (unsigned __int128)a * a % p; b >>= 1; } cout << answer << '\n'; }''',
        '把溢出后的 long long 乘积再取模无效，必须在乘法前提升类型。P=1 时答案始终零。',
        complexity=r'每组时间 $O(\log B)$，额外空间 $O(1)$。')
    put(19115, 1800, ['组合数学', '快速幂'], 'n 个有顺序的人围成环，相邻颜色不同，使用 c 种颜色计数。',
        '环的染色数为 (c-1)^n+(-1)^n(c-1)。可用递推证明：把 n 点环最后一条边先去掉，路径有 c(c-1)^(n-1) 种染法；其中首尾同色者把首尾合并后对应 n-1 点环，所以 C[n]=c(c-1)^(n-1)-C[n-1]。从 C[2]=c(c-1) 开始代入即可归纳得到公式。用快速幂算第一项，再按 n 奇偶加减 c-1。',
        r'''const long long mod = 10007; long long n, c; cin >> n >> c; long long base = c - 1, exponent = n, answer = 1;
        while (exponent) { if (exponent & 1) answer = answer * base % mod; base = base * base % mod; exponent >>= 1; }
        answer += n % 2 ? -(c - 1) : c - 1; cout << (answer % mod + mod) % mod;''',
        '人有固定顺序，旋转后的着色仍算不同，不要再除以 n。奇数环减法后应规范到非负模值。',
        complexity=r'时间 $O(\log n)$，额外空间 $O(1)$。')
    inversions = r'''long long disagreements(vector<array<int,3>> a, int x, int y) {
        sort(a.begin(), a.end(), [=](const auto &u, const auto &v) { return u[x] < v[x]; }); int n = a.size(); vector<int> tree(n + 1); long long result = 0;
        for (int i = 0; i < n; i++) { int rank = a[i][y], count = 0; for (int p = rank; p > 0; p -= p & -p) count += tree[p]; result += i - count; for (int p = rank; p <= n; p += p & -p) tree[p]++; }
        return result;
    }'''
    put(13947, 1900, ['逆序对', '树状数组', '计数'], '三场比赛中，两队都至少有一场排名胜过对方，求这种无序队伍对数。',
        '对任意队伍对，考察三场排名给出的胜负方向。若方向全相同，两队不会互相认为强；若不全相同，必是一边赢两场、另一边赢一场，此时三个比赛对 (a,b)、(a,c)、(b,c) 中恰有两个给出相反方向。因此分别统计两场排名之间的逆序对数，三项相加后除二就是答案。每次按一场排名排序，用树状数组统计另一场的逆序。',
        r'''int n; cin >> n; vector<array<int,3>> ranks(n); for (auto &row : ranks) cin >> row[0] >> row[1] >> row[2]; cout << (disagreements(ranks, 0, 1) + disagreements(ranks, 0, 2) + disagreements(ranks, 1, 2)) / 2;''',
        '每场名次为一到 n 的排列，无并列名次。无序队伍对在三次统计中恰出现两次，所以最后除二。', declarations=inversions,
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    candy = r'''unordered_map<long long,long long> memo{{0,0},{1,0}};
    long long balanced(long long n) { auto found = memo.find(n); if (found != memo.end()) return found->second; long long answer = balanced(n / 2) + balanced(n - n / 2) + n % 2; return memo[n] = answer; }'''
    put(50038, 2000, ['分治', '记忆化', '数学'], '从 n 堆各一颗糖出发，两堆合并代价为大小差，求总成本最小值。',
        '定义 G[0]=G[1]=0，G[n]=G[floor(n/2)]+G[ceil(n/2)]+n%2。它对应尽量等分的合并树：两子堆相等就零代价，不等只差一。记忆化后，每层只会有两个相邻规模，单次询问只产生 O(log n) 个状态。\n\n为什么等分可达最优？关键不等式是 G[a+b]<=G[a]+G[b]+|a-b|。对 a+b 归纳即可证明，按 a、b 奇偶展开 G：例如 a=2u、b=2v+1 且 u<=v，左式展开后分别对 (u,v) 与 (u,v+1) 使用归纳假设，额外项合计恰为 2(v-u)+1=b-a；两者都偶时直接把同一个归纳式乘二；两者都奇时分别对 (u,v+1)、(u+1,v) 使用归纳式，u=v 时取等号，其余情况界更宽。另一种一奇一偶对称。\n\n把这个不等式用于任意合并树的每个节点并相加，所有子堆的 G 抵消，得到实际总代价至少 G[n]，因为初始 G[1]=0。等分递推又恰好实现 G[n]，所以下界可达。',
        r'''int tests; cin >> tests; while (tests--) { long long n; cin >> n; cout << balanced(n) << '\n'; }''',
        '单纯不带记忆化递归会重复计算同样规模。n=0 和 n=1 都不需要合并，不能对零继续递归。', declarations=candy,
        complexity=r'单次新询问至多新增 $O(\log n)$ 状态；哈希查表平均常数，总空间等于已缓存的不同状态数。',
        cases=[{'input': '5\n0\n1\n8\n9\n10', 'output': '0\n0\n0\n3\n4'}])


if __name__ == '__main__':
    run()
    print('Registered fifteen reviewed divide-and-conquer articles.')
