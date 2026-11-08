from core7_completion import add, DSU, SCC

TREE_PATHS=r'''
struct TreePaths{int n,levels;vector<int>depth,root;vector<vector<int>>up;vector<vector<long long>>minimum;
TreePaths(const vector<vector<pair<int,long long>>>&g):n(g.size()),levels(1),depth(n,-1),root(n){while((1<<levels)<=n)levels++;up.assign(levels,vector<int>(n));minimum.assign(levels,vector<long long>(n,LLONG_MAX));for(int start=0;start<n;start++)if(depth[start]<0){depth[start]=0;root[start]=start;for(int j=0;j<levels;j++)up[j][start]=start;vector<int>q={start};for(int i=0;i<(int)q.size();i++){int v=q[i];for(auto [u,w]:g[v])if(depth[u]<0){depth[u]=depth[v]+1;root[u]=start;up[0][u]=v;minimum[0][u]=w;for(int j=1;j<levels;j++){up[j][u]=up[j-1][up[j-1][u]];minimum[j][u]=min(minimum[j-1][u],minimum[j-1][up[j-1][u]]);}q.push_back(u);}}}}
int lca(int a,int b)const{if(depth[a]<depth[b])swap(a,b);int difference=depth[a]-depth[b];for(int j=0;j<levels;j++)if((difference>>j)&1)a=up[j][a];if(a==b)return a;for(int j=levels-1;j>=0;j--)if(up[j][a]!=up[j][b]){a=up[j][a];b=up[j][b];}return up[0][a];}
long long bottleneck(int a,int b)const{if(a==b)return 0;long long answer=LLONG_MAX;if(depth[a]<depth[b])swap(a,b);int difference=depth[a]-depth[b];for(int j=0;j<levels;j++)if((difference>>j)&1){answer=min(answer,minimum[j][a]);a=up[j][a];}if(a==b)return answer;for(int j=levels-1;j>=0;j--)if(up[j][a]!=up[j][b]){answer=min({answer,minimum[j][a],minimum[j][b]});a=up[j][a];b=up[j][b];}return min({answer,minimum[0][a],minimum[0][b]});}};
'''

add('P1949','密码与光标位置共同作为 BFS 状态',
    '相同密码在不同光标位置的下一步不同，必须把六位密码与光标位置一起编码。六种按键均为一步，BFS 首次遇到目标密码时就是最少击键次数，目标光标任意。',
    '密码只有一百万种，光标六种位置，总状态六百万，可以直接使用数组记录距离，避免字符串映射开销。密码虽按整数编码，仍按六位固定十进制权值取出某位，因此前导零不会丢失。\n\n对状态 (code,p)，左右键改变 p；up、down 只在当前位未达九或零时增减相应十进制权值；swap0、swap1 通过两个位置数位差更新整数，光标不动。所有状态转移代价都是一，用普通队列 BFS。\n\n目标只要求密码等于目标串，不限制光标。因此任意光标的目标状态首次出队就能返回。最坏可逐位调整并向右移动，距离不超过几十，使用一个字节保存距离、255 表示未访问即可节省空间。',
    '时间 O(6·10^6)，空间 O(6·10^6)。','密码与光标共同编码；up/down 不循环；允许前导零；目标光标任意。',r'''
string s,t;cin>>s>>t;int start=stoi(s),goal=stoi(t);if(start==goal){cout<<0<<'\n';return 0;}int power[6]={100000,10000,1000,100,10,1};vector<unsigned char>distance(6000000,255);vector<int>queue;queue.reserve(6000000);queue.push_back(start*6);distance[start*6]=0;for(size_t front=0;front<queue.size();front++){int state=queue[front],code=state/6,p=state%6,depth=distance[state];if(code==goal){cout<<depth<<'\n';return 0;}auto push=[&](int next){if(distance[next]==255){distance[next]=depth+1;queue.push_back(next);}};if(p)push(code*6+p-1);if(p<5)push(code*6+p+1);int digit=code/power[p]%10;if(digit<9)push((code+power[p])*6+p);if(digit>0)push((code-power[p])*6+p);for(int q:{0,5}){int other=code/power[q]%10;int next=code+(other-digit)*power[p]+(digit-other)*power[q];push(next*6+p);}}
''')

add('AT_indeednow_2015_quala_4','曼哈顿距离剪枝的迭代加深',
    '所有非空格到目标位置的曼哈顿距离之和是剩余步数下界。逐渐增加允许总步数，深搜中若已走步数加这个下界超限就剪枝，并跳过立即撤销上一步的移动。',
    '一次操作只把一个数字格移动一格，它到目标的曼哈顿距离至多减少一。因此所有数字格距离之和 h 不会高估还需的操作数，是安全的搜索下界；空白格不计入。\n\n从初始 h 开始限制总步数，只有当前步数 g+h 不超过限制的分支才继续。每移动一个数字，只更新这个数字的距离变化，不必重算整个棋盘。数字按目标行列确定位置，适用于六乘六而非只能编码十五数码。\n\n一次移动使 h 的奇偶翻转，因此解长与初始 h 同奇偶，限制每次增加二即可。优先尝试使 h 较小的移动，找解更快；禁止空白立即走回原位置，去掉必无价值的往返。原题保证最短解不超过二十四，首次找到的迭代深度就是最短步数。',
    '最坏指数时间，实际搜索由深度二十四保证和曼哈顿剪枝控制；递归空间 O(24+HW)。','不计算空格的曼哈顿距离；交换后回溯恢复；棋盘可达六乘六；只跳过直接回退。',r'''
int h,w;cin>>h>>w;int n=h*w;vector<int>a(n);int blank=0,estimate=0;vector<vector<int>>distance(n,vector<int>(n));for(int p=0;p<n;p++)for(int value=1;value<n;value++)distance[p][value]=abs(p/w-(value-1)/w)+abs(p%w-(value-1)%w);for(int i=0;i<n;i++){cin>>a[i];if(a[i])estimate+=distance[i][a[i]];else blank=i;}vector<vector<int>>neighbors(n);for(int p=0;p<n;p++)for(auto [dx,dy]:vector<pair<int,int>>{{1,0},{-1,0},{0,1},{0,-1}}){int x=p/w+dx,y=p%w+dy;if(x>=0&&x<h&&y>=0&&y<w)neighbors[p].push_back(x*w+y);}function<bool(int,int,int,int,int)>search=[&](int hole,int previous,int used,int lower,int limit){if(used+lower>limit)return false;if(lower==0)return true;vector<pair<int,int>>moves;for(int next:neighbors[hole])if(next!=previous){int value=a[next],newLower=lower-distance[next][value]+distance[hole][value];moves.push_back({newLower,next});}sort(moves.begin(),moves.end());for(auto [newLower,next]:moves){swap(a[hole],a[next]);bool found=search(next,hole,used+1,newLower,limit);swap(a[hole],a[next]);if(found)return true;}return false;};for(int limit=estimate;limit<=24;limit+=2)if(search(blank,-1,0,estimate,limit)){cout<<limit<<'\n';return 0;}
''')

add('P1967','最大生成森林上的路径最小边',
    '按边权降序做 Kruskal，得到最大生成森林。原图两点间能承受的最大瓶颈，等于森林中路径最小边。用倍增维护祖先和沿途最小值回答多次查询。',
    '设希望货车载重至少 W，则只能走承重不小于 W 的边。按边权降序合并时，两点第一次连通的边权正是最大可行 W。最大生成森林保留了每个阈值下的连通性，因此它们在森林路径上的最小边就是这个阈值。\n\n先用 Kruskal 选择不成环的边，原图不连通时得到多棵树。预处理每个点的 2^j 级祖先，以及到该祖先路径上的最小边权。查询先把深点抬到同深，再同时向上抬，两侧每次都把经过段的最小值合入。\n\n两点不在同一个并查集块时输出 −1。连通时倍增过程得到路径最小边，无须每次重新跑图搜索。',
    '时间 O(m log m+(n+q) log n)，空间 O(m+n log n)。','最大生成树按权值降序；查询取路径最小边；先判断是否连通。',r'''
int n,m;cin>>n>>m;vector<tuple<long long,int,int>>edges(m);for(auto &[w,a,b]:edges){cin>>a>>b>>w;a--;b--;}sort(edges.rbegin(),edges.rend());DSU d(n);vector<vector<pair<int,long long>>>g(n);for(auto [w,a,b]:edges)if(d.join(a,b)){g[a].push_back({b,w});g[b].push_back({a,w});}TreePaths paths(g);int q;cin>>q;while(q--){int a,b;cin>>a>>b;a--;b--;if(d.find(a)!=d.find(b))cout<<-1<<'\n';else cout<<paths.bottleneck(a,b)<<'\n';}
''',DSU+TREE_PATHS)

add('P8191','按有限纵坐标保留必要近邻边',
    '纵坐标只有 0 到 10。对每个点与每条水平行，只连接横坐标最近的左右邻居，再在这些 O(11n) 条候选边上做 Kruskal。',
    '完整欧氏图有平方条边，但每个点只落在十一种纵坐标之一。把每行按横坐标排序，对点 u 在任一行中找到横坐标刚不小于它的点和前一个点，加入这两条候选边。\n\n为什么可以省掉其它边 u−v？在 v 所在行中，先连接从 u 朝 v 方向的最近点，再沿这一行的相邻点走到 v。第一条边纵坐标差与 u−v 相同、横差更小，后续横向相邻边的长度也都不超过 u−v。因此每条被省掉的完整图边，其两端在候选图中已经由不更重的边相连。\n\n这说明每个权值阈值下两图连通性相同，Kruskal 选出的最小生成树总权也相同。候选边权保存距离平方，排序后做并查集合并，避免开方。坐标相同或边重复都不影响正确性。',
    '时间 O(11n log n)，空间 O(11n)。','边权是平方距离；每行找左右近邻；坐标乘法用 long long。',r'''
int n;cin>>n;vector<long long>x(n);vector<int>y(n);array<vector<int>,11>rows;for(int i=0;i<n;i++){cin>>x[i]>>y[i];rows[y[i]].push_back(i);}for(auto &row:rows)sort(row.begin(),row.end(),[&](int a,int b){return x[a]<x[b];});vector<tuple<long long,int,int>>edges;auto connect=[&](int a,int b){if(a==b)return;long long dx=x[a]-x[b],dy=y[a]-y[b];edges.push_back({dx*dx+dy*dy,a,b});};for(int i=0;i<n;i++)for(auto &row:rows){auto it=lower_bound(row.begin(),row.end(),x[i],[&](int a,long long value){return x[a]<value;});if(it!=row.end()){if(*it!=i)connect(i,*it);else if(next(it)!=row.end())connect(i,*next(it));}if(it!=row.begin())connect(i,*prev(it));}sort(edges.begin(),edges.end());DSU d(n);long long answer=0;for(auto [w,a,b]:edges)if(d.join(a,b))answer+=w;cout<<answer<<'\n';
''',DSU)

add('CF1245D','建电站作为虚拟源边的 Prim',
    '增加虚拟电源 0，连接城市 i 的费用为建站费 c_i，城市间边权为曼哈顿距离乘 (k_i+k_j)。对这张隐式完全图做 Prim，同时记录每个城市是建站还是接线。',
    '一个合法供电网络中，每座城市都必须通过线路连到某座电站。增加虚拟点 0，把建站看作连接 0 的一条边后，供电要求就等价于所有城市与 0 连通，目标为最小生成树。\n\n初始化每个城市的最佳费用为它自己的建站费、来源为 0，表示已经把虚拟点加入树。每轮选费用最小的未选城市，累加费用并记录它的来源；随后用它到其它城市的线路费用尝试改进。\n\n来源为 0 的城市需要建站，其余来源记录一条电线。Prim 的割性质保证总价最小。n<=2000，平方扫描即可，不必储存全部城市边；费用乘积与总额用 long long。',
    '时间 O(n²)，空间 O(n)。','允许建多座电站；线路单价是两城市 k 之和；记录来源并输出实际方案。',r'''
int n;cin>>n;vector<long long>x(n),y(n),c(n),k(n),distance;for(int i=0;i<n;i++)cin>>x[i]>>y[i];for(auto &v:c)cin>>v;for(auto &v:k)cin>>v;distance=c;vector<int>from(n,-1),stations;vector<pair<int,int>>wires;vector<char>used(n);long long answer=0;for(int step=0;step<n;step++){int v=-1;for(int i=0;i<n;i++)if(!used[i]&&(v<0||distance[i]<distance[v]))v=i;used[v]=1;answer+=distance[v];if(from[v]<0)stations.push_back(v+1);else wires.push_back({from[v]+1,v+1});for(int u=0;u<n;u++)if(!used[u]){long long cost=(llabs(x[u]-x[v])+llabs(y[u]-y[v]))*(k[u]+k[v]);if(cost<distance[u]){distance[u]=cost;from[u]=v;}}}cout<<answer<<'\n'<<stations.size()<<'\n';for(int v:stations)cout<<v<<' ';cout<<'\n'<<wires.size()<<'\n';for(auto [a,b]:wires)cout<<a<<' '<<b<<'\n';
''',checker='power-grid')

add('UVA1151','枚举套餐并在基础 MST 上补边',
    '套餐至多八个，枚举购买子集，把每个套餐城市先合并，再用最小生成树边补齐网络。基础道路的 MST 可先用 Prim 求出；加入零费用套餐边后，只在这棵 MST 上继续 Kruskal 就足够。',
    '购买套餐后，它包含的城市内部可以看作零费用连通，而套餐本身代价固定。枚举购买子集，就把选择套餐与铺普通道路分开。\n\n先在完整平方距离图上用 Prim 得到一棵基础 MST。往图中加入一条零费用边时，可以在原 MST 加这条边形成的环中删去最重边，得到新 MST；反复加入所有套餐内部边后，最优树始终可从“原 MST 加新增零边”中取得。因此不需要为每个子集重新扫描平方条普通边。\n\n对每个套餐子集重新建并查集，累计套餐费，并把同套餐城市合并；再按权值递增扫描基础 MST 的 n−1 条边，连接不同块就付费。所有子集的最小总额即答案。输入按原题先给套餐，再给城市坐标，测试组之间输出空行。',
    '时间 O(n²+2^q·(n+套餐总人数))，空间 O(n+套餐总人数)。','套餐费一次支付；普通路费为平方距离；每个子集重建并查集。',r'''
int tests;cin>>tests;for(int test=0;test<tests;test++){int n,q;cin>>n>>q;vector<vector<int>>packages(q);vector<long long>price(q);for(int i=0;i<q;i++){int size;cin>>size>>price[i];packages[i].resize(size);for(int &v:packages[i]){cin>>v;v--;}}vector<long long>x(n),y(n);for(int i=0;i<n;i++)cin>>x[i]>>y[i];vector<long long>distance(n,LLONG_MAX);vector<int>from(n,-1);vector<char>used(n);vector<tuple<long long,int,int>>edges;distance[0]=0;for(int step=0;step<n;step++){int v=-1;for(int i=0;i<n;i++)if(!used[i]&&(v<0||distance[i]<distance[v]))v=i;used[v]=1;if(from[v]>=0)edges.push_back({distance[v],from[v],v});for(int u=0;u<n;u++)if(!used[u]){long long dx=x[u]-x[v],dy=y[u]-y[v],cost=dx*dx+dy*dy;if(cost<distance[u]){distance[u]=cost;from[u]=v;}}}sort(edges.begin(),edges.end());long long answer=LLONG_MAX;for(int mask=0;mask<(1<<q);mask++){DSU d(n);long long cost=0;for(int i=0;i<q;i++)if((mask>>i)&1){cost+=price[i];for(int v:packages[i])d.join(packages[i][0],v);}for(auto [w,a,b]:edges)if(d.join(a,b))cost+=w;answer=min(answer,cost);}if(test)cout<<'\n';cout<<answer<<'\n';}
''',DSU)

add('UVA1665','倒序海平面下激活陆地',
    '把格子按高度降序、询问按海平面降序处理。高于当前海平面的格子才是陆地，逐个激活并与四邻陆地合并，维护连通块数。',
    '正向海平面升高会删除格子，让连通块拆分，并查集不适合；反过来从高海平面向低海平面处理，则只会增加格子和合并，正好适合并查集。\n\n按高度从大到小激活所有严格高于当前水位的格子。一个新格子先贡献一个岛屿，每次与一个不同的相邻陆地块合并成功就减一。已经同属一块的邻居不能重复减，否则会因环把岛屿数扣错。\n\n用格子下标 x·m+y 表示顶点，邻接仅共享边的四个方向。询问保存原编号，最后按原输入顺序在同一行输出。等于海平面的格子已经被淹没，激活条件必须是严格大于。',
    '时间 O(nm log(nm)+T log T)，空间 O(nm+T)。','海水能进入所有低格，无需从边界灌水；严格高于水位才激活；使用四邻域。',r'''
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;int count=n*m;vector<int>height(count),order(count);for(int &x:height)cin>>x;iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return height[a]>height[b];});int q;cin>>q;vector<pair<int,int>>queries(q);for(int i=0;i<q;i++){cin>>queries[i].first;queries[i].second=i;}sort(queries.rbegin(),queries.rend());DSU d(count);vector<char>active(count);vector<int>answer(q);int position=0,islands=0;for(auto [water,id]:queries){while(position<count&&height[order[position]]>water){int v=order[position++],x=v/m,y=v%m;active[v]=1;islands++;for(auto [dx,dy]:vector<pair<int,int>>{{1,0},{-1,0},{0,1},{0,-1}}){int a=x+dx,b=y+dy;if(a>=0&&a<n&&b>=0&&b<m&&active[a*m+b]&&d.join(v,a*m+b))islands--;}}answer[id]=islands;}for(int i=0;i<q;i++)cout<<answer[i]<<(i+1==q?'\n':' ');}
''',DSU)

LOWLINK=r'''
struct Lowlink{
 int n,timer=0;vector<vector<pair<int,int>>>g;vector<pair<int,int>>edges;vector<int>tin,low,parent,parentEdge,children,size;vector<char>bridge,cut;vector<vector<int>>blocks;
 Lowlink(int n):n(n),g(n),tin(n),low(n),parent(n,-1),parentEdge(n,-1),children(n),size(n,1),cut(n){}
 void edge(int a,int b){int id=edges.size();edges.push_back({a,b});g[a].push_back({b,id});g[b].push_back({a,id});}
 void build(){bridge.assign(edges.size(),0);vector<int>vertices;
 for(int root=0;root<n;root++)if(!tin[root]){vector<pair<int,int>>st={{root,0}};tin[root]=low[root]=++timer;vertices.push_back(root);
 while(!st.empty()){int v=st.back().first;int &next=st.back().second;
 if(next<(int)g[v].size()){auto [u,id]=g[v][next++];if(id==parentEdge[v])continue;
 if(!tin[u]){parent[u]=v;parentEdge[u]=id;children[v]++;tin[u]=low[u]=++timer;vertices.push_back(u);st.push_back({u,0});}
 else low[v]=min(low[v],tin[u]);
 }else{st.pop_back();int p=parent[v];if(p>=0){size[p]+=size[v];low[p]=min(low[p],low[v]);bridge[parentEdge[v]]=low[v]>tin[p];
 if(low[v]>=tin[p]){if(parent[p]>=0)cut[p]=1;vector<int>block={p};while(true){int u=vertices.back();vertices.pop_back();block.push_back(u);if(u==v)break;}blocks.push_back(move(block));}}
 else{cut[v]=children[v]>1;if(children[v]==0)blocks.push_back({v});vertices.pop_back();}}
 }}}
};
'''
LOW_START=r'''
int n,m;cin>>n>>m;Lowlink graph(n);for(int i=0;i<m;i++){int a,b;cin>>a>>b;graph.edge(a-1,b-1);}graph.build();
'''
LOW_REASON='在 DFS 树中，tin[u] 是首次访问顺序，low[u] 是从 u 的子树沿树边向下、再经至多一条返祖边能到达的最早顺序。处理完孩子 v 后，若 low[v]>=tin[u]，它的子树无法绕过 u 到达更早祖先，形成一个点双块的分界；若严格大于，则父子边还是桥。\n\n代码用显式栈保存当前顶点与下一条邻边，模拟递归进入和退出。无向边按边编号识别，只跳过同一条父边，避免把平行边全部跳过。\n\n'

add('P3388','lowlink 判定割点',
    '非根点若有孩子 v 满足 low[v]>=tin[u]，删除 u 会把该孩子子树分开，因此是割点。DFS 根仅在拥有至少两个搜索树孩子时是割点。',
    LOW_REASON+'非根 u 的父亲及祖先构成一侧，孩子子树若不能借返祖边绕过 u，就在删点后与这一侧分离，所以是割点。若每个孩子都能绕到更早祖先，删除 u 后它们仍能通过祖先侧相互连接，就不是割点。\n\n根没有父亲一侧，不能沿用相同条件。根的不同 DFS 孩子之间不可能存在绕过根的边，否则它们早已属于同一搜索分支；因此根的孩子数大于一才是割点。对每个未访问点重新启动 DFS，覆盖非连通图。',
    '时间 O(n+m)，空间 O(n+m)。','根与非根判定不同；按父边编号跳过；全图可能不连通。',
    LOW_START+r'''cout<<count(graph.cut.begin(),graph.cut.end(),1)<<'\n';for(int i=0;i<n;i++)if(graph.cut[i])cout<<i+1<<' ';cout<<'\n';''',LOWLINK)

for pid,ordered in [('B3610',True),('P8435',False)]:
    body=LOW_START
    if ordered:body+=r'''
vector<vector<int>>blocks;for(auto block:graph.blocks){if(block.size()==1&&graph.g[block[0]].empty())continue;for(int &v:block)v++;sort(block.begin(),block.end());blocks.push_back(move(block));}sort(blocks.begin(),blocks.end());cout<<blocks.size()<<'\n';for(auto &block:blocks){for(int v:block)cout<<v<<' ';cout<<'\n';}
'''
    else:body+=r'''
cout<<graph.blocks.size()<<'\n';for(auto &block:graph.blocks){cout<<block.size();for(int v:block)cout<<' '<<v+1;cout<<'\n';}
'''
    add(pid,'顶点栈提取点双连通块',
        'DFS 时把新顶点压入栈。当孩子 v 满足 low[v]>=tin[u]，从栈顶弹到 v，并补上 u，得到一个点双块。割点可属于多个块。'+('孤立点按本题约定不输出，块内和块间都按字典序整理。' if ordered else '孤立点以及只有自环的单点各形成一个单点块。'),
        LOW_REASON+'顶点栈保存尚未归入完整块的搜索分支。当 low[v]>=tin[u] 时，v 子树的这一段无法绕到 u 之前，它与 u 恰好形成一个最大无割点子图。弹出直至 v，把 u 加入这一块；u 本身仍留在栈中，便能参与其它相邻块。\n\n'+('B3610 的块与“边双连通分量”不同，桥的两个端点本身形成一块。按题目约定去掉无边孤立点，然后对每块排序，再按整个成员序列排序输出，不在行首输出大小。' if ordered else 'P8435 要求保留孤立点。一个 DFS 根没有树孩子时，直接输出它自身作为单点块；这同样覆盖只有自环的单点。普通自环不会产生新的跨点关系，也不会额外拆出一个已被更大块包含的单点块。')+'\n\n平行边用边编号区分，第二条到父亲的边是合法返祖边。不同原连通分量分别搜索。',
        '时间 O(n+m)'+('，输出排序额外需要 O(m log m)' if ordered else '')+'，空间 O(n+m)。',
        '不要误写成边双分量；割点可以重复出现在多个块；按本题约定处理孤立点。',body,LOWLINK,checker='' if ordered else 'vertex-blocks')

add('P3469','统计删除顶点后各分块的有序点对',
    '利用 lowlink 找出删点后分离的孩子子树，大小记为 s。不同分块间的有序点对贡献 Σs(n−1−s)，再加上以被删顶点为端点的 2(n−1) 对。',
    LOW_REASON+'图原本连通，删除 u 后，满足 low[v]>=tin[u] 的孩子子树会分别成为独立分块，其余未分离部分合在一起。用子树大小即可得出每块点数。\n\n对一个大小为 s 的块，它与剩下 n−1−s 个点之间有 s(n−1−s) 个以本块为起点的有序点对。对所有块求和，每个跨块无向点对自然按两个方向各计一次。最后还有所有以 u 为起点或终点的 2(n−1) 个点对，它们也因 u 被封锁而不可通行。\n\n累计分离孩子大小及对应贡献，再用剩余大小 n−1−sum 补上最后一块。根也可以统一这样计数，因为它没有祖先侧，其所有孩子都形成分离块，剩余大小自然为零。',
    '时间 O(n+m)，空间 O(n+m)。','统计有序点对；包含被封锁点作为端点的情况；答案用 long long。',
    LOW_START+r'''
vector<long long>answer(n,2LL*(n-1)),separated(n);for(int v=0;v<n;v++){int p=graph.parent[v];if(p>=0&&graph.low[v]>=graph.tin[p]){long long s=graph.size[v];answer[p]+=s*(n-1-s);separated[p]+=s;}}for(int v=0;v<n;v++){long long rest=n-1-separated[v];answer[v]+=rest*(n-1-rest);cout<<answer[v]<<'\n';}
''',LOWLINK)

add('CF1000E','桥缩成树后求直径',
    '非桥边位于环内，不会成为两点间所有路径都必须经过的边。把非桥连接的点合并，剩下桥形成树；需要的最大必经桥数就是这棵树的直径。',
    LOW_REASON+'删除非桥不会让图分开，桥才可能成为两个位置之间无法绕开的必经连接。把所有非桥边连接的点压成一个块，块之间的边都是桥，缩点图是树。\n\n对于任意两点，其间必经桥的数量正好等于所属块在树上的距离。要让这个数量最大，就是求树直径。任选一块 BFS 得到最远块 A，再从 A BFS，最大距离即为直径。\n\n原图没有桥时全部缩成一个块，直径为零。并查集合并非桥边后，可直接把代表元作为树顶点编号，不必重新分配连续编号。',
    '时间 O(n+m)，空间 O(n+m)。','只合并非桥；树距离按边数；没有桥时输出 0。',
    LOW_START+r'''
DSU d(n);for(int i=0;i<(int)graph.edges.size();i++)if(!graph.bridge[i])d.join(graph.edges[i].first,graph.edges[i].second);vector<vector<int>>tree(n);for(int i=0;i<(int)graph.edges.size();i++)if(graph.bridge[i]){auto [a,b]=graph.edges[i];a=d.find(a);b=d.find(b);tree[a].push_back(b);tree[b].push_back(a);}auto farthest=[&](int start){vector<int>distance(n,-1);queue<int>q;q.push(start);distance[start]=0;int best=start;while(!q.empty()){int v=q.front();q.pop();if(distance[v]>distance[best])best=v;for(int u:tree[v])if(distance[u]<0){distance[u]=distance[v]+1;q.push(u);}}return pair<int,int>{best,distance[best]};};auto [a,unused]=farthest(d.find(0));cout<<farthest(a).second<<'\n';
''',LOWLINK+DSU)

add('CF1777E','二分反向阈值与唯一源强连通分量',
    '权值不超过 x 的边允许反转，就先把它视作双向边。存在能到达全图的起点，当且仅当该图缩点后只有一个入度为零的分量。按阈值二分最小 x。',
    '若某条边允许反转，在判断“是否存在一条从根出发的生成有向树”时，可以暂时同时保留两个方向。找到生成树后，每条树边只需一个方向，因此可以按树实际使用方向给原边定向，不会出现同一条边必须同时取两向的冲突。\n\n在任意有向图中，一个点能到达所有点，当且仅当缩点 DAG 有唯一源分量。必要性显然：其它源无法从外部进入。充分性来自 DAG 中每个点都能从某个源到达，源唯一时便能覆盖全图。\n\n阈值增大会增加反向边，不会破坏可行性。先以最大边权检查是否有解；不可行则输出 −1，否则在零到最大权之间二分第一个可行值。',
    '每组时间 O((n+m) log W)，空间 O(n+m)。','判定唯一源而非唯一汇；阈值含等号；最大阈值仍不连通则无解。',r'''
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<tuple<int,int,int>>edges(m);int maximum=0;for(auto &[a,b,w]:edges){cin>>a>>b>>w;a--;b--;maximum=max(maximum,w);}auto ok=[&](int limit){SCC s(n);for(auto [a,b,w]:edges){s.edge(a,b);if(w<=limit)s.edge(b,a);}s.build();vector<char>in(s.count);for(auto [a,b,w]:edges){if(s.component[a]!=s.component[b]){in[s.component[b]]=1;if(w<=limit)in[s.component[a]]=1;}}return count(in.begin(),in.end(),0)==1;};if(!ok(maximum)){cout<<-1<<'\n';continue;}int l=0,r=maximum;while(l<r){int mid=l+(r-l)/2;if(ok(mid))r=mid;else l=mid+1;}cout<<l<<'\n';}
''',SCC)

add('P8097','逆序恢复道路与活跃农场',
    '从最终状态开始，逆序把 R 恢复为加边、D 恢复为激活。某个无活跃点的块首次接入活跃块时，里面尚未确定的农场最后相关时间就是当前时刻。A 的逆操作可忽略，因为当时两端仍活跃。',
    '从后向前看，每个农场第一次恢复为“有关”时，正好找到了它在正向过程中的最后有关时刻。逆序 R 会恢复一条边，逆序 D 会激活一个农场，这两类操作只会增加相关性，适合并查集。\n\n逆序 A 本来应该删边，但题目保证加边时两端都活跃，所以这条边在更早时刻即使保留，也只会连接两个本来就有关的点，不会凭空把无关块变为有关。随着逆序进行，它们仍保持活跃。因此可以忽略这个删边，整个逆过程只剩合并与激活。\n\n每个并查集块保存是否含活跃点，以及其中尚未确定答案的顶点列表。激活或合并后，只要块变得有关，就为列表内所有点写下当前时间并清空。每个点只被写一次；列表按小块并入大块，避免反复搬运过多。\n\n先在最终保留的道路上合并，用最终仍活跃的农场给出时间 Q 的答案，再从第 Q 次操作倒退。撤销第 i 次操作后是时刻 i−1，不能误写成 i。',
    '时间 O((n+q) log n)，空间 O(n+q)。','逆序时间为 i−1；最后仍有关的点答案 Q；忽略 A 依赖加边两端活跃的原题保证。',r'''
int n,q;cin>>n>>q;vector<Operation>operations(q);vector<pair<int,int>>edges;vector<char>removed,active(n,1);for(auto &op:operations){cin>>op.kind>>op.x;op.x--;if(op.kind=='A'){cin>>op.y;op.y--;edges.push_back({op.x,op.y});removed.push_back(0);}else if(op.kind=='R')removed[op.x]=1;else active[op.x]=0;}DSU d(n);vector<char>relevant(n);vector<vector<int>>pending(n);vector<int>answer(n,-1);for(int i=0;i<n;i++)pending[i]={i};auto mark=[&](int root,int time){root=d.find(root);relevant[root]=1;for(int v:pending[root])answer[v]=time;pending[root].clear();};auto unite=[&](int a,int b,int time){a=d.find(a);b=d.find(b);if(a==b)return;if(d.size[a]<d.size[b])swap(a,b);d.p[b]=a;d.size[a]+=d.size[b];pending[a].insert(pending[a].end(),pending[b].begin(),pending[b].end());pending[b].clear();relevant[a]|=relevant[b];if(relevant[a])mark(a,time);};for(int i=0;i<(int)edges.size();i++)if(!removed[i])unite(edges[i].first,edges[i].second,q);for(int v=0;v<n;v++)if(active[v])mark(v,q);for(int i=q-1;i>=0;i--){auto op=operations[i];if(op.kind=='D')mark(op.x,i);else if(op.kind=='R')unite(edges[op.x].first,edges[op.x].second,i);}for(int x:answer)cout<<x<<'\n';
''',DSU+r'''
struct Operation{char kind;int x,y=0;};
''')

add('P11380','把唯一前后继关系压成链',
    '每人最多有一个必须紧邻的前驱和后继。若出现冲突或有向环就无解；否则各条定向链内部顺序固定，把链当作整体任意排列，答案为链数的阶乘。',
    '约束 a 紧挨着 b 前面，意味着 next[a]=b 且 previous[b]=a。某人若被要求接两个不同后继或前驱，无法同时满足；重复的同一条约束则没有新增限制。\n\n没有冲突时，每个点入度、出度至多一，连通结构只能是定向链或定向环。环不可能放到一条直线队伍中。从所有没有前驱的人出发沿后继遍历，若未覆盖全部人，就说明剩余结构中存在环。\n\n合法时，每条链的内部次序被完全确定，且不能在中间插入其它人，否则破坏相邻关系。不同链之间没有约束，所以把链作为整体排列，有 K! 种。单独一个人也算一条链。',
    '时间 O(n+m)，空间 O(n)。','重复约束不重复计数；自环无解；检查所有点是否属于某条链。',r'''
int n,m;cin>>n>>m;vector<int>next(n+1),previous(n+1);bool ok=true;while(m--){int a,b;cin>>a>>b;if(a==b||(next[a]&&next[a]!=b)||(previous[b]&&previous[b]!=a))ok=false;else{next[a]=b;previous[b]=a;}}int chains=0,visited=0;for(int i=1;i<=n;i++)if(!previous[i]){chains++;for(int v=i;v;v=next[v])visited++;}if(!ok||visited!=n){cout<<0<<'\n';return 0;}long long ans=1;for(int i=1;i<=chains;i++)ans=ans*i%1000000007;cout<<ans<<'\n';
''')

add('P4961','零格连通块展开后统计剩余数字',
    '先计算每个非雷格周围雷数。每个八连通零格块只需点一次，并会自动展开周围数字；最后仍未展开的非雷数字格各需再点一次。',
    '没有邻雷的空格被点开后，会自动展开相邻空格及其周围数字，因此整个八连通空格块只需一次点击。不同空格块无法互相展开，至少各点一次，这给出了必要点击数。\n\n先统计八邻域雷数。遇到尚未访问的零格时，答案加一，BFS 遍历这个零块，并把它周围所有非雷格标为已展开；只把零格加入队列，数字格不能继续扩张。\n\n完成全部零块后，尚未展开的非雷格都不与任何零格相邻，无法借助自动展开，只能逐个点击。因此各加一，得到下界可实现的最少次数。',
    '时间 O(nm)，空间 O(nm)。','使用八邻域；数字只标记，不继续入队扩张；雷格始终不点击。',r'''
int n,m;cin>>n>>m;vector<vector<int>>a(n,vector<int>(m)),near=a;for(auto &row:a)for(int &x:row)cin>>x;for(int i=0;i<n;i++)for(int j=0;j<m;j++)for(int dx=-1;dx<=1;dx++)for(int dy=-1;dy<=1;dy++){int x=i+dx,y=j+dy;if(x>=0&&x<n&&y>=0&&y<m)near[i][j]+=a[x][y];}vector<vector<char>>seen(n,vector<char>(m));int ans=0;for(int i=0;i<n;i++)for(int j=0;j<m;j++)if(!a[i][j]&&!near[i][j]&&!seen[i][j]){ans++;queue<pair<int,int>>q;q.push({i,j});seen[i][j]=1;while(!q.empty()){auto [x,y]=q.front();q.pop();for(int dx=-1;dx<=1;dx++)for(int dy=-1;dy<=1;dy++){int u=x+dx,v=y+dy;if(u>=0&&u<n&&v>=0&&v<m&&!a[u][v]&&!seen[u][v]){seen[u][v]=1;if(!near[u][v])q.push({u,v});}}}}for(int i=0;i<n;i++)for(int j=0;j<m;j++)if(!a[i][j]&&!seen[i][j])ans++;cout<<ans<<'\n';
''')

add('P1025','非递减地枚举各部分',
    '把每个划分按非递减顺序写出，只枚举这种规范顺序，避免同一组数的排列重复。递归记录剩余和、剩余份数与下一份最小值。',
    '划分不区分各部分的先后，所以同一组正整数若按任意顺序枚举，会重复。规定每一份不小于前一份后，每个划分就有唯一表示。\n\n状态 solve(sum,count,minimum) 表示还需 count 个不小于 minimum 的正整数凑成 sum。下一份 x 不能大于 sum/count，否则剩余每份都至少 x，总和就会超过 sum。枚举 minimum 到 sum/count，递归求 sum−x、count−1、x。\n\n只剩一份时，只要 sum>=minimum 就恰有一种分法。该终止条件同时处理相等部分，不需要集合去重。',
    '时间为实际枚举的划分状态数，递归空间 O(k)。','各份必须正数；下一份可以等于上一份；上界用剩余和除剩余份数。',r'''
int n,k;cin>>n>>k;function<long long(int,int,int)>solve=[&](int sum,int count,int minimum)->long long{if(count==1)return sum>=minimum;long long ans=0;for(int x=minimum;x<=sum/count;x++)ans+=solve(sum-x,count-1,x);return ans;};cout<<solve(n,k,1)<<'\n';
''')

add('P2080','按好感差保存最大好感和',
    '每件事贡献差值 a−b 和总值 a+b。用 0/1 背包维护每个差值下能得到的最大总值，最后在总值达到 v 的状态中取差值绝对值最小者。',
    '两人能否走到一起取决于总好感，幸福程度取决于差的绝对值，因此把原来的两个维度变成“差值”和“总和”。固定差值时，总和越大永远越好，其它较小总和可以丢弃。\n\n令 dp[d] 为选若干已处理事件后，差值 d 能达到的最大总和。初始只有差零、和零可达。对每个事件，从旧数组复制一份表示不选，再把旧状态加上本次差与和，更新新数组。使用两个版本可以同时处理正负差，避免原地扫描方向错误。\n\n每个差绝对值最多二百，三十件事的总差范围只有六千。用偏移量把负差映射到数组下标，处理完后枚举满足 dp[d]>=v 的状态，取 |d| 最小；没有状态就输出 −1。',
    '时间 O(n²A)，空间 O(nA)，A 为单项差值的上界。','好感可负；保留最大总和而非最小；转移使用旧数组，防止重复选事件。',r'''
int n,v;cin>>n>>v;vector<pair<int,int>>events(n);int bound=0;for(auto &[a,b]:events){cin>>a>>b;bound+=abs(a-b);}const int neg=INT_MIN/4;vector<int>dp(2*bound+1,neg);dp[bound]=0;for(auto [a,b]:events){auto next=dp;int difference=a-b;for(int i=0;i<(int)dp.size();i++)if(dp[i]!=neg&&i+difference>=0&&i+difference<(int)dp.size())next[i+difference]=max(next[i+difference],dp[i]+a+b);dp.swap(next);}int ans=INT_MAX;for(int i=0;i<(int)dp.size();i++)if(dp[i]>=v)ans=min(ans,abs(i-bound));cout<<(ans==INT_MAX?-1:ans)<<'\n';
''')

add('P4888','从给定中心向两边直接扩展',
    '每次询问分别沿所在行和列向两侧同步扩展，只要两侧字母相同就继续。中心固定为一个格子，因此只需检查奇数长度回文，取水平和竖直的最大值。',
    '题目只问给定格子为中心的回文，不要求预处理全部中心。中心是一个实际格子，所以所有合法回文长度都是奇数，初始长度为一。\n\n沿水平方向比较左右距离一的两格，再比较距离二，直到越界或不相同为止。由于更长回文必须包含更短回文，第一次失败后不可能再有更大半径。竖直方向完全相同。\n\n每次最多检查矩阵边长的常数倍，边长和询问数都不超过两千，总比较次数只有几百万，直接扩展已经足够。这样实现比为所有行列建立哈希更简单，且没有碰撞。',
    '每次 O(l)，总时间 O(l²+ql)，空间 O(l²)。','坐标转为 0 起始；只取水平或竖直，不能走对角线；中心本身长度为 1。',r'''
int n,q;cin>>n>>q;vector<string>a(n);for(auto &s:a)cin>>s;while(q--){int x,y;cin>>x>>y;x--;y--;int horizontal=0,vertical=0;while(y-horizontal-1>=0&&y+horizontal+1<n&&a[x][y-horizontal-1]==a[x][y+horizontal+1])horizontal++;while(x-vertical-1>=0&&x+vertical+1<n&&a[x-vertical-1][y]==a[x+vertical+1][y])vertical++;cout<<2*max(horizontal,vertical)+1<<'\n';}
''')

add('P1032','正反各五步的双向 BFS',
    '从起始串按原规则搜索至五步，从目标串按反向规则搜索至五步。任意不超过十步的最短路径都能在两边覆盖的某个中间串相遇，取两侧距离和的最小值。',
    '一次操作只能替换某个具体出现位置的子串，所以同一条规则在一个字符串中可能产生多个后继，必须枚举全部出现位置，包括相互重叠的位置。BFS 首次访问某串的层数就是最少替换次数。\n\n十层单向搜索分支可能太多，改为两边各搜五层。反向搜索把每条规则的左右串交换；如果存在长度 L<=10 的路径，可在距离起点 min(5,L) 的位置切开，剩余长度也不超过五，所以两个搜索集合必有交集。\n\n每边用映射保存最短距离并去重，深度五的状态保留但不继续扩展。最后枚举交集，取距离和最小者；超过十步或没有交集时输出 NO ANSWER!。',
    '时间与五层内实际产生的不同字符串及匹配位置数量成正比，空间与访问状态总长度成正比。','枚举同规则所有出现位置；反向规则要交换两端；恰好十步也允许。',r'''
string start,goal;cin>>start>>goal;vector<pair<string,string>>rules;string a,b;while(cin>>a>>b)rules.push_back({a,b});auto search=[&](string initial,bool reverseRule){unordered_map<string,int>distance;queue<string>q;distance[initial]=0;q.push(initial);while(!q.empty()){string s=q.front();q.pop();int depth=distance[s];if(depth==5)continue;for(auto rule:rules){string from=reverseRule?rule.second:rule.first,to=reverseRule?rule.first:rule.second;for(size_t pos=s.find(from);pos!=string::npos;pos=s.find(from,pos+1)){string next=s.substr(0,pos)+to+s.substr(pos+from.size());if(distance.emplace(next,depth+1).second)q.push(next);}}}return distance;};auto forward=search(start,false),backward=search(goal,true);int ans=11;for(auto &[s,d]:forward){auto it=backward.find(s);if(it!=backward.end())ans=min(ans,d+it->second);}if(ans<=10)cout<<ans<<'\n';else cout<<"NO ANSWER!\n";
''')

add('P6004','二分虫洞宽度并检查置换连通性',
    '固定最小宽度 W，只保留宽度至少 W 的虫洞。每头牛的当前位置与目标位置在同一个连通块时且仅时能完成排序，二分最大的可行 W。已经有序时按题意输出 -1。',
    '同一连通块内，沿道路的相邻交换可以生成任意排列，因此牛能被送回目标位置，当且仅当它当前的位置和目标位置属于同一连通块。不同块之间无法交换，这个条件也是必要的。\n\n若要求最窄虫洞至少为 W，就只能使用宽度不小于 W 的边。用并查集连接这些边，再检查每个位置 i 与 permutation[i] 是否同块。W 越小可用边越多，条件单调。\n\n二分最大可行宽度。若输入本来已经有序，不需要经过任何虫洞，原题要求输出 −1，必须在二分前特判。',
    '时间 O((n+m) log W·α(n))，空间 O(n+m)。','保留宽度大于等于阈值的边；检查牛与目标位置；已排序输出 -1。',r'''
int n,m;cin>>n>>m;vector<int>p(n+1);bool sorted=true;for(int i=1;i<=n;i++){cin>>p[i];sorted&=p[i]==i;}vector<tuple<int,int,int>>edges(m);int maximum=0;for(auto &[a,b,w]:edges){cin>>a>>b>>w;maximum=max(maximum,w);}if(sorted){cout<<-1<<'\n';return 0;}auto ok=[&](int limit){DSU d(n+1);for(auto [a,b,w]:edges)if(w>=limit)d.join(a,b);for(int i=1;i<=n;i++)if(d.find(i)!=d.find(p[i]))return false;return true;};int l=0,r=maximum;while(l<r){int mid=l+(r-l+1)/2;if(ok(mid))l=mid;else r=mid-1;}cout<<l<<'\n';
''',DSU)

add('P13461','筛出能连接区间内两数的质因子',
    '若质数 p>B−A，它在区间内至多有一个倍数，无法产生合并。因此只筛到区间长度，对 p≥P 的倍数逐个与第一个倍数合并，最后统计并查集块数。',
    '两个不同的 p 倍数相差至少 p；如果 p 超过区间宽度 B−A，就不可能同时出现两个倍数，因此无需分解高达十的十二次方的端点。\n\n对每个 P<=p<=B−A 的质数，算出区间内第一个倍数 first=ceil(A/p)p，再把后续 first+p、first+2p… 全部与 first 合并。这相当于把共享该质因子的所有数连成一组，所有质因子处理后，传递合并也由并查集自动完成。\n\n并查集下标使用数值减 A，只需 B−A+1 个元素。每次合并成功就把集合数减一，按 Case #编号输出。',
    '每组时间 O(D log log D)，空间 O(D)，D=B−A。','只筛到区间宽度；端点运算用 long long；质因子阈值含等号。',r'''
int tests;cin>>tests;for(int test=1;test<=tests;test++){long long a,b,minimum;cin>>a>>b>>minimum;int width=b-a;vector<char>composite(width+1);DSU d(width+1);int answer=width+1;for(int p=2;p<=width;p++)if(!composite[p]){for(int j=p+p;j<=width;j+=p)composite[j]=1;if(p<minimum)continue;long long first=(a+p-1)/p*p;for(long long x=first+p;x<=b;x+=p)if(d.join(first-a,x-a))answer--;}cout<<"Case #"<<test<<": "<<answer<<'\n';}
''',DSU)

add('P1265','隐式完全图上的 Prim',
    '每两个城镇之间都能修路，权值为欧氏距离。无需生成全部边，用 Prim 保存每个未加入城镇到当前树的最短距离，逐个加入最近者。',
    '完整图有平方数量的边，把它们全部存下并排序没有必要。Prim 每次只需要知道每个未选点到已选集合的最短连接距离。\n\n初始任选一个城镇，距离为零。每轮扫描所有未选点，挑连接距离最小者加入，费用累加它的距离；再用新点到其它未选点的直线距离更新记录。这个选择始终是跨越“已选与未选”割的最小边，满足最小生成树割性质。\n\n比较时可以保存距离平方，只在实际加入点时开平方累加，从而减少开方调用。总共 n 轮，每轮线性扫描，空间仅为坐标、距离和选中标记。',
    '时间 O(n²)，空间 O(n)。','距离比较可用平方；加入时才开方；答案保留两位小数。',r'''
int n;cin>>n;vector<long double>x(n),y(n),distance(n,numeric_limits<long double>::infinity());for(int i=0;i<n;i++)cin>>x[i]>>y[i];vector<char>used(n);distance[0]=0;long double ans=0;for(int step=0;step<n;step++){int v=-1;for(int i=0;i<n;i++)if(!used[i]&&(v<0||distance[i]<distance[v]))v=i;used[v]=1;ans+=sqrt(distance[v]);for(int u=0;u<n;u++)if(!used[u])distance[u]=min(distance[u],(x[u]-x[v])*(x[u]-x[v])+(y[u]-y[v])*(y[u]-y[v]));}cout<<fixed<<setprecision(2)<<ans<<'\n';
''')

SCC_START=r'''
int n,m;cin>>n>>m;SCC s(n);for(int i=0;i<m;i++){int a,b;cin>>a>>b;s.edge(a-1,b-1);}s.build();vector<int>size(s.count),in(s.count),out(s.count);for(int v=0;v<n;v++){size[s.component[v]]++;for(int u:s.g[v])if(s.component[u]!=s.component[v]){out[s.component[v]]++;in[s.component[u]]++;}}
'''
SCC_REASON='强连通分量内任意两点互相可达，分量之间压缩后形成有向无环图。代码用两遍非递归 DFS：先在原图记录退出顺序，再按退出顺序逆序遍历反图，每次搜索恰好得到一个分量。显式栈记录当前顶点与下一条待访问边，保证记录的是退出顺序。\n\n'

add('B3609','两遍 DFS 划分强连通分量',
    '先求各点所属强连通分量，再按顶点编号递增把点放入对应分组。各分组按最小顶点递增输出，组内也保持递增。',
    SCC_REASON+'第一遍的退出顺序能把缩点图中较靠前的分量优先留给第二遍；第二遍沿反边无法越过尚未处理的前驱，所以一次搜索不会混入别的分量。\n\n算法内部产生的分量编号不一定符合题目输出顺序。求完编号后，按 1 到 n 顺序收集各组成员，组内天然有序。再按每组最小成员排序，得到题目要求的“先输出最小未输出顶点所在组”。重边与自环不会影响访问标记。',
    '时间 O(n+m+n log n)，空间 O(n+m)。','输出顺序要单独整理；第一遍记录退出顺序；重边和自环不重复访问。',
    SCC_START+r'''vector<vector<int>>groups(s.count);for(int v=0;v<n;v++)groups[s.component[v]].push_back(v+1);sort(groups.begin(),groups.end(),[](const auto&a,const auto&b){return a[0]<b[0];});cout<<s.count<<'\n';for(auto &group:groups){for(int v:group)cout<<v<<' ';cout<<'\n';}''',SCC)

add('P1726','最大强连通分量与字典序',
    '双向道路建两条边，求强连通分量。按编号顺序收集成员，选择人数最多、并列时字典序最小的一组。',
    SCC_REASON+'题目中的“绝对连通”正是互相可达，因此最大绝对连通区域就是最大的强连通分量。单向道路只添加一条边，双向道路添加两个方向。\n\n扫描顶点 1 到 n，把它放入所属组，保证每组成员递增。比较两组时先看大小，大小相同再比较整个 vector 的字典序。分量互不相交，所以并列时也可比较最小成员，但直接比较 vector 更直观。',
    '时间 O(n+m)，空间 O(n+m)。','t=2 要建双向边；并列按升序成员表比较。',r'''
int n,m;cin>>n>>m;SCC s(n);while(m--){int a,b,t;cin>>a>>b>>t;s.edge(a-1,b-1);if(t==2)s.edge(b-1,a-1);}s.build();vector<vector<int>>groups(s.count);for(int v=0;v<n;v++)groups[s.component[v]].push_back(v+1);vector<int>ans;for(auto &v:groups)if(v.size()>ans.size()||(v.size()==ans.size()&&v<ans))ans=v;cout<<ans.size()<<'\n';for(int v:ans)cout<<v<<' ';cout<<'\n';
''',SCC)

add('P2341','缩点后寻找唯一的汇点',
    '能被所有牛到达的顶点必须位于缩点图的汇分量。只有一个出度为零的分量时，答案是它的大小；有多个时答案为零。',
    SCC_REASON+'同一分量内的牛互相可达，是否被其它分量到达也完全相同，所以答案一定包含整个分量。\n\n在有向无环图中，从任意点不断沿出边走，最终会到达一个出度为零的汇点。若汇点唯一，每个点最终都能到达它，因此该分量内每头牛都受欢迎。若有两个汇点，它们都没有出边，不可能互相到达，更不可能存在被二者共同到达的其它点。\n\n统计跨分量边带来的出度即可，自环和分量内部边不计。只关心是否为零，不需要去重平行边。',
    '时间 O(n+m)，空间 O(n+m)。','判断出度，不是入度；多个汇分量时输出 0。',
    SCC_START+r'''int target=-1;for(int c=0;c<s.count;c++)if(!out[c]){if(target!=-1){cout<<0<<'\n';return 0;}target=c;}cout<<size[target]<<'\n';''',SCC)

add('P2863','统计含至少两个顶点的强连通分量',
    '能通过若干单向道路互相联系的一群牛构成强连通分量。求分量大小，统计大小大于 1 的分量个数。',
    SCC_REASON+'每个符合要求的群体中，任意两头牛必须能够互相到达，因此它恰好属于一个强连通分量。不同强连通分量不能合并，否则就与最大互相可达集合的定义矛盾。\n\n题目要求至少两头牛组成群体，所以大小为一的分量不计，即使该顶点带有自环也不能把它当成两头牛。只需累计每个分量的顶点数，再统计大于一的项。',
    '时间 O(n+m)，空间 O(n+m)。','统计分量数，非顶点数；单点自环不构成两牛群体。',
    SCC_START+r'''int ans=0;for(int x:size)ans+=x>1;cout<<ans<<'\n';''',SCC)

add('P7251','最大分量与强连通增边数',
    '第一问取最大强连通分量大小。第二问在缩点 DAG 上数入度为零的源与出度为零的汇；已有一个分量时为 0，否则答案为两种数量的较大者。',
    SCC_REASON+'第一问要求所选点两两可达，所以恰好取一个最大分量。第二问中，每个源分量都必须获得一条新入边，每个汇分量都必须获得一条新出边，所以至少增加 max(源数,汇数) 条。\n\n这一界也能达到：在缩点 DAG 中把源到汇的可达链适当串接成环，再把未覆盖的源与汇接入，所需新增边数为两者较大者。这里仅输出数量，不需要构造具体增边。\n\n当原图本来只有一个强连通分量时，源和汇计数都是一，但无需任何新边，必须单独输出零。',
    '时间 O(n+m)，空间 O(n+m)。','一个分量时增边数为 0；内部边不影响源汇统计。',
    SCC_START+r'''cout<<*max_element(size.begin(),size.end())<<'\n';cout<<(s.count==1?0:max(count(in.begin(),in.end(),0),count(out.begin(),out.end(),0)))<<'\n';''',SCC)

add('P2812','缩点后统计源与汇',
    '第一问是缩点图中入度为零的分量数；第二问若只有一个分量为 0，否则是源分量数与汇分量数的较大者。',
    SCC_REASON+'软件在同一个强连通分量内能够传遍所有学校，因此初始只需在选中的每个分量里放一份。入度为零的源分量无法从其它分量获得软件，必须至少选择一个学校；而从所有源出发就能覆盖整个 DAG，所以源的数量也是充分的。\n\n要使整个图强连通，每个源必须有新入边、每个汇必须有新出边，至少需要两类数量的较大者；把源汇链串成循环可以达到这个下界。已有一个强连通分量时无需加边，但第一问仍需要一份软件。\n\n每所学校的邻接列表以 0 结束，不是逐行读取固定数量的边。',
    '时间 O(n+m)，空间 O(n+m)。','每行的 0 只是结束标记；一分量时答案是 1 和 0。',r'''
int n;cin>>n;SCC s(n);for(int i=0;i<n;i++){int x;while(cin>>x&&x)s.edge(i,x-1);}s.build();vector<int>in(s.count),out(s.count);for(int v=0;v<n;v++)for(int u:s.g[v])if(s.component[u]!=s.component[v]){in[s.component[u]]++;out[s.component[v]]++;}int a=count(in.begin(),in.end(),0),b=count(out.begin(),out.end(),0);cout<<a<<'\n'<<(s.count==1?0:max(a,b))<<'\n';
''',SCC)

add('P2169','零费用强连通分量缩点后最短路',
    '局域网内部互相可达，传输费用为零。先缩强连通分量，只保留跨分量的原权边，再求 1 所在分量到 n 所在分量的最短路。',
    SCC_REASON+'同一个强连通分量内任意两台电脑都可互相到达，按题意内部传输免费，因此可以把整个分量当成一个点。跨分量边仍须付原来的费用，不能因为图中存在一条环外的返回路径就随意消掉某条费用。\n\n每条原边检查两个端点的分量，内部边丢弃，外部边带原权重加入新图。随后用 Dijkstra 求最短路。它每次确定当前距离最小的点，边权非负保证距离不再被未来路线改小。优先队列中旧距离要跳过。\n\n原图点数大，强连通搜索使用显式栈；距离中间量使用 long long。',
    '时间 O((n+m) log n)，空间 O(n+m)。','只把强连通分量内部费用置零；优先队列过期项跳过。',r'''
int n,m;cin>>n>>m;SCC s(n);vector<tuple<int,int,int>>edges;while(m--){int a,b,w;cin>>a>>b>>w;a--;b--;s.edge(a,b);edges.push_back({a,b,w});}s.build();vector<vector<pair<int,int>>>g(s.count);for(auto [a,b,w]:edges)if(s.component[a]!=s.component[b])g[s.component[a]].push_back({s.component[b],w});const long long inf=LLONG_MAX/4;vector<long long>d(s.count,inf);int start=s.component[0],goal=s.component[n-1];d[start]=0;priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;q.push({0,start});while(!q.empty()){auto [dist,v]=q.top();q.pop();if(dist!=d[v])continue;for(auto [u,w]:g[v])if(d[u]>dist+w){d[u]=dist+w;q.push({d[u],u});}}cout<<d[goal]<<'\n';
''',SCC)

add('SP14887','缩点 DAG 上的最大点权路径',
    '强连通分量内部可以绕行收集全部非负快乐值，再从任意出口离开。把分量点权求和后，在 DAG 上做从 S 到 E 的最长路动态规划。',
    SCC_REASON+'一个分量内允许重复经过城市，且快乐值只收集一次。由于全部点权非负，可以先在分量内部绕行访问所有城市，再到达需要的出口，不会损失收益，所以缩点后的权值就是分量内快乐值之和。\n\n缩点图没有环，一条路线经过的分量也不会重复。令 dp[c] 表示从起点分量出发到 c 时的最大快乐值。仅把起点初始化为自身点权，其它点为负无穷；按拓扑顺序，对每条 c→d 用 dp[c]+weight[d] 更新 dp[d]。\n\n拓扑队列处理全部分量，但不可达分量不能参与数值转移。终点所属分量的 dp 就是答案；即使起终点同属一分量，也能先绕行收集整块再结束。',
    '时间 O(n+m)，空间 O(n+m)。','点权为非负是整块求和的依据；不能从不可达状态转移；总和用 long long。',r'''
int n,m,start,goal;cin>>n>>m>>start>>goal;start--;goal--;vector<long long>w(n);for(auto&x:w)cin>>x;SCC s(n);while(m--){int a,b;cin>>a>>b;s.edge(a-1,b-1);}s.build();vector<long long>weight(s.count);vector<vector<int>>g(s.count);vector<int>in(s.count);for(int v=0;v<n;v++){weight[s.component[v]]+=w[v];for(int u:s.g[v])if(s.component[u]!=s.component[v]){g[s.component[v]].push_back(s.component[u]);in[s.component[u]]++;}}const long long neg=LLONG_MIN/4;vector<long long>dp(s.count,neg);dp[s.component[start]]=weight[s.component[start]];queue<int>q;for(int c=0;c<s.count;c++)if(!in[c])q.push(c);while(!q.empty()){int v=q.front();q.pop();for(int u:g[v]){if(dp[v]!=neg)dp[u]=max(dp[u],dp[v]+weight[u]);if(--in[u]==0)q.push(u);}}cout<<dp[s.component[goal]]<<'\n';
''',SCC)

add('P4171','把两种喜好写成 2-SAT 子句',
    '一个评审要求的两道菜至少做一道，即子句 A 或 B。加入非 A→B、非 B→A 两条蕴含边；某食材的满式与汉式在同一个强连通分量时无解。',
    '每种材料只有两种互斥做法，可以用一个布尔变量表示。评审仅在两种喜好都未满足时淘汰选手，所以对应逻辑条件 A∨B。这个条件等价于：若 A 不成立，就必须 B 成立；若 B 不成立，就必须 A 成立。\n\n把每个文字及其否定作为两个顶点，用相邻编号表示，异或一就得到相反做法。对每位评审加入两条蕴含边。若某变量与其否定互相蕴含，它们位于同一强连通分量，任意取值都会推出矛盾。\n\n反过来，当每个变量的两个文字处于不同分量时，按缩点图逆拓扑方向选择尚未赋值的分量即可得到满足所有子句的取值，因此该条件也是充分的。本题只判断是否存在，不必输出具体菜单。',
    '每组时间 O(n+m)，空间 O(n+m)。','m 表示满式，h 表示汉式；否定文字用 ^1；每组重新建图。',r'''
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;SCC s(2*n);while(m--){string a,b;cin>>a>>b;auto id=[](string v){return 2*(stoi(v.substr(1))-1)+(v[0]=='m');};int x=id(a),y=id(b);s.edge(x^1,y);s.edge(y^1,x);}s.build();bool ok=true;for(int i=0;i<n;i++)if(s.component[2*i]==s.component[2*i+1])ok=false;cout<<(ok?"GOOD":"BAD")<<'\n';}
''',SCC)

add('P3007','2-SAT 可行性与强制取值',
    '先建立每头牛的两个投票至少满足一个的 2-SAT 图。无矛盾后，若 N 能推出 Y，则议案必须通过；若 Y 能推出 N，则必须否决；都不能推出时两种取值均可。',
    '每头牛的要求是两个文字的析取，按非 A→B 与非 B→A 建图。先求强连通分量，某议案的 Y、N 同属一分量时整体无解。\n\n接着判断某个取值是否会造成矛盾。如果从文字 N 能沿蕴含边到 Y，那么假设 N 为真会同时推出它的否定，故 N 不可取，所有解都只能取 Y。对 Y 到 N 的情形同理。\n\n如果两个方向都不可达，则都存在可扩展成完整解的赋值，这是可满足 2-SAT 蕴含图的性质：加入单个文字为真的条件只有在它能推出自身否定时才会破坏可满足性。顶点不超过两千，可以对每个议案的两个文字分别遍历图，无需建立巨大传递闭包。',
    '时间 O(n(n+m))，空间 O(n+m)。','无解先输出 IMPOSSIBLE；可行时强制方向不能反；未知输出 ?。',r'''
int n,m;cin>>n>>m;SCC s(2*n);while(m--){int a,b;char x,y;cin>>a>>x>>b>>y;int u=2*(a-1)+(x=='Y'),v=2*(b-1)+(y=='Y');s.edge(u^1,v);s.edge(v^1,u);}s.build();for(int i=0;i<n;i++)if(s.component[2*i]==s.component[2*i+1]){cout<<"IMPOSSIBLE\n";return 0;}auto reach=[&](int a,int b){vector<char>seen(2*n);vector<int>st={a};seen[a]=1;while(!st.empty()){int v=st.back();st.pop_back();if(v==b)return true;for(int u:s.g[v])if(!seen[u]){seen[u]=1;st.push_back(u);}}return false;};for(int i=0;i<n;i++)cout<<(reach(2*i,2*i+1)?'Y':reach(2*i+1,2*i)?'N':'?');cout<<'\n';
''',SCC)

add('P4819','源分量的必要检查与最后一人推断',
    '每个源强连通分量通常必须查证一人，风险人数为源分量数。若存在单点源，且它指向的每个分量还有其它入边，就能把此人留到最后推断，风险人数再减一。',
    SCC_REASON+'查证一个平民后，可以沿认识关系继续获得信息。每个源分量没有来自外部的认识关系，通常至少查证其中一个人；选择哪个人遇到杀手的概率都是 1/n，所以应最小化必须冒险查证的人数。\n\n最后剩下一个未确定身份的人时，可以直接推断他是杀手，无需查证。要省下一次源分量查证，这个源必须是单点；若包含多人，仍有多个候选无法区分。同时，跳过它后其余所有分量必须仍能被其它源覆盖。在缩点 DAG 上，这等价于它的每个出邻居的入度都至少为二。\n\n跨分量的重边先去重，避免同一个源重复指向一个分量被误算成多个来源。满足条件的单点源只需存在一个，就能把它留到最后，最多省一次。概率为 1−风险人数/n；n=1 时可以直接确定唯一的人。',
    '时间 O((n+m) log m)，空间 O(n+m)。','统计不同来源的入边，重边去重；最多省一次；输出六位小数。',r'''
int n,m;cin>>n>>m;SCC s(n);while(m--){int a,b;cin>>a>>b;s.edge(a-1,b-1);}s.build();vector<int>size(s.count),in(s.count);vector<pair<int,int>>edges;for(int v=0;v<n;v++){size[s.component[v]]++;for(int u:s.g[v])if(s.component[v]!=s.component[u])edges.push_back({s.component[v],s.component[u]});}sort(edges.begin(),edges.end());edges.erase(unique(edges.begin(),edges.end()),edges.end());vector<vector<int>>g(s.count);for(auto [a,b]:edges){g[a].push_back(b);in[b]++;}int risk=count(in.begin(),in.end(),0);for(int c=0;c<s.count;c++)if(!in[c]&&size[c]==1){bool ok=true;for(int u:g[c])if(in[u]==1)ok=false;if(ok){risk--;break;}}cout<<fixed<<setprecision(6)<<1.0-(double)risk/n<<'\n';
''',SCC)

add('AT_dfs_a','栈模拟深度优先搜索',
    '从起点出发，只走未访问的非墙格，把能到达的格子全部标记。终点被标记就输出 Yes，否则输出 No。',
    '把每个非墙格看成一个顶点，上下左右相邻的两格之间连边。题目只问是否存在路线，不需要求最短距离，因此按任意顺序遍历所有可达格即可。\n\n先找到 s，把它放进栈并立即标记。取出一个格子时，检查四个相邻格；只有坐标合法、不是墙且未访问，才标记并入栈。在入栈时标记能避免多个邻居重复加入同一格。\n\n每个加入栈的格子都有一条由起点延伸而来的路线；反过来，一条合法路线上的格子会依次被遍历。因此遍历结束后，g 被标记当且仅当起点能到达它。使用显式栈还避免了很长走廊造成递归栈溢出。',
    '时间 O(HW)，空间 O(HW)。','先判断坐标再访问数组；墙不能走；在入栈时标记。',r'''
int h,w;cin>>h>>w;vector<string>a(h);int start=-1,goal=-1;
for(int i=0;i<h;i++){cin>>a[i];for(int j=0;j<w;j++){if(a[i][j]=='s')start=i*w+j;if(a[i][j]=='g')goal=i*w+j;}}
vector<char>seen(h*w);vector<int>st={start};seen[start]=1;int dx[]={1,-1,0,0},dy[]={0,0,1,-1};
while(!st.empty()){int v=st.back();st.pop_back();int x=v/w,y=v%w;for(int k=0;k<4;k++){int u=x+dx[k],v=y+dy[k];if(u>=0&&u<h&&v>=0&&v<w&&a[u][v]!='#'&&!seen[u*w+v]){seen[u*w+v]=1;st.push_back(u*w+v);}}}
cout<<(seen[goal]?"Yes":"No")<<'\n';
''',cases=[('1 3\ns#g\n','No\n'),('1 2\nsg\n','Yes\n')])

add('P1443','广度优先搜索马步距离',
    '把一次合法马步看作一条长度为 1 的边，从起点 BFS。第一次到达的步数就是最少步数，未到达的格子保留 -1。',
    '从起点走一步能到的格子距离是 1，再从这些格子走一步，才可能得到距离为 2 的新格子。这种逐层扩展正是广度优先搜索。\n\n距离数组初始为 -1，起点置 0 并入队。每次取出队首，枚举横向 1、纵向 2 或横向 2、纵向 1 的八种带符号位移；合法且距离仍为 -1 的格子得到当前距离加 1，再加入队尾。\n\n队列中的距离单调不降。假设第一次到某格的路线不是最短路线，那么更短路线的倒数第二格会先出队，并且更早发现它，产生矛盾。无须重复松弛。输出按题目要求使用左对齐固定列宽，-1 表示不可达。',
    '时间 O(nm)，空间 O(nm)。','输入坐标是 1 起始；八种位移不能漏；不要把未访问初始化成 0。',r'''
int n,m,x,y;cin>>n>>m>>x>>y;x--;y--;vector<vector<int>>d(n,vector<int>(m,-1));queue<pair<int,int>>q;q.push({x,y});d[x][y]=0;
int dx[]={1,1,-1,-1,2,2,-2,-2},dy[]={2,-2,2,-2,1,-1,1,-1};
while(!q.empty()){auto [a,b]=q.front();q.pop();for(int k=0;k<8;k++){int u=a+dx[k],v=b+dy[k];if(u>=0&&u<n&&v>=0&&v<m&&d[u][v]<0){d[u][v]=d[a][b]+1;q.push({u,v});}}}
for(auto &row:d){for(int value:row)cout<<left<<setw(5)<<value;cout<<'\n';}
''')

add('UVA439','棋盘上的八方向马步 BFS',
    '将 a1 到 h8 映射到 8×8 数组，按八种马步 BFS，输出终点第一次被访问时的距离。',
    '每次移动的代价都为一步，因此不能按几何直线距离估算，而要在棋盘允许的边上求最短路。横坐标由字母减 a 得到，纵坐标由数字减 1 得到。\n\n为每组起终点重新建立距离数组，只把起点置为 0。队列逐层扩展，八种马步均检查是否仍在棋盘内。第一次访问某格时记录当前格距离加 1；后来的路线不可能更短，所以不再入队。起终点相同时自然得到 0。\n\n输入直到文件结束，多组之间不能复用旧距离。最后保留题目规定的整句输出和标点。',
    '每组时间 O(64)，空间 O(64)。','读到 EOF；保留原坐标字符串用于输出；每组清空距离。',r'''
string a,b;while(cin>>a>>b){int d[8][8];memset(d,-1,sizeof d);queue<pair<int,int>>q;int sx=a[0]-'a',sy=a[1]-'1';d[sx][sy]=0;q.push({sx,sy});int dx[]={1,1,-1,-1,2,2,-2,-2},dy[]={2,-2,2,-2,1,-1,1,-1};
while(!q.empty()){auto [x,y]=q.front();q.pop();for(int k=0;k<8;k++){int u=x+dx[k],v=y+dy[k];if(u>=0&&u<8&&v>=0&&v<8&&d[u][v]<0){d[u][v]=d[x][y]+1;q.push({u,v});}}}
cout<<"To get from "<<a<<" to "<<b<<" takes "<<d[b[0]-'a'][b[1]-'1']<<" knight moves.\n";}
''')

add('CF1761C','求每个顶点的祖先集合',
    '若矩阵第 i 行第 j 列为 1，就让 j 的集合包含 i 的集合。对每个目标点沿反向边遍历，把所有能到达它的顶点编号与它自身放入集合。',
    '给第 i 个集合放入一个专属于它的编号 i。如果图中有从 i 到 j 的路径，子集关系的传递性要求 i 的编号也出现在 j 的集合中。因此可以令第 j 个集合恰好包含所有能到达 j 的顶点。\n\n对每个 j，从 j 沿反向边搜索，访问到的编号就是答案。存在 i→j 时，i 的每个祖先也能到达 j，所以构造满足包含关系。原题保证可构造且对应关系允许这种偏序构造，不会要求相互严格包含。\n\n矩阵大小至多一百，直接为每个顶点做一次遍历即可。输出集合大小和实际编号，不需要枚举整数子集。',
    '每组时间 O(n³)，空间 O(n²)。','矩阵方向不能反；每个集合包含自己的编号；输出的是集合元素。',r'''
int t;cin>>t;while(t--){int n;cin>>n;vector<string>a(n);for(auto&s:a)cin>>s;for(int target=0;target<n;target++){vector<char>seen(n);vector<int>st={target};seen[target]=1;while(!st.empty()){int v=st.back();st.pop_back();for(int u=0;u<n;u++)if(a[u][v]=='1'&&!seen[u]){seen[u]=1;st.push_back(u);}}cout<<count(seen.begin(),seen.end(),1);for(int u=0;u<n;u++)if(seen[u])cout<<' '<<u+1;cout<<'\n';}}
''',checker='set-construction')

add('CF659E','数出没有环的连通分量',
    '每个连通分量单独考虑。树无论怎样定向都至少留下一个入度为 0 的点；含环分量可以沿环定向，再由环向外扩展，使所有点入度至少为 1。答案是树形连通分量个数。',
    '目标是尽量减少入度为零的顶点。一个有 v 个点的树只有 v−1 条边，全部顶点入度之和也是 v−1，不可能人人入度至少为一，因此至少有一个零入度点。任选根，所有边由根指向孩子，恰好只有根为零，达到下界。\n\n如果连通分量含环，把一个环按环方向定向；环上每点已有入边。再从环向未覆盖的点做搜索，把搜索树边由内向外定向，每个新点也得到一条入边，其余边任意定向即可。此时贡献为零。\n\n所以只需遍历无向连通分量，统计点数 v 和邻接表总长度的一半 e。连通无向图满足 e=v−1 当且仅当它是树。孤立点同样是一棵树，要贡献一。',
    '时间 O(n+m)，空间 O(n+m)。','无向边在邻接表中出现两次；孤立点也要统计。',r'''
int n,m;cin>>n>>m;vector<vector<int>>g(n);while(m--){int u,v;cin>>u>>v;u--;v--;g[u].push_back(v);g[v].push_back(u);}vector<char>seen(n);int ans=0;
for(int s=0;s<n;s++)if(!seen[s]){long long edges=0;int vertices=0;vector<int>st={s};seen[s]=1;while(!st.empty()){int v=st.back();st.pop_back();vertices++;edges+=g[v].size();for(int u:g[v])if(!seen[u]){seen[u]=1;st.push_back(u);}}ans+=edges/2==vertices-1;}cout<<ans<<'\n';
''')

add('CF888E','折半枚举与有序查找',
    '把数组分成两半，分别枚举子集和对 m 的余数。对于左半余数 x，在排好序的右半余数中找不超过 m−1−x 的最大值，更新不回绕的最优和。',
    '三十五个元素不能枚举全部 2³⁵ 个子集，但分成两半后，各自只有约 2¹⁸ 个子集。每个完整子集唯一拆成一个左半子集和一个右半子集。\n\n两半的和都先对 m 取余，结果为 x、y。若 x+y<m，答案就是 x+y；若回绕，结果为 x+y−m，它不超过 x 或 y 中任一非负较大者，而另一半取空集时已经能够得到单半余数。因此全局最优一定可由一对不回绕的余数达到。\n\n排序右半列表。对每个 x，用 upper_bound 找第一个大于 m−1−x 的元素，向前一步就得到允许范围内的最大 y。空子集提供余数零，所以始终存在可选值。余数与加法使用 long long，避免两个接近模数的数相加溢出 int。',
    '时间 O(2^(n/2)·n)，空间 O(2^(n/2))。','两半都包含空集；先取余；upper_bound 返回位置，取前驱前检查边界。',r'''
int n;long long mod;cin>>n>>mod;vector<long long>a(n);for(auto&x:a)cin>>x;
auto enumerate=[&](int l,int r){vector<long long>s={0};for(int i=l;i<r;i++){int z=s.size();for(int j=0;j<z;j++)s.push_back((s[j]+a[i])%mod);}return s;};
auto l=enumerate(0,n/2),r=enumerate(n/2,n);sort(r.begin(),r.end());long long ans=0;for(long long x:l){auto it=upper_bound(r.begin(),r.end(),mod-1-x);if(it!=r.begin())ans=max(ans,x+*prev(it));}cout<<ans<<'\n';
''')

add('P4799','折半枚举不超预算的子集数',
    '分别枚举两半装备的价格和并保留不超过预算的值。排序右半，对每个左半价格 x，用 upper_bound 统计右半中不超过 M−x 的个数。',
    '每件装备只有选和不选两种状态。把装备分为两半，每个完整选择唯一对应一个左半选择和一个右半选择，因此可以先生成两个价格列表，再统计符合预算的配对数。\n\n生成列表时，从只含空集价格零的列表开始，每加入一件装备，就把原有每个价格加上它的价格形成新状态。由于所有价格非负，超过预算的状态不可能在以后恢复合法，可以直接丢弃。\n\n右半列表排序后，固定左半价格 x，合法右半价格恰好构成不超过 M−x 的前缀，upper_bound 与 begin 的距离就是数量。不同装备组合即使价格相同，也要分别计数，所以列表不能去重。答案最多为 2⁴⁰，使用六十四位整数。空集是否购买零件均由原题的方案定义自然包含。',
    '时间 O(n·2^(n/2))，空间 O(2^(n/2))。','相同价格的不同子集不能去重；答案和预算都用 long long。',r'''
int n;long long m;cin>>n>>m;vector<long long>a(n);for(auto&x:a)cin>>x;auto generate=[&](int l,int r){vector<long long>s={0};for(int i=l;i<r;i++){int size=s.size();for(int j=0;j<size;j++)if(a[i]<=m-s[j])s.push_back(s[j]+a[i]);}return s;};auto l=generate(0,n/2),r=generate(n/2,n);sort(r.begin(),r.end());long long ans=0;for(long long x:l)ans+=upper_bound(r.begin(),r.end(),m-x)-r.begin();cout<<ans<<'\n';
''')

for pid,mode in [('P3366','minimum'),('P2820','removed'),('P1396','bottleneck')]:
    prefix = 'int n,m;cin>>n>>m;'
    if mode=='bottleneck': prefix+='int s,t;cin>>s>>t;'
    code=prefix+r'''
struct E{int u,v;long long w;};vector<E>e(m);long long total=0;for(auto &x:e){cin>>x.u>>x.v>>x.w;total+=x.w;}sort(e.begin(),e.end(),[](E a,E b){return a.w<b.w;});DSU d(n+1);long long answer=0;int used=0;
'''
    if mode=='bottleneck':code+=r'''if(s==t){cout<<0<<'\n';return 0;}for(auto x:e){d.join(x.u,x.v);if(d.find(s)==d.find(t)){cout<<x.w<<'\n';return 0;}}'''
    else:
        code+='for(auto x:e)if(d.join(x.u,x.v)){answer+=x.w;used++;}\n'
        code+=r'''if(used!=n-1)cout<<"orz\n";else cout<<answer<<'\n';''' if mode=='minimum' else r'''cout<<total-answer<<'\n';'''
    add(pid,'按边权排序的 Kruskal',
        '将边按权值从小到大排序，用并查集判断两端是否已连通。连接两个不同连通块的边才能进入生成树。'+('累计被删除边权等于全部边权减去最小生成树权值。' if mode=='removed' else '两指定点第一次连通时的边权就是路径最大边权的最小值。' if mode=='bottleneck' else '选满 n−1 条边得到最小生成树；不能选满则图不连通。'),
        '已经选出的边形成若干互不相交的连通块。下一条连接不同连通块的最小边，对跨越相应割的任何生成树都是安全选择：若某棵最优树没有它，加入后产生的环中可以删除一条不更小的跨块边，总代价不会增加。\n\n依次处理排好序的边，若两端代表元相同，加入会成环，应跳过；否则合并并累计边权。并查集采用路径压缩与按大小合并。\n\n'+('原网络边权之和是固定的。为了尽可能多地拆除而保持连通，保留一棵最小生成树即可；答案为总边权减去所保留的边权。' if mode=='removed' else '把所有权值不超过 W 的边加入后，两点连通等价于存在最大边权不超过 W 的路径。排序扫描中首次连通的阈值正是所求。' if mode=='bottleneck' else '连通图的生成树恰有 n−1 条边；选边不足说明仍存在无法连接的块，按题目要求输出 orz。'),
        '时间 O(m log m)，空间 O(n+m)。','并查集按顶点编号开空间；总权值使用六十四位整数；相同权值任意处理。',code,DSU)

add('P1550','把水井作为连接虚拟水源的边',
    '增加虚拟顶点 0，在农场 i 打井等价于选边 (0,i)，权值为打井费用。原有管道费用作为农场间边，求这张图的最小生成树。',
    '只考虑农场之间的管道会遗漏水源的代价。引入虚拟水源 0 后，打井与铺管道都变成一次连接：打井连接水源与农场，管道连接两个农场。\n\n任何合法供水方案都使每个农场通过某口井连接到 0。反过来，若所有点在含 0 的图中连通，沿路径也必然能找到一个水源。两种方案代价完全一致，所以问题变成包含 n+1 个点的最小生成树。\n\n读取打井费用和费用矩阵，把对称管道只加入一次。Kruskal 按费用从小到大选不成环的边，允许选择多口井，因为那可能比长管道便宜。',
    '时间 O(n² log n)，空间 O(n²)。','不能强制只打一口井；虚拟点也要加入并查集。',r'''
int n;cin>>n;struct E{int u,v,w;};vector<E>e;for(int i=1;i<=n;i++){int x;cin>>x;e.push_back({0,i,x});}for(int i=1;i<=n;i++)for(int j=1;j<=n;j++){int x;cin>>x;if(i<j)e.push_back({i,j,x});}sort(e.begin(),e.end(),[](E a,E b){return a.w<b.w;});DSU d(n+1);long long ans=0;for(auto x:e)if(d.join(x.u,x.v))ans+=x.w;cout<<ans<<'\n';
''',DSU)
