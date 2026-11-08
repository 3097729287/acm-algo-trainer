"""First loop/representation articles; no answer is inferred from a title."""
from nowcoder_editorials import add, CONTENT, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if 'nowcoder-global::' + str(n) not in existing:
            add(n, *args, **kwargs)

    put(20750, 800, ['输出'], '按原题图片输出六行小飞机。',
        '前两行各是五个空格和两个星号，中间两行各十二个星号，最后两行各是四个空格、一个星号、两个空格、一个星号。逐行输出即可，行末不补空格。原站样例的输入输出均为空，形状以题面图片为准。',
        r'''cout << "     **\n     **\n************\n************\n    *  *\n    *  *";''',
        '图案使用半角空格与星号；不能把原站空白样例误当作无需输出。', exact=True,
        empty_sample_reason='原站该样例没有任何输入或输出；已查看完整六行原图，逐行重建并另设严格逐字节检查。',
        cases=[{'name': '逐行核对原站飞机图', 'input': '', 'output': '     **\n     **\n************\n************\n    *  *\n    *  *'}])
    put(16740, 1300, ['物理', '区间计数'], '小球从固定横坐标同时下落，小车向左运动，求能被小车接到的球数。',
        '从原图可见，小车初始左侧坐标为 S1，右侧为 S1+L，且向左行驶。球降到车顶高度 K 的时刻为 t1=√((H-K)/5)，降到地面的时刻为 t2=√(H/5)。在这段时间，小车覆盖的横坐标并集是 [S1-Vt2,S1+L-Vt1]。对这个区间与整数球位零到 n-1 取交集即可。按题意给端点加入 10^-5 的容差。',
        r'''long double h, s, v, l, k; long long n; cin >> h >> s >> v >> l >> k >> n;
        long double t1 = sqrtl(max((long double)0, (h - k) / 5));
        long double t2 = sqrtl(h / 5), eps = 1e-5L;
        long long left = max(0LL, (long long)ceill(s - v * t2 - eps));
        long long right = min(n - 1, (long long)floorl(s + l - v * t1 + eps));
        cout << max(0LL, right - left + 1);''',
        '必须先核对图中的行驶方向与 S1 所指边界；球落到车高之前，即使横坐标在车上也不能直接算已接到。',
        cases=[{'input': '5 1 1 1 1 10', 'output': '2'}])
    put(22204, 900, ['循环', '图案'], '读入多组 n，输出上半高 n、总高 2n-1 的实心菱形。',
        '从行号零到 2n-2 枚举。该行距离中间行的距离 d=|i-(n-1)|，行首有 d 个空格，随后有 2(n-d)-1 个星号。多组数据连续输出，无额外空行。',
        r'''int n; while (cin >> n) {
            for (int i = 0; i < 2 * n - 1; i++) {
                int d = abs(i - (n - 1)); cout << string(d, ' ') << string(2 * (n - d) - 1, '*') << '\n';
            }
        }''', '本题输入没有组数 T，循环读到文件结束。', complexity=r'每组输出 $O(n^2)$ 个字符，使用 $O(n)$ 临时字符串空间。')
    put(22208, 800, ['循环', '格式化输出'], '第 i 行输出 i 个连续整数，从一开始，每个数至少占四列。',
        '用一个自增计数器记录下一个待输出的数，外层控制行数、内层控制该行数量，每次使用 setw(4)。宽度是最小宽度，大于四位的数字仍完整输出。',
        r'''int n; cin >> n; int value = 1;
        for (int i = 1; i <= n; i++) { for (int j = 0; j < i; j++) cout << setw(4) << value++; cout << '\n'; }''',
        '此处各数字靠字段宽度衔接，不另加分隔空格。', complexity=r'时间 $O(n^2)$，除输出缓冲外额外空间 $O(1)$。')
    put(22209, 900, ['循环', '图案'], '打印从 A 到指定大写字母的对称字母金字塔。',
        '若共有 n 层，第 i 层先输出 n-i 个空格，再输出从 A 到第 i 个字母的递增串，最后从前一个字母递减回 A。中心字母只出现一次。',
        r'''char last; cin >> last; int n = last - 'A' + 1;
        for (int i = 1; i <= n; i++) {
            cout << string(n - i, ' ');
            for (int j = 0; j < i; j++) cout << char('A' + j);
            for (int j = i - 2; j >= 0; j--) cout << char('A' + j);
            cout << '\n';
        }''', '下降半边从 i-2 开始，避免中心字母重复。', complexity=r'时间 $O(n^2)$，临时字符串空间 $O(n)$，其中 $n≤26$。')
    put(214218, 900, ['循环', '图案'], '每组给定奇数总高度 n，输出星号菱形。',
        '中间行为 n/2。第 i 行距离中间行 d=|i-n/2|，前导空格数为 d，星号数为 n-2d。逐行输出，不输出行末空格。',
        r'''int t; cin >> t; while (t--) {
            int n; cin >> n;
            for (int i = 0; i < n; i++) { int d = abs(i - n / 2); cout << string(d, ' ') << string(n - 2 * d, '*') << '\n'; }
        }''', '这里的 n 是总行数，与上下金字塔题中的半高含义不同。', complexity=r'每组时间 $O(n^2)$，临时空间 $O(n)$。')
    put(22056, 900, ['循环', '图案'], '多组读入 n，打印总高 2n+1 的右向箭形。',
        '中间行下标为 n。第 i 行令 d=|i-n|，先输出 2d 个空格，再输出 n-d+1 个星号。上下两半通过绝对值统一。',
        r'''int n; while (cin >> n) {
            for (int i = 0; i <= 2 * n; i++) { int d = abs(i - n); cout << string(2 * d, ' ') << string(n - d + 1, '*') << '\n'; }
        }''', '缩进每层相差两个空格，星号数每层相差一个，不能套普通菱形公式。', complexity=r'每组时间 $O(n^2)$，临时空间 $O(n)$。')
    put(22156, 800, ['循环', '数列'], '求一到 n 的交错和，奇数项加、偶数项减。',
        '按照定义枚举每个整数，奇数加到答案中，偶数从答案中减去。n 不超过一百，直接累加足够。',
        r'''int n; cin >> n; int ans = 0; for (int i = 1; i <= n; i++) ans += (i % 2 ? i : -i); cout << ans;''',
        '第一项为正，第二项为负。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(22157, 800, ['循环', '浮点运算'], '计算调和数列前 n 项和。',
        '枚举分母 i，将 1.0/i 累加到 double 变量。输出足够的小数位以满足十万分之一误差。',
        r'''int n; cin >> n; double ans = 0; for (int i = 1; i <= n; i++) ans += 1.0 / i;
        cout << fixed << setprecision(9) << ans;''', '写成 1/i 会执行整数除法，第二项起都变零。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(22158, 900, ['循环', '数列'], '累加分母为奇数交错前缀和的倒数，并保留三位小数。',
        '分母依次为 1、1-3、1-3+5 等。循环维护当前分母，奇数步加 2i-1，偶数步减 2i-1，再把其浮点倒数加入答案。分母实际交替为正 i 和负 i，始终不会为零。',
        r'''int n; cin >> n; long long denominator = 0; long double ans = 0;
        for (int i = 1; i <= n; i++) { denominator += (i % 2 ? 2LL * i - 1 : -(2LL * i - 1)); ans += 1.0L / denominator; }
        cout << fixed << setprecision(3) << ans;''', '倒数的分母是当前整段交错和，而不是新加入的单个奇数。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。',
        cases=[{'input': '3', 'output': '0.833'}])
    put(22159, 800, ['循环', '前缀和'], '求一到 i 的和，再把这些前缀和从 i=1 累加到 n。',
        '维护 prefix 表示当前 1+…+i，每次先加上 i，再将 prefix 加入总答案。没有必要为每个 i 重新从一循环。',
        r'''int n; cin >> n; long long prefix = 0, ans = 0; for (int i = 1; i <= n; i++) { prefix += i; ans += prefix; } cout << ans;''',
        '累加到答案中的是前缀和，不是单独的 i。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(22160, 800, ['递推'], '求首两项为一的斐波那契数列第 n 项。',
        '用 a、b 保存相邻两项，从第三项起令 next=a+b，再同步前移。n=1 或二时循环不执行，输出一。',
        r'''int n; cin >> n; long long a = 1, b = 1; for (int i = 3; i <= n; i++) { long long next = a + b; a = b; b = next; } cout << b;''',
        '更新 b 前先保存两项的和，否则容易误用已经更新的 a。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。', cases=[{'input': '46', 'output': '1836311903'}])
    put(22161, 900, ['递推'], '首三项为零、一、一，之后每项等于前三项按一、二、一的权重求和。',
        '建立长度二十一的数组，初始化前三项。按下标递增计算 a[i]=a[i-3]+2a[i-2]+a[i-1]，所需的三项均已存在。',
        r'''int n; cin >> n; long long a[21] = {}; a[2] = a[3] = 1;
        for (int i = 4; i <= n; i++) a[i] = a[i - 3] + 2 * a[i - 2] + a[i - 1]; cout << a[n];''',
        '只有倒数第二项乘二；第一项是零，不能照搬斐波那契初始化。', complexity=r'时间与数组空间均为 $O(n)$。')
    for n in [14748, 22165]:
        put(n, 800, ['循环', '输入输出'], '连续读入多组整数对，分别输出两数之和。',
            '本题没有提前给出数据组数。把 cin>>a>>b 作为 while 条件，每成功读取完整一组就输出一行，文件结束时自动退出。',
            r'''long long a, b; while (cin >> a >> b) cout << a + b << '\n';''',
            '不能把第一组的第一个数误当成组数，也不能只处理一组。', complexity=r'若有 $T$ 组，时间 $O(T)$，额外空间 $O(1)$。')
    put(22166, 800, ['循环', '输入输出'], '先读组数 T，再处理 T 对整数的加法。',
        '第一项是组数，不参与求和。循环 T 次，每次读取 a、b，并独立输出 a+b。',
        r'''int t; cin >> t; while (t--) { int a, b; cin >> a >> b; cout << a + b << '\n'; }''',
        '这里有组数 T，与读到文件结束的版本不同。', complexity=r'时间 $O(T)$，额外空间 $O(1)$。')
    put(22167, 800, ['循环', '输入输出'], '逐组相加，读到两个数同时为零时结束，该组不输出。',
        '先读取一整对，再判断 a==0 且 b==0；如果成立就退出，否则输出和。单独一个零仍是正常数据。',
        r'''int a, b; while (cin >> a >> b) { if (a == 0 && b == 0) break; cout << a + b << '\n'; }''',
        '结束条件需要两个数都为零，不能写成 a==0 或 b==0。', complexity=r'时间 $O(T)$，额外空间 $O(1)$。',
        cases=[{'input': '0 3\n4 0\n0 0\n', 'output': '3\n4'}])
    put(14673, 900, ['枚举', '数位'], '输出一到 n 中既不含数字四、又不是四的倍数的数。',
        '从小到大枚举。先检查余数不为零，再把数字转换为字符串，检查其中找不到字符四。只有两个条件都成立才输出。',
        r'''int n; cin >> n; for (int x = 1; x <= n; x++) if (x % 4 != 0 && to_string(x).find('4') == string::npos) cout << x << '\n';''',
        '不是四的倍数也可能含四，例如四十一仍应被排除。', complexity=r'时间 $O(n\log n)$，数位临时空间 $O(\log n)$。')
    put(15942, 1000, ['位运算'], '对每组有符号整数，统计它的六十四位补码中一的数量。',
        '先将 long long 转成 unsigned long long，转换保留模 2^64 的位模式。再不断读取最低位并逻辑右移，直到无符号数变零；负数也会在六十四次内结束。',
        r'''long long n; while (cin >> n) { unsigned long long x = static_cast<unsigned long long>(n); int ans = 0;
            while (x) { ans += x & 1ULL; x >>= 1; } cout << ans << '\n'; }''',
        '直接右移负的有符号数可能不断补一，导致死循环；先转换为无符号类型。', complexity=r'每组至多六十四步，额外空间 $O(1)$。',
        cases=[{'input': '-1\n0\n-9223372036854775808', 'output': '64\n0\n1'}])
    put(16668, 1200, ['进制转换', '构造'], '把互不相同的 k 的幂的非空和从小到大排序，求第 N 个。',
        '每个幂只可选零次或一次，所以合法数的 k 进制只含零一。对 k≥三，最高不同位决定大小，合法数的顺序与二进制正整数的顺序完全一致。因此把 N 的二进制位依次当成 k 进制位求值。',
        r'''long long k, n; cin >> k >> n; long long power = 1, ans = 0;
        while (n) { if (n & 1) ans += power; n >>= 1; power *= k; } cout << ans;''',
        '第一项对应 N=1，而不是 N=0；无需真的生成前 N 项再排序。', complexity=r'时间 $O(\log N)$，额外空间 $O(1)$。')
    put(208253, 1200, ['进制转换', '构造'], '按样例从小到大排列若干不同三的幂的非空和，求第 k 项。',
        '选不选第 i 个土豆，正好对应三进制第 i-1 位上的零或一。保持位序，把 k 的二进制解释成三进制即可。原文写“第 k 大”，但无限集合没有第 k 大，样例明确采用从小到大的第 k 项。',
        r'''int t; cin >> t; for (int tc = 1; tc <= t; tc++) {
            long long k; cin >> k; long long power = 1, ans = 0;
            while (k) { if (k & 1) ans += power; k >>= 1; power *= 3; }
            cout << "Case #" << tc << ": " << ans << '\n';
        }''', '位数可达三十一，三的幂及答案必须使用 long long。输出含 Case、井号、冒号和空格。',
        complexity=r'每组时间 $O(\log k)$，额外空间 $O(1)$。')
    put(16607, 1100, ['贪心', '模拟'], '按队伍顺序收取二十五元票款，判断能否从零零钱开始完成所有找零。',
        '维护二十五与五十元钞票数量。收五十元时消耗一张二十五；收一百元时优先用一张五十和一张二十五，否则用三张二十五。优先消耗五十元能保留用途更广的二十五元，不会使后续找零更差。',
        r'''int n; cin >> n; int c25 = 0, c50 = 0; bool ok = true;
        for (int i = 0; i < n; i++) {
            int x; cin >> x; if (!ok) continue;
            if (x == 25) c25++;
            else if (x == 50) { if (c25 == 0) ok = false; else { c25--; c50++; } }
            else if (c50 > 0 && c25 > 0) { c50--; c25--; }
            else if (c25 >= 3) c25 -= 3;
            else ok = false;
        }
        cout << (ok ? "YES" : "NO");''', '不能改变排队顺序，也不能用当前这一张一百元给自己找零。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(18414, 900, ['加权平均', '浮点运算'], '用各科绩点和学分计算总绩点，保留一位小数。',
        '分子累加每科绩点乘学分，分母累加学分。全部读完后一次相除并四舍五入输出，避免对每科先舍入带来误差。',
        r'''int n; cin >> n; double sum = 0, credits = 0;
        for (int i = 0; i < n; i++) { double g, s; cin >> g >> s; sum += g * s; credits += s; }
        cout << fixed << setprecision(1) << sum / credits;''', '不同课程的学分不同，不能直接对绩点做普通平均。', complexity=r'时间 $O(n)$，额外空间 $O(1)$。')
    put(16437, 900, ['枚举', '取整'], '只允许买同一种包装，求至少买够 n 支铅笔的最低费用。',
        '对每种包装分别计算需要的包数 ceil(n/size)，用 (n+size-1)/size 完成整数上取整，再乘包价。三种方案取最小值。',
        r'''long long n; cin >> n; long long ans = LLONG_MAX;
        for (int i = 0; i < 3; i++) { long long size, price; cin >> size >> price; ans = min(ans, (n + size - 1) / size * price); } cout << ans;''',
        '不允许混合买包装。单支价格便宜不代表补足整包后的总价最低。')
    put(14516, 800, ['循环', '计数'], '统计给出的整数中一、五、十分别出现多少次。',
        '用下标零到十的频次数组，每读到一个数就增加对应位置。最后按一、五、十的顺序输出三个计数。',
        r'''int k; cin >> k; int count[11] = {}; for (int i = 0; i < k; i++) { int x; cin >> x; count[x]++; }
        cout << count[1] << ' ' << count[5] << ' ' << count[10];''', '题目正文规定只有一组输入，不要把 k 当作测试组数。', complexity=r'时间 $O(k)$，额外空间 $O(1)$。')
    put(14669, 1300, ['贪心', '排序'], '选最多国家互相建立外交关系，每份使馆占一块地，有外交关系的国家还需预留一块地。',
        '选 k 个国家时，每国要放其余 k-1 国的大使馆，另预留一块，所以每个入选国家至少有 k 块土地。按土地数降序排列，若第 k 大土地数≥k，则前 k 国可组成方案。扫描最大的合法 k 即可。',
        r'''int t; cin >> t; while (t--) {
            int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; sort(a.rbegin(), a.rend());
            int ans = 0; for (int i = 0; i < n; i++) { if (a[i] >= i + 1) ans = i + 1; else break; } cout << ans << '\n';
        }''', '不能漏掉备用使馆占用的一块土地；只要求各国都够 k 块，不需要把土地数求和。',
        complexity=r'每组时间 $O(n\log n)$，数组空间 $O(n)$。')


if __name__ == '__main__':
    run()
    print('Registered loop and representation editorials.')
