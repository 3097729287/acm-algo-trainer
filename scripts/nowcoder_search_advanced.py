"""All remaining eligible search-list algorithms, reviewed against the originals."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_dsu_support import DSU
from nowcoder_sudoku_support import SUDOKU


def run():
    existing = read(CONTENT / 'reviewed.json')
    def put(n, *args, **kwargs):
        if f'nowcoder-global::{n}' not in existing:
            add(n, *args, **kwargs)
    put(24911, 1600, ['深度优先搜索', '位运算', '搜索剪枝'], '解唯一解的9×9数独，空位用0表示。',
        '分别用9位二进制记录每行、每列、每宫已经用过的数字。空格的候选等于全集去掉三个位集的并。每次选择候选最少的空格，依次尝试候选，递归后撤销；某格没有候选立刻回退。所有格填满即得到唯一解。选择最少候选不改变搜索范围，但能尽早发现矛盾。',
        r'''Sudoku solver; solver.first = true; for (int &x : solver.board) cin >> x; solver.solve(); for (int r = 0; r < 9; r++) for (int c = 0; c < 9; c++) cout << solver.board[r * 9 + c] << (c == 8 ? '\n' : ' ');''',
        '试填和撤销必须成对更新行、列、宫。行尾不加空格；每行输出九个数字。', declarations=SUDOKU,
        complexity=r'若有 $E$ 个空格，保守上界 $O(81\cdot9^E)$，剪枝后通常远小于此；固定81格，搜索栈 $O(E)$。')
    put(16612, 2200, ['深度优先搜索', '搜索剪枝', '数独'], '满足数独约束的所有填法中，最大化数字乘靶形格子权值的总和。',
        '用行、列、宫位集求候选，每次选候选最少的空格搜索。格子权值为6+min(行号,列号,8−行号,8−列号)，中心恰为10。所有格填满时更新最大总分，不能找到首个解就退出。优先尝试大数字便于较早找到高分。\n\n对当前每个空格，取其候选中最大数字乘该格权值，加到已确定得分，得到乐观上界。忽略空格之间的冲突只会高估，若这个上界仍不超过已知最好分数，就可剪枝。无候选也立即剪枝。',
        r'''Sudoku solver; for (int &x : solver.board) cin >> x; solver.solve(); cout << solver.best;''',
        '给定数字同样计分。不同解可能得分不同，必须搜索全部未被合法上界剪掉的分支；无解输出−1。', declarations=SUDOKU,
        complexity=r'空格数 $E\le57$，保守时间上界 $O(81\cdot9^E)$，实际依赖约束传播和上界剪枝；栈空间 $O(E)$。')
    put(51032, 1800, ['广度优先搜索', '状态压缩', '路径恢复'], '三乘三滑块，把x与四邻格交换，输出到标准排列的移动串或unsolvable。',
        '每个九字符排列是一个状态，交换一次是边。BFS按步数递增访问，记录每个新状态的父状态编号和到达它的移动字符，到目标后沿父链倒序恢复。最多9!种状态，全部存储足够。若可达状态遍历完仍无目标，则无解。相同状态只入队一次，避免在滑块来回交换中循环。',
        r'''string start; char c; while (cin >> c) start += c; const string target = "12345678x"; vector<string> states{start}; vector<int> parent{-1}; vector<char> move{'?'}; unordered_map<string,int> id; id.reserve(200000); id[start] = 0; int found = -1; int dr[] = {-1,1,0,0}, dc[] = {0,0,-1,1}; string names = "udlr";
        for (size_t h = 0; h < states.size(); h++) { string current = states[h]; if (current == target) { found = h; break; } int p = current.find('x'), r = p / 3, col = p % 3; for (int d = 0; d < 4; d++) { int rr = r + dr[d], cc = col + dc[d]; if (rr < 0 || rr >= 3 || cc < 0 || cc >= 3) continue; string next = current; swap(next[p],next[rr * 3 + cc]); if (!id.count(next)) { int index = states.size(); id[next] = index; states.push_back(next); parent.push_back(h); move.push_back(names[d]); } } } if (found == -1) cout << "unsolvable"; else { string answer; for (int u = found; parent[u] != -1; u = parent[u]) answer += move[u]; reverse(answer.begin(),answer.end()); cout << answer; }''',
        '字符表示空格x的移动方向。样例可能给出另一条合法路径，本地校验会逐步执行整条输出并检查最终排列。', complexity=r'记状态数 $S\le9!$，每状态最多四条边、字符串长9，期望时间 $O(9S)$，空间 $O(9S)$。',
        checker='eight-puzzle-path', cases=[{'input':'1 2 3 4 5 6 8 7 x','output':'unsolvable'},{'input':'1 2 3 4 5 6 7 8 x','output':''}])
    put(16742, 2100, ['双向搜索', '广度优先搜索', '字符串'], '按给定子串替换规则，求A到B不超过10步的最少变换数。',
        '任何长度至多10的变换路径，都有一个中间串，距A和B各不超过5步。分别从A按正规则、从B按反规则做深度最多5的BFS，每次枚举每条规则在当前串中的所有出现位置，包括重叠位置。将两边所有共同状态的距离和取最小，即得到完整的10步内最短距离。没有交点就输出NO ANSWER!。边必须按方向反转，不能仅交换搜索起点。',
        r'''string a, b; cin >> a >> b; vector<pair<string,string>> rules; string from, to; while (cin >> from >> to) rules.push_back({from,to}); auto search = [&](const string &start, bool backward) { unordered_map<string,int> distance; vector<string> queue{start}; distance[start] = 0; for (size_t h = 0; h < queue.size(); h++) { string current = queue[h]; int depth = distance.at(current); if (depth == 5) continue; for (const auto &rule : rules) { const string &x = backward ? rule.second : rule.first, &y = backward ? rule.first : rule.second; for (size_t p = current.find(x); p != string::npos; p = current.find(x,p + 1)) { string next = current.substr(0,p) + y + current.substr(p + x.size()); if (!distance.count(next)) { distance[next] = depth + 1; queue.push_back(next); } } } } return distance; }; auto left = search(a,false), right = search(b,true); int answer = 11; for (auto &[s,d] : left) { auto it = right.find(s); if (it != right.end()) answer = min(answer,d + it->second); } if (answer <= 10) cout << answer; else cout << "NO ANSWER!";''',
        '不能人为把中间串长度截在输入长度20，变换过程中可以暂时增长。A等于B时答案0。', complexity=r'若两侧各生成 $S$ 个状态、最大中间长度 $L$、规则数 $R\le6$，保守时间 $O(SRL^2)$，空间 $O(SL)$；搜索层数各不超过5。')
    put(251580, 1900, ['01BFS', '最短路'], '顺当前格的洋流方向移动耗能0，其他七方向耗能1，多次求最少能量。',
        '八邻接边权只有0或1，使用01BFS：松弛0边放队首，1边放队尾，队列按待确定距离保持非递减。每个点首次出队时确定最短距离，之后重复记录跳过，目标确定后即可停止。为配合原题满数据时限，用数组实现循环双端队列，避免通用堆的对数因子和频繁节点分配。每条边至多成功入队一次的上界为8V，加初始结点后队列容量8V+2足够。',
        r'''int n, m; while (cin >> n >> m) { vector<string> grid(n); for (auto &row : grid) cin >> row; int queries; cin >> queries; int size = n * m, capacity = 8 * size + 2; vector<int> queue(capacity), distance(size); vector<unsigned char> done(size); int dr[] = {-1,-1,0,1,1,1,0,-1}, dc[] = {0,1,1,1,0,-1,-1,-1}; while (queries--) { int a,b,c,d; cin >> a >> b >> c >> d; int start = (a - 1) * m + b - 1, target = (c - 1) * m + d - 1; fill(distance.begin(),distance.end(),1000000000); fill(done.begin(),done.end(),0); int head = 0, tail = 1; queue[0] = start; distance[start] = 0;
        while (head != tail) { int u = queue[head]; if (++head == capacity) head = 0; if (done[u]) continue; done[u] = 1; if (u == target) break; int r = u / m, col = u % m, direction = grid[r][col] - '0'; for (int k = 0; k < 8; k++) { int rr = r + dr[k], cc = col + dc[k]; if (rr < 0 || rr >= n || cc < 0 || cc >= m) continue; int v = rr * m + cc, w = k != direction; if (!done[v] && distance[v] > distance[u] + w) { distance[v] = distance[u] + w; if (w == 0) { if (--head < 0) head = capacity - 1; queue[head] = v; } else { queue[tail] = v; if (++tail == capacity) tail = 0; } } } } cout << distance[target] << '\n'; } }''',
        '边权由出发格的方向决定。输入坐标从1开始；0号方向是北，之后顺时针。起终点相同耗能0。', complexity=r'每次询问时间、空间均为 $O(nm)$，方向数8为常数。')
    put(20566, 1900, ['并查集', '图匹配', '贪心'], '每件装备有两个可选属性，只能用一次，求能连续覆盖从1开始的多少种属性。',
        '把属性值看成点，每件装备是一条连接两个属性的边，选某属性相当于把一条未用边分配给端点。一个连通块若有环，可以沿环循环分配，树枝各分配父边，因此所有点都能覆盖；若无环，则是树，边数比点数少一，至多覆盖少一个点。反之只要指定某个不覆盖的点为根，其他点各用父边，就能全部覆盖。\n\n因此一个树形连通块中不能把所有属性都包含在目标前缀里；它最大的属性编号必须留在前缀之外，故答案至多该块最大编号减一。所有树块取这个界的最小值，带环块不限制。用并查集维护块大小、最大编号、装备边数即可，孤立属性同样是零边树，会自然截断缺失编号。',
        r'''const int values = 10000; int n; cin >> n; DSU dsu(values); vector<int> edgeCount(values + 1), maximum(values + 1); iota(maximum.begin(),maximum.end(),0); while (n--) { int a, b; cin >> a >> b; a = dsu.find(a); b = dsu.find(b); if (a == b) edgeCount[a]++; else { if (dsu.size[a] < dsu.size[b]) swap(a,b); dsu.parent[b] = a; dsu.size[a] += dsu.size[b]; edgeCount[a] += edgeCount[b] + 1; maximum[a] = max(maximum[a],maximum[b]); } } int answer = values; for (int v = 1; v <= values; v++) if (dsu.find(v) == v && edgeCount[v] < dsu.size[v]) answer = min(answer,maximum[v] - 1); cout << answer;''',
        '同一属性对出现多次是多条独立装备边，可以形成环。两个属性相同形成自环，也能覆盖该属性。', declarations=DSU, complexity=r'属性上限 $A=10000$，时间 $O((n+A)\alpha(A))$，空间 $O(A)$。')
    put(19910, 1900, ['深度优先搜索', '平面图', '计数'], '沿格线把矩形分成两个均连通、均接触原边界的非空部分，求不区分两部分的方案数。',
        '两部分都连通且都碰外边界时，它们之间的分界线必须是一条从外边界到外边界、不自交的简单格线路径。闭环会把一块包在内部；多条分界弧会让某一块分裂。因此可枚举这条线：两个端点在边界非角点，中间仅经过内部格点，每个内部格点至多一次。每条这样的弧恰好分出两块合法区域。\n\n把内部格点建四邻接图。boundary[u]记录它有几个外边界邻点，作为进入或离开端点的选择数。枚举起始内部点，DFS不重复内部点，随时按boundary[当前]计结束方案。起点未走时要排除“从同一端点进出”，贡献为b*(b−1)。最终除二去掉路径的两个方向。左右、上下反射对称的起点只算一个，再乘轨道大小，减少重复搜索。若一边宽度为1，只有逐条直线切割，答案a*b−1。',
        r'''int a, b; cin >> a >> b; if (a == 1 || b == 1) { cout << a * b - 1; return 0; } int rows = a - 1, cols = b - 1, n = rows * cols; vector<unsigned long long> adjacent(n); vector<int> boundary(n); for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) { int u = r * cols + c; boundary[u] = (r == 0) + (r + 1 == rows) + (c == 0) + (c + 1 == cols); if (r) adjacent[u] |= 1ULL << (u - cols); if (r + 1 < rows) adjacent[u] |= 1ULL << (u + cols); if (c) adjacent[u] |= 1ULL << (u - 1); if (c + 1 < cols) adjacent[u] |= 1ULL << (u + 1); }
        auto dfs = [&](auto &&self, int u, unsigned long long used) -> long long { long long count = boundary[u]; unsigned long long next = adjacent[u] & ~used; while (next) { int v = __builtin_ctzll(next); next &= next - 1; count += self(self,v,used | (1ULL << v)); } return count; }; long long oriented = 0; for (int r = 0; r <= (rows - 1) / 2; r++) for (int c = 0; c <= (cols - 1) / 2; c++) { int u = r * cols + c; if (!boundary[u]) continue; int symmetry = (r == rows - 1 - r ? 1 : 2) * (c == cols - 1 - c ? 1 : 2); oriented += symmetry * boundary[u] * (dfs(dfs,u,1ULL << u) - 1); } cout << oriented / 2;''',
        '枚举的是格线交点，不是单元格染色。边界只能作为首尾，不能沿外边界继续走；路径方向不构成不同划分。', complexity=r'内部格点数 $V=(a-1)(b-1)\le30$，时间为简单路径枚举的指数级，可界为 $O(V3^V)$，栈及图空间 $O(V)$。',
        cases=[{'input':'1 7','output':'6'},{'input':'2 2','output':'6'}])
    put(16665, 2200, ['深度优先搜索', '搜索剪枝', '进位'], 'N进制的三个N位字母数满足加法，数字与字母一一对应，允许前导零，求唯一映射。',
        '从最低位开始处理，已知这一位的输入进位。先给两个加数字母中尚未赋值者尝试未用数字，再由(a+b+carry)%N强制确定结果字母；输出进位为整除N。若结果字母已赋值就校验，否则必须占用一个尚未使用的数字。每列完成后递归下一列，最高列之后要求进位为0。\n\n额外检查所有三个字母都已赋值的列：即使它们还未按顺序处理，输入进位也只可能是0或1，因此结果必须等于这两种余数之一。最高列两个加数已知且和≥N时必定溢出，也可立即剪枝。',
        r'''int n; string a,b,c; cin >> n >> a >> b >> c; array<int,26> value; value.fill(-1); vector<bool> used(n); auto possible = [&]() { for (int p = 0; p < n; p++) { int x = value[a[p] - 'A'], y = value[b[p] - 'A'], z = value[c[p] - 'A']; if (p == 0 && x != -1 && y != -1 && x + y >= n) return false; if (x != -1 && y != -1 && z != -1 && (x + y) % n != z && (x + y + 1) % n != z) return false; } return true; };
        auto dfs = [&](auto &&self, int p, int carry) -> bool { if (p < 0) return carry == 0; int letters[2] = {a[p] - 'A',b[p] - 'A'}, result = c[p] - 'A'; auto assign = [&](auto &&fill, int at) -> bool { if (at == 2) { int sum = value[letters[0]] + value[letters[1]] + carry, digit = sum % n; if (value[result] != -1) return value[result] == digit && self(self,p - 1,sum / n); if (used[digit]) return false; value[result] = digit; used[digit] = true; if (possible() && self(self,p - 1,sum / n)) return true; used[digit] = false; value[result] = -1; return false; } int letter = letters[at]; if (value[letter] != -1) return fill(fill,at + 1); for (int digit = n - 1; digit >= 0; digit--) if (!used[digit]) { value[letter] = digit; used[digit] = true; if (possible() && fill(fill,at + 1)) return true; used[digit] = false; value[letter] = -1; } return false; }; return assign(assign,0); }; dfs(dfs,n - 1,0); for (int i = 0; i < n; i++) cout << value[i] << (i + 1 == n ? '\n' : ' ');''',
        '允许前导零。最高位不能再产生额外进位；相同字母在同列出现多次时只能赋同一个数字。', complexity=r'最坏为排列搜索，粗略上界 $O(N^2N!)$，各列强制赋值和一致性检查大幅剪枝；空间 $O(N)$。')


if __name__ == '__main__':
    run()
