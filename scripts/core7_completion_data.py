from core7_completion import add, FENWICK

MIN_TREE=r'''
struct MinTree{int n;vector<long long>value,tag;MinTree(const vector<long long>&a):n(a.size()),value(4*n),tag(4*n){build(1,0,n-1,a);}
void build(int p,int l,int r,const vector<long long>&a){if(l==r){value[p]=a[l];return;}int m=(l+r)/2;build(p*2,l,m,a);build(p*2+1,m+1,r,a);value[p]=min(value[p*2],value[p*2+1]);}
void apply(int p,long long x){value[p]+=x;tag[p]+=x;}void push(int p){if(tag[p]){apply(p*2,tag[p]);apply(p*2+1,tag[p]);tag[p]=0;}}
void add(int p,int l,int r,int a,int b,long long x){if(a<=l&&r<=b){apply(p,x);return;}push(p);int m=(l+r)/2;if(a<=m)add(p*2,l,m,a,b,x);if(b>m)add(p*2+1,m+1,r,a,b,x);value[p]=min(value[p*2],value[p*2+1]);}
long long query(int p,int l,int r,int a,int b){if(a<=l&&r<=b)return value[p];push(p);int m=(l+r)/2;long long ans=LLONG_MAX/4;if(a<=m)ans=min(ans,query(p*2,l,m,a,b));if(b>m)ans=min(ans,query(p*2+1,m+1,r,a,b));return ans;}
void add(int l,int r,long long x){add(1,0,n-1,l,r,x);}long long query(int l,int r){return query(1,0,n-1,l,r);}};
'''

add('P1937','按右端排序的区间容量贪心',
    '优先考虑结束较早的申请，并列时优先起点较晚的。若申请区间内剩余容量最小值大于零，就接受并把整段容量减一；线段树维护区间最小值和区间加。',
    '一头牛占用其申请区间内每个畜栏的一单位容量。结束更早的申请把资源释放得更早；右端相同而左端更晚的申请占用范围更小，更应优先。\n\n按右端递增、左端递减排序。若当前区间所有位置还有容量，接受它；否则至少一个位置已经满，当前申请无法在不撤销已有申请的前提下加入。交换论证表明，已有最优方案中若未选择当前最早结束的可行申请，可用它替换某个与其竞争的较晚结束申请，不减少最终数量；相同右端时较短范围也不会增加冲突。\n\n剩余容量是动态的，用懒标记线段树维护区间最小值。查询最小值大于零才执行区间减一，因此不会产生负容量。',
    '时间 O((n+m) log n+m log m)，空间 O(n+m)。','每个申请会占整段容量；并列右端优先更晚左端；查询大于零才接受。',r'''
int n,m;cin>>n>>m;vector<long long>a(n);for(auto&x:a)cin>>x;vector<pair<int,int>>requests(m);for(auto &[r,l]:requests){cin>>l>>r;l--;r--;}sort(requests.begin(),requests.end(),[](auto a,auto b){if(a.first!=b.first)return a.first<b.first;return a.second>b.second;});MinTree tree(a);int ans=0;for(auto [r,l]:requests)if(tree.query(l,r)>0){ans++;tree.add(l,r,-1);}cout<<ans<<'\n';
''',MIN_TREE)

add('CF1070C','扫描日期并维护最便宜的 k 个核心',
    '套餐在开始日加入、结束日次日删除。按价格维护当前可租核心数量与总费用，每天取价格最小的至多 k 个核心，用两棵树状数组做数量排名与费用前缀和。',
    '不同天的租赁决定互不影响，所以每天只需选择当天最便宜的 k 个核心；不足 k 个时全部租下。套餐中每个核心价格相同，可以把容量看成该价格的重复次数。\n\n把套餐转成两个事件：l 日增加 c 个价格 p 的核心，r+1 日删除 c 个。价格离散化后，用第一棵树状数组保存数量，第二棵保存数量乘价格。\n\n每天处理完事件，令 need=min(k,总数量)。在数量树上二进制提升，找第 need 个核心所在价格。更低价格全部买入，费用用前缀和取得；剩余 need−低价数量 个按临界价格购买。一个套餐只产生两次点更新，不能把每个核心展开存储。',
    '时间 O((n+m) log m)，空间 O(n+m)。','结束事件在 r+1；不足需求时租全部；数量与总费用用 long long。',r'''
int n,m;long long k;cin>>n>>k>>m;struct Offer{int l,r,c,p;};vector<Offer>offers(m);vector<int>prices;for(auto &x:offers){cin>>x.l>>x.r>>x.c>>x.p;prices.push_back(x.p);}sort(prices.begin(),prices.end());prices.erase(unique(prices.begin(),prices.end()),prices.end());vector<vector<pair<int,int>>>events(n+2);for(auto x:offers){int rank=lower_bound(prices.begin(),prices.end(),x.p)-prices.begin()+1;events[x.l].push_back({rank,x.c});events[x.r+1].push_back({rank,-x.c});}Fenwick count(prices.size()),cost(prices.size());long long total=0,answer=0;int step=1;while(step<=(int)prices.size()/2)step*=2;for(int day=1;day<=n;day++){for(auto [rank,delta]:events[day]){count.add(rank,delta);cost.add(rank,1LL*delta*prices[rank-1]);total+=delta;}long long need=min(k,total);if(!need)continue;int position=0;long long taken=0;for(int bit=step;bit;bit/=2){int next=position+bit;if(next<=(int)prices.size()&&taken+count.t[next]<need){position=next;taken+=count.t[next];}}answer+=cost.sum(position)+(need-taken)*prices[position];}cout<<answer<<'\n';
''',FENWICK)

add('CF1093G','枚举坐标符号后的线段树最大值',
    '曼哈顿距离等于所有正负号组合下线性差的最大值。对每种符号保存区间内点的最大线性值，答案为某种符号的最大值与相反符号的最大值之和。',
    '一维有 |x−y|=max(x−y,y−x)。对 k 维各自选择正负号，得到距离=max_s Σs_i(x_i−y_i)，其中 s_i∈{−1,+1}。\n\n固定符号 s，区间内最大点对差为 max F_s(point)−min F_s(point)。而 min F_s=−max F_(−s)，所以只需为全部 2^k 种符号维护最大值。查询后，遍历符号 mask，取 best[mask]+best[mask xor full] 的最大值。\n\n每个叶子由实际坐标计算全部符号值，父节点逐种取最大。单点修改更新一条祖先链，区间查询逐种合并。k<=5，符号组合至多三十二种，空间和时间可控。',
    '建树 O(n·2^k·k)，每次操作 O(2^k(log n+k))，空间 O(n·2^k)。','相反符号是 mask xor (2^k−1)；同一点配对允许得到零；最大值初始为负无穷。',r'''
int n,k;cin>>n>>k;int masks=1<<k,size=1;while(size<n)size*=2;vector<array<int,32>>tree(2*size);for(auto &v:tree)v.fill(INT_MIN/4);auto readPoint=[&](int p){vector<int>a(k);for(int &x:a)cin>>x;for(int mask=0;mask<masks;mask++){int value=0;for(int j=0;j<k;j++)value+=((mask>>j)&1)?a[j]:-a[j];tree[p][mask]=value;}};for(int i=0;i<n;i++)readPoint(size+i);auto pull=[&](int p){for(int mask=0;mask<masks;mask++)tree[p][mask]=max(tree[p*2][mask],tree[p*2+1][mask]);};for(int p=size-1;p;p--)pull(p);int q;cin>>q;while(q--){int op,l;cin>>op>>l;if(op==1){int p=size+l-1;readPoint(p);for(p/=2;p;p/=2)pull(p);}else{int r;cin>>r;array<int,32>best;best.fill(INT_MIN/4);for(l+=size-1,r+=size;l<r;l/=2,r/=2){if(l&1){for(int mask=0;mask<masks;mask++)best[mask]=max(best[mask],tree[l][mask]);l++;}if(r&1){r--;for(int mask=0;mask<masks;mask++)best[mask]=max(best[mask],tree[r][mask]);}}int answer=0;for(int mask=0;mask<masks;mask++)answer=max(answer,best[mask]+best[mask^(masks-1)]);cout<<answer<<'\n';}}
''')

add('P3924','将路径期望拆成各叶子的固定系数',
    '深度为 d 的节点被走到的概率为 2^(−d)。一个叶子数值会出现在其所有祖先区间和中，系数为 1+1/2+…+1/2^depth=2−2^(−depth)。预处理系数前缀和，区间加直接更新总期望。',
    '每个线段树节点的值是它区间内叶子值之和。随机走树时，某节点对期望的贡献是“到达概率×节点值”。把求和顺序交换，改为固定某个叶子的 a[i]，它会被所有祖先节点包含。\n\n根深度为零，每次左右等概率，所以祖先深度 d 的到达概率为 1/2^d。叶深 D 的总系数为 Σ(d=0..D)2^(−d)=2−2^(−D)。这个系数只依赖分割方式，不随 a[i] 或修改改变。\n\n取所有叶子的最大深度 H，把系数同时乘 2^H 转成整数 weight[i]=2^(H+1)−2^(H−D)。维护加权和 V=Σa[i]weight[i]；区间加 x 只需 V+=x·Σ区间weight。系数前缀和使每次修改成为 O(1)。\n\n输出时再乘 qwq 并除以 2^H。按题目保证最终是整数，程序用 __int128 保存累计乘积，避免多次大范围加法后的中间溢出。',
    '预处理 O(n)，每次修改 O(1)，空间 O(n)。','使用题目给出的按中点分割；叶深不一定全相等；中间加权和用 __int128。',r'''
int n,m;long long denominator;cin>>n>>m>>denominator;int h=0;while((1<<h)<n)h++;long long base=1LL<<h;vector<long long>a(n+1),weight(n+1),prefix(n+1);for(int i=1;i<=n;i++)cin>>a[i];function<void(int,int,int)>build=[&](int l,int r,int depth){if(l==r){weight[l]=2*base-(1LL<<(h-depth));return;}int mid=(l+r)/2;build(l,mid,depth+1);build(mid+1,r,depth+1);};build(1,n,0);__int128 value=0;for(int i=1;i<=n;i++){prefix[i]=prefix[i-1]+weight[i];value+=(__int128)a[i]*weight[i];}auto print=[](__int128 x){if(x<0){cout<<'-';x=-x;}string s;do{s.push_back('0'+x%10);x/=10;}while(x);reverse(s.begin(),s.end());cout<<s<<'\n';};while(m--){int l,r;long long x;cin>>l>>r>>x;value+=(__int128)x*(prefix[r]-prefix[l-1]);print(value*denominator/base);}
''')

add('CF838B','Euler 子树上的距离和返回根最小值',
    '从 u 到 v，若 v 在 u 子树内就直接下行；否则先在 u 子树中找最便宜的回根出口，再从根到 v。线段树维护 dist[x]+back[x]，树边修改对应整个子树加，回根边修改对应单点加。',
    '所有普通树边都从根向下，所以不经过根时，只能到达当前点的后代。若 v 是 u 后代，直接路径长为 dist[v]−dist[u]，任何绕根路线都更长。\n\n否则必须在 u 的某个后代 x 处走回根边，再从根到 v，费用为 dist[x]−dist[u]+back[x]+dist[v]。因此只需查询 u 子树内 dist[x]+back[x] 的最小值。Euler 序把子树变成连续区间。\n\n修改一条树边增加 delta，会让其孩子整个子树的 dist 同增 delta，于是线段树对应区间加 delta；修改回根边只使一个点的 back 改变，做单点加。当前 dist[u] 可由该点维护值减去 back[u] 得到。\n\nEuler 遍历用显式栈，避免深链递归；区间加与区间最小值用懒标记线段树，所有路长使用 long long。',
    '时间 O((n+q) log n)，空间 O(n)。','前 n−1 条是向下树边；回根边按实际起点映射；修改后查询使用当前距离。',r'''
int n,q;cin>>n>>q;int m=2*n-2;vector<int>from(m),to(m);vector<long long>w(m),back(n),distance(n);vector<vector<pair<int,int>>>g(n);for(int i=0;i<m;i++){cin>>from[i]>>to[i]>>w[i];from[i]--;to[i]--;if(i<n-1)g[from[i]].push_back({to[i],i});else back[from[i]]=w[i];}vector<int>tin(n),tout(n);int timer=0;vector<pair<int,int>>stack={{0,0}};tin[0]=timer++;while(!stack.empty()){int v=stack.back().first;int &next=stack.back().second;if(next<(int)g[v].size()){auto [u,id]=g[v][next++];distance[u]=distance[v]+w[id];tin[u]=timer++;stack.push_back({u,0});}else{tout[v]=timer-1;stack.pop_back();}}vector<long long>initial(n);for(int v=0;v<n;v++)initial[tin[v]]=distance[v]+back[v];MinTree tree(initial);while(q--){int op,a;long long b;cin>>op>>a>>b;a--;if(op==1){long long delta=b-w[a];w[a]=b;if(a<n-1)tree.add(tin[to[a]],tout[to[a]],delta);else{int v=from[a];back[v]+=delta;tree.add(tin[v],tin[v],delta);}}else{int v=b-1;long long da=tree.query(tin[a],tin[a])-back[a],db=tree.query(tin[v],tin[v])-back[v];if(tin[a]<=tin[v]&&tin[v]<=tout[a])cout<<db-da<<'\n';else cout<<tree.query(tin[a],tout[a])-da+db<<'\n';}}
''',MIN_TREE)

add('UVA11895','最大概率堆与精确分数更新',
    '之前结果不公开，一个袋子被选 r 次后，下次中奖概率为 (l/t)((t−1)/t)^r。每个人都会选择当前概率最大的袋子，用堆取最大并更新，取第 K 次的概率。',
    '每个袋子始终保留 t 个信封，中奖后只是拿走奖票，空信封仍放回。对其中一张初始奖票，它在前 r 次抽取中没有被抽中的概率为 ((t−1)/t)^r，所以剩余奖票期望为 l 乘这个值，下次中奖概率再除以 t。\n\n前面学生的结果不公开，后续学生不能根据具体中奖结果更新袋子，只能根据它已被抽了多少次计算上述无条件概率。每人为了最大化自己的中奖概率，都会选当前概率最大者；抽一次后，该袋子概率乘 (t−1)/t。\n\n把各袋概率放进最大堆，重复 K−1 次取顶并更新，第 K 次堆顶就是答案。用约分后的有理数保存概率，比较用 __int128 交叉相乘，避免接近概率的浮点误排。更新先交叉约分，再相乘。题目保证本人与所有前驱实际选中的概率分子分母都在 32 位范围，更新后的候选使用六十四位保存。',
    '时间 O((N+K) log N)，空间 O(N)。','信封放回但奖票不放回；前面结果不可见；比较分数用宽整数；最后约分输出。',r'''
int tests;cin>>tests;while(tests--){int n,k;cin>>n>>k;priority_queue<Bag,vector<Bag>,Compare>q;for(int i=0;i<n;i++){long long t,l;cin>>t>>l;long long g=gcd(t,l);q.push({l/g,t/g,t});}for(int step=1;step<k;step++){Bag b=q.top();q.pop();long long a=b.total-1,d=b.total,g=gcd(a,b.denominator);a/=g;b.denominator/=g;g=gcd(d,b.numerator);d/=g;b.numerator/=g;b.numerator*=a;b.denominator*=d;if(!b.numerator)b.denominator=1;q.push(b);}auto b=q.top();long long g=gcd(b.numerator,b.denominator);cout<<b.numerator/g<<'/'<<b.denominator/g<<'\n';}
''',r'''
struct Bag{long long numerator,denominator,total;};struct Compare{bool operator()(const Bag&a,const Bag&b)const{return (__int128)a.numerator*b.denominator<(__int128)b.numerator*a.denominator;}};
''')

MO_ORDER=r'''
struct Query{int l,r,id;};vector<Query>queries(q);for(int i=0;i<q;i++){cin>>queries[i].l>>queries[i].r;queries[i].id=i;}
int block=max(1,(int)sqrt(n));sort(queries.begin(),queries.end(),[&](Query a,Query b){if(a.l/block!=b.l/block)return a.l<b.l;return (a.l/block)&1?a.r>b.r:a.r<b.r;});
'''

add('P4109','枚举十进制末尾零的数量',
    '枚举 10 的幂作为末尾零因子。对每种因子，检查区间内最小的倍数，以及去零后末位为 5 的最小倍数，比较真实荒谬度，并列取最小价格。',
    '去掉末尾零后，荒谬度只取决于剩余位数，以及最后一位是不是五。设价格是 q·10^k，枚举 k 后，可行 q 落在一个整数区间。\n\n在同一 k 下，最小 q 的位数不会比其它候选更大，它给出了普通偶数荒谬度的最优候选。若末位为五可能降低一，则还需检查不小于下界且模十为五的最小 q；更大的同类 q 不会有更少位数，也不会有更小价格。\n\n对这两类候选都重新按题意去零计算荒谬度，避免它实际上带有更多尾零时误判。所有 k 的最优候选中，先比较荒谬度，再比较价格。上界至多十亿，只有十种幂需要考虑。',
    '每组时间 O(log² R)，空间 O(1)。','候选必须在 [L,R]；并列取更小；最小倍数使用向上取整。',r'''
int tests;cin>>tests;while(tests--){long long l,r;cin>>l>>r;int best=INT_MAX;long long answer=l;auto test=[&](long long p){if(p<l||p>r)return;long long x=p;while(x%10==0)x/=10;int score=2*(int)to_string(x).size()-(x%10==5);if(score<best||(score==best&&p<answer)){best=score;answer=p;}};for(long long power=1;power<=r;power*=10){long long q=(l+power-1)/power;test(q*power);long long five=q+(5-q%10+10)%10;test(five*power);}cout<<answer<<'\n';}
''')

add('P4863','固定除数计算全部商的和',
    '用前缀函数 F(N) 表示 1 到 N 的总愉悦值。交换求和顺序后，对每个 j 计算 Σ(i=1..N) floor(i/j)，再按 j 奇偶加减；区间答案为 F(B)−F(A−1)。',
    '内层贡献的符号只取决于 j，因此可以把二重循环交换：固定 j，计算它对所有 i<=N 的贡献。前面不足 j 的 i 商为零，不必另外限制 i>=j。\n\n令 q=N/j。商 1 到 q−1 各出现 j 次，最后的 q 出现 N−qj+1 次，所以商之和为 j·q(q−1)/2+q(N−qj+1)。j 为偶数时加入，为奇数时减去。\n\n每个 j 只进行常数次运算，前缀计算从平方降为线性。最后用两个前缀相减得到闭区间 [A,B] 的结果。中间乘积使用 long long，负答案正常保留。',
    '时间 O(B)，空间 O(1)。','(-1)^j 对奇数是负；F(0)=0；乘法先用六十四位。',r'''
long long a,b;cin>>a>>b;auto solve=[](long long n){long long ans=0;for(long long j=1;j<=n;j++){long long q=n/j;long long value=j*q*(q-1)/2+q*(n-q*j+1);ans+=(j%2?-value:value);}return ans;};cout<<solve(b)-solve(a-1)<<'\n';
''')

add('CF877F','有方向的前缀和莫队',
    '数学书取正值、经济书取负值，子段条件化为前缀差等于 k。莫队维护前缀下标区间 [l−1,r]，左右端加入时分别查询 v+k 与 v−k，保持下标先后关系。',
    '把每本数学书的问题数记为正，经济书记为负。子段 [x,y] 符合条件当且仅当 prefix[y]−prefix[x−1]=k。与异或不同，减法有方向，不能把两个前缀值当作无序配对。\n\n在右端加入值 v，它是较晚的前缀，需要已有较早前缀等于 v−k；在左端加入值 v，它是较早的前缀，需要较晚值等于 v+k。删除时先减少自身频数，再按相同方向减去配对数，以处理 k=0。\n\n前缀和可达十的十四次方，用 long long。把所有前缀及其加减 k 的值统一离散化，提前记录三个索引，端点移动时仅访问数组。每个原子段对应一对不同且有序的前缀下标，既不遗漏也不重复。',
    '时间 O((n+q)sqrt n+n log n)，空间 O(n+q)。','左右端配对公式不同；包含 prefix[0]；前缀和与答案均为六十四位。',r'''
int n;long long k;cin>>n>>k;vector<int>type(n+1);for(int i=1;i<=n;i++)cin>>type[i];vector<long long>p(n+1),values;for(int i=1;i<=n;i++){long long x;cin>>x;p[i]=p[i-1]+(type[i]==1?x:-x);}for(long long x:p){values.push_back(x);values.push_back(x-k);values.push_back(x+k);}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());vector<int>id(n+1),minus(n+1),plus(n+1);for(int i=0;i<=n;i++){id[i]=lower_bound(values.begin(),values.end(),p[i])-values.begin();minus[i]=lower_bound(values.begin(),values.end(),p[i]-k)-values.begin();plus[i]=lower_bound(values.begin(),values.end(),p[i]+k)-values.begin();}int q;cin>>q;
'''+MO_ORDER+r'''
vector<int>freq(values.size());vector<long long>ans(q);long long current=0;int l=0,r=-1;auto add=[&](int i,bool left){current+=freq[left?plus[i]:minus[i]];freq[id[i]]++;};auto remove=[&](int i,bool left){freq[id[i]]--;current-=freq[left?plus[i]:minus[i]];};for(auto x:queries){x.l--;while(l>x.l)add(--l,true);while(r<x.r)add(++r,false);while(l<x.l)remove(l++,true);while(r>x.r)remove(r--,false);ans[x.id]=current;}for(long long x:ans)cout<<x<<'\n';
''')
for pid,kind in [('CF220B','equal'),('P1494','pairs'),('P2709','squares')]:
    start='int n,q;cin>>n>>q;'
    if kind=='squares':start+='int k;cin>>k;'
    body=start+r'''
vector<int>a(n+1),values;for(int i=1;i<=n;i++){cin>>a[i];values.push_back(a[i]);}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());for(int i=1;i<=n;i++)a[i]=lower_bound(values.begin(),values.end(),a[i])-values.begin();
'''+MO_ORDER+r'''
vector<int>freq(values.size());vector<long long>answer(q),length(q);long long current=0;
'''
    if kind=='equal':body+=r'''auto change=[&](int p,int delta){int x=a[p];current-=freq[x]==values[x];freq[x]+=delta;current+=freq[x]==values[x];};'''
    elif kind=='pairs':body+=r'''auto change=[&](int p,int delta){int &c=freq[a[p]];current-=1LL*c*(c-1);c+=delta;current+=1LL*c*(c-1);};'''
    else:body+=r'''auto change=[&](int p,int delta){int &c=freq[a[p]];current-=1LL*c*c;c+=delta;current+=1LL*c*c;};'''
    body+=r'''
int l=1,r=0;for(auto query:queries){while(l>query.l)change(--l,1);while(r<query.r)change(++r,1);while(l<query.l)change(l++,-1);while(r>query.r)change(r--,-1);answer[query.id]=current;length[query.id]=query.r-query.l+1;}
'''
    if kind=='pairs':body+=r'''for(int i=0;i<q;i++){long long a=answer[i],b=length[i]*(length[i]-1);if(a==0)cout<<"0/1\n";else{long long g=gcd(a,b);cout<<a/g<<'/'<<b/g<<'\n';}}'''
    else:body+=r'''for(long long x:answer)cout<<x<<'\n';'''
    specific={
        'equal':('区间内出现次数等于数值的种类数','一个值 x 的贡献是 freq[x]==x。修改它的频数前，先减去旧贡献，修改后再加入新贡献。其它数的贡献完全不变。', '数值和压缩下标不能混淆；值大于 n 时永远不会贡献。'),
        'pairs':('同色袜子的抽取概率','若一种颜色有 c 只袜子，有序抽取两只的同色方案为 c(c−1)。全部有序方案为 len(len−1)，各颜色贡献之和除以这个分母就是所求概率。长度一或分子零时输出 0/1；其它情况用 gcd 约分。','分子分母都用 long long；长度为一输出 0/1；不同袜子按编号区分。'),
        'squares':('频数平方和','某个数的频数从 c 改为 c+delta 时，它的贡献从 c² 变为 (c+delta)²。先减旧平方再加新平方，即可在常数时间更新整个答案。','平方运算先转 long long；k 是值域上限，不是查询数量。'),
    }[kind]
    add(pid,'莫队维护'+specific[0],
        '把询问离线排序，让相邻询问的区间端点缓慢移动。维护每个值的出现次数，每次只增删一个位置，常数时间更新答案。'+specific[1],
        '所有询问都只读取同一份静态数组，可以改变处理顺序，再按原编号输出。把左端点分成长度约 sqrt(n) 的块，同块内按右端点排序；奇偶块交替排序方向可减少右端点回跳。\n\n维护当前闭区间 [l,r]，初始为空。要到达下一个区间，移动四个边界，每步只加入或删除一个位置，因此只有一个值的频数发生变化。'+specific[1]+'\n\n数组值先离散化，频数按压缩下标保存，原数值另存以便需要时比较。左右端点总移动量为 O((n+q)sqrt(n))，每步修改是 O(1)。结果存到询问的原始编号位置。',
        '时间 O((n+q)sqrt n)，空间 O(n+q)。',specific[2],body)

for pid in ['P4462','CF617E']:
    add(pid,'前缀异或上的莫队配对',
        '定义前缀异或 p，子区间异或等于 k 等价于两个前缀值异或为 k。把 [l,r] 改为前缀下标区间 [l−1,r]，用莫队维护其中符合条件的不同下标对数。',
        '前缀异或满足 a[x] xor … xor a[y]=p[y] xor p[x−1]。因此原查询 [l,r] 中的每个非空子区间，唯一对应前缀下标区间 [l−1,r] 内的一对不同下标。异或关系对两端对称，每对下标按原位置顺序恰好对应一个子区间。\n\n维护当前前缀值频数。加入一个值 v 时，它与已有的 v xor k 各形成一对，所以先把该频数加到答案，再增加 v 的频数。删除时顺序相反：先减少 v 的频数，再减去剩下的 v xor k 数量。k=0 时这种顺序能避免将下标与自己配对。\n\n把所有 p[i] 与 p[i] xor k 一起离散化，避免依赖原始值域上界。莫队只移动区间端点，答案使用六十四位整数。',
        '时间 O((n+q)sqrt n+n log n)，空间 O(n+q)。','左端要减一；包含 p[0]=0；删除先减频次，尤其注意 k=0。',r'''
int n,q,k;cin>>n>>q>>k;vector<int>p(n+1),values;for(int i=1,x;i<=n;i++){cin>>x;p[i]=p[i-1]^x;}for(int v:p){values.push_back(v);values.push_back(v^k);}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());vector<int>id(n+1),partner(n+1);for(int i=0;i<=n;i++){id[i]=lower_bound(values.begin(),values.end(),p[i])-values.begin();partner[i]=lower_bound(values.begin(),values.end(),p[i]^k)-values.begin();}
'''+MO_ORDER+r'''
vector<int>freq(values.size());vector<long long>ans(q);long long current=0;auto add=[&](int i){current+=freq[partner[i]];freq[id[i]]++;};auto remove=[&](int i){freq[id[i]]--;current-=freq[partner[i]];};int l=0,r=-1;for(auto x:queries){x.l--;while(l>x.l)add(--l);while(r<x.r)add(++r);while(l<x.l)remove(l++);while(r>x.r)remove(r--);ans[x.id]=current;}for(long long x:ans)cout<<x<<'\n';
''')

add('P3901','前一次出现位置的前缀最大值',
    '记录每个位置的值上次出现在哪里。令 bad[r] 是前 r 项中这些前驱位置的最大值，则 [l,r] 全部不同当且仅当 bad[r]<l。',
    '区间内出现重复，等价于存在某个位置 i，它与相同值的前一次出现位置 pre[i] 都落在 [l,r] 中，即 l<=pre[i]<i<=r。\n\n维护 bad[r]=max(pre[1],…,pre[r])。若 bad[r]>=l，产生该最大值的位置 i 一定大于 pre[i]、不超过 r，因此它与前驱都在查询区间内，存在重复。若 bad[r]<l，所有位置的同值前驱都在区间外，不可能出现重复。\n\n读取数组时用 last[value] 得到前驱，再更新 bad 的前缀最大值。每次查询只比较一个整数，不需要莫队或线段树。',
    '时间 O(n+q)，空间 O(n)。','比较是严格小于 l；last 的零表示从未出现。',r'''
int n,q;cin>>n>>q;vector<int>last(n+1),bad(n+1);for(int i=1;i<=n;i++){int x;cin>>x;bad[i]=max(bad[i-1],last[x]);last[x]=i;}while(q--){int l,r;cin>>l>>r;cout<<(bad[r]<l?"Yes":"No")<<'\n';}
''')

add('SP3267','按右端点扫描的最近出现标记',
    '按右端点排序询问。扫描数组时，每个值只在它最近出现的位置放一个 1，旧位置清零。树状数组查询 [l,r] 的标记和，就是不同值数量。',
    '固定已扫描前缀 1 到 r，对于每个出现过的值，仅保留最后一次出现位置的标记。某个值在 [l,r] 出现，当且仅当它在前缀内的最后位置不小于 l。因此查询区间的标记数恰好等于不同值数。\n\n按 r 从小到大处理询问，每向右扫描一个数，就把它旧位置的标记减一、新位置加一，再更新 last。树状数组支持单点加减与前缀求和，sum(r)−sum(l−1) 得到区间标记数。\n\n询问保存原编号，离线排序只改变处理次序。数值最高一百万，可以直接用 last 数组；标记树按下标长度 n 开空间。',
    '时间 O((n+q) log n+q log q)，空间 O(n+q+A)。','旧标记要删除；last 按数值，树状数组按位置；按原询问顺序输出。',r'''
int n;cin>>n;vector<int>a(n+1);int limit=0;for(int i=1;i<=n;i++){cin>>a[i];limit=max(limit,a[i]);}int q;cin>>q;struct Query{int l,r,id;};vector<Query>queries(q);for(int i=0;i<q;i++){cin>>queries[i].l>>queries[i].r;queries[i].id=i;}sort(queries.begin(),queries.end(),[](Query a,Query b){return a.r<b.r;});vector<int>last(limit+1),ans(q);Fenwick bit(n);int next=1;for(auto x:queries){while(next<=x.r){int value=a[next];if(last[value])bit.add(last[value],-1);bit.add(next,1);last[value]=next;next++;}ans[x.id]=bit.sum(x.r)-bit.sum(x.l-1);}for(int x:ans)cout<<x<<'\n';
''',FENWICK)

add('SP1684','有序数组的等值连续段合并',
    '因为数组有序，同一值只出现在一个连续段。线段树维护首尾值、等值前后缀长度和最高频次；合并时仅边界相同才产生跨界段。',
    '如果数组无序，最高频次不能仅靠左右段的最大频次合并；但本题数组非降，同值必连续，因此最高频次就是最长等值连续段。\n\n节点记录长度、首尾值、最长等值前缀、后缀以及最佳段。合并时，若左末值等于右首值，跨界候选为左后缀加右前缀；否则最佳只可能完全位于一侧。前缀只有在整个左段同值且边界相同时才能延长，后缀同理。\n\n区间查询保持从左到右的顺序。空节点长度为零，合并时直接返回另一边，方便处理查询边界。输入以 n=0 结束。',
    '每组建树 O(n)，每次查询 O(log n)，空间 O(n)。','依赖数组有序；查询必须保持拼接次序；n=0 结束。',r'''
int n,q;while(cin>>n&&n){cin>>q;int size=1;while(size<n)size*=2;vector<Node>t(2*size);for(int i=0;i<n;i++){int x;cin>>x;t[size+i]={1,x,x,1,1,1};}for(int p=size-1;p;p--)t[p]=merge(t[p*2],t[p*2+1]);while(q--){int l,r;cin>>l>>r;Node a,b;for(l+=size-1,r+=size;l<r;l/=2,r/=2){if(l&1)a=merge(a,t[l++]);if(r&1)b=merge(t[--r],b);}cout<<merge(a,b).best<<'\n';}}
''',r'''
struct Node{int len=0,first=0,last=0,pre=0,suf=0,best=0;};
Node merge(Node a,Node b){if(!a.len)return b;if(!b.len)return a;Node c={a.len+b.len,a.first,b.last,a.pre,b.suf,max(a.best,b.best)};if(a.last==b.first){c.best=max(c.best,a.suf+b.pre);if(a.pre==a.len)c.pre=a.len+b.pre;if(b.suf==b.len)c.suf=b.len+a.suf;}return c;}
''')

for pid,singleton in [('SP30906',True),('UVA12345',False)]:
    parse=r'''int op,l,r;cin>>op>>l>>r;if(op==1){changes.push_back({l,working[l],r});working[l]=r;}else queries.push_back({l,r,(int)changes.size(),(int)queries.size()});''' if singleton else r'''char op;int l,r;cin>>op>>l>>r;if(op=='M'){changes.push_back({l,working[l],r});working[l]=r;}else queries.push_back({l,r-1,(int)changes.size(),(int)queries.size()});'''
    change=r'''current-=freq[x]==1;freq[x]+=delta;current+=freq[x]==1;''' if singleton else r'''current-=freq[x]>0;freq[x]+=delta;current+=freq[x]>0;'''
    add(pid,'带修改的三维莫队',
        '把每次查询记录为左端、右端和此前修改次数。离线排序后，移动两个区间端点以及时间指针，维护当前各值频数，'+('统计频数恰为 1 的值数。' if singleton else '统计频数大于 0 的值数。查询使用从 0 开始的左闭右开区间。'),
        '普通莫队要求数组不变，本题增加了单点修改，所以还需要时间维度。先顺序读入操作，为每次修改保存位置、修改前的值与修改后的值；每次查询记录此前已有多少次修改。\n\n按左块、右块、时间排序，块长取约 n^(2/3)。处理查询时，先把当前数组推进或回退到它对应的时间；若被改位置在当前区间中，先删除旧值贡献，赋新值后再加入新贡献。若在区间之外，只改数组。随后像普通莫队一样移动左右端点。\n\n'+('贡献函数是 [freq==1]。每次修改一个频数，先减去它旧的单次出现贡献，再加上新贡献。' if singleton else '贡献函数是 [freq>0]。原题模仿 Python 切片，Q L R 包含 L 而不含 R，读入后转成闭区间 [L,R−1]，下标仍从零开始。')+'\n\n在读入时使用 working 数组保存修改前的值，真正执行莫队时另用初始数组。重复修改同一位置也能够准确撤销。',
        '时间 O((n+q)·n^(2/3))，空间 O(n+q+A)。','修改须保存旧值；时间撤销要对称；下标从 0 开始。',r'''
int n,q;cin>>n>>q;vector<int>a(n),working;for(int &x:a)cin>>x;working=a;vector<Change>changes;vector<Query>queries;for(int i=0;i<q;i++){
'''+parse+r'''}
int limit=0;for(int x:a)limit=max(limit,x);for(auto c:changes)limit=max(limit,c.after);int block=max(1,(int)pow(n,2.0/3));sort(queries.begin(),queries.end(),[&](Query a,Query b){if(a.l/block!=b.l/block)return a.l<b.l;if(a.r/block!=b.r/block)return a.r<b.r;return a.time<b.time;});vector<int>freq(limit+1),answer(queries.size());int current=0,l=0,r=-1,time=0;
auto adjust=[&](int x,int delta){'''+change+r'''};
auto apply=[&](Change c,bool forward){if(l<=c.position&&c.position<=r)adjust(a[c.position],-1);a[c.position]=forward?c.after:c.before;if(l<=c.position&&c.position<=r)adjust(a[c.position],1);};
for(auto query:queries){while(time<query.time){apply(changes[time],true);time++;}while(time>query.time){time--;apply(changes[time],false);}while(l>query.l)adjust(a[--l],1);while(r<query.r)adjust(a[++r],1);while(l<query.l)adjust(a[l++],-1);while(r>query.r)adjust(a[r--],-1);answer[query.id]=current;}for(int x:answer)cout<<x<<'\n';
''',r'''
struct Change{int position,before,after;};struct Query{int l,r,time,id;};
''')

add('P1204','排序后合并覆盖区间',
    '把工作区间按左端点排序，维护当前连续覆盖的左右端点。相交或首尾相接就合并，出现空隙时结算最长忙碌和空闲时间。',
    '同一时刻多名农夫工作仍只计一段忙碌时间，不能累加每个人的工作时长。排序后，尚未处理的区间左端不会比当前区间更早，因此只需维护最后一段合并区间。\n\n若下一区间左端不大于当前右端，覆盖连续，右端更新为两者较大值。否则中间存在长度为新左端减旧右端的空闲段；先结算旧忙碌长度，再开始新的忙碌段。扫描结束还需结算最后一段。\n\n只计算第一次开始工作到最后一次结束之间的空闲，前后无限长的无工作时间不计入。首尾相接没有正长度空隙，应当合并。',
    '时间 O(n log n)，空间 O(n)。','相接时合并；不要漏结算最后一段；时间长度是右端减左端。',r'''
int n;cin>>n;vector<pair<int,int>>a(n);for(auto &[l,r]:a)cin>>l>>r;sort(a.begin(),a.end());int l=a[0].first,r=a[0].second,busy=0,idle=0;for(int i=1;i<n;i++){if(a[i].first<=r)r=max(r,a[i].second);else{busy=max(busy,r-l);idle=max(idle,a[i].first-r);tie(l,r)=a[i];}}busy=max(busy,r-l);cout<<busy<<' '<<idle<<'\n';
''')

add('P10288','按数值记录出现位置',
    '把每个值的出现下标按顺序存入列表。查询 x 在 [l,r] 出现几次，就是位置列表中不超过 r 的个数减去小于 l 的个数。',
    '序列不会修改，同一数值的出现位置完全固定。读取第 i 个数 x 时，把 i 追加到 x 的位置列表；由于按下标递增读取，每个列表天然有序。\n\n例如 x 出现在位置 2、5、8，查询 [3,8] 时，合法位置是 5、8。lower_bound(l) 找到第一个不小于 l 的位置，upper_bound(r) 找到第一个大于 r 的位置，它们之间的元素恰好落在闭区间内，迭代器相减即为次数。\n\n数值可达十亿，不能按最大值开数组。用 map 将数值映射到 vector。查不到 x 时直接回答零，避免为大量未出现的查询值创建无用列表。每组测试都重新建立映射。',
    '建表 O(n log n)，每次查询 O(log n)，空间 O(n)。','查询是闭区间；不存在的值回答 0；每组清空位置表。',r'''
int t;cin>>t;while(t--){int n;cin>>n;map<int,vector<int>>pos;for(int i=1;i<=n;i++){int x;cin>>x;pos[x].push_back(i);}int q;cin>>q;while(q--){int l,r,x;cin>>l>>r>>x;auto it=pos.find(x);if(it==pos.end())cout<<0<<'\n';else{auto &v=it->second;cout<<upper_bound(v.begin(),v.end(),r)-lower_bound(v.begin(),v.end(),l)<<'\n';}}}
''')

add('P1531','单点更新与区间最大值',
    '用线段树保存每段的最大成绩。修改沿叶子到根更新最大值，查询把目标区间拆成若干完整节点并取最大值。',
    '一个区间的最大值等于左右两个子区间最大值中的较大者，因此可以用二叉树分治维护。叶子存一个学生的成绩，父节点存两个孩子的最大值。\n\n修改某个成绩时，只有包含这个位置的节点会改变，从叶子一路重新计算到根。查询 [l,r] 时，完整落在范围内的节点可直接使用；其它节点继续分解。代码采用迭代线段树，把闭区间转换为左闭右开区间，左侧结果和右侧结果最终一起取最大值。\n\n输入包含多组数据，直到文件结束。U 表示将成绩改成给定值，不是增加；Q 的两个参数是查询端点。',
    '建树 O(n)，每次操作 O(log n)，空间 O(n)。','更新是赋值；输入到 EOF；最大值查询的空段使用最小整数。',r'''
int n,m;while(cin>>n>>m){int size=1;while(size<n)size*=2;vector<int>t(2*size,INT_MIN);for(int i=0;i<n;i++)cin>>t[size+i];for(int i=size-1;i;i--)t[i]=max(t[i*2],t[i*2+1]);while(m--){char op;int x,y;cin>>op>>x>>y;if(op=='U'){int p=size+x-1;t[p]=y;for(p/=2;p;p/=2)t[p]=max(t[p*2],t[p*2+1]);}else{if(x>y)swap(x,y);int ans=INT_MIN;for(int l=size+x-1,r=size+y;l<r;l/=2,r/=2){if(l&1)ans=max(ans,t[l++]);if(r&1)ans=max(ans,t[--r]);}cout<<ans<<'\n';}}}
''')

FLIP=r'''
struct Tree{int n;vector<int>sum;vector<char>tag;Tree(int n):n(n),sum(4*n),tag(4*n){}
void apply(int p,int l,int r){sum[p]=r-l+1-sum[p];tag[p]^=1;}
void push(int p,int l,int r){if(tag[p]&&l<r){int m=(l+r)/2;apply(p*2,l,m);apply(p*2+1,m+1,r);tag[p]=0;}}
void change(int p,int l,int r,int a,int b){if(a<=l&&r<=b){apply(p,l,r);return;}push(p,l,r);int m=(l+r)/2;if(a<=m)change(p*2,l,m,a,b);if(b>m)change(p*2+1,m+1,r,a,b);sum[p]=sum[p*2]+sum[p*2+1];}
int query(int p,int l,int r,int a,int b){if(a<=l&&r<=b)return sum[p];push(p,l,r);int m=(l+r)/2,ans=0;if(a<=m)ans+=query(p*2,l,m,a,b);if(b>m)ans+=query(p*2+1,m+1,r,a,b);return ans;}};
'''
add('P2846','区间翻转的懒标记线段树',
    '每个节点保存亮灯数量。翻转整段后，亮灯数变成区间长度减去原亮灯数；翻转标记按异或合并，两次翻转抵消。',
    '一段灯只有亮与灭两种状态，若原来亮了 s 盏、长度为 len，全部翻转后就亮 len−s 盏。因此不需要逐个改变叶子。\n\n在线段树节点上记录待下传的翻转标记。整段更新直接改变亮灯数并把标记异或 1；只有继续访问孩子时，才把翻转作用到两个孩子并清除父标记。两个翻转连续发生等价于没有翻转，所以标记不能简单地设为 true。\n\n查询完整覆盖节点时直接读取亮灯数；部分覆盖时先下传，再把左右答案相加。初始全部熄灭，节点计数和标记均为零。',
    '每次操作 O(log n)，空间 O(n)。','标记使用异或；下传时同步改变孩子计数；初始全灭。',r'''
int n,m;cin>>n>>m;Tree t(n);while(m--){int op,l,r;cin>>op>>l>>r;if(op==0)t.change(1,1,n,l,r);else cout<<t.query(1,1,n,l,r)<<'\n';}
''',FLIP)

add('P6492','维护交替前缀、后缀与最长段',
    '每段保存首尾字符、最长交替前缀与后缀、段内最优长度。左右边界字符不同才可以拼接，跨界候选为左后缀长度加右前缀长度。',
    '合法字符串必须左右交替。合并两段时，最长答案可能完全在左段、完全在右段，或跨越分界。前两者直接取已有答案；跨界答案只有在左段末字符不同于右段首字符时存在，此时能拼接的最大长度就是左后缀加右前缀。\n\n父节点前缀通常等于左前缀。只有左段整体交替且边界可以拼接时，才继续接上右前缀；后缀的处理对称。记录首尾字符与区间长度，合并所需信息就齐全。\n\n初始所有字符为 L，每次只翻转一个叶子，然后沿路径重新合并。根节点的最优长度就是整串答案。长为一的字符串天然合法。',
    '建树 O(n)，每次修改 O(log n)，空间 O(n)。','边界不同才能拼接；前缀扩展要求整个左段合法，后缀扩展要求整个右段合法。',r'''
int n,q;cin>>n>>q;vector<Node>t(4*n);function<void(int,int,int)>build=[&](int p,int l,int r){t[p].len=r-l+1;if(l==r)return;int m=(l+r)/2;build(p*2,l,m);build(p*2+1,m+1,r);t[p]=merge(t[p*2],t[p*2+1]);};build(1,1,n);
function<void(int,int,int,int)>change=[&](int p,int l,int r,int x){if(l==r){t[p].first^=1;t[p].last^=1;return;}int m=(l+r)/2;if(x<=m)change(p*2,l,m,x);else change(p*2+1,m+1,r,x);t[p]=merge(t[p*2],t[p*2+1]);};while(q--){int x;cin>>x;change(1,1,n,x);cout<<t[1].best<<'\n';}
''',r'''
struct Node{int len=1,pre=1,suf=1,best=1,first=0,last=0;};
Node merge(Node a,Node b){Node c;c.len=a.len+b.len;c.first=a.first;c.last=b.last;c.pre=a.pre;c.suf=b.suf;c.best=max(a.best,b.best);if(a.last!=b.first){c.best=max(c.best,a.suf+b.pre);if(a.pre==a.len)c.pre=a.len+b.pre;if(b.suf==b.len)c.suf=b.len+a.suf;}return c;}
''')

add('CF914D','用区间 gcd 跳过全部整除的段',
    '至多修改一个数后整段能被 x 整除，等价于原区间中至多一个数不能被 x 整除。线段树保存 gcd，某段 gcd 能被 x 整除时整段跳过；找到两个坏点立即停止。',
    '题目允许把一个数改成任意整数。如果区间只有零个或一个不被 x 整除的数，就能让整段 gcd 为 x 的倍数；若有两个坏数，一次修改不能同时修复。因此查询转化为坏数计数。\n\n一段所有数都能被 x 整除，当且仅当它们的 gcd 能被 x 整除。线段树保存每段 gcd，遇到能够整除的整段无需继续往下；否则分解，直到叶子确认一个坏数。坏数达到两个立即返回，不再遍历更多节点。\n\n每层至多沿着两个坏点的路径深入，因此查询仍是对数复杂度。单点修改后沿祖先重新计算 gcd。注意这里只判断能否通过修改实现整除关系，不要求原区间 gcd 恰好等于 x。',
    '每次操作 O(log n·log A)，空间 O(n)。','找到两个坏点就停止；剪枝条件是 gcd % x == 0；更新是赋值。',r'''
int n;cin>>n;vector<int>t(4*n);function<void(int,int,int)>build=[&](int p,int l,int r){if(l==r){cin>>t[p];return;}int m=(l+r)/2;build(p*2,l,m);build(p*2+1,m+1,r);t[p]=gcd(t[p*2],t[p*2+1]);};build(1,1,n);
function<void(int,int,int,int,int)>change=[&](int p,int l,int r,int x,int v){if(l==r){t[p]=v;return;}int m=(l+r)/2;if(x<=m)change(p*2,l,m,x,v);else change(p*2+1,m+1,r,x,v);t[p]=gcd(t[p*2],t[p*2+1]);};
function<void(int,int,int,int,int,int,int&)>bad=[&](int p,int l,int r,int a,int b,int x,int&count){if(count>=2||r<a||l>b||t[p]%x==0)return;if(l==r){count++;return;}int m=(l+r)/2;bad(p*2,l,m,a,b,x,count);bad(p*2+1,m+1,r,a,b,x,count);};
int q;cin>>q;while(q--){int op;cin>>op;if(op==1){int l,r,x,c=0;cin>>l>>r>>x;bad(1,1,n,l,r,x,c);cout<<(c<=1?"YES":"NO")<<'\n';}else{int p,x;cin>>p>>x;change(1,1,n,p,x);}}
''')

add('CF438D','区间最大值剪枝取模',
    '线段树同时维护区间和与最大值。对 x 取模时，最大值小于 x 的段完全不变，直接跳过；其余段递归至叶子修改，再合并信息。',
    '取模不是能直接作用于区间和的运算，例如总和相同的两段取模后可能不同。因此这里不设置取模懒标记，而利用值域缩小剪枝。\n\n若一段最大值小于 x，所有元素都不变；否则向孩子递归，直到单点计算余数。一个正数真正发生取模变化后，会至少减半：若 x 不超过原数的一半，余数小于 x；若 x 大于一半，余数等于原数减 x，也小于一半。\n\n所以两次赋值之间，一个数只能被有效取模 O(log A) 次。区间和查询与单点赋值按普通线段树实现，赋值可能重新增大数值，它带来的后续变化次数一并计入摊还成本。',
    '取模操作摊还总时间 O((n+q) log A log n)，查询与赋值 O(log n)，空间 O(n)。','最大值等于模数时仍须修改；区间和用 long long；不能直接对整段和取模。',r'''
int n,q;cin>>n>>q;vector<long long>sum(4*n);vector<int>mx(4*n);auto pull=[&](int p){sum[p]=sum[p*2]+sum[p*2+1];mx[p]=max(mx[p*2],mx[p*2+1]);};
function<void(int,int,int)>build=[&](int p,int l,int r){if(l==r){cin>>mx[p];sum[p]=mx[p];return;}int m=(l+r)/2;build(p*2,l,m);build(p*2+1,m+1,r);pull(p);};build(1,1,n);
function<long long(int,int,int,int,int)>query=[&](int p,int l,int r,int a,int b)->long long{if(a<=l&&r<=b)return sum[p];int m=(l+r)/2;long long ans=0;if(a<=m)ans+=query(p*2,l,m,a,b);if(b>m)ans+=query(p*2+1,m+1,r,a,b);return ans;};
function<void(int,int,int,int,int,int)>mod=[&](int p,int l,int r,int a,int b,int x){if(r<a||l>b||mx[p]<x)return;if(l==r){mx[p]%=x;sum[p]=mx[p];return;}int m=(l+r)/2;mod(p*2,l,m,a,b,x);mod(p*2+1,m+1,r,a,b,x);pull(p);};
function<void(int,int,int,int,int)>setvalue=[&](int p,int l,int r,int i,int x){if(l==r){sum[p]=mx[p]=x;return;}int m=(l+r)/2;if(i<=m)setvalue(p*2,l,m,i,x);else setvalue(p*2+1,m+1,r,i,x);pull(p);};
while(q--){int op,l,r,x;cin>>op>>l>>r;if(op==1)cout<<query(1,1,n,l,r)<<'\n';else if(op==2){cin>>x;mod(1,1,n,l,r,x);}else setvalue(1,1,n,l,r);}
''')

add('SP1043','维护最大子段和的四个量',
    '每段保存总和、最大非空前缀和、最大非空后缀和与最大子段和。合并时跨分界的子段必为左后缀加右前缀。',
    '查询中的最优子段可能位于左侧、右侧，或同时经过左右两侧。跨越分界时，它在左边一定取一个后缀，在右边一定取一个前缀；两者独立取最大即可。\n\n因此节点需要四个量：sum 为总和，pre 为最大非空前缀和，suf 为最大非空后缀和，best 为最大非空子段和。合并式为 pre=max(左pre,左sum+右pre)，suf 对称，best=max(左best,右best,左suf+右pre)。\n\n区间查询必须保持从左到右的合并次序。代码用长度为零的节点代表查询之外的空区间，遇到空节点直接返回另一边，避免把零错误当成合法非空子段。全负数组的答案是最大的那个负数。',
    '建树 O(n)，每次查询 O(log n)，空间 O(n)。','子段必须非空；有序合并；不要把负数答案初始化为 0。',r'''
int n;cin>>n;int size=1;while(size<n)size*=2;vector<Node>t(2*size);for(int i=0;i<n;i++){long long x;cin>>x;t[size+i]={1,x,x,x,x};}for(int p=size-1;p;p--)t[p]=merge(t[p*2],t[p*2+1]);int q;cin>>q;while(q--){int l,r;cin>>l>>r;Node a,b;for(l+=size-1,r+=size;l<r;l/=2,r/=2){if(l&1)a=merge(a,t[l++]);if(r&1)b=merge(t[--r],b);}cout<<merge(a,b).best<<'\n';}
''',r'''
struct Node{int len=0;long long sum=0,pre=0,suf=0,best=0;};
Node merge(Node a,Node b){if(!a.len)return b;if(!b.len)return a;return {a.len+b.len,a.sum+b.sum,max(a.pre,a.sum+b.pre),max(b.suf,b.sum+a.suf),max({a.best,b.best,a.suf+b.pre})};}
''')

add('P6373','按子序列拼接维护 IOI 计数',
    '节点保存 I、O、IO、OI、IOI 的子序列数。跨界的 IOI 只能拆成左 I 与右 OI，或左 IO 与右 I，两类相加即可。',
    '题目要求下标递增，不要求字符连续，因此一个区间的计数需要记录可以与另一段拼接的短子序列。除了单字符 I、O，还要记录 IO、OI 以及完整的 IOI。\n\n合并左右两段时，IO 的跨界贡献为左 I 数乘右 O 数；OI 类似。IOI 要么完全在某一边，要么第一个字符在左边、后两个在右边，或前两个在左边、最后一个在右边。于是跨界贡献为左 I×右 OI+左 IO×右 I。\n\n这两类按跨界前字符数划分，互不重叠且覆盖所有可能。单点修改只改变一个叶子，再沿祖先合并。查询采用左右两个累积节点，始终按原字符串顺序拼接。三元组数可达 O(n³)，所有计数都用 long long。',
    '建树 O(n)，每次操作 O(log n)，空间 O(n)。','统计子序列；合并顺序不能交换；乘法和计数使用六十四位整数。',r'''
int n,m;string s;cin>>n>>m>>s;int size=1;while(size<n)size*=2;vector<Node>t(2*size);for(int i=0;i<n;i++)t[size+i]=leaf(s[i]);for(int p=size-1;p;p--)t[p]=merge(t[p*2],t[p*2+1]);while(m--){int op,l;cin>>op>>l;if(op==1){char c;cin>>c;int p=size+l-1;t[p]=leaf(c);for(p/=2;p;p/=2)t[p]=merge(t[p*2],t[p*2+1]);}else{int r;cin>>r;Node a,b;for(l+=size-1,r+=size;l<r;l/=2,r/=2){if(l&1)a=merge(a,t[l++]);if(r&1)b=merge(t[--r],b);}cout<<merge(a,b).ioi<<'\n';}}
''',r'''
struct Node{long long i=0,o=0,io=0,oi=0,ioi=0;};
Node leaf(char c){Node a;a.i=c=='I';a.o=c=='O';return a;}
Node merge(Node a,Node b){return {a.i+b.i,a.o+b.o,a.io+b.io+a.i*b.o,a.oi+b.oi+a.o*b.i,a.ioi+b.ioi+a.i*b.oi+a.io*b.i};}
''')

add('P10798','单调栈分组后平衡正负数量',
    '绝对值无法改变。对每个绝对值，只在中间没有更大绝对值的同值元素间形成威胁。这些元素形成独立组，非零组把正负数量尽量平分；零不能变号，组内任意两点都贡献一次。',
    '一次翻转只改变符号，不能改变谁是区间绝对值的最大值。若两端的绝对值为 v，中间出现大于 v 的元素，这对端点永远不形成威胁；否则只取决于两端符号是否相同。\n\n用绝对值单调不增的栈保存还没有遇到更大值的组。当读入 v，所有栈顶小于 v 的组都被这个更大的元素截断，可以结算；栈顶等于 v 时把当前元素计入同一组，否则建立新组。更小值不会隔断一组。\n\n一组有 c 个非零元素，若 p 个为正，威胁数为 p(p−1)/2+(c−p)(c−p−1)/2。两种数量相差超过一时，把一个多数符号改成少数符号会减少答案，所以最优为尽量平分。v=0 时翻转仍是零，贡献 c(c−1)/2。每组的元素互不相交，可独立安排符号，故各组最小值相加就是全局最优。',
    '时间 O(n)，空间 O(n)。','0 无法改变符号；只在遇到严格更大绝对值时结算小组；答案用 long long。',r'''
int n;cin>>n;vector<pair<long long,long long>>st;long long ans=0;auto settle=[&](){auto [v,c]=st.back();st.pop_back();if(v==0)ans+=c*(c-1)/2;else{long long a=c/2,b=c-a;ans+=a*(a-1)/2+b*(b-1)/2;}};for(int i=0;i<n;i++){long long x;cin>>x;x=llabs(x);while(!st.empty()&&st.back().first<x)settle();if(!st.empty()&&st.back().first==x)st.back().second++;else st.push_back({x,1});}while(!st.empty())settle();cout<<ans<<'\n';
''')
