"""Dominance, weighted inversions, nonlinear aggregates and order statistics."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_range_more import BIT

ALTERNATING = r'''
struct Node {
    long long sum=0,prefix=0,suffix=0,best=LLONG_MIN;
    int left=0,right=0; bool all=true,empty=true;
};
Node mergeNode(const Node &a,const Node &b) {
    if (a.empty) return b; if (b.empty) return a;
    Node c; c.empty=false; c.left=a.left; c.right=b.right;
    bool join=a.right!=b.left;
    c.sum=a.sum+b.sum; c.all=a.all && b.all && join;
    c.prefix=a.prefix; if (a.all && join) c.prefix=max(c.prefix,a.sum+b.prefix);
    c.suffix=b.suffix; if (b.all && join) c.suffix=max(c.suffix,b.sum+a.suffix);
    c.best=max(a.best,b.best); if (join) c.best=max(c.best,a.suffix+b.prefix);
    return c;
}
Node leaf(long long x) { Node a; a.empty=false; a.sum=a.prefix=a.suffix=a.best=x; a.left=a.right=(x%2+2)%2; return a; }
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(50428,1400,['树状数组','二维偏序'],'按y再x升序给出星星，统计左下方点数的等级分布。',
        '输入顺序保证当前点左下方的点已经全部出现：y更小，或同y但x更小。用树状数组记录已出现的x频数，查询x以下含x的前缀和就是等级，给该等级的答案加1，然后把当前点插入。',
        r'''int n; cin >> n; Fenwick bit(32002); vector<int> count(n); for (int i=0;i<n;i++) { int x,y; cin >> x >> y; x++; count[bit.sum(x)]++; bit.add(x,1); } for (int x : count) cout << x << '\n';''',
        'x可以为0，树状数组下标整体加1。同y的点也应按输入顺序立即插入，因为正左方包含在等级中。',
        declarations=BIT,complexity=r'时间 $O(n\log U)$，空间 $O(U+n)$。')
    put(26253,1800,['二维偏序','树状数组','最长链'],'不断取出没有更强者的妹子，求各自被取出的轮数。',
        '比i更强的点满足a、b都更大。i必须等所有更强点移除后才能取，因此t[i]=1+max(t[j])，j遍历同时严格大于它的点。按a从大到小处理，b离散化为反向排名，树状数组维护前缀最大值。查询当前b反向排名之前的位置，得到所有b更大点的最大轮数。',
        r'''int n; cin >> n; vector<array<int,3>> point(n); vector<int> coordinate; for (int i=0;i<n;i++) { cin >> point[i][0] >> point[i][1]; point[i][2]=i; coordinate.push_back(point[i][1]); } sort(coordinate.begin(),coordinate.end(),greater<int>()); sort(point.begin(),point.end(),[](auto a,auto b) { return a[0]>b[0]; }); vector<int> bit(n+1),answer(n); for (auto [a,b,id] : point) { int rank=lower_bound(coordinate.begin(),coordinate.end(),b,greater<int>())-coordinate.begin()+1; int value=1; for (int p=rank-1;p;p-=p&-p) value=max(value,bit[p]+1); answer[id]=value; for (int p=rank;p<=n;p+=p&-p) bit[p]=max(bit[p],value); } for (int x : answer) cout << x << '\n';''',
        '题目保证a和b各自互不相同，无需对同a批量延迟更新。输出恢复原输入顺序。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(17877,2000,['线段树','三角函数','懒标记'],'区间整数角度加，查询正弦之和。',
        '同时维护S=Σsin(a[i])和C=Σcos(a[i])。加角v后，由和角公式S新=S*cos(v)+C*sin(v)，C新=C*cos(v)−S*sin(v)。这是一组整体旋转，因此区间加可以累积成整数角度懒标记。标记保留整数，向子节点应用时再计算三角函数，减少逐次角度浮点累加误差。',
        r'''int n; cin >> n; vector<long double> sine(4*n+4),cosine(4*n+4); vector<long long> tag(4*n+4); auto build=[&](auto &&self,int u,int l,int r)->void { if (l==r) { long long x; cin >> x; sine[u]=sinl(x); cosine[u]=cosl(x); return; } int mid=(l+r)/2; self(self,u*2,l,mid); self(self,u*2+1,mid+1,r); sine[u]=sine[u*2]+sine[u*2+1]; cosine[u]=cosine[u*2]+cosine[u*2+1]; }; build(build,1,1,n); auto apply=[&](int u,long long v) { long double s=sinl(v),c=cosl(v),old=sine[u]; sine[u]=old*c+cosine[u]*s; cosine[u]=cosine[u]*c-old*s; tag[u]+=v; }; auto push=[&](int u) { if (tag[u]) { apply(u*2,tag[u]); apply(u*2+1,tag[u]); tag[u]=0; } }; auto update=[&](auto &&self,int u,int l,int r,int ql,int qr,long long v)->void { if (ql<=l && r<=qr) { apply(u,v); return; } push(u); int mid=(l+r)/2; if (ql<=mid) self(self,u*2,l,mid,ql,qr,v); if (qr>mid) self(self,u*2+1,mid+1,r,ql,qr,v); sine[u]=sine[u*2]+sine[u*2+1]; cosine[u]=cosine[u*2]+cosine[u*2+1]; }; auto query=[&](auto &&self,int u,int l,int r,int ql,int qr)->long double { if (ql<=l && r<=qr) return sine[u]; push(u); int mid=(l+r)/2; long double result=0; if (ql<=mid) result+=self(self,u*2,l,mid,ql,qr); if (qr>mid) result+=self(self,u*2+1,mid+1,r,ql,qr); return result; }; int m; cin >> m; cout << fixed << setprecision(1); while (m--) { int op,l,r; cin >> op >> l >> r; if (op==1) { long long v; cin >> v; update(update,1,1,n,l,r,v); } else cout << query(query,1,1,n,l,r) << '\n'; }''',
        '题目角度按弧度代入sin，不转换为度。更新两个统计量时保存旧S，避免使用已更新值。',
        floating_output=True,complexity=r'构建 $O(n)$，每次操作 $O(\log n)$，空间 $O(n)$。')
    put(14522,1900,['树状数组','贡献法','大整数'],'求所有子区间的逆序对数量总和。',
        '固定逆序对i<j、a[i]>a[j]，包含它的子区间左端有i种、右端有n−j+1种，贡献i*(n−j+1)。从左向右扫描j，用按值离散化的树状数组维护先前下标之和。所有已出现下标和减去≤a[j]的前缀和，就是满足a[i]>a[j]的下标总和，再乘n−j+1。\n\n最坏答案为四次规模，n至百万时超过64位，累加使用128位并自行输出。',
        r'''int n; cin >> n; vector<int> a(n),coordinate; for (int &x : a) cin >> x; coordinate=a; sort(coordinate.begin(),coordinate.end()); coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end()); Fenwick bit(coordinate.size()); long long previous=0; __int128 answer=0; for (int j=1;j<=n;j++) { int rank=lower_bound(coordinate.begin(),coordinate.end(),a[j-1])-coordinate.begin()+1; answer+=(__int128)(previous-bit.sum(rank))*(n-j+1); bit.add(rank,j); previous+=j; } string text; do { text.push_back('0'+answer%10); answer/=10; } while (answer); reverse(text.begin(),text.end()); cout << text;''',
        '相等不构成逆序对，必须减去≤当前值的全部贡献。树状数组存下标之和，不是出现次数。',
        declarations=BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(23054,2100,['根号分治','树状数组'],'给所有D倍数位置加K，询问区间和。',
        '按D大小分治。D≤B时，只累积small[D]，询问时该更新在[L,R]中的贡献是small[D]*(floor(R/D)−floor((L−1)/D))。D>B时，倍数至多N/B个，逐点加进树状数组；询问再加树状数组区间和。两类更新相互独立，可直接相加。代码取B约为sqrt(N log N)，平衡小D询问与大D逐点修改。',
        r'''int n,m; cin >> n >> m; int boundary=max(1,(int)sqrt(n*max(1.0,log2(n+1.0)))); boundary=min(boundary,n); vector<long long> small(boundary+1); Fenwick bit(n); while (m--) { int op,l; long long r; cin >> op >> l >> r; if (op==1) { if (l<=boundary) small[l]+=r; else for (int p=l;p<=n;p+=l) bit.add(p,r); } else { long long answer=bit.sum((int)r)-bit.sum(l-1); for (int d=1;d<=boundary;d++) answer+=small[d]*(r/d-(l-1)/d); cout << answer << '\n'; } }''',
        '多次小D更新要累加，不能覆盖。K至10^8、操作十万次，权值及区间和均用64位。',
        declarations=BIT,complexity=r'修改最坏 $O((N/B)\log N)$，询问 $O(B+\log N)$，空间 $O(N+B)$。')
    put(15162,2100,['线段树','最大子段和'],'单点修改，查询相邻奇偶交替的最大非空子段和。',
        '每段记录首尾奇偶、总和、整段是否交替、最大非空前缀/后缀/子段和。合并左右时，只有左尾与右首奇偶不同，才允许跨界连接。前缀向右延伸还要求左段整体交替，后缀同理。最大子段取左右答案，若可连接再与左最大后缀+右最大前缀比较。查询也按原顺序用相同合并函数。',
        r'''int n,m; cin >> n >> m; int size=1; while (size<n) size<<=1; vector<Node> tree(size*2); for (int i=0;i<n;i++) { long long x; cin >> x; tree[size+i]=leaf(x); } for (int u=size-1;u;u--) tree[u]=mergeNode(tree[u*2],tree[u*2+1]); while (m--) { int op,x; long long y; cin >> op >> x >> y; if (op==1) { int p=size+x-1; tree[p]=leaf(y); for (p>>=1;p;p>>=1) tree[p]=mergeNode(tree[p*2],tree[p*2+1]); } else { int l=size+x-1,r=size+(int)y; Node left,right; for (;l<r;l>>=1,r>>=1) { if (l&1) left=mergeNode(left,tree[l++]); if (r&1) right=mergeNode(tree[--r],right); } cout << mergeNode(left,right).best << '\n'; } }''',
        '不能允许空子段，否则全负区间会错误输出0。负数奇偶使用规范化余数；左右合并不可交换。',
        declarations=ALTERNATING,complexity=r'构建 $O(n)$，每次操作 $O(\log n)$，空间 $O(n)$。')
    put(19429,2000,['线段树','按位统计','异或懒标记'],'区间异或、区间和，数值和异或掩码至10^5。',
        '每个节点按二进制位记录1的个数。第b位异或1时，计数变成区间长度−原计数，其他位不变；懒标记按异或合并。数值小于2^17，记录17位即可。区间和是Σ count[b]*2^b。',
        r'''int n,m; cin >> n >> m; vector<array<int,17>> count(4*n+4); vector<int> tag(4*n+4); auto pull=[&](int u) { for (int b=0;b<17;b++) count[u][b]=count[u*2][b]+count[u*2+1][b]; }; auto build=[&](auto &&self,int u,int l,int r)->void { if (l==r) { int x; cin >> x; for (int b=0;b<17;b++) count[u][b]=x>>b&1; return; } int mid=(l+r)/2; self(self,u*2,l,mid); self(self,u*2+1,mid+1,r); pull(u); }; build(build,1,1,n); auto apply=[&](int u,int l,int r,int x) { for (int b=0;b<17;b++) if (x>>b&1) count[u][b]=r-l+1-count[u][b]; tag[u]^=x; }; auto push=[&](int u,int l,int r) { if (tag[u]) { int mid=(l+r)/2; apply(u*2,l,mid,tag[u]); apply(u*2+1,mid+1,r,tag[u]); tag[u]=0; } }; auto update=[&](auto &&self,int u,int l,int r,int ql,int qr,int x)->void { if (ql<=l && r<=qr) { apply(u,l,r,x); return; } push(u,l,r); int mid=(l+r)/2; if (ql<=mid) self(self,u*2,l,mid,ql,qr,x); if (qr>mid) self(self,u*2+1,mid+1,r,ql,qr,x); pull(u); }; auto query=[&](auto &&self,int u,int l,int r,int ql,int qr)->long long { if (ql<=l && r<=qr) { long long result=0; for (int b=0;b<17;b++) result+=1LL*count[u][b]*(1<<b); return result; } push(u,l,r); int mid=(l+r)/2; long long result=0; if (ql<=mid) result+=self(self,u*2,l,mid,ql,qr); if (qr>mid) result+=self(self,u*2+1,mid+1,r,ql,qr); return result; }; while (m--) { int op,l,r; cin >> op >> l >> r; if (op==2) { int k; cin >> k; update(update,1,1,n,l,r,k); } else cout << query(query,1,1,n,l,r) << '\n'; }''',
        '异或两次同一掩码应抵消，所以懒标记用xor。不要只记录区间异或值，它无法恢复区间和。',
        complexity=r'每次操作 $O(17\log n)$，空间 $O(17n)$。')
    put(14402,1600,['均值界','有序多重集'],'单点修改后求任意两点斜率(a[j]−a[i])/(j−i)的最大值。',
        '任意两点斜率等于它们之间相邻差分的平均数，不超过其中最大差分；最大相邻差分本身也对应合法两点。因此答案就是max(a[i+1]−a[i])。用multiset保存全部差分，修改a[p]时只删除并重算p−1、p两项。',
        r'''int n; cout << fixed << setprecision(2); while (cin >> n) { vector<long long> a(n); for (auto &x : a) cin >> x; multiset<long long> difference; for (int i=1;i<n;i++) difference.insert(a[i]-a[i-1]); int q; cin >> q; while (q--) { int p; long long y; cin >> p >> y; p--; if (p) difference.erase(difference.find(a[p]-a[p-1])); if (p+1<n) difference.erase(difference.find(a[p+1]-a[p])); a[p]=y; if (p) difference.insert(a[p]-a[p-1]); if (p+1<n) difference.insert(a[p+1]-a[p]); cout << (long double)*difference.rbegin() << '\n'; } }''',
        '最大值可以为负。multiset删除要用迭代器删除一份，不能把相同差分全部删掉。',
        floating_output=True,complexity=r'构建 $O(n\log n)$，每次修改 $O(\log n)$，空间 $O(n)$。')
    put(53370,1800,['树状数组','离散化','第k小'],'动态加入三维点，查询以原点为心覆盖至少k点的最小整数半径。',
        '每个点仅由距离平方d=x²+y²+z²决定。先读操作，离散化全部插入点的d，再按时间执行。树状数组维护距离频数，用二进制提升查第k小距离平方，最后输出ceil(sqrt(d))。k=0时半径0；已插入数量不足k时输出−1。',
        r'''int n; cin >> n; struct Operation { int type,k; long long distance; }; vector<Operation> operation; vector<long long> coordinate; for (int i=0;i<n;i++) { int op; cin >> op; if (op==1) { long long x,y,z; cin >> x >> y >> z; long long d=x*x+y*y+z*z; operation.push_back({1,0,d}); coordinate.push_back(d); } else { int k; cin >> k; operation.push_back({2,k,0}); } } sort(coordinate.begin(),coordinate.end()); coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end()); Fenwick bit(coordinate.size()); int total=0; for (auto op : operation) { if (op.type==1) { int rank=lower_bound(coordinate.begin(),coordinate.end(),op.distance)-coordinate.begin()+1; bit.add(rank,1); total++; } else if (!op.k) cout << 0 << '\n'; else if (op.k>total) cout << -1 << '\n'; else { int p=0; long long remaining=op.k; int step=1; while (step<=bit.n/2) step<<=1; for (;step;step>>=1) if (p+step<=bit.n && bit.tree[p+step]<remaining) { p+=step; remaining-=bit.tree[p]; } long long d=coordinate[p],r=sqrtl(d); while (r*r<d) r++; while (r>0 && (r-1)*(r-1)>=d) r--; cout << r << '\n'; } }''',
        '重复坐标也会增加能量，频数要累加。距离平方用64位，最后用整数平方校正浮点开方。',
        declarations=BIT,complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')


if __name__ == '__main__': run()
