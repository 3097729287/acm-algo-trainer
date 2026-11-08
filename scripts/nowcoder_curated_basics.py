"""Original curated-list entries, including their exact I/O differences."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_dsu_support import DSU


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    for target,source,reason in [
        (16589,285873,'完整核对FIFO缓存，M≤100、N≤1000、命中不刷新顺序，样例和原题一致。'),
        (235817,251580,'核对洋流0至7方向、起终坐标、50次查询和1000×1000范围，与Ocean Currents相同。'),
        (235611,251572,'核对攻防同时结算、Case编号输出、总n+m界及样例，与Defeat the Enemy相同。'),
        (235953,210734,'核对恰好m个非空不相交子段，输入格式相同；n提高至百万而m降为20，O(nm)滚动仍适用。'),
        (236173,232853,'核对30001岛、首次跳d、之后跳长差至多1、同位置多宝藏和两组样例。'),
        (235543,232854,'核对双向无限使用魔法、费用最小、n≤300与gcd达到1的同一目标。')]:
        if f'nowcoder-global::{target}' not in existing: reviewed_clone(target,source,reason)
    put(207053,1700,['扫描线','整数区间'],'猜数回复可能错误，找最多同时正确的回复数。',
        '将每条回复变为目标整数的可行区间：“+”是目标≤v−1，“−”是目标≥v+1，“.”是目标=v。扫描目标值时，所有“+”先计入初始覆盖；在v处将它减1。“−”在v+1处加1；“.”在v处加1、v+1处减1。用有序map合并同坐标事件，扫描取最大覆盖数。',
        r'''int n; cin >> n; map<long long,int> event; int current=0; while (n--) { long long v; char op; cin >> v >> op; if (op=='+') { current++; event[v]--; } else if (op=='-') event[v+1]++; else { event[v]++; event[v+1]--; } } int answer=current; for (auto [position,delta]:event) { current+=delta; answer=max(answer,current); } cout << answer;''',
        '比较是严格不等，整数目标需使用v−1或v+1边界。同坐标事件先合并再计最大，避免制造不存在的区间。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(235250,1900,['状态枚举','翻灯'],'n×m翻灯变全黑或全白，最少按键数，m≤10。',
        '枚举目标颜色和第一行按键。第一行按法确定后，为消掉上一行残留，第i行按键被唯一确定。每行用m位掩码，按键p对本行的影响是p xor(p<<1) xor(p>>1)，再加上下行同列影响。依次强制推出所有行，检查最后一行是否清空，累计popcount取最少。',
        r'''int n,m; cin >> n >> m; int full=(1<<m)-1; vector<int> original(n); for (int i=0;i<n;i++) for (int j=0;j<m;j++) { char c; cin >> c; original[i]|=(c-'0')<<j; } int answer=INT_MAX; for (int target=0;target<2;target++) { vector<int> a=original; if (target) for (int &x:a) x^=full; for (int first=0;first<=full;first++) { vector<int> press(n); press[0]=first; for (int i=1;i<n;i++) press[i]=(a[i-1]^press[i-1]^(press[i-1]<<1)^(press[i-1]>>1)^(i>=2?press[i-2]:0))&full; int last=(a[n-1]^press[n-1]^(press[n-1]<<1)^(press[n-1]>>1)^(n>=2?press[n-2]:0))&full; if (!last) { int count=0; for (int p:press) count+=__builtin_popcount((unsigned)p); answer=min(answer,count); } } } if (answer==INT_MAX) cout << "Impossible"; else cout << answer;''',
        '必须同时考虑全黑和全白。每行位移后用full截掉棋盘外位。',
        complexity=r'时间 $O(2^m n+nm)$，空间 $O(n)$。')
    put(200190,1900,['枚举子集','贪心'],'矩阵k次选择行或列清零，最大得分。',
        '所有权值为正，重复清零不会再加分，结果只由选中的行、列集合决定。枚举行子集，先取得这些行全部权值；每列只计算未被选中行的剩余和，再选最大的k−行数列。k≥min(n,m)可直接清空所有行或所有列，答案为全矩阵和。',
        r'''int n,m,k; cin >> n >> m >> k; vector<vector<long long>> a(n,vector<long long>(m)); long long total=0; for (auto &row:a) for (auto &x:row) { cin >> x; total+=x; } if (k>=min(n,m)) { cout << total; return 0; } long long answer=0; for (int mask=0;mask<(1<<n);mask++) { int rows=__builtin_popcount((unsigned)mask); if (rows>k) continue; vector<long long> column(m); long long score=0; for (int i=0;i<n;i++) for (int j=0;j<m;j++) { if (mask>>i&1) score+=a[i][j]; else column[j]+=a[i][j]; } sort(column.rbegin(),column.rend()); for (int j=0;j<k-rows && j<m;j++) score+=column[j]; answer=max(answer,score); } cout << answer;''',
        '行列交点只计一次，选列时必须用删去所选行后的剩余列和。多余回合可重复清零，不会降低分数。',
        complexity=r'时间 $O(2^n(nm+m\log m))$，空间 $O(nm)$。')
    put(235558,1100,['二分查找'],'有序数组，多次统计数值位于[x,y]的元素数。',
        'lower_bound(x)定位第一个≥x的位置，upper_bound(y)定位第一个>y的位置，两者相减恰好是闭区间内元素数。数组已保证非递减，重复元素全部保留。',
        r'''int n; cin >> n; vector<long long> a(n); for (auto &x:a) cin >> x; int q; cin >> q; while (q--) { long long x,y; cin >> x >> y; cout << upper_bound(a.begin(),a.end(),y)-lower_bound(a.begin(),a.end(),x) << '\n'; }''',
        '右端用upper_bound，不要只查到第一个等于y的元素。',
        complexity=r'时间 $O(n+q\log n)$，空间 $O(n)$。')
    put(235254,1700,['二分答案'],'自然每分钟干1，单台烘干器每分钟使一件干k，求全部干的最短时间。',
        '若总时间T，每件自然干T，剩余max(0,a[i]−T)必须由烘干器的额外k−1效率补足，所需烘干分钟ceil(剩余/(k−1))。所有所需分钟之和≤T即能排入单台机器。可行性单调，二分0..max(a)。k=1时机器没有额外效果，直接取最大水量。',
        r'''int n; cin >> n; vector<long long> a(n); long long high=0; for (auto &x:a) { cin >> x; high=max(high,x); } long long k; cin >> k; if (k==1) { cout << high; return 0; } auto feasible=[&](long long time) { long long needed=0; for (long long x:a) if (x>time) { needed+=(x-time+k-2)/(k-1); if (needed>time) return false; } return true; }; long long low=0; while (low<high) { long long mid=(low+high)/2; if (feasible(mid)) high=mid; else low=mid+1; } cout << low;''',
        '烘干时总下降k，不是自然1再额外k，所以额外效率为k−1。',
        complexity=r'时间 $O(n\log\max a)$，空间 $O(n)$。')
    put(235260,1500,['折半枚举','二分计数'],'四组各选一个数，统计和为0的方案数。',
        '枚举前两组的n²个和并排序。再枚举后两组和s，用equal_range统计前表中−s的出现次数，累加即可。各行只是输入四组数据，不限制选取数字来自同一行。',
        r'''int n; cin >> n; vector<long long> a(n),b(n),c(n),d(n); for (int i=0;i<n;i++) cin >> a[i] >> b[i] >> c[i] >> d[i]; vector<long long> sum; sum.reserve(n*n); for (auto x:a) for (auto y:b) sum.push_back(x+y); sort(sum.begin(),sum.end()); long long answer=0; for (auto x:c) for (auto y:d) { auto range=equal_range(sum.begin(),sum.end(),-x-y); answer+=range.second-range.first; } cout << answer;''',
        '相同数值在不同下标属于不同选择，所以保留重复和。答案最多n⁴，使用64位。',
        complexity=r'时间 $O(n^2\log n)$，空间 $O(n^2)$。')
    put(235267,1700,['映射','离线分组','删除标记'],'横线或竖线轰炸，统计每次新摧毁的基地数。',
        '分别按x、y把基地编号分组。攻击某条线时遍历该组，未摧毁者计数并标记；处理后清空该组。同一基地最多在x组和y组各访问一次，总遍历量O(n)，重复轰炸空组不再扫描。',
        r'''int n,m; cin >> n >> m; map<long long,vector<int>> byX,byY; for (int i=0;i<n;i++) { long long x,y; cin >> x >> y; byX[x].push_back(i); byY[y].push_back(i); } vector<bool> destroyed(n); while (m--) { int c; long long d; cin >> c >> d; auto &groups=c==0?byX:byY; auto it=groups.find(d); int answer=0; if (it!=groups.end()) { for (int id:it->second) if (!destroyed[id]) { destroyed[id]=true; answer++; } groups.erase(it); } cout << answer << '\n'; }''',
        '已经被另一方向攻击摧毁的基地不会再计数。删除整组后总扫描量才有线性界。',
        complexity=r'时间 $O((n+m)\log n)$，空间 $O(n)$。')
    put(235294,2000,['贪心','二维匹配'],'机器时间等级都不低于任务要求，最大任务数并最大报酬。',
        '任务按所需时间从大到小、同时间按等级从大到小处理；机器按可用时间降序。处理任务时，把时间足够的未用机器加入等级频数表，选择等级≥要求的最小等级机器。这样给当前任务留够能力，又保留高等级机器。时间每增1带来的500收益大于等级全部范围差的20收益，因此降序任务也对应优先较高报酬。\n\n交换论证：可行分配若使用更强等级机器完成当前任务，可与贪心的较弱机器交换；若当前任务原本没被选，换掉其占用机器上的后续任务，任务数不减、报酬不降。',
        r'''int n,m; cin >> n >> m; vector<pair<int,int>> machine(n),task(m); for (auto &[x,y]:machine) cin >> x >> y; for (auto &[x,y]:task) cin >> x >> y; sort(machine.rbegin(),machine.rend()); sort(task.rbegin(),task.rend()); array<int,11> count={}; int p=0,completed=0; long long reward=0; for (auto [time,level]:task) { while (p<n && machine[p].first>=time) count[machine[p++].second]++; for (int y=level;y<=10;y++) if (count[y]) { count[y]--; completed++; reward+=500LL*time+2*level; break; } } cout << completed << ' ' << reward;''',
        '每台机器至多一项任务；同所需时间时先安排等级高、收益也高的任务。',
        complexity=r'时间 $O(n\log n+m\log m+11m)$，空间 $O(n+m)$。')
    put(235622,1800,['带权并查集'],'整列积木放到另一列顶，查询某块下方积木数。',
        '并查集根表示整列最底部，size[root]记录列高，distance[x]记录x到父节点下方偏移。把x列根rx接到y列根ry时，distance[rx]=size[ry]，再增大ry列高。路径压缩时把原父节点到底部的距离加上，最终distance[x]就是下方块数。',
        r'''const int limit=30000; vector<int> parent(limit+1),size(limit+1,1),distance(limit+1); iota(parent.begin(),parent.end(),0); auto find=[&](int x) { vector<int> path; int root=x; while (parent[root]!=root) { path.push_back(root); root=parent[root]; } int accumulated=0; for (int i=(int)path.size()-1;i>=0;i--) { int u=path[i]; accumulated+=distance[u]; parent[u]=root; distance[u]=accumulated; } return root; }; int q; cin >> q; while (q--) { char op; int x; cin >> op >> x; if (op=='M') { int y; cin >> y; int rx=find(x),ry=find(y); parent[rx]=ry; distance[rx]=size[ry]; size[ry]+=size[rx]; } else { find(x); cout << distance[x] << '\n'; } }''',
        '移动的是整列，不只是x上方部分。题目不输入n，按最大编号30000初始化。',
        complexity=r'路径压缩总计近线性，单次保守上界 $O(n)$；空间 $O(n)$，无递归压缩。')
    put(235745,1900,['离线逆序','并查集'],'动态删边并查询所在连通块最大繁荣度。',
        '读完全部操作，先用从未被删除的边建最终图。逆序处理，原删除变成加边，原查询则直接查当前并查集根的最大繁荣度。合并时同步取块最大值。逆序得到的查询答案最后反转输出。',
        r'''int n,m; cin >> n >> m; vector<int> value(n); for (int &x:value) cin >> x; vector<pair<int,int>> edge(m); map<pair<int,int>,int> index; for (int i=0;i<m;i++) { int u,v; cin >> u >> v; u--;v--;if(u>v)swap(u,v);edge[i]={u,v};index[edge[i]]=i; } int q; cin >> q; struct Operation { char type; int x,y; }; vector<Operation> operation(q); vector<bool> removed(m); for (auto &op:operation) { cin >> op.type >> op.x; op.x--; op.y=-1; if (op.type=='D') { cin >> op.y; op.y--; if (op.x>op.y) swap(op.x,op.y); removed[index[{op.x,op.y}]]=true; } } DSU dsu(n); auto unite=[&](int u,int v) { int a=dsu.find(u),b=dsu.find(v),maximum=max(value[a],value[b]); dsu.unite(a,b); value[dsu.find(a)]=maximum; }; for (int i=0;i<m;i++) if (!removed[i]) unite(edge[i].first,edge[i].second); vector<int> answer; for (int i=q-1;i>=0;i--) { auto op=operation[i]; if (op.type=='D') unite(op.x,op.y); else answer.push_back(value[dsu.find(op.x)]); } reverse(answer.begin(),answer.end()); for (int x:answer) cout << x << '\n';''',
        '无向边统一较小端在前，避免删除时找不到反向输入的边。查询答案要恢复原时间顺序。',
        declarations=DSU,complexity=r'时间 $O((n+m+q)\log n)$，空间 $O(n+m+q)$。')
    put(235813,1500,['回溯','位运算'],'n≤12的N皇后方案数。',
        '逐行放皇后，用三个位掩码记录已占列、两类对角线在当前行的攻击位置。当前可放列available=full & ~(columns|left|right)，依次取最低位放置。进入下一行时左右对角线分别左移、右移；放满n行计一种。',
        r'''int n; cin >> n; unsigned full=(1U<<n)-1; long long answer=0; auto dfs=[&](auto &&self,unsigned columns,unsigned left,unsigned right)->void { if (columns==full) { answer++; return; } unsigned available=full&~(columns|left|right); while (available) { unsigned bit=available&-available; available-=bit; self(self,columns|bit,(left|bit)<<1,(right|bit)>>1); } }; dfs(dfs,0,0,0); cout << answer;''',
        '每行恰放一个，列掩码满了就完成。越界对角线位由full在下次候选计算时屏蔽。',
        complexity=r'保守时间 $O(n!)$，递归空间 $O(n)$。')
    put(235814,1400,['动态规划','有向无环图'],'马只允许四种x增大的日字移动，求角到角路径数。',
        '四种允许移动都使横坐标x严格增加，因此按列从1到m计算是拓扑顺序。dp[x][y]为到此的路径数，将它加到四种不越界的下一位置。dp[1][1]=1，最后取dp[m][n]，即第m列第n行。',
        r'''int rows,columns; cin >> rows >> columns; long long dp[16][16]={}; dp[1][1]=1; const int dx[]={1,1,2,2},dy[]={2,-2,1,-1}; for (int x=1;x<=columns;x++) for (int y=1;y<=rows;y++) for (int d=0;d<4;d++) { int xx=x+dx[d],yy=y+dy[d]; if (xx<=columns && yy>=1 && yy<=rows) dp[xx][yy]+=dp[x][y]; } cout << dp[columns][rows];''',
        '原题坐标终点文字与“n行m列、不能向左”及样例不一致。按行列含义，横坐标x取1..m，纵坐标y取1..n，目标为(m,n)；样例4行5列仅有一条向右路线。只用列出的四种移动。1×1有一条空路径。',
        complexity=r'时间、空间均 $O(nm)$。')
    put(235247,1700,['余数BFS','最小字典序'],'只用0..K−1数字组成能被M整除的最小正整数。',
        '按位追加数字时只需记录当前余数，转移为(10*r+d)%M。BFS按长度递增，并按数字升序扩展，就先得到最短、同长度字典序最小的数字。首位只枚举1..K−1，避免0这个无意义答案。每个余数只访问一次，保存父余数与末位，首次找到余数0后沿父链还原。',
        r'''int k,m; cin >> k >> m; vector<int> parent(m,-2),digit(m); queue<int> queue; for (int d=1;d<k;d++) { int r=d%m; if (parent[r]==-2) { parent[r]=-1; digit[r]=d; queue.push(r); } } while (parent[0]==-2 && !queue.empty()) { int r=queue.front(); queue.pop(); for (int d=0;d<k;d++) { int next=(r*10+d)%m; if (parent[next]==-2) { parent[next]=r; digit[next]=d; queue.push(next); } } } string answer; for (int r=0;r!=-1;r=parent[r]) answer.push_back('0'+digit[r]); reverse(answer.begin(),answer.end()); cout << answer;''',
        'K是允许数码的上界，不是数制，构造的仍是十进制数。不能用普通整数保存可能很长的答案。',
        complexity=r'时间 $O(KM)$，空间 $O(M)$。')
    put(235911,1000,['递推'],'n阶楼梯，每次1或2阶，求方案数。',
        '按最后一步拆分，f[n]=f[n−1]+f[n−2]，f[0]=1、f[1]=1。从2滚动计算，n≤50需64位。',
        r'''int n; cin >> n; long long previous=1,current=1; for (int i=2;i<=n;i++) { long long next=previous+current; previous=current; current=next; } cout << current;''',
        '空台阶有一种“已经完成”的方式，设f[0]=1才能正确得到f[2]=2。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(235954,1600,['有向无环图','动态规划'],'严格下降的四邻路径最大长度。',
        '把格子按高度升序处理，dp[u]=1+max(dp[v])，v为更低的四邻格；没有更低格时为1。低格已先处理，依赖顺序正确，最后对全部起点取最大。这样避免递归路径很长时的栈问题。',
        r'''int n,m; cin >> n >> m; vector<int> height(n*m),order(n*m),dp(n*m,1); for (int &x:height) cin >> x; iota(order.begin(),order.end(),0); sort(order.begin(),order.end(),[&](int a,int b) { return height[a]<height[b]; }); int answer=1; const int dr[]={-1,1,0,0},dc[]={0,0,-1,1}; for (int u:order) { int r=u/m,c=u%m; for (int d=0;d<4;d++) { int rr=r+dr[d],cc=c+dc[d]; if (rr>=0 && rr<n && cc>=0 && cc<m && height[rr*m+cc]<height[u]) dp[u]=max(dp[u],dp[rr*m+cc]+1); } answer=max(answer,dp[u]); } cout << answer;''',
        '相等高度不能滑动。路径长度按经过格子数，单格为1。',
        complexity=r'格子数V=nm，时间 $O(V\log V)$，空间 $O(V)$。')
    put(235948,1200,['最大子段和'],'求最大非空连续子数组和。',
        '维护end为恰以当前元素x结尾的最大子段和，更新end=max(x,end+x)，再更新全局最大值。初始用第一个元素，保证全负数组仍选出最大的单个负数。',
        r'''int n; cin >> n; long long ending=0,answer=LLONG_MIN; for (int i=0;i<n;i++) { long long x; cin >> x; ending=i?max(x,ending+x):x; answer=max(answer,ending); } cout << answer;''',
        '至少选一个，不能用0作为最终答案下界。百万个十亿值相加需64位。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(235624,1500,['最长公共子序列'],'多组两个字符串，求LCS长度。',
        'f[i][j]表示前i、j字符的LCS长度。末字符相等时可由f[i−1][j−1]+1转移，否则从跳过其中一个末字符的两个状态取最大。仅依赖上一行和本行左方，滚动一维，另存被覆盖前的左上角值。',
        r'''string s,t; while (cin >> s >> t) { vector<int> dp(t.size()+1); for (char c:s) { int diagonal=0; for (int j=1;j<=(int)t.size();j++) { int old=dp[j]; if (c==t[j-1]) dp[j]=diagonal+1; else dp[j]=max(dp[j],dp[j-1]); diagonal=old; } } cout << dp.back() << '\n'; }''',
        '子序列不要求连续；输入直到EOF，每组重新初始化。',
        complexity=r'每组时间 $O(|s||t|)$，空间 $O(|t|)$。')
    put(235950,1500,['多重背包'],'每种有限个物品，容量至100，最大价值。',
        '按物品种类逐层转移。用旧dp副本保留不选，对每个旧容量和数量1..x枚举，不能超过总容量。只从旧数组转移，保证同一类最多取x件。',
        r'''int n,capacity; cin >> n >> capacity; vector<int> dp(capacity+1); while (n--) { int count,weight,value; cin >> count >> weight >> value; auto next=dp; for (int used=0;used<=capacity;used++) for (int k=1;k<=count && used+k*weight<=capacity;k++) next[used+k*weight]=max(next[used+k*weight],dp[used]+k*value); dp.swap(next); } cout << *max_element(dp.begin(),dp.end());''',
        '输入顺序是数量、重量、价值。容量不要求恰好用满。',
        complexity=r'时间 $O(nT\max x)$，空间 $O(T)$。')


if __name__ == '__main__': run()
