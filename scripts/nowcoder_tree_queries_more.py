"""Iterative Euler order, LCA, tree differences and a binary-tree LIS."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_euler_support import EULER, LCA
from nowcoder_range_more import BIT
from nowcoder_tree_support import TREE

SQUARE = r'''
struct SquareTree {
    static constexpr long long mod=23333;
    int n; vector<long long> sum,square,tag;
    SquareTree(const vector<long long> &a):n((int)a.size()-1),sum(4*n+4),square(4*n+4),tag(4*n+4) { build(1,1,n,a); }
    void pull(int u) { sum[u]=(sum[u*2]+sum[u*2+1])%mod; square[u]=(square[u*2]+square[u*2+1])%mod; }
    void build(int u,int l,int r,const vector<long long> &a) { if (l==r) { sum[u]=(a[l]%mod+mod)%mod; square[u]=sum[u]*sum[u]%mod; return; } int mid=(l+r)/2; build(u*2,l,mid,a); build(u*2+1,mid+1,r,a); pull(u); }
    void apply(int u,int l,int r,long long v) { v=(v%mod+mod)%mod; square[u]=(square[u]+2*v*sum[u]+(r-l+1)*v%mod*v)%mod; sum[u]=(sum[u]+(r-l+1)*v)%mod; tag[u]=(tag[u]+v)%mod; }
    void push(int u,int l,int r) { if (!tag[u] || l==r) return; int mid=(l+r)/2; apply(u*2,l,mid,tag[u]); apply(u*2+1,mid+1,r,tag[u]); tag[u]=0; }
    void change(int u,int l,int r,int ql,int qr,long long v) { if (ql<=l && r<=qr) { apply(u,l,r,v); return; } push(u,l,r); int mid=(l+r)/2; if (ql<=mid) change(u*2,l,mid,ql,qr,v); if (qr>mid) change(u*2+1,mid+1,r,ql,qr,v); pull(u); }
    long long query(int u,int l,int r,int ql,int qr) { if (ql<=l && r<=qr) return square[u]; push(u,l,r); int mid=(l+r)/2; long long value=0; if (ql<=mid) value+=query(u*2,l,mid,ql,qr); if (qr>mid) value+=query(u*2+1,mid+1,r,ql,qr); return value%mod; }
};
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(23482,1800,['倍增LCA','树上距离'],'树上另有一条免费缆车边，批量求两点最少步行距离。',
        '最短路线若不用缆车，代价为树距离dist(x,y)；若使用，因为树边正权，免费缆车最多有必要用一次，分别考虑x→U、V→y以及x→V、U→y。取三个代价的最小值。树距离由深度和LCA得到，倍增预处理后每次查询对数时间。',
        r'''int n; cin >> n; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(1); Ancestors ancestor(tree); int u,v,q; cin >> u >> v >> q; while (q--) { int x,y; cin >> x >> y; cout << min({ancestor.distance(x,y),ancestor.distance(x,u)+ancestor.distance(v,y),ancestor.distance(x,v)+ancestor.distance(u,y)}) << '\n'; }''',
        '缆车双向且代价为0，不要额外加1。迭代遍历避免长链递归栈溢出。',
        declarations=EULER+LCA,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n\log n)$。')
    put(13611,1700,['组合计数','树上连通块'],'k色染树，要求每种已用颜色的节点构成连通块。',
        '合法方案中，每条异色边切开后得到若干单色连通块；同一种颜色不能出现在两个块，否则路径中出现别色。若有c块，则恰切c−1条树边，可任意选择C(n−1,c−1)种。给c个有区别的块分配不同颜色有k*(k−1)*...*(k−c+1)种。累加c=1..min(n,k)即可，树形不影响计数。',
        r'''int n,k; cin >> n >> k; for (int i=1;i<n;i++) { int u,v; cin >> u >> v; } const long long mod=1000000007; vector<long long> choose(n); choose[0]=1; for (int i=1;i<n;i++) for (int j=i;j>=1;j--) choose[j]=(choose[j]+choose[j-1])%mod; long long falling=1,answer=0; for (int c=1;c<=min(n,k);c++) { falling=falling*(k-c+1)%mod; answer=(answer+choose[c-1]*falling)%mod; } cout << answer;''',
        '颜色有区别，块之间颜色必须互不相同；不能只乘k^c。边仍须全部读入。',
        complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(204871,1600,['DFS序','树状数组'],'固定根树单点加，查询子树权值和，n至百万。',
        '深度优先序中，一个节点的整棵子树恰是连续区间[in[u],out[u]]。用显式栈生成DFS先序，逆序累加子树大小即可得到out。按in把点权放入树状数组，点修改为单点加，子树查询为两个前缀和之差。',
        r'''int n,m,k; cin >> n >> m >> k; vector<long long> value(n+1); for (int i=1;i<=n;i++) cin >> value[i]; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(k); Fenwick bit(n); for (int u=1;u<=n;u++) bit.add(tree.in[u],value[u]); while (m--) { int op,u; cin >> op >> u; if (op==1) { long long x; cin >> x; bit.add(tree.in[u],x); } else cout << bit.sum(tree.out[u])-bit.sum(tree.in[u]-1) << '\n'; }''',
        '根是输入k，不一定为1。点权与增量可能为负；所有和使用64位。',
        declarations=EULER+BIT,complexity=r'预处理 $O(n\log n)$，操作 $O(\log n)$，空间 $O(n)$。')
    put(23051,2100,['离线建树','DFS序','出生时间'],'动态添加零权儿子，子树加，单点查询。',
        '先读完操作建最终树，得到DFS子树区间，再按原时间重放。用差分树状数组做最终子树区间加、单点查询。最终子树中包含未来才出生的节点，会被早期更新计入；因此新节点出生时，记下当前该位置的累计值base。其真实权值始终是当前累计值−base，恰好去掉出生之前的全部更新。根从一开始存在，base为0。',
        r'''int m; cin >> m; struct Operation { int type,node,created; long long value; }; vector<Operation> operation; EulerTree tree(m+1); int nodes=1; for (int i=0;i<m;i++) { int op,u; cin >> op >> u; u++; if (op==1) { int v=++nodes; tree.add(u,v); operation.push_back({op,u,v,0}); } else { long long x=0; if (op==2) cin >> x; operation.push_back({op,u,0,x}); } } tree.root(1); Fenwick bit(nodes); vector<long long> base(nodes+1); for (auto op : operation) { if (op.type==1) base[op.created]=bit.sum(tree.in[op.created]); else if (op.type==2) { bit.add(tree.in[op.node],op.value); if (tree.out[op.node]<nodes) bit.add(tree.out[op.node]+1,-op.value); } else cout << bit.sum(tree.in[op.node])-base[op.node] << '\n'; }''',
        '内部编号整体加1以兼容Fenwick下标。新节点初始必须为0，不能继承父节点历史增量。',
        declarations=EULER+BIT,complexity=r'时间 $O(M\log M)$，空间 $O(M)$。')
    put(22494,1900,['遍历顺序','最长上升子序列'],'二叉树选最多节点，根小于所选后代，所选左子树值大于右子树值。',
        '按“根、右子树、左子树”先序遍历。任意两个选中节点，若为祖孙，先出现的祖先必须更小；否则其最近公共祖先把它们分在右、左子树，右先出现且必须更小。因此合法选择与此遍历序列的严格上升子序列恰好对应。用tails二分求严格LIS即可，树遍历用栈。',
        r'''int n; cin >> n; vector<long long> value(n+1); vector<int> left(n+1),right(n+1); for (int i=1;i<=n;i++) cin >> value[i]; for (int i=1;i<=n;i++) cin >> left[i] >> right[i]; vector<int> stack={1}; vector<long long> tails; while (!stack.empty()) { int u=stack.back(); stack.pop_back(); auto it=lower_bound(tails.begin(),tails.end(),value[u]); if (it==tails.end()) tails.push_back(value[u]); else *it=value[u]; if (left[u]) stack.push_back(left[u]); if (right[u]) stack.push_back(right[u]); } cout << tails.size();''',
        '顺序必须是根右左，栈中先压左再压右。严格上升用lower_bound，重复值不能同时选。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    for number,squirrel in [(20139,True),(24019,False)]:
        body=r'''int n; INPUT vector<int> visit; VISIT EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(1); Ancestors ancestor(tree); vector<long long> difference(n+1); PATHS for (int i=n-1;i>0;i--) { int u=tree.order[i]; difference[tree.parent[u]]+=difference[u]; } OUTPUT'''
        path=r'''auto addPath=[&](int u,int v) { int a=ancestor.lca(u,v); difference[u]++; difference[v]++; difference[a]--; difference[tree.parent[a]]--; };'''
        if squirrel:
            code=body.replace('INPUT','cin >> n;').replace('VISIT','visit.resize(n); for (int &x : visit) cin >> x;').replace('PATHS',path+' for (int i=1;i<n;i++) addPath(visit[i-1],visit[i]);').replace('OUTPUT','for (int i=1;i<n;i++) difference[visit[i]]--; for (int u=1;u<=n;u++) cout << difference[u] << \'\\n\';')
            idea='对每次相邻参观点u→v，先给整条点路径加1：diff[u]++、diff[v]++、diff[LCA]−−、diff[parent(LCA)]−−，再逆序把子树差分累加到父亲，得到路径经过次数。相邻两段会在连接点重复计数，最后到餐厅也不吃糖，所以对指南中的第2到第n个终点各减1，保留每段出发点到终点之前的贡献。'
        else:
            code=body.replace('INPUT','int k; cin >> n >> k;').replace('VISIT','').replace('PATHS',path+' while (k--) { int u,v; cin >> u >> v; addPath(u,v); }').replace('OUTPUT','cout << *max_element(difference.begin()+1,difference.end());')
            idea='每条点路径u→v对所有经过节点加1。设a=LCA(u,v)，差分标记diff[u]++、diff[v]++、diff[a]−−、diff[parent(a)]−−。逆序累加子树到父节点后，a以下两条链各得到1，a本身也得到1，a以上抵消为0。全部路径累加后取最大节点值。'
        put(number,1900,['倍增LCA','树上差分'],'树上批量路径计数。',idea,code,
            '这里统计点而非边，LCA本身必须保留一次；根的父亲用0哨兵，不向它继续累加。',
            declarations=EULER+LCA,complexity=r'时间 $O((n+q)\log n)$，空间 $O(n\log n)$。')
    put(19428,2000,['DFS序','线段树','平方和'],'子树加，查询子树权值平方和模23333。',
        'DFS序把子树化为区间。线段树同时维护总和S与平方和Q；长度len的一段加v后，Q新=Q+2vS+len*v²，S新=S+len*v。区间加懒标记累加，下传后再做部分修改或查询，始终模23333。',
        r'''int n,q; cin >> n >> q; vector<long long> value(n+1); for (int i=1;i<=n;i++) cin >> value[i]; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(1); vector<long long> a(n+1); for (int u=1;u<=n;u++) a[tree.in[u]]=value[u]; SquareTree segment(a); while (q--) { int op,u; cin >> op >> u; if (op==1) { long long v; cin >> v; segment.change(1,1,n,tree.in[u],tree.out[u],v); } else cout << segment.query(1,1,n,tree.in[u],tree.out[u]) << '\n'; }''',
        'Q的更新使用修改前的S。平方和与和的平方不同，不能只维护总和。',
        declarations=EULER+SQUARE,complexity=r'构建 $O(n)$，每次操作 $O(\log n)$，空间 $O(n)$。')
    put(15844,1400,['中序遍历','二叉搜索树'],'检查给定二叉树是否满足左子树≤根≤右子树。',
        '允许相等的二叉搜索树，当且仅当中序遍历权值非递减。用显式栈按左、根、右遍历，每次与前一个权值比较；出现下降就不合法。等价性来自中序顺序把整个左子树放在根前、整个右子树放在根后，而不是只比较两个直接儿子。',
        r'''int tests; cin >> tests; while (tests--) { int n,root; cin >> n >> root; vector<unsigned long long> value(n+1); vector<int> left(n+1),right(n+1); for (int i=1;i<=n;i++) cin >> value[i] >> left[i] >> right[i]; vector<int> stack; int u=root; bool ok=true,hasPrevious=false; unsigned long long previous=0; while (u || !stack.empty()) { while (u) { stack.push_back(u); u=left[u]; } u=stack.back(); stack.pop_back(); if (hasPrevious && value[u]<previous) ok=false; previous=value[u]; hasPrevious=true; u=right[u]; } cout << (ok?"yes\n":"no\n"); }''',
        '相同值允许，比较用<。根编号由输入给出；迭代遍历适用于退化长链。',
        complexity=r'每棵树时间、空间均 $O(n)$。')
    put(213912,1900,['树上前缀异或','倍增LCA','回文重排'],'树路径上收集字母，可重排部分字母，求最长回文长度。',
        '任意字母可成对放在回文两侧，最多留下一个奇数频次字母放中心。路径长len、奇数频次字母数odd时，答案为len−max(0,odd−1)。用26位掩码记录根路径上字母频次奇偶，路径掩码为mask[x] xor mask[y] xor (1<<字母[LCA])，popcount得到odd。长度由深度和LCA求出。',
        r'''int n; cin >> n; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } string s; cin >> s; tree.root(1); Ancestors ancestor(tree); vector<unsigned> mask(n+1); for (int u:tree.order) mask[u]=mask[tree.parent[u]]^(1U<<(s[u-1]-'a')); int q; cin >> q; while (q--) { int x,y; cin >> x >> y; int a=ancestor.lca(x,y),length=tree.depth[x]+tree.depth[y]-2*tree.depth[a]+1; int odd=__builtin_popcount(mask[x]^mask[y]^(1U<<(s[a-1]-'a'))); cout << length-max(0,odd-1) << '\n'; }''',
        'LCA在两个前缀掩码中抵消，必须补回它的字母。题目允许重排，不是路径上的最长回文子串。',
        declarations=EULER+LCA,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n\log n)$。')
    put(24048,1800,['DFS序','离线排序','树状数组'],'每个节点统计子树中能力严格更高的后代数。',
        '先用DFS序得到每个子树区间，然后按能力从高到低插入节点。处理u时，已插入的恰是能力更高者，查询其子树区间计数就是答案，随后把u插入。原题能力互不相同，因此无需同值分组。',
        r'''int n; cin >> n; vector<long long> power(n+1); vector<int> order(n); for (int i=1;i<=n;i++) { cin >> power[i]; order[i-1]=i; } EulerTree tree(n); for (int v=2;v<=n;v++) { int p; cin >> p; tree.add(p,v); } tree.root(1); sort(order.begin(),order.end(),[&](int a,int b) { return power[a]>power[b]; }); Fenwick bit(n); vector<int> answer(n+1); for (int u:order) { answer[u]=bit.sum(tree.out[u])-bit.sum(tree.in[u]-1); bit.add(tree.in[u],1); } for (int u=1;u<=n;u++) cout << answer[u] << '\n';''',
        '先查询后插入，避免把自身算入后代。统计严格高于而非不低于。',
        declarations=EULER+BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(24727,1700,['DFS序','树状数组'],'牛依次从根走向各自牧场，统计经过已到达牛的次数。',
        '已停在节点u的牛，会使后来目标位于u子树的牛减速。因此每到达一头牛，就给u的整个DFS子树区间加1；下一头牛的减速次数是其目标点当前位置值。用差分树状数组做区间加、单点查询，先查询再加入。',
        r'''int n; cin >> n; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(1); Fenwick bit(n); for (int i=0;i<n;i++) { int u; cin >> u; cout << bit.sum(tree.in[u]) << '\n'; bit.add(tree.in[u],1); if (tree.out[u]<n) bit.add(tree.out[u]+1,-1); }''',
        '根节点也可能是某头牛的牧场，会影响之后所有牛。当前牛尚未到达，不能先插入再查询。',
        declarations=EULER+BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(210473,2000,['二分答案','树形DP','最小割'],'预算内切断所有根到叶路径，最小化所切边的最大长度。',
        '二分最长可切边限制X。自底向上计算dp[u]为阻断u到其子树所有原叶子的最小代价；非根叶子设无穷。对每个儿子v，或者在内部支付dp[v]，或者在边权w≤X时直接切父子边支付w，取较小值，各儿子求和。dp[root]≤预算即可行。可行性随X增大单调，搜索0到最大边长；若最大边长仍不可行输出−1。只有根时没有叛军，答案0。',
        r'''int n; long long budget; cin >> n >> budget; Tree tree(n); int maximum=0; for (int i=1;i<n;i++) { int u,v,w; cin >> u >> v >> w; tree.add(u-1,v-1,w); maximum=max(maximum,w); } tree.root(0); auto feasible=[&](int limit) { vector<long long> dp(n); for (int i=n-1;i>=0;i--) { int u=tree.order[i]; if (u && tree.edge[u].size()==1) { dp[u]=budget+1; continue; } for (auto [v,w]:tree.edge[u]) if (tree.parent[v]==u) dp[u]=min(budget+1,dp[u]+min(dp[v],w<=limit?w:budget+1)); } return dp[0]<=budget; }; if (!feasible(maximum)) { cout << -1; return 0; } int low=0,high=maximum; while (low<high) { int mid=(low+high)/2; if (feasible(mid)) high=mid; else low=mid+1; } cout << low;''',
        '叶子是原树中除根外度数1的点。预算超出后截为budget+1，防止无穷累加。',
        declarations=TREE,complexity=r'时间 $O(n\log W)$，空间 $O(n)$。')
    put(15748,1800,['树形DP','最大独立集'],'住宿点不能已被游览，首日固定在s，求最多天数。',
        '某日住宿会游览自身及所有邻点，因此全部住宿点必须两两不相邻；反过来任何包含s的独立集都可按任意顺序住宿。问题就是必须选s的树上最大独立集。以s为根，dp[u][1]=1+Σdp[v][0]，dp[u][0]=Σmax(dp[v][0],dp[v][1])，输出dp[s][1]。',
        r'''int n,s; cin >> n >> s; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(s); vector<array<int,2>> dp(n+1); for (int i=n-1;i>=0;i--) { int u=tree.order[i]; dp[u][1]=1; for (int v:tree.edge[u]) if (tree.parent[v]==u) { dp[u][0]+=max(dp[v][0],dp[v][1]); dp[u][1]+=dp[v][0]; } } cout << dp[s][1];''',
        '首日s强制选中，不能输出根两个状态的最大值。题目没有要求每天住宿点与前一天相邻。',
        declarations=EULER,complexity=r'时间、空间均 $O(n)$。')
    put(13249,2200,['树上贪心','区间覆盖'],'选择向祖先染黑的操作，最少覆盖整棵树。',
        '操作u覆盖深度区间[depth[u]−k[u]+1,depth[u]]上的祖先链。先忽略“选点必须白色”：任何选点集合都可按深度从浅到深执行，之前的操作只染祖先，不会提前染黑后面要选的深点，所以限制不会改变最优值。\n\n按后序处理最深的尚未覆盖节点u。要覆盖它，操作起点必在它的子树内；选择其中能向上延伸最远的起点最优。交换证明：替换任意覆盖u的操作，u以下节点此前已覆盖，u以上新操作覆盖至少一样高，因此不变差。\n\n维护best[u]为整个子树内所有候选操作最浅能到的深度，covered[u]为已选操作最浅覆盖深度。合并儿子取最小，再加入u自己的候选。若covered[u]>depth[u]，u尚未覆盖，答案加1并选best[u]。只需传递深度，不必实际染色。',
        r'''int n; cin >> n; EulerTree tree(n); for (int v=2;v<=n;v++) { int p; cin >> p; tree.add(p,v); } vector<int> k(n+1); for (int i=1;i<=n;i++) cin >> k[i]; tree.root(1); const int inf=INT_MAX/2; vector<int> best(n+1),covered(n+1,inf); int answer=0; for (int i=n-1;i>=0;i--) { int u=tree.order[i]; best[u]=tree.depth[u]-k[u]+1; for (int v:tree.edge[u]) if (tree.parent[v]==u) { best[u]=min(best[u],best[v]); covered[u]=min(covered[u],covered[v]); } if (covered[u]>tree.depth[u]) { answer++; covered[u]=best[u]; } } cout << answer;''',
        '候选包括已被其他操作覆盖的节点，它可以在最终执行顺序中提前操作。仅对尚未染黑节点直接操作的朴素后序贪心不正确。',
        declarations=EULER,complexity=r'时间、空间均 $O(n)$。')
    put(201400,1800,['换根DP','距离和'],'任选树根，使所有节点深度和最小。',
        '先以1为根求深度和W[1]及每棵子树大小size。根从u移到儿子v时，v子树的size[v]个点距离各减1，其余n−size[v]个点各加1，所以W[v]=W[u]+n−2*size[v]。一次逆序求size，再按先序换根，取全部W最小值。',
        r'''int n; cin >> n; EulerTree tree(n); for (int i=1;i<n;i++) { int u,v; cin >> u >> v; tree.add(u,v); } tree.root(1); vector<int> size(n+1,1); vector<long long> value(n+1); for (int u:tree.order) value[1]+=tree.depth[u]; for (int i=n-1;i>0;i--) { int u=tree.order[i]; size[tree.parent[u]]+=size[u]; } long long answer=value[1]; for (int u:tree.order) if (u!=1) { value[u]=value[tree.parent[u]]+n-2LL*size[u]; answer=min(answer,value[u]); } cout << answer;''',
        '距离和长链可达n(n−1)/2，需64位。树百万节点，使用迭代遍历。',
        declarations=EULER,complexity=r'时间、空间均 $O(n)$。')


if __name__ == '__main__': run()
