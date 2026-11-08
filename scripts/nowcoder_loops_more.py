"""Remaining elementary simulation and number theory articles."""
from nowcoder_editorials import add, CONTENT, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(214219, 800, ['模拟'], '按给定顺序尝试购买猫粮，买得起就买，买不起跳过，统计购买种数。',
        '题目已经规定了购买决策，没有自由选择空间。维护剩余金额 money，遇到 price≤money 时扣款并增加计数，否则只继续读取下一项。',
        r'''int t; cin >> t; while (t--) { int money, m; cin >> money >> m; int ans = 0;
            for (int i = 0; i < m; i++) { int p; cin >> p; if (p <= money) { money -= p; ans++; } } cout << ans << '\n'; }''',
        '不能按价格排序，也不能遇到买不起的猫粮就结束。', complexity='每组时间 $O(M)$，额外空间 $O(1)$。')
    put(16756, 1300, ['进制转换', '数论'], '将十进制整数转换成指定的负进制，数码使用零到九及大写字母。',
        '反复做除基取余。负进制也要求数码非负，因此若 C++ 余数 r<0，就令 r-=base，并把商加一。这个调整仍保持 n=quotient*base+r。收集余数后反转，零单独输出。',
        r'''long long n; int base; cin >> n >> base; long long original = n; string ans;
        const string digits = "0123456789ABCDEFGHIJ";
        do { long long q = n / base, r = n % base; if (r < 0) { r -= base; q++; } ans += digits[r]; n = q; } while (n != 0);
        reverse(ans.begin(), ans.end()); cout << original << '=' << ans << "(base" << base << ')';''',
        '调整余数后必须同时调整商；输出中保留原十进制数的符号，负进制数本身不用另加负号。',
        complexity=r'时间与数码空间均为 $O(\log_{|base|}(|N|+1))$。', cases=[{'input': '0 -2', 'output': '0=0(base-2)'}])
    put(22200, 900, ['素数', '枚举'], '分别判断 T 个正整数是否为素数。',
        '小于二的数不是素数。其余数只需试除到平方根：若 n=ab 为合数，则 a、b 中至少有一个不超过平方根。找到任意整除因子就判合数，否则判素数。',
        r'''int t; cin >> t; while (t--) { int n; cin >> n; bool prime = n >= 2;
            for (int d = 2; d <= n / d; d++) if (n % d == 0) { prime = false; break; }
            cout << (prime ? "Yes" : "No") << '\n'; }''',
        '一不是素数；输出只有首字母大写。用 d≤n/d 避免平方溢出。', complexity=r'每组时间 $O(\sqrt n)$，额外空间 $O(1)$。')
    put(201610, 1300, ['博弈', '质因数分解'], '双方轮流将一个数拆成两个大于一的因数，无数可拆时当前玩家输，问败者。',
        '设 n 分解质因数后共有 c 个因子，重数也计入。每次拆分让集合元素数增加一，最终必然恰好是这 c 个质因子，所以总操作数固定为 c-1，策略不会改变奇偶性。c≥二且为偶数时先手完成最后一步，败者是 Johnson；否则败者是 Nancy。n=1 时也无合法操作。',
        r'''int n; cin >> n; int count = 0;
        for (int p = 2; p <= n / p; p++) while (n % p == 0) { n /= p; count++; }
        if (n > 1) count++;
        cout << (count >= 2 && count % 2 == 0 ? "Johnson" : "Nancy");''',
        '质因子要按重数计数；输出的是败者而不是胜者。', complexity=r'时间 $O(\sqrt n)$，额外空间 $O(1)$。',
        cases=[{'input': '1', 'output': 'Nancy'}, {'input': '8', 'output': 'Nancy'}, {'input': '16', 'output': 'Johnson'}])
    put(16785, 1100, ['枚举', '数列'], '沿 Cantor 表的斜对角线按 Z 字顺序，输出第 N 个分数。',
        '第 d 条对角线有 d 项，先不断减去整条长度，直到 N≤d，此时 N 是该条内部的一起始偏移。d 为偶数时分子从一递增，为奇数时分子从 d 递减，分子加分母总为 d+1。',
        r'''int n; cin >> n; int diagonal = 1; while (n > diagonal) { n -= diagonal; diagonal++; }
        if (diagonal % 2 == 0) cout << n << '/' << diagonal - n + 1;
        else cout << diagonal - n + 1 << '/' << n;''',
        '本题输出表格里的原分数，不需要约分。方向必须按第一条为 1/1、第二条为 1/2 到 2/1 核对。',
        complexity=r'时间 $O(\sqrt N)$，额外空间 $O(1)$。')
    put(204457, 800, ['扫描', '最值'], '在 n 个整数中选两个，求最大的差值。',
        '任意差都不超过最大值减最小值，直接选这两个极值就能取到上界。读取时同时维护最大与最小值，最后相减。',
        r'''int n; cin >> n; int lo = INT_MAX, hi = INT_MIN; for (int i = 0; i < n; i++) { int x; cin >> x; lo = min(lo, x); hi = max(hi, x); } cout << hi - lo;''',
        '数组可以全负，最大值不能随意初始化为零。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(214227, 800, ['扫描', '统计'], '输出成绩平均分、最高分和最低分。',
        '一次读取中累加总分，并更新最大与最小值。总分除以浮点数 n 得平均值，平均值固定两位，其余按整数输出。',
        r'''int n; cin >> n; int sum = 0, lo = 100, hi = 0;
        for (int i = 0; i < n; i++) { int x; cin >> x; sum += x; lo = min(lo, x); hi = max(hi, x); }
        cout << fixed << setprecision(2) << (double)sum / n << ' ' << hi << ' ' << lo;''',
        '不要对平均值先做整数除法。三个输出的顺序按题目要求。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(207595, 1000, ['贪心', '奇偶性'], '选择若干整堆糖果，使总数为偶数且尽量多。',
        '先求所有糖果的和。若已经为偶数就全部带走；若为奇数，必须去掉奇数总量，最少可去掉最小的一堆奇数糖果。任何其他奇数总量至少包含一堆奇数，去除量不会更小。',
        r'''int n; cin >> n; long long sum = 0; int odd = INT_MAX;
        for (int i = 0; i < n; i++) { int x; cin >> x; sum += x; if (x % 2) odd = min(odd, x); }
        if (sum % 2) sum -= odd; cout << sum;''',
        '总和为奇数时一定存在奇数堆，因此最小奇数一定有定义；允许最终选择零堆。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(210751, 900, ['排序', '去重'], '求不同数值中的最大、次大、次小、最小之间指定的四个差。',
        '先排序并去除重复数值，再取末尾两个与开头两个元素。依次计算最大减次大、最大减次小、次大减次小、次大减最小。重复出现不会改变数值的次序。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x;
        sort(a.begin(), a.end()); a.erase(unique(a.begin(), a.end()), a.end()); int m = a.size();
        cout << a[m - 1] - a[m - 2] << ' ' << a[m - 1] - a[1] << ' ' << a[m - 2] - a[1] << ' ' << a[m - 2] - a[0];''',
        '次大是小于最大值的最大数值，不能让最大值的重复项占据次大位置。', complexity=r'时间 $O(n\log n)$，数组空间 $O(n)$。',
        cases=[{'input': '7\n1 1 2 3 4 5 5', 'output': '1 3 2 3'}])
    put(205453, 1000, ['贪心'], '可以选择每只蚂蚁的初始方向，求全部离开热杆的最早时间。',
        '每只蚂蚁至少需要走到最近的一端，即 min(x,L-x)。让所有蚂蚁都朝更近的一端爬即可同时达到这些下界；全部离开时刻是各自离开时刻的最大值。',
        r'''int length, n; cin >> length >> n; int ans = 0;
        for (int i = 0; i < n; i++) { int x; cin >> x; ans = max(ans, min(x, length - x)); } cout << ans;''',
        '不是把各只蚂蚁的时间相加，它们同时运动。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(21201, 1200, ['思维', '等价转化'], '蚂蚁等速行走、相遇后掉头，求所有蚂蚁离开路径的时间。',
        '两只完全相同的蚂蚁相遇后交换方向，忽略身份就等价于穿过彼此。因此只需分别计算每只蚂蚁保持原方向直到端点的时间：向左为 x，向右为 n-x，再取最大值。',
        r'''int n, m; cin >> n >> m; int ans = 0;
        for (int i = 0; i < m; i++) { int direction, x; cin >> direction >> x; ans = max(ans, direction == 0 ? x : n - x); } cout << ans;''',
        '该转化保留了所有蚂蚁位置的集合及最后离开时刻，但不保留某只蚂蚁的身份轨迹。', complexity='时间 $O(m)$，额外空间 $O(1)$。')
    put(214437, 800, ['字符串', '计数'], '读入多行小写文本，直到单独的句点，统计字符 a 的总数。',
        '题目保证普通行只有小写字母，可以逐段用 cin 读取。遇到字符串等于句点时结束，否则累加这一段中 a 的出现次数。',
        r'''string s; long long ans = 0; while (cin >> s && s != ".") for (char c : s) if (c == 'a') ans++; cout << ans;''',
        '不是只统计最后一行，也不把结束标记计入文本。', complexity='时间 $O(L)$，临时空间为最长行长度，$L$ 为总字符数。')
    put(216200, 800, ['字符串', '模拟'], '把数字字符串中的所有字符五改为星号。',
        '字符串可能有一百万位，无法存进整数类型。逐字符检查，遇到字符五就替换成星号，其余位置保持原样。',
        r'''string s; cin >> s; for (char &c : s) if (c == '5') c = '*'; cout << s;''',
        '需要修改字符串中的字符时使用引用 char&，不能只修改循环变量的副本。', complexity='时间与字符串空间均为 $O(|s|)$。')
    put(22163, 800, ['模拟', '循环'], '重复奇数乘三加一、偶数除二，统计首次变成一所需的操作数。',
        '只要 n 不等于一就执行一次规定变换，并将计数加一。给定范围不超过一百，直接模拟即可。',
        r'''long long n; cin >> n; int steps = 0; while (n != 1) { n = n % 2 ? 3 * n + 1 : n / 2; steps++; } cout << steps;''',
        '输入一时零次操作已经完成；这题需要循环，与单次卡拉兹函数题不同。', complexity='若实际经过 $s$ 步，时间 $O(s)$，额外空间 $O(1)$。', cases=[{'input': '1', 'output': '0'}])
    put(16648, 800, ['扫描', '计数'], '有三十厘米板凳，统计十个苹果中高度不超过伸手高度加三十的数量。',
        '先保存十个高度，再读取伸手高度。能碰到就能摘下，所以对每个苹果检查 height≤reach+30，累加满足条件的个数。',
        r'''int a[10]; for (int &x : a) cin >> x; int reach; cin >> reach; int ans = 0;
        for (int x : a) if (x <= reach + 30) ans++; cout << ans;''',
        '恰好能碰到的苹果也算可摘，比较符号要包含等号。')
    put(16662, 1000, ['模拟'], '逐月收三百元、支付预算、把整百存给妈妈；首次不足输出负月份，否则年末存款返还两成利息。',
        '维护手头 cash 与累计存款 saved。每月加三百再扣预算，若为负则立即输出负的月份；否则把 cash/100 个整百存入，手头只留 cash%100。年末输出 cash+saved*120/100，存款本来是整百，整数计算精确。',
        r'''int cash = 0, saved = 0;
        for (int month = 1; month <= 12; month++) { int expense; cin >> expense; cash += 300 - expense;
            if (cash < 0) { cout << -month; return 0; } saved += cash / 100 * 100; cash %= 100;
        }
        cout << cash + saved * 120 / 100;''', '存给妈妈的钱年内不能取出应急；利息只加到存款上，手头零钱不计息。')
    put(14610, 900, ['模拟', '分支'], '月亮大小在零到十五之间往返，已知连续两天大小，求下一天。',
        '如果最近一天为零，下一天只能为一；如果为十五，下一天只能为十四。其他位置按照前两天的增减方向继续加一或减一。',
        r'''int t; cin >> t; while (t--) { int a, b; cin >> a >> b;
            if (b == 0) cout << 1; else if (b == 15) cout << 14; else cout << b + (b > a ? 1 : -1); cout << '\n'; }''',
        '在零和十五处方向必须翻转，不能一直沿用差值。', complexity='每组时间与额外空间均为 $O(1)$。')
    put(17361, 1100, ['扫描', '状态机'], '只把上升、可选的平顶、下降组成的完整山峰计为一次翻越。',
        '比较相邻高度，忽略相等的边，把剩余变化记为上升或下降。每当最近一次非零变化是上升，而当前变化是下降，就完整经过一个山峰。边界上的单纯上升或下降都不计数。',
        r'''int n; cin >> n; long long previous; cin >> previous; int direction = 0, ans = 0;
        for (int i = 1; i < n; i++) { long long x; cin >> x; int next = (x > previous) - (x < previous);
            if (next != 0) { if (direction == 1 && next == -1) ans++; direction = next; } previous = x; }
        cout << ans;''', '平台可以有任意长度，同高度不应清除前一次上升方向。', complexity='时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '6\n1 2 2 2 1 1', 'output': '1'}, {'input': '4\n4 4 4 4', 'output': '0'}])
    put(216024, 1100, ['模拟', '资源兑换'], '可以用钱买酒、两空瓶换酒或四瓶盖换酒，求最多能喝的总数。',
        '先用非负可用现金买尽可能多的酒，喝完得到对应空瓶和瓶盖。之后只要能兑换，就同时把全部可用空瓶和瓶盖换成新酒，喝完再加入新产生的两种资源，直到都不够兑换。每换一瓶，两倍空瓶数加瓶盖数恰好减少一，所以不会无限兑换。',
        r'''long long m, bottles, caps, price; cin >> m >> bottles >> caps >> price;
        long long ans = max(0LL, m / price); bottles += ans; caps += ans;
        while (bottles >= 2 || caps >= 4) { long long next = bottles / 2 + caps / 4; bottles = bottles % 2 + next; caps = caps % 4 + next; ans += next; }
        cout << ans;''', '负债时只能兑换现有空瓶和瓶盖，不能用负的买酒数量扣掉资源。兑换后喝完还会产生新空瓶、新瓶盖。',
        complexity='按批量兑换，资源规模每轮按比例下降，时间为初始资源规模的对数级，额外空间 $O(1)$。')
    put(213356, 900, ['枚举', '数位'], '统计闭区间里百位乘十位的个位等于原个位的三位数。',
        '合法对象只有一百到九百九十九，直接枚举这九百个候选。提取百位 x/100、十位 x/10%10 与个位 x%10，同时检查候选位于输入区间。',
        r'''int t; cin >> t; while (t--) { long long l, r; cin >> l >> r; int ans = 0;
            for (int x = 100; x <= 999; x++) if (l <= x && x <= r && (x / 100 * (x / 10 % 10)) % 10 == x % 10) ans++;
            cout << ans << '\n'; }''', '定义只针对三位数，不能把区间里的两位数或四位数也按相同规则计入。', complexity='每组固定九百次检查，额外空间 $O(1)$。')
    put(22192, 800, ['枚举', '取余'], '按递增顺序输出一到 n 中对三、五、七取余分别为二、三、二的数。',
        'n 不超过十万，逐个枚举并同时检查三个余数条件，满足就输出。三个条件需要全部成立。',
        r'''int n; cin >> n; for (int x = 1; x <= n; x++) if (x % 3 == 2 && x % 5 == 3 && x % 7 == 2) cout << x << '\n';''',
        '应使用逻辑与，不能任意满足一个条件就输出。', complexity='时间 $O(n)$，额外空间 $O(1)$。')
    put(22169, 900, ['枚举', '字符串'], '按递增顺序输出不超过 n 的正回文数。',
        '从一到 n 枚举，将当前整数转成字符串，复制后反转。如果两串相等，说明从两端读取完全相同，就输出该整数。',
        r'''int n; cin >> n; for (int x = 1; x <= n; x++) { string s = to_string(x), r = s; reverse(r.begin(), r.end()); if (s == r) cout << x << '\n'; }''',
        '零不是本题从一开始的输出对象；个位数天然都是回文。', complexity=r'时间 $O(n\log n)$，临时字符串空间 $O(\log n)$。')
    put(22199, 800, ['数位'], '取整数绝对值后，计算各十进制数位之和。',
        '先把 n 变为非负，再反复取 n%10 加入答案，随后整除十移去最低位。输入为零时循环不执行，答案正好为零。',
        r'''long long n; cin >> n; n = abs(n); int ans = 0; while (n) { ans += n % 10; n /= 10; } cout << ans;''',
        '负号不是数位，不计入总和。', complexity=r'时间 $O(\log(|n|+1))$，额外空间 $O(1)$。')
    put(22212, 800, ['曼哈顿距离'], '在五乘五的空广场，把唯一箱子推到中心，求最少单位步数。',
        '扫描矩阵找到箱子所在行列。横向至少要走到第三列，纵向至少要走到第三行，两方向互不影响，所以答案是 |row-3|+|column-3|。',
        r'''int ans = 0; for (int i = 1; i <= 5; i++) for (int j = 1; j <= 5; j++) { int x; cin >> x; if (x == 1) ans = abs(i - 3) + abs(j - 3); } cout << ans;''',
        '这里没有墙或其他障碍，不需要搜索。按零下标写时中心下标应为二。')
    put(22164, 1000, ['数论', '欧几里得算法'], '求两个正整数的最大公约数。',
        '从较大数反复减小数，不会改变公约数集合。把连续相减合并成一次取余，就得到欧几里得算法 gcd(a,b)=gcd(b,a%b)，直到第二项为零。该写法与更相减损术结果相同且避免悬殊输入的过多相减。',
        r'''int a, b; cin >> a >> b; while (b != 0) { int remainder = a % b; a = b; b = remainder; } cout << a;''',
        '终止时返回非零的 a，而不是已经变为零的 b。', complexity=r'时间 $O(\log\min(a,b))$，额外空间 $O(1)$。', cases=[{'input': '1 1000000', 'output': '1'}])


if __name__ == '__main__':
    run()
    print('Registered remaining loop and elementary math editorials.')
