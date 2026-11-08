"""Greedy decisions and stack invariants, each tied to its NC contract."""
from nowcoder_editorials import add, CONTENT, read, register


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(15128, 1000, ['全排列', '枚举'], '按字典序输出一到八的全部排列，每行末尾没有空格。',
        '从递增排列开始，每次输出当前排列，再用 next_permutation 转到下一个字典序排列。该函数在没有下一个排列时返回 false，因此 do-while 正好输出首项到末项各一次，共 40320 行。原站样例中的英文是占位说明，不能作为真正输出。',
        r'''vector<int> a(8); iota(a.begin(), a.end(), 1);
        do { for (int i = 0; i < 8; i++) { if (i) cout << ' '; cout << a[i]; } cout << '\n'; } while (next_permutation(a.begin(), a.end()));''',
        '必须从递增排列开始，才能覆盖所有排列。输出最后一项之后再调用一次只用于结束循环，不再输出重置的排列。',
        complexity='一般 $n$ 个元素的全排列输出时间 $O(n·n!)$，数组空间 $O(n)$；这里 $n=8$。', checker='all-permutations-1-to-8')
    put(14721, 1200, ['贪心', '排序'], '恰好 K 个巧克力早上吃，其余晚上吃，最大化总甜蜜值。',
        '先假设全部晚上吃，得到基准 sum(B)。把第 i 个改到早上，收益只改变 A[i]-B[i]。因此选差值最大的 K 个，累加这些增量即可。即使增量为负，恰好 K 个的要求也仍需选择。',
        r'''int n, k; cin >> n >> k; vector<long long> a(n), delta(n); for (auto &x : a) cin >> x; long long answer = 0;
        for (int i = 0; i < n; i++) { long long b; cin >> b; answer += b; delta[i] = a[i] - b; }
        sort(delta.rbegin(), delta.rend()); for (int i = 0; i < k; i++) answer += delta[i]; cout << answer;''',
        '不能只按早上甜蜜值排序，选到早上意味着同时失去晚上甜蜜值。总和可达百亿，要用 long long。',
        complexity=r'时间 $O(n\log n)$，数组空间 $O(n)$。', cases=[{'input': '2 0\n1 2\n3 4', 'output': '7'}, {'input': '2 2\n1 2\n3 4', 'output': '3'}])
    put(204117, 1100, ['排序', '贪心'], '从数组中选三个不同位置的正数，组成任意一个非退化三角形。',
        '排序后只需检查相邻三项。若某三个数 x≤y≤z 能成三角形，选定 z 前面最大的两个数也不会更小，因此同样满足两短边之和大于长边。于是只要存在答案，某一组相邻三项一定是答案。',
        r'''int n; cin >> n; vector<long long> a(n); for (auto &x : a) cin >> x; sort(a.begin(), a.end());
        for (int i = 2; i < n; i++) if (a[i - 2] + a[i - 1] > a[i]) { cout << a[i - 2] << ' ' << a[i - 1] << ' ' << a[i]; return 0; }
        cout << "No solution";''',
        '等号只能组成退化线段，不算三角形。同值元素可来自不同位置，不能去重。原题允许任意合法答案，验证按元素重数与三角不等式进行。',
        complexity=r'时间 $O(n\log n)$，数组空间 $O(n)$。', checker='any-valid-triangle', cases=[{'input': '3\n2 2 2', 'output': '2 2 2'}])
    put(16783, 1300, ['排序', '贪心'], '排列整数的连接顺序，使拼成的十进制字符串最大。',
        '比较两个串 a、b 时，应比较 a+b 与 b+a，而不是比较单独数值或字典序。若 a+b 更大，就让 a 在前；相邻交换论证说明每一对都满足该顺序后，总串不能再改进。保存字符串后按这个比较器排序并连接输出。',
        r'''int n; cin >> n; vector<string> a(n); for (string &s : a) cin >> s;
        sort(a.begin(), a.end(), [](const string &a, const string &b) { return a + b > b + a; }); for (string s : a) cout << s;''',
        '前缀关系最容易出错，例如九和九十一应比较 991 与 919，而不是看长串更长。整个答案可能很长，不转成整数。',
        complexity=r'最大串长为 $L$ 时，时间 $O(nL\log n)$，字符串空间 $O(nL)$。')
    put(21874, 1200, ['栈', '括号匹配'], '判断能否从空串反复插入 ab 得到目标串。',
        '把 a 当左括号、b 当右括号。插入 ab 不会使任何前缀中的 b 多于 a，也不改变总数相等。反过来，任何满足前缀余额非负且最终为零的非空串，都有一对相邻 ab；删去它后条件仍成立，递归即可回到空串。因此扫描维护 a 数减 b 数，并拒绝其他字母。',
        r'''string s; cin >> s; int balance = 0; bool ok = true; for (char c : s) {
            if (c == 'a') balance++; else if (c == 'b') balance--; else ok = false; if (balance < 0) ok = false; }
        cout << (ok && balance == 0 ? "Good" : "Bad");''',
        '只检查 a、b 总数相等不够，ba 的总数相等但首个前缀已经不合法。其他小写字母也不能由操作生成。', complexity='时间 $O(|S|)$，额外空间 $O(1)$。')
    put(14326, 1200, ['栈', '模拟'], '列车按一到 N 进入单端车站，判断多组目标出站排列是否可行。',
        '维护下一节尚未进站的车厢编号。对于目标 x，若栈顶还不是 x，就把后续车厢依次压入，直到栈顶为 x 或全部已进站。栈顶匹配就弹出；无法匹配则当前目标不可能实现。每个目标排列都要重新开始。',
        r'''int n; while (cin >> n && n != 0) { while (true) { vector<int> target(n); cin >> target[0]; if (target[0] == 0) break;
                for (int i = 1; i < n; i++) cin >> target[i]; vector<int> st; int next = 1; bool ok = true;
                for (int x : target) { while ((st.empty() || st.back() != x) && next <= n) st.push_back(next++);
                    if (!st.empty() && st.back() == x) st.pop_back(); else { ok = false; break; } }
                cout << (ok ? "Yes" : "No") << '\n'; }
            cout << '\n';
        }''', '输入有两层结束标记：块内单独零结束当前 N 的排列，外层 N 为零结束全部输入。每块结果之后还需空行。',
        complexity='每个目标排列时间与栈空间均为 $O(N)$。')
    put(14893, 1600, ['栈', '贪心', '后缀最值'], '固定入栈顺序，允许随时出栈，求字典序最大的出栈序列。',
        '若栈顶小于尚未读入的最大数，现在弹出它会让下一位变小，所以应继续压栈等待更大数。反之，栈顶已经大于后面所有数，立即输出它就是当前能获得的最大下一项。预处理后缀最大值，每读入一项后反复弹出大于剩余后缀最大值的栈顶。',
        r'''int n; cin >> n; vector<int> a(n), suffix(n + 1), st; for (int &x : a) cin >> x;
        for (int i = n - 1; i >= 0; i--) suffix[i] = max(suffix[i + 1], a[i]); bool first = true;
        for (int i = 0; i < n; i++) { st.push_back(a[i]); while (!st.empty() && st.back() > suffix[i + 1]) {
                if (!first) cout << ' '; first = false; cout << st.back(); st.pop_back(); } }''',
        '不能通过排序改变入栈顺序。比较对象是还没入栈的整个后缀最大值，而不只是紧邻的下一个元素。', complexity='每项进出栈各一次，时间与数组空间均为 $O(n)$。')
    put(15029, 1200, ['栈', '字符串消除'], '从左到右处理小泡泡合并、大泡泡消除，输出稳定后的泡泡串。',
        '用字符串作栈，保持栈内已经不能变化。加入新字符后，若栈顶两项相同，就弹出这两项；两个小 o 还需压入一个大 O，两个大 O 则直接消失。新形成的大 O 可能继续与前一个相消，所以反复检查，直到末尾稳定。',
        r'''int t; cin >> t; while (t--) { string s, st; cin >> s; for (char c : s) { st += c;
                while (st.size() >= 2 && st.back() == st[st.size() - 2]) { char last = st.back(); st.pop_back(); st.pop_back(); if (last == 'o') st += 'O'; }
            } cout << st << '\n'; }''',
        '合并后必须继续处理连锁变化，不能只替换一次相邻字符。大小写分别表示两类泡泡。', complexity='每次变化缩短序列，摊还时间 $O(|S|)$，栈空间 $O(|S|)$。')


if __name__ == '__main__':
    run()
    print('Registered first stack and greedy articles.')
