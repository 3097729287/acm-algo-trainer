"""Reviewed character-order constraints, XOR ties and changing prefix counts."""
from nowcoder_editorials import CONTENT, add, problem, read, review_rating, sha, statement
from nowcoder_kmp_support import PREFIX_FUNCTION


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(15049, 2100, ['字典树', '拓扑排序'], '可任意重排字母表，找出哪些输入字符串能够成为字典序最小者。',
        '将全部词放进 Trie。检查某个候选词时沿其路径走：若途中已遇到另一个词的终点，它是候选的真前缀，无论字母顺序如何都会更小，候选失败。否则在每个节点，候选走字符 c 的边，所有其他存在的字符边 d 都要求 c<d，给字母图连 c→d。所有比较都由首次分叉决定，所以这些约束既必要又充分。字母图无环就能拓扑排序成一个合法字母表；有环则顺序要求矛盾。按输入顺序输出无环且没有短前缀的词。',
        r'''int n; cin >> n; vector<string> words(n); size_t total = 1; for (auto &s : words) { cin >> s; total += s.size(); } vector<array<int,26>> trie(1); vector<bool> terminal(1,false); trie.reserve(total); terminal.reserve(total);
        for (const auto &s : words) { int node = 0; for (char c : s) { int letter = c - 'a'; if (!trie[node][letter]) { trie[node][letter] = trie.size(); trie.push_back({}); terminal.push_back(false); } node = trie[node][letter]; } terminal[node] = true; }
        vector<int> answer; for (int id = 0; id < n; id++) { unsigned int edges[26] = {}; int node = 0; bool valid = true;
            for (char raw : words[id]) { if (terminal[node]) { valid = false; break; } int c = raw - 'a'; for (int d = 0; d < 26; d++) if (d != c && trie[node][d]) edges[c] |= 1U << d; node = trie[node][c]; }
            if (!valid) continue; int degree[26] = {}; for (int c = 0; c < 26; c++) for (int d = 0; d < 26; d++) if (edges[c] >> d & 1U) degree[d]++;
            vector<int> order; for (int c = 0; c < 26; c++) if (!degree[c]) order.push_back(c); for (size_t i = 0; i < order.size(); i++) { int c = order[i]; for (int d = 0; d < 26; d++) if ((edges[c] >> d & 1U) && --degree[d] == 0) order.push_back(d); } if (order.size() == 26) answer.push_back(id); }
        cout << answer.size() << '\n'; for (int id : answer) cout << words[id] << '\n';''',
        '不能把不同候选词的字母约束混在一起，每个词允许使用自己的字母表。前缀长短关系不受重排字母影响。重复边用位集去重，避免入度重复。',
        complexity=r'总字符数 $L$、词数 $n$，时间 $O(26L+26^2n)$，空间 $O(26L)$。')
    put(50993, 1700, ['01 字典树', '位运算', '贪心'], '从非负31位整数中选两数，最大化异或值。',
        '把每个整数从第30位到第0位插入二进制 Trie。查询 x 时，从高位到低位优先走与 x 当前位相反的分支，使结果这一位为一；不存在才走相同分支。高位一的收益超过所有低位之和，因此每步贪心成立。对所有 x 取查询结果的最大值。',
        r'''int n; cin >> n; vector<int> a(n); vector<array<int,2>> trie(1); trie.reserve(1 + 31 * n); for (int &x : a) { cin >> x; int node = 0; for (int b = 30; b >= 0; b--) { int bit = x >> b & 1; if (!trie[node][bit]) { trie[node][bit] = trie.size(); trie.push_back({0,0}); } node = trie[node][bit]; } }
        int answer = 0; for (int x : a) { int node = 0, value = 0; for (int b = 30; b >= 0; b--) { int bit = x >> b & 1; if (trie[node][bit ^ 1]) { value |= 1 << b; node = trie[node][bit ^ 1]; } else node = trie[node][bit]; } answer = max(answer, value); } cout << answer;''',
        '最高允许位是第30位，共31位。这里输出异或值，不是组成该值的两个原整数；重复数也可插入。',
        complexity=r'时间 $O(31n)$，最坏空间 $O(31n)$。')
    put(22998, 1800, ['前缀异或', '01 字典树'], '找异或最大的非空连续段；并列先取最早结束，再取最短长度。',
        '区间 [l,r] 异或为 prefix[r]^prefix[l-1]。按 r 从小到大，把已经出现的前缀异或放入二进制 Trie，查询与 prefix[r] 异或最大的旧前缀。相同旧前缀只保留最新下标，便能在固定 r、固定最大异或时取最大 l，也就是最短段。只有找到严格更大异或时才更新全局答案，扫描顺序自然保留最早的结束位置。查询后才插入 prefix[r]，确保区间非空。',
        r'''int n; cin >> n; struct Node { int child[2] = {}, latest = 0; }; vector<Node> trie(1); trie.reserve(1 + 21 * (n + 1));
        auto insert = [&](int value, int index) { int node = 0; for (int b = 20; b >= 0; b--) { int bit = value >> b & 1; if (!trie[node].child[bit]) { trie[node].child[bit] = trie.size(); trie.push_back({}); } node = trie[node].child[bit]; } trie[node].latest = index; };
        insert(0,0); int prefix = 0, best = -1, answerLeft = 1, answerRight = 1;
        for (int r = 1; r <= n; r++) { int x; cin >> x; prefix ^= x; int node = 0, value = 0; for (int b = 20; b >= 0; b--) { int bit = prefix >> b & 1; if (trie[node].child[bit ^ 1]) { value |= 1 << b; node = trie[node].child[bit ^ 1]; } else node = trie[node].child[bit]; }
            if (value > best) { best = value; answerLeft = trie[node].latest + 1; answerRight = r; } insert(prefix,r); } cout << best << ' ' << answerLeft << ' ' << answerRight;''',
        '社会等级越高对应编号越小，所以并列优先结束下标小。重复前缀要保留最新位置才能满足次级的最短长度要求。',
        complexity=r'时间、最坏空间均为 $O(21n)$。',
        cases=[{'input': '3\n0\n0\n0', 'output': '0 1 1'}, {'input': '3\n1\n0\n2', 'output': '3 1 3'}])
    put(233499, 1800, ['KMP', '前缀函数', '计数'], '找同时为前后缀且在整串中至少出现 k 次的最长非空串。',
        '对 S 求前缀函数。长度 len 的前缀的全部 border，沿 len→pi[len-1] 这条链依次出现。把每个前缀长度初始计数设为一，表示它自己在相应末尾的那次出现；按长度从大到小，把 count[len] 加到 count[pi[len-1]]，即可统计所有前缀的出现次数，包含重叠。最后从完整长度 n 开始沿 border 链回退，首个次数至少 k 的长度就是答案。',
        r'''int n, k; string s; cin >> n >> k >> s; auto pi = prefixFunction(s); vector<int> count(n + 1,1); count[0] = 0; for (int length = n; length > 0; length--) count[pi[length - 1]] += count[length];
        int length = n; while (length > 0 && count[length] < k) length = pi[length - 1]; if (length == 0) cout << -1; else cout << s.substr(0,length);''',
        '本题不要求是真 border，所以 k=1 时可以直接选完整字符串。重叠出现也计数；只检查最长真 border 会漏掉更短但次数足够的候选。',
        declarations=PREFIX_FUNCTION, complexity=r'时间、空间均为 $O(n)$。')
    put(233500, 2300, ['KMP', '树状数组', '倍增', '离线处理'], '末尾不断加字符，多次查询至少出现 k 次的最长前后缀长度。',
        '所有操作可以预读，先把追加后的最终字符串求出前缀函数，建立失败树：长度 i 的父亲是 pi[i-1]。任意较早版本的前缀函数不会因后续追加而改变，因此这棵最终树也适用于所有时刻。对当前串每个结束位置 j，激活失败树上的结点 j；某个前缀长度 len 的出现次数，恰是它失败树子树内已激活结点数。因为 len 是以 j 结尾的匹配，当且仅当 len 在 j 的 border 祖先链上。\n\n用迭代 DFS 求子树欧拉区间，树状数组做单点激活、子树计数。追加只激活一个新结点。查询的候选是当前长度的祖先链，越向上串越短，出现次数不会更少；利用倍增跳过仍不足 k 次的祖先，再看其父亲。每次频数查询 O(log N)，总查询 O(log²N)。',
        r'''int n, q; string s; cin >> n >> q >> s; s.reserve(n + q); struct Operation { int type, k = 0; char c = 0; }; vector<Operation> operations(q); for (auto &op : operations) { cin >> op.type; if (op.type == 1) { cin >> op.c; s += op.c; } else cin >> op.k; }
        int total = s.size(); const int log = 20; auto pi = prefixFunction(s); vector<array<int,log>> up(total + 1); vector<int> head(total + 1,-1), next(total + 1,-1), enter(total + 1), leave(total + 1);
        for (int i = 1; i <= total; i++) { int parent = pi[i - 1]; up[i][0] = parent; for (int b = 1; b < log; b++) up[i][b] = up[up[i][b - 1]][b - 1]; next[i] = head[parent]; head[parent] = i; }
        vector<pair<int,int>> stack; stack.reserve(total + 1); stack.push_back({0,0}); int timer = 0; while (!stack.empty()) { auto [u, stage] = stack.back(); stack.pop_back(); if (stage == 0) { enter[u] = ++timer; stack.push_back({u,1}); for (int v = head[u]; v != -1; v = next[v]) stack.push_back({v,0}); } else leave[u] = timer; }
        vector<int> tree(timer + 1); auto activate = [&](int node) { for (int p = enter[node]; p <= timer; p += p & -p) tree[p]++; }; auto prefix = [&](int p) { int value = 0; for (; p > 0; p -= p & -p) value += tree[p]; return value; }; auto count = [&](int node) { return prefix(leave[node]) - prefix(enter[node] - 1); };
        for (int i = 1; i <= n; i++) activate(i); int current = n; for (auto op : operations) { if (op.type == 1) { activate(++current); continue; } int node = current;
            if (count(node) < op.k) { for (int b = log - 1; b >= 0; b--) { int ancestor = up[node][b]; if (ancestor && count(ancestor) < op.k) node = ancestor; } node = up[node][0]; } cout << (node ? node : -1) << '\n'; }''',
        '未来追加的结点先建好，但只能在实际追加时激活。子树统计的是已出现的结束位置，不能直接使用最终整棵失败树的子树大小。空前缀不能作为答案。',
        declarations=PREFIX_FUNCTION,
        complexity=r'最终长度 $N\le n+q$，预处理与激活 $O(N\log N)$，每次查询 $O(\log^2N)$，空间 $O(N\log N)$。')
    source = problem('luogu-training-P4735')
    review_rating(51120, source['difficulty'], '完整核对动态末尾追加、区间起点限制、后缀异或与额外x，n/m各三十万、值一千万，与P4735一致。前缀异或转化后需持久化01Trie做版本区间查询，沿用ToBe2700映射档，非牛客官方评级。',
                  origin={'id': source['id'], 'url': source['url'], 'difficultySource': source.get('difficultySource'), 'sourceStatementSha256': sha(statement(source['id'])['markdown'])})
    review_rating(53251, 2800, '十万任意非负数，要求同一区间的前缀异或、最大值、最小值三者异或最大；最大值与最小值随两端共同变化，普通最大异或Trie或单独RMQ不足以枚举全部候选。需按极值结构组织分治/区间Trie查询并控制最坏复杂度，按2800估算。', knowledge=['01 字典树', '分治', '区间最值'])


if __name__ == '__main__':
    run()
    print('Registered five reviewed trie/border articles and two above-cutoff reviews.')
