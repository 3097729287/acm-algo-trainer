from core7_completion import add, FENWICK
from core7_completion_actual_graph import HLD

add('P1878','链表维护相邻关系，堆选择最优舞伴',
    '用双向链表表示还在队伍中的人，把相邻异性对按技术差、左端编号放入最小堆。弹出时检查是否仍相邻，删除有效的一对，并加入新产生的邻接对。',
    '删除一对后，只有左侧邻居与右侧邻居之间出现一个新的相邻关系，其它候选对的技术差不变。因此不必每轮重新扫描全部队伍。\n\n初始将所有相邻异性对入堆，关键字先比较技术绝对差，再比较左端编号。原始编号随队伍保持顺序，左端编号最小正好表示最左一对。\n\n堆内旧候选不必立即删除，弹出时检查两人未离队且 next[left]==right，失效就丢弃。有效对离队后，将前后邻居接起来，若性别不同则插入新候选。每次删除最多产生一对，所有堆项数量为线性。',
    '时间 O(n log n)，空间 O(n)。','技术差取绝对值；同差按左端编号；堆内过期对必须跳过。',r'''
int n;string gender;cin>>n>>gender;vector<int>a(n),left(n),right(n);vector<char>alive(n,1);for(int&x:a)cin>>x;for(int i=0;i<n;i++){left[i]=i-1;right[i]=i+1<n?i+1:-1;}using P=tuple<int,int,int>;priority_queue<P,vector<P>,greater<P>>heap;auto push=[&](int l,int r){if(l>=0&&r>=0&&gender[l]!=gender[r])heap.push({abs(a[l]-a[r]),l,r});};for(int i=1;i<n;i++)push(i-1,i);vector<pair<int,int>>ans;while(!heap.empty()){auto[diff,l,r]=heap.top();heap.pop();if(!alive[l]||!alive[r]||right[l]!=r)continue;ans.push_back({l+1,r+1});alive[l]=alive[r]=0;int L=left[l],R=right[r];if(L>=0)right[L]=R;if(R>=0)left[R]=L;push(L,R);}cout<<ans.size()<<'\n';for(auto[l,r]:ans)cout<<l<<' '<<r<<'\n';
''')

add('P3988','树状数组查找存活牌的第 k 张',
    '存活牌按原编号保持循环顺序。记录当前牌顶在存活序列中的排名，销牌只需排名加 R 后取模，再用树状数组找对应编号并删除。',
    '每次把牌顶移到底只改变循环起点，不改变剩余牌的相对顺序。若剩余 remain 张、当前零开始排名为 rank，销 R 次后的发牌排名为 (rank+R)%remain。\n\n每个编号存一表示尚未发出，树状数组维护前缀存活数量。用倍增查找前缀和首次达到 rank+1 的位置，就是这一张的原编号。删除后，它的下一张在新序列中仍占据同一个 rank；若刚删除末尾，下次取模自然回到零。\n\n初始全为一，Fenwick 的每项可直接初始化为 lowbit(i)，避免逐点建立。',
    '时间 O(N log N)，空间 O(N)。','排名按剩余牌数取模；删除后起点是下一张；输出原牌号。',r'''
int n;cin>>n;Fenwick bit(n);for(int i=1;i<=n;i++)bit.t[i]=i&-i;long long rank=0;int highest=1;while((highest<<1)<=n)highest<<=1;for(int remain=n;remain>=1;remain--){long long R;cin>>R;rank=(rank+R)%remain;long long need=rank+1;int pos=0;for(int step=highest;step;step>>=1){int next=pos+step;if(next<=n&&bit.t[next]<need){need-=bit.t[next];pos=next;}}int card=pos+1;cout<<card<<'\n';bit.add(card,-1);}
''',FENWICK)

add('P9588','连续块编号与单调队列维护最大值',
    '每次加入 1..x 只记录为一个块。所有加入元素使用全局连续编号，弹出只增加已删除总数；第 z 个元素二分定位所属块，最大值用各未删完块的 x 的单调队列维护。',
    '将一次入队的 1..x 视为区间块，记录累计右端 end 与块长 x。若全局编号为 p，它属于第一个 end≥p 的块，值就是 p−(end−x)。队头删除 y 个只让 removed 增加 y；第 z 个元素的全局编号是 removed+z。\n\n一个尚未删完的块，无论前端已经删了多少，它的最大元素 x 都还在末尾，所以全队最大值就是所有 end>removed 的块长最大值。维护块长递减的双端队列，新块到来时弹出较小末项；它们更早结束且最大值不更大，之后也不会有用。\n\n删除时弹去已经完全消失的队首块。全局长度可达二乘十的十四次方，累计编号必须用 long long。',
    '时间 O(q log q)，空间 O(q)。','半删块的最大值仍是 x；全局编号不回收；二分找第一个 end≥p。',r'''
int caseId,q;cin>>caseId>>q;vector<long long>ends,lengths;deque<int>maximum;long long total=0,removed=0;while(q--){int type;cin>>type;if(type==1){long long x;cin>>x;total+=x;ends.push_back(total);lengths.push_back(x);int i=ends.size()-1;while(!maximum.empty()&&lengths[maximum.back()]<=x)maximum.pop_back();maximum.push_back(i);}else if(type==2){long long y;cin>>y;removed+=y;while(!maximum.empty()&&ends[maximum.front()]<=removed)maximum.pop_front();}else if(type==3){long long z;cin>>z;long long p=removed+z;int i=lower_bound(ends.begin(),ends.end(),p)-ends.begin();cout<<p-(ends[i]-lengths[i])<<'\n';}else cout<<lengths[maximum.front()]<<'\n';}
''')

add('P14078','位置与等待时间组成二维最长链',
    '把金币变为点 (x,t−x)。从一枚走到下一枚，等价于两个坐标都不减。排除起点不可达金币，按第一维、第二维升序排序，再求第二维最长不下降子序列。',
    '从 (x1,t1) 到 (x2,t2) 只能右移或等待，条件是 x2≥x1 且 t2−t1≥x2−x1，第二个条件等价于 t2−x2≥t1−x1。因此变换后变成两维非降链。\n\n从零出发要求 x≥0、t−x≥0。满足这两个条件的点按 x、t−x 升序排序，第一维已经合法，剩下求第二维最长不下降子序列。用 upper_bound 替换牌堆顶，允许相等值延长。\n\n同一位置同一时刻出现多枚金币可以同时收走，它们对应完全相同的点，应分别计数，不能去重。',
    '时间 O(n log n)，空间 O(n)。','第二维是 t−x；用 upper_bound 允许相等；同点金币不能去重。',r'''
int n;cin>>n;vector<pair<long long,long long>>points;for(int i=0;i<n;i++){long long x,t;cin>>x>>t;if(x>=0&&t>=x)points.push_back({x,t-x});}sort(points.begin(),points.end());vector<long long>tails;for(auto[x,y]:points){auto it=upper_bound(tails.begin(),tails.end(),y);if(it==tails.end())tails.push_back(y);else *it=y;}cout<<tails.size()<<'\n';
''')

add('P2982','先到牧场对子树统一增加一次减速',
    '一头已到达牧场的牛，会使以后所有目的地位于该牧场子树的奶牛减速一次。Euler 序把子树变成区间，用差分树状数组区间加、单点查询。',
    '从根到目的地的路径会经过某个已有奶牛的牧场，当且仅当该牧场是目的地的祖先，也就是目的地位于它的子树内。\n\n预处理 DFS 进入顺序与子树大小，子树对应 [tin,tin+size−1]。每头牛先在目的地 tin 做前缀和查询，得到之前到达的祖先牧场数；随后将自己的整个子树加一。\n\n树状数组维护差分：区间 [l,r] 加一转为 l 加一、r+1 减一，位置查询取差分前缀和。先查询后更新，不会把自己算成减速原因。遍历用显式栈避免长链递归。',
    '时间 O(n log n)，空间 O(n)。','先查后加；根上的牛会影响所有后来奶牛；Euler 子树区间包含根。',r'''
int n;cin>>n;vector<vector<int>>g(n);for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}HLD tree(g);Fenwick bit(n+1);for(int i=0;i<n;i++){int p;cin>>p;p--;int l=tree.pos[p]+1,r=l+tree.size[p]-1;cout<<bit.sum(l)<<'\n';bit.add(l,1);bit.add(r+1,-1);}
''',HLD+FENWICK)

add('P3616','可见连通块等于可见点数减可见边数',
    '露出的石头在链上形成森林，连通块数等于点数减边数。每个石头高度贡献加一，每对相邻石头的较小高度贡献减一；水位查询转为高度不小于水位的权值和。',
    '可见点条件是高度≥B，一条相邻边可见当且仅当两端都可见，等价于两端最小高度≥B。链的任意诱导子图无环，所以块数始终等于可见点数减可见边数。\n\n因此在高度轴上建立计数：每个点在自己的高度加一，每条边在两端最小值位置减一。查询所有高度≥B 的权值和即可。\n\n修改一个点只影响它自身和左右两条边，先移除旧贡献，再改高度、加入新贡献。离线收集所有初值和修改值进行坐标压缩，所有边最小值也必在这些高度里；查询阈值用 lower_bound 定位。',
    '时间 O((N+M) log(N+M))，空间 O(N+M)。','与水面持平仍可见；边贡献为负一；修改时先移除旧相邻边。',r'''
int n,m;cin>>n>>m;vector<long long>a(n),values;for(auto&x:a){cin>>x;values.push_back(x);}struct Op{int type,p;long long x;};vector<Op>ops;for(int i=0;i<m;i++){int type;cin>>type;if(type==1){long long B;cin>>B;ops.push_back({1,0,B});}else{int p;long long x;cin>>p>>x;ops.push_back({2,p-1,x});values.push_back(x);}}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());Fenwick bit(values.size());auto change=[&](long long h,int delta){int r=lower_bound(values.begin(),values.end(),h)-values.begin()+1;bit.add(r,delta);};for(int i=0;i<n;i++){change(a[i],1);if(i)change(min(a[i-1],a[i]),-1);}for(auto op:ops)if(op.type==1){int r=lower_bound(values.begin(),values.end(),op.x)-values.begin();cout<<bit.sum(values.size())-bit.sum(r)<<'\n';}else{int p=op.p;change(a[p],-1);if(p)change(min(a[p-1],a[p]),1);if(p+1<n)change(min(a[p],a[p+1]),1);a[p]=op.x;change(a[p],1);if(p)change(min(a[p-1],a[p]),-1);if(p+1<n)change(min(a[p],a[p+1]),-1);}
''',FENWICK)

add('P10814','按查询值激活数组位置',
    '将元素按值排序、询问按 x 排序。处理询问前把值≤x 的位置在树状数组中置一，区间和就是满足条件的个数。',
    '每个元素对应二维点 (下标,值)，询问要统计下标在 [l,r] 且值≤x 的点。离线按第二维扫描，就只剩一维区间计数。\n\n按 x 从小到大处理，每次将尚未加入且 a[i]≤x 的位置加一，已经加入的永远不需删除。树状数组查询前 r 个位置数量减前 l−1 个，得到闭区间计数。\n\n保存询问原编号，最后按输入次序输出。相同数值也都要在等值 x 的询问之前加入。',
    '时间 O((n+m) log(n+m))，空间 O(n+m)。','使用≤而非<；相同数值全部激活；答案恢复原询问顺序。',r'''
int n,m;cin>>n>>m;vector<pair<int,int>>a(n);for(int i=0;i<n;i++){cin>>a[i].first;a[i].second=i+1;}sort(a.begin(),a.end());struct Q{int l,r,x,id;};vector<Q>queries(m);for(int i=0;i<m;i++){cin>>queries[i].l>>queries[i].r>>queries[i].x;queries[i].id=i;}sort(queries.begin(),queries.end(),[](Q a,Q b){return a.x<b.x;});Fenwick bit(n);vector<long long>ans(m);int p=0;for(auto q:queries){while(p<n&&a[p].first<=q.x){bit.add(a[p].second,1);p++;}ans[q.id]=bit.sum(q.r)-bit.sum(q.l-1);}for(auto x:ans)cout<<x<<'\n';
''',FENWICK)

add('CF413E','线段树合并两行边界最短路矩阵',
    '每段保存左边界两格到右边界两格的四个最短距离。相邻段通过上、下两种边界横边连接，枚举跨边所在行合并。查询两点列区间得到对应矩阵项。',
    '对起终列之间的矩形，最短路不需要跑到更外侧：若从边界一行出发绕到外侧再回另一行，两边界格都可走，可以用边界上的一条竖边替代并缩短。因此只需查询这两列之间。\n\n两行图的一个竖直切口只有两条横边。无重复顶点的最短路从切口左侧到右侧，跨过切口的次数必须为奇数，又不可能重复使用边，所以只跨一次。于是合并距离为 min_r(left[a][r]+1+right[r][b])。障碍对应无穷距离。\n\n单列同格距离零，两格都开放时跨行距离一。线段树合并按从左到右的顺序，不能交换查询两侧累计矩阵。编号先拆成行与列，必要时交换起终点使起始列较小。',
    '预处理 O(n)，每问 O(log n)，空间 O(n)。','矩阵合并有顺序；同列可以直接走竖边；不可达输出 −1。',r'''
int n,q;cin>>n>>q;string s[2];cin>>s[0]>>s[1];int size=1;while(size<n)size*=2;vector<Matrix>tree(2*size);for(int i=0;i<n;i++){auto&v=tree[size+i];v.valid=true;for(int a=0;a<2;a++)for(int b=0;b<2;b++)v.d[a][b]=s[a][i]=='.'&&s[b][i]=='.'?(a==b?0:1):INF;}for(int i=size-1;i>=1;i--)tree[i]=mergeMatrix(tree[2*i],tree[2*i+1]);auto query=[&](int l,int r){Matrix left,right;for(l+=size,r+=size;l<r;l/=2,r/=2){if(l&1)left=mergeMatrix(left,tree[l++]);if(r&1)right=mergeMatrix(tree[--r],right);}return mergeMatrix(left,right);};while(q--){int a,b;cin>>a>>b;a--;b--;int ra=a/n,ca=a%n,rb=b/n,cb=b%n;if(ca>cb){swap(ca,cb);swap(ra,rb);}int ans=query(ca,cb+1).d[ra][rb];cout<<(ans>=INF?-1:ans)<<'\n';}
''',r'''
const int INF=100000000;struct Matrix{bool valid=false;int d[2][2]={{INF,INF},{INF,INF}};};Matrix mergeMatrix(const Matrix&a,const Matrix&b){if(!a.valid)return b;if(!b.valid)return a;Matrix c;c.valid=true;for(int i=0;i<2;i++)for(int j=0;j<2;j++)for(int r=0;r<2;r++)c.d[i][j]=min(c.d[i][j],a.d[i][r]+1+b.d[r][j]);return c;}
''')

add('P2325','DFS 待分配栈凑足一省就切出',
    '后序遍历中把尚未归省的点留在栈上。处理一个孩子后，若当前根累计的待分配点不少于 B，就把这一段整体划为一省，以当前根为省会。最后剩余点并入最后一省。',
    '每个孩子返回时未分配的部分少于或等于 B；在当前根下累计未分配点，达到 B 就立即切出。切出前累计不足 B，加上一个孩子剩余最多 B，因此新省大小不超过 2B−1。\n\n这些点到当前根的路径，除省会本身外都处在本次切出的栈段内，所以满足省会可在省外的路径条件。当前根随后也留在未分配栈中，可以作为多个省的省会。\n\n最后根返回的剩余最多 B 个点，并入最后一省后大小不超过 3B−1，连接路径也都在该省或省会中。若从未切出省，全部 n 个点一起为一省；此时由算法可知 n≤B，结合题设 B≤n，恰为 B。',
    '时间 O(n)，空间 O(n)。','省会可以在省外；只弹当前根积累的栈段；末尾剩余不能独立形成过小省。',r'''
int n,B;cin>>n>>B;vector<vector<int>>g(n);for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}vector<int>st,belong(n),capitals;function<void(int,int)>dfs=[&](int v,int p){int base=st.size();for(int u:g[v])if(u!=p){dfs(u,v);if((int)st.size()-base>=B){capitals.push_back(v);int id=capitals.size();while((int)st.size()>base){belong[st.back()]=id;st.pop_back();}}}st.push_back(v);};dfs(0,-1);if(capitals.empty())capitals.push_back(0);for(int v:st)belong[v]=capitals.size();cout<<capitals.size()<<'\n';for(int i=0;i<n;i++)cout<<belong[i]<<(i+1==n?'\n':' ');for(int i=0;i<(int)capitals.size();i++)cout<<capitals[i]+1<<(i+1==(int)capitals.size()?'\n':' ');
''',checker='provinces')

add('P3645','小跳长共享状态，大跳长直接展开',
    '小跳长 p 建立“仍持有 p”的位置状态，可左右一步跳并随时换狗；大跳长从当前楼直接枚举所有可到楼，边权为跳数。对隐式分层图运行 Dijkstra。',
    '若为每条狗都沿整条同余链扩展，最坏会重复平方次。取阈值 B≈sqrt(n)，按跳长分情况。\n\np<B 时，把 (p,楼号) 作为共享状态：从持有该狗的楼可零代价进入，状态内向左右 p 格移动代价一，也可零代价回到普通楼状态换狗。所有同跳长的狗共享这一层。\n\np≥B 时，一次持狗能到达的楼不超过 O(n/B)，从普通楼直接连到这些楼，代价是距离除以 p。无需保存大跳层。\n\n所有边权非负，Dijkstra 按最小跳数扩展。普通楼状态只在最短距离确定时处理狗，大跳展开总计 O(mn/B)，小跳状态 O(nB)。起点和终点是输入前两只狗所在楼，楼号原本从零开始。',
    '时间 O((nB+mn/B) log(nB))，空间 O(nB+m)，B≈sqrt(n)。','进入小跳层不花步数；普通状态才能换狗；起终来自前两条记录。',r'''
int n,m;cin>>n>>m;int B=max(2,(int)sqrt(n)+1),start=0,goal=0;vector<vector<int>>dogs(n);for(int i=0;i<m;i++){int b,p;cin>>b>>p;dogs[b].push_back(p);if(i==0)start=b;if(i==1)goal=b;}for(auto&v:dogs){sort(v.begin(),v.end());v.erase(unique(v.begin(),v.end()),v.end());}const int INF=1000000000;vector<int>d(n*B,INF);priority_queue<pair<int,int>,vector<pair<int,int>>,greater<pair<int,int>>>heap;d[start]=0;heap.push({0,start});auto relax=[&](int state,int value){if(value<d[state]){d[state]=value;heap.push({value,state});}};while(!heap.empty()){auto[dist,state]=heap.top();heap.pop();if(d[state]!=dist)continue;int p=state/n,v=state%n;if(!p){if(v==goal){cout<<dist<<'\n';return 0;}for(int jump:dogs[v]){if(jump<B)relax(jump*n+v,dist);else{int cost=1;for(int u=v+jump;u<n;u+=jump,cost++)relax(u,dist+cost);cost=1;for(int u=v-jump;u>=0;u-=jump,cost++)relax(u,dist+cost);}}}else{relax(v,dist);if(v+p<n)relax(p*n+v+p,dist+1);if(v-p>=0)relax(p*n+v-p,dist+1);}}cout<<-1<<'\n';
''')

add('P10190','分离正负斜率后分别优化上下截距',
    '右下角必须用正斜率、右上角必须用负斜率。左端顶点按高度排序，低的分给负斜率、高的分给正斜率。随后分别二分正斜率截距的最大下界与负斜率截距的最小上界。',
    '射向右上角的线若为正斜率，会先穿过矩形内部，所以必须负斜率；右下角同理必须正斜率。左侧两个顶点没有符号限制。正负斜率数量均至少 N 才可能完成。\n\n所有左端横坐标相同。若较低左顶点分给正斜率、较高顶点分给负斜率，交换它们会让正斜率牛的截距升高、负斜率牛的截距降低，两个新截距都位于原两截距之间。因此可以把最小的“负斜率数−N”个左顶点分给负斜率，其余分给正斜率。\n\n记斜率绝对值为 s，正斜率截距为 y−sx，负斜率截距为 y+sx。所有正斜率截距的最大值不会超过某个负斜率截距：每个顶点高度总有相应矩形右上角高度不低于它；对最低值有对称论证。因此整体最小值由正组决定、最大值由负组决定，两组匹配可独立优化。\n\n正组要求所有截距≥L，等价于每个目标允许 s≤floor((y−L)/x)；负组要求截距≤U，等价于 s≤floor((U−y)/x)。把斜率和允许上限分别排序，逐项比较即可判定匹配存在。分别二分最大 L、最小 U，答案 U−L。',
    '时间 O(N log N log V)，V 为截距范围；空间 O(N)。','右侧角点符号不能反；左端点按高度分配；乘积与截距需六十四位。',r'''
int T;cin>>T;while(T--){int n;long long X;cin>>n>>X;vector<pair<long long,long long>>positive,negative;vector<long long>leftY;for(int i=0;i<n;i++){long long y1,y2,x2;cin>>y1>>y2>>x2;positive.push_back({x2,y1});negative.push_back({x2,y2});leftY.push_back(y1);leftY.push_back(y2);}vector<long long>p,q;for(int i=0;i<4*n;i++){long long s;cin>>s;if(s>0)p.push_back(s);else q.push_back(-s);}if((int)p.size()<n||(int)q.size()<n){cout<<-1<<'\n';continue;}sort(p.begin(),p.end());sort(q.begin(),q.end());sort(leftY.begin(),leftY.end());int lowCount=q.size()-n;for(int i=0;i<2*n;i++)(i<lowCount?negative:positive).push_back({X,leftY[i]});auto feasible=[&](const vector<pair<long long,long long>>&points,const vector<long long>&slopes,long long bound,bool lower){vector<long long>caps;caps.reserve(points.size());for(auto[x,y]:points){long long numerator=lower?y-bound:bound-y;if(numerator<0)return false;caps.push_back(numerator/x);}sort(caps.begin(),caps.end());for(int i=0;i<(int)caps.size();i++)if(slopes[i]>caps[i])return false;return true;};long long lo=-1000000000000000000LL,hi=1000000000LL;while(lo<hi){long long mid=lo+(hi-lo+1)/2;if(feasible(positive,p,mid,true))lo=mid;else hi=mid-1;}long long L=lo;lo=0;hi=2000000000000000000LL;while(lo<hi){long long mid=lo+(hi-lo)/2;if(feasible(negative,q,mid,false))hi=mid;else lo=mid+1;}cout<<lo-L<<'\n';}
''')
