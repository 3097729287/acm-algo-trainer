"""Reviewed modern statement versions, including their output contracts."""
from nowcoder_editorials import CONTENT, add, alias, read


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(285704, 1200, ['模拟', '字符串'], '按大小写、重复次数、正反序规则，展开合法减号。',
        '从左到右只检查原串。一个减号合法，当且仅当它不在两端、左右同为数字或同为小写字母，且左端严格小于右端。枚举两端之间的字符，按 p1 转换，再重复 p2 次，最后按 p3 决定是否反转整段填充串。两端字符本身仍由原串扫描正常输出。相邻字符之间没有待填字符，合法减号直接消失。',
        r'''int p1, p2, p3; string s; cin >> p1 >> p2 >> p3 >> s;
        auto kind = [](char c) { return isdigit((unsigned char)c) ? 1 : islower((unsigned char)c) ? 2 : 0; };
        for (int i = 0; i < (int)s.size(); i++) { bool expand = s[i] == '-' && i > 0 && i + 1 < (int)s.size() && kind(s[i - 1]) && kind(s[i - 1]) == kind(s[i + 1]) && s[i - 1] < s[i + 1];
            if (!expand) { cout << s[i]; continue; } string fill; for (char c = s[i - 1] + 1; c < s[i + 1]; c++) { char value = p1 == 3 ? '*' : p1 == 2 && islower((unsigned char)c) ? toupper((unsigned char)c) : c; fill += string(p2, value); }
            if (p3 == 2) reverse(fill.begin(), fill.end()); cout << fill; }''',
        '不要把展开后的字符串继续展开，也不要把减号两侧改成大写。a-b 要删减号，a-a 必须保留。',
        complexity=r'设输出长度为 $L$，时间 $O(|s|+L)$，单段缓冲最多 $O(26p_2)$。',
        cases=[{'input': '1 1 1\n-a-b--c-0-a-a', 'output': '-ab--c-0-a-a'}])
    put(285873, 1100, ['队列', '模拟'], '模拟先进先出的单词缓存，统计缓存未命中次数。',
        '队列保存单词进入缓存的顺序，布尔表记录是否在缓存中。命中时什么都不做；未命中时答案加一，若队列已满先移除队首并清掉标记，再把新单词入队。队列与布尔表始终表示同一批单词。',
        r'''int capacity, n; cin >> capacity >> n; queue<int> cache; bool present[1001] = {}; int answer = 0;
        while (n--) { int word; cin >> word; if (present[word]) continue; answer++; if ((int)cache.size() == capacity) { present[cache.front()] = false; cache.pop(); } cache.push(word); present[word] = true; } cout << answer;''',
        '命中不会刷新进入时间，不能按最近使用时间淘汰。单词编号包含零。',
        complexity=r'时间 $O(n)$，队列空间 $O(m)$，编号表固定大小。')
    put(285819, 1000, ['模拟', '几何'], '查询一个点被最后铺下的哪张轴对齐矩形地毯覆盖。',
        '保存每张地毯的左下与右上坐标，从编号最大的一张反向检查。点位于闭矩形内就立即输出，该地毯之后再没有更晚的覆盖；全部未命中则输出 -1。',
        r'''int n; cin >> n; struct Carpet { int x, y, right, top; }; vector<Carpet> a(n); for (auto &c : a) { int w, h; cin >> c.x >> c.y >> w >> h; c.right = c.x + w; c.top = c.y + h; }
        int x, y; cin >> x >> y; for (int i = n - 1; i >= 0; i--) if (a[i].x <= x && x <= a[i].right && a[i].y <= y && y <= a[i].top) { cout << i + 1; return 0; } cout << -1;''',
        '边界和顶点都算覆盖，比较必须包含等号。宽、高不是右上角坐标。',
        complexity=r'时间 $O(n)$，空间 $O(n)$。')
    put(284603, 1800, ['枚举', '向量', '几何'], '在字符矩阵中找四角都是井号的最大正方形，允许倾斜。',
        '取正方形最上方、并列时最左的顶点 P=(r,c)。它向右的相邻顶点可写为 Q=(r+dr,c+dc)，其中 dr>=0、dc>0；把边向量旋转九十度，另一相邻点为 R=(r+dc,c-dr)，最后一点为 S=Q+R-P。枚举 P、dr、dc，先保证四点不越界，再检查四角字符。边长平方为 dr²+dc²，直接比较整数平方，不开根号。这样的规范方向覆盖每个正方形。',
        r'''int n; cin >> n; vector<string> a(n); for (auto &row : a) cin >> row; int best = -1; array<pair<int, int>, 4> answer;
        for (int r = 0; r < n; r++) for (int c = 0; c < n; c++) if (a[r][c] == '#')
            for (int dr = 0; dr <= c && r + dr < n; dr++) for (int dc = 1; c + dc < n && r + dr + dc < n; dc++) {
                int length = dr * dr + dc * dc; if (length <= best) continue;
                if (a[r + dr][c + dc] == '#' && a[r + dc][c - dr] == '#' && a[r + dr + dc][c + dc - dr] == '#') { best = length; answer = {{{r, c}, {r + dr, c + dc}, {r + dc, c - dr}, {r + dr + dc, c + dc - dr}}}; }
            }
        for (auto [r, c] : answer) cout << r + 1 << ' ' << c + 1 << '\n';''',
        '不要求边或内部都是井号。只枚举水平、竖直边会漏掉第二个样例中的倾斜正方形。输出任意一个最大解均可。',
        complexity=r'最坏时间 $O(n^4)$，越界限制会剪去大量组合；存储矩阵 $O(n^2)$。',
        checker='maximum-square-corners')
    put(285821, 1200, ['枚举', '日期'], '统计闭日期区间中，八位数字回文且日历上合法的日期。',
        '回文日期的后四位由年份唯一确定。枚举起止年份，反转四位年份得到 MMDD，拼回八位日期，检查是否在区间内。再检查月份一到十二、日期不超过对应月份天数，二月按公历闰年规则确定。',
        r'''int a, b; cin >> a >> b; int answer = 0; for (int year = a / 10000; year <= b / 10000; year++) { int reversed = 0, x = year; for (int i = 0; i < 4; i++) { reversed = reversed * 10 + x % 10; x /= 10; }
            int date = year * 10000 + reversed, month = reversed / 100, day = reversed % 100; if (date < a || date > b || month < 1 || month > 12) continue;
            int days[] = {0,31,28,31,30,31,30,31,31,30,31,30,31}; if (year % 400 == 0 || (year % 4 == 0 && year % 100 != 0)) days[2]++;
            if (day >= 1 && day <= days[month]) answer++; } cout << answer;''',
        '数字回文不保证日期存在。反转必须处理恰好四位，产生的月日中允许有前导零。',
        complexity=r'设枚举年份数为 $Y$，时间 $O(Y)$，额外空间 $O(1)$。')
    put(282533, 1000, ['前缀和'], '静态数组上回答大量闭区间求和。',
        'prefix[i] 保存前 i 项之和，prefix[0]=0。每个查询 [l,r] 输出 prefix[r]-prefix[l-1]；减掉的恰是查询左端之前的部分。',
        r'''int n, q; cin >> n >> q; vector<long long> prefix(n + 1); for (int i = 1; i <= n; i++) { long long x; cin >> x; prefix[i] = prefix[i - 1] + x; }
        while (q--) { int l, r; cin >> l >> r; cout << prefix[r] - prefix[l - 1] << '\n'; }''',
        '一百万个绝对值十亿的数，其和可达 10^15，前缀数组必须为 long long。',
        complexity=r'时间 $O(n+q)$，空间 $O(n)$。')
    put(284579, 1200, ['差分', '前缀和'], '先进行所有区间加法，再一次性输出最终数组。',
        '令 d[i]=a[i]-a[i-1]，a[0]=0。给 [l,r] 加 x，只会使 d[l] 增加 x、d[r+1] 减少 x，区间内部相邻两项同时变化，差不变。所有操作记录完后，对 d 求前缀和即可还原结果。',
        r'''int n, q; cin >> n >> q; vector<long long> difference(n + 2); long long previous = 0;
        for (int i = 1; i <= n; i++) { long long x; cin >> x; difference[i] = x - previous; previous = x; }
        while (q--) { int l, r; long long x; cin >> l >> r >> x; difference[l] += x; difference[r + 1] -= x; }
        long long value = 0; for (int i = 1; i <= n; i++) { value += difference[i]; if (i > 1) cout << ' '; cout << value; }''',
        '右端的反向标记在 r+1，不在 r。r=n 时仍可写 n+1，所以数组多留两格。叠加结果需要 long long。',
        complexity=r'时间 $O(n+q)$，空间 $O(n)$。')
    if 'nowcoder-global::285823' not in existing:
        alias(285823, 'luogu-training-P1047', '已逐条核对 NOIP2005 简单版：零至 L 的整数点均有树，闭区间重复删除，L<=10000，输入输出一致。')
    put(285338, 1300, ['排序', '区间合并'], '在长度十亿的整数道路上删除多个闭区间中的树，求剩余棵数。',
        '道路共有 l+1 棵树，不能逐点建数组。把删除区间按左端点排序，维护当前合并段 [left,right]；新区间若与当前段重叠或相邻就扩展右端，否则结算 right-left+1 并开始下一段。最后扣除删除并集大小。相邻整数段可以合并，因为两段间没有遗漏整数点。',
        r'''long long length; int n; cin >> length >> n; vector<pair<long long,long long>> a(n); for (auto &[l, r] : a) cin >> l >> r; sort(a.begin(), a.end());
        long long left = a[0].first, right = a[0].second, removed = 0; for (int i = 1; i < n; i++) { if (a[i].first <= right + 1) right = max(right, a[i].second); else { removed += right - left + 1; left = a[i].first; right = a[i].second; } }
        removed += right - left + 1; cout << length + 1 - removed;''',
        '闭区间长度是 right-left+1，不是几何长度。道路的零号位置也有树。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(285825, 1700, ['前缀和', '计数'], '按样例与原 CQOI 题意，统计中位数为 b 的奇数长度连续子段。',
        '题面对子序列的注释与样例有歧义：样例统计的是连续子段，此处按样例及原题处理。排列中 b 只有一个，合法段必须包含它。把大于 b 的数看成 +1，小于 b 的数看成 -1，合法条件就变为两种数个数相同。以 b 为中心，枚举左边界，统计左侧符号和的频次（包含空左侧的零）；再从 b 向右累加，若右侧和为 s，就加入左侧和为 -s 的个数。符号和为零已保证除 b 外元素成对，长度自然为奇数。',
        r'''int n, b; cin >> n >> b; vector<int> a(n); int position = 0; for (int i = 0; i < n; i++) { cin >> a[i]; if (a[i] == b) position = i; }
        vector<long long> count(2 * n + 3); int offset = n + 1, balance = 0; count[offset] = 1;
        for (int i = position - 1; i >= 0; i--) { balance += a[i] > b ? 1 : -1; count[offset + balance]++; }
        long long answer = count[offset]; balance = 0; for (int i = position + 1; i < n; i++) { balance += a[i] > b ? 1 : -1; answer += count[offset - balance]; } cout << answer;''',
        '这里的处理对象是连续子段；若按任意删除得到的非连续子序列计数，第一个样例就不再是三。答案可为二次量级，要用 long long。',
        complexity=r'时间、空间均为 $O(n)$。',
        cases=[{'input': '1 1\n1', 'output': '1'}])
    put(285827, 1700, ['滑动窗口', '二维前缀和'], '用轴对齐、边长 r 的开正方形覆盖最多目标价值，同坐标价值累加。',
        '整数坐标的两个点若相差 r 就不能同时落在开区间内；一边能覆盖的恰是至多 r 个连续整数坐标。按 x 维护宽为 r 的竖条，把条内各点价值累计到 y 数组。竖条右移一格，移出一列并移入一列。每个竖条内，再用长度 r 的 y 滑动窗口求最大和。目标均非负，边缘不足 r 的窗口可向外延伸，不影响合法性。这样不必保存完整的五千平方前缀和表。',
        r'''int n, radius; cin >> n >> radius; const int limit = 5000; vector<vector<pair<int,int>>> columns(limit + 1); int maxX = 0, maxY = 0;
        for (int i = 0; i < n; i++) { int x, y, value; cin >> x >> y >> value; columns[x].push_back({y, value}); maxX = max(maxX, x); maxY = max(maxY, y); }
        vector<int> band(maxY + 1); auto change = [&](int x, int sign) { for (auto [y, value] : columns[x]) band[y] += sign * value; };
        for (int x = 0; x <= min(maxX, radius - 1); x++) change(x, 1); int answer = 0;
        for (int x = 0; x <= maxX; x++) { if (x > 0) { change(x - 1, -1); if (x + radius - 1 <= maxX) change(x + radius - 1, 1); }
            int sum = 0; for (int y = 0; y <= maxY; y++) { sum += band[y]; if (y >= radius) sum -= band[y - radius]; answer = max(answer, sum); } }
        cout << answer;''',
        '同位置可能有多目标，必须累加。窗口含 r 个整数位置，不含 r+1 个；可以把正方形边放在半整数上来避开边界。',
        complexity=r'坐标上限为 $M=5000$，时间 $O(M^2+n)$，空间 $O(M+n)$。',
        cases=[{'input': '2 1\n0 0 100\n1 0 100', 'output': '100'}, {'input': '2 2\n0 0 100\n1 1 100', 'output': '200'}])
    put(284613, 1500, ['贪心', '带权中位数'], '从有序位置中选一个集合点，使所有人的移动距离总和最小。',
        '取累计人数首次达到总人数一半的位置，即满足 2*prefix>=total 的第一个编号。它是带权中位数。把集合点从一个坐标向右移动一小步，左侧每人距离加一步，右侧每人距离减一步；左边人数少于一半时右移能降低总距离，达到一半后再右移已无益，所以该位置最优。人数恰好平分时可能有一段最优位置，取最左的一个即可。',
        r'''int n; cin >> n; vector<long long> positions(n), weight(n); for (auto &x : positions) cin >> x; long long total = 0; for (auto &x : weight) { cin >> x; total += x; }
        long long prefix = 0; for (int i = 0; i < n; i++) { prefix += weight[i]; if (prefix * 2 >= total) { cout << i + 1; break; } }''',
        '选的是人数加权后的中位数，不是位置数组的中间下标，也不是坐标加权平均。总人数可能超过 int。',
        complexity=r'时间 $O(n)$，保存输入空间 $O(n)$。',
        checker='weighted-median-index')


if __name__ == '__main__':
    run()
    print('Registered twelve reviewed modern simulations.')
