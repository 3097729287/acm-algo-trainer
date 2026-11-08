"""SCC and bridge consequences, cut models and time-expanded transport."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_graph_support import SCC
from nowcoder_dsu_support import DSU
from nowcoder_flow_support import DINIC,FLOW_EXPLANATION,COST_FLOW


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(19790,1900,['二分图染色','奇环构造'],'输出图的二染色或任意简单奇环。',
        'BFS用深度奇偶染色，同时保存父节点。若每条边两端异色，直接输出染色。否则找到同色边(u,v)，在BFS树中把u、v分别沿父链上移到公共祖先，合并成树上简单路径，再用原边闭合。两端同色意味着树路径长度为偶数，加闭合边形成奇环。公共祖先只放一次，保证简单。',
        r'''int n,m;cin >> n >> m;vector<vector<int>> edge(n);while(m--){int u,v;cin >> u >> v;u--;v--;edge[u].push_back(v);edge[v].push_back(u);}vector<int> color(n,-1),parent(n,-1),depth(n);vector<int> queue={0};color[0]=0;int a=-1,b=-1;for(size_t h=0;h<queue.size() && a<0;h++){int u=queue[h];for(int v:edge[u]){if(color[v]<0){color[v]=color[u]^1;parent[v]=u;depth[v]=depth[u]+1;queue.push_back(v);}else if(color[v]==color[u]){a=u;b=v;break;}}}if(a<0){cout << 0 << '\n';for(int i=0;i<n;i++)cout << color[i] << (i+1==n?'\n':' ');return 0;}vector<int> left,right;while(a!=b){if(depth[a]>=depth[b]){left.push_back(a);a=parent[a];}else{right.push_back(b);b=parent[b];}}left.push_back(a);reverse(right.begin(),right.end());left.insert(left.end(),right.begin(),right.end());cout << left.size() << '\n';for(int i=0;i<(int)left.size();i++)cout << left[i]+1 << (i+1==(int)left.size()?'\n':' ');''',
        '同色边加树路径是奇环，不应输出整个DFS访问序列。图保证连通，二分图与有奇环恰好二选一。',
        checker='color-or-odd-cycle',complexity=r'时间、空间均 $O(n+m)$。')
    put(15707,1900,['强连通分量','缩点'],'最小出发点集覆盖全部可达点，字典序最小。',
        '强连通分量内部任一点都能到其他点。缩成DAG后，每个入度0分量必须选至少一个点，因为无法从外部进入；每个其他分量又都可由某个源分量到达。因此恰选每个源分量一个点。要让升序答案字典序最小，每个分量选最小原编号，再整体排序。',
        r'''int n,m;cin >> n >> m;vector<vector<int>> graph(n),reverse(n);while(m--){int u,v;cin >> u >> v;u--;v--;graph[u].push_back(v);reverse[v].push_back(u);}auto [count,component]=components(graph,reverse);vector<int> indegree(count),minimum(count,n);for(int u=0;u<n;u++){minimum[component[u]]=min(minimum[component[u]],u);for(int v:graph[u])if(component[u]!=component[v])indegree[component[v]]++;}vector<int> answer;for(int c=0;c<count;c++)if(!indegree[c])answer.push_back(minimum[c]+1);sort(answer.begin(),answer.end());cout << answer.size() << '\n';for(int i=0;i<(int)answer.size();i++)cout << answer[i] << (i+1==(int)answer.size()?'\n':' ');''',
        '不能直接按原图入度选点，环内可能所有点原入度非零。SCC模板使用迭代Kosaraju避免长链栈溢出。',
        declarations=SCC,complexity=r'时间 $O(n+m+n\log n)$，空间 $O(n+m)$。')
    put(19960,1800,['强连通分量','缩点'],'有向关系可传递，统计所有点都能到达的点数。',
        '缩点DAG中，若有两个不同出度0分量，它们无法彼此到达，无人能被全体到达。若恰有一个汇分量，DAG中任一点沿出边最终必到某个汇，故全部会到这个唯一汇。答案就是该SCC大小。',
        r'''int n,m;cin >> n >> m;vector<vector<int>> graph(n),reverse(n);while(m--){int u,v;cin >> u >> v;u--;v--;graph[u].push_back(v);reverse[v].push_back(u);}auto [count,component]=components(graph,reverse);vector<int> size(count),out(count);for(int u=0;u<n;u++){size[component[u]]++;for(int v:graph[u])if(component[u]!=component[v])out[component[u]]++;}int target=-1;for(int c=0;c<count;c++)if(!out[c]){if(target>=0){cout << 0;return 0;}target=c;}cout << size[target];''',
        '所求是所有点都能到它，关注汇分量，而不是入度0源分量。重复边不影响是否为0。',
        declarations=SCC,complexity=r'时间、空间均 $O(n+m)$。')
    put(50403,1700,['割点','枚举删除'],'两指定点的全部通路必经的最小编号中间服务器。',
        'n≤100，直接按编号枚举除a、b外的候选。暂时禁止经过该点，从a做BFS；若b不可达，该服务器就在全部a到b路径上，最先成功的编号即答案。若原图两中心就不连通，没有需截获的通信路径，输出No solution。',
        r'''int n;cin >> n;vector<vector<int>> edge(n);int u,v;while(cin >> u >> v && (u||v)){u--;v--;edge[u].push_back(v);edge[v].push_back(u);}int a,b;cin >> a >> b;a--;b--;auto reachable=[&](int banned){vector<bool> seen(n);vector<int> queue={a};seen[a]=true;for(size_t i=0;i<queue.size();i++)for(int v:edge[queue[i]])if(v!=banned && !seen[v]){seen[v]=true;queue.push_back(v);}return (bool)seen[b];};if(reachable(-1))for(int candidate=0;candidate<n;candidate++)if(candidate!=a && candidate!=b && !reachable(candidate)){cout << candidate+1;return 0;}cout << "No solution";''',
        '不能把两个中心自身当中间服务器。无需枚举所有简单路径，删除点后测试连通性等价。',
        complexity=r'时间 $O(n(n+m))$，空间 $O(n+m)$。')
    put(51269,1900,['强连通分量','缩点'],'最少起始软件副本，以及最少加边使全图强连通。',
        '缩点DAG中，每个源分量必须得到一个初始副本，其他点都能由源到达，所以第一问为源数。若只有一个SCC，第二问为0；否则至少要给每个源补入边、每个汇补出边，下界max(源数,汇数)。通过把源到汇的可达链连接成环并接入其余源汇可达到此界，因此第二问为两者最大。',
        r'''int n;cin >> n;vector<vector<int>> graph(n),reverse(n);for(int u=0;u<n;u++){int v;while(cin >> v && v){v--;graph[u].push_back(v);reverse[v].push_back(u);}}auto [count,component]=components(graph,reverse);vector<int> in(count),out(count);for(int u=0;u<n;u++)for(int v:graph[u])if(component[u]!=component[v]){in[component[v]]++;out[component[u]]++;}int sources=0,sinks=0;for(int c=0;c<count;c++){sources+=in[c]==0;sinks+=out[c]==0;}cout << sources << '\n' << (count==1?0:max(sources,sinks));''',
        '已经强连通时第一问仍需1份副本，第二问才是0。',
        declarations=SCC,complexity=r'时间、空间均 $O(n+m)$。')
    put(51307,2100,['桥','边双连通分量'],'加最少无向边让任意两点有两条边不重合路线。',
        '两条边不相交路径等价于没有桥。找出所有桥，把非桥边相连的点缩为边双连通分量，原连通图缩成一棵桥树。每个叶分量都需要至少一条新边接到外部，一条边最多照顾两个叶子，因此下界ceil(叶子数/2)；按DFS叶序跨半圈配对可让新边形成的环覆盖所有桥，达到下界。桥树只有一个节点时答案0。\n\n参考代码用迭代DFS记录dfn/low，回退时判low[child]>dfn[parent]为桥。以边编号跳过父边，保留平行边的回边作用。',
        r'''int n,m;cin >> n >> m;vector<vector<pair<int,int>>> edge(n);vector<pair<int,int>> endpoints(m);for(int i=0;i<m;i++){int u,v;cin >> u >> v;u--;v--;endpoints[i]={u,v};edge[u].push_back({v,i});edge[v].push_back({u,i});}vector<int> dfn(n),low(n),parent(n,-1),parentEdge(n,-1),next(n),stack={0};vector<bool> bridge(m);int timer=1;dfn[0]=low[0]=1;while(!stack.empty()){int u=stack.back();if(next[u]<(int)edge[u].size()){auto [v,id]=edge[u][next[u]++];if(id==parentEdge[u])continue;if(!dfn[v]){parent[v]=u;parentEdge[v]=id;dfn[v]=low[v]=++timer;stack.push_back(v);}else low[u]=min(low[u],dfn[v]);}else{stack.pop_back();if(parent[u]>=0){int p=parent[u];low[p]=min(low[p],low[u]);if(low[u]>dfn[p])bridge[parentEdge[u]]=true;}}}DSU dsu(n);for(int i=0;i<m;i++)if(!bridge[i])dsu.unite(endpoints[i].first,endpoints[i].second);vector<int> degree(n);for(int i=0;i<m;i++)if(bridge[i]){degree[dsu.find(endpoints[i].first)]++;degree[dsu.find(endpoints[i].second)]++;}int leaves=0;for(int x:degree)leaves+=x==1;cout << (leaves+1)/2;''',
        '原图允许重边，不能仅用父节点编号跳过所有返父边。题目保证原图连通。',
        declarations=DSU,complexity=r'时间 $O(n+m\alpha(n))$，空间 $O(n+m)$。')
    put(51319,2200,['交替环','强连通分量'],'给定完美婚配，求每个男孩可在某个完美匹配中迎娶的女孩。',
        '设owner[g]是给定匹配中女孩g的男孩。每条喜欢边u→g转成男孩图边u→owner[g]。把u改配g会挤占另一个男孩，若可沿此图回到u，便能沿交替环轮换所有婚配。故喜欢边可选当且仅当u和owner[g]在同一个SCC；原匹配对应自环自然可选。每人筛选后按女孩编号排序。',
        r'''int n;cin >> n;vector<vector<int>> likes(n);for(auto &row:likes){int k;cin >> k;row.resize(k);for(int &g:row){cin >> g;g--;}}vector<int> owner(n);for(int u=0;u<n;u++){int g;cin >> g;owner[g-1]=u;}vector<vector<int>> graph(n),reverse(n);for(int u=0;u<n;u++)for(int g:likes[u]){int v=owner[g];graph[u].push_back(v);reverse[v].push_back(u);}auto [count,component]=components(graph,reverse);for(int u=0;u<n;u++){vector<int> answer;for(int g:likes[u])if(component[u]==component[owner[g]])answer.push_back(g+1);sort(answer.begin(),answer.end());cout << answer.size();for(int g:answer)cout << ' ' << g;cout << '\n';}''',
        '两完美匹配的对称差是交替环，所以条件既必要又充分。只在原喜欢列表中筛，不输出不喜欢的女孩。',
        declarations=SCC,complexity=r'时间 $O(n+E+E\log n)$（含输出排序），空间 $O(n+E)$。')
    put(20405,1900,['最小割'],'改变个人投票偏好与朋友分歧各付1，最少冲突。',
        '把源侧看作投1、汇侧看作投0。原偏好1者连源→人容量1，偏好0者连人→汇容量1，割掉时恰罚一次改票。朋友间连两个方向容量1，分在两侧时只有一个方向从源侧跨到汇侧，恰罚一次朋友分歧。总割容量与冲突数一一对应，求最大流。\n\n'+FLOW_EXPLANATION,
        r'''int n,m;cin >> n >> m;int source=n,sink=n+1;Dinic flow(n+2);for(int i=0;i<n;i++){int preference;cin >> preference;if(preference)flow.add(source,i,1);else flow.add(i,sink,1);}while(m--){int u,v;cin >> u >> v;u--;v--;flow.add(u,v,1);flow.add(v,u,1);}cout << flow.maximum(source,sink);''',
        '朋友关系无向，两个方向各1；不是容量2。两侧含义必须与个人偏好边方向一致。',
        declarations=DINIC,complexity=r'一般Dinic最坏 $O(V^2E)$，空间 $O(V+E)$。')
    put(213820,2200,['最长不下降子序列','拆点最大流'],'最长不下降长度及最多不相交最长子序列，另允许首尾复用。',
        'O(n²)求f[i]为以i结尾的最长不下降长度S。建源连f=1点、f=S点连汇，每点拆入出容量1；i<j、a[i]≤a[j]且f[j]=f[i]+1时，连i出→j入容量1。每条单位流对应一条长度S的子序列，节点容量保证互不重叠。\n\n第三问将点1、n的拆点容量及相应源/汇边容量改大，其他不变。转移边保持1，避免同一条仅含首尾的序列被无穷重复。S=1时有n个单点序列，两问均输出n。',
        r'''int n;cin >> n;vector<int> a(n),length(n,1);for(int &x:a)cin >> x;int longest=1;for(int i=0;i<n;i++){for(int j=0;j<i;j++)if(a[j]<=a[i])length[i]=max(length[i],length[j]+1);longest=max(longest,length[i]);}cout << longest << '\n';if(longest==1){cout << n << '\n' << n;return 0;}auto solve=[&](bool reusable){int source=2*n,sink=source+1;Dinic flow(sink+1);for(int i=0;i<n;i++){int capacity=reusable && (i==0 || i==n-1)?n+1:1;flow.add(i,n+i,capacity);if(length[i]==1)flow.add(source,i,capacity);if(length[i]==longest)flow.add(n+i,sink,capacity);for(int j=i+1;j<n;j++)if(a[i]<=a[j] && length[j]==length[i]+1)flow.add(n+i,j,1);}return flow.maximum(source,sink);};cout << solve(false) << '\n' << solve(true);''',
        '原题虽称“递增”，明确求的是不下降，允许相等。第三问只放宽编号1和n，不能放宽所有最长序列端点。',
        declarations=DINIC,complexity=r'建图 $O(n²)$；一般Dinic最坏 $O(V²E)$，空间 $O(n²)$。')
    put(213822,2000,['二分图最大权独立集','最小割'],'网格选不相邻格最大权值和。',
        '棋盘黑白染色，邻接图是二分图。最大权独立集=总权−最小权顶点覆盖。源到黑格容量权值，白格到汇容量权值，黑白相邻格连无穷容量。有限割必须在每条邻接边至少舍弃一个端点，割成本恰是舍弃格的总权，因此答案总权−最大流。',
        r'''int rows,cols;cin >> rows >> cols;int cells=rows*cols,source=cells,sink=cells+1;Dinic flow(cells+2);vector<long long> weight(cells);long long total=0;for(auto &x:weight){cin >> x;total+=x;}const int dr[]={-1,1,0,0},dc[]={0,0,-1,1};for(int r=0;r<rows;r++)for(int c=0;c<cols;c++){int u=r*cols+c;if((r+c)%2==0){flow.add(source,u,weight[u]);for(int d=0;d<4;d++){int rr=r+dr[d],cc=c+dc[d];if(rr>=0 && rr<rows && cc>=0 && cc<cols)flow.add(u,rr*cols+cc,total+1);}}else flow.add(u,sink,weight[u]);}cout << total-flow.maximum(source,sink);''',
        '无穷容量取总权+1即可，不必取会溢出的极大值。答案是总权减割，不是割本身。',
        declarations=DINIC,complexity=r'一般Dinic最坏 $O(V²E)$，网格E=O(V)，空间 $O(V)$。')
    put(213825,2300,['时间分层图','增量最大流'],'周期飞船运输k人从地球到月球，最短完成时间。',
        '先把每艘正容量飞船所停站点用并查集合并。允许任意等待，若地球与月球不在同一连通分量就永远无法转移，输出0；否则等待合适周期总能依次中转。\n\n时间t建立每站副本，上一层站点到本层同站连容量k等待边；每艘飞船按其(t−1)模周期到t模周期的实际站点连容量H运输边。源只连t=0的地球，所有时刻月球连汇。逐天扩图，在已有残量网络上继续增广，首次总流达到k的天数即答案。等待边和运输边精确表示每人每分钟的合法选择。',
        r'''int n,m,k;cin >> n >> m >> k;int stations=n+2,moon=n+1;struct Ship{int capacity;vector<int> route;};vector<Ship> ship(m);DSU dsu(stations);for(auto &s:ship){int r;cin >> s.capacity >> r;s.route.resize(r);for(int &x:s.route){cin >> x;if(x==-1)x=moon;}if(s.capacity>0)for(int x:s.route)dsu.unite(s.route[0],x);}if(dsu.find(0)!=dsu.find(moon)){cout << 0;return 0;}auto vertex=[&](int time,int station){return 2+time*stations+station;};int source=0,sink=1;Dinic flow(2+stations);flow.add(source,vertex(0,0),k);flow.add(vertex(0,moon),sink,k);long long moved=0;for(int day=1;;day++){flow.resize(2+(day+1)*stations);for(int s=0;s<stations;s++)flow.add(vertex(day-1,s),vertex(day,s),k);for(auto &s:ship){int r=s.route.size();flow.add(vertex(day-1,s.route[(day-1)%r]),vertex(day,s.route[day%r]),s.capacity);}flow.add(vertex(day,moon),sink,k);moved+=flow.maximum(source,sink,k-moved);if(moved==k){cout << day;break;}}''',
        '时刻0飞船在路线第一个站，第一分钟边是route[0]→route[1%r]。增量流要保留反向残量，允许重新分配早先乘客路线。',
        declarations=DSU+DINIC,complexity=r'若答案T，V=O(T(n+2))、E=O(T(n+m))；一般增量Dinic保守上界 $O(TV²E)$，实际复用既有流且总运量k≤50；空间 $O(V+E)$。')
    put(213829,2100,['最小费用最大流'],'供需平衡运输，求最低与最高总费用。',
        '源→仓库容量供应，仓库→商店容量总货量、费用c，商店→汇容量需求。满流恰为合法全部运输方案，最小费用流给最小费用。再用独立网络把所有运输费用取负，求最小费用后取负得到最大费用。每次找残量最短路并增广瓶颈量，按流量乘路径费用累积。',
        r'''int m,n;cin >> m >> n;vector<long long> supply(m),demand(n);long long total=0;for(auto &x:supply){cin >> x;total+=x;}for(auto &x:demand)cin >> x;vector<vector<long long>> cost(m,vector<long long>(n));for(auto &row:cost)for(auto &x:row)cin >> x;auto solve=[&](int sign){int source=m+n,sink=source+1;CostFlow flow(sink+1);for(int i=0;i<m;i++)flow.add(source,i,supply[i],0);for(int j=0;j<n;j++)flow.add(m+j,sink,demand[j],0);for(int i=0;i<m;i++)for(int j=0;j<n;j++)flow.add(i,m+j,total,sign*cost[i][j]);return sign*flow.minimum(source,sink).second;};cout << solve(1) << '\n' << solve(-1);''',
        '两次计算必须新建网络，不能直接在已流满残量图上改费用。容量和总费用使用64位。',
        declarations=COST_FLOW,complexity=r'每次SPFA最坏 $O(VE)$，若增广A次总 $O(AVE)$，空间 $O(V+E)$。')
    put(24424,2200,['线段树','动态规划'],'一排不选相邻机器，逐日单点修改，累加每天最大收益。',
        '每个区间保存2×2状态，索引为左端、右端是否选中，值为该限制下的最大独立集权和。合并两段时枚举相接的两个端点状态，禁止它们同时选中，其余取最大。叶子只有(0,0)=0、(1,1)=权值合法。点修改后沿树重算，根的四状态最大值为当日最优，累加到总答案。',
        r'''int n,days;cin >> n >> days;const long long negative=LLONG_MIN/4;struct Node{long long value[2][2];bool empty=true;Node(){for(auto &row:value)for(auto &x:row)x=negative;}};auto leaf=[&](long long x){Node node;node.empty=false;node.value[0][0]=0;node.value[1][1]=x;return node;};auto merge=[&](const Node &a,const Node &b){if(a.empty)return b;if(b.empty)return a;Node c;c.empty=false;for(int l=0;l<2;l++)for(int r=0;r<2;r++)for(int x=0;x<2;x++)for(int y=0;y<2;y++)if(!x || !y)c.value[l][r]=max(c.value[l][r],a.value[l][x]+b.value[y][r]);return c;};int size=1;while(size<n)size<<=1;vector<Node> tree(2*size);for(int i=0;i<n;i++){long long x;cin >> x;tree[size+i]=leaf(x);}for(int u=size-1;u;u--)tree[u]=merge(tree[u*2],tree[u*2+1]);long long total=0;while(days--){int p;long long x;cin >> p >> x;p+=size-1;tree[p]=leaf(x);for(p>>=1;p;p>>=1)tree[p]=merge(tree[p*2],tree[p*2+1]);long long best=0;for(auto &row:tree[1].value)for(long long v:row)best=max(best,v);total+=best;}cout << total;''',
        '每次更新在当天开始生效，累加更新后的根答案。空填充叶设empty，避免把无效负无穷与实际状态混合。',
        complexity=r'构建 $O(n)$，每天 $O(\log n)$，空间 $O(n)$。')
    put(216116,800,['整数运算'],'按输入顺序计算两个记忆量的差。',
        '直接输出a−b。样例2020与1906得到114，题目中的诗句不参与运算。',
        r'''int a,b;cin >> a >> b;cout << a-b;''',
        '保留输入顺序，不排序两个数。差值可能为负，使用有符号整数。',
        complexity=r'时间、空间均 $O(1)$。')


if __name__=='__main__':run()
