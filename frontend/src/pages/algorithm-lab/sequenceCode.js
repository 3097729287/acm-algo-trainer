const head = '#include <bits/stdc++.h>\nusing namespace std;\n';
export const SEQUENCE_CODE = {
  prefix: { title: '静态区间和', input: '输入 n q、n 个整数，再输入 q 行 l r；1≤l≤r≤n。n,q≤200000，|a[i]|≤10⁹。', complexity: '建表 O(n)，每问 O(1)，总计 O(n+q)，额外空间 O(n)。数组改动后必须更新这份快照。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是元素数，q 是查询数；题目使用从 1 开始的闭区间。
    int n, q; cin >> n >> q;
    // p[i] 是前 i 个数的和，p[0]=0 为第一格查询保留边界。
    vector<long long> p(n + 1, 0); // p[0]：前 0 个数的和
    for (int i = 1; i <= n; ++i) {
        // x 是当前位置的原值；求和用 long long 防止累加溢出。
        long long x; cin >> x;
        // 以前 i-1 个数的和为基础，只补上新读入的一个数。
        p[i] = p[i - 1] + x;
    }
    while (q--) {
        // 本次查询包含 l 与 r；不修改原数组。
        int l, r; cin >> l >> r;
        // 前 r 个数去掉前 l-1 个数，恰好留下整个闭区间。
        cout << p[r] - p[l - 1] << '\\n';
    }
}` },
  difference: { title: '批量区间加，最后取值', input: '输入 n m、原数组，再输入 m 行 l r k，表示闭区间 [l,r] 加 k。n,m≤200000，|a[i]|,|k|≤10⁹。输出最终数组。', complexity: '每次只写两个事件 O(1)，最后扫描 O(n)，总计 O(n+m)，空间 O(n)。这里 delta 只记增量，初始全 0。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是原数组长度，m 是需要批量处理的区间加操作数。
    int n, m; cin >> n >> m;
    // a 保存原值；delta 仅记录增量的变化，额外一格容纳 r+1 事件。
    vector<long long> a(n + 1), delta(n + 2, 0);
    for (int i = 1; i <= n; ++i) cin >> a[i];
    while (m--) {
        // [l,r] 是闭区间，k 是每格要增加的值，允许负数。
        int l, r; long long k; cin >> l >> r >> k;
        // 从 l 起，让后面的累计增量多出 k。
        delta[l] += k;
        // 到 r 的下一格撤销这次增量，不能在 r 处提前撤销。
        delta[r + 1] -= k; // 从下一格起取消
    }
    // add 是当前位置受到的全部操作的净增量。
    long long add = 0;
    for (int i = 1; i <= n; ++i) {
        // 累积到 i 处为止的事件，还原这一格的增量。
        add += delta[i];
        // 原值与净增量相加，输出操作全部完成后的值。
        cout << a[i] + add << (i == n ? '\\n' : ' ');
    }
}` },
  plane: { title: '二维静态矩形和', input: '输入 h w q、h 行各 w 个整数，再输入 q 行 x1 y1 x2 y2。坐标从 1 开始，给左上与右下角。h,w≤1000，|a[i][j]|≤10⁶。', complexity: '预处理 O(hw)，每次 O(1)，空间 O(hw)。第 0 行和第 0 列全 0，表示空矩形。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // h/w 是行列数，q 是查询数；输入坐标从 1 开始。
    int h, w, q; cin >> h >> w >> q;
    // p[i][j] 是左上角到 (i,j) 的矩形和，第 0 行/列代表空矩形。
    vector<vector<long long>> p(h + 1, vector<long long>(w + 1));
    for (int i = 1; i <= h; ++i)
        for (int j = 1; j <= w; ++j) {
            long long a; cin >> a;
            // 上方与左方的矩形相加会重复左上重叠区，所以要减去一次。
            p[i][j] = a + p[i-1][j] + p[i][j-1] - p[i-1][j-1];
        }
    while (q--) {
        // (x1,y1) 是查询左上角，(x2,y2) 是右下角，四条边都包含。
        int x1, y1, x2, y2; cin >> x1 >> y1 >> x2 >> y2;
        // 先取右下大矩形，再减去查询区上方和左方。
        cout << p[x2][y2] - p[x1-1][y2] - p[x2][y1-1]
             // 左上交叠区被减了两次，现在补回一次。
             + p[x1-1][y1-1] << '\\n';
    }
}` },
  pair: { title: '有序数组中寻找一对', input: '输入 n target 和非递减排列的 n 个整数，判断是否存在两个不同位置之和为 target。n≤200000，数值与 target 的绝对值≤10⁹。', complexity: '输入已有序时 O(n)，额外空间 O(1)（不计输入数组）。若先排序，总时间 O(n log n)；需要原下标时连同原下标排序。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是数组长度，target 是目标和；必须先保证 a 非递减。
    int n; long long target; cin >> n >> target;
    // a 记录有序数列；长整型避免两个元素相加时溢出。
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    // 只保留尚未被排除的区间 [l,r]，两端各指向一个候选。
    int l = 0, r = n - 1;
    // 两个位置必须不同；每次移动都排除一个绝不可能参与答案的端点。
    while (l < r) { // 两个位置必须不同
        // 固定这两个候选，比较它们的和与目标。
        long long sum = a[l] + a[r];
        if (sum == target) { cout << "YES\\n"; return 0; }
        if (sum < target) ++l; // a[l] 配上最大的都不够
        else --r;             // a[r] 配上最小的都超了
    }
    cout << "NO\\n";
}` },
  window: { title: '非负数组：和至少 S 的最短非空段', input: '输入 n S 与 n 个非负整数；S≥1，n≤200000，a[i],S≤10⁹。无解输出 0。课堂先用正数说明严格变化，0 也允许，因为和仍不反向变化。', complexity: '左右端点各至多前进 n 次，总时间 O(n)，额外空间 O(1)（不计输入数组）。每个新右端点都要尽量收缩，故使用 while。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是长度，S>0 是目标下界；本方法要求所有 a[i]>=0。
    int n; long long S; cin >> n >> S;
    vector<long long> a(n);
    for (auto &x : a) cin >> x;
    // l 是窗口左端，answer=n+1 作为尚未找到合法段的标记，sum 为窗口和。
    int l = 0, answer = n + 1; long long sum = 0;
    for (int r = 0; r < n; ++r) {
        // 右端加入一个元素；非负性保证扩展不会让和变小。
        sum += a[r];
        // 同一右端点下不断尝试更短合法窗口；只缩一次可能漏掉答案。
        while (sum >= S) {
            // 先记录当前合法窗口，长度包含两端所以要加一。
            answer = min(answer, r - l + 1); // 先记合法窗口
            // 移除旧左端后再前移；即使移除 0，也会继续缩短长度。
            sum -= a[l++];                 // 再尝试更短的
        }
    }
    // 哨兵仍未变化说明无解，按题意输出 0。
    cout << (answer == n + 1 ? 0 : answer) << '\\n';
}` },
  unique: { title: '最长无重复字符段', input: '输入一个不含空白的 ASCII 字符串 s，长度 1～200000。输出最长连续无重复段的长度。', complexity: '每个字符各进出一次，O(n) 时间，256 个计数 O(1) 空间；这里按 ASCII 字节计数，不直接处理 Unicode 字符。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // s 是不含空白的 ASCII 字符串，下面按字节维护窗口。
    string s; cin >> s;
    // count[c] 是字符 c 在窗口中的次数；l 是左端，answer 是最大合法长度。
    int count[256] = {}, l = 0, answer = 0;
    for (int r = 0; r < (int)s.size(); ++r) {
        // 避免 char 为负导致数组下标错误；先把新右端字符计入窗口。
        unsigned char c = s[r]; ++count[c];
        // 旧窗口已无重复，因此只需检查本次新加入的字符。
        while (count[c] > 1) {
            // 逐个移走左端字符；移到旧 c 之后，新窗口才恢复合法。
            --count[(unsigned char)s[l]]; ++l;
        }
        // 此时窗口已合法，再更新最长长度。
        answer = max(answer, r - l + 1);
    }
    cout << answer << '\\n';
}` },
  compact: { title: '原地保留所有非零数', input: '输入 n 和 n 个整数，输出保留非零数后的长度及内容，保持原相对顺序。n≤200000。', complexity: 'read 扫描一次，write 至多前进 n 次，O(n) 时间、O(1) 额外空间。尾部旧值不属于结果，不必逐个清零。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是输入个数，a 是可原地修改的数组。
    int n; cin >> n; vector<int> a(n);
    for (auto &x : a) cin >> x;
    // [0,write) 永远是已经筛选出的全部非零数，且顺序不变。
    int write = 0;
    // read 扫描尚未处理的位置；始终 write<=read，不会盖掉未读数据。
    for (int read = 0; read < n; ++read)
        // 遇到需要保留的数才写入，并推进结果边界。
        if (a[read] != 0) a[write++] = a[read];
    // write 就是新长度；只输出这之前的内容，后面的旧值不属于结果。
    cout << write << '\\n';
    for (int i = 0; i < write; ++i)
        cout << a[i] << (i + 1 == write ? '\\n' : ' ');
}` },
  exact: { title: '含负数：和恰好 K 的段数', input: '输入 n K 与 n 个整数，可含负数和 0。n≤200000，|a[i]|,|K|≤10⁹。输出非空连续段的数量。', complexity: 'unordered_map 的查找/插入平均 O(1)，总计期望 O(n)，空间 O(n)；哈希最坏可退化。需要最坏界时改用 map，时间 O(n log n)。', code: head + `int main() {
    ios::sync_with_stdio(false); cin.tie(nullptr);
    // n 是元素数，K 是目标和；负数也允许，不能依赖窗口和的单调性。
    int n; long long K; cin >> n >> K;
    // freq[s] 记录此前前缀和等于 s 的次数；次数与答案都用 long long。
    unordered_map<long long, long long> freq;
    // 先放入空前缀，才能统计从第一个元素开始、和为 K 的区间。
    freq[0] = 1; // 空前缀：允许从第一个数开始的段
    // p 是当前前缀和，answer 累计所有非空合法区间。
    long long p = 0, answer = 0;
    for (int i = 0; i < n; ++i) {
        // 读入当前元素并扩展前缀和。
        long long x; cin >> x; p += x;
        // 若旧前缀为 p-K，两前缀相减就得到和为 K 的段。
        auto it = freq.find(p - K);
        // 每个出现过的匹配前缀都对应一个不同左端点。
        if (it != freq.end()) answer += it->second;
        // 查询后才登记本前缀，防止 K=0 时把空段也算进去。
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
