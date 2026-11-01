"""Spanning forests, bottlenecks, augmentation and tree-path certificates."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
K=A+['graphs','dsu','sort','lambda-local']
DSU=r'''
struct DSU{
    vector<int>parent,size;
    // 这里的n表示0至n-1共n个对象。
    explicit DSU(int n):parent(n),size(n,1){iota(parent.begin(),parent.end(),0);}
    int root(int u){while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;}
    bool merge(int u,int v){u=root(u);v=root(v);if(u==v)return false;
        if(size[u]<size[v])swap(u,v);parent[v]=u;size[u]+=size[v];return true;
    }
};
struct Edge{int u,v;long long w;};
'''

add('P1194','把原价购买看作从虚拟商店连来的一条边',
    'B件商品原价均为A。拥有商品i后可按给定促销价购买j，可使用已买的任意商品触发优惠。零表示没有优惠，求全部买齐的最低总价。',
    r'''为商店建虚拟结点，向每件商品连费用A的边；非零优惠作为商品间的无向边。购买过程对应一棵以商店为根的生成树，反之按树从根购买也能实现。用Prim，初始每件商品的连接费用都为A，之后通过已买商品的非零优惠改善即可。''',
    r'''先买二号花三元，再用它以两元买一号、三号，总共七元。促销不要求刚买的商品才能触发，二号买完以后可以支持不止一件商品，所以不是只能沿一条链购买。

给商店增加虚拟顶点零。直接按原价买商品i对应商店到i的费用A边，凭已有商品j的促销购买i对应j到i的费用边。每次新买的商品都连到此前已有的商品或商店，最终得到包含商店的树，费用恰为总支出。

反过来，任意这样的生成树以商店为根，从根向外购买。每个商品购买时，其父亲已经买好，父边的价格就可用。因此最低购买费用等于这个增广图的最小生成树。

Prim维护已经买到的一组商品，best[v]表示把v直接接到这组或商店的最小单边费用。开始商店已在树中，所有best=A。每次挑最小best的未买商品，支付它，再用它能提供的促销价更新其它best。割的最轻边可安全加入最小生成树：若某棵最优树没有这条边，加入它后环上必有另一条跨割边，换掉不会增加费用。

矩阵中的零不是免费促销，而是没有促销，必须跳过。促销大于原价也不必特别删除，best从A开始只接受更便宜的值；A为零时全部可免费原价购买。''',
    r'''long long A;int B;cin>>A>>B;vector<vector<int>>price(B,vector<int>(B));for(auto &row:price)for(int &v:row)cin>>v;
vector<long long>best(B,A);vector<char>used(B);long long answer=0;
// 虚拟商店已经加入，所有原价边就是初始候选。
for(int step=0;step<B;++step){int u=-1;for(int v=0;v<B;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=best[u];
    for(int v=0;v<B;++v)if(!used[v]&&price[u][v]>0)best[v]=min(best[v],(long long)price[u][v]);
}cout<<answer<<'\n';''',
    '促销零表示不存在；可始终选择原价；已买商品可触发多次优惠；第一件也要计价；不把购买顺序限制成一条链。',
    r'时间与输入矩阵空间均为 $O(B^2)$。',tags=['生成树'],lessons=A+['graphs'])

add('P1195','从n个连通块开始，合并到恰好k个就停止',
    '给出能连接云朵的关系及非负代价，要求所有云朵恰好组成K个非空连通组，总连接代价最小；做不到输出No Answer。',
    r'''按边权升序做Kruskal，只接受连接两个不同并查集的边。每接受一条，组数减少一；成功接受N-K条后立即停止并输出总费用。若遍历完边仍不足N-K条，原图无法连接到K组。K=N时费用为零。''',
    r'''不需要先造完整生成树再尝试各种切法。从每个顶点各成一组开始，连接两个不同组正好使组数减少一，所以从N组变成K组恰好需要N-K次有效合并。

组内多余的环边不能减少组数，代价非负，可以删去而不损失连通。最优方案可选成一个有K个连通块的森林。按边权升序扫描，若边两端尚不连通，就将它加入，直到选够N-K条。

安全性与Kruskal相同：某个当前连通块向外的最轻可用连接，可以交换进入某个最优K块森林而不增加费用；也可由图的森林交换性质逐步保持一个包含已选边的最优解。关键是总接受边数固定为N-K，不去多付让组数少于K的费用。

图允许重边、自环或零费用时，并查集判断仍适用：自环和已经连通的重边跳过，真正连接不同组的零边可以选。若原图本来有超过K个连通分量，无论怎样都无法达标，扫描结束时接受的边数就会不足。

代码把输入编号减一，DSU内部仅保存零至N-1的N个对象。K>N或K<1不可能；K=N时不需要任何边。输出的No Answer大小写及中间空格按原题保持。''',
    r'''int n,m,k;cin>>n>>m>>k;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
if(k<1||k>n){cout<<"No Answer\n";return 0;}
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);int selected=0;long long answer=0;
for(const auto &e:edges){if(selected==n-k)break;if(dsu.merge(e.u,e.v)){answer+=e.w;++selected;}}
if(selected==n-k)cout<<answer<<'\n';else cout<<"No Answer\n";''',
    '只计成功合并；恰选N-K条；K=N时为零；原图不连通不一定无解，只要能达到K组即可。',
    r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。',tags=['生成树','并查集'],lessons=K,declarations=DSU)

add('CF1687B','单边询问得权值，再用最大森林查询判断是否成环',
    '原题为交互协议：只知道n、m，不知道边的端点或长度；可询问一个启用边集合的最大生成森林总权，至多2m次，求全部边的最小生成森林总权。',
    r'''先对每条边单独询问，得到它的权值。按权升序尝试加入当前已接受森林S；询问S加这条边的最大生成森林权值，若恰等于旧总权加边权，说明未形成环，接受；否则撤回。森林加边不成环时所有边都必须使用，成环则至少丢一条正权边。总计m+m次，正好模拟Kruskal。''',
    r'''模拟器返回最大生成森林，目标却是最小生成森林；不能直接对全一集合询问一次就把返回值当答案。可以先把它转变成判断一组已选边是否仍是森林的工具。

只启用一条边时，由于边的两个端点不同，这条边自身就是完整生成森林，返回值恰为其长度。对m条边分别询问，即得到全部边权，却仍不知道端点。把边按长度递增排序，接下来模拟Kruskal。

保持S是一片已接受森林，总权为sum。尝试加入边e，权值为w。如果它连接两个不同分量，S加e仍为森林，完整生成森林必须使用其中每条边，模拟器返回sum+w。

如果它形成环，任何生成森林都必须从环里至少删一条边；全部边权至少一，故返回值严格小于sum+w。只要比较是否相等就知道能否接受，无需知道端点。注意不是比较返回值是否比sum大：权一、二的已选树加入权三的环边，最大森林返回五，虽然大于原sum三，却小于全部边之和六，应该拒绝。

每次接受的恰是按权升序、连接不同分量的边，因此与Kruskal构造同一类最小生成森林。图可能不连通，目标是每个原有连通分量的生成树总权，孤点不增加费用；不用强行选满n-1条。

前半m次查询边权，后半每条边最多再查询一次，总数不超过2m。每次输出问号、长m的零一串与换行后必须刷新，再读回复；读到负数或读失败立即结束，不能继续输出。最终答案以叹号开头并刷新。原站同时列出的Hacks完整图输入不是这份交互程序的协议，不把对话样例当成普通固定输入输出测试。''',
    r'''int n,m;if(!(cin>>n>>m))return 0;vector<long long>weight(m);string selected(m,'0');
for(int i=0;i<m;++i){selected[i]='1';weight[i]=ask(selected);selected[i]='0';}
vector<int>order(m);iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return weight[a]<weight[b];});
long long total=0;for(int i:order){selected[i]='1';long long reply=ask(selected);
    // 只有全部正权边都被保留，才说明这次没有形成环。
    if(reply==total+weight[i])total+=weight[i];else selected[i]='0';
}cout<<"! "<<total<<endl;''',
    '模拟器给最大森林，目标是最小森林；比较sum+w而非sum；正权保证成环时严格少；每次询问刷新；输入失败或负回复立即退出；原图可不连通。',
    r'至多2m次询问，每次输出m位，程序端时间 $O(m^2+m\log m)$，空间 $O(m)$。',
    tags=['生成树','交互题'],lessons=A+['graphs','sort','lambda-local','interactive-io'],
    declarations=r'''long long ask(const string &selection){
    cout<<"? "<<selection<<endl;long long reply;
    if(!(cin>>reply)||reply<0)exit(0);return reply;
}''',checker='railway_transcript',interactive='railway')

TREE_MAX=DSU+r'''
struct TreeMax{
    int n,levels;vector<int>depth;vector<vector<int>>up;vector<vector<long long>>largest;
    explicit TreeMax(const vector<vector<pair<int,long long>>> &g):n(g.size()),levels(1),depth(n,-1){
        while((1LL<<levels)<=n)++levels;
        up.assign(levels,vector<int>(n));largest.assign(levels,vector<long long>(n,LLONG_MIN));
        for(int root=0;root<n;++root)if(depth[root]==-1){
            vector<int>order{root};depth[root]=0;up[0][root]=root;
            for(size_t at=0;at<order.size();++at){int u=order[at];
                for(auto [v,w]:g[u])if(depth[v]==-1){depth[v]=depth[u]+1;up[0][v]=u;largest[0][v]=w;order.push_back(v);}
            }
        }
        // 两段等长上行路径拼成更长一段，同时合并最大边。
        for(int k=1;k<levels;++k)for(int v=0;v<n;++v){
            int middle=up[k-1][v];up[k][v]=up[k-1][middle];largest[k][v]=max(largest[k-1][v],largest[k-1][middle]);
        }
    }
    long long query(int u,int v)const{
        if(u==v)return 0;long long answer=LLONG_MIN;if(depth[u]<depth[v])swap(u,v);
        int delta=depth[u]-depth[v];for(int k=0;k<levels;++k)if(delta>>k&1){answer=max(answer,largest[k][u]);u=up[k][u];}
        if(u==v)return answer;
        for(int k=levels-1;k>=0;--k)if(up[k][u]!=up[k][v]){
            answer=max({answer,largest[k][u],largest[k][v]});u=up[k][u];v=up[k][v];
        }
        return max({answer,largest[0][u],largest[0][v]});
    }
};
'''

add('CF1184E2','非树边能降到的临界值，是树上两端路径的最大边',
    '所有边权互异，当前最小生成树唯一。对每条不在这棵树中的边，求把它改到多大时仍可能进入某棵最小生成树，按原输入顺序输出。',
    r'''先用Kruskal标出当前MST。每条非树边(u,v)的答案是MST上u到v路径的最大边权：等于它可换边，超过它则为环上唯一最重边。对树预处理祖先倍增表与每段最大边，所有非树边各做一次对数时间查询。''',
    r'''给最小生成树增加一条非树边(u,v)，会形成由这条边与树上u-v路径组成的唯一环。设路径最大边权为B。若把新边设为B，就能换下路径中的B权边，生成树总权不变，故存在最优树使用它。

如果新权值大于B，它就是这条环上唯一最重边。任意包含它的生成树删掉它后形成一个割，原树路径中至少一条边跨过这个割且更轻，可以换进来降低总权，所以它不属于任何最小生成树。因此答案恰为B，等号允许。

构造MST时保留输入边编号，后续只输出那些未被接受的边。题目保证初始权值互异，所以这棵树就是当前唯一计划；改变某条非树边后可能出现并列最优，这不妨碍“可能被使用”的要求。

树上查询不能每次重新搜索。选根后，up[k][v]表示向上走2^k步的祖先，largest[k][v]是这段上行路径的最大边。把两段2^(k-1)拼起来，就能同时计算更远祖先与段最大值。

查询先把较深端抬到同深，每抬一段都累积最大边；若尚未相遇，就从大步长向小步长同时上跳，直到两点的父亲相同，最后补上各自到父亲的一条边。这样恰好覆盖整条树路径，且不包含公共祖先以上的边。

建树深度使用队列式数组遍历，避免十万点长链的递归栈风险。若原图本身是一棵树，非树边数为零，什么都不输出；不能误输出树边的阈值。''',
    r'''int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
vector<int>order(m);iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return edges[a].w<edges[b].w;});
DSU dsu(n);vector<char>used(m);vector<vector<pair<int,long long>>>tree(n);
for(int i:order){const auto &e=edges[i];if(dsu.merge(e.u,e.v)){used[i]=true;tree[e.u].push_back({e.v,e.w});tree[e.v].push_back({e.u,e.w});}}
TreeMax paths(tree);for(int i=0;i<m;++i)if(!used[i])cout<<paths.query(edges[i].u,edges[i].v)<<'\n';''',
    '只查询非树边并保持输入顺序；最大树路径边是临界值，等号允许；每次抬升同步累积最大值；原图是树则不输出。',
    r'时间 $O(m\log m+(n+m)\log n)$，空间 $O(m+n\log n)$。',tags=['生成树','倍增','LCA'],lessons=K+['trees','binary-lifting'],declarations=TREE_MAX)

add('P2245','最小生成森林保存所有两点间的最小瓶颈',
    '每次询问两星系之间一条路线的最大危险边，要求把这个最大值尽量降低。图可能不连通，也可能有重边、自环；不可达输出impossible。',
    r'''先做最小生成森林。任意连通两点间的最小瓶颈，等于森林里唯一路径的最大边权；否则更低瓶颈路线可替换该最大边，降低生成树权和。对森林做倍增，查询路径最大边；先用并查集检查是否同一分量。''',
    r'''路线的危险是沿途最大的一条边，不是所有边的和。可能有一条多走很多边的路线，却能避开一条特别危险的直航边，所以普通最短路并不直接回答这个问题。

设T是所在连通块的最小生成树，u到v的树路径最大边为B。删掉这条B边，树被分成两侧，u、v各在一边。任意原图u-v路线都必须跨过这道割；若能让沿途所有边都小于B，就能选其中一条跨割边替换B，得到更轻的树，与最优性矛盾。因此任意路线瓶颈至少B，而树路径本身能达到B，正好最优。

对不连通图分别保留每块的最小树，即最小生成森林。Kruskal的并查集同时给出最终分量，询问两端根不同就输出impossible，无需在不同的树间做路径查询。自环不合并，平行边按费用排序后正常处理。

森林中的每棵树任选一个根，预处理向上2^k步的祖先和途中最大边。查询先对齐深度，再同时抬升两端至最近公共祖先的下一层，把经过各段的最大值合并即可，每次只需对数步。

最大值表的空段使用LLONG_MIN，不把零无条件混入非空路径最大值。询问同一点时允许不走边，按空路线输出零。建深度用迭代遍历，整条长链也不会因递归过深失败。''',
    r'''int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);vector<vector<pair<int,long long>>>tree(n);
for(const auto &e:edges)if(dsu.merge(e.u,e.v)){tree[e.u].push_back({e.v,e.w});tree[e.v].push_back({e.u,e.w});}
TreeMax paths(tree);int Q;cin>>Q;while(Q--){int u,v;cin>>u>>v;--u;--v;
    if(dsu.root(u)!=dsu.root(v))cout<<"impossible\n";else cout<<paths.query(u,v)<<'\n';
}''',
    '求最大边的最小值，不求距离和；图可不连通，逐分量预处理；重边、自环按并查集处理；同点空路线为零；impossible全小写。',
    r'时间 $O(m\log m+(n+Q)\log n)$，空间 $O(m+n\log n)$。',tags=['生成树','倍增','LCA'],lessons=K+['trees','binary-lifting'],declarations=TREE_MAX)

add('CF545E','最短路确定后，每个点选最便宜的合法最后一条边',
    '要求一棵保持指定源点到所有点最短距离的树，并在这些最短路树中让边权总和最小；输出总权与任意一组合法边编号。',
    r'''先Dijkstra求dist。对非源点v，只能从满足dist[u]+w(u,v)=dist[v]的边中选父边，取权值最小者。边权严格为正，父亲的距离严格下降，独立选择也必然汇成一棵以源点为根的树；每个点各自最小即使总和最小。''',
    r'''这是最短路树的二次优化，不能直接输出最小生成树；后者虽总权小，却未必保留源点到所有点的最短距离。

先以给定源点s求出原图最短距离dist。v的父边(u,v)必须满足dist[u]+w=dist[v]，否则树上到v的距离就不是原图最短距离。反过来，只要为每个非源点选择一条这样的边，就能维持最短距离，前提是它们确实组成树。

本题边权都大于零，所以合法父亲满足dist[u]<dist[v]。沿父指针，距离严格下降，不可能形成环。每个非源点都有父亲，源点没有，且图连通、所有点可达，父链最终只能结束在源点。于是全部选择恰为n-1条边的一棵树，不会因为分别选择而发生环或漏点。

树的总权就是各非源点父边费用之和，各点的合法候选只由固定的dist决定，互不占用资源。因此逐点选最小权父边，就使整个和最小。若权相等，可任选一条，不需固定与样例相同的边编号。

实现先完成Dijkstra，再扫描原始无向边的两个方向，分别检查等式并改善对应点的父边。这样把距离优化与父边优化分开，避免在距离尚未稳定时误保留父边。每条输入边保存原编号，最后按顶点遍历输出选择，源点跳过。

距离最多约$3\times10^{14}$，距离和答案均用long long。正权是独立选父边不成环的关键；若允许零权边，需要另行处理相同距离中的环，不能直接照搬结论。''',
    r'''int n,m;cin>>n>>m;vector<Edge>edges(m);vector<vector<pair<int,int>>>g(n);
for(int i=0;i<m;++i){auto &e=edges[i];cin>>e.u>>e.v>>e.w;--e.u;--e.v;g[e.u].push_back({e.v,i});g[e.v].push_back({e.u,i});}
int s;cin>>s;--s;const long long INF=(1LL<<62);vector<long long>dist(n,INF);using State=pair<long long,int>;
priority_queue<State,vector<State>,greater<State>>pq;dist[s]=0;pq.push({0,s});
while(!pq.empty()){auto [du,u]=pq.top();pq.pop();if(du!=dist[u])continue;
    for(auto [v,index]:g[u])if(du+edges[index].w<dist[v]){dist[v]=du+edges[index].w;pq.push({dist[v],v});}
}
vector<long long>cost(n,INF);vector<int>parentEdge(n,-1);
for(int i=0;i<m;++i){const auto &e=edges[i];
    if(dist[e.u]+e.w==dist[e.v]&&e.w<cost[e.v]){cost[e.v]=e.w;parentEdge[e.v]=i;}
    if(dist[e.v]+e.w==dist[e.u]&&e.w<cost[e.u]){cost[e.u]=e.w;parentEdge[e.u]=i;}
}long long answer=0;for(int v=0;v<n;++v)if(v!=s)answer+=cost[v];cout<<answer<<'\n';
for(int v=0;v<n;++v)if(v!=s)cout<<parentEdge[v]+1<<' ';cout<<'\n';''',
    '不是MST；父边必须满足最短路等式；每点选最便宜合法父边；严格正权保证无环；输出原边编号，方案可与样例不同。',
    r'时间 $O(n+m\log(m+1))$，空间 $O(n+m)$。',tags=['最短路','贪心'],lessons=A+['graphs','shortest-path','heap','trees'],declarations='struct Edge{int u,v;long long w;};',checker='shortest_tree')

add('P14362','枚举真正采用的乡镇，旧道路先压缩成一棵MST',
    '可修复旧路，也可付一次城市化费用后启用乡镇到各原城市的新路。只要求原有城市全部连通，乡镇可任意选，求最低总费。',
    r'''先求原城市道路的一棵MST，后续只保留其n-1条边：新增任意乡镇边后，总有一棵最优树只用旧MST和新增边。枚举至多2^k个乡镇集合，加一次启用费，在旧树及所选乡镇的连边上求MST。所有候选边只排序一次，每个集合过滤后扫描。''',
    r'''一个乡镇的启用费只付一次，它与多个城市的道路再各自计费，所以不能把启用费简单加到每条乡镇边上。k最多十，先枚举采用哪些乡镇，把这部分固定费用与连接费用分开。

固定集合S后，考虑原城市及S中的乡镇，旧路和这些乡镇的新路都是可选边，求最小生成树，再加sum(c_j)。虽然题目只要求原城市连通，这样强制所选乡镇也连通不会丢失最优：最优网络中真正使用的乡镇都在连接原城市的那部分中；没有用到的乡镇可以从S去掉，非负启用费不会增加。反过来，每个枚举出的生成树也确实连通全部原城市，是可行方案。

难点在原路最多一百万条，不能在1024个集合里全部反复排序。先对原图求一棵MST T，之后旧路只保留T即可。为什么新增乡镇后仍足够？把新乡镇先看作孤点，逐条插入新边。每次插入边，都能通过在当前最优森林中加边、再删唯一环的最重边得到新最优森林。因此始终存在只使用最初T及已插新边的最优森林，未入T的旧边不需要恢复。

这样候选最多n-1+kn条，约十一万。将旧树边和全部乡镇边统一按费用升序排好，给每条乡镇边标记它所属的乡镇。每次枚举，重置并查集，跳过未启用乡镇的边，进行Kruskal；连通的目标顶点数为n+|S|，需接受n+|S|-1条边。

代码中mask的第j位为一，表示启用乡镇j。每条乡镇边记一个仅第j位为一的bit；mask与bit按位与非零才允许这条边。旧树边的bit为零，表示无需启用乡镇、始终可选。

费用全部非负，可以在固定启用费已经不小于当前最好答案时跳过，也可在累计连接费达到当前最好答案时停止这一枚举，但不能把尚未接通的部分费用当作完整可行答案。S为空同样必须枚举，它对应只修旧路。

总费用可能超过32位，用long long。先算旧MST再加乡镇边的性质是插入更新，不意味着把城市化费用当作普通边权；这两步不能混淆。题面引用的第二至第四组附件没有提供字面数据，本次只将可读取样例一计入官方样例。''',
    r'''int n,m,k;cin>>n>>m>>k;vector<Edge>roads(m);for(auto &e:roads){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(roads.begin(),roads.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU original(n);
struct Candidate{int u,v;long long w;int bit;};vector<Candidate>edges;
for(const auto &e:roads)if(original.merge(e.u,e.v))edges.push_back({e.u,e.v,e.w,0});
vector<long long>activation(k);for(int j=0;j<k;++j){cin>>activation[j];for(int i=0;i<n;++i){long long w;cin>>w;edges.push_back({n+j,i,w,1<<j});}}
sort(edges.begin(),edges.end(),[](const Candidate &a,const Candidate &b){return a.w<b.w;});
long long answer=(1LL<<62);
for(int mask=0;mask<(1<<k);++mask){long long total=0;for(int j=0;j<k;++j)if(mask>>j&1)total+=activation[j];
    if(total>=answer)continue;int needed=n+__builtin_popcount((unsigned)mask)-1,selected=0;DSU dsu(n+k);
    if(needed==0){answer=min(answer,total);continue;}
    for(const auto &e:edges){if(e.bit&&!(mask&e.bit))continue;
        if(dsu.merge(e.u,e.v)){total+=e.w;++selected;if(selected==needed||total>=answer)break;}
    }
    if(selected==needed)answer=min(answer,total);
}cout<<answer<<'\n';''',
    '乡镇启用费只付一次；枚举空集合；只要求原城市连通由“真正使用的乡镇集合”解释；旧路缩减必须取MST；剪枝后未接通的费用不能更新答案。',
    r'设E=n-1+kn，时间 $O(m\log m+E\log E+2^k(n+k+E\alpha(n+k)))$，空间 $O(m+E+n+k)$。',tags=['生成树','枚举'],lessons=K+['bitwise'],declarations=DSU)

add('P1546','每次选接入整棵已建网络的最便宜线路',
    '给出农场间完整费用矩阵，求铺设光纤使所有农场连通的最小总长度；允许通过其它农场间接连通。',
    r'''矩阵Prim：先从任一农场开始，best[v]记录v到已选网络的最小单边费用。每次取未选农场中best最小者，把该费用加入答案，再用它到其它农场的直接费用更新best。不要累加起点到它的路径距离。''',
    r'''目标是建成一张大家都能使用的网络，某条光纤只铺一次。因此它是最小生成树，不是把某个农场到各处的最短距离相加。

已选集合表示已经接入网络的农场，best[v]是从集合中某个农场直接连到v的最轻边。把best最小的未选农场u接进来，支付best[u]。此后它也可以作为新线路的一端，故对每个未选v令best[v]=min(best[v],cost[u][v])。

选择是安全的：把已选网络与未选农场看成一个割，当前候选是跨过这个割的最轻边。若某棵最优树没有它，加入后产生的环中必有另一条跨割边；用当前不更贵的边换下那条边，仍是最优树，且包含这次选择。逐次交换，所有选择都能属于某棵最优树。

最初指定一个农场为种子，best[0]=0，这个零只表示起点无需接线；其它值先设为无穷。运行N次后恰好支付N-1条边，所有农场连通。

这里的更新不写best[u]+cost[u][v]。那是在比较从起点沿路到v的总路长，而我们只为新增加的这一条线付费。输入即使因换行限制折成多行，连续读取N²个整数也不受影响。''',
    r'''int n;cin>>n;vector<vector<long long>>cost(n,vector<long long>(n));for(auto &row:cost)for(auto &w:row)cin>>w;
const long long INF=(1LL<<60);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long long answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=best[u];
    // 只比较新铺这条线的费用，不能加到根的距离。
    for(int v=0;v<n;++v)if(!used[v])best[v]=min(best[v],cost[u][v]);
}cout<<answer<<'\n';''',
    '不是最短路树；best只是一条跨割边的费用；矩阵按整数读取而非按物理行读取；起点的零不算真实线路。',
    r'时间与矩阵空间均为 $O(N^2)$。',tags=['生成树'],lessons=A+['graphs'])

add('P1547','Kruskal最后接通全图的边就是所求瓶颈',
    '连通无向图允许平行道路，求最小生成树中最长边的长度。',
    r'''按边长升序扫描，接受连接不同并查集的边。第N-1次成功合并时全图接通，该边是已选边中最大的长度，直接输出。不同最小生成树可能选边不同，但这个瓶颈值相同。''',
    r'''这里不问最小生成树的边长总和，而问其中最长的一条。仍可以正常做Kruskal，只记录成功选边的当前长度，不累计为答案。

将边按长度递增处理。在第N-1条边被接受之前，所有严格更短的边仍无法把图连通，否则并查集早已合成一个整体。因此任何连通方案都必须使用至少一条不短于当前边的道路。

另一方面，当前接受的N-1条边已经构成一棵生成树，而且它们都不长于当前边，所以这个下界确实达到。Kruskal同时保证总权最小，得到原题要求的最小生成树；其瓶颈也等于所有生成树的最小可能瓶颈。

例如一到二为二十三，二到三为一千，一到三为四十三。先接受二十三，再接受四十三就连通，最大边四十三；没有必要为了使用二到三而付一千。

平行边都可以保留，较长的一条通常会因为两端已经连通而被跳过。只在合并成功时修改答案；遇到环边不能把它的长度误记成新的瓶颈。题面保证图连通，最终会选到N-1条边。''',
    r'''int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);int selected=0;long long answer=0;
for(const auto &e:edges)if(dsu.merge(e.u,e.v)){answer=e.w;if(++selected==n-1)break;}
cout<<answer<<'\n';''',
    '输出最大已选边，不输出权值和；环边不改变答案；成功合并N-1次才连通；输入边是无向的。',
    r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。',tags=['生成树','并查集'],lessons=K,declarations=DSU)

add('P2212','只允许平方距离至少c的边，隐式做Prim',
    '连接两点的费用是欧氏距离平方；费用小于c的连边禁止。求使全部点连通的最小总费用，无法连通输出-1。',
    r'''将所有合法点对看作边，权为平方距离，在这张图上求最小生成树。用Prim按需计算当前点与其它点的平方距离，只有距离平方≥c才更新。若某轮最小候选仍无穷，剩余点无法接入。答案累加平方距离，不能开根号。''',
    r'''本题与普通欧氏最小生成树有两处区别：边的费用就是平方距离，而太近的点反而不能直接连接。必须先按平方距离过滤候选，不能先求普通最小生成树再删短边。

维护已经接入的点集，best[v]是从点集向v的最便宜合法连接。每次选择最小best的未选点，再枚举其它点计算dx²+dy²。若该值小于c，这条路根本不存在；否则可以用于改善best。割的最轻合法边可交换进入最优树，故Prim仍然正确。

例如某些点彼此太近，直接道路被禁，却可能通过远处的点中转连接起来；不能只按几何最近邻把它们判成孤立。反之，如果某轮所有未选点的best都为无穷，就没有任何合法边跨过已选与未选的割，整个图确实不连通。

点最多两千，点对很多但可以按需计算，不存所有边。坐标差先用long long，平方和及总答案也用long long；单条平方距离至多两百万，总和仍可能超过int。

只有一个点时，不需要道路，答案为零，即使c很大也不能判无解。恰好等于c的边允许使用；代码的过滤条件应为w>=c。''',
    r'''int n;long long c;cin>>n>>c;vector<long long>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];
const long long INF=(1LL<<60);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long long answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    if(u==-1||best[u]==INF){cout<<-1<<'\n';return 0;}used[u]=true;answer+=best[u];
    for(int v=0;v<n;++v)if(!used[v]){long long dx=x[u]-x[v],dy=y[u]-y[v],w=dx*dx+dy*dy;
        if(w>=c)best[v]=min(best[v],w);
    }
}cout<<answer<<'\n';''',
    '费用是平方距离本身；太短的边禁止，等于门槛允许；无法跨割才判不连通；总和用long long；单点费用零。',
    r'时间 $O(n^2)$，额外空间 $O(n)$。',tags=['生成树','计算几何'],lessons=A+['graphs','geometry'])

add('P2330','先确定n-1条，再最小化其中最大的分值',
    '要求改造道路连接所有路口，先使改造道路条数最少，再使所选最大分值尽量小。输出条数与该最大分值。',
    r'''连通n个点至少需要n-1条边，生成树恰能达到。按分值递增做Kruskal，接受n-1条后停止，输出n-1及最后一条接受边的分值。此前较小分值边尚不能全连通，说明任何生成树都需要达到这个门槛。''',
    r'''优化条件有顺序：首先全部连通，其次边数尽量少，最后才比较最大分值，题目没有要求这些分值的和最小。

连通图中只要有环，就能删掉环上一条边而不破坏连通，直到剩生成树。生成树有n-1条边，而少于n-1条不可能连通n个点，因此最少道路数直接确定为n-1。

再看最大分值。将边按分值升序加入，跳过产生环的边。最后一次合并之前，全部已处理的较小分值边仍把图分成至少两个连通块，任何生成树都必须再跨过它们，无法只使用更小分值。最后这条边的分值是必要下界；当前选中的树又只用了不超过它的边，故可以达到。

这正是Kruskal的过程。它顺带得到一棵总权最小的树，但我们利用的是瓶颈最小的性质，输出仍是边数和最大分值，不能错把总和输出。

题面保证原图连通。n=1时无需改造道路，按空方案输出零、零；常规情况下统计成功合并次数，环边不改变最大已选分值。''',
    r'''int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);int selected=0;long long largest=0;
for(const auto &e:edges)if(dsu.merge(e.u,e.v)){largest=e.w;if(++selected==n-1)break;}
cout<<selected<<' '<<largest<<'\n';''',
    '优先条数，后比瓶颈；不输出分值和；合并失败的环边忽略；n=1为空方案。',
    r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。',tags=['生成树','并查集'],lessons=K,declarations=DSU)

add('P2872','已有道路记零，新道路比较平方距离后再开根累加',
    '点的坐标与若干已有无向道路已给出，要添加道路使所有点连通，最小化新增道路的真实欧氏长度，输出两位小数。',
    r'''已有道路的新增费用为零，其它点对费用为欧氏长度。隐式Prim中用平方距离作比较键，已有边键为零；每次选中接入点时才将sqrt(best[u])加到答案。平方根单调，所以比较平方值与比较真实长度等价，最终不能把平方值直接相加。''',
    r'''已有道路无论多长都已经修好，不计入新增费用。把它们看成零权边，便可以与新建的欧氏边一起求最小生成树。通过多条旧路间接相连的点，也会经零权边依次进入同一已建网络。

Prim每轮选择从已选集合向外最轻的连接。若u、v之间已有道路，候选键为零；否则为(dx²+dy²)。平方根在非负范围严格单调，所有边的大小顺序保持，所以用平方键选边仍等价于按真实距离选最轻跨割边，不会改变最小生成树的选择。

但单调变换只保持边的比较，不保持费用总和。将点u接入时，实际新增长度是sqrt(best[u])，应当只在这一时刻开根并加入答案，不能先把所有平方值加起来再开根。

同坐标的两个点可以用长度零的新边连接，这也合法；已有道路可重复输入，只需在布尔矩阵上标记。两个方向都要标记，不能因读入顺序只免去一个方向的费用。

坐标差使用long long，平方和最大约$2\times10^{12}$，不会溢出；best也用整数，避免大量浮点比较误差。总长使用long double，最后一次性保留两位，不在每条边上提前舍入。''',
    r'''int n,m;cin>>n>>m;vector<long long>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];
vector<vector<char>>exists(n,vector<char>(n));for(int i=0;i<m;++i){int u,v;cin>>u>>v;--u;--v;exists[u][v]=exists[v][u]=true;}
const long long INF=(1LL<<62);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long double answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;answer+=sqrtl((long double)best[u]);
    for(int v=0;v<n;++v)if(!used[v]){long long dx=x[u]-x[v],dy=y[u]-y[v];long long w=exists[u][v]?0:dx*dx+dy*dy;best[v]=min(best[v],w);}
}cout<<fixed<<setprecision(2)<<answer<<'\n';''',
    '已有路费用零且双向；平方距离只作比较键；选中后开根累加；所有边的总长最后统一舍入两位；同坐标零长边有效。',
    r'时间 $O(n^2)$，已有道路矩阵空间 $O(n^2)$。',tags=['生成树','计算几何'],lessons=A+['graphs','geometry'],checker='mst_decimal')

add('P17016','先按精确平方距离过滤，再求欧氏最小生成树',
    '两基站间距离不超过l才允许建线，费用为真实欧氏长度；求连接全部基站的最小总长，不能连接输出Impossible。',
    r'''隐式Prim，只有dx²+dy²≤l²的点对可更新候选。用平方值比较最轻连接，选中后开根累加真实长度。若某轮最小候选为无穷则不连通。避免用浮点误差判断恰好位于距离上限的边。''',
    r'''线路有长度上限，必须在建图含义上排除过长的边。距离等于l时允许；用整数平方比较(dx²+dy²)≤l²，可以精确处理这条边界，不需要加一个随意的浮点epsilon。

其余就是最小生成树。Prim记录每个未接入点到当前网络的最轻合法边，每次选跨割最轻者加入。平方根单调，因此比较时可以保存平方值；加入答案时再开根，得到真正需要修建的长度。

如果没有任何合法边跨过当前已接入集合与其余点，所有剩余best均为无穷，说明图被这个割分开，任意方法都不能连通，输出Impossible。不能为了完成生成树而放宽长度限制。

例如样例中l从二缩成一后，左下基站到其它基站都没有长度不超过一的边，就无法接入。相反，多个短边可以分段连接相距很远的基站，不要求任意两点之间的直接距离都不超过l。

有负坐标但平方差仍非负，先用long long算差和平方。单点答案零；已有候选中的零也是真实零长度边，不表示不可达。总长用long double，最后保留两位小数。''',
    r'''int n;long long l;cin>>n>>l;vector<long long>x(n),y(n);for(int i=0;i<n;++i)cin>>x[i]>>y[i];
const long long INF=(1LL<<60);vector<long long>best(n,INF);vector<char>used(n);best[0]=0;long double answer=0;
for(int step=0;step<n;++step){int u=-1;for(int v=0;v<n;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    if(u==-1||best[u]==INF){cout<<"Impossible\n";return 0;}used[u]=true;answer+=sqrtl((long double)best[u]);
    for(int v=0;v<n;++v)if(!used[v]){long long dx=x[u]-x[v],dy=y[u]-y[v],w=dx*dx+dy*dy;if(w<=l*l)best[v]=min(best[v],w);}
}cout<<fixed<<setprecision(2)<<answer<<'\n';''',
    '上限用平方整数精确比较，等于允许；比较用平方，费用用开根后的长度；不连通输出Impossible；单点为0.00。',
    r'时间 $O(n^2)$，额外空间 $O(n)$。',tags=['生成树','计算几何'],lessons=A+['graphs','geometry'],checker='mst_decimal')

add('P1340','每周只在上周最小生成森林加新边后重算',
    '每周新增一条道路，要求立即输出全部已知道路中最小生成树的总长；尚不连通时输出-1，早先未管理的旧道路仍允许再次使用。',
    r'''保留前一周的一棵最小生成森林F，将新边加入F后做一次Kruskal，得到新的最小生成森林。插入一条边后，总有最优森林只使用F及这条边：不成环时直接连接，成环时删环上最重边。候选始终至多n条，不需每周重排全部旧边。''',
    r'''直接把每周之前的全部道路重新排序也能求解，但最多六千周会反复处理大量旧边。原图只有两百个点，一棵生成森林最多保留一百九十九条边，可以利用插入更新的性质压缩候选。

假设F是之前全部道路的一棵最小生成森林。新边e连接不同连通分量时，它是当前唯一新出现的跨分量联系，直接把这两个最优部分接起来即可。若e两端已经连通，加入F会形成一个环；用e替换环上最重的边，或者在e本身最重时不选它，就能得到新图的某棵最小生成森林。

这也是最小生成树的交换性质：新图中比旧最优更便宜的变化必须利用新边，而加入新边后消除一个环就足够恢复森林；无需恢复先前被F淘汰的旧边。因此“只保留F”是保存一份足够的最优证据，不是在修改题意、禁止使用没管理过的道路。

实现不必专门在树上找最大边。每周将新边放进forest，按权排序，在这个至多n条边的小集合上重新做Kruskal；用所有成功合并的边覆盖forest。即使尚未全图连通，也保留每个连通块内的最小树，下一周仍可继续。

森林边数等于n-1才输出费用，否则输出-1。新边可能与旧边端点相同且更便宜，也可能没有改善；代码都通过相同的重算处理。所有累计费用用long long。''',
    r'''int n,W;cin>>n>>W;vector<Edge>forest;
for(int week=0;week<W;++week){Edge next;cin>>next.u>>next.v>>next.w;--next.u;--next.v;forest.push_back(next);
    sort(forest.begin(),forest.end(),[](const Edge &a,const Edge &b){return a.w<b.w;});DSU dsu(n);vector<Edge>chosen;long long total=0;
    for(const auto &e:forest)if(dsu.merge(e.u,e.v)){chosen.push_back(e);total+=e.w;}
    forest.swap(chosen);
    cout<<((int)forest.size()==n-1?total:-1)<<'\n';
}''',
    '尚不连通也保留最小生成森林；每周都输出；候选不是随便的一棵树，必须是前周最小森林；旧边仍可用的题意由交换性质保证。',
    r'每周至多n条候选，时间 $O(Wn\log n)$，额外空间 $O(n)$。',tags=['生成树','并查集'],lessons=K,declarations=DSU)

add('P2700','贵边优先保留，只有连接两个敌方组时才切断',
    '原道路是一棵树，若干城市被敌方占领。删除道路使任意两处敌方城市不连通，最小化被删道路的费用；城市编号从零开始。',
    r'''按破坏代价从大到小扫描。并查集记录当前保留道路的连通块，每块标记是否含敌方。边两端的块都含敌方时不能合并，删除并累加代价；否则保留并合并标记。这样尽量保留昂贵道路，把不可避免的断开留给便宜边。''',
    r'''把目标换成等价的保留费用最大：所有道路代价总和固定，少付删除费用就等于多保留代价。每个保留连通块最多含一处敌方城市。

从最贵道路开始考虑，若两端块中至多一块含敌方，连接后仍合法，可以保留。若两块都含敌方，这条边会连接两处敌方，必须拒绝；已经保留在两块内部的道路均不比当前便宜，用当前边切开不会更贵。

为了完整证明这个贪心，可以在仅用于论证的图里把所有敌方点认成一个逻辑点。原图是一棵树，某个保留子图中有两处敌方连通，当且仅当认点后出现环；没有这样的连通时，各块只是共享这个逻辑点，不会产生环。于是合法保留方案等价于认点图中的森林。按边从大到小、能不成环就加入，正是最大生成森林的Kruskal，交换性质保证保留总代价最大。

实现保持原始城市，并不真的让敌方城市互通。has[root]只说明这个实际保留连通块是否已有敌方。合并后用两个标记的或更新新根；按大小合并可能更换根，不能只更新原先较小编号。

图本来无环，因此保留的道路也无环。无需考虑额外删去非必要道路：删除它们只会增加费用。输入编号已经从零开始，不能再减一；答案最多约$10^{11}$，使用long long。''',
    r'''int n,k;cin>>n>>k;vector<char>has(n);for(int i=0,v;i<k;++i){cin>>v;has[v]=true;}
vector<Edge>edges(n-1);for(auto &e:edges)cin>>e.u>>e.v>>e.w;
sort(edges.begin(),edges.end(),[](const Edge &a,const Edge &b){return a.w>b.w;});DSU dsu(n);long long removed=0;
for(const auto &e:edges){int u=dsu.root(e.u),v=dsu.root(e.v);if(u==v)continue;
    if(has[u]&&has[v])removed+=e.w;
    else{bool occupied=has[u]||has[v];dsu.merge(u,v);has[dsu.root(u)]=occupied;}
}cout<<removed<<'\n';''',
    '代价降序，优先保留贵边；实际连通块最多一处敌方；合并后更新新根标记；城市从零编号；输出删除费用而非保留费用。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',tags=['生成树','贪心','并查集'],lessons=K,declarations=DSU)

add('P5425','常数接近模数，使最小生成树必为以N为中心的星',
    '完全图中两点距离由给定取模公式确定，将N头牛分成K个非空组，最大化不同组之间的最小距离。',
    r'''设模数P=2019201997，距离化为P-84x-48y，因为N≤7500，不会再次绕模。每个x<N的唯一最轻邻边都是(x,N)，所以这些星形边构成最小生成树。最优K组间距是删去K-1条最大树边时最小的被删边，等于P-84(K-1)-48N。''',
    r'''先利用实际常数，而不是建出至多两千八百万条边。原公式中的两个系数分别是模数P减八十四、P减四十八。对x<y，84x+48y最多约九十九万，严格小于P，所以取模结果恰为P-84x-48y，是正数。

固定顶点x<N。如果另一端y>x，边权随y变大而减小，最轻的一条指向N。如果另一端z<x，与(x,N)比较，其边权之差是84(x-z)+48(N-x)，严格为正。因此(x,N)是顶点x的唯一最轻邻边，按单点割的最轻边性质必须出现在最小生成树中。所有x<N的这些边正好组成以N为中心的星形树。

再解释分组与树边的关系。在任意最小生成树上删去K-1条最大边，会得到K个组，所有组间边都不小于最小被删树边；否则用更小的跨组边替换树边就能降低生成树总权。反过来，若要求组间最小距离再大一点，树中不超过这条门槛的边都必须留在同组，而这些边已经把点连成至多K-1块，无法再分成K组。所以这个门槛就是最佳间距。

星形边(x,N)随x递增而变小。最大的K-1条对应x=1至K-1，其中最小的一条恰为x=K-1，于是直接代入得到答案。这里的组间距离是任意两头不同组奶牛的原始距离，不是组到中心的距离和。

例如N=3、K=2，将一号单独分开，其余含中心三号的两头同组，间距就是边(1,3)。所有乘法使用long long即可，代码保留原常数形式的等价减法，不做浮点运算。''',
    r'''long long N,K;cin>>N>>K;const long long P=2019201997;
cout<<P-84*(K-1)-48*N<<'\n';''',
    'x<y时才使用对应系数；化简成立依赖N≤7500；删的是K-1条最大树边；答案是最小被删边，不是树边和。',
    r'时间与额外空间均为 $O(1)$。',tags=['生成树','结论与计数'],lessons=A+['graphs','modular'])

add('P5425','不依赖特殊化简，Prim求树后取分组门槛',
    '按给定距离形成完全图，分成K个非空组，使不同组之间的最小边权最大。',
    r'''隐式Prim按原公式计算边权，得到N-1条最小生成树边。升序排列这些边，第N-K+1小的值是最优分组间距：删去最大的K-1条边后，它是最小被删边。只保存每个点的最佳接入费用，不存完全图。''',
    r'''即使没有看出常数的星形结构，也可以直接用最小生成树解决分组。只要在同一组内有足够的短边把各点连通，组间才能保留较大门槛；这个门槛可以由Kruskal的连通层次或任意最小生成树读出。

先对原完全图执行Prim。每轮从未接入点中找最轻接入边，加入树后按原取模公式更新其它点的候选。费用随点对而定，可以临时计算，避免保存平方条边。

将树边升序记为w₁至wₙ₋₁。删除最大的K-1条后得到K块，最小被删边是wₙ₋ₖ₊₁。若有更便宜的原图边跨过这些块，用它替换相应树边就会得到更轻的树，矛盾，所以形成的组间距至少为该值。

另一方面，如果想让所有跨组边都严格大于该值，那么树的前N-K+1条边都必须落在组内。它们已经形成只有K-1个连通块的森林，任何满足要求的分组只能合并这些块，不能再细分成K组。这给出上界，与构造相同。

数组下标从零开始，读取升序树边的下标N-K。K=N时取最小树边，K=2时取最大树边。距离计算先将端点编号排序为x<y，不能随意交换两个系数。该做法比直接公式慢，但适用于更一般的显式距离函数。''',
    r'''int N,K;cin>>N>>K;const long long P=2019201997,INF=(1LL<<60);
vector<long long>best(N,INF),treeEdges;vector<char>used(N);best[0]=0;
for(int step=0;step<N;++step){int u=-1;for(int v=0;v<N;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;if(step)treeEdges.push_back(best[u]);
    for(int v=0;v<N;++v)if(!used[v]){long long x=min(u,v)+1,y=max(u,v)+1;
        long long w=(2019201913LL*x+2019201949LL*y)%P;best[v]=min(best[v],w);
    }
}sort(treeEdges.begin(),treeEdges.end());cout<<treeEdges[N-K]<<'\n';''',
    '原公式区分小编号x与大编号y；不存所有边；只收集N-1条真实接入边；N-K是零下标位置。',
    r'时间 $O(N^2)$，额外空间 $O(N)$。',tags=['生成树'],lessons=A+['graphs','sort','modular'],key='implicit-prim')

add('P12375','推迟Kruskal每次接受新边的时刻，两个上界一起达到',
    '构造n点m边的简单连通无向图，边权恰为一到m，使它的最小生成树权和最大；只输出最大值模998244353，多组数据，n、m可到10^18。',
    r'''设第i条被Kruskal接受的边权为r_i。前i-1次合并后，已读边至多装在一个i点团内，所以r_i≤C(i,2)+1；还必须给后面的n-1-i次合并留边，故r_i≤m-n+i+1。将这两个上界逐项取小可以同时达到。令D=m-n，p为不超过n-1且p(p-3)≤2D的最大整数，t=n-1-p；答案为C(p+1,3)+p+t(2D+p+n+2)/2，再取模。''',
    r'''Kruskal按边权一、二、三……扫描，接受一条跨连通块边就让生成树多一条。想让最小生成树总和大，就要尽量让这些被接受的边来得晚，把小权边先放在已经连通的部分中，使它们只形成环。

记第i次成功合并发生在权值r_i。此前只有i-1次合并，各连通块大小为s_j，满足各(s_j-1)之和为i-1。能够容纳的内部边数在把所有合并集中到一个i点块时最多，为C(i,2)：将两个非平凡块的合并预算集中起来，只会增加可放点对。因此在下一条新合并之前，最多只能读完C(i,2)条内部边，得到第一个上界。

另一个上界来自还没连接的顶点。总共还需要n-1-i条被接受边，而r_i之后只剩m-r_i条边，所以r_i≤m-n+i+1。故任何构造的树权都不超过下面各项之和：

$$r_i\le\min\left(\binom i2+1,\ D+i+1\right),\qquad D=m-n.$$

为什么所有项可以同时达到？逐次扩大一个团：已有i个点时，先把它们内部尚未使用的点对补成团，再用下一条边接入一个新点。这样成功合并权依次为一、二、四、七……。当剩余边必须留给尚未接入的点时，在当前团内用尽剩余可形成环的边，然后每一条剩余边都接入一个新点。没有重边或自环，最终连通，后半段成功边恰好是连续的D+i+1。若团已经覆盖全部点，剩余较重边直接放在未用点对中，不改变最小生成树。

当p<n-1时，接入第p+1个点后，当前已用的边数是C(p,2)+1；必须再为余下n-p-1个点各留一条新边。因此还能放入的内部环边预算为D-p(p-3)/2。p的最大性保证这个数在零至p-2之间，而当前团里仍有p-1个未使用点对，确实放得下。这说明上述构造没有暗中使用重边，也不会耗尽接入剩余点所需的边。

两上界的交界满足i(i-3)≤2D。令p为满足它的最大i，并限制p≤n-1，前p项取团容量上界，后t=n-1-p项取剩余边数上界。两部分分别为

$$S_1=\binom{p+1}{3}+p,$$

$$S_2=\frac{t(2D+p+n+2)}2.$$

答案是S₁+S₂取模。例子n=m=5时，前三条被接受边为一、二、四，最后一条必须留在五，合计十二；不能继续填团而导致剩余顶点没边可接。

代码先用平方根估计p，再用整数不等式向两边修正，避免浮点开根在整点边界误差。所有精确乘法先转__int128：答案不超过(n-1)m<10^36，在有符号128位范围内；先整除再取模，因此不需要模逆元。GNU C++17支持该整数类型，不能先在long long里乘完再转换。''',
    r'''int T;cin>>T;const long long MOD=998244353;
while(T--){long long n,m;cin>>n>>m;long long D=m-n;
    long long p=min(n-1,(long long)((3+sqrtl(9.0L+8.0L*D))/2));
    // 开根只是估计，最终边界用128位整数严格校正。
    while(p>0&&(__int128)p*(p-3)>(__int128)2*D)--p;
    while(p<n-1&&(__int128)(p+1)*(p-2)<=(__int128)2*D)++p;
    long long t=n-1-p;
    __int128 first=(__int128)p*(p-1)*(p+1)/6+p;
    __int128 second=(__int128)t*(2*D+p+n+2)/2;
    cout<<(long long)((first+second)%MOD)<<'\n';
}''',
    '同时考虑团容量与给剩余顶点留边；p限制在n-1；开根后整数校正；乘法先转__int128；整数除法先于最终取模。',
    r'每组固定范围内一次开根及常数次整数校正，时间 $O(T)$，除输入输出外空间 $O(1)$。',tags=['生成树','结论与计数'],lessons=A+['graphs','modular'])

add('CF1184E1','删掉第一条边，求两端重新连通的最低门槛',
    '只改变第一条边的权值，求不超过10^9的最大新权值，使它仍属于某棵最小生成树；可能属于即可，不要求所有最小生成树都包含它。',
    r'''暂时排除第一条边，把其它边按权升序加入并查集。其两端第一次连通时的权值B就是最小瓶颈替代路径，最大新权为B。若始终无法连通，第一条边是桥，任何权值都必须选，输出10^9。等于B时可交换得到包含它的最优树。''',
    r'''第一条边原来的权值不影响要找的阈值，关键是不用它时，两端能以怎样的最大边权接通。把其它边按升序加入，并查集第一次使它两端连通的门槛记为B，这正是替代路径上最大边权的最小值。

如果把第一条边设成大于B，替代路径的每条边都更轻，它成为这条环上唯一最重边，不可能出现在最小生成树中：任何包含它的树都可换成跨它断口的某条更轻路径边。

如果设成B，它可以与替代路径中的一条B权边交换，因此有一棵最小生成树包含它。更一般地，在加入小于B的边后，它两端仍在不同连通块；处理权B时优先接受这条边，再按Kruskal接完，就能得到所需最优树。题目只要求存在，所以这里等号必须保留。

若删掉它后两端永远不连通，它就是桥，任何生成树都不得不用它，无论新权值多大。题目允许的上限是10^9，所以输出这个上限，不是-1或无穷。

实现把第一条边单独读出，不把它放回排序候选。边权允许零，门槛也可能为零；不能用答案为零来表示还没找到替代路径。使用初值10^9，成功接通时覆盖它即可。''',
    r'''int n,m;cin>>n>>m;int a,b;long long ignored;cin>>a>>b>>ignored;--a;--b;vector<Edge>edges(m-1);
for(auto &e:edges){cin>>e.u>>e.v>>e.w;--e.u;--e.v;}
sort(edges.begin(),edges.end(),[](const Edge &x,const Edge &y){return x.w<y.w;});DSU dsu(n);long long answer=1000000000;
for(const auto &e:edges){dsu.merge(e.u,e.v);if(dsu.root(a)==dsu.root(b)){answer=e.w;break;}}
cout<<answer<<'\n';''',
    '排除待修改的第一条边；原权值不决定阈值；等于瓶颈仍允许；桥输出上限10^9；零权路径是有效答案。',
    r'时间 $O(m\log m+(n+m)\alpha(n))$，空间 $O(n+m)$。',tags=['生成树','并查集'],lessons=K,declarations=DSU)
