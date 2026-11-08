"""Reviewed windows, forced propagation, subsequence queries and digit greed."""
from nowcoder_editorials import CONTENT, add, read, review_rating


FLIP = r'''
bool solvable(const vector<string> &a) {
    int n = a.size(), m = a[0].size(), limit = (1 << n) - 1;
    vector<int> initial(m);
    for (int c = 0; c < m; c++) for (int r = 0; r < n; r++) if (a[r][c] == '1') initial[c] |= 1 << r;
    for (int first = 0; first <= limit; first++) {
        int previous = 0, current = first;
        for (int c = 0; c < m; c++) {
            int next = initial[c] ^ previous ^ current ^ ((current << 1) & limit) ^ (current >> 1);
            previous = current; current = next;
        }
        if (current == 0) return true;
    }
    return false;
}
'''


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(282271, 1400, ['双指针', '滑动窗口'], '找出所有元素互异、长度达到全局最大的连续区间，按左端点排序输出。',
        'last[x] 保存数 x 上一次出现的位置。扫描右端点 right，若它的上次位置仍在当前区间内，就把 left 移到那个位置之后；其他元素本来互异，所以新区间重新合法，且是以 right 结尾的最长合法段。比当前最大长度更长就清空旧答案，等长则加入答案。右端点递增、长度相同，最终左端点也必递增。',
        r'''int n; cin >> n; vector<int> last(n + 1, 0); vector<pair<int,int>> answer; int left = 1, best = 0;
        for (int right = 1; right <= n; right++) { int x; cin >> x; left = max(left, last[x] + 1); last[x] = right; int length = right - left + 1;
            if (length > best) { best = length; answer.clear(); } if (length == best) answer.push_back({left, right}); }
        cout << answer.size() << '\n'; for (auto [l, r] : answer) cout << l << ' ' << r << '\n';''',
        'left 只能右移，不能无条件设成 last[x]+1。需要输出所有最长区间，不是只输出最大长度。',
        complexity=r'时间与空间均为 $O(n)$。')
    put(285843, 1400, ['滑动窗口', '字符串'], '找包含全部二十六种小写字母的最短连续子串。',
        '窗口维护各字母次数与已出现种类数。右端加入一个字符后，只要种类数为二十六，就用当前长度更新答案，再删去左端字符尝试缩短；某种次数变零时窗口不再合法，继续扩张右端。每个端点都只向右走。',
        r'''string s; cin >> s; int count[26] = {}, kinds = 0, left = 0, answer = INT_MAX;
        for (int right = 0; right < (int)s.size(); right++) { if (count[s[right] - 'a']++ == 0) kinds++;
            while (kinds == 26) { answer = min(answer, right - left + 1); if (--count[s[left] - 'a'] == 0) kinds--; left++; } }
        cout << (answer == INT_MAX ? -1 : answer);''',
        '重复字母不增加种类数；删字符后只有次数变为零才减少种类。窗口长度的理论下限是二十六。',
        complexity=r'时间 $O(|s|)$，频次数组额外空间 $O(1)$。',
        cases=[{'input': 'abcdefghijklmnopqrstuvwxyz', 'output': '26'}])
    put(285845, 1700, ['双指针', '环形数组'], '在边长不等的圆环上选两点，最大化顺、逆时针距离的较小值。',
        '设圆周长为 total。两点间顺时针距离为 d 时，实际距离 min(d,total-d) 在 d 接近 total/2 时最大。把环复制一遍，用前缀和得到距离；枚举左端点，让右指针尽量靠近但不超过半周，再检查该点与下一个点。边长都为正，左端前进时最优右端不会后退，因此双指针线性完成。若第一条边就超过半周，也检查它，此时半周之前没有其他不同的点。',
        r'''int n; cin >> n; vector<long long> a(n), prefix(2 * n + 1); for (auto &x : a) cin >> x; for (int i = 0; i < 2 * n; i++) prefix[i + 1] = prefix[i] + a[i % n];
        long long total = prefix[n], answer = 0; int right = 1;
        for (int left = 0; left < n; left++) { right = max(right, left + 1); while (right + 1 < left + n && 2 * (prefix[right + 1] - prefix[left]) <= total) right++;
            for (int end = right; end <= right + 1 && end < left + n; end++) { long long d = prefix[end] - prefix[left]; answer = max(answer, min(d, total - d)); } }
        cout << answer;''',
        '每组只输入 n 个间隔；题面末行描述仍指第 n 个间隔。只比较直线距离或直接输出半周都会错误。用 long long 避免翻倍溢出。',
        complexity=r'时间、空间均为 $O(n)$。',
        cases=[{'input': '3\n100\n1\n1', 'output': '2'}, {'input': '2\n1\n100', 'output': '1'}])
    put(285847, 1400, ['递推', '枚举'], '仅第一列可放雷，第二列给出相邻三格雷数，统计所有合法布雷。',
        '记第一列第 i 格是否有雷为 x[i]，边界 x[0]=x[n+1]=0。只需枚举 x[1] 为零或一；由 a[i]=x[i-1]+x[i]+x[i+1]，每个后续 x[i+1] 都被唯一确定。递推出的值必须为零或一，最后还必须满足棋盘外的 x[n+1]=0。统计两次尝试中合法的个数。',
        r'''int n; cin >> n; vector<int> a(n + 1); for (int i = 1; i <= n; i++) cin >> a[i]; int answer = 0;
        for (int first = 0; first <= 1; first++) { int previous = 0, current = first; bool valid = true;
            for (int i = 1; i <= n; i++) { int next = a[i] - previous - current; if (next < 0 || next > 1 || (i == n && next != 0)) { valid = false; break; } previous = current; current = next; } answer += valid; }
        cout << answer;''',
        '越出上下边界均无雷，最后一项必须专门检查。后续位置已被方程强迫，不需要枚举二的 n 次方种布局。',
        complexity=r'时间 $O(n)$，保存输入 $O(n)$。',
        cases=[{'input': '1\n1', 'output': '1'}, {'input': '1\n2', 'output': '0'}])
    flip_idea = '对同一格按两次会抵消，操作顺序也不影响结果，所以每格只需考虑按或不按。沿列处理，枚举第一列的全部按键方案；第一列按完后，若仍有灯亮，唯一还能改变它的就是下一列同一行的按键，因此第二列按法被唯一确定，后面依此类推。用 n 位整数表示一列，上一列按键、自身按键以及自身按键上下移一位的异或，就是已有影响。递推出末列之后所需的虚拟下一列按键必须为零，才表示末列也已熄灭。'
    for number, rating, body in [(285342, 1500, 'vector<string> a(4); for (auto &row : a) cin >> row; cout << (solvable(a) ? "YES" : "NO");'),
                                  (285340, 1700, 'int n, m; cin >> n >> m; vector<string> a(n); for (auto &row : a) cin >> row; cout << (solvable(a) ? "YES" : "NO");')]:
        put(number, rating, ['枚举', '状态压缩', '递推'], '判断能否通过按键翻转自身及上下左右灯，使全部灯关闭。',
            flip_idea, body, '困难版只有行数 n 不超过十，必须沿列推进来枚举 2^n 种首列，而不是枚举可能长达一百的首行。左移后屏蔽超出 n 位的部分。',
            declarations=FLIP, complexity=r'时间 $O(nm+2^n m)$，额外空间 $O(m)$（不计输入矩阵）。')
    review_rating(285230, 2500, '逐条核对为 CF333E Summer Earnings，n<=3000、三等圆与最大最小点距完全相同。原站当前评级为2500，超过2300；常规全边排序加位集查三角形需要二次边存储与位集优化。',
                  origin={'url': 'https://codeforces.com/problemset/problem/333/E', 'rating': 2500, 'ratingVerifiedAt': '2026-11-08', 'platform': 'Codeforces'}, estimate=False)
    put(285865, 800, ['数学'], '一到 n 中恰有一个学生缺席，找出他的学号。',
        '完整学号总和为 n(n+1)/2。逐个减去到场的 n-1 个不同学号，最后剩下的就是缺席学号。',
        r'''long long n; cin >> n; long long answer = n * (n + 1) / 2; for (int i = 0; i < n - 1; i++) { int x; cin >> x; answer -= x; } cout << answer;''',
        '总和超过 int，用 long long 计算乘法。n=1 时没有到场学号，直接输出一。',
        complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(285871, 1000, ['集合', '字符串'], '已知全班字符串学号，删去到场者，按字典序输出两位缺席者。',
        '用有序集合保存全部学号，读到一个到场学号就删除。剩下的元素就是缺席者，集合遍历天然按字典序排列。',
        r'''int n; cin >> n; set<string> absent; for (int i = 0; i < n; i++) { string s; cin >> s; absent.insert(s); }
        for (int i = 0; i < n - 2; i++) { string s; cin >> s; absent.erase(s); } for (const auto &s : absent) cout << s << '\n';''',
        '学号含大小写字母和数字，需要保存字符串并按完整字符串字典序比较；不能转为整数。',
        complexity=r'学号最大长度 $L=20$，时间 $O(nL\log n)$，空间 $O(nL)$。')
    put(285867, 1500, ['二分查找', '子序列', '字符串'], '预处理一个长串，多次判断给定字符串是否为其子序列。',
        '分别保存每种字母在 s 中出现的所有下标。匹配一个查询时，维护已匹配到的位置 previous；对查询的每个字母，在它的下标列表里二分找第一个大于 previous 的位置。找不到就失败。每次尽量用最早位置，只会给后续留下更多空间，因此贪心匹配充分且必要。相比每次扫描完整 s，查询只处理自身字符。',
        r'''string s; cin >> s; vector<int> positions[26]; for (int i = 0; i < (int)s.size(); i++) positions[s[i] - 'a'].push_back(i);
        int q; cin >> q; while (q--) { string t; cin >> t; int previous = -1; bool valid = true; for (char c : t) { const auto &v = positions[c - 'a']; auto it = upper_bound(v.begin(), v.end(), previous); if (it == v.end()) { valid = false; break; } previous = *it; } cout << (valid ? "YES\n" : "NO\n"); }''',
        '下一位置必须严格大于上一位置，重复字母不能复用同一下标。每条查询都要从 previous=-1 重新开始。',
        complexity=r'设查询总长度为 $Q$，时间 $O(|s|+Q\log |s|)$，额外索引空间 $O(|s|)$。')
    put(285879, 1300, ['排序', '贪心', '字符串'], '重排正整数并连接，得到最大的十进制数。',
        '把每个数当作字符串。两个相邻串 a、b 应在 a+b>b+a 时把 a 放前面；如果一个排列存在相反的相邻顺序，交换这两项就能使完整连接串变大。因此按该比较规则排序，再依次输出。这个比较对应重复串的字典序，满足排序所需的严格弱序。',
        r'''int n; cin >> n; vector<string> a(n); for (auto &x : a) cin >> x; sort(a.begin(), a.end(), [](const string &x, const string &y) { return x + y > y + x; }); for (const auto &x : a) cout << x;''',
        '按数值或单个字符串的字典序降序都不保证最大；例如 9 应放在 91 之前。比较相等时返回 false，不能写大于等于。',
        complexity=r'单串最多 $L=10$ 位，时间 $O(nL\log n)$，空间 $O(nL)$。')
    put(285906, 1300, ['贪心', '构造'], '构造位数为 m、数位和为 s 的最小和最大非负十进制整数。',
        '除单个零外，多位数首位不能为零；若 s 为零或超过 9m 就无解。最大值从高位开始尽量填九。最小值则从高位枚举当前可用的最小数字 d，要求剩余数位和非负且不超过剩下位数的九倍；该条件充分，所以选第一个可行 d 即可。每一步选最小可行前缀，整体即最小。',
        r'''int t; cin >> t; while (t--) { int m, s; cin >> m >> s; if (m == 1 && s == 0) { cout << "0 0\n"; continue; } if (s == 0 || s > 9 * m) { cout << "-1\n"; continue; }
            string minimum, maximum; int remaining = s; for (int i = 0; i < m; i++) for (int d = i == 0 ? 1 : 0; d <= 9; d++) if (remaining >= d && remaining - d <= 9 * (m - i - 1)) { minimum += char('0' + d); remaining -= d; break; }
            remaining = s; for (int i = 0; i < m; i++) { int d = min(9, remaining); maximum += char('0' + d); remaining -= d; } cout << minimum << ' ' << maximum << '\n'; }''',
        '本牛客版本第一行有测试组数，无解只输出一个 -1；不要直接照搬原 Codeforces 版本的输入输出格式。',
        complexity=r'每组时间 $O(10m)$，结果空间 $O(m)$。')


if __name__ == '__main__':
    run()
    print('Registered eleven articles and one verified above-cutoff review.')
