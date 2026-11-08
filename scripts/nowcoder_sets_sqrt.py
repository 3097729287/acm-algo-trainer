"""Reviewed deletion potential, nearest matching and unchanged difficulty mappings."""
from nowcoder_editorials import CONTENT, add, problem, read, review_rating, sha, statement


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    mosquitoes = r'''struct MosquitoTree {
        int n; vector<vector<int>> sizes; vector<int> maximum;
        explicit MosquitoTree(int count) : n(count), sizes(count + 1), maximum(4 * count + 4) {}
        void build(int p, int l, int r) { if (l == r) { sort(sizes[l].begin(), sizes[l].end()); maximum[p] = sizes[l].empty() ? 0 : sizes[l].back(); return; } int mid = (l + r) / 2; build(p * 2, l, mid); build(p * 2 + 1, mid + 1, r); maximum[p] = max(maximum[p * 2], maximum[p * 2 + 1]); }
        long long strike(int p, int l, int r, int ql, int qr, int threshold) {
            if (r < ql || qr < l || maximum[p] < threshold) return 0;
            if (l == r) { long long answer = 0; while (!sizes[l].empty() && sizes[l].back() >= threshold) { answer += sizes[l].back(); sizes[l].pop_back(); } maximum[p] = sizes[l].empty() ? 0 : sizes[l].back(); return answer; }
            int mid = (l + r) / 2; long long answer = strike(p * 2, l, mid, ql, qr, threshold) + strike(p * 2 + 1, mid + 1, r, ql, qr, threshold); maximum[p] = max(maximum[p * 2], maximum[p * 2 + 1]); return answer;
        }
    };'''
    put(226861, 2000, ['线段树', '势能分析'], '每次消灭位置区间内体形至少 p 的活蚊子，输出本次消灭的体形和。',
        '每个位置的蚊子按体形排序，活蚊子最大值在末尾。线段树维护区间最大活蚊子体形；若最大值小于阈值，整段不用访问。否则递归到有关叶子，从末尾连续删除不小于阈值的蚊子，累加体形，随后更新最大值。虽然一次可能删很多，但每只蚊子只能被删一次，所有深入删除的工作可以摊还到这只被删除的蚊子上；另加每次查询的边界访问即可。',
        r'''int n, m, k; cin >> n >> m >> k; MosquitoTree tree(n); for (int i = 0; i < m; i++) { int position, size; cin >> position >> size; tree.sizes[position].push_back(size); } tree.build(1, 1, n);
        while (k--) { int l, r, threshold; cin >> l >> r >> threshold; cout << tree.strike(1, 1, n, l, r, threshold) << '\n'; }''',
        '同一位置可能有多只，不能只存一只。拍死后永久删除，之后查询不能再次计入。体形总和使用 long long。',
        declarations=mosquitoes, complexity=r'排序总计 $O(m\log m)$，所有操作摊还 $O((m+k)\log n)$，空间 $O(n+m)$。')
    square_root = r'''struct RootTree {
        int n; vector<long long> sum, maximum;
        explicit RootTree(const vector<long long> &a) : n((int)a.size() - 1), sum(4 * n + 4), maximum(4 * n + 4) { build(1, 1, n, a); }
        void pull(int p) { sum[p] = sum[p * 2] + sum[p * 2 + 1]; maximum[p] = max(maximum[p * 2], maximum[p * 2 + 1]); }
        void build(int p, int l, int r, const vector<long long> &a) { if (l == r) { sum[p] = maximum[p] = a[l]; return; } int mid = (l + r) / 2; build(p * 2, l, mid, a); build(p * 2 + 1, mid + 1, r, a); pull(p); }
        void change(int p, int l, int r, int ql, int qr) { if (maximum[p] <= 1) return; if (l == r) { long long value = sqrtl(sum[p]); while ((value + 1) * (value + 1) <= sum[p]) value++; while (value * value > sum[p]) value--; sum[p] = maximum[p] = value; return; } int mid = (l + r) / 2; if (ql <= mid) change(p * 2, l, mid, ql, qr); if (qr > mid) change(p * 2 + 1, mid + 1, r, ql, qr); pull(p); }
        long long query(int p, int l, int r, int ql, int qr) { if (ql <= l && r <= qr) return sum[p]; int mid = (l + r) / 2; long long answer = 0; if (ql <= mid) answer += query(p * 2, l, mid, ql, qr); if (qr > mid) answer += query(p * 2 + 1, mid + 1, r, ql, qr); return answer; }
    };'''
    put(226595, 2100, ['线段树', '势能分析'], '区间内各正整数开平方向下取整，并查询区间和。',
        '线段树维护区间和与最大值。开方时，最大值不超过一的节点已经稳定，整段跳过；其他节点递归到叶子修改并回算。初值最大十亿，连续开方至多六次就变成一，因此每个叶子真正改变的次数有固定小上界。后面的开方查询只会走到边界及尚未稳定的位置。浮点开根后用整数平方校正，确保完全平方数边界准确。',
        r'''int n, m; cin >> n >> m; vector<long long> a(n + 1); for (int i = 1; i <= n; i++) cin >> a[i]; RootTree tree(a); while (m--) { int op, l, r; cin >> op >> l >> r; if (op == 1) tree.change(1, 1, n, l, r); else cout << tree.query(1, 1, n, l, r) << '\n'; }''',
        '区间和开方不等于逐个元素开方后的和。剪枝依据最大值，而不是区间和；这一版没有区间加法，稳定值不会重新变大。',
        declarations=square_root, complexity=r'初值上限 $A$，总时间 $O((m+n\log\log A)\log n)$，空间 $O(n)$。')
    put(20034, 1500, ['有序集合', '二分查找'], '宠物与领养人依次到来，异类按最近特点值匹配，同差优先较小值，累计不满意度。',
        '任意时刻等待者只会是一种类型。用 multiset 保存他们的特点值：新来者同类就加入；异类就找 lower_bound(x)，它是第一个不小于 x 的候选，再检查其前驱。最接近的值只可能是这两个，距离相同时取较小的前驱。配对后从集合中删掉被匹配的一项，累计距离并对一百万取模。',
        r'''int n; cin >> n; multiset<long long> waiting; int kind = -1; long long answer = 0;
        while (n--) { int type; long long x; cin >> type >> x; if (waiting.empty() || type == kind) { kind = type; waiting.insert(x); continue; }
            auto right = waiting.lower_bound(x), chosen = right; if (right == waiting.end()) chosen = prev(right); else if (right != waiting.begin()) { auto left = prev(right); if (x - *left <= *right - x) chosen = left; }
            answer = (answer + llabs(x - *chosen)) % 1000000; waiting.erase(chosen); } cout << answer;''',
        '同差时选较小特点值。集合为空时重新设置等待类型；没有配对的人或宠物不产生费用。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    pairs = {
        51117: ('luogu-training-P3369', '六种动态可重集合操作与样例完全一致；牛客把数值范围放宽至正负二十亿，沿用同题2400档。'),
        210158: ('luogu-training-P3380', '区间排名、第k小、单点修改、前驱、后继的接口与样例一致。洛谷当前已扩容，未把其新增数据范围冒充牛客范围；树套树组合沿用2400档。'),
        210157: ('luogu-training-P3391', '初始一到n、反复区间翻转、最终输出排列，牛客样例说明给n/m十万，与同题范围相同。'),
        20009: ('luogu-training-P4097', '同样十万次强制在线线段插入与竖线最高交点查询，横坐标39989、纵坐标十亿、同高最小编号和竖直段规则一致。'),
    }
    for number, (source_id, reason) in pairs.items():
        source = problem(source_id)
        review_rating(number, source['difficulty'], reason + ' 此数值是ToBe已有CF-EQ映射，非牛客官方评级。',
                      origin={'id': source_id, 'url': source['url'], 'difficultySource': source.get('difficultySource'),
                              'sourceStatementSha256': sha(statement(source_id)['markdown'])})
    review_rating(226598, 2400, '区间开方、正数加法、区间和，n/m各二十万；加法会重置稳定性，不能套仅max<=1剪枝。需用区间min/max的开方结果是否相同或变化量是否相同来批量修改，并证明有重置操作的势能摊还界。', knowledge=['线段树', '势能分析', '懒标记'])
    review_rating(227884, 2400, '五万结点、十万树上颜色种类查询；需双欧拉序路径转区间、LCA额外结点处理、结点开关计数和莫队排序，组合难度按2400估算。', knowledge=['树上莫队', '最近公共祖先'])


if __name__ == '__main__':
    run()
    print('Registered three articles and six full above-cutoff reviews.')
