"""Persistent mex, append games, monotone ancestry and exact geometric thresholds."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_range_more import BIT
from nowcoder_euler_support import EULER,LCA

TREAP=r'''
struct Treap {
    struct Node { int left=0,right=0,count=1,size=1; long long key=0; unsigned priority=0; };
    vector<Node> tree; mt19937 random{20261108}; int root=0;
    Treap(int n) { tree.reserve(n+1); tree.emplace_back(); tree[0].count=tree[0].size=0; }
    void pull(int u) { if (u) tree[u].size=tree[tree[u].left].size+tree[tree[u].right].size+tree[u].count; }
    void split(int u,long long key,int &a,int &b) {
        if (!u) { a=b=0;return; }
        if (tree[u].key<=key) { a=u;split(tree[u].right,key,tree[u].right,b);pull(a); }
        else { b=u;split(tree[u].left,key,a,tree[u].left);pull(b); }
    }
    int merge(int a,int b) {
        if (!a || !b) return a?a:b;
        if (tree[a].priority<tree[b].priority) { tree[a].right=merge(tree[a].right,b);pull(a);return a; }
        tree[b].left=merge(a,tree[b].left);pull(b);return b;
    }
    void change(long long key,bool insert) {
        int a,b,c;split(root,key-1,a,b);split(b,key,b,c);
        if (insert) {
            if (b) { tree[b].count++;pull(b); }
            else { b=tree.size();tree.emplace_back();tree[b].key=key;tree[b].priority=random(); }
        } else if (b) {
            if (--tree[b].count==0) b=merge(tree[b].left,tree[b].right);
            else pull(b);
        }
        root=merge(merge(a,b),c);
    }
    int rank(long long key) {
        int u=root,answer=1;
        while(u) { if(tree[u].key<key) { answer+=tree[tree[u].left].size+tree[u].count;u=tree[u].right; } else u=tree[u].left; }
        return answer;
    }
    long long kth(int k) {
        int u=root;
        while(u) { int left=tree[tree[u].left].size;if(k<=left)u=tree[u].left;else if(k<=left+tree[u].count)return tree[u].key;else {k-=left+tree[u].count;u=tree[u].right;} }
        return 0;
    }
    long long neighbor(long long key,bool successor) {
        int u=root;long long answer=0;
        while(u) { if(successor?tree[u].key>key:tree[u].key<key) { answer=tree[u].key;u=successor?tree[u].left:tree[u].right; } else u=successor?tree[u].right:tree[u].left; }
        return answer;
    }
};
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(51117,2100,['FHQ Treap','顺序统计'],'支持重复值的插删、排名、第k小、严格前驱后继。',
        'FHQ Treap按键保持BST、按随机优先级保持堆。split将树拆成≤key与>key，merge合并键值范围有序的两棵树。每个不同键存重复次数count，size为含重复的子树大小。插删时两次split隔离该键；排名按左子树size累加，第k小按左右数量定位，前驱后继沿BST下降。\n\n重复插入只增count，删除只减一份，减至0才合并两个儿子替换该节点。随机优先级使树高期望对数。',
        r'''int n;cin >> n;Treap tree(n);while(n--){int op;long long x;cin >> op >> x;if(op==1 || op==2)tree.change(x,op==1);else if(op==3)cout << tree.rank(x) << '\n';else if(op==4)cout << tree.kth(x) << '\n';else cout << tree.neighbor(x,op==6) << '\n';}''',
        '严格前驱/后继不包含相等值。key用64位，split(key−1)不会在原32位边界溢出。题目查询需要存在合法答案。',
        declarations=TREAP,complexity=r'每次期望 $O(\log n)$，极端优先级下最坏 $O(n)$；空间 $O(n)$。')
    put(21758,2300,['区间mex','可持久化线段树'],'子数组独立离散化，求数值发生变化的元素个数。',
        '正整数x离散化后仍等于x，当且仅当区间内1..x全部出现。令M为区间最小缺失正整数mex，则不变元素恰为值<M的元素，其余全变。\n\n按右端点建可持久化值域树，节点同时记录出现总数count和每种值最近出现位置的最小值minimum。版本R中，mex就是第一个最近位置<L的值：看左子树minimum是否<L决定向左或向右。随后用版本R与L−1之差统计值<M的频次，答案为长度减去该频次。\n\n值域只需1..n+1，超出值域的数一定改变，可不插入。空节点minimum=0，正确表示从未出现。',
        r'''int n;cin >> n;struct Node{int left=0,right=0,count=0,minimum=0;};vector<Node> tree;tree.reserve((size_t)n*21+1);tree.emplace_back();vector<int> root(n+1);auto update=[&](auto &&self,int old,int l,int r,int position,int time)->int{int u=tree.size();tree.push_back(tree[old]);tree[u].count++;if(l==r){tree[u].minimum=time;return u;}int mid=(l+r)/2;if(position<=mid)tree[u].left=self(self,tree[old].left,l,mid,position,time);else tree[u].right=self(self,tree[old].right,mid+1,r,position,time);tree[u].minimum=min(tree[tree[u].left].minimum,tree[tree[u].right].minimum);return u;};for(int i=1;i<=n;i++){int x;cin >> x;root[i]=x<=n+1?update(update,root[i-1],1,n+1,x,i):root[i-1];}auto prefix=[&](auto &&self,int u,int l,int r,int bound)->int{if(!u || bound<l)return 0;if(r<=bound)return tree[u].count;int mid=(l+r)/2;return self(self,tree[u].left,l,mid,bound)+self(self,tree[u].right,mid+1,r,bound);};int q;cin >> q;while(q--){int l,r;cin >> l >> r;int u=root[r],low=1,high=n+1;while(low<high){int mid=(low+high)/2;if(tree[tree[u].left].minimum<l){u=tree[u].left;high=mid;}else{u=tree[u].right;low=mid+1;}}int unchanged=prefix(prefix,root[r],1,n+1,low-1)-prefix(prefix,root[l-1],1,n+1,low-1);cout << r-l+1-unchanged << '\n';}''',
        '离散化rank不可能大于原正整数值；只找mex还不够，答案要按元素出现次数计数，重复元素不能去重。',
        complexity=r'时间 $O((n+q)\log n)$，空间 $O(n\log n)$。')
    put(285230,2300,['图中三角形','位集','离线排序'],'三点作等半径圆，圆可相切但不相交，最大半径。',
        '固定三点，半径最多是三条距离最小值的一半。将所有点对按距离平方降序加入无向图。首次出现三角形时，这个三角形最短边就是当前阈值，而此前更大的阈值无三角形，所以得到全局最优。\n\n加入边(u,v)前，只需检查u、v此前的邻接集合是否有交集；用64位位集逐字AND，非零即存在第三点。距离平方为整数，可精确比较；仅最后做sqrt/2。3000点边数约450万，端点用16位存储减少排序内存。',
        r'''int n;cin >> n;vector<pair<int,int>> point(n);for(auto &[x,y]:point)cin >> x >> y;struct Edge{int distance;uint16_t u,v;};vector<Edge> edge;edge.reserve((size_t)n*(n-1)/2);for(int i=0;i<n;i++)for(int j=i+1;j<n;j++){long long dx=point[i].first-point[j].first,dy=point[i].second-point[j].second;edge.push_back({(int)(dx*dx+dy*dy),(uint16_t)i,(uint16_t)j});}sort(edge.begin(),edge.end(),[](auto a,auto b){return a.distance>b.distance;});int words=(n+63)/64;vector<vector<unsigned long long>> neighbor(n,vector<unsigned long long>(words));for(auto e:edge){bool triangle=false;for(int w=0;w<words;w++)if(neighbor[e.u][w]&neighbor[e.v][w]){triangle=true;break;}if(triangle){cout << fixed << setprecision(12) << sqrtl(e.distance)/2;return 0;}neighbor[e.u][e.v/64]|=1ULL<<(e.v%64);neighbor[e.v][e.u/64]|=1ULL<<(e.u%64);}''',
        '目标是最大化三边中的最小边，不是最大直径或外接圆。等长边按任意顺序加入，首次成三角形的阈值仍正确。',
        floating_output=True,complexity=r'时间 $O(n^2\log n+n^3/64)$，空间 $O(n^2)$，每条边8字节。')
    put(236242,1800,['树状数组','有序集合','均摊分析'],'区间向下开根，查询区间和。',
        '正整数反复向下开根很快变1，而1以后不变。用set只保存值>1的位置，修改区间时从lower_bound(l)遍历至r，逐点开根并给Fenwick加入差值，变1就从set移除。每个初值≤10^9最多约5次有效变化，总修改量远小于nQ。',
        r'''int n,q;cin >> n >> q;vector<long long> a(n+1);Fenwick bit(n);set<int> active;for(int i=1;i<=n;i++){cin >> a[i];bit.add(i,a[i]);if(a[i]>1)active.insert(i);}while(q--){int op,l,r;cin >> op >> l >> r;if(op==2)cout << bit.sum(r)-bit.sum(l-1) << '\n';else{auto it=active.lower_bound(l);while(it!=active.end() && *it<=r){int p=*it;long long x=sqrtl(a[p]);while((x+1)*(x+1)<=a[p])x++;while(x*x>a[p])x--;bit.add(p,x-a[p]);a[p]=x;if(x==1)it=active.erase(it);else it++;}}}''',
        '不能把整个区间和开根。开方用整数平方校正，避免完全平方数的浮点误差。',
        declarations=BIT,complexity=r'总时间 $O((Q+n\log\log A)\log n)$，空间 $O(n)$。')
    put(15667,1900,['线段树','位掩码','区间OR'],'区间每桶加入某色球，询问范围内不同颜色数。',
        '颜色0..60用64位掩码。加入颜色c相当于区间每桶掩码OR上1ULL<<c，节点统计整段颜色并集也OR该位，懒标记用OR合并。部分访问时下传标记，查询将所有命中段的并集OR起来，popcount得到颜色数。',
        r'''int n,m;while(cin >> n >> m){vector<unsigned long long> value(4*n+4),tag(4*n+4);auto apply=[&](int u,unsigned long long mask){value[u]|=mask;tag[u]|=mask;};auto push=[&](int u){if(tag[u]){apply(u*2,tag[u]);apply(u*2+1,tag[u]);tag[u]=0;}};auto update=[&](auto &&self,int u,int l,int r,int ql,int qr,unsigned long long mask)->void{if(ql<=l && r<=qr){apply(u,mask);return;}push(u);int mid=(l+r)/2;if(ql<=mid)self(self,u*2,l,mid,ql,qr,mask);if(qr>mid)self(self,u*2+1,mid+1,r,ql,qr,mask);value[u]=value[u*2]|value[u*2+1];};auto query=[&](auto &&self,int u,int l,int r,int ql,int qr)->unsigned long long{if(ql<=l && r<=qr)return value[u];push(u);int mid=(l+r)/2;unsigned long long answer=0;if(ql<=mid)answer|=self(self,u*2,l,mid,ql,qr);if(qr>mid)answer|=self(self,u*2+1,mid+1,r,ql,qr);return answer;};while(m--){int op,l,r;cin >> op >> l >> r;if(op==1){int c;cin >> c;update(update,1,1,n,l,r,1ULL<<c);}else cout << __builtin_popcountll(query(query,1,1,n,l,r)) << '\n';}}''',
        '操作是增加颜色，不是覆盖桶的旧颜色；懒标记应OR累积。颜色0用第0位。',
        complexity=r'每组时间 $O(m\log n)$，空间 $O(n)$。')
    put(235654,2000,['倍增LCA','树上中点'],'查询到x与y等距的树节点数。',
        'x=y时全树等距；路径长度为奇数时没有整数节点中点，答案0。长度为偶数时，等距点恰是去掉中点通向x、y的两条边后，包含中点的连通块。\n\n若x、y同深度，中点为LCA，设其两侧儿子为a、b，答案n−size[a]−size[b]。否则令x较深，中点z在x一侧，令a为z通向x的儿子，答案size[z]−size[a]。用倍增跳指定步数得到这些点。',
        r'''int n;cin >> n;EulerTree tree(n);for(int i=1;i<n;i++){int u,v;cin >> u >> v;tree.add(u,v);}tree.root(1);Ancestors ancestor(tree);vector<int> size(n+1,1);for(int i=n-1;i>0;i--){int u=tree.order[i];size[tree.parent[u]]+=size[u];}auto jump=[&](int u,int steps){for(int b=0;steps;b++,steps>>=1)if(steps&1)u=ancestor.up[b][u];return u;};int q;cin >> q;while(q--){int x,y;cin >> x >> y;if(x==y){cout << n << '\n';continue;}int distance=ancestor.distance(x,y);if(distance%2){cout << 0 << '\n';continue;}int half=distance/2;if(tree.depth[x]==tree.depth[y])cout << n-size[jump(x,half-1)]-size[jump(y,half-1)] << '\n';else{if(tree.depth[x]<tree.depth[y])swap(x,y);int z=jump(x,half),a=jump(x,half-1);cout << size[z]-size[a] << '\n';}}''',
        '等距点不是只算路径中点，还包含中点旁支。半长至少1，x=y已单独处理。',
        declarations=EULER+LCA,complexity=r'预处理 $O(n\log n)$，每问 $O(\log n)$，空间 $O(n\log n)$。')
    put(236244,2300,['单调祖先链','在线倍增'],'动态加点，沿最近不小权祖先链在预算内取最多节点。',
        '每点下一步被规则唯一确定为“最近的权值不小于自己的祖先”，称单调父亲；沿此链权值非递减。新点挂在R下时，若w[R]够大就取R，否则沿R的单调祖先倍增跳过仍小于新权的节点，再取其单调父亲。这不会漏掉原树中合格祖先，因为被单调父亲跳过的点权都更小。\n\n同时维护jump[b][u]及cost[b][u]：从u开始取2^b个链点的总代价与之后位置。查询从高位到低位尝试整块加入，预算够就扣除并前进。权值非负，跳过可支付的最长块是最优。0号为无穷权哨兵，防止越过根多计零节点，根1权为0可正常选一次。',
        r'''int q;cin >> q;const int levels=20;const unsigned long long inf=4000000000000000000ULL;vector<array<int,levels>> up(q+2);vector<array<unsigned long long,levels>> cost(q+2);vector<unsigned long long> weight(q+2,inf);cost[0].fill(inf);cost[1].fill(inf);cost[1][0]=0;weight[1]=0;int nodes=1;unsigned long long last=0;while(q--){int op;unsigned long long p,value;cin >> op >> p >> value;int r=(int)(p^last);value^=last;if(op==1){int parent=r;if(weight[parent]<value){for(int b=levels-1;b>=0;b--)if(weight[up[parent][b]]<value)parent=up[parent][b];parent=up[parent][0];}int u=++nodes;weight[u]=value;up[u][0]=parent;cost[u][0]=value;for(int b=1;b<levels;b++){int v=up[u][b-1];up[u][b]=up[v][b-1];cost[u][b]=min(inf,cost[u][b-1]+cost[v][b-1]);}}else{last=0;int u=r;for(int b=levels-1;b>=0;b--)if(cost[u][b]<=value){value-=cost[u][b];last+=1ULL<<b;u=up[u][b];}cout << last << '\n';}}''',
        '每行p、q都先与上次查询答案异或；添加操作不更新last。样例包含零权新点，代码同样支持。',
        complexity=r'每次操作 $O(\log Q)$，空间 $O(Q\log Q)$。')
    put(236260,2300,['博弈DP','最近出现位置','小值域'],'末尾追加0..255值，查询从指定位置已选后谁获胜。',
        '固定序列从后向前，令lose表示“选中此处后，下一人无必胜策略”的位置值集合。位置i若能走到某个lose位置，就是胜态；否则是lose并加入其值。可走条件是两个值相同或仅差一个二进制位，所以一旦某个值被lose集合的邻值覆盖，此后永远不会成为lose。\n\n因此同一个数只需看它的最后一次出现；按256种值的最后位置从大到小扫描，若该值尚未被覆盖，就选为lose，并覆盖自身及8个一位差邻值。为每种值v记录所有已选lose邻值的最大位置threshold[v]。\n\n查询起点k已经由Alice选中，轮到Bob；Bob能赢当且仅当存在位置>k的lose邻值，即threshold[a[k]]>k。追加时把该值移到最近使用链表表头，重算256种值的覆盖即可；查询常数时间。',
        r'''int n,m;cin >> n >> m;vector<int> a; a.reserve(n+m);array<int,256> latest={},threshold={};for(int i=1;i<=n;i++){int x;cin >> x;a.push_back(x);latest[x]=i;}list<int> order;vector<int> values;for(int v=0;v<256;v++)if(latest[v])values.push_back(v);sort(values.begin(),values.end(),[&](int x,int y){return latest[x]>latest[y];});array<list<int>::iterator,256> where;for(int v:values){order.push_back(v);where[v]=prev(order.end());}auto rebuild=[&](){array<bool,256> blocked={};threshold.fill(0);for(int v:order)if(!blocked[v]){auto cover=[&](int x){blocked[x]=true;threshold[x]=max(threshold[x],latest[v]);};cover(v);for(int b=0;b<8;b++)cover(v^(1<<b));}};rebuild();while(m--){int op,k;cin >> op >> k;if(op==1){if(latest[k])order.erase(where[k]);order.push_front(k);where[k]=order.begin();a.push_back(k);latest[k]=a.size();rebuild();}else cout << (threshold[a[k-1]]>k?"Bob\n":"Alice\n");}''',
        '相同数也可跳，邻域包含自身。全局记录中位置≤k的lose点不会误判，因为查询要求严格大于k。',
        complexity=r'初始化 $O(n+256\log256)$，追加 $O(256\cdot9)$，查询 $O(1)$；空间 $O(n+m+256)$。')
    put(236212,1800,['构造','奇偶性','最大公约数'],'n组四个数，两两gcd=k，组间不重复，最小化最大数。',
        '所有数都可除以k，问题变成每组四个数两两互素。一组至多一个偶数，因此4n个不同数中至少3n个为奇数，最大数至少6n−1。\n\n对i=0..n−1构造{6i+1,6i+2,6i+3,6i+5}，恰用3个奇数和1个偶数。不同奇数差2或4，可能公共奇因子只有来自差的因子，故互素；偶数与两邻数连续，与6i+5差3但它不被3整除，也互素。所有组不重复，最大值6n−1达到下界。最后全体乘k。',
        r'''long long n,k;cin >> n >> k;cout << (6*n-1)*k << '\n';for(long long i=0;i<n;i++)cout << (6*i+1)*k << ' ' << (6*i+2)*k << ' ' << (6*i+3)*k << ' ' << (6*i+5)*k << '\n';''',
        '最大公因数恰好k，构造基础数必须两两互素，不能只让整组gcd为1。',
        checker='pairwise-gcd-groups',complexity=r'时间 $O(n)$，额外空间 $O(1)$。')


if __name__=='__main__':run()
