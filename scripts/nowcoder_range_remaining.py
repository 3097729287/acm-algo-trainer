"""Remaining BIT and sweep-line exercises."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_range_more import BIT
from nowcoder_sweep_support import COVER, AREA


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(51101,1600,['树状数组','逆序还原'],'已知每个位置前面更小编号数，恢复1到n的排列。',
        '从最后一个位置倒推。此时尚未分配的编号恰好属于当前及其前面，若前面有c个更小编号，当前编号就是剩余编号中的第c+1小。树状数组记录每个编号是否未使用，二进制提升查第k个1，找到后删除。第一个位置默认c=0。',
        r'''int n; cin >> n; vector<int> smaller(n+1),answer(n+1); for (int i=2;i<=n;i++) cin >> smaller[i]; Fenwick bit(n); for (int i=1;i<=n;i++) bit.add(i,1); for (int i=n;i>=1;i--) { int p=0,k=smaller[i]+1,step=1; while (step<=n/2) step<<=1; for (;step;step>>=1) if (p+step<=n && bit.tree[p+step]<k) { p+=step; k-=bit.tree[p]; } answer[i]=p+1; bit.add(p+1,-1); } for (int i=1;i<=n;i++) cout << answer[i] << '\n';''',
        '必须倒序恢复，正序时尚不清楚哪些更小编号会出现在后方。',
        declarations=BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(15172,1700,['二维树状数组'],'单点翻转灯泡，查询矩形亮灯数量。',
        '二维树状数组支持单点增量和左上前缀矩形和，矩形查询用四个前缀容斥。保存当前灯泡状态，0变1时加1，1变0时减1。初始化先把原矩阵写入bit，再依次沿两个维度向Fenwick父节点累加，可在线性于矩阵大小的时间建表。',
        r'''int n,m; cin >> n >> m; vector<vector<int>> state(n+1,vector<int>(n+1)),bit=state; for (int i=1;i<=n;i++) for (int j=1;j<=n;j++) { char c; cin >> c; state[i][j]=bit[i][j]=c-'0'; } for (int i=1;i<=n;i++) if (i+(i&-i)<=n) for (int j=1;j<=n;j++) bit[i+(i&-i)][j]+=bit[i][j]; for (int j=1;j<=n;j++) if (j+(j&-j)<=n) for (int i=1;i<=n;i++) bit[i][j+(j&-j)]+=bit[i][j]; auto sum=[&](int x,int y) { int result=0; for (int i=x;i;i-=i&-i) for (int j=y;j;j-=j&-j) result+=bit[i][j]; return result; }; while (m--) { int op,x,y; cin >> op >> x >> y; if (op==1) { int delta=state[x][y]?-1:1; state[x][y]^=1; for (int i=x;i<=n;i+=i&-i) for (int j=y;j<=n;j+=j&-j) bit[i][j]+=delta; } else { int xx,yy; cin >> xx >> yy; cout << sum(xx,yy)-sum(x-1,yy)-sum(xx,y-1)+sum(x-1,y-1) << '\n'; } }''',
        '原矩阵逐字符读0/1，可同时兼容有无空格的行。查询两个坐标分别是左上和右下。',
        complexity=r'构建 $O(n^2)$，每次操作 $O(\log^2 n)$，空间 $O(n^2)$。')
    put(19427,1700,['离线查询','树状数组'],'静态数组，询问[l,r]中≤x的元素数。',
        '将数组元素按值升序，询问按阈值x升序。处理一个询问前，把所有值≤x的元素在其原下标上加1。此时树状数组的区间计数就是答案。询问保留编号，最后按原顺序输出。',
        r'''int n,m; cin >> n >> m; vector<pair<int,int>> a(n); for (int i=0;i<n;i++) { cin >> a[i].first; a[i].second=i+1; } vector<array<int,4>> query(m); for (int i=0;i<m;i++) { int l,r,x; cin >> l >> r >> x; query[i]={x,l,r,i}; } sort(a.begin(),a.end()); sort(query.begin(),query.end()); Fenwick bit(n); vector<int> answer(m); int p=0; for (auto [x,l,r,id] : query) { while (p<n && a[p].first<=x) { bit.add(a[p].second,1); p++; } answer[id]=bit.sum(r)-bit.sum(l-1); } for (int x : answer) cout << x << '\n';''',
        '阈值相等的数组元素要先全部插入，条件是≤而非<。离线排序不能改变输出顺序。',
        declarations=BIT,complexity=r'时间 $O((n+m)\log(n+m))$，空间 $O(n+m)$。')
    put(54585,1900,['树状数组','计数DP'],'统计长度K的严格递增下标子序列，n至五十万。',
        '设dp[len][i]为以第i项结尾、长len的严格递增子序列数，转移是所有之前值小于a[i]的dp[len−1]之和。值离散化，对每个长度维护一棵树状数组，查询rank−1前缀并把结果加到当前rank。长度倒序更新，最后插入长1的一种方案。长度K的总数单独累加。',
        r'''int n,k; cin >> n >> k; vector<int> a(n),coordinate; for (int &x : a) cin >> x; coordinate=a; sort(coordinate.begin(),coordinate.end()); coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end()); int size=coordinate.size(); constexpr int mod=998244353; vector<vector<int>> bit(k+1,vector<int>(size+1)); auto addValue=[&](int len,int p,int value) { for (;p<=size;p+=p&-p) { bit[len][p]+=value; if (bit[len][p]>=mod) bit[len][p]-=mod; } }; auto prefix=[&](int len,int p) { int result=0; for (;p;p-=p&-p) { result+=bit[len][p]; if (result>=mod) result-=mod; } return result; }; int answer=0; for (int x : a) { int rank=lower_bound(coordinate.begin(),coordinate.end(),x)-coordinate.begin()+1; for (int len=k;len>=2;len--) { int value=prefix(len-1,rank-1); addValue(len,rank,value); if (len==k) { answer+=value; if (answer>=mod) answer-=mod; } } addValue(1,rank,1); } cout << answer;''',
        '相同值不能接在一起，查询到rank−1。相同数值但不同下标的选择属于不同子序列。',
        complexity=r'时间 $O(nK\log n)$，空间 $O(nK)$。')
    put(25078,1800,['扫描线','有序多重集'],'求多个地面矩形楼房轮廓覆盖面积。',
        '把每座楼的左右端点变为加入/删除高度事件，按x排序。两事件x之间最高楼高不变，面积增加宽度乘当前最高高度。multiset保存全部在场楼高，加入0作为地面哨兵；删除仅删一份。相同x的事件之间宽度为0，不影响面积。',
        r'''int n; cin >> n; vector<array<long long,3>> event; for (int i=0;i<n;i++) { long long a,b,h; cin >> a >> b >> h; event.push_back({a,h,1}); event.push_back({b,h,-1}); } sort(event.begin(),event.end()); multiset<long long> height={0}; long long previous=event[0][0],area=0; for (auto [x,h,delta] : event) { area+=(x-previous)* *height.rbegin(); previous=x; if (delta==1) height.insert(h); else height.erase(height.find(h)); } cout << area;''',
        '重叠楼房只计最高处，不是把楼面积直接相加。面积用64位。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(24309,1900,['扫描线','矩形并面积','线段树'],'求有重叠轴平行矩形的并面积。',
        '按x扫描左右边界，每次对y区间覆盖次数加1或减1。将y端点离散化，树叶代表相邻端点之间的真实长度；节点覆盖次数>0时全段覆盖，否则覆盖长度由子节点相加。前后事件之间覆盖总长不变，面积增加x差乘根节点覆盖长度。输入上下角坐标先统一为升序。',
        AREA,'离散下标距离不是几何长度，长度必须用原坐标相减。区间按半开[y1,y2)维护，对应叶下标到rank(y2)−1。',
        declarations=COVER,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(24748,1900,['逆序对','循环旋转','贡献变化'],'排列经相邻交换变为任意循环升序排列的最少次数。',
        '固定目标1,2,...,n时，最少相邻交换数就是原排列逆序数，用树状数组求出。把目标首项v移到目标末尾，相当于v从最小变最大：原排列中在v前面的p−1个元素原来与它构成逆序，现在消失；后面的n−p个元素新产生逆序。所以代价变化n+1−2p。记录每个编号原位置，依次枚举n种目标起点并取最小。',
        r'''int n; cin >> n; vector<int> position(n+1); Fenwick bit(n); long long inversions=0; for (int i=1;i<=n;i++) { int x; cin >> x; position[x]=i; inversions+=i-1-bit.sum(x); bit.add(x,1); } long long answer=inversions; for (int value=1;value<n;value++) { inversions+=n+1-2LL*position[value]; answer=min(answer,inversions); } cout << answer;''',
        '旋转的是目标编号顺序，变化量使用该编号在原排列中的位置，不是编号本身。',
        declarations=BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')


if __name__ == '__main__': run()
