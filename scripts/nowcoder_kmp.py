"""Reviewed KMP transformations and the source's explicitly noncontiguous query."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_kmp_support import EXPLANATION, MATCH_OCCURRENCES, PREFIX_FUNCTION


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(232778, 1800, ['KMP', '前缀函数'], '输出模式串在文本中所有出现位置，并输出模式每个前缀的最长 border 长度。',
        EXPLANATION + '\n\n先对模式串计算 pi，它本身就是最后一行所需答案。再扫描文本，维护当前匹配长度；达到整个模式长度时输出起点 i-|pattern|+2（一基编号），随后退到 pi[matched-1]，继续寻找可能重叠的出现。',
        r'''string text, pattern; cin >> text >> pattern; auto pi = prefixFunction(pattern); int matched = 0;
        for (int i = 0; i < (int)text.size(); i++) { while (matched > 0 && text[i] != pattern[matched]) matched = pi[matched - 1]; if (text[i] == pattern[matched]) matched++; if (matched == (int)pattern.size()) { cout << i - (int)pattern.size() + 2 << '\n'; matched = pi[matched - 1]; } }
        for (int i = 0; i < (int)pi.size(); i++) { if (i) cout << ' '; cout << pi[i]; } cout << '\n';''',
        'border 不含整个前缀本身。找到一次后不能清零匹配长度，否则会漏重叠匹配，例如 ABA 在 ABABA 中出现两次。',
        declarations=PREFIX_FUNCTION, complexity=r'文本长 $n$、模式长 $m$，时间 $O(n+m)$，前缀表空间 $O(m)$。')
    put(15071, 1600, ['KMP', '逻辑推理'], '对每个输入字符串，计算它在所有输入字符串中出现次数的乘积。',
        '只要某个被乘的出现次数为零，答案就为零。设最短字符串长度为 L，所有比 L 长的候选在最短串中都不可能出现，答案必为零；长度为 L 的候选若要在最短串中出现，就只能与它完全相同。因此若多个最短串并不相同，全部答案都是零；否则只需把唯一的最短串当模式，对所有串跑一次 KMP，并将出现次数相乘。最终只有这些最短串的位置输出该乘积，其余输出零。\n\n' + EXPLANATION,
        r'''const long long mod = 998244353; int n; cin >> n; vector<string> strings(n); int shortest = 0; for (int i = 0; i < n; i++) { cin >> strings[i]; if (strings[i].size() < strings[shortest].size()) shortest = i; }
        const string &pattern = strings[shortest]; bool valid = true; for (const auto &s : strings) if (s.size() == pattern.size() && s != pattern) valid = false; long long answer = valid ? 1 : 0;
        if (valid) { auto pi = prefixFunction(pattern); for (const auto &s : strings) { answer = answer * occurrences(s, pattern, pi) % mod; if (answer == 0) break; } }
        for (const auto &s : strings) cout << (s.size() == pattern.size() ? answer : 0) << '\n';''',
        '出现可重叠，且大小写敏感。不能对每个字符串各跑一遍全体匹配，会退化成输入串数乘总长。',
        declarations=PREFIX_FUNCTION + MATCH_OCCURRENCES,
        complexity=r'设总字符数为 $N$，时间 $O(N+n)$，保存全部输入空间 $O(N+n)$。',
        cases=[{'input': '3\na\naa\naaa', 'output': '6\n0\n0'}, {'input': '2\na\nb', 'output': '0\n0'}])
    put(14694, 1800, ['KMP', '差分', '同余'], '统计 A 的长度 m 子段，使它与 B 对位相加后模 k 的结果全相同。',
        '所有结果相同，等价于每一对相邻结果差为零，即 A段[i+1]-A段[i]≡B[i]-B[i+1] (mod k)。因此把 A 转为相邻正向差分模 k，把 B 转为反向差分模 k，问题变成长度 n-1 序列中匹配长度 m-1 序列的出现次数。用整数序列上的 KMP，允许重叠匹配。负差取模后加 k 规范为非负。\n\n' + EXPLANATION,
        r'''int tests; cin >> tests; while (tests--) { int n, m; long long k; cin >> n >> m >> k; vector<long long> a(n), b(m); for (auto &x : a) cin >> x; for (auto &x : b) cin >> x; vector<long long> text(n - 1), pattern(m - 1);
            for (int i = 0; i + 1 < n; i++) text[i] = (a[i + 1] - a[i] + k) % k; for (int i = 0; i + 1 < m; i++) pattern[i] = (b[i] - b[i + 1] + k) % k;
            auto pi = prefixFunction(pattern); cout << occurrences(text, pattern, pi) << '\n'; }''',
        'B 的差分方向与 A 相反。k=1 时全部差分均为零，应该匹配全部 n-m+1 个窗口。',
        declarations=PREFIX_FUNCTION + MATCH_OCCURRENCES, complexity=r'每组时间、空间均为 $O(n+m)$。')
    put(213329, 1800, ['KMP', '贡献法'], '统计 S 的所有连续子串中，有多少个包含完整的 T。',
        '因为 T 的长度正好是 k，和 T 满足 k 匹配就等价于子串内包含 T。按右端点 i 扫描，令 last 是截至 i 已经完整出现的 T 中最靠右的起点（一基编号）。以 i 结尾的子串，左端点选一到 last 时恰好包含一次完整 T，贡献 last 个；没有出现时贡献零。KMP 找到每次出现时更新 last，逐项累加即可，重叠出现不会重复计同一个区间。',
        r'''int n, k; string s, t; cin >> n >> k; s.reserve(n); t.reserve(k); cin >> s >> t; auto pi = prefixFunction(t); int matched = 0, last = 0; long long answer = 0;
        for (int i = 0; i < n; i++) { while (matched > 0 && s[i] != t[matched]) matched = pi[matched - 1]; if (s[i] == t[matched]) matched++; if (matched == k) { last = i - k + 2; matched = pi[matched - 1]; } answer += last; } cout << answer;''',
        '一个子串即使含多次 T 也只算一次，使用最靠右起点统一计数。n 可达一千万，答案要用 long long，字符串预留容量减少内存扩容。',
        declarations=PREFIX_FUNCTION, complexity=r'时间 $O(n+k)$，额外前缀表空间 $O(k)$，另保存两输入串。',
        cases=[{'input': '4 2\naaaa\naa', 'output': '6'}, {'input': '3 1\naaa\nb', 'output': '0'}])
    put(25138, 1500, ['子序列自动机', '字符串'], '按原题的明确定义，判断每个查询串是否可从 s 中按顺序选出，允许不连续。',
        '原题把允许不连续选择的子序列称为子串，例子中 abc 的 ac 也算，故按这个定义处理。预处理 next[i][c]，表示从位置 i 起第一个字符 c 的位置，不存在记 n。从右向左复制下一行并覆盖当前字母即可。查询从位置零开始，每取到一个字母，就跳到它的位置之后；不存在则失败。每次取最早位置，给后面保留的选择最多，因此贪心判定正确。',
        r'''int n, q; string s; cin >> n >> q >> s; vector<array<int,26>> next(n + 1); next[n].fill(n); for (int i = n - 1; i >= 0; i--) { next[i] = next[i + 1]; next[i][s[i] - 'a'] = i; }
        while (q--) { string t; cin >> t; int position = 0; bool valid = true; for (char c : t) { int found = next[position][c - 'a']; if (found == n) { valid = false; break; } position = found + 1; } cout << (valid ? "YES\n" : "NO\n"); }''',
        '必须使用不同且递增的下标，匹配后跳到 found+1。不能按通常的连续子串匹配来解释此题。',
        complexity=r'预处理 $O(26n)$，全部查询 $O(\sum|t|)$，空间 $O(26n)$。')


if __name__ == '__main__':
    run()
    print('Registered five reviewed prefix-function and subsequence articles.')
