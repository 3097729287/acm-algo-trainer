"""Reviewed static pair probability and small bounded dynamic-color queries."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing = read(CONTENT / 'reviewed.json')
    if 'nowcoder-global::51115' not in existing:
        add(51115, 2100, ['莫队算法', '计数', '概率'], '每次从指定区间随机抽两只袜子，输出颜色相同的概率的最简分数。',
            '设窗口内每色数量为 count[c]，同色无序对数 pairs=ΣC(count[c],2)，总无序对数为 C(len,2)。加入一只颜色 c 时，它与原有 count[c] 只各形成一对，所以先加 count[c] 再把计数加一；删除时先减计数，再减去剩下的 count[c]。这使窗口左右端移动一步只需常数时间。\n\n把询问按左端所在块、再按右端排序，用莫队维护当前窗口；相邻块采用相反右端方向以减少来回移动。答案为 pairs/C(len,2)，用最大公约数约分，零概率单独写成 0/1。',
            r'''int n, m; cin >> n >> m; vector<int> color(n + 1); for (int i = 1; i <= n; i++) cin >> color[i]; int block = max(1, (int)sqrt(n)); struct Query { int l, r, id; }; vector<Query> queries(m); for (int i = 0; i < m; i++) { cin >> queries[i].l >> queries[i].r; queries[i].id = i; }
            sort(queries.begin(), queries.end(), [&](auto a, auto b) { int x = a.l / block, y = b.l / block; if (x != y) return x < y; return x % 2 ? a.r > b.r : a.r < b.r; }); vector<long long> count(n + 1); vector<pair<long long,long long>> answer(m); long long pairs = 0; int left = 1, right = 0;
            auto add = [&](int p) { pairs += count[color[p]]++; }; auto remove = [&](int p) { pairs -= --count[color[p]]; };
            for (auto q : queries) { while (left > q.l) add(--left); while (right < q.r) add(++right); while (left < q.l) remove(left++); while (right > q.r) remove(right--); long long length = q.r - q.l + 1, total = length * (length - 1) / 2;
                if (pairs == 0 || total == 0) answer[q.id] = {0,1}; else { long long divisor = gcd(pairs, total); answer[q.id] = {pairs / divisor, total / divisor}; } }
            for (auto [a, b] : answer) cout << a << '/' << b << '\n';''',
            '加入与删除时修改计数的先后不同，写反会漏或多算一组。分子、分母都要 long long；输出按原查询顺序恢复。',
            complexity=r'时间 $O((n+m)\sqrt n+m\log m)$，空间 $O(n+m)$。')
    if 'nowcoder-global::202003' not in existing:
        add(202003, 2200, ['分块', '位集', '离散化'], '支持单点改色和区间不同颜色计数，按本题 n、m 各一万及至多一千次修改范围处理。',
            '先读入全部操作，将初始颜色与修改中会出现的颜色统一离散化；最多一万一千种颜色。把位置按约一百个一块划分，每块维护每种颜色出现次数，以及哪些颜色存在的压位集合。修改时只更新一个块的两种计数与对应位。\n\n查询时，零散边缘逐个把颜色位设为一，完整块则把该块位集按机器字或进临时集合，最后统计一的数量。位集做的是集合并，不会重复计颜色；块内频数则保证删掉一个位置后，只有同色真的消失才清位。这里能预读操作且范围较小，压位分块足够，不需要假定输入是强制在线。',
            r'''int n, m; cin >> n >> m; vector<int> a(n), keys; for (int &x : a) { cin >> x; keys.push_back(x); } struct Operation { char type; int x, y; }; vector<Operation> operations(m);
            for (auto &op : operations) { cin >> op.type >> op.x >> op.y; if (op.type == 'R') keys.push_back(op.y); } sort(keys.begin(), keys.end()); keys.erase(unique(keys.begin(), keys.end()), keys.end());
            auto compressed = [&](int x) { return (int)(lower_bound(keys.begin(), keys.end(), x) - keys.begin()); }; for (int &x : a) x = compressed(x); for (auto &op : operations) if (op.type == 'R') op.y = compressed(op.y);
            int block = max(1, (int)sqrt(n)), blocks = (n + block - 1) / block, values = keys.size(), words = (values + 63) / 64; vector<vector<int>> count(blocks, vector<int>(values)); vector<vector<unsigned long long>> present(blocks, vector<unsigned long long>(words));
            for (int i = 0; i < n; i++) { count[i / block][a[i]]++; present[i / block][a[i] / 64] |= 1ULL << (a[i] % 64); }
            for (auto op : operations) { if (op.type == 'R') { int p = op.x - 1, group = p / block, old = a[p]; if (--count[group][old] == 0) present[group][old / 64] &= ~(1ULL << (old % 64)); if (++count[group][op.y] == 1) present[group][op.y / 64] |= 1ULL << (op.y % 64); a[p] = op.y; }
                else { int l = op.x - 1, r = op.y - 1; vector<unsigned long long> colors(words); auto include = [&](int p) { colors[a[p] / 64] |= 1ULL << (a[p] % 64); };
                    while (l <= r && l % block) include(l++); while (l + block - 1 <= r) { for (int w = 0; w < words; w++) colors[w] |= present[l / block][w]; l += block; } while (l <= r) include(l++);
                    int answer = 0; for (auto word : colors) answer += __builtin_popcountll(word); cout << answer << '\n'; } }''',
            '离散化时要包含未来修改的新颜色。修改成原颜色也合法，计数先减后加可正确还原。每条查询都重新清空临时集合。',
            complexity=r'设颜色种数为 $V$、块长 $B\approx\sqrt n$，修改 $O(1)$；查询 $O(B+(n/B)\lceil V/64\rceil)$，空间 $O((n/B)V+n+m)$。预处理离散化另需 $O((n+m)\log(n+m))$。')


if __name__ == '__main__':
    run()
    print('Registered socks probability and bounded dynamic-color queries.')
