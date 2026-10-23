const head = '#include <bits/stdc++.h>\nusing namespace std;\n';
export const SEQUENCE_CODE = {
  prefix: { title: '静态区间和', input: '输入 n q、n 个整数，再输入 q 行 l r；1≤l≤r≤n。n,q≤200000，|a[i]|≤10⁹。', complexity: '建表 O(n)，每问 O(1)，总计 O(n+q)，额外空间 O(n)。数组改动后必须更新这份快照。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, q; cin >> n >> q;
    vector<long long> p(n + 1, 0); // p[0]：前 0 个数的和
    for (int i = 1; i <= n; ++i) {
        long long x; cin >> x;
        p[i] = p[i - 1] + x;
    }
    while (q--) {
        int l, r; cin >> l >> r;
        cout << p[r] - p[l - 1] << '\\n';
    }
}` },
  difference: { title: '批量区间加，最后取值', input: '输入 n m、原数组，再输入 m 行 l r k，表示闭区间 [l,r] 加 k。n,m≤200000，|a[i]|,|k|≤10⁹。输出最终数组。', complexity: '每次只写两个事件 O(1)，最后扫描 O(n)，总计 O(n+m)，空间 O(n)。这里 delta 只记增量，初始全 0。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, m; cin >> n >> m;
    vector<long long> a(n + 1), delta(n + 2, 0);
    for (int i = 1; i <= n; ++i) cin >> a[i];
    while (m--) {
        int l, r; long long k; cin >> l >> r >> k;
        delta[l] += k;
        delta[r + 1] -= k; // 从下一格起取消
    }
    long long add = 0;
    for (int i = 1; i <= n; ++i) {
        add += delta[i];
        cout << a[i] + add << (i == n ? '\\n' : ' ');
    }
}` },
  plane: { title: '二维静态矩形和', input: '输入 h w q、h 行各 w 个整数，再输入 q 行 x1 y1 x2 y2。坐标从 1 开始，给左上与右下角。h,w≤1000，|a[i][j]|≤10⁶。', complexity: '预处理 O(hw)，每次 O(1)，空间 O(hw)。第 0 行和第 0 列全 0，表示空矩形。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int h, w, q; cin >> h >> w >> q;
    vector<vector<long long>> p(h + 1, vector<long long>(w + 1));
    for (int i = 1; i <= h; ++i)
        for (int j = 1; j <= w; ++j) {
            long long a; cin >> a;
            p[i][j] = a + p[i-1][j] + p[i][j-1] - p[i-1][j-1];
        }
    while (q--) {
        int x1, y1, x2, y2; cin >> x1 >> y1 >> x2 >> y2;
        cout << p[x2][y2] - p[x1-1][y2] - p[x2][y1-1]
             + p[x1-1][y1-1] << '\\n';
    }
}` },
  pair: { title: '有序数组中寻找一对', input: '输入 n target 和非递减排列的 n 个整数，判断是否存在两个不同位置之和为 target。n≤200000，数值与 target 的绝对值≤10⁹。', complexity: '输入已有序时 O(n)，额外空间 O(1)（不计输入数组）。若先排序，总时间 O(n log n)；需要原下标时连同原下标排序。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; long long target; cin >> n >> target;
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    int l = 0, r = n - 1;
    while (l < r) { // 两个位置必须不同
        long long sum = a[l] + a[r];
        if (sum == target) { cout << "YES\\n"; return 0; }
        if (sum < target) ++l; // a[l] 配上最大的都不够
        else --r;             // a[r] 配上最小的都超了
    }
    cout << "NO\\n";
}` },
  window: { title: '非负数组：和至少 S 的最短非空段', input: '输入 n S 与 n 个非负整数；S≥1，n≤200000，a[i],S≤10⁹。无解输出 0。课堂先用正数说明严格变化，0 也允许，因为和仍不反向变化。', complexity: '左右端点各至多前进 n 次，总时间 O(n)，额外空间 O(1)（不计输入数组）。每个新右端点都要尽量收缩，故使用 while。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; long long S; cin >> n >> S;
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    int l = 0, answer = n + 1; long long sum = 0;
    for (int r = 0; r < n; ++r) {
        sum += a[r];
        while (sum >= S) {
            answer = min(answer, r - l + 1); // 先记合法窗口
            sum -= a[l++];                 // 再尝试更短的
        }
    }
    cout << (answer == n + 1 ? 0 : answer) << '\\n';
}` },
  unique: { title: '最长无重复字符段', input: '输入一个不含空白的 ASCII 字符串 s，长度 1～200000。输出最长连续无重复段的长度。', complexity: '每个字符各进出一次，O(n) 时间，256 个计数 O(1) 空间；这里按 ASCII 字节计数，不直接处理 Unicode 字符。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    string s; cin >> s;
    int count[256] = {}, l = 0, answer = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        unsigned char c = s[r]; ++count[c];
        while (count[c] > 1) {
            --count[(unsigned char)s[l]]; ++l;
        }
        answer = max(answer, r - l + 1);
    }
    cout << answer << '\\n';
}` },
  compact: { title: '原地保留所有非零数', input: '输入 n 和 n 个整数，输出保留非零数后的长度及内容，保持原相对顺序。n≤200000。', complexity: 'read 扫描一次，write 至多前进 n 次，O(n) 时间、O(1) 额外空间。尾部旧值不属于结果，不必逐个清零。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; cin >> n; vector<int> a(n);
    for (auto &x : a) cin >> x;
    int write = 0;
    for (int read = 0; read < n; ++read)
        if (a[read] != 0) a[write++] = a[read];
    cout << write << '\\n';
    for (int i = 0; i < write; ++i)
        cout << a[i] << (i + 1 == write ? '\\n' : ' ');
}` },
  exact: { title: '含负数：和恰好 K 的段数', input: '输入 n K 与 n 个整数，可含负数和 0。n≤200000，|a[i]|,|K|≤10⁹。输出非空连续段的数量。', complexity: 'unordered_map 的查找/插入平均 O(1)，总计期望 O(n)，空间 O(n)；哈希最坏可退化。需要最坏界时改用 map，时间 O(n log n)。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n; long long K; cin >> n >> K;
    unordered_map<long long, long long> freq;
    freq[0] = 1; // 空前缀：允许从第一个数开始的段
    long long p = 0, answer = 0;
    for (int i = 0; i < n; ++i) {
        long long x; cin >> x; p += x;
        auto it = freq.find(p - K);
        if (it != freq.end()) answer += it->second;
        ++freq[p]; // 先查再存，保证只配对更早的前缀
    }
    cout << answer << '\\n';
}` },
};

export const SEQUENCE_COURSES = {
  'prefix-difference': { title: '前缀和与差分', subtitle: '把一整段工作，搬到两个边界。', chapters: [
    ['sum', '少算一整段'], ['inverse', '累计与变化，互相还原'], ['events', '只在边界下指令'], ['plane', '矩形里的加减法'], ['choose', '各自何时上场'], ['code', '从推导到 C++'], ['debug', '让反例检查理解'],
  ], codes: ['prefix', 'difference', 'plane', 'exact'] },
  'two-pointers': { title: '双指针算法', subtitle: '移动一步之前，先证明不会错过答案。', chapters: [
    ['pair', '一次排除一整片'], ['window', '让窗口伸缩'], ['unique', '窗口里还可以放什么'], ['compact', '一个读，一个写'], ['negative', '负数推翻了哪句话'], ['code', '为什么不回头就够了'], ['transfer', '先判断，再选工具'],
  ], codes: ['pair', 'window', 'unique', 'compact'] },
};
