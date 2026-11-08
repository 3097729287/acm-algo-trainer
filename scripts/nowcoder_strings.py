"""String and matrix simulation editorials; preserved input contracts."""
from nowcoder_editorials import add, CONTENT, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(220705, 1000, ['矩阵', '标记数组'], '判断填满的九乘九盘面是否同时满足各行、各列、各宫一到九各一次。',
        '为每行、每列、每个三乘三宫建立出现标记。位置 (i,j) 所属宫号为 (i/3)*3+j/3。读入数值时检查范围以及三个标记中是否已有这个数，有任何重复即不合法。每组恰有九格，不重复且都在一到九内便意味着每种数字恰一次。',
        r'''bool rows[9][10] = {}, cols[9][10] = {}, boxes[9][10] = {}; bool ok = true;
        for (int i = 0; i < 9; i++) for (int j = 0; j < 9; j++) { int x; cin >> x; int b = i / 3 * 3 + j / 3;
            if (x < 1 || x > 9) { ok = false; continue; }
            if (rows[i][x] || cols[j][x] || boxes[b][x]) ok = false;
            rows[i][x] = cols[j][x] = boxes[b][x] = true;
        }
        cout << (ok ? "YES" : "NO");''', '只检查每行或每列的和等于四十五并不充分，重复值可能抵消。棋盘已经填满，不需要求解数独。')
    put(22230, 1000, ['矩阵', '模拟'], '从左上角向右开始，顺时针螺旋填入一到 n²。',
        '保存当前坐标和方向，按右、下、左、上的次序移动。如果下一步越界或已填过，就顺时针转一次。每次放入下一个整数，因此所有格子恰好填一次。',
        r'''int n; cin >> n; vector<vector<int>> a(n, vector<int>(n)); int row = 0, col = 0, direction = 0;
        int dr[] = {0, 1, 0, -1}, dc[] = {1, 0, -1, 0};
        for (int value = 1; value <= n * n; value++) { a[row][col] = value; int x = row + dr[direction], y = col + dc[direction];
            if (x < 0 || x >= n || y < 0 || y >= n || a[x][y]) { direction = (direction + 1) % 4; x = row + dr[direction]; y = col + dc[direction]; }
            row = x; col = y;
        }
        for (auto &r : a) { for (int j = 0; j < n; j++) { if (j) cout << ' '; cout << r[j]; } cout << '\n'; }''',
        '必须在访问下一格之前检查是否越界。零作为未填标记，因为真正填入的数从一开始。', complexity='时间与矩阵空间均为 $O(n^2)$。')
    put(22231, 1100, ['矩阵', '枚举'], '按斜对角线往返填写蛇形矩阵。',
        '同一条斜线上的格子满足 row+col=s。s 为奇数时行号递增，s 为偶数时行号递减。每条斜线可用的行号范围是 max(0,s-n+1) 到 min(n-1,s)，列号由 s-row 得到。',
        r'''int n; cin >> n; vector<vector<int>> a(n, vector<int>(n)); int value = 1;
        for (int s = 0; s <= 2 * n - 2; s++) { int lo = max(0, s - n + 1), hi = min(n - 1, s);
            if (s % 2) { for (int i = lo; i <= hi; i++) a[i][s - i] = value++; }
            else { for (int i = hi; i >= lo; i--) a[i][s - i] = value++; }
        }
        for (auto &row : a) { for (int j = 0; j < n; j++) { if (j) cout << ' '; cout << row[j]; } cout << '\n'; }''',
        '这是斜对角蛇形，不是逐行左右往返。跨过主反对角线后，每条斜线的长度会递减。', complexity='时间与矩阵空间均为 $O(n^2)$。')
    put(15056, 900, ['排序'], '将多个时、分、秒三元组按时间递增排列。',
        '把每条时间保存为 tuple。tuple 的默认比较按第一项、第二项、第三项依次比较，正好等于按时、分、秒排序。输出仍使用三个整数，不改成带冒号的格式。',
        r'''int n; cin >> n; vector<tuple<int, int, int>> a(n); for (auto &[h, m, s] : a) cin >> h >> m >> s;
        sort(a.begin(), a.end()); for (auto [h, m, s] : a) cout << h << ' ' << m << ' ' << s << '\n';''',
        '题目举例有冒号，但实际输入输出要求都是空格分隔的三个整数。', complexity=r'时间 $O(n\log n)$，数组空间 $O(n)$。')
    put(213927, 900, ['排序', '整数运算'], '按点到原点的距离平方递增输出坐标及距离平方。',
        '平方距离为 x²+y²，与真实距离具有相同大小顺序，无须开根。坐标可接近一百万，平方距离用 long long；稳定排序让同距点保留输入顺序。',
        r'''int n; cin >> n; struct Point { long long x, y, distance; }; vector<Point> a(n);
        for (auto &p : a) { cin >> p.x >> p.y; p.distance = p.x * p.x + p.y * p.y; }
        stable_sort(a.begin(), a.end(), [](const Point &a, const Point &b) { return a.distance < b.distance; });
        for (auto p : a) cout << p.x << ' ' << p.y << ' ' << p.distance << '\n';''',
        '只把距离变量声明为 long long 还不够，参与乘法的坐标也要先使用 long long。', complexity=r'时间 $O(n\log n)$，数组空间 $O(n)$。')
    put(16674, 1200, ['模拟', '字符串'], '对同一份逐球记录，分别计算十一分制和二十一分制比分。',
        '先读取到 E 为止并保存 W、L。对每种目标分重放一次：加分后若最高分已达到目标且双方相差至少二，就输出本局并清零。重放结束后仍要输出当前局，即使刚好清零也输出 0:0。两种计分之间空一行。',
        r'''string record; char ch; while (cin >> ch && ch != 'E') record += ch;
        auto score = [&](int target) { int a = 0, b = 0; for (char c : record) {
            if (c == 'W') a++; else b++;
            if (max(a, b) >= target && abs(a - b) >= 2) { cout << a << ':' << b << '\n'; a = b = 0; }
        } cout << a << ':' << b << '\n'; };
        score(11); cout << '\n'; score(21);''',
        '达到十一或二十一不一定结束，平分后必须净胜两分。忽略 E 后面的全部内容。', complexity='时间与记录空间均为 $O(L)$。',
        cases=[{'input': 'E', 'output': '0:0\n\n0:0'}, {'input': 'WWWWWWWWWWWE', 'output': '11:0\n0:0\n\n11:0'}])
    put(204868, 900, ['分支', '循环关系'], '按大象吃虎、虎吃猫、猫吃鼠、鼠吃象的四环关系判断输赢。',
        '把四种棋子按环顺序编号零到三。若第一种的后一项等于第二种，就为 win；反向关系成立则为 lose，其余都是 tie，包括同种与相隔两步。',
        r'''vector<string> names = {"elephant", "tiger", "cat", "mouse"}; string a, b; cin >> a >> b;
        int x = find(names.begin(), names.end(), a) - names.begin(), y = find(names.begin(), names.end(), b) - names.begin();
        if ((x + 1) % 4 == y) cout << "win"; else if ((y + 1) % 4 == x) cout << "lose"; else cout << "tie";''',
        '不是所有不同种棋子都分胜负，例如大象与猫之间没有吃子关系。')
    put(14831, 800, ['字符串', '模拟'], '将正整数依次拼接，查询第 n 个字符。',
        'n 最大一千，直接从一开始把 to_string(x) 追加到字符串，直到长度至少为 n。字符位置是一开始编号，访问下标 n-1。',
        r'''int n; cin >> n; string s; for (int x = 1; (int)s.size() < n; x++) s += to_string(x); cout << s[n - 1];''',
        '第十位是一十中的一，第十一位是零，跨过九之后每个整数贡献两位。', complexity='生成字符数为 $O(n)$，时间与空间均为 $O(n)$。')
    put(17870, 800, ['字符串', '查找'], '忽略大小写找 Bob 第一次出现的零起始位置，没有则输出负一。',
        '先把整串转成小写，再用 find 查找固定子串 bob。find 返回的第一个位置就是答案，找不到时返回 string::npos，需要显式改成负一。',
        r'''string s; cin >> s; for (char &c : s) c = tolower(static_cast<unsigned char>(c)); auto p = s.find("bob");
        if (p == string::npos) cout << -1; else cout << p;''',
        '题名里的 BFS 是题目自定义名称，这里是字符串匹配，不需要图搜索。', complexity='固定模式长度为三，时间 $O(|S|)$，字符串空间 $O(|S|)$。')
    put(207915, 800, ['字符串', '大小写转换'], '取每个单词首字母并大写，按原顺序连接。',
        '输入只有这一行复合词，可以用 cin 依次读取被空格分隔的单词，立即输出其首字母的大写形式。输出之间不加空格。',
        r'''string word; while (cin >> word) cout << char(toupper(static_cast<unsigned char>(word[0])));''',
        '只取各词首字母，而不是输出原串的所有大写字母。', complexity='时间 $O(L)$，临时空间为最长单词长度。', exact=True)
    put(212819, 1000, ['计数', '分支'], '按题面明确的唯一最短、唯一最长规则，在四个选项中作答。',
        '计算四行长度及最短、最长长度的出现次数。仅有唯一最短而没有唯一最长时选最短；仅有唯一最长而没有唯一最短时选最长。两者同时存在或都不存在时都选 C。',
        r'''int t; cin >> t; string line; getline(cin, line); while (t--) { vector<int> length(4);
            for (int i = 0; i < 4; i++) { getline(cin, line); if (!line.empty() && line.back() == '\r') line.pop_back(); length[i] = line.size(); }
            int lo = *min_element(length.begin(), length.end()), hi = *max_element(length.begin(), length.end());
            int cl = count(length.begin(), length.end(), lo), ch = count(length.begin(), length.end(), hi), ans = 2;
            if (cl == 1 && ch != 1) ans = find(length.begin(), length.end(), lo) - length.begin();
            else if (ch == 1 && cl != 1) ans = find(length.begin(), length.end(), hi) - length.begin();
            cout << char('A' + ans) << '\n';
        }''',
        '四个长度完全不同会同时有唯一最长和最短，按当前定义应选 C。使用 getline 保留选项整行。',
        complexity='每题时间为四个选项总长度，额外空间为最长选项长度。', cases=[{'input': '1\na\nbb\nccc\ndddd', 'output': 'C'}])
    put(213352, 800, ['标记数组'], '统计字符串中不同 ASCII 字符的数量，大小写视为不同。',
        '用长度二百五十六的布尔表记录每个字节是否出现，扫描字符串打标记，再统计为真的位置。',
        r'''string s; cin >> s; bool seen[256] = {}; for (unsigned char c : s) seen[c] = true; int ans = 0; for (bool x : seen) ans += x; cout << ans;''',
        'a 与 A 是不同字符，不能先统一大小写。', complexity='时间 $O(|S|+256)$，额外标记空间 $O(1)$。')
    put(216136, 800, ['字符串', '查找'], '统计昵称中包含 alan 的人数，不区分大小写。',
        '每个昵称单独转小写，检查 find("alan") 是否成功。只要包含一次就把人数加一，同一昵称出现多次 alan 也只计一个人。',
        r'''int n; cin >> n; int ans = 0; while (n--) { string s; cin >> s; for (char &c : s) c = tolower(static_cast<unsigned char>(c)); if (s.find("alan") != string::npos) ans++; } cout << ans;''',
        '昵称可能含数字与符号，但这些字符不影响固定子串检查。', complexity='时间为所有昵称总长度，空间为最长昵称长度。')
    put(15054, 800, ['字符串', '格式化输出'], '在整数的十进制表示中，从右往左每三位插入逗号。',
        '从左往右输出数字。如果当前不是首位，并且从当前位置到末尾的位数为三的倍数，就先输出逗号。这样从右侧数每三位恰好分一组。',
        r'''string s; cin >> s; for (size_t i = 0; i < s.size(); i++) { if (i > 0 && (s.size() - i) % 3 == 0) cout << ','; cout << s[i]; }''',
        '分组是从右侧开始，不能固定每输出三个字符就加逗号，否则首组长度会错误。', complexity='时间与字符串空间均为 $O(|S|)$。',
        cases=[{'input': '1000', 'output': '1,000'}, {'input': '100', 'output': '100'}])
    put(16749, 1500, ['字符串解析', '方程'], '解析只含整数、同一未知数及加减等号的一元一次方程，输出唯一解。',
        '把两侧全部移到左边，累计成 Kx+C=0。扫描时记录所在一侧与当前项符号：等号右侧的项统一乘负一。读数字后若紧跟字母，就加入未知数系数，只有字母时系数为一；否则加入常数。最后解为 -C/K。',
        r'''string s; cin >> s; long long coefficient = 0, constant = 0; int side = 1, sign = 1; char variable = 'x';
        for (size_t i = 0; i < s.size();) {
            if (s[i] == '=') { side = -1; sign = 1; i++; continue; }
            if (s[i] == '+') { sign = 1; i++; continue; }
            if (s[i] == '-') { sign = -1; i++; continue; }
            long long value = 0; bool hasDigit = false;
            while (i < s.size() && isdigit(static_cast<unsigned char>(s[i]))) { hasDigit = true; value = value * 10 + s[i] - '0'; i++; }
            if (i < s.size() && isalpha(static_cast<unsigned char>(s[i]))) { variable = s[i++]; coefficient += side * sign * (hasDigit ? value : 1); }
            else constant += side * sign * value;
        }
        cout << variable << '=' << fixed << setprecision(3) << -(long double)constant / coefficient;''',
        '右侧移项要同时改变未知项与常数项符号；x 与 -x 的省略系数分别是一与负一。',
        complexity='时间与输入字符串空间均为 $O(|S|)$。', cases=[{'input': '-x=2', 'output': 'x=-2.000'}, {'input': 'x+2=3x-4', 'output': 'x=3.000'}])
    put(14112, 800, ['字符串', '前缀'], '统计参赛账号所属学校恰好为 bnu 的队伍数。',
        '账号格式已经固定，只需检查是否以 bnu16- 开头。不能只查找中间是否出现 bnu，以免误计更长学校缩写。每组独立累加。',
        r'''int t; cin >> t; while (t--) { int n; cin >> n; int ans = 0; while (n--) { string s; cin >> s; if (s.rfind("bnu16-", 0) == 0) ans++; } cout << ans << '\n'; }''',
        '队伍编号可能相同但学校不同，不能按编号计数或去重。', complexity='时间为账号字符总数，空间为最长账号长度。')
    put(16585, 1200, ['字符串', '扫描'], '忽略大小写查找完整单词，输出出现次数及第一次的零起始字符位置。',
        '把目标与文章都转小写，但不改变空格与字符位置。沿文章依次找到由空格分隔的每个单词区间，仅当长度与内容均等于目标时计数，并记下第一次的起点。重复空格直接跳过。',
        r'''string word, text; getline(cin, word); getline(cin, text);
        for (char &c : word) c = tolower(static_cast<unsigned char>(c)); for (char &c : text) c = tolower(static_cast<unsigned char>(c));
        int count = 0, first = -1; size_t i = 0;
        while (i < text.size()) { if (text[i] == ' ') { i++; continue; } size_t start = i; while (i < text.size() && text[i] != ' ') i++;
            if (i - start == word.size() && text.compare(start, word.size(), word) == 0) { if (first == -1) first = start; count++; } }
        if (count == 0) cout << -1; else cout << count << ' ' << first;''',
        '目标是独立单词，不能把 Ottoman 中间的 to 当作命中。位置必须包含原文章开头及中间空格占用的字符。',
        complexity='时间与输入空间均为 $O(|文章|+|单词|)$。', cases=[{'input': 'a\n  A  aa a', 'output': '2 2'}])
    put(15940, 1000, ['进制转换', '字符串'], '每五位十进制编号对应一个三字母小写串，依次译出。',
        '从 aaa 的零号开始，三个字母的序号构成二十六进制数。每次截取五位转成整数 v，三位依次是 v/676、v/26%26、v%26，各加上字符 a 后输出。',
        r'''int t; cin >> t; while (t--) { int length; string s; cin >> length >> s;
            for (int i = 0; i < length; i += 5) { int v = stoi(s.substr(i, 5)); cout << char('a' + v / 676) << char('a' + v / 26 % 26) << char('a' + v % 26); } cout << '\n'; }''',
        'aaa 对应 00000，按题目后文的明确映射与样例从零编号，不要错误减一。数字串必须保留前导零后再按五位分组。',
        complexity='时间与输入字符串空间均为 $O(length)$。')
    put(14895, 800, ['字符串', '模拟'], '按顺序在指定闭区间内替换指定字符。',
        'n、m 都不超过一百，直接执行每次操作。把一开始的左右端点减一，逐个检查区间内当前字符是否等于 c1，相等则改成 c2。后续操作读取修改后的串。',
        r'''int n, m; string s; cin >> n >> m >> s; while (m--) { int l, r; char a, b; cin >> l >> r >> a >> b;
            for (int i = l - 1; i < r; i++) if (s[i] == a) s[i] = b; } cout << s;''',
        '区间两端都包含；必须依次修改，不能把所有替换统一套在原串上。', complexity='时间 $O(nm)$，字符串空间 $O(n)$。')
    put(15758, 1000, ['字符串', '贪心'], '多组车厢中选择最前一排、同排最左的一组相邻空座，把它们标成加号。',
        '按输入顺序扫描每排，先检查左侧两座，再检查右侧两座。只有尚未选中时才改写恰好一对。读完后，有方案则输出 YES 和全部座位，否则只输出 NO。',
        r'''int n; while (cin >> n) { vector<string> a(n); bool found = false;
            for (string &s : a) { cin >> s; if (!found && s[0] == 'O' && s[1] == 'O') { s[0] = s[1] = '+'; found = true; }
                else if (!found && s[3] == 'O' && s[4] == 'O') { s[3] = s[4] = '+'; found = true; } }
            if (!found) cout << "NO\n"; else { cout << "YES\n"; for (string s : a) cout << s << '\n'; }
        }''',
        '不能跨过道选择中间两座。原题样例包含多组输入，需读到文件结束。', complexity='每组时间与座位数组空间均为 $O(n)$。')
    put(15661, 1100, ['计数', '矩阵'], '在固定六乘六字符表中，找出同时处于最高频行与最高频列的所有字符。',
        '先将数字与大写字母依次编号零到三十五，行号为编号整除六、列号为编号模六。每个字符为对应行列各贡献一次。求行频率最大值与列频率最大值，再按编号递增输出两个条件都满足的字符。',
        r'''int t; cin >> t; const string alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        while (t--) { string s; cin >> s; int row[6] = {}, col[6] = {};
            for (char c : s) { int id = c <= '9' ? c - '0' : c - 'A' + 10; row[id / 6]++; col[id % 6]++; }
            int bestRow = *max_element(row, row + 6), bestCol = *max_element(col, col + 6);
            for (int id = 0; id < 36; id++) if (row[id / 6] == bestRow && col[id % 6] == bestCol) cout << alphabet[id]; cout << '\n';
        }''', '找的是所有最大频率行与列的交点，某个交点字符即使没在原串中出现，也可能需要输出。',
        complexity='每组时间 $O(|S|+36)$，除输入字符串外额外空间 $O(1)$。')
    put(16422, 1100, ['排序', '取余'], '每位读者指定编码后缀，求满足后缀的最小图书编码。',
        '先将所有图书编码递增排序。后缀长度为 d 时，编码的最后 d 位就是对 10^d 取余。每个查询从最小编码开始扫描，第一个余数等于需求码的书就是答案，没有则负一。',
        r'''int n, q; cin >> n >> q; vector<long long> a(n); for (auto &x : a) cin >> x; sort(a.begin(), a.end());
        while (q--) { int length; long long code; cin >> length >> code; long long mod = 1; for (int i = 0; i < length; i++) mod *= 10;
            long long ans = -1; for (long long x : a) if (x % mod == code) { ans = x; break; } cout << ans << '\n'; }''',
        '需求码相同但长度不同，应使用不同的模数。重复图书编码无需删除。', complexity=r'排序 $O(n\log n)$，查询合计 $O(nq)$，数组空间 $O(n)$。')
    put(16609, 1200, ['映射', '字符串'], '由已知密文与原文推断双射密码，必须获得全部二十六字母映射后才能译出新密文。',
        '同时维护密文字母到原文和原文字母到密文两个映射。逐位加入对应关系，如果任意一端已有不同对应值则失败。扫描结束后两端都必须覆盖二十六种字母，否则也输出 Failed；成功时逐字符查表译出。',
        r'''string cipher, plain, query; cin >> cipher >> plain >> query; int forward[26], reverseMap[26]; fill(forward, forward + 26, -1); fill(reverseMap, reverseMap + 26, -1); bool ok = true;
        for (size_t i = 0; i < cipher.size(); i++) { int a = cipher[i] - 'A', b = plain[i] - 'A';
            if ((forward[a] != -1 && forward[a] != b) || (reverseMap[b] != -1 && reverseMap[b] != a)) ok = false;
            forward[a] = b; reverseMap[b] = a;
        }
        for (int i = 0; i < 26; i++) if (forward[i] == -1 || reverseMap[i] == -1) ok = false;
        if (!ok) cout << "Failed"; else for (char c : query) cout << char('A' + forward[c - 'A']);''',
        '只建立单向映射会漏掉两个字母共用密字的冲突；即便新密文只使用已知字母，缺少其他字母的映射也仍须失败。',
        complexity='时间 $O(|已知串|+|查询串|)$，映射空间 $O(26)$。')
    put(16560, 1100, ['字符串', '取余'], '给定循环密钥与 Vigenère 密文，恢复保留大小写的原文。',
        '密钥字母忽略大小写，映射为零到二十五的位移。密文的同一位置减去密钥位移，再加二十六取余得到原文字母序号；原文字母的大小写沿用密文，密钥下标对密钥长度取余。',
        r'''string key, cipher; cin >> key >> cipher;
        for (size_t i = 0; i < cipher.size(); i++) { char base = isupper(static_cast<unsigned char>(cipher[i])) ? 'A' : 'a'; int shift = tolower(static_cast<unsigned char>(key[i % key.size()])) - 'a';
            cout << char(base + (cipher[i] - base - shift + 26) % 26); }''',
        '输入第二行是密文，要减密钥位移；直接加位移会再次加密。', complexity='时间 $O(|密文|)$，输入字符串空间 $O(|密钥|+|密文|)$。')
    put(201626, 900, ['集合', '字符串'], '统计输入字符串中有多少种不同内容。',
        '将每个完整字符串插入 set。集合会合并相同键，全部插入后集合大小即为不同字符串数。相同字母组成但顺序不同的字符串仍是不同内容。',
        r'''int n; cin >> n; set<string> values; while (n--) { string s; cin >> s; values.insert(s); } cout << values.size();''',
        '不能排序字符串内部字符；aaa 与 aa 也必须区分。', complexity=r'最长串长为 $L$ 时，时间 $O(nL\log n)$，字符串存储空间 $O(nL)$。')
    put(16654, 1100, ['模拟', '计数'], '按五项独立条件累计每名学生奖学金，输出最高者、最高金额及总金额。',
        '每条奖学金规则分别用一个 if 判断，符合多项就叠加多项。用总和累加全部学生金额；只有当前金额严格超过历史最高时才更新姓名，保证并列选择输入最早者。',
        r'''int n; cin >> n; string bestName; int best = -1, total = 0;
        for (int i = 0; i < n; i++) { string name; int exam, review, papers; char leader, west; cin >> name >> exam >> review >> leader >> west >> papers; int award = 0;
            if (exam > 80 && papers >= 1) award += 8000;
            if (exam > 85 && review > 80) award += 4000;
            if (exam > 90) award += 2000;
            if (exam > 85 && west == 'Y') award += 1000;
            if (review > 80 && leader == 'Y') award += 850;
            total += award; if (award > best) { best = award; bestName = name; }
        }
        cout << bestName << '\n' << best << '\n' << total;''',
        '五项规则不是互斥关系，不能写成 else if。成绩门槛均为严格高于。', complexity='时间 $O(n)$，除姓名外额外空间 $O(1)$。')
    put(14710, 1200, ['逆向思维', '构造'], '从零开始，通过 x→2x+1 或 x→2x+2，构造恰好到 n 的按钮序列。',
        '从目标逆推。奇数只能由 N 按钮得到，前值为 (n-1)/2；偶数只能由 G 按钮得到，前值为 (n-2)/2。每次目标变小，最终到零。记录的是从后往前的按钮，最后反转。',
        r'''long long n; cin >> n; string ans; while (n > 0) { if (n % 2) { ans += 'N'; n = (n - 1) / 2; } else { ans += 'G'; n = (n - 2) / 2; } } reverse(ans.begin(), ans.end()); cout << ans;''',
        '偶数逆推不是直接除二，还需先减二；不反转字符串会把按键顺序颠倒。', complexity=r'时间与输出字符串空间均为 $O(\log(n+1))$。')


if __name__ == '__main__':
    run()
    print('Registered string and remaining matrix editorials.')
