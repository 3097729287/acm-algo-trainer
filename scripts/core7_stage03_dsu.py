"""Connectivity, potentials and forests from the union-find unit."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
D=A+['dsu']
DSU=r'''struct DSU {
    vector<int>parent,size;
    DSU(int n):parent(n+1),size(n+1,1){iota(parent.begin(),parent.end(),0);}
    int find(int x){return parent[x]==x?x:parent[x]=find(parent[x]);}
    bool merge(int a,int b){
        a=find(a);b=find(b);if(a==b)return false;
        if(size[a]<size[b])swap(a,b);
        parent[b]=a;size[a]+=size[b];return true;
    }
};'''

add('P1536','统计已有连通块，再用道路把它们连成树',
    '若干组城镇与无向道路，允许重复道路。给每组图添加尽量少的道路，使所有城镇互相可达。读到单独的零结束。',
    r'''起初 n 个城镇是 n 个连通块。每读一条道路，若两端代表不同，就合并并把块数减一；代表相同则已经可达，不减。最后有 c 块，答案为 c−1：每条新道路最多减少一块，而从任意一块向其余各块各连一条便能达到。''',
    r'''要求是互相可达，允许经过中间城镇，并不要求每对城镇都有直接道路。已有的连通区域内部无需再修路，把每个区域看作一个整体即可。

并查集初始化时，每个城镇独立，令 c=n。道路连接 u、v 时，先找两端的根。如果根不同，两个区域连在一起，成功合并后 c 减一；根相同则只是在一个区域内部增加通道，不改变区域数。重复道路和形成环的道路都属于后一种情况。

剩 c 个区域时，一条新道路只有两个端点，最多把两个区域变成一个，因此至少需要 c−1 条。另一方面，从第一个区域选一个城镇，分别连向其它每个区域的一个城镇，恰好用 c−1 条就能互通。这同时给出下界和可行方案。

单个城镇或本来连通时输出零；没有道路时输出 n−1。程序先读 n，再判断是否为零，只有非零组才继续读 m；为每组重新建立并查集，不能沿用上一组的关系。''',
    r'''int n;
while(cin>>n&&n){
    int m;cin>>m;DSU groups(n);int components=n;
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;if(groups.merge(u,v))--components;}
    cout<<components-1<<'\n';
}''',
    '只在成功合并时减一；重复道路不重复减少块数；终止行只有一个零。',
    r'每组时间 $O(n+m\alpha(n))$，额外空间 $O(n)$。',tags=['并查集','图论'],lessons=D,declarations=DSU)

add('CF1263D','合并同一密码里的字母，只维护二十六个字母',
    '密码非空且只含小写字母。有共同字母的密码等价，等价还可以经由其它密码传递。求保证覆盖所有可能管理员密码所需的最少尝试数。',
    r'''在二十六个字母上建并查集，把每个密码的首字母与其中所有字母合并，并标记出现过的字母。最后只统计出现过的字母所对应的不同根。这些块恰是密码的等价类：同一密码把字母连在一起，共同字母把不同密码连起来。每类试一个密码且至少试一个。''',
    r'''逐对检查密码的共同字母会花二次方时间，但关系只经过二十六种字母，可以压缩连接对象。

同一个密码的全部字母由这个密码联系起来。将首字母与其余字母合并，就能让这些字母属于同一区域，不必为每对字母建边。两个密码若有共同字母，其字母区域便相交；多段共同字母关系也会自动传递。

反过来，字母间每一条合并连接都来自某个实际密码。沿这些连接从一个密码走到另一个密码时，相邻密码拥有共同字母，组成题目允许的等价链。因此不会额外合并本不等价的两类。

只统计真正出现的字母。未出现的字母虽有数组位置，却不对应候选密码，不能计数。每个密码非空，必挂在某个有效字母块中；重复字符和重复密码只重复尝试合并，不产生新类。

每类任选一个已给密码即可覆盖该类全部可能性。若某类一个也没试，便不能保证管理员没有选它，所以答案正好是有效块数。''',
    r'''int n;cin>>n;DSU groups(25);vector<int>used(26),seen(26);int answer=0;
for(int i=0;i<n;++i){string s;cin>>s;int first=s[0]-'a';for(char c:s){int x=c-'a';used[x]=1;groups.merge(first,x);}}
for(int x=0;x<26;++x)if(used[x]){int root=groups.find(x);if(!seen[root]){seen[root]=1;++answer;}}
cout<<answer<<'\n';''',
    '未出现的字母不计类；下标为零到二十五；等价关系包含传递关系。',
    r'总字符数为 L，时间 $O(n+L\alpha(26))$，当前输入串外的额外空间 $O(26)$。',tags=['并查集'],lessons=D+['strings'],declarations=DSU)

add('P1656','逐条暂时删去铁路，重建并查集检查是否断开',
    '连通无向图没有重边。找出删掉后会使图不连通的铁路，端点小者在前并按数对升序输出。',
    r'''枚举唯一被炸掉的铁路编号，重新初始化并查集并合并其它所有铁路。若最后不止一个连通块，这条铁路就是桥。n≤150、m≤5000，至多约二千五百万次边检查，直接重建可行。收集规范化端点并排序输出。''',
    r'''只有一发炮弹表示每次只删一条铁路。原图连通，删边后不连通当且仅当至少存在一对城市不能互达，这就是关键铁路的定义。

给每条铁路独立编号，枚举 skip。为这个候选新建并查集，初始块数为 n；遍历所有边，唯独跳过编号 skip，其余成功合并一次就把块数减一。结束后块数大于一即选中该边。这个过程直接验证定义，不需要猜哪些边看起来重要。

每个候选都必须重新初始化。前一个候选合并的关系若残留，普通并查集又不能拆组，就会污染之后的判断。环上删一条边仍能绕行，对应重建后仍只有一块；树的每条边则都会选中。

用编号跳过候选，使“只删一次，其余全部保留”容易检查。收集答案时转换成 min(u,v)、max(u,v)，最后整体排序；输出端点与并查集代表无关。

本方法利用小规模直接验证。另一解法用 DFS 访问时间和回边最低到达时间一次找出所有桥，适合更大图，单独列在算法选择中。''',
    r'''int n,m;cin>>n>>m;vector<pair<int,int>>edge(m),answer;
for(auto &e:edge)cin>>e.first>>e.second;
for(int skip=0;skip<m;++skip){DSU groups(n);int components=n;
    for(int i=0;i<m;++i)if(i!=skip&&groups.merge(edge[i].first,edge[i].second))--components;
    if(components>1)answer.push_back(minmax(edge[skip].first,edge[skip].second));
}
sort(answer.begin(),answer.end());for(auto e:answer)cout<<e.first<<' '<<e.second<<'\n';''',
    '每条候选重新建组；原图保证连通；规范化并排序输出实际端点。',
    r'时间 $O(mn+m^2\alpha(n))$，空间 $O(n+m)$。',tags=['并查集','图论','枚举'],lessons=D+['structures','sort'],key='rebuild',declarations=DSU)

add('P1656','DFS 记录子树能绕到的最早祖先，一次找出所有桥',
    '找出连通无向图中删掉后使图断开的铁路，并按规范化端点数对升序输出。',
    r'''首次访问 u 时记入时间 dfn[u]；low[u] 表示其 DFS 子树经树边和一条向上回边能到的最早访问时间。树边 u−v 是桥当且仅当 low[v]>dfn[u]，即 v 子树绕不开父边去到 u 或更高祖先。子树算完后更新父亲，收集并排序。''',
    r'''DFS 把首次发现新点的边选作树边。对父亲 u 与孩子 v，若不存在别的路把 v 的整棵子树接回 u 或更高祖先，删去 u−v 就会隔离这棵子树；存在这样的绕路时，父边便可替代。

dfn[u] 是首次访问的递增时间，low[u] 初始等于 dfn[u]。检查 u−v：若 v 尚未访问，先递归处理 v，再用 low[v] 更新 low[u]；若 v 已访问且不是当前父边，就用 dfn[v] 更新 low[u]。前者传回整棵子树的最低时间，后者记录一条非树边能直接到的位置。

在 v 处理完后比较 low[v] 和 dfn[u]。严格大于表示没有绕路，是桥；等于表示能绕回 u，已经可以避开父边，不是桥。不能误写成大于等于。

无向 DFS 不会漏掉横跨两棵独立子树的通道：若存在一条边通向尚未访问的点，DFS 会当场把它纳入当前子树。因此所有可能的绕路均在上述树边与回边更新中体现。

邻接表保存边编号，递归只跳过当前父边的反向记录，避免把父亲顶点与实际父边混淆。本题 n≤150，递归深度也不超过一百五十；迁移到很深的大图时，应改用显式调用栈。

根的每条孩子边仍用同一桥判据，不要套用割点的根特殊规则。最后规范化并排序，因为 DFS 发现顺序并非输出字典序。''',
    r'''int m;cin>>vertices>>m;graph.assign(vertices+1,{});dfn.assign(vertices+1,0);low.assign(vertices+1,0);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back({v,i});graph[v].push_back({u,i});}
for(int u=1;u<=vertices;++u)if(!dfn[u])dfs(u,-1);
sort(bridges.begin(),bridges.end());for(auto e:bridges)cout<<e.first<<' '<<e.second<<'\n';''',
    '子树完成后判断；等于已存在绕路；跳过父边编号；不要套割点根规则。',
    r'DFS 时间 $O(n+m)$，答案排序 $O(m\log m)$，空间 $O(n+m)$。',tags=['DFS','图论'],lessons=A+['graphs','recursion','structures','sort'],key='lowlink',
    declarations=r'''int vertices,timer=0;vector<vector<pair<int,int>>>graph;vector<int>dfn,low;vector<pair<int,int>>bridges;
void dfs(int u,int parent_edge){
    dfn[u]=low[u]=++timer;
    for(auto [v,id]:graph[u]){
        if(id==parent_edge)continue;
        if(!dfn[v]){dfs(v,id);low[u]=min(low[u],low[v]);if(low[v]>dfn[u])bridges.push_back(minmax(u,v));}
        else low[u]=min(low[u],dfn[v]);
    }
}''')

add('P2256','姓名映射为整数，合并组别后回答同组查询',
    '先给全部参赛选手姓名，再给同组关系及询问。同组关系有传递性，严格输出 Yes. 或 No.。',
    r'''把每个姓名映射为唯一整数编号，之后用并查集维护组别。每条关系合并两个编号；每条询问比较根是否相同。姓名只用来找到编号，不能以字符串相等代替同组。map 的字符串查找需要对数次比较，不依赖哈希在特定输入上的表现。''',
    r'''姓名是选手身份，所属组会随关系合并而扩大。先按给定顺序分配一到 n 的编号，使用 map<string,int> 保存姓名到整数的对应，再处理关系。

每条 A 与 B 同组的关系都合并两者编号。原先不是同组时连接两个根；已同组时重复关系不改变结果。A 与 B、B 与 C 会使 A、C 沿父指针到达同一根，因此传递关系不必额外枚举。

询问比较 find(id[X]) 与 find(id[Y])，不能只比较当前直接父亲，因为同组成员也可能暂时有不同父亲。根相同表示已经由关系链连通，输出 Yes.；不同则输出 No.。

题目保证关系和询问中的姓名均已登记，因此程序可直接用 map 下标读编号。在一般程序中，读取未知键会默认插入一项，下标操作不能当成检查姓名存在；这里依赖的是已给保证。

map 按字符串字典序组织键。查找需要对数次比较，每次比较还与姓名长度有关；本题名字最长二十，不应把字符串查找在概念上等同于整数数组访问。输出末尾句点也要保留。''',
    r'''int n,m;cin>>n>>m;map<string,int>id;for(int i=1;i<=n;++i){string name;cin>>name;id[name]=i;}
DSU groups(n);
for(int i=0;i<m;++i){string a,b;cin>>a>>b;groups.merge(id[a],id[b]);}
int queries;cin>>queries;
while(queries--){string a,b;cin>>a>>b;cout<<(groups.find(id[a])==groups.find(id[b])?"Yes.":"No.")<<'\n';}''',
    '先登记全部姓名；比较根而非直接父亲；末尾句点必须保留。',
    r'最长姓名 L，时间 $O((n+m+K)L\log n+(m+K)\alpha(n))$，空间 $O(nL)$。',tags=['并查集'],lessons=D+['maps','strings'],declarations=DSU)

add('P3420','钥匙位置形成函数图，每个弱连通块恰需砸一只',
    '第 i 只罐的钥匙放在第 x 只罐里。打开罐后可取出其中全部钥匙，求打开所有罐最少要砸多少只；只需数量。',
    r'''连有向边 i→x，每点恰有一条出边，每个忽略方向的连通块恰含一个有向环。环的钥匙互相锁住，至少砸一只；砸环上一只后，可开完整环并沿入树向外开全部罐。所以答案是弱连通块数，用并查集合并 i、x 统计。''',
    r'''i→x 表示要开 i，先到 x 取钥匙。这是依赖方向，拿到钥匙后的实际开罐传播方向相反。每个罐自己的钥匙仅有一个存放位置，因此每个点恰有一条出边。

从任一点不断沿出边走，最终必定重复，形成有向环。一条边两端沿出边走的最终环相同，沿无向边连接的所有点也因此具有同一个最终环；所以每个弱连通块恰有一个环，其余点的依赖路径汇入它。

环上任何一只都未开时，拿不到彼此的钥匙，必须先砸环上一只。随后沿环反向依次打开整环，再按离环越来越远的顺序打开入树中的罐。每块砸一只足够，不同块又无法互相提供钥匙，因此数量等于块数。

不能说在块中任砸一只。例如 1→2、2→3、3→2，砸一号未必得到二号或三号的钥匙，仍打不开环；砸二号或三号才行。程序只求数量，无须构造被砸编号。

从 n 块开始，每读 x 就合并 i、x，成功才减一。不必保存有向图也能统计弱连通块。自环表示钥匙锁在自己的罐里，仍需砸一次；它不会成功合并到别块，计数自然保留。''',
    r'''int n;cin>>n;DSU groups(n);int components=n;
for(int i=1;i<=n;++i){int x;cin>>x;if(groups.merge(i,x))--components;}
cout<<components<<'\n';''',
    '应砸环上的罐；依赖箭头与拿钥匙传播方向相反；自环也要砸一次。',
    r'时间 $O(n\alpha(n))$，空间 $O(n)$。',tags=['并查集','图论'],lessons=D+['graphs'],declarations=DSU)

add('P10378','交流双方染成异色，各块独立选择两侧人数',
    '交流一定发生在不同学校之间，输入合法。求已知 n 名同学中 B 校人数的最小、最大可能值。',
    r'''同学为点、交流为无向边，每条边两端异色。对每块 BFS 二染色得到两侧人数 a、b，可整体交换两色对应的学校，因此最小值加 min(a,b)，最大值加 max(a,b)。各块无约束相连，选择相互独立。孤立点两侧为一与零，可属于任意学校。''',
    r'''没有交流不表示同校，只表示没有约束。每次已知交流则明确要求两人异校，这是相邻点颜色不同的二分图条件。

从未染色的同学出发染零色，沿边走到的同学染成相反颜色，使用队列处理。输入保证合法，不会在奇环上产生矛盾。在一个连通块里，一旦确定起点属于哪校，其余人的学校便沿边全部确定。

若两侧人数是 a、b，可以让零色属于 B 得 a 人，也可以整体交换得 b 人。不能在块内单独交换一个点，否则会破坏其邻边约束。不同块之间没有边，因此可独立选择，最小人数是各块较小侧之和，最大人数是较大侧之和。

孤立点也要单独处理，两侧人数一与零，贡献最小零、最大一。忽略它会使最大值偏小。重复交流不重复统计学生；每人只在首次染色入队时计数。人数只针对给定的 n 名同学，不额外猜测活动外还有多少学生。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>color(n+1,-1);int minimum=0,maximum=0;
for(int start=1;start<=n;++start)if(color[start]==-1){
    int count[2]={1,0};queue<int>todo;todo.push(start);color[start]=0;
    while(!todo.empty()){int u=todo.front();todo.pop();for(int v:graph[u])if(color[v]==-1){color[v]=color[u]^1;++count[color[v]];todo.push(v);}}
    minimum+=min(count[0],count[1]);maximum+=max(count[0],count[1]);
}
cout<<minimum<<' '<<maximum<<'\n';''',
    '无边不表示同校；每块可整体换色；孤立点贡献零或一；输入保证可二染色。',
    r'时间、空间均为 $O(n+m)$。',tags=['BFS','图论'],lessons=A+['graphs','queue-stack'])

add('CF1365D','封住坏人相邻空格，再从出口检查全部人',
    '只可在空格加墙，使所有好人都能到右下角、所有坏人都不能到。已有的人与墙不能改，允许封掉原本为空的出口。',
    r'''坏人邻接好人则无解，否则把坏人旁的全部空格封墙，再从未封的出口 BFS。检查每个 G 可达且每个 B 不可达。任何合法好人路线都不能经过坏人相邻空格，否则坏人可一步加入这条路线；所以这些墙不会误删合法方案必需的通路。''',
    r'''坏人与好人相邻时，若好人能走出去，坏人就能先走到好人原来的格子，再沿同一路线逃走。人所在格不能封，因此这种情况无解。

其它情况下，将坏人相邻的全部空格封墙。假设合法方案中一条好人路线经过这样的空格，某个坏人只要一步走到该格，就能沿路线剩余部分逃走，矛盾。因此合法好人路线本就不能使用这些格子，全部封上不会损失任何合法方案。

移动是无向的，从出口做一次 BFS，访问集合恰好是能走到出口的格子，不必从每人分别搜索。若有好人未访问，便没能全部救出；若有坏人被访问，便仍能逃走；两者都没有时，当前墙的设置本身就是可行方案。

出口若已被封，不启动 BFS。有好人时会因不可达失败，没有好人时则可能成功，不能一律判无解。相邻坏人可以一起隔在墙后，不必直接失败；好人可共享通道。

题目求存在方案，并不要求加墙最少，所以可把全部上述危险空格都封掉，再进行这个确定的可达性检查。''',
    r'''int tests;cin>>tests;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(tests--){int n,m;cin>>n>>m;vector<string>grid(n);for(auto &row:grid)cin>>row;bool possible=true;
    for(int r=0;r<n;++r)for(int c=0;c<m;++c)if(grid[r][c]=='B')for(int d=0;d<4;++d){int nr=r+dr[d],nc=c+dc[d];if(nr<0||nr>=n||nc<0||nc>=m)continue;if(grid[nr][nc]=='G')possible=false;else if(grid[nr][nc]=='.')grid[nr][nc]='#';}
    vector<vector<int>>seen(n,vector<int>(m));queue<pair<int,int>>todo;
    if(grid[n-1][m-1]!='#'){seen[n-1][m-1]=1;todo.push({n-1,m-1});}
    while(!todo.empty()){auto [r,c]=todo.front();todo.pop();for(int d=0;d<4;++d){int nr=r+dr[d],nc=c+dc[d];if(nr>=0&&nr<n&&nc>=0&&nc<m&&grid[nr][nc]!='#'&&!seen[nr][nc]){seen[nr][nc]=1;todo.push({nr,nc});}}}
    for(int r=0;r<n;++r)for(int c=0;c<m;++c)if((grid[r][c]=='G'&&!seen[r][c])||(grid[r][c]=='B'&&seen[r][c]))possible=false;
    cout<<(possible?"Yes":"No")<<'\n';
}''',
    '坏人挨好人无解；只封空格；出口可以封；没有好人时不强求出口可达。',
    r'每组时间、空间均为 $O(nm)$。',tags=['BFS','贪心','图论'],lessons=A+['graphs','queue-stack','greedy','strings','structures','bindings'])

add('UVA10369','按距离连接到剩 S 个无线区域，卫星再连接这些区域',
    'P 个哨所坐标已知，所有无线设备采用同一通信半径 D，另可给 S 个哨所配卫星设备，卫星之间不受距离限制。求让全网互通的最小 D，保留两位小数。[原站 PDF](https://onlinejudge.org/external/103/10369.pdf)。',
    r'''固定 D，把距离不超过 D 的哨所连边。若有 c 个无线连通块，至少每块一个卫星端点，因此恰在 c≤S 时能由卫星接通。按距离从小到大做 Kruskal，直到成功合并 P−S 次，最后一次的距离就是最小半径。比较距离平方，最终只开一次平方根。''',
    r'''卫星设备连接的是被选中的哨所，并非任意删除一条远边。先只考虑无线网络，若分成 c 块，为把这些块接到一起，每块至少要有一个卫星哨所；若 c≤S，每块任选一个配卫星就足够。因此问题转成：求最小半径，使无线图连通块数不超过 S。

列出每对哨所的距离平方并排序，从短到长加入边。并查集只在两块首次接通时成功合并，每次减少一块。最初 P 块，成功合并 P−S 次恰好降至 S 块，最后一次所用距离给出可行半径。

在这条边之前的所有更短边都已处理。若不用达到这一距离的边，连通块数仍大于 S，不可能靠 S 个卫星端点覆盖全部无线区域。因此更小半径无解，当前半径最优。相同距离的边任选处理顺序，最终阈值不变。

也可以先构造完整最小生成树，再去掉最长的 S−1 条边；直接在剩 S 块时停止，省去了不必保留的后续边。这里优化的是无线最大边长，不是把卫星费用加到欧氏距离上。

原题给 S<P≤500，坐标为零到一万的整数。距离平方可用 long long 精确比较，避免排序中反复计算浮点根；只在输出前 sqrt，并用 fixed 与 setprecision(2) 输出。输入有多组，每组重新建图和并查集。''',
    r'''int tests;cin>>tests;while(tests--){
    int satellites,n;cin>>satellites>>n;vector<pair<long long,long long>>point(n);
    for(auto &p:point)cin>>p.first>>p.second;vector<Edge>edges;
    for(int i=0;i<n;++i)for(int j=0;j<i;++j){long long dx=point[i].first-point[j].first,dy=point[i].second-point[j].second;edges.push_back({dx*dx+dy*dy,i,j});}
    sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.square<b.square;});
    DSU groups(n);int components=n;long long last=0;
    for(auto e:edges){if(components<=satellites)break;if(groups.merge(e.u,e.v)){--components;last=e.square;}}
    cout<<fixed<<setprecision(2)<<sqrt((double)last)<<'\n';
}''',
    '成功合并 P−S 次；S 个卫星端点覆盖的是无线连通块；排序比较平方，输出才开根。',
    r'边数 $O(P^2)$，时间 $O(P^2\log P)$，空间 $O(P^2)$。',tags=['生成树','并查集'],lessons=D+['sort','lambda-local','structures','geometry','numeric-tools'],declarations=DSU+'\nstruct Edge{long long square;int u,v;};',exact=True)

add('P1621','筛出质数，把区间里同一大质因数的倍数合并',
    '初始每个区间整数单独成组，允许合并拥有不小于 p 的共同质因数的两个整数，求最终组数。',
    r'''筛出不超过 b 的质数，对每个质数 q≥p，找区间内第一个倍数 f，再把后续所有 q 的倍数与 f 合并。它们都共享合法质因数；任意可合并的原整数对也必在某个这样的质数中被连接，因此最终得到全部传递合并。只统计区间 a 到 b 的组数。''',
    r'''判定条件是共同质因数，不是最大公约数本身大于 p。例如两个数的 gcd 为六、p 为五时，公因数六虽大于五，质因数却只有二和三，不满足条件。

对某个合法质数 q，区间内所有 q 的倍数都可直接相互合并。只需选第一个倍数 f 作为中间点，把其它倍数接向 f，连接成一组即可，不必把每对倍数建边。

第一项 f 等于 ceil(a/q) 乘 q；正整数运算可写成 (a+q−1)/q*q。如果 f>b，这个质数在区间没有倍数；只有一个倍数时也不会成功合并。筛法只枚举质数，不能把四、六等合数当作独立的合法质因数。

程序每次成功合并都来自共享 q≥p，所以不会额外连接不合法的对象。反过来，任何一对拥有合法共同质因数的原整数，都在该质数的倍数组中连通；所以算法最终包含题目允许的全部边及其传递闭包。

父数组按原整数值开到 b，但连通块计数从 b−a+1 开始，循环只对区间内倍数合并。小于 a 的数组位置只是未用槽位，不能加入答案。重复由不同质数连接同一组时，merge 返回 false，不再减数。''',
    r'''int a,b,p;cin>>a>>b>>p;vector<int>composite(b+1);DSU groups(b);int components=b-a+1;
for(int q=2;q<=b;++q)if(!composite[q]){
    if(q<=b/q)for(int multiple=q*q;multiple<=b;multiple+=q)composite[multiple]=1;
    if(q<p)continue;int first=(a+q-1)/q*q;
    for(int x=first+q;x<=b;x+=q)if(groups.merge(first,x))--components;
}
cout<<components<<'\n';''',
    '枚举质数而非全部大公因数；只合并区间内倍数；组数不含小于 a 的槽位。',
    r'筛法 $O(b\log\log b)$；倍数访问数不超过 $O(b\log\log b)$，合并摊还再乘 $\alpha(b)$；空间 $O(b)$。',tags=['并查集','素数'],lessons=D+['prime-sieve','number-theory'],declarations=DSU)

add('P2916','把往返路程和重复谈话折算到边上，再求最小生成树',
    '在保持所有牧场连通的前提下删掉尽量多道路，随后从自选牧场出发访问全部奶牛并回到起点。走边耗时 L，每次到达牧场都要谈话 C，起点出发与最终返回各谈一次，求最少总时间。',
    r'''删最多道路后只能留下生成树。树中最省的闭合遍历让每条边走两次，路程贡献 2L；牧场 v 被到达 deg(v) 次，起点另有出发时的一次。因此总费用为所留边的 Σ(2L+C[u]+C[v]) 加起点的 C。起点独立选 C 最小者，按新边权 Kruskal 求最小生成树。''',
    r'''连通 n 个点至少留 n−1 条边。若留下环，还可删环上一边保持连通，因此“删掉尽量多”使保留图必须是一棵生成树，不能另选多留边来缩短行走。

树上每条边是访问两侧所必经的唯一通道。从起点出发最后回到起点，每条边至少往返各一次；深度优先遍历可以恰好每边走两次，达到最少路程 2ΣL。

这时牧场 v 的每条相邻边恰有一次向 v 的到达，共 deg(v) 次谈话；起点还多了最开始尚未走边时的一次。最终返回的谈话已在“沿相邻边到达”中计过，不应再额外加第二次。于是谈话总费用为 ΣC[v]deg(v)+C[start]。

每条边 u−v 各给两端增加一个度数，故把两部分合在一起，单边新权值是 2L+C[u]+C[v]，全部边权之和外再加 C[start]。起点可任意选择，与树的选择独立，取全体 C 的最小值即可。

现在才是标准最小生成树：对新权值排序，跨块的边才选入，成功 n−1 次结束。不能先按原路程 L 选树再加谈话费用，两种排序可能选出不同树。答案使用 long long，保留零长度道路，谈话费用仍正常计入。''',
    r'''int n,m;cin>>n>>m;vector<long long>cost(n+1);long long answer=LLONG_MAX;
for(int i=1;i<=n;++i){cin>>cost[i];answer=min(answer,cost[i]);}
vector<Edge>edges(m);for(auto &e:edges){long long length;cin>>e.u>>e.v>>length;e.weight=2*length+cost[e.u]+cost[e.v];}
sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.weight<b.weight;});
DSU groups(n);int chosen=0;for(auto e:edges)if(groups.merge(e.u,e.v)){answer+=e.weight;if(++chosen==n-1)break;}
cout<<answer<<'\n';''',
    '先改边权再排序；最终返回谈话已在度数项中，只另加一次起点 C；保留图必须是树。',
    r'时间 $O(m\log m+m\alpha(n)+n)$，空间 $O(n+m)$。',tags=['生成树','并查集'],lessons=D+['trees','graphs','sort','structures','lambda-local','counting'],declarations=DSU+'\nstruct Edge{int u,v;long long weight;};')

add('CF1624G','从高位到低位尝试禁止这一位，连通才保留禁令',
    '连通无向图边权为正整数，选择一棵生成树，使所有所选边权的按位或尽量小。求这个最小或值，不是边权和。',
    r'''维护已决定必须为零的位集合 forbidden。从二十九位向零位尝试加入新禁位，只用不含任何禁位的边做连通检查；若仍连通，就能找到使该位为零的生成树，保留禁令，否则答案该位必须为一。每次判定都新建并查集，数值比较由最高不同位决定，故可逐位贪心。''',
    r'''按位或的一位为零，当且仅当每条选中边这一位都为零。因此若要求某些位统一为零，只需删除所有含这些位的边，检查剩余图是否连通。连通图一定有生成树，所以这是充要条件。

从高位向低位决定答案，因为最高不同位的一次变小，胜过所有低位可能增加的总和。forbidden 记录已能保持为零的高位。试着再禁止当前位，重新用满足 (weight & trial)==0 的全部边合并。

若仍连通，至少有一棵生成树满足全部已选零位，当前位可设零；把试探禁令保存。若不连通，任何满足先前零位约束的生成树都必须选一条带当前位的边，所以当前答案位必为一。之后再限制更低位不会改变这一必然性。

每次只保留通过连通检查的禁令，因此始终存在满足当前约束的生成树；全部位判完后，每个失败位对所有剩余生成树都必须出现，而成功位均不出现，得到的正是最小或值。

边权不超过十亿，只需检查二十九到零位。每次重建并查集，不能沿用上一轮被删除边带来的合并。反例三角形边权为三、四、四：最小和树取三与四，但或为七；取四与四的或为四，才是本题最优。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<Edge>edges(m);for(auto &e:edges)cin>>e.u>>e.v>>e.weight;
    int forbidden=0,answer=0;
    for(int bit=29;bit>=0;--bit){int trial=forbidden|(1<<bit);DSU groups(n);int components=n;
        for(auto e:edges)if((e.weight&trial)==0&&groups.merge(e.u,e.v))--components;
        if(components==1)forbidden=trial;else answer|=1<<bit;
    }
    cout<<answer<<'\n';
}''',
    '优化按位或而非和；判定是全部禁位均不得出现；每轮重建；从高位先决定。',
    r'每组时间 $O(30(n+m\alpha(n)))$，空间 $O(n+m)$。',tags=['并查集','位运算','贪心'],lessons=D+['bitwise','greedy','graphs','structures'],declarations=DSU+'\nstruct Edge{int u,v,weight;};')

add('P7991','把已有连通块缩成点，扫描每块到两端区域的最近距离',
    '已有道路免费，至多新建两条道路，使田地一与田地 N 连通。新连 i、j 的费用为 (i−j) 的平方，求最小费用。',
    r'''先并查集得到一号区域 A、N 号区域 B。枚举中转区域 C，费用是 C 到 A 的最小编号距离平方，加 C 到 B 的最小距离平方，两条路在 C 的端点可不同，靠已有路连接。对所有田地向左、向右各扫描一次，得到到 A、B 的最近编号，再按根取最小值。C 可为 A 或 B，覆盖只修一条或不修。''',
    r'''已有连通块内部可免费通行。若修两条路，一条从起点所在块 A 进入某个中间块 C，另一条从 C 到终点块 B；进入与离开 C 的田地不必相同，因为它们已有免费路径相连。

对固定 C，两条新边互不限制，因此可独立选择最便宜的一条 A−C 边和一条 C−B 边。分别记最小费用为 bestA[C]、bestB[C]，枚举 C 取两者和的最小值。

如何求各块的最近距离：田地编号已经有序。从左到右维护最近一个属于 A 的编号 lastA，就得到每个田地左侧最近 A 位置；从右到左再扫，补上右侧最近位置。B 同理。最靠近的 A 田地必位于这两者之一，距离越近其平方也越小，因此两遍扫描足够，不必枚举田地对。

对田地 i 算出的候选费用归入其并查集根，更新该块的最小值。A 内部到 A 的费用自然为零，B 内部到 B 同理；所以令 C=A 或 C=B 会包含只修一条路的方案，若 A、B 已连通，直接输出零。

反过来，任意至多两条新路的可行方案都可压缩成上述某个中转块的路径，多余绕行不可能降低非负费用，因此枚举没有遗漏。平方和可能超过 int，先转 long long 再乘，不能让乘法先在 int 内溢出。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;DSU groups(n);
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;groups.merge(u,v);}vector<int>root(n+1);for(int i=1;i<=n;++i)root[i]=groups.find(i);
    int start=root[1],finish=root[n];if(start==finish){cout<<0<<'\n';continue;}
    const long long infinity=1LL<<60;vector<long long>a(n+1,infinity),b(n+1,infinity);
    for(int direction:{1,-1}){int nearestA=-1,nearestB=-1;
        for(int i=direction==1?1:n;1<=i&&i<=n;i+=direction){
            if(root[i]==start)nearestA=i;if(root[i]==finish)nearestB=i;
            if(nearestA!=-1){long long delta=i-nearestA;a[root[i]]=min(a[root[i]],delta*delta);}
            if(nearestB!=-1){long long delta=i-nearestB;b[root[i]]=min(b[root[i]],delta*delta);}
        }
    }
    long long answer=infinity;for(int i=1;i<=n;++i)if(root[i]==i)answer=min(answer,a[i]+b[i]);cout<<answer<<'\n';
}''',
    '中转块的入点和出点可不同；扫描左右两侧；按连通块取最小；平方先转 long long。',
    r'每组时间 $O(n+(n+m)\alpha(n))$，空间 $O(n)$。',tags=['并查集','图论'],lessons=D+['graphs'],declarations=DSU)

add('P16495','同缺一种景色就相连，把景点连通性压到至多六十个零位',
    '依次插入景点位掩码，每次输出最少几次踏青能访问目前全部景点。一次路线允许重复访问，相邻两景点的按位或必须不是全一。',
    r'''两景点能相邻，当且仅当至少共同缺一种景色。把每个零位当一个中介点，景点把自己所有零位合并；出现过的零位连通块数就是这些非全一景点的路线数。全一景点没有零位，与任何其它景点都不能相邻，每次出现单独加一。每次插入只合并至多 n 个位，空间无需随 q 增长。''',
    r'''允许重复访问意味着不用求不重复的路径。一个连通块可从任意点出发，沿生成树往返走遍全部点，用一次踏青覆盖；不同连通块之间没有合法相邻步骤，不能放在同一路线。因此答案就是当前景点图的连通块数。

两个掩码按位或不为全一，等价于某一位在两者中都为零。对每种景色设一个“缺少它”的中介点，一个景点连接其全部零位。共享零位的两个景点就经同一中介连通；反过来，沿中介连接的景点链每一步都共享某个零位，恰好是合法路线。

一个非全一景点至少有一个零位，把这些位合并后，它属于一个有效位连通块。刚出现的新零位先成为独立块，数量加一；合并不同位块时数量减一。最终有效位块与非全一景点连通块一一对应，不必为每次插入新建景点节点。

全一景点没有任何零位，与任何其它景点的或都为全一，即使两个掩码相同也不能相邻。不同次搜索得到的全一景点是分别待覆盖的景点，必须每次单独加一；不能把重复全一掩码去重。其它重复掩码则共享零位，会自然连在一起。

用 (1ULL<<n)−1 表示低 n 位全一，n≤60，位移和掩码均用 unsigned long long。遍历零到 n−1 位，不能把高位补零也当缺少的景色。时间与位数 n 成正比，但只维护至多六十个中介，不维护五十万个景点。''',
    r'''int n,q;cin>>n>>q;DSU groups(n);vector<int>used(n);int components=0,isolated=0;
unsigned long long full=(1ULL<<n)-1;
while(q--){unsigned long long value;cin>>value;if(value==full){++isolated;cout<<components+isolated<<'\n';continue;}
    int first=-1;
    for(int bit=0;bit<n;++bit)if(((value>>bit)&1ULL)==0){
        if(!used[bit]){used[bit]=1;++components;}
        if(first==-1)first=bit;else if(groups.merge(first,bit))--components;
    }
    cout<<components+isolated<<'\n';
}''',
    '允许重复访问，所以求连通块而非哈密顿路径；合并零位；全一每次独立；仅处理低 n 位。',
    r'时间 $O(qn\alpha(n))$，额外空间 $O(n)$，其中 $n\le60$。',tags=['并查集','位运算','图论'],lessons=D+['graphs','bitwise','unsigned64'],declarations=DSU)

add('P2294','区间收入改成前缀和之差，用带权并查集判矛盾',
    '若干条记录给出连续月份的收入总和，收入允许为负。判断是否存在一份月收入账本同时满足所有记录，每组输出小写 true 或 false。',
    r'''设 S[i] 为前 i 月总收入，记录 s 到 t 收入 v 等价于 S[t]−S[s−1]=v。在前缀下标零到 n 上建带权并查集，offset[x] 保存 S[x]−S[parent[x]]。两端同根时检查已有差值；不同根时按等式推导两根之差后合并，不能把区间当成相同组直接合并。''',
    r'''原约束是区间和，直接给每个月猜收入会产生巨大搜索。引入前缀 S[0] 到 S[n] 后，每条约束只联系两个量：S[t]−S[s−1]=v。月份收入仍可由相邻前缀之差还原，所以没有增加限制；即使某个前缀分量与 S[0] 不连通，也可独立选一个整体平移量。

带权并查集的根只是差值坐标的代表。offset[x] 表示 S[x]−S[parent[x]]，路径压缩后要累加为 S[x]−S[root]。find 必须先保存旧父亲，递归压缩旧父亲，再把其到根的差值加到当前点，不能只改 parent 丢掉距离。

令 x=s−1、y=t，压缩后两根为 rx、ry，当前偏移 dx=S[x]−S[rx]、dy=S[y]−S[ry]。若同根，要求 dy−dx=v，已有关系不符就是矛盾。若不同根，由

$$S[ry]-S[rx]=v+dx-dy$$

得到把 ry 接到 rx 时应存的偏移。若为按大小合并而反向挂接，就存相反数，不能只交换根而忘了改变符号。

不同分量原本没有相对位置约束，平移整个一侧即可满足新等式；只有同分量的闭合约束可能矛盾。因此所有等式检查通过，当且仅当存在一致前缀赋值，再取相邻差便得到月收入。

即使已发现矛盾，也必须读完本组剩余记录，保持下一组输入对齐。使用 long long 累计差值，允许负收入；不把“总收入为负”误判为伪造。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;WeightedDSU groups(n);bool possible=true;
    for(int i=0;i<m;++i){int s,t;long long value;cin>>s>>t>>value;if(!groups.constrain(s-1,t,value))possible=false;}
    cout<<(possible?"true":"false")<<'\n';
}''',
    '前缀下标是 s−1 与 t；压缩时累计偏移；反向挂根需反号；负收入合法；读完全部记录。',
    r'每组时间 $O(n+m\alpha(n))$，空间 $O(n)$。',tags=['并查集','前缀和'],lessons=D+['prefix','weighted-dsu'],
    declarations=r'''struct WeightedDSU{
    vector<int>parent,size;vector<long long>offset;
    WeightedDSU(int n):parent(n+1),size(n+1,1),offset(n+1){iota(parent.begin(),parent.end(),0);}
    int find(int x){if(parent[x]==x)return x;int old=parent[x];parent[x]=find(old);offset[x]+=offset[old];return parent[x];}
    bool constrain(int x,int y,long long value){
        int a=find(x),b=find(y);long long difference=value+offset[x]-offset[y];
        if(a==b)return difference==0;
        if(size[a]>=size[b]){parent[b]=a;offset[b]=difference;size[a]+=size[b];}
        else{parent[a]=b;offset[a]=-difference;size[b]+=size[a];}
        return true;
    }
};''')

add('P1196','带权并查集存相对位置，队首位置与代表分开维护',
    '三万艘舰船初始各成一列。M i j 把 i 所在整列接到 j 所在列尾部，不改变列内顺序；C i j 询问两舰之间的舰船数，不同列输出负一。',
    r'''offset[x] 保存舰船位置减父亲位置，压缩后得到相对根的坐标；size[root] 是队伍长度，head[root] 是根距实际队首的位置。把 A 接到 B 后，A 的所有坐标整体增加 size[B]。两根的新差为 size[B]+head[A]−head[B]，按大小挂接时存该差或相反数，并更新幸存根的队首距离。同列答案是两偏移差的绝对值减一。''',
    r'''移动的是整列，不是单艘舰船；直接给每个成员改位置会重复搬动大量对象。列内已有的两舰距离在整体移动后不变，适合维护相对坐标。

offset[x] 定义为位置 x 减去父亲位置，路径压缩后累加为位置 x 减根位置。同一列两艘舰船的根相同，相减时根坐标抵消，故它们之间的舰船数是 abs(offset[i]−offset[j])−1。查询保证两舰不同；不同根则输出负一。

根不必是实际队首。为支持按大小合并，另存 head[root]，表示根到当前列队首的距离；size[root] 同时是列长和合并大小。初始根就是自身，head 为零、size 为一。

设 i 所在列的根为 A，j 所在列的根为 B。执行 M 后以 B 的原队首为零，B 的位置全部不变，A 的位置全部增加 size[B]。所以两根新位置之差为

$$\Delta=size[B]+head[A]-head[B].$$

若把 A 根挂到 B 根，offset[A]=Δ，B 仍为代表，head[B] 不变；若按大小选择反向挂接，则 offset[B]=−Δ，A 仍为代表，但它距新队首的距离要增加原 size[B]。两种方向最后都累加队伍长度。旧子树内部的相对差值不用修改，因为整体平移会同时作用于两端。

例如某列顺序为二、一、三，根是二；把它接到单舰四之后，实际顺序变成四、二、一、三。若仍以二为根，它距队首一格，四的相对偏移为负一。负偏移并非错误，它表示舰船位于代表之前；不能强行要求代表永远在队首。

根的实际位置与身份分开维护后，就能同时按大小合并和压缩路径，避免把固定“队首作根”的任意挂接误套双优化复杂度。参考程序计算 Δ 后才改 size，保证使用的仍是原 B 列长。''',
    r'''int commands;cin>>commands;Fleet groups(30000);
while(commands--){char type;int i,j;cin>>type>>i>>j;
    if(type=='M')groups.append(i,j);
    else{int a=groups.find(i),b=groups.find(j);if(a!=b)cout<<-1<<'\n';else cout<<abs(groups.offset[i]-groups.offset[j])-1<<'\n';}
}''',
    '移动整列；根可在队中，偏移可负；反向挂根要反号并更新 head；先算位移后改长度。',
    r'设舰船数 N=30000、命令数 T，时间 $O(N+T\alpha(N))$，空间 $O(N)$。',tags=['并查集'],lessons=D+['weighted-dsu'],
    declarations=r'''struct Fleet{
    vector<int>parent,size,offset,head;
    Fleet(int n):parent(n+1),size(n+1,1),offset(n+1),head(n+1){iota(parent.begin(),parent.end(),0);}
    int find(int x){if(parent[x]==x)return x;int old=parent[x];parent[x]=find(old);offset[x]+=offset[old];return parent[x];}
    void append(int i,int j){
        int a=find(i),b=find(j);if(a==b)return;
        int difference=size[b]+head[a]-head[b];
        if(size[a]<=size[b]){parent[a]=b;offset[a]=difference;size[b]+=size[a];}
        else{parent[b]=a;offset[b]=-difference;head[a]+=size[b];size[a]+=size[b];}
    }
};''')

add('P7073','后缀表达式建树，反向标记能改变根值的变量',
    '给出每变量恰出现一次的布尔后缀表达式。每次独立取反一个变量，询问表达式值；先前询问的取反不保留。',
    r'''用栈把后缀式建成表达式树，节点创建顺序保证孩子在父亲之前，可直接顺序求原值。再从根向下传递“单独翻转这个子式是否会改变根”的标记：非门总传递，与门只向另一孩子为一的方向传递，或门只向另一孩子为零的方向传递。查询输出原根值异或该变量的标记，无须修改或重算整树。''',
    r'''每个变量恰出现一次很关键。取反一个叶子时，它到根路径上的所有兄弟子树都保持原值，因此能逐层判断变化是否被遮住；若变量重复出现，兄弟子树也可能同时改变，这套传递便不再适用。

读后缀式时，变量创建叶子并入栈；非门弹一个孩子后创建父节点；与、或门先弹右孩子再弹左孩子，创建父节点并压回。最后栈中唯一节点就是根。孩子先于父亲创建，所以按节点下标递增即可求原值，避免深表达式递归溢栈。

标记 important[u] 表示只把 u 子式的结果取反是否能改变整式。根本身取反当然改变整式，先标记根。非门把输入取反会使输出取反，标记可向唯一孩子传递。

对与门，若另一孩子原值为零，当前孩子无论零或一，父值都为零，变化被遮住；另一孩子为一时，父值随当前孩子翻转。或门相反：另一孩子为一会遮住变化，为零才传递。父节点本来不重要时，其后代任何单独变化也不会通过这一路影响根，不再向下传递。

按下标递减处理父节点，保证标记先从父亲传给孩子。抵达叶子后，important 为一表示这次翻转根值，否则保持原值，所以每次答案为原根值与该标记异或。所有询问均独立，不修改原值数组。

表达式最多一百万字符，程序手动扫描 x 后的连续数字，运算符分别处理，空格跳过；不把 x10 当 x1 再接一个零。用动态数组保存节点与显式栈，空间随表达式长度增长。''',
    r'''string expression;getline(cin,expression);vector<Node>nodes;vector<int>stack,leaf(1);
for(size_t at=0;at<expression.size();){
    if(expression[at]==' '){++at;continue;}
    if(expression[at]=='x'){++at;int variable=0;while(at<expression.size()&&expression[at]>='0'&&expression[at]<='9')variable=variable*10+expression[at++]-'0';
        if((int)leaf.size()<=variable)leaf.resize(variable+1);leaf[variable]=(int)nodes.size();nodes.push_back({'v',-1,-1,variable});stack.push_back((int)nodes.size()-1);
    }else{char kind=expression[at++];int right=stack.back();stack.pop_back();int left=right;
        if(kind!='!'){left=stack.back();stack.pop_back();}nodes.push_back({kind,left,right,0});stack.push_back((int)nodes.size()-1);
    }
}
int n;cin>>n;vector<int>initial(n+1);for(int i=1;i<=n;++i)cin>>initial[i];
vector<int>value(nodes.size()),important(nodes.size());
for(size_t i=0;i<nodes.size();++i){auto u=nodes[i];if(u.kind=='v')value[i]=initial[u.variable];else if(u.kind=='!')value[i]=value[u.left]^1;else if(u.kind=='&')value[i]=value[u.left]&value[u.right];else value[i]=value[u.left]|value[u.right];}
int root=stack.back();important[root]=1;
for(int i=(int)nodes.size()-1;i>=0;--i)if(important[i]){auto u=nodes[i];if(u.kind=='!')important[u.left]=1;
    else if(u.kind=='&'){if(value[u.right])important[u.left]=1;if(value[u.left])important[u.right]=1;}
    else if(u.kind=='|'){if(!value[u.right])important[u.left]=1;if(!value[u.left])important[u.right]=1;}
}
int queries;cin>>queries;while(queries--){int variable;cin>>variable;cout<<(value[root]^important[leaf[variable]])<<'\n';}''',
    '只适用于变量恰出现一次；询问相互独立；遮挡取决于另一孩子原值；用显式栈避免深递归。',
    r'预处理 $O(|s|+n)$，每问 $O(1)$，总时间 $O(|s|+n+q)$，空间 $O(|s|+n)$。',tags=['树形 DP','栈'],lessons=A+['trees','queue-stack','strings','bitwise','structures'],declarations='struct Node{char kind;int left,right,variable;};')

add('UVA1395','枚举允许的最小边，从小到大连通后立即停止',
    '无向简单图中求生成树最大边权减最小边权的最小值；原图不连通输出负一，多组以两个零结束。[原站 PDF](https://onlinejudge.org/external/13/1395.pdf)。',
    r'''边按权排序。枚举起点 l，只使用 l 及其后的边，从小到大做 Kruskal，首次选够 n−1 条时记 w[r]−w[l]。固定下界时，首次连通给出最小可行上界；最优树的最小权必出现在某次枚举中，因此取最小即可。若某个后缀已经不能连通，更短后缀也不可能，可结束枚举。''',
    r'''本题优化边权跨度，并非边权和。三角形权值为一、五十、五十时，最小和树跨度四十九，而选两条五十的边跨度为零，才是目标最优。

先把全部边按权排序，固定下界边下标 l。从 l 起重新建立并查集，依次加入之后的边，成功合并一次增加选边数。第一次达到 n−1 条时，当前 r 就是这一后缀能连通全图的最早位置，因而给出最小上界。

为什么枚举不会漏最优树：设某棵最优树的最小、最大权是 L、R。枚举到权值 L 的第一条边时，该后缀仍包含这棵树全部边，扫描到不超过 R 的某个权值便一定连通，因此候选跨度不大于 R−L。反过来，每次连通检查都确实选出生成树，所以候选也不可能优于全局最优，最终相等。

无自环保证当前后缀第一条边会成功选入，故此时树的最小边确为 w[l]。相同权值可以任意排序，枚举到该权值的第一条边时已覆盖全部这些边。

若扫描完某后缀仍未连通，删掉更多前端边只会减少可用边，之后所有后缀都不可能连通，可直接跳出。n≤100、简单图 m≤4950，重建扫描的二次边数规模可以接受；无边时也应输出负一，不能把零答案当成没有找到树。''',
    r'''int n,m;while(cin>>n>>m&&(n||m)){vector<Edge>edges(m);for(auto &e:edges)cin>>e.u>>e.v>>e.weight;
    sort(edges.begin(),edges.end(),[](const Edge&a,const Edge&b){return a.weight<b.weight;});int answer=INT_MAX;
    for(int left=0;left<m;++left){DSU groups(n);int chosen=0;
        for(int right=left;right<m;++right)if(groups.merge(edges[right].u,edges[right].v)){
            if(++chosen==n-1){answer=min(answer,edges[right].weight-edges[left].weight);break;}
        }
        if(chosen<n-1)break;
    }
    cout<<(answer==INT_MAX?-1:answer)<<'\n';
}''',
    '最小跨度不是最小和；每个下界重新建组；零是合法答案；无树输出负一。',
    r'时间 $O(m\log m+mn+m^2\alpha(n))$，空间 $O(n+m)$。',tags=['生成树','并查集','枚举'],lessons=D+['graphs','sort','structures','lambda-local'],declarations=DSU+'\nstruct Edge{int u,v,weight;};')

add('P13308','只保留操作点，压缩子树区域后倒序恢复删边',
    '最多六十层的满二叉树按堆式编号，操作可删掉节点与父亲的边，重复删除或删根无效果；查询所在连通块大小，最后输出全部查询答案的异或。',
    r'''树无法展开。收集所有操作节点及根，按完整树的先序位置排序，用子树区间栈找到每个操作点最近的已收集祖先。一个压缩区域是该点完整子树扣掉其压缩孩子的完整子树，大小可直接用二的幂计算。区域内部没有可删边，始终连通。先按全部删除建立最终森林，再倒序把首次有效删除恢复为并查集合并，查询读区域质量。重复删除用计数，减到零才恢复。''',
    r'''整棵树可有接近二的六十次方个节点，不能建普通邻接表，也不必把每个操作点的所有祖先都加入。只收集曾被操作的节点及根：所有可能删除的边，其下端都已收集；所有查询位置也都已收集。

对收集点 u，找最近的另一个收集祖先作为压缩父亲。把 u 完整子树中，各压缩孩子的完整子树挖去，剩余点作为 u 的区域。这个区域仍连通：每个留下节点到 u 的祖先路径也留下。所有区域互不相交且覆盖全树，区域之间恰对应压缩孩子与其实际父节点的那条原树边。

区域内部没有任何删除操作，因而始终可以整体看作一个加权点。其权值不是压缩路径长度，而是完整子树大小减去各压缩孩子完整子树大小，保留了未被操作的全部旁支。若节点深度为 d，其完整子树有

$$2^{n-d+1}-1$$

个点。每条压缩父子关系只减一次，子树之间不重叠。

最近收集祖先可用完整树先序区间找出。根先序位置为一，向左孩子走一步，先序位置加一；走右孩子时要跳过整棵左子树，位置增加相应的二的幂。每个节点最多六十位，可直接算位置与子树大小。按先序排序后，用栈弹出已经结束的子树区间，栈顶就是最近收集祖先。这是在压缩连通区域，不是计算任意两点距离的常规虚树，所以无须补入未操作的分叉祖先；那些祖先已保留在某个连通区域里。

普通并查集不能删边，但可以倒序加边。统计每个非根操作点被删除的次数，先仅连接删除计数为零的区域边，得到最终森林。倒序遇查询，读该点代表根上的区域权值和；遇删除，把计数减一，只有变成零时才恢复边。这样重复删除在逆序中不会提前恢复，根操作始终忽略。

查询点属于以自身为代表起点的区域，读并查集质量即可。所有质量之和不超过原树点数，使用 unsigned long long；n≤60，移位仍在其范围内。压缩查询索引用排序后的编号表二分查找，lambda 引用的表在处理全过程中保持存在且不修改。''',
    r'''int operations;cin>>levels>>operations;vector<Operation>op(operations);vector<Node>nodes={describe(1)};
for(auto &o:op){cin>>o.type>>o.node;nodes.push_back(describe(o.node));}
sort(nodes.begin(),nodes.end(),[](const Node&a,const Node&b){return a.begin<b.begin;});
nodes.erase(unique(nodes.begin(),nodes.end(),[](const Node&a,const Node&b){return a.id==b.id;}),nodes.end());
int count=(int)nodes.size();vector<pair<unsigned long long,int>>index;for(int i=0;i<count;++i)index.push_back({nodes[i].id,i});sort(index.begin(),index.end());
auto index_of=[&](unsigned long long u){return lower_bound(index.begin(),index.end(),make_pair(u,-1))->second;};
vector<int>parent(count,-1),stack={0},deleted(count);vector<unsigned long long>mass(count);
for(int i=0;i<count;++i)mass[i]=nodes[i].subtree;
for(int i=1;i<count;++i){
    while(nodes[i].begin>=nodes[stack.back()].begin+nodes[stack.back()].subtree)stack.pop_back();
    parent[i]=stack.back();mass[parent[i]]-=nodes[i].subtree;stack.push_back(i);
}
for(auto &o:op){o.index=index_of(o.node);if(o.type==1&&o.index!=0)++deleted[o.index];}
RegionDSU groups(mass);for(int i=1;i<count;++i)if(deleted[i]==0)groups.merge(i,parent[i]);
unsigned long long answer=0;
for(int i=operations-1;i>=0;--i){int u=op[i].index;
    if(op[i].type==2)answer^=groups.mass[groups.find(u)];
    else if(u!=0&&--deleted[u]==0)groups.merge(u,parent[u]);
}
cout<<answer<<'\n';''',
    '区域权值包含全部未操作旁支；重复删边计数归零才恢复；根删除无效果；质量不是压缩节点个数。',
    r'每个操作点计算先序位置 $O(n)$，排序和查询映射 $O(m\log m)$，合并摊还 $O(m\alpha(m))$；总时间 $O(mn+m\log m)$，空间 $O(m)$。',tags=['并查集','图论'],lessons=D+['trees','subtree-regions','unsigned64','structures','sort','bounds','iterators','lambda-local'],
    declarations=r'''int levels;
struct Node{unsigned long long id,begin,subtree;};
struct Operation{int type;unsigned long long node;int index;};
Node describe(unsigned long long u){
    int depth=0;for(auto x=u;x;x>>=1)++depth;unsigned long long begin=1;
    for(int level=2;level<=depth;++level)begin+=((u>>(depth-level))&1ULL)?(1ULL<<(levels-level+1)):1ULL;
    return {u,begin,(1ULL<<(levels-depth+1))-1};
}
struct RegionDSU{
    vector<int>parent,size;vector<unsigned long long>mass;
    RegionDSU(const vector<unsigned long long>&weights):parent(weights.size()),size(weights.size(),1),mass(weights){iota(parent.begin(),parent.end(),0);}
    int find(int x){return parent[x]==x?x:parent[x]=find(parent[x]);}
    void merge(int a,int b){a=find(a);b=find(b);if(a==b)return;if(size[a]<size[b])swap(a,b);parent[b]=a;size[a]+=size[b];mass[a]+=mass[b];}
};''')
