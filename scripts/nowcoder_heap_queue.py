"""Reviewed queues, offline cache replacement and persistent text history."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing = read(CONTENT / 'reviewed.json')

    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)

    put(15688, 1900, ['贪心', '优先队列', '离线处理'], '完整访问序列已知，容量 N 的页面缓存最少发生多少次缺页。',
        '先倒序预处理每次访问之后，这个页面下一次会在哪个时刻被用到；不再访问则记为无穷。缓存满且缺页时，淘汰下一次访问最晚的页面。交换论证：若某最优方案反而淘汰更早要用的页面，在那个较早时刻之前保留它、换掉较晚页面，不会多缺页；到较早时刻再使两方案缓存一致即可。\n\n用大根堆保存 (下次访问时刻,页面)。页面命中后更新时间并再入堆，旧记录延迟删除；淘汰时跳过已经不在缓存或记录时间过期的堆顶。',
        r'''int capacity, pages, q; while (cin >> capacity >> pages >> q) { vector<int> request(q), next(q), last(pages + 1, q), current(pages + 1, -1); for (int &x : request) cin >> x;
            for (int i = q - 1; i >= 0; i--) { next[i] = last[request[i]]; last[request[i]] = i; }
            vector<bool> present(pages + 1); priority_queue<pair<int,int>> heap; int size = 0, misses = 0;
            for (int i = 0; i < q; i++) { int page = request[i]; if (!present[page]) { misses++; if (size == capacity) { while (!heap.empty() && (!present[heap.top().second] || current[heap.top().second] != heap.top().first)) heap.pop(); int removed = heap.top().second; heap.pop(); present[removed] = false; size--; } present[page] = true; size++; }
                current[page] = next[i]; heap.push({next[i], page}); } cout << misses << '\n'; }''',
        '这是已知未来的离线最优置换，命中也必须更新下一访问时刻。多组输入直到文件结束，每组清空缓存。',
        complexity=r'时间 $O(Q\log Q+M)$，空间 $O(Q+M)$；堆包含待清理的旧记录。')
    put(15975, 2000, ['可持久化', '倍增', '栈'], '支持末尾插入、删除、第 k 字符查询与撤销最近一次修改。',
        '把每个字符结点连向前一个字符，当前文本只用末尾结点 root 表示。插入创建新结点，删除 k 个字符就是沿祖先退 k 步；撤销只需恢复修改前保存的 root，旧结点从不覆盖。第 k 个字符位于从末尾向前 length-k 步。用二进制倍增祖先表，让删除和查询都只走 O(log L) 次。历史栈只记录插入、删除之前的 root，查询与撤销不新增历史。\n\n这种表示会共享不同版本的前缀，反复删除、撤销长文本也只切换结点编号，不复制整段内容。累计新建字符不超过输入 append 字符总量一百万；预留二十级祖先表约八十兆字节，连同其他数组在本题一百二十八兆限制内。',
        r'''int q; while (cin >> q) { const int log = 20; vector<array<int,log>> up(1); vector<int> depth(1,0), history; vector<char> letter(1,0); up[0].fill(0); up.reserve(1000001); depth.reserve(1000001); letter.reserve(1000001); history.reserve(q); int root = 0;
            auto ancestor = [&](int node, int steps) { for (int bit = 0; bit < log; bit++) if (steps >> bit & 1) node = up[node][bit]; return node; };
            while (q--) { int type; cin >> type; if (type == 1) { string text; cin >> text; history.push_back(root); for (char c : text) { array<int,log> row{}; row[0] = root; for (int bit = 1; bit < log; bit++) row[bit] = up[row[bit - 1]][bit - 1]; up.push_back(row); letter.push_back(c); depth.push_back(depth[root] + 1); root = (int)letter.size() - 1; } }
                else if (type == 2) { int k; cin >> k; history.push_back(root); root = ancestor(root, k); }
                else if (type == 3) { int k; cin >> k; cout << letter[ancestor(root, depth[root] - k)] << '\n'; }
                else { root = history.back(); history.pop_back(); } } }''',
        '样例允许删成空串，零号结点代表空文本。预留容量避免大祖先表扩容时同时占用新旧内存。撤销后再插入会分出新版本，不能重写旧结点。',
        complexity=r'累计插入 $L$ 个字符、$q$ 个操作，时间 $O((L+q)\log L)$，空间 $O(L\log L+q)$。')
    put(16663, 1300, ['贪心', '优先队列', 'Huffman 树'], '反复合并任意两堆，代价为两堆之和，最小化累计代价。',
        '把合并过程看作二叉树，每堆重量会按它的叶子深度重复计入代价。最深处有一对兄弟叶子，把最小的两堆交换到这里不会增加总费用。因此可以先合并当前最小两堆，缩成一堆后继续同样的问题。用小根堆重复取两项、累加其和、把和放回。',
        r'''int n; cin >> n; priority_queue<long long, vector<long long>, greater<long long>> heap; for (int i = 0; i < n; i++) { long long x; cin >> x; heap.push(x); } long long answer = 0;
        while (heap.size() > 1) { long long x = heap.top(); heap.pop(); long long y = heap.top(); heap.pop(); answer += x + y; heap.push(x + y); } cout << answer;''',
        '新合成的一堆也必须参与之后的最小值选择。n=1 时已经是一堆，代价零。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(16430, 2100, ['单调队列', '懒标记', '多路归并'], '每秒切最长蚯蚓，只有未新生的蚯蚓增长 q，按步数和最终排名抽样输出。',
        '用全局增量 offset 表示所有已有蚯蚓的统一增长，保存长度减 offset 后的基准值。当前最大实际长度是最大基准值加 offset。切分后先把 offset 增加 q，再把两个新段减去新的 offset 存入，保证它们本秒不增长。\n\n初始蚯蚓排序后是一条递减队列，两种切分结果也分别按生成顺序递减：相邻两次被切的实际长度 x、y 满足 y<=x+q，而 floor(py)-floor(px)<=q，所以扣除每秒增长后，第一种新段不会变大；第二种同理。于是只需三条队列，每次比较三个队首取最大，不用数百万次堆操作。切完后按同样三路归并取最终降序排名。',
        r'''int n, m, growth, u, v, interval; cin >> n >> m >> growth >> u >> v >> interval; vector<int> queues[3]; queues[0].resize(n); queues[1].reserve(m); queues[2].reserve(m); for (int &x : queues[0]) cin >> x; sort(queues[0].begin(), queues[0].end(), greater<int>()); size_t head[3] = {}; long long offset = 0;
        auto take = [&]() { int selected = -1; for (int j = 0; j < 3; j++) if (head[j] < queues[j].size() && (selected == -1 || queues[j][head[j]] > queues[selected][head[selected]])) selected = j; return queues[selected][head[selected]++]; };
        bool first = true; auto output = [&](long long x) { if (!first) cout << ' '; first = false; cout << x; };
        for (int second = 1; second <= m; second++) { long long length = take() + offset; if (second % interval == 0) output(length); long long left = length * u / v, right = length - left; offset += growth; queues[1].push_back((int)(left - offset)); queues[2].push_back((int)(right - offset)); }
        cout << '\n'; first = true; for (int rank = 1; rank <= n + m; rank++) { long long length = take() + offset; if (rank % interval == 0) output(length); } cout << '\n';''',
        '切段乘 u 前先用 long long，不能浮点乘 p 再取整。新段扣的是增长后的 offset。本题基准值范围约在 -14亿至1亿，可用 int 节省队列空间；实际长度和乘法仍用 long long。',
        complexity=r'时间 $O(n\log n+n+m)$，空间 $O(n+m)$。',
        cases=[{'input': '1 0 0 1 2 2\n0', 'output': '\n\n'}])
    put(14661, 1300, ['双端队列', '模拟', '懒标记'], '支持双端插删、整体反转、输出与少量排序操作。',
        '用 deque 保存物理顺序，再用 reversed 标志表示逻辑方向。反转只切换标志；逻辑头尾的插删依标志映射到物理头尾。输出按逻辑方向遍历。排序次数最多十次，可以直接把 deque 升序排序并把 reversed 清零，令逻辑顺序确为从小到大。',
        r'''int n, m; cin >> n >> m; deque<int> a; bool reversed = false; while (m--) { int op; cin >> op;
            if (op == 1 || op == 3) { int x; cin >> x; bool front = (op == 1) != reversed; if (front) a.push_front(x); else a.push_back(x); }
            else if (op == 2 || op == 4) { bool front = (op == 2) != reversed; if (front) a.pop_front(); else a.pop_back(); }
            else if (op == 5) reversed = !reversed;
            else if (op == 6) { cout << a.size() << '\n'; for (int i = 0; i < (int)a.size(); i++) { if (i) cout << ' '; cout << a[reversed ? a.size() - 1 - i : i]; } cout << '\n'; }
            else { sort(a.begin(), a.end()); reversed = false; } }''',
        '整体反转后，头插和尾插的物理位置也必须随之反转。排序应清除反转标志。输出末尾不留空格。',
        complexity=r'普通操作 $O(1)$，每次输出 $O(n)$，每次排序 $O(n\log n)$；输出、排序合计至多十次，空间 $O(n)$。')
    put(17059, 1400, ['链表', '模拟'], '把任意指定元素移到队首或队尾，最终输出排列。',
        '用双向链表存队列，另按元素值保存它的迭代器。每次操作借助 list::splice，把指定结点直接挪到表头或表尾，结点迭代器保持有效，不用重新搜索或移动中间元素。最后顺序遍历链表。',
        r'''int n; cin >> n; list<int> queue; vector<list<int>::iterator> location(n + 1); for (int i = 0; i < n; i++) { int x; cin >> x; queue.push_back(x); location[x] = prev(queue.end()); }
        int p; cin >> p; while (p--) { string op; int x; cin >> op >> x; if (op == "FIRST") queue.splice(queue.begin(), queue, location[x]); else queue.splice(queue.end(), queue, location[x]); }
        bool first = true; for (int x : queue) { if (!first) cout << ' '; first = false; cout << x; }''',
        '每个编号只出现一次，移动时应挪动已有结点。单纯在 vector 中查找、擦除会退化为每次线性。',
        complexity=r'时间 $O(n+p)$，空间 $O(n)$。')


if __name__ == '__main__':
    run()
    print('Registered six reviewed heap and queue articles.')
