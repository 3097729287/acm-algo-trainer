"""Reviewed simulations with rounding, quoting, and scope boundaries."""
from nowcoder_editorials import add, CONTENT, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(200369, 1700, ['贪心', '字符串'], '最多四舍五入 t 次，每次只能处理小数部分，求最大的最终数并去除小数尾零。',
        '先找小数部分最靠左的至少为五的数字。直接在这里舍入，比先处理更右位置更有利。删去该位及其右侧，将前一位加一；若前一位变成五且还有机会，继续向左舍入。由于起点已经是最靠左的五以上数字，其左边小数位原来都不超过四，向左传递时不会遇到小数九的长进位；只有进到整数部分时，单独处理整数进位并结束。',
        r'''int n; long long t; string s; cin >> n >> t >> s; int dot = s.find('.');
        if (dot < 0) { cout << s; return 0; } int p = dot + 1; while (p < (int)s.size() && s[p] < '5') p++; int cut = s.size();
        while (p < (int)s.size() && p > dot && s[p] >= '5' && t > 0) { t--; cut = p;
            if (p == dot + 1) { s.resize(dot); int j = (int)s.size() - 1; while (j >= 0 && s[j] == '9') { s[j] = '0'; j--; }
                if (j >= 0) s[j]++; else s.insert(s.begin(), '1'); cout << s; return 0; }
            s[p - 1]++; p--;
        }
        s.resize(cut); while (!s.empty() && s.back() == '0') s.pop_back(); if (!s.empty() && s.back() == '.') s.pop_back(); cout << s;''',
        '每次舍入只耗一次机会，之后新出现的五才需要再耗一次。整数中的末尾零不能删；代码只有在仍含小数点的分支删小数尾零。',
        complexity='每个字符最多向左处理一次，时间与字符串空间均为 $O(n)$，不按可能十亿次的 t 循环。',
        cases=[{'input': '6 3\n1.4499', 'output': '2'}, {'input': '6 1\n99.999', 'output': '100'}, {'input': '5 1\n10.00', 'output': '10'}])
    put(13585, 1300, ['模拟', '网格'], '检查九宫格解锁路径是否重复使用数字，或越过了尚未使用的中间点。',
        '把一到九转成三乘三网格坐标。相邻两次选点若行坐标之和、列坐标之和均为偶数，连线中点恰好也是一个网格点；如果它不是两端点，就必须已经被访问。每一步还要检查当前点未曾使用，然后才打上访问标记。',
        r'''string s; while (cin >> s) { bool used[10] = {}, ok = true;
            for (int i = 0; i < (int)s.size(); i++) { int current = s[i] - '0'; if (used[current]) ok = false;
                if (i > 0) { int previous = s[i - 1] - '0', r1 = (previous - 1) / 3, c1 = (previous - 1) % 3, r2 = (current - 1) / 3, c2 = (current - 1) % 3;
                    if ((r1 + r2) % 2 == 0 && (c1 + c2) % 2 == 0) { int middle = (r1 + r2) / 2 * 3 + (c1 + c2) / 2 + 1;
                        if (middle != previous && middle != current && !used[middle]) ok = false; } }
                used[current] = true;
            } cout << (ok ? "YES" : "NO") << '\n';
        }''', '题面只规定这两条规则，不额外要求至少四个点。判断中点时，要使用本次选点之前的访问状态。', complexity='每组时间 $O(|S|)$，访问表空间 $O(1)$。')
    put(13588, 1700, ['字符串', '状态机'], '删除引号外完整配对的块注释，保留字符串、转义引号和未配对的注释符号。',
        '读入整个文件并扫描。当前若在引号内，就保留字符直到对应的非转义引号；转义引号作为普通文本保留。只有在引号外遇到 /* 时才寻找后面的第一个 */，有则整段跳过，没有则余下全部原样保留。注释内的引号与另一个 /* 都不改变它的结束位置。',
        r'''string s((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>()), answer; char quote = 0;
        for (size_t i = 0; i < s.size();) {
            if (s[i] == '\\' && i + 1 < s.size() && (s[i + 1] == '"' || s[i + 1] == '\'')) { answer += s[i++]; answer += s[i++]; continue; }
            if (quote) { char c = s[i++]; answer += c; if (c == quote) quote = 0; continue; }
            if (s[i] == '"' || s[i] == '\'') { quote = s[i]; answer += s[i++]; continue; }
            if (i + 1 < s.size() && s[i] == '/' && s[i + 1] == '*') { auto end = s.find("*/", i + 2);
                if (end == string::npos) { answer += s.substr(i); break; } i = end + 2;
            } else answer += s[i++];
        }
        cout << answer;''',
        '输出需要逐字保留注释之外的空格和换行，不能按单词读取再拼接。未配对的 /* 不是注释，应保留。',
        complexity='时间与输入输出缓冲空间均为 $O(L)$，这里 $L≤5$ KB。', exact=True,
        cases=[{'input': 'a/**/ b', 'output': 'a b'}, {'input': '"/*x*/"/*y*/', 'output': '"/*x*/"'}, {'input': 'a*/b/*', 'output': 'a*/b/*'}])
    put(13814, 1000, ['字符串', '匹配'], '按出现顺序输出验证码中的零、二、四、六、九及它们的英文单词对应的数字。',
        '从左到右枚举每个起点。若当前字符是指定的五种数字就直接输出；否则分别检查 zero、two、four、six、nine 是否从这里开始，匹配就输出对应数字。固定五个模式都很短，直接比较足够。',
        r'''int t; cin >> t; vector<pair<string,char>> words = {{"zero",'0'},{"two",'2'},{"four",'4'},{"six",'6'},{"nine",'9'}};
        while (t--) { string s; cin >> s; for (size_t i = 0; i < s.size(); i++) { if (string("02469").find(s[i]) != string::npos) cout << s[i];
                else for (auto [word, digit] : words) if (s.compare(i, word.size(), word) == 0) { cout << digit; break; } } cout << '\n'; }''',
        '其他数字及其单词都忽略，例如 one、three 不输出。需要匹配完整英文拼写，多个 i 的 siiiiix 不是 six。',
        complexity='固定模式总长为常数，时间 $O(|S|)$，字符串空间 $O(|S|)$。')
    put(212226, 1400, ['贪心', '回文', '构造'], '必须用完给定的各数字次数，构造无前导零的最小回文数。',
        '回文两侧成对，最多只有一个数字出现奇数次，它必须居中。若总长大于一，左半边第一位必须取有至少一对的最小非零数字；没有就无解。先消耗这对作为最外侧，再把剩余左半边按零到九递增排列，接上可选中间数及左半边反转。单个零单独允许。',
        r'''int count[10], length = 0, center = -1, odd = 0; for (int i = 0; i < 10; i++) { cin >> count[i]; length += count[i]; if (count[i] % 2) { odd++; center = i; } }
        if (odd > 1) { cout << -1; return 0; } if (length == 1) { cout << center; return 0; }
        int first = -1; for (int d = 1; d <= 9; d++) if (count[d] >= 2) { first = d; break; }
        if (first == -1) { cout << -1; return 0; } count[first] -= 2; string left(1, char('0' + first));
        for (int d = 0; d <= 9; d++) left += string(count[d] / 2, char('0' + d)); string right = left; reverse(right.begin(), right.end());
        cout << left; if (center != -1) cout << center; cout << right;''',
        '不能把唯一出现一次的非零数挪到开头，它只能居中。全零的多位数违反无前导零要求。',
        complexity='时间与结果空间均为总数字数 $O(L)$。')
    put(16415, 1800, ['栈', '作用域', '复杂度分析'], '检查循环声明是否合法，并比较实际最高 n 次数与给出的复杂度。',
        '用栈保存每个循环的变量、是否本层永不执行、是否实际贡献一个 n 因子。n 当成大于所有常数的哨兵即可比较上下界；常数到 n 的活跃循环贡献一次方，n 到常数的循环不执行。维护当前被阻断层数，使不可执行循环内部不增加指数；但变量声明与 F/E 配对仍照常检查。并列循环取最高指数，嵌套的活跃循环指数相加。',
        r'''int t; cin >> t; while (t--) { int lines; string claimed; cin >> lines >> claimed; int expected = claimed == "O(1)" ? 0 : stoi(claimed.substr(claimed.find('^') + 1));
            struct Frame { int variable; bool dead, contributes; }; vector<Frame> stack; int active[26] = {}, blocked = 0, exponent = 0, maximum = 0; bool error = false;
            for (int line = 0; line < lines; line++) { char command; cin >> command;
                if (command == 'F') { char variable; string x, y; cin >> variable >> x >> y; int id = variable - 'a'; if (active[id] > 0) error = true; active[id]++;
                    int lower = x == "n" ? 1000 : stoi(x), upper = y == "n" ? 1000 : stoi(y); bool dead = lower > upper;
                    bool contributes = blocked == 0 && !dead && x != "n" && y == "n"; stack.push_back({id, dead, contributes});
                    if (dead) blocked++; if (contributes) exponent++; maximum = max(maximum, exponent);
                } else { if (stack.empty()) { error = true; continue; } auto frame = stack.back(); stack.pop_back(); active[frame.variable]--;
                    if (frame.dead) blocked--; if (frame.contributes) exponent--; }
            }
            if (!stack.empty()) error = true; if (error) cout << "ERR\n"; else cout << (maximum == expected ? "Yes\n" : "No\n");
        }''', '不会执行的代码仍可能有重复变量或括号配对错误，语法错误优先输出 ERR。变量只在对应 E 后销毁，后面的并列循环可重用。',
        complexity='每行只进出一次栈，时间与栈空间均为 $O(L)$。',
        cases=[{'input': '1\n6 O(1)\nF i n 1\nF j 1 n\nF i 1 2\nE\nE\nE', 'output': 'ERR'}])
    put(200519, 900, ['枚举', '棋盘'], '只按是否存在三子连线判断井字棋结果，不检查正常轮流落子的合法性。',
        '分别检查三行、三列和两条对角线，共八条线。如果某条线的三个位置都是 A 或 B，就标记对应玩家获胜。两人都赢输出 invalid，只有 A 赢输出 Yes，只有 B 赢输出 No，否则 draw。',
        r'''int t; cin >> t; while (t--) { char a[3][3]; for (auto &row : a) for (char &c : row) cin >> c; bool winA = false, winB = false;
            auto check = [&](char x, char y, char z) { if (x == y && y == z) { if (x == 'A') winA = true; if (x == 'B') winB = true; } };
            for (int i = 0; i < 3; i++) { check(a[i][0], a[i][1], a[i][2]); check(a[0][i], a[1][i], a[2][i]); }
            check(a[0][0], a[1][1], a[2][2]); check(a[0][2], a[1][1], a[2][0]);
            cout << (winA && winB ? "invalid" : winA ? "Yes" : winB ? "No" : "draw") << '\n';
        }''', '空格三个点连成线也不算获胜。题目明确允许一人连下多手，不能额外用棋子个数判 invalid。', complexity='每组固定九格与八条线，时间与空间均为常数。')
    put(201612, 1400, ['线性 DP', '子序列计数'], '忽略大小写，统计 iloveyou 作为子序列的出现次数，并对 20010905 取模。',
        'dp[j] 表示已处理前缀能选出目标前 j 个字母的方案数，dp[0]=1。读入字符 c 后，若它匹配目标第 j 个字母，就把原 dp[j-1] 加到 dp[j]。j 从八往一倒序更新，确保当前字符在一次选择中只用一次；不选当前字符的方案保留在原 dp[j] 中。',
        r'''const int mod = 20010905; string s, target = "iloveyou"; cin >> s; int dp[9] = {1};
        for (unsigned char raw : s) { char c = tolower(raw); for (int j = 8; j >= 1; j--) if (c == target[j - 1]) dp[j] = (dp[j] + dp[j - 1]) % mod; } cout << dp[8];''',
        '子序列不要求连续，但所选下标必须递增。目标中的两个 o 分别属于不同匹配阶段，不能只统计字母频次后相乘。',
        complexity='目标长度固定为八，时间 $O(8|S|)$，DP 额外空间 $O(1)$。')


if __name__ == '__main__':
    run()
    print('Registered quoted-text and scope-sensitive simulations.')
