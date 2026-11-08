"""Full-statement reviews: heaps, ordered frontiers and component merging."""
from nowcoder_editorials import CONTENT, ROOT, add, alias, read, register, review_rating
from nowcoder_dsu_support import DSU


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(20154, 2100, ['贪心', '优先队列', '调度'], '每栋建筑有抢修耗时和截止时刻，一次修一栋，求最多抢修数。',
        '按截止时刻递增。把当前建筑加入已选任务，若累计耗时超过截止时刻，从所有已选任务中删去耗时最长的一个。原已选任务均可行，删去最大耗时至少抵消新加入耗时，因此删一个就恢复可行。\n\n同数量的可行任务中，选择总耗时最小者能给后续留最多时间。遇到超时时必须舍弃至少一项，而舍弃最长项使剩余总耗时最小；由这一不变式逐项处理可保持最优数量。大根堆支持删除最长耗时。',
        r'''int n; cin >> n; vector<pair<int,int>> tasks(n); for (auto &[deadline,duration] : tasks) cin >> duration >> deadline; sort(tasks.begin(),tasks.end()); priority_queue<int> selected; long long elapsed = 0; for (auto [deadline,duration] : tasks) { elapsed += duration; selected.push(duration); if (elapsed > deadline) { elapsed -= selected.top(); selected.pop(); } } cout << selected.size();''',
        '截止时刻恰好完成仍可抢救。总耗时需64位；不能简单地忽略所有当前放不下的任务，替换最长任务可能为后续腾出时间。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(16884, 1800, ['并查集', '关系建模'], '逐条判定三类动物的同类、捕食关系是否与之前真话冲突，统计假话。',
        '每只动物建三个结点 x、x+n、x+2n，表示循环三种相对类。相同关系要求三组对应相连；x吃y要求 x 与 y+n、x+n 与 y+2n、x+2n 与 y 相连。加入前先判断与另外两种关系是否冲突。相同关系若 x 已与 y+n 或 y+2n 同组就是假话；捕食关系若 x 已与 y 或 y+2n 同组就是假话。越界同样是假话。只合并真话，假话完全忽略。',
        r'''int n, k; cin >> n >> k; DSU dsu(3 * n); int lies = 0; while (k--) { int type; long long rawX, rawY; cin >> type >> rawX >> rawY; if (rawX < 1 || rawX > n || rawY < 1 || rawY > n) { lies++; continue; } int x = rawX, y = rawY; bool falsehood = type == 1 ? (dsu.find(x) == dsu.find(y + n) || dsu.find(x) == dsu.find(y + 2 * n)) : (dsu.find(x) == dsu.find(y) || dsu.find(x) == dsu.find(y + 2 * n)); if (falsehood) { lies++; continue; } if (type == 1) { for (int offset = 0; offset < 3; offset++) dsu.unite(x + offset * n,y + offset * n); } else { dsu.unite(x,y + n); dsu.unite(x + n,y + 2 * n); dsu.unite(x + 2 * n,y); } } cout << lies;''',
        '捕食是有方向的三循环，不能只维护敌我两类。假话不写入并查集。x吃x会由同根检测自动判假。', declarations=DSU, complexity=r'时间 $O((n+k)\alpha(n))$，空间 $O(n)$。')
    put(16417, 1500, ['并查集', '空间距离'], '同半径球形空洞相交或相切即可通行，判断能否从奶酪底面到顶面。',
        '增加底面和顶面两个虚拟结点。球心高度 z≤r 时连到底面，z+r≥h 时连到顶面；任意两球心距离平方不超过4r²时合并。所有合并完成后比较两虚拟结点是否同根。距离只比较平方，不用开根号。坐标差最多二十亿，三个平方的和可能超过64位，用128位做距离计算。',
        r'''int tests; cin >> tests; while (tests--) { int n; long long h, r; cin >> n >> h >> r; vector<array<long long,3>> p(n); DSU dsu(n + 1); int bottom = n, top = n + 1; for (int i = 0; i < n; i++) { cin >> p[i][0] >> p[i][1] >> p[i][2]; if (p[i][2] <= r) dsu.unite(i,bottom); if (p[i][2] + r >= h) dsu.unite(i,top); for (int j = 0; j < i; j++) { __int128 distance = 0; for (int axis = 0; axis < 3; axis++) { __int128 d = p[i][axis] - p[j][axis]; distance += d * d; } if (distance <= (__int128)4 * r * r) dsu.unite(i,j); } } cout << (dsu.find(bottom) == dsu.find(top) ? "Yes\n" : "No\n"); }''',
        '相切也允许，所以使用≤。每组重新初始化；先转128位再乘，避免乘法已溢出后才转换。', declarations=DSU, complexity=r'每组时间 $O(n^2\alpha(n))$，空间 $O(n)$。')
    put(50940, 1500, ['优先队列', '中位数'], '每读入奇数个数，就输出当前中位数，答案每行至多十个。',
        '用大根堆存较小的一半，小根堆存较大的一半。插入时先按大根堆顶分边，再调整到左堆个数等于右堆或多一。保持左堆所有数不大于右堆所有数后，奇数时左堆堆顶就是中位数。每组先输出原数据编号与答案个数，随后按十个一行输出。',
        r'''int tests; cin >> tests; while (tests--) { int id, n; cin >> id >> n; priority_queue<int> left; priority_queue<int, vector<int>, greater<int>> right; vector<int> answer;
        for (int i = 0; i < n; i++) { int x; cin >> x; if (left.empty() || x <= left.top()) left.push(x); else right.push(x);
            if (left.size() > right.size() + 1) { right.push(left.top()); left.pop(); } if (left.size() < right.size()) { left.push(right.top()); right.pop(); } if (i % 2 == 0) answer.push_back(left.top()); }
        cout << id << ' ' << answer.size() << '\n'; for (int i = 0; i < (int)answer.size(); i++) { cout << answer[i]; cout << ((i % 10 == 9 || i + 1 == (int)answer.size()) ? '\n' : ' '); } }''',
        '比较原整数，不把两个堆顶相加，避免32位有符号整数溢出。本题只在奇数长度时输出，无需求偶数中位数。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    put(214362, 1400, ['优先队列', '第k小'], '只插入元素，多次查询固定的第 k 小，不足 k 个输出负一。',
        '维护一个最多有 k 个元素的大根堆，始终保留已经出现的最小 k 个数。每次插入后，若超过 k 个就删除最大者。因此满 k 个时堆顶恰是第 k 小；未满则不存在答案。重复值作为独立元素保留。',
        r'''int n, m, k; cin >> n >> m >> k; priority_queue<int> heap; auto insert = [&](int x) { heap.push(x); if ((int)heap.size() > k) heap.pop(); }; for (int i = 0, x; i < n; i++) { cin >> x; insert(x); } while (m--) { int type; cin >> type; if (type == 1) { int x; cin >> x; insert(x); } else cout << ((int)heap.size() < k ? -1 : heap.top()) << '\n'; }''',
        'k 固定才可以丢弃更大的元素。第 k 小按重数计，不能用会去重的 set。', complexity=r'时间 $O((n+m)\log k)$，空间 $O(k)$。')
    put(50439, 1800, ['贪心', '优先队列'], '选择士兵，人数不能超过每个入选士兵的上限，最大化战力和。',
        '按人数上限 s 从大到小扫描。处理上限为 s 的士兵时，之前见过的士兵都允许至少 s 人的队伍；用小根堆保留至多 s 个战力最大的士兵。加入当前士兵后，堆过大就弹掉最弱者，记录战力和最大值。任一最优队伍都有最小上限 s，在该上限处理完后堆给出的战力至少同样大，因此不会漏解。',
        r'''int n; cin >> n; vector<pair<int,int>> soldiers(n); for (auto &[limit, value] : soldiers) cin >> value >> limit; sort(soldiers.rbegin(), soldiers.rend()); priority_queue<int,vector<int>,greater<int>> heap; long long sum = 0, answer = 0;
        for (auto [limit, value] : soldiers) { heap.push(value); sum += value; while ((int)heap.size() > limit) { sum -= heap.top(); heap.pop(); } answer = max(answer, sum); } cout << answer;''',
        '战力全为正，所以容量允许时应尽量保留。战力总和可达十万乘十亿，必须用64位。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(20185, 2100, ['优先队列', '贪心', '离线处理'], '已知全部访问请求，求容量固定的空缓存的最少缺失次数。',
        '先将任意大编号离散化，再倒序求每次访问的下次位置，不再访问记为 n。缓存满时淘汰下次使用最晚的页面。交换理由：若某最优策略先淘汰较早再用的页面，可改为淘汰较晚者；直到较早者再次被请求前都不增加缺失，届时再对齐两种缓存，故最优值不会变差。\n\n大根堆存下次位置与页面，命中后也更新。旧的堆记录延迟删除，淘汰前跳过已不在缓存或下次位置过期的记录。',
        r'''int n, capacity; cin >> n >> capacity; vector<int> a(n), values; for (int &x : a) cin >> x; values = a; sort(values.begin(), values.end()); values.erase(unique(values.begin(), values.end()), values.end()); for (int &x : a) x = lower_bound(values.begin(),values.end(),x) - values.begin();
        int kinds = values.size(); vector<int> next(n), last(kinds,n), current(kinds,-1); for (int i = n - 1; i >= 0; i--) { next[i] = last[a[i]]; last[a[i]] = i; } vector<bool> present(kinds); priority_queue<pair<int,int>> heap; int size = 0, misses = 0;
        for (int i = 0; i < n; i++) { int x = a[i]; if (!present[x]) { misses++; if (size == capacity) { while (!present[heap.top().second] || current[heap.top().second] != heap.top().first) heap.pop(); present[heap.top().second] = false; heap.pop(); size--; } present[x] = true; size++; } current[x] = next[i]; heap.push({next[i],x}); } cout << misses;''',
        '题目编号可达十亿，不能按编号直接开数组。缓存初始为空；即使命中也要更新下次访问时间。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(20951, 1800, ['贪心', '优先队列', '区间匹配'], '每条服务线只能接待某一编号区间中的用户，且有容量，最大化被接待人数。',
        '按用户编号从小到大处理，把左端点不超过当前用户的服务线入小根堆，按右端点排序，弹出已过期的线。若还有线就给当前用户分配右端点最早的一条，并减少其剩余容量。若最优方案用另一条线服务当前用户，可以交换两条线后续服务的用户：更晚结束的线能承接较早结束的线所承接的后续用户，故不减少人数。没有可用线时只能跳过。',
        r'''int n, m; while (cin >> n >> m) { struct Line { int l, r, capacity; }; vector<Line> lines(m); for (auto &x : lines) cin >> x.l >> x.r >> x.capacity; sort(lines.begin(),lines.end(),[](auto a, auto b) { return a.l < b.l; }); priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>> heap; int j = 0, answer = 0;
        for (int user = 1; user <= n; user++) { while (j < m && lines[j].l <= user) { if (lines[j].capacity > 0) heap.push({lines[j].r,lines[j].capacity}); j++; } while (!heap.empty() && heap.top().first < user) heap.pop(); if (!heap.empty()) { auto [r,c] = heap.top(); heap.pop(); answer++; if (--c) heap.push({r,c}); } } cout << answer << '\n'; }''',
        '原题多组读至EOF，没有开头测试组数。每个用户只能分配一次，线的剩余容量归零后不再入堆。', complexity=r'每组时间 $O((n+m)\log m)$，空间 $O(m)$。')
    put(22604, 2000, ['贪心', '优先队列', '调度'], '允许付实数金币缩短任务耗时，不能缩到负数，求按时完成所有任务的最少金币。',
        '先按截止时间排序：若相邻两任务的截止时间逆序，交换后不影响较早截止任务完成，且较晚截止任务也不会更晚，因此可用截止时间顺序执行。依次加入任务的原始耗时。若累计耗时超过当前截止时间，必须从已经加入的任务中删去这段超时。每枚金币能减少 z 单位时间，优先缩短 z 最大的任务最省钱；用大根堆记录 z 和该任务尚可缩短的耗时。可删完整任务，也可只删够当前超时。\n\n每个截止前缀都必须满足；在当前前缀内选择最便宜的时间缩减，不能用未来任务替代。对任一可行方案交换同等缩减量到更大 z 的已到期前缀内，不会破坏前缀约束且费用不增，故贪心成立。',
        r'''int n; cin >> n; struct Task { int z, x, deadline; }; vector<Task> tasks(n); for (auto &t : tasks) cin >> t.z >> t.x >> t.deadline; sort(tasks.begin(),tasks.end(),[](auto a, auto b) { return a.deadline < b.deadline; }); priority_queue<pair<int,int>> heap; long long elapsed = 0; long double cost = 0;
        for (auto t : tasks) { elapsed += t.x; heap.push({t.z,t.x}); while (elapsed > t.deadline) { auto [z, remaining] = heap.top(); heap.pop(); long long remove = min<long long>(remaining,elapsed - t.deadline); elapsed -= remove; cost += (long double)remove / z; remaining -= remove; if (remaining) heap.push({z,remaining}); } } cout << fixed << setprecision(1) << cost;''',
        '金币可为实数，耗时的缺口和剩余可缩短时间仍是整数。优先比较 z，而不是原耗时或单个任务总费用。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。', floating_output=True)
    put(17889, 1200, ['优先队列', '模拟'], '新建时取最小空闲正编号；删除时判断文件是否存在。',
        '将1到n都放入小根堆，表示空闲编号；至多n次新建，故这些编号足够。新建取堆顶并标记存在；成功删除时取消标记并将编号放回堆。删除不存在的文件不能放回编号，否则会重复分配。',
        r'''int n; cin >> n; priority_queue<int,vector<int>,greater<int>> available; vector<bool> exists(n + 1); for (int i = 1; i <= n; i++) available.push(i); while (n--) { string op; cin >> op; if (op == "New") { int id = available.top(); available.pop(); exists[id] = true; cout << id << '\n'; } else { int id; cin >> id; if (id > 0 && id < (int)exists.size() && exists[id]) { exists[id] = false; available.push(id); cout << "Successful\n"; } else cout << "Failed\n"; } }''',
        '删除编号可能超过实际创建过的最大编号，需要先检查数组范围。只有成功删除才回收。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    if 'nowcoder-global::207569' not in existing:
        code = r'''#include <bits/stdc++.h>
        using namespace std;
        class Solution { public: int oddNumber(int n, vector<int>& a) { (void)n; vector<int> even; for (int x : a) if (x % 2 == 0) even.push_back(x); sort(even.begin(),even.end()); even.erase(unique(even.begin(),even.end()),even.end()); priority_queue<int> heap(even.begin(),even.end()); int answer = 0; while (!heap.empty()) { int x = heap.top(); heap.pop(); if (!heap.empty() && heap.top() == x) continue; answer++; x /= 2; if (x % 2 == 0) heap.push(x); } return answer; } };'''
        article = '## 牛牛爱奇数\n\n### 思路\n\n从最大的偶数开始操作。同一数值的所有副本能一次一起处理；先处理较大值，能让它们除二后与较小值合并，再一起操作。若先处理较小值，则未来可能需要为到达这个值的数重复付费，所以交换为降序处理不会更差。用大根堆去掉同值副本，每个不同堆顶计一次操作，除二后仍偶数才入堆。\n\n### 参考代码\n\n原站采用函数接口，保留指定方法 `oddNumber`。\n\n```cpp\n' + code + '\n```\n\n### 复杂度\n\n每个偶数每次至少减半，记生成的不同偶数状态数为 $K$。时间 $O(n\log n+K\log n)$，空间 $O(n)$。\n\n### 易错点\n\n一次处理全部相同值；奇数无需入堆。输入的方括号样例由平台驱动读取，提交代码只提供类和函数。\n'
        driver = r'''int main() { string raw((istreambuf_iterator<char>(cin)), {}); for (char &c : raw) if (!isdigit((unsigned char)c)) c = ' '; istringstream input(raw); int n; input >> n; vector<int> a(n); for (int &x : a) input >> x; cout << Solution().oddNumber(n,a); }'''
        register(207569, 1500, ['优先队列', '贪心'], '最大偶数优先、合并重复状态，已核验原站指定oddNumber类方法。', {'default': article}, driver=driver)
    put(251558, 2000, ['有序集合', '贪心', '二维偏序'], '每次加入一位候选人，统计两个评分均越小越好的非支配者人数；完全同分者互不支配。',
        '非支配前沿按第一评分 x 递增后，第二评分 y 必须严格递减。用 map 将 x 映射到 (y,人数)。插入 (x,y) 时，先看同 x 的旧点：旧 y 更小则新点被支配；相等则增加人数；更大则旧点应删除。再看 x 更小的最近前驱，若其 y≤新 y，新点被支配。否则新点有效，并依次删除右侧所有 y≥新 y 的点。前沿的严格单调性保证被删除点连续，每个点最多删一次。答案维护人数而非不同评分对个数。',
        r'''int tests; cin >> tests; for (int tc = 1; tc <= tests; tc++) { int n; cin >> n; map<int,pair<int,int>> frontier; int total = 0; if (tc > 1) cout << '\n'; cout << "Case #" << tc << ":\n";
        for (int i = 0; i < n; i++) { int x, y; cin >> x >> y; auto it = frontier.lower_bound(x); bool dominated = false; if (it != frontier.begin() && prev(it)->second.first <= y) dominated = true;
            if (it != frontier.end() && it->first == x) { if (it->second.first < y) dominated = true; else if (it->second.first == y) { it->second.second++; total++; cout << total << '\n'; continue; } }
            if (!dominated) { while (it != frontier.end() && it->second.first >= y) { total -= it->second.second; it = frontier.erase(it); } frontier[x] = {y,1}; total++; } cout << total << '\n'; } }''',
        '相同的两个评分必须保留两个人；支配定义要求至少一个评分严格更好。原题测试组之间空一行。', complexity=r'每组摊还时间 $O(n\log n)$，空间 $O(n)$。')
    put(251572, 2100, ['贪心', '有序集合', '二维匹配'], '每个我方部队只能攻击一次，必须消灭全部敌军，最大化战后我方存活总数。',
        '按敌军防御从大到小处理，将攻击力足够消灭当前敌人的全部未用我军放入按防御排序的 multiset。这些部队也都能打后面防御更低的敌人。若集合为空则无法完成。优先选防御严格大于敌军攻击的最小值，以存活且留下更强防御；若没有这样的部队，当前必有一支牺牲，选最小防御者。\n\n交换论证：固定任一最优分配。当前贪心选的部队若原本分配给后面的敌人，可与最优方案当前用兵交换，攻击条件仍满足。选到最弱的可存活者时，被换到后面的部队防御不小于它，或当前方案原本要牺牲从而已多救一人；选到最弱且必死者时，其他可用部队也全会死，换到后面不会变差。故逐步固定贪心选择可保持最优。初始 n 支均存活，每次被敌军消灭才减一。',
        r'''int tests; cin >> tests; for (int tc = 1; tc <= tests; tc++) { int n, m; cin >> n >> m; vector<pair<int,int>> ours(n), enemies(m); for (auto &[attack,defense] : ours) cin >> attack >> defense; for (auto &[defense,attack] : enemies) cin >> attack >> defense; sort(ours.rbegin(),ours.rend()); sort(enemies.rbegin(),enemies.rend()); multiset<int> defense; int j = 0, survivors = n; bool possible = true;
        for (auto [need,enemyAttack] : enemies) { while (j < n && ours[j].first >= need) { defense.insert(ours[j].second); j++; } if (defense.empty()) { possible = false; break; } auto it = defense.upper_bound(enemyAttack); if (it == defense.end()) { it = defense.begin(); survivors--; } defense.erase(it); } cout << "Case #" << tc << ": " << (possible ? survivors : -1) << '\n'; }''',
        '攻击力等于防御力也会消灭对手，我军存活要求防御严格大于敌攻击。没出战的我军也计入存活数。', complexity=r'每组时间 $O((n+m)\log(n+m))$，空间 $O(n+m)$。')
    put(22596, 1800, ['有序集合', '二叉搜索树'], '按图中规则向普通二叉搜索树插入，重复值不新建，每次输出深度总和。',
        '已查看原题伪代码：小于走左、大于走右，等于时不做任何事。新值的父亲一定是已插入值中的前驱或后继；两者都存在时，取深度更大的一个，再加一。原因是前驱与后继之间没有已插入键，新键所在空隙的两个边界中较深者就是直接父结点；若两边界都在树中，较浅者是较深者的祖先。用 map 保存已插入键的深度，根深度为零。',
        r'''int n; cin >> n; map<int,int> depth; long long total = 0; while (n--) { int x; cin >> x; auto it = depth.lower_bound(x); if (it == depth.end() || it->first != x) { int parentDepth = -1; if (it != depth.end()) parentDepth = max(parentDepth,it->second); if (it != depth.begin()) parentDepth = max(parentDepth,prev(it)->second); int d = parentDepth + 1; depth[x] = d; total += d; } cout << total << '\n'; }''',
        '不能真的按普通BST一路走，升序输入会退化到平方。伪代码没有处理相等值，因此相等时深度总和不变。', complexity=r'时间 $O(n\log n)$，空间 $O(n)$。', cases=[{'input':'5\n2\n1\n3\n2\n4','output':'0\n1\n2\n2\n4'}])
    put(23803, 1200, ['并查集', '字符串映射'], '按姓名合并亲戚关系并查询连通性，重名视为同一个人。',
        '先把不同姓名映射到整数编号，重复姓名复用原编号。亲戚关系满足传递性，因此每个家族是一个并查集集合；类型一合并，类型二比较根。按集合大小合并并压缩路径。',
        r'''int n, m; cin >> n >> m; map<string,int> id; int count = 0; for (int i = 0; i < n; i++) { string name; cin >> name; if (!id.count(name)) id[name] = ++count; } DSU dsu(count); while (m--) { int type; string a, b; cin >> type >> a >> b; if (type == 1) dsu.unite(id.at(a),id.at(b)); else cout << (dsu.find(id.at(a)) == dsu.find(id.at(b))) << '\n'; }''',
        '两条相同姓名记录不能分配不同结点；查询不新增关系。', declarations=DSU, complexity=r'映射使用平衡树，时间 $O((n+m)\log n)$，空间 $O(n)$。')
    put(14545, 1700, ['并查集', '多重背包'], '只能与关系网中从1可接触的人交际，每人一次，在精力容量内最大化收益。',
        '关系可传递，先并查集合并全部无向关系，只保留与1同根的人。之后是独立的01背包。相同 (精力,收益) 的人可合为一类，把数量按1、2、4等二进制拆组，逐组倒序更新容量，减少重复物品带来的开销。起点1没有对应可选收益物品。',
        r'''int tests; cin >> tests; while (tests--) { int n, m, capacity; cin >> n >> m >> capacity; vector<pair<int,int>> items(n + 1); for (int i = 2; i <= n; i++) cin >> items[i].first >> items[i].second; DSU dsu(n); while (m--) { int a, b; cin >> a >> b; dsu.unite(a,b); } map<pair<int,int>,int> counts; for (int i = 2; i <= n; i++) if (dsu.find(i) == dsu.find(1)) counts[items[i]]++; vector<long long> dp(capacity + 1);
        for (auto [item,count] : counts) { auto [cost,value] = item; for (int block = 1; count > 0; block *= 2) { int take = min(block,count); count -= take; int weight = cost * take; long long profit = 1LL * value * take; for (int c = capacity; c >= weight; c--) dp[c] = max(dp[c],dp[c - weight] + profit); } } cout << dp[capacity] << '\n'; }''',
        '只看1的连通块；不能将整块人数当成必须一起选的一个物品。分组后仍需倒序更新。', declarations=DSU, complexity=r'设保留物品数为 $R$、拆分后组数为 $G$，时间 $O((n+m)\alpha(n)+R\log R+GC)$，空间 $O(n+R+C)$。')
    put(24608, 1500, ['并查集', '构造'], '有共同语言的牛能互相传话，最少买语言书使所有牛连通，并输出具体教书方案。',
        '每种语言记一只已经会它的牛，以后遇到也会该语言的牛就将两者合并。得到 c 个牛的连通块后，一本书最多使两个块连起来，因此至少 c−1 本。选牛1已经会的一种语言，给其余每个块的一只代表牛各买一本这种语言的书，恰好 c−1 本便全部连通。每只牛至少会一种语言，故所选公共语言一定存在。',
        r'''int n, m; cin >> n >> m; DSU dsu(n); vector<int> owner(m + 1); int common = 0; for (int cow = 1; cow <= n; cow++) { int k; cin >> k; while (k--) { int language; cin >> language; if (cow == 1 && common == 0) common = language; if (owner[language]) dsu.unite(cow,owner[language]); else owner[language] = cow; } } vector<int> representatives; for (int cow = 1; cow <= n; cow++) if (dsu.find(cow) == cow && dsu.find(cow) != dsu.find(1)) representatives.push_back(cow); cout << representatives.size() << '\n'; for (int cow : representatives) cout << common << ' ' << cow << '\n';''',
        '未被任何牛使用的语言不构成需要连通的块。输出先是语言编号，再是牛编号；题面样例只给书本数，但完整提交仍要输出方案。', declarations=DSU, complexity=r'总已知语言条数 $L$，时间 $O((n+L)\alpha(n)+m)$，空间 $O(n+m)$。', checker='language-connectivity-books')
    put(14685, 1100, ['并查集', '连通分量'], '给无向图加最少的边，使任意两点可达。',
        '每次成功合并两个连通块，块数减一。最终若有 c 块，一条新边最多减少一个块，所以至少加 c−1 条；把各块代表连成一条链就能达到。',
        r'''int n, m; cin >> n >> m; DSU dsu(n); int components = n; while (m--) { int a, b; cin >> a >> b; if (dsu.unite(a,b)) components--; } cout << components - 1;''',
        '原有重边或自环不减少连通块数，只有合并成功才减。', declarations=DSU, complexity=r'时间 $O((n+m)\alpha(n))$，空间 $O(n)$。')
    put(15976, 2200, ['并查集', '启发式合并'], '按顺序连线，对每种游戏求全部玩家首次同处一个连通块的时刻。',
        '每个并查集根维护一个“游戏编号→本块人数”的映射，另统计各游戏总人数。合并两块时把较小块的计数加进较大块；某个游戏的块内人数达到总数，就在此时首次连通，记录当前线号。每种游戏只需首次记录。小块并入大块时，每个被搬运玩家所在块大小至少翻倍，因此所有搬运总量 O(n log n)，映射用平衡树再乘一个对数。只有一个玩家（或没有玩家）的游戏在时刻0就无须连线；始终分散者输出−1。',
        r'''int n, m, q; while (cin >> n >> m >> q) { vector<int> game(n + 1), total(m + 1), answer(m + 1,-1); vector<map<int,int>> count(n + 1); DSU dsu(n); for (int i = 1; i <= n; i++) { cin >> game[i]; total[game[i]]++; count[i][game[i]] = 1; } for (int g = 1; g <= m; g++) if (total[g] <= 1) answer[g] = 0;
        for (int time = 1; time <= q; time++) { int a, b; cin >> a >> b; a = dsu.find(a); b = dsu.find(b); if (a == b) continue; if (dsu.size[a] < dsu.size[b]) swap(a,b); dsu.parent[b] = a; dsu.size[a] += dsu.size[b]; for (auto [g,c] : count[b]) { int value = (count[a][g] += c); if (value == total[g] && answer[g] == -1) answer[g] = time; } count[b].clear(); } for (int g = 1; g <= m; g++) cout << answer[g] << '\n'; }''',
        '联通的是整条路径，不要求同一游戏的玩家直接相连；可以借助玩其他游戏的中间人。重复连接同块不改变计数。', declarations=DSU, complexity=r'每组时间 $O((n+q)\alpha(n)+n\log^2 n)$，空间 $O(n+m)$。')
    put(51097, 1800, ['并查集', '前缀异或', '离散化'], '区间一的个数奇偶约束，求最长一致的陈述前缀。',
        '设 prefix[i] 为前 i 位异或，区间 [l,r] 奇偶就是 prefix[l−1]^prefix[r]。只对出现的 l−1、r 离散化。用两倍并查集：结点 x 表示该前缀值，x+K 表示它的反值。偶约束将同值合并、反值合并；奇约束交叉合并。加入前先检查是否已被强制成相反关系；首次矛盾时，之前陈述数就是答案。',
        r'''int length, m; cin >> length >> m; struct Query { int l, r, odd; }; vector<Query> queries(m); vector<int> values; for (auto &q : queries) { string kind; cin >> q.l >> q.r >> kind; q.l--; q.odd = kind == "odd"; values.push_back(q.l); values.push_back(q.r); } sort(values.begin(),values.end()); values.erase(unique(values.begin(),values.end()),values.end()); int k = values.size(); DSU dsu(2 * k); int answer = m;
        for (int i = 0; i < m; i++) { auto q = queries[i]; int a = lower_bound(values.begin(),values.end(),q.l) - values.begin(), b = lower_bound(values.begin(),values.end(),q.r) - values.begin(); bool conflict = q.odd ? dsu.find(a) == dsu.find(b) : dsu.find(a) == dsu.find(b + k); if (conflict) { answer = i; break; } if (q.odd) { dsu.unite(a,b + k); dsu.unite(a + k,b); } else { dsu.unite(a,b); dsu.unite(a + k,b + k); } } cout << answer;''',
        '左端点用 l−1，不能用 l。输出矛盾之前的条数，不是第一条矛盾的编号。原序列十亿长度，不可直接开数组。', declarations=DSU, complexity=r'时间 $O(m\log m)$，空间 $O(m)$。')
    review_rating(17315, 2500, '十万物品、恰取m个、容量限制且偶数时目标为两中心值平均。单一阈值只约束上半部分，不能确定两个中心值的和；需排序后的两侧最小代价维护与双中心联合优化，区别于普通二分最大下中位数。按2500估分，等待原站数字评级时优先覆盖此估分。', knowledge=['优先队列', '中位数', '贪心'])


if __name__ == '__main__':
    run()
