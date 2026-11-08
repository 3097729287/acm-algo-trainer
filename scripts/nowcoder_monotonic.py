"""Reviewed strict/non-strict ownership and weighted histogram boundaries."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    if 'nowcoder-global::24840' not in existing:
        reviewed_clone(24840, 18356, '已核对完整英文Look Up题意、十万长度与百万高度：目标是右侧首个严格更高的下标，不存在输出零；原六项样例完全一致。')
    put(50965, 1600, ['单调栈', '柱状图最大矩形'], '多个单位宽柱状图中求最大矩形面积，读到 n=0 结束。',
        '栈保存高度不下降的柱下标。读到更矮柱 i 时，栈顶柱 j 的向右扩展第一次被挡住，弹栈后新的栈顶 left 是左侧边界，矩形可占 left+1 到 i-1，面积 h[j]*(i-left-1)。相等高度可暂时都留在栈中，最终最左的同高柱会覆盖完整跨度。末尾补一根零高柱，结算全部正高度。',
        r'''int n; while (cin >> n && n) { vector<long long> height(n + 2); for (int i = 1; i <= n; i++) cin >> height[i]; vector<int> stack; long long answer = 0;
            for (int i = 1; i <= n + 1; i++) { while (!stack.empty() && height[stack.back()] > height[i]) { int j = stack.back(); stack.pop_back(); int left = stack.empty() ? 0 : stack.back(); answer = max(answer, height[j] * (i - left - 1)); } stack.push_back(i); } cout << answer << '\n'; }''',
        '最高柱不一定给出最大面积。面积可达 10^14，使用 long long；结束标记零不是一个需输出答案的测试。',
        complexity=r'每组时间、空间均为 $O(n)$。')
    contribution = r'''long long contribution(const vector<long long> &a, bool maximum) {
        int n = a.size(); vector<int> stack; long long answer = 0;
        for (int i = 0; i <= n; i++) { while (!stack.empty() && (i == n || (maximum ? a[stack.back()] <= a[i] : a[stack.back()] >= a[i]))) {
                int j = stack.back(); stack.pop_back(); int left = stack.empty() ? -1 : stack.back(); answer += a[j] * (j - left) * (i - j);
            } if (i < n) stack.push_back(i); } return answer;
    }'''
    put(20806, 1800, ['单调栈', '贡献法', '区间最值'], '累计所有长度至少二的区间中，最大值减最小值的总和。',
        '区间价值就是 max-min，可分别累计所有区间最大值、最小值，再相减。计算最大值贡献时，让每个区间归属于其中最右边的最大元素 j。设左侧首个严格更大位置为 L，右侧首个大于等于的位置为 R，则左端有 j-L 种选法、右端有 R-j 种，贡献 a[j]*(j-L)*(R-j)。用递减栈，遇到大于等于栈顶的当前值就弹出并结算，恰好得到这两个边界。最小值将比较反过来。单元素区间的最大最小相同，会自行抵消，可以一起统计。',
        r'''int tests; cin >> tests; while (tests--) { int n; cin >> n; vector<long long> a(n); for (auto &x : a) cin >> x; cout << contribution(a, true) - contribution(a, false) << '\n'; }''',
        '左右不能都用严格比较，否则重复最值会被重复归属或遗漏。当前实现统一归给最右边的相同最值；计数乘积与总和使用 long long。',
        declarations=contribution, complexity=r'每组时间、空间均为 $O(n)$。',
        cases=[{'input': '1\n4\n2 2 2 2', 'output': '0'}])
    put(23619, 1800, ['单调栈', '前缀和', '柱状图最大矩形'], '每根柱宽不同，求下端对齐柱状图内最大矩形面积。',
        '仍用高度不下降的单调栈，遇到更矮的第 i 柱时弹出 j。此时以 h[j] 为高度，范围为弹栈后栈顶 left 之后，到 i-1 为止。这里宽度不能用柱数，而应使用宽度前缀和 width[i-1]-width[left]。末尾补零高柱清栈，取所有结算面积最大值。',
        r'''int n; cin >> n; vector<long long> width(n + 2), height(n + 2); for (int i = 1; i <= n; i++) { long long x; cin >> x; width[i] = width[i - 1] + x; } for (int i = 1; i <= n; i++) cin >> height[i];
        vector<int> stack; long long answer = 0; for (int i = 1; i <= n + 1; i++) { while (!stack.empty() && height[stack.back()] > height[i]) { int j = stack.back(); stack.pop_back(); int left = stack.empty() ? 0 : stack.back(); answer = max(answer, height[j] * (width[i - 1] - width[left])); } stack.push_back(i); } cout << answer;''',
        '总宽可达一亿，高度可达十亿，面积可达 10^17，必须使用 long long。柱宽只影响区间长度，不改变按高度找边界的规则。',
        complexity=r'时间、空间均为 $O(n)$。',
        cases=[{'input': '2\n100 100\n1000000000 1000000000', 'output': '200000000000'}])
    put(25084, 1500, ['单调栈', '计数'], '每头牛向右看到第一头不矮于自己的牛之前，统计全部可见的更矮牛对数。',
        '从左到右扫描，栈中保存尚未被不矮者挡住的牛，身高严格递减。当前牛到来时，弹出所有身高小于等于它的栈顶，因为这些牛今后都被当前牛挡住。剩下的每头栈中牛都比当前牛高、且中间没有挡住它的牛，恰好都能看到当前牛，答案加栈大小，再将当前身高入栈。',
        r'''int n; cin >> n; vector<long long> stack; long long answer = 0; for (int i = 0; i < n; i++) { long long height; cin >> height; while (!stack.empty() && stack.back() <= height) stack.pop_back(); answer += stack.size(); stack.push_back(height); } cout << answer;''',
        '同高牛也会遮挡，且看不到对方头顶，弹栈应使用小于等于。总对数可能超过 int。',
        complexity=r'时间、空间均为 $O(n)$。',
        cases=[{'input': '3\n3\n3\n2', 'output': '1'}])
    put(24325, 1800, ['双指针', '单调队列'], '选最窄的水平花盆区间，使接到的雨滴最高与最低落地时间差至少 D。',
        '落地速度为一，时间差就是窗口内 y 的最大值减最小值。按 x 排序后，维护窗口的最大 y、最小 y 两条单调队列。每次扩张右端，只要高度差已至少 D，就记录 x[right]-x[left] 并移出左端，继续尝试更窄区间；不再满足时再扩张右端。两队列各自按下标移除过期项。',
        r'''int n, d; cin >> n >> d; vector<pair<int,int>> drops(n); for (auto &[x, y] : drops) cin >> x >> y; sort(drops.begin(), drops.end()); deque<int> maximum, minimum; int left = 0, answer = INT_MAX;
        for (int right = 0; right < n; right++) { while (!maximum.empty() && drops[maximum.back()].second <= drops[right].second) maximum.pop_back(); while (!minimum.empty() && drops[minimum.back()].second >= drops[right].second) minimum.pop_back(); maximum.push_back(right); minimum.push_back(right);
            while (!maximum.empty() && drops[maximum.front()].second - drops[minimum.front()].second >= d) { answer = min(answer, drops[right].first - drops[left].first); if (maximum.front() == left) maximum.pop_front(); if (minimum.front() == left) minimum.pop_front(); left++; } }
        cout << (answer == INT_MAX ? -1 : answer);''',
        '雨滴落在盆边也算命中，所以宽度就是端点坐标之差，不加一。同一 x 可有不同高度的雨滴，最小宽度可能为零。',
        complexity=r'排序 $O(n\log n)$，滑动窗口 $O(n)$，空间 $O(n)$。',
        cases=[{'input': '2 5\n3 1\n3 6', 'output': '0'}, {'input': '1 1\n0 0', 'output': '-1'}])


if __name__ == '__main__':
    run()
    print('Registered six reviewed monotonic-stack and queue articles.')
