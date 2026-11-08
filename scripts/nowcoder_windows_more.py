"""Final reviewed problems in simulation/greedy contest 20960."""
from nowcoder_editorials import CONTENT, add, read, register, reviewed_clone


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(15553, 1500, ['前缀和', '线性 DP'], '选两个长度都为 k、互不重叠的连续区间，使得分总和最大。',
        '用前缀和求任意长度 k 的窗口和，best[i] 保存完全位于前 i 项的这类窗口的最大和。枚举第二段左端点 r，第一段必须完全位于前 r-1 项，候选就是 best[r-1]+第二段的和。二者覆盖所有合法选择，取最大即可。',
        r'''int tests; cin >> tests; while (tests--) { int n, k; cin >> n >> k; vector<long long> prefix(n + 1), best(n + 1, LLONG_MIN / 4);
            for (int i = 1; i <= n; i++) { long long x; cin >> x; prefix[i] = prefix[i - 1] + x; }
            for (int i = k; i <= n; i++) best[i] = max(best[i - 1], prefix[i] - prefix[i - k]);
            long long answer = LLONG_MIN; for (int right = k + 1; right + k - 1 <= n; right++) answer = max(answer, best[right - 1] + prefix[right + k - 1] - prefix[right - 1]); cout << answer << '\n'; }''',
        '分数可以全负，最大值不能初始化为零。两段允许紧挨着，只需不重叠；R=L+k 合法。',
        complexity=r'每组时间、空间均为 $O(n)$。', cases=[{'input': '1\n4 1\n-4 -2 -3 -1', 'output': '-3'}])
    put(14247, 1700, ['前缀异或', '枚举', '计数'], '统计互不重叠的两个非空区间，使两段所有数合起来的异或为零。',
        '两段合并异或为零，等价于各自的异或相等。枚举右侧区间的左端点 l，频次数组保存所有结束位置小于 l 的区间异或值。先把刚结束在 l-1 的所有区间加入频次，再枚举从 l 开始的右段，求其异或 v 并加上 freq[v]。每对不重叠区间都有唯一左右顺序，也只会在这个 l 被计数。',
        r'''int n; cin >> n; vector<int> a(n); for (int &x : a) cin >> x; vector<long long> frequency(1 << 17); long long answer = 0;
        for (int left = 0; left < n; left++) { int value = 0; for (int i = left - 1; i >= 0; i--) { value ^= a[i]; frequency[value]++; }
            value = 0; for (int right = left; right < n; right++) { value ^= a[right]; answer += frequency[value]; } } cout << answer;''',
        '不是要求两段各自异或都为零，而是两段异或相等。元素小于 100000，所有异或小于 2^17；答案需要 long long。',
        complexity=r'时间 $O(n^2+2^{17})$，空间 $O(n+2^{17})$。',
        cases=[{'input': '2\n1 1', 'output': '1'}, {'input': '1\n0', 'output': '0'}])
    put(202492, 1600, ['带权中位数', '数学'], '在需求矩阵中选仓库，使需求次数乘曼哈顿距离的总和最小。',
        '横纵距离可分开：将每行需求加总，得到选仓库行号的一维带权绝对距离问题；每列同理。每一维都取累计权重首次达到总权重一半的位置，即带权中位数，然后求所有权重乘与该位置的距离。两个一维最小费用相加就是答案，仓库可位于有需求的格子。',
        r'''int tests; cin >> tests; while (tests--) { int n, m; cin >> n >> m; vector<long long> rows(m), columns(n); for (int r = 0; r < m; r++) for (int c = 0; c < n; c++) { long long x; cin >> x; rows[r] += x; columns[c] += x; }
            auto cost = [](const vector<long long> &weights) { long long total = accumulate(weights.begin(), weights.end(), 0LL), prefix = 0, answer = 0; int median = 0;
                for (int i = 0; i < (int)weights.size(); i++) { prefix += weights[i]; if (prefix * 2 >= total) { median = i; break; } }
                for (int i = 0; i < (int)weights.size(); i++) answer += weights[i] * abs(i - median); return answer; };
            cout << cost(rows) + cost(columns) << '\n'; }''',
        '输入先给宽 n、高 m，之后是 m 行 n 列。每次需求只按题意计算运输距离，不额外乘二；样例首组答案二可核对这一点。',
        complexity=r'时间 $O(nm+n+m)$，额外空间 $O(n+m)$。')
    put(53676, 1300, ['二维前缀和', '枚举'], '统计地图中含至少一座建筑的 k 乘 k 正方形窗口数。',
        '二维前缀和 prefix[r][c] 保存左上矩形建筑数量。枚举所有能完整放入地图的 k 乘 k 窗口，用四项容斥得到窗口总和；大于零就让答案加一。即使窗口内有多个建筑也只算一种施法位置。',
        r'''int n, m, k; cin >> n >> m >> k; vector<vector<int>> prefix(n + 1, vector<int>(m + 1));
        for (int r = 1; r <= n; r++) for (int c = 1; c <= m; c++) { char x; cin >> x; prefix[r][c] = prefix[r - 1][c] + prefix[r][c - 1] - prefix[r - 1][c - 1] + (x == '1'); }
        int answer = 0; for (int r = k; r <= n; r++) for (int c = k; c <= m; c++) if (prefix[r][c] - prefix[r - k][c] - prefix[r][c - k] + prefix[r - k][c - k] > 0) answer++; cout << answer;''',
        '矩阵样例是不带空格的字符串，逐字符读入也能兼容有空格的写法。窗口不能越出地图。',
        complexity=r'时间、空间均为 $O(nm)$。')
    if 'nowcoder-global::18386' not in existing:
        reviewed_clone(18386, 285843, '已核对长度上限一百万、二十六字母与最短连续子串相同；此版本额外保证存在答案，所以原程序的无解分支不会触发。')
    put(224938, 1800, ['排序', '滑动窗口', '带权中位数'], '至多 k 次把单个元素加一或减一，最大化某个值的出现次数。',
        '排序后，最优选出的若干数可取为一段连续元素：固定目标值时，优先选择距离它最近的数，不会跳过中间更近的数。把区间 [l,r] 全改成同一个数，最省操作的目标是其中位数 a[mid]。用前缀和 O(1) 算出左半部分增加的代价与右半部分减少的代价。右端递增时，若代价超过 k 就右移左端；删除元素不会增加最小代价，所以双指针能找到最长可行段。',
        r'''int n; long long k; cin >> n >> k; vector<long long> a(n), prefix(n + 1); for (auto &x : a) cin >> x; sort(a.begin(), a.end()); for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + a[i];
        auto cost = [&](int l, int r) { int mid = (l + r) / 2; return a[mid] * (mid - l + 1) - (prefix[mid + 1] - prefix[l]) + (prefix[r + 1] - prefix[mid + 1]) - a[mid] * (r - mid); };
        int left = 0, answer = 0; for (int right = 0; right < n; right++) { while (cost(left, right) > k) left++; answer = max(answer, right - left + 1); } cout << answer;''',
        '允许同时增加、减少，目标应取中位数；一律改成最大值并不最省。前缀和与操作预算都需要 long long。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。',
        cases=[{'input': '3 2\n1 2 3', 'output': '3'}])
    if 'nowcoder-global::204370' not in existing:
        text = '''## 牛牛的木板

### 思路

把连续一段洗成全白，恰好要清洗其中所有的零，因此问题就是找至多含 m 个零的最长区间。右端每加入一个元素就更新零数；超过 m 时不断移出左端，直到合法。这样得到的是以当前右端结束的最长合法段，取所有长度的最大值。

### 参考代码

本题为函数题，保留原站的 `Solution::solve` 接口，直接返回答案。

```cpp
#include <bits/stdc++.h>
using namespace std;
class Solution {
public:
    int solve(int n, int m, vector<int>& a) {
        int left = 0, zeros = 0, answer = 0;
        for (int right = 0; right < n; right++) {
            zeros += a[right] == 0;
            while (zeros > m) { zeros -= a[left] == 0; left++; }
            answer = max(answer, right - left + 1);
        }
        return answer;
    }
};
```

### 复杂度与易错点

左右指针都至多移动 n 次，时间 $O(n)$，额外空间 $O(1)$。一表示白色，零才需要清洗；不要求必须用完清洗剂。
'''
        driver = r'''int main() { string input((istreambuf_iterator<char>(cin)), istreambuf_iterator<char>()); for (char &c : input) if (!isdigit((unsigned char)c)) c = ' '; stringstream stream(input); int n, m; stream >> n >> m; vector<int> a(n); for (int &x : a) stream >> x; cout << Solution().solve(n, m, a); }'''
        register(204370, 1300, ['滑动窗口', '双指针'], '完整题面为至多m个零的最长连续窗口，n<=10^6；原站函数签名 solve(int,int,vector<int>&) 已核对。', {'default': text}, driver=driver)
    if 'nowcoder-global::23053' not in existing:
        reviewed_clone(23053, 285867, '完整核对为月月查手机原题，原串与查询总长均一百万；输出合同是 Yes/No 而非 YES/NO，已同步修改参考代码中的输出。',
                       replacements={'"YES\\n" : "NO\\n"': '"Yes\\n" : "No\\n"'})
    put(221825, 1400, ['枚举', '字符串'], '两次手表显示可能含问号，且同一天内第一次严格早于第二次，求间隔最小、最大值。',
        '一天只有一千四百四十分钟，按时间递增枚举。用格式 HH:MM 检查是否匹配两种显示。当前分钟若匹配第二次显示，就和之前最晚的合法第一次时间求最小差，和之前最早的合法第一次时间求最大差。处理完第二次匹配后，才把当前分钟作为第一次的候选加入，保证两次不能相等。',
        r'''string first, second; cin >> first >> second; auto match = [](const string &pattern, int minute) { string s = "00:00"; int h = minute / 60, m = minute % 60; s[0] += h / 10; s[1] += h % 10; s[3] += m / 10; s[4] += m % 10; for (int i = 0; i < 5; i++) if (pattern[i] != '?' && pattern[i] != s[i]) return false; return true; };
        int earliest = -1, latest = -1, minimum = INT_MAX, maximum = 0;
        for (int t = 0; t < 1440; t++) { if (match(second, t) && earliest != -1) { minimum = min(minimum, t - latest); maximum = max(maximum, t - earliest); }
            if (match(first, t)) { if (earliest == -1) earliest = t; latest = t; } } cout << minimum << ' ' << maximum;''',
        '不能允许跨午夜，也不能只单独取两次时间的最早、最晚值而忘记严格先后条件。',
        complexity=r'时间 $O(1440)$，额外空间 $O(1)$。',
        cases=[{'input': '??:??\n??:??', 'output': '1 1439'}])
    put(25025, 1700, ['贪心', '优先队列'], '每头牛可接受一个防晒 SPF 区间，每瓶可供若干头，最大化匹配数量。',
        '按 SPF 从小到大处理防晒霜；把最低要求不超过当前 SPF 的牛加入按最高可接受 SPF 排序的小根堆。丢掉最高要求已小于当前 SPF 的牛，因为后续更高 SPF 也无法救它们。当前每份防晒霜优先给最高要求最小、最着急的牛；若某方案给了更宽松的牛，交换两者不会影响当前合法性，且把更宽松的牛留给后面也不会更差。',
        r'''int n, m; cin >> n >> m; vector<pair<int,int>> cows(n), lotions(m); for (auto &[low, high] : cows) cin >> low >> high; for (auto &[spf, count] : lotions) cin >> spf >> count; sort(cows.begin(), cows.end()); sort(lotions.begin(), lotions.end());
        priority_queue<int, vector<int>, greater<int>> waiting; int next = 0, answer = 0; for (auto [spf, count] : lotions) { while (next < n && cows[next].first <= spf) waiting.push(cows[next++].second); while (!waiting.empty() && waiting.top() < spf) waiting.pop();
            while (count > 0 && !waiting.empty()) { waiting.pop(); count--; answer++; } } cout << answer;''',
        '可接受区间两端都包含。每头牛只能领一份；一瓶容量大时也只循环实际分配成功的次数。',
        complexity=r'时间 $O((n+m)\log(n+m))$，空间 $O(n+m)$。')
    put(23036, 1500, ['贪心', '区间覆盖'], '选最少闭整数区间，使并集覆盖一到 N 的所有整数点。',
        '维护下一处未覆盖整数 need，初始为一。把左端点不超过 need 的所有片段读入，选择其中右端点最远的一段；若最远仍小于 need，说明无法覆盖。否则使用一次片段并令 need=最远右端+1。任何可行方案都必须用一段覆盖 need，选更远的段只会留下更短的待覆盖后缀，因此贪心成立。',
        r'''long long n; int m; cin >> n >> m; vector<pair<long long,long long>> segments(m); for (auto &[l, r] : segments) cin >> l >> r; sort(segments.begin(), segments.end());
        long long need = 1; int next = 0, answer = 0; while (need <= n) { long long farthest = need - 1; while (next < m && segments[next].first <= need) { farthest = max(farthest, segments[next].second); next++; }
            if (farthest < need) { cout << -1; return 0; } answer++; need = farthest + 1; } cout << answer;''',
        '只关注整数，所以 [1,2] 与 [3,4] 可以无缝覆盖一到四；下一目标是 r+1，而不是 r。',
        complexity=r'时间 $O(m\log m)$，空间 $O(m)$。')
    put(200183, 1300, ['贪心', '字符串'], '把整个零一串切为最多段，每段都至少有一个零和一个一。',
        '从左到右累积当前段出现过的数字，一旦零和一都出现，就立刻切一段并清空标记。任何合法第一段的终点都不会比这个最早位置更早，提前结束第一段会给后续留下更多字符，因此不会减少后面可切段数。末尾若只剩一种数字，把它并入上一段，不改变段数。',
        r'''string s; cin >> s; int mask = 0, answer = 0; for (char c : s) { mask |= 1 << (c - '0'); if (mask == 3) { answer++; mask = 0; } } cout << answer;''',
        '必须覆盖全串，末尾剩余字符要并入已有最后一段。题目保证全串同时含零和一，所以至少可形成一段。',
        complexity=r'时间 $O(|s|)$，额外空间 $O(1)$。')
    put(25136, 1500, ['贪心', '区间选点'], '用最少竖直切线，使每个横向长条的内部都被切到。',
        '把开始位置 x 与长度 len 转成开区间 (x,x+len)。按右端点升序排序；若当前长条尚未被前一刀覆盖，就在它右端点左侧紧挨着的位置切一刀。这个位置在当前条内部，又尽量靠右，能覆盖最多后续长条。只需保存该刀右侧的整数边界 end；后续长条左端严格小于 end 才能被这刀切到，等于 end 则必须再切。',
        r'''int n; cin >> n; vector<pair<long long,long long>> intervals(n); for (auto &[right, left] : intervals) { long long length; cin >> left >> length; right = left + length; } sort(intervals.begin(), intervals.end());
        long long boundary = LLONG_MIN; int answer = 0; for (auto [right, left] : intervals) if (left >= boundary) { answer++; boundary = right; } cout << answer;''',
        '第二个输入数是长度，不是右端点。切在端点不能把条切开，所以共享端点的两条需要分别处理。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(53681, 1900, ['贪心', '排序'], '安排先损失 a、再回复 b 的障碍顺序，判断初始稳定性能否完成全部障碍。',
        '先处理 b>=a 的不亏障碍，按 a 升序；越容易的增益越应先拿，完成后不会降低后续可行性。再处理 b<a 的亏损障碍，按 b 降序。对两个亏损障碍 A、B，若 bA>=bB，先 A 再 B 所需初始量 max(aA,aA-bA+aB)，不超过反序所需的 max(aB,aB-bB+aA)，因此该顺序安全。按排序模拟，每次先检查当前量至少为 a，再加 b-a。',
        r'''int tests; cin >> tests; while (tests--) { int n; long long stability; cin >> n >> stability; vector<pair<long long,long long>> a(n); for (auto &[loss, gain] : a) cin >> loss >> gain;
            sort(a.begin(), a.end(), [](const auto &x, const auto &y) { bool gx = x.second >= x.first, gy = y.second >= y.first; if (gx != gy) return gx > gy; return gx ? x.first < y.first : x.second > y.second; });
            bool possible = true; for (auto [loss, gain] : a) { if (stability < loss) { possible = false; break; } stability += gain - loss; } cout << (possible ? "Yes\n" : "No\n"); }''',
        '必须先承担损失才收到回复；即使 a=b，也不能在当前稳定性小于 a 时通过。零稳定性允许存在，负数才散架。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
    print('Registered fourteen reviewed window and interval articles.')
