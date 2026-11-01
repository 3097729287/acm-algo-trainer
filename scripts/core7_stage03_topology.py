"""Dependencies, directed paths, cycles and condensation in the third unit."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
G=A+['graphs','queue-stack','topology']

add('B3644','每次列出没有未列出长辈的人',
    '给出每个人的后代编号，以零结束一行。输出所有人的一种排列，使每条已知长辈关系中，长辈都在后辈之前；可以输出任意合法顺序。',
    r'''把长辈到后辈连成有向边，入度记录尚未列出的直接前驱数。先将所有入度为零的人加入队列；取出一个人输出，并将其所有后继的入度减一，减到零才入队。每个人输出时全部前驱已经输出，故顺序合法。不同的可选人之间无需再按辈数比较。''',
    r'''关系表示谁必须先出现，不能仅根据编号排序。比如一号与二号都必须在三号前，三号又必须在四号前，开始可以列出一号、二号以及没有关系的五号；但只列出一号还不能解锁三号。

将每条关系 u→v 保存为邻接表，并给 indegree[v] 加一。这里的入度在算法过程中会变化：它表示还没输出的前驱数量。把所有初始零入度顶点入队，反复取队首加入答案。随后沿 u 的每条出边给后继减一次入度，恰好减到零的后继才能入队。

每次取出的点都没有未处理前驱，所以不会违反任何一条关系。输出后删除它的影响，剩余问题仍是同样的要求。无环依赖图只要还有点，就一定有零入度点；否则不断找一个前驱会重复顶点，形成环。因此队列最终能列出全部人。

队列只负责选择一种合法顺序，不保证字典序最小，而题目也没有这个要求。一行的零只是输入终止标志，不是顶点。孤立的人同样需要输出。''',
    r'''int n;cin>>n;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);
for(int u=1;u<=n;++u){int v;while(cin>>v&&v){graph[u].push_back(v);++indegree[v];}}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();cout<<u<<' ';
    for(int v:graph[u])if(--indegree[v]==0)ready.push(v);
}cout<<'\n';''',
    '边从长辈指向后辈；所有零入度点都入队；零不建边；答案不必与样例排列相同。',
    r'关系数为 m，时间与空间均为 $O(n+m)$。',tags=['拓扑排序'],lessons=G,checker='family_order')

add('P1113','输入顺序已满足依赖，直接计算最早完成时间',
    '工人数量足够，无依赖的杂务可以并行。每项杂务的所有准备工作完成后才能开始；准备工作的编号严格较小，输入按编号递增。求全部工作的最早完成时刻。',
    r'''令 finish[u] 为杂务 u 的最早完成时刻。它最早在全部准备工作完成时开始，即这些 finish 的最大值，再加自身耗时。无准备工作时最大值为零。题目已按依赖顺序输入，可以读一项算一项，无需额外拓扑排序。答案是所有 finish 的最大值。''',
    r'''一项工作若有两个准备工作，分别在第五、第八分钟完成，就必须等到第八分钟；它们可以同时进行，不能把五与八相加。若本项耗时三分钟，其最早完成时刻为十一。

finish[u] 表示已经完成包括 u 本身在内的全部必要工作的最早时刻。读到 u 的前驱列表时，对每个前驱 v 读取已经算好的 finish[v]，取最大值 wait。所有前驱都在 wait 时刻之前结束，u 便可以立即开始，得到 finish[u]=wait+duration。没有前驱时 wait=0。

这既是必要下界，也是可实现的时间：任何安排都必须等待最慢的准备工作；另一方面，足够多的工人允许所有前驱及无关任务并行，所以在所有依赖满足时立刻开工不会争抢人手。对编号从小到大归纳即可。

编号较小这一保证很关键，它使输入本身就是一种拓扑顺序。一般任务系统不能直接按编号计算，需先建立依赖图、再按拓扑顺序转移。本题只保留每项完成时间即可。

最后要取所有任务完成时间的最大值。编号最大不代表最晚结束，可能某项没有后继的早编号任务耗时更长。输入中的工作编号要实际读取，不要把它当成耗时。''',
    r'''int n;cin>>n;vector<long long>finish(n+1);long long answer=0;
for(int i=0;i<n;++i){int u,duration;cin>>u>>duration;int v;long long wait=0;
    while(cin>>v&&v)wait=max(wait,finish[v]);
    finish[u]=wait+duration;answer=max(answer,finish[u]);
}cout<<answer<<'\n';''',
    '并行前驱取最大值，不求和；全部任务的最晚完成时刻不一定属于编号最大的任务；无依赖时从零开始。',
    r'准备关系总数为 m，时间 $O(n+m)$，空间 $O(n)$。',tags=['拓扑排序','线性 DP'],lessons=A+['dp'])

add('P1137','拓扑顺序中取最长路径，所有城市都允许作起点',
    '道路只允许从西面的城市走向东面的城市。对每个城市，求以它为终点的一条路线最多经过多少个城市，起点可自由选择。',
    r'''将每条道路从西向东建边，严格向东保证没有环。初始 best[u]=1，表示只游览 u 本身；拓扑取出 u 后，沿边 u→v 更新 best[v]=max(best[v],best[u]+1)。等 v 的全部前驱处理完，它的最长路线已确定。不能只从一号城市出发。''',
    r'''题目询问每个终点，并允许任意起点，因此任何城市最少都能单独组成一条含一个城市的路线。将 best 的初值全部设为一，不把未从一号到达的点当作无效。

道路 u→v 表示可以在游览完 u 后再到 v。这种接法把以 u 结尾的最佳路线延长一个城市，候选长度为 best[u]+1。v 可能有多个前驱，取所有候选的最大值；这些路线是不同选择，不能把城市数相加。

严格向东使道路图为 DAG。用入度队列取得拓扑顺序，处理 u 时它的所有前驱已经完成，故 best[u] 已经是最终答案，可以安全地向后传递。即使某条道路跨过很多城市，也只增加实际到达的这个终点，不能按编号差增加。

例如一到二、一到三、二到四、三到四，四号的最佳长度是三，而不是把两条支路中的四个城市都相加。若另有五到六，则六号也能从五号出发得到长度二，与一号是否可达无关。

道路编号与东西位置没有给出一致关系，必须沿输入方向建边，不能自行把较小编号放在前面。最后按城市编号逐行输出 best。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1),best(n+1,1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:graph[u]){
    best[v]=max(best[v],best[u]+1);if(--indegree[v]==0)ready.push(v);
}}for(int u=1;u<=n;++u)cout<<best[u]<<'\n';''',
    '所有点初始化为一；对多条候选路线取最大值；不是固定从一号出发；道路按给定方向建边。',
    r'时间与空间均为 $O(n+m)$。',tags=['拓扑排序','线性 DP'],lessons=G+['dp'])

add('P1960','零入度候选超过一个，就存在另一种合法排名',
    '已知部分球队之间的胜负，强队排名必须更靠前。输出一种符合结果的完整排名，并输出是否还存在另一种排名；题目没有要求排名字典序最小。',
    r'''从胜者向败者建边，进行拓扑排序。若某次选择时零入度队列里至少有两个点，则它们都能放在当前位置，可以得到不同排名，标记为一。若每次都只有一个选择，完整顺序被逐位强制，标记为零。始终输出所取得的一种合法顺序。''',
    r'''一条 X 战胜 Y 的结果要求 X 出现在 Y 前面，间接胜负也会通过有向路径施加同样约束。拓扑排序正好列出满足这些前后关系的排列。

检查唯一性时，要在取出当前点之前看 ready 的大小。若当前有 u、v 两个零入度点，它们之间不可能存在有向路径：若有 u 到 v 的路径，v 至少还在等待该路径的最后一个前驱。于是先取 u 或先取 v 都不会违反依赖，剩余无环图仍可排完，得到两种不同排名。

反之，假设每一步都只有一个零入度点。任何合法排名的第一名都必须零入度，因此只能选这个点；删除后第二名也被同样强制。逐位归纳，整个排名只有这一种。

发现某一步不唯一后，仍继续完成拓扑过程，不能只输出标记而漏掉排名。重复比赛关系如被重复输入，邻接记录与入度也都按同样次数处理，仍能正确减到零。合法排名输入的依赖不会自相矛盾；若把方法用于一般资料，应另外检查最终是否取满 n 个点来发现矛盾环。

最终前 n 行各输出一个球队编号，最后一行输出零或一。队列里的编号次序只决定采用哪一个合法答案，不影响唯一性判断。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1),order;
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);bool multiple=false;
while(!ready.empty()){if(ready.size()>1)multiple=true;int u=ready.front();ready.pop();order.push_back(u);
    for(int v:graph[u])if(--indegree[v]==0)ready.push(v);
}for(int u:order)cout<<u<<'\n';cout<<multiple<<'\n';''',
    '在取点前统计选择数；有多个选择只说明排名不唯一，仍须输出一种排名；输出一表示存在其它排名。',
    r'时间与空间均为 $O(n+m)$。',tags=['拓扑排序'],lessons=G,checker='ranking_order')

add('P2419','传递闭包确定谁比谁强，再检查与所有人的关系',
    '胜负始终由不同的真实实力决定，资料没有矛盾。根据部分比赛结果，统计具体名次已经可以唯一确定的奶牛数量。',
    r'''用 reach[u][v] 表示已知 u 强于 v。对每个中转点 k，若 u 能到 k、k 能到 v，就补上 u 能到 v。完成 Floyd 传递闭包后，若对一头牛 u，其余每头牛 v 都满足 reach[u][v] 或 reach[v][u]，则 u 的名次确定。只数直接比赛会漏掉间接胜负。''',
    r'''若 A 赢 B、B 赢 C，实力严格排名就保证 A 也强于 C，即使两者没有直接比赛。需要先补齐全部可以推出的大小关系。

reach[u][v] 只表示“能根据资料确定 u 比 v 强”，不是任意猜测的真实胜负。初始化已给比赛后，按 k、u、v 三层循环：如果 u 强于 k 且 k 强于 v，就知道 u 强于 v。k 逐个加入允许经过的中转点，最终涵盖任意长度的关系链。

对于固定 u，若每个其它顶点与它都有已知大小关系，那么比 u 强的数量固定，它的名次就是这个数量加一。其它牛之间即便仍无法排序，也不会改变它们在 u 上面还是下面。

为什么只要还有不可比较对象，u 的名次就不能确定？把必在 u 前的祖先先排好；可以立刻放 u，得到最早位置。也可以先把所有不是 u 后继的点排完再放 u，得到最晚位置：不存在从后继指回这些点的边，否则它们也会成为后继。两种位置相差不可比较点的数量。因此至少一个不可比较点就带来不同名次。

图无矛盾环，所以一对不同奶牛不会同时互相可达。程序检查所有 v≠u，不把 u 自己算作一个已比较对象。n 不超过一百，三次方的传递闭包足够。''',
    r'''int n,m;cin>>n>>m;vector<vector<bool>>reach(n+1,vector<bool>(n+1));
for(int i=0;i<m;++i){int u,v;cin>>u>>v;reach[u][v]=true;}
for(int k=1;k<=n;++k)for(int u=1;u<=n;++u)if(reach[u][k])
    for(int v=1;v<=n;++v)reach[u][v]=reach[u][v]||reach[k][v];
int answer=0;for(int u=1;u<=n;++u){bool fixed=true;for(int v=1;v<=n;++v)if(v!=u&&!reach[u][v]&&!reach[v][u])fixed=false;if(fixed)++answer;}
cout<<answer<<'\n';''',
    'Floyd 的中转点循环放最外层；统计可推导的全部关系；一个人的名次确定不要求全体排名唯一。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['图论'],lessons=A+['graphs'])

add('P2712','只在实际摄像头之间统计监视依赖',
    '摄像头和普通位置共用编号。一个摄像头只有在没有其它仍存在的摄像头监视时才能砸毁。判断能否全部砸毁，否则输出剩余的实际摄像头数量。',
    r'''先读完全部摄像头位置，标记哪些位置确实有摄像头。摄像头 x 监视实际摄像头 y 时建边 x→y，普通位置不建依赖，自己监视自己也不算“其它摄像头”。不断砸掉零入度摄像头并撤去它的监视。最终未被删除的摄像头数就是答案；为零则输出 YES。''',
    r'''监视到编号七的位置，并不代表七号位置就有摄像头。必须先读完所有记录，才能区分摄像头与普通地面；不能把每个 y 都当成待砸对象。

用编号零到五百的布尔数组 camera 标记实际摄像头，暂存每个摄像头监视的位置。第二遍只为两个实际摄像头建立依赖 x→y：只要 x 还存在，y 就不能砸。题意限定的是其它摄像头，x=y 的自我监视不妨碍砸毁。

入度是尚未砸毁、仍监视当前摄像头的数量。把零入度摄像头加入队列，取出时计作已砸，并给它所监视的其它实际摄像头减入度。某个位置减到零，表示最后一个阻碍刚刚消失，可以继续砸。

过程结束后，剩余摄像头若存在，每个都仍被某个剩余摄像头监视，已经没有合法的第一步。它们不仅可能是环上的摄像头，还可能是一直被环监视的后继；这些后继同样要计入剩余数量。普通位置永远不计数。

选择哪个可砸摄像头不会让别的摄像头重新受到监视，因为动作只会撤销监视。因此贪心地砸掉全部当前可砸对象，能够砸掉所有可以通过合法过程消除的对象。输出要区分成功的 YES 与失败时的数字。''',
    r'''int n;cin>>n;vector<int>positions;vector<vector<int>>watched(501),graph(501);vector<int>camera(501),indegree(501);
for(int i=0;i<n;++i){int x,m;cin>>x>>m;camera[x]=1;positions.push_back(x);while(m--){int y;cin>>y;watched[x].push_back(y);}}
for(int x:positions)for(int y:watched[x])if(x!=y&&camera[y]){graph[x].push_back(y);++indegree[y];}
queue<int>ready;for(int x:positions)if(!indegree[x])ready.push(x);int removed=0;
while(!ready.empty()){int x=ready.front();ready.pop();++removed;for(int y:graph[x])if(--indegree[y]==0)ready.push(y);}
if(removed==n)cout<<"YES\n";else cout<<n-removed<<'\n';''',
    '普通位置不产生依赖；先读完摄像头身份再建边；忽略自己的监视；环的受阻后继也计入剩余数量。',
    r'监视记录总数为 L，编号范围为 V=501，时间与空间均为 $O(V+n+L)$。',tags=['拓扑排序'],lessons=G)

add('P3183','从生产者累加路径数，排除孤立物种',
    '有向边表示能量从被捕食者流向捕食者。统计从无入边物种到无出边物种的完整食物链数量，单独的孤立物种不算一条链；答案保证不超过 int。',
    r'''所有入度零点的 ways 初值为一，代表从这个生产者出发的一个起点。按拓扑顺序沿每条边 u→v 累加 ways[v]+=ways[u]。最后只对出度零且原入度非零的点求和，从而排除孤立物种。不同最后一条边对应不同路径，直接相加不会重复。''',
    r'''一条完整食物链必须从没有更低层食物来源的生产者开始，在没有更高层捕食者的物种结束。问题数的是路径条数，不是最长路径的长度，也不是物种数量。

令 ways[v] 为从任意生产者走到 v 的路径数。每个无入边点初值为一，表示从它自身开始的一种路径前缀；其它点初值零。若最后一步是 u→v，那么到 u 的每条路径都恰好延长为一条到 v 的路径。

不同前驱对应不同最后一条边，得到的路径互不相同，故把所有 ways[u] 相加。数据符合食物网的无环性质，拓扑顺序保证 u 的全部路径都已累计完，再将它传给后继。不能只保留最后一个前驱的贡献，也不能在合流处取最大值。

最终将所有无出边顶点的 ways 相加。但是本题明确排除孤立物种：无入边且无出边的点虽然初值为一，却没有经过任何能量关系，不能进入答案。因此额外保存原始入度，在汇总时要求它大于零。处理过程中修改的 indegree 最终都会变成零，不能拿它判断是否孤立。

使用 long long 保存中间路径数，避免大量分支先合并时发生窄类型溢出；题目保证最终答案在 int 内，无需取模。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);vector<long long>ways(n+1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}vector<int>original=indegree;
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u]){ready.push(u);ways[u]=1;}
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:graph[u]){ways[v]+=ways[u];if(--indegree[v]==0)ready.push(v);}}
long long answer=0;for(int u=1;u<=n;++u)if(graph[u].empty()&&original[u])answer+=ways[u];cout<<answer<<'\n';''',
    '保存原始入度排除孤立点；数完整路径而非长度；合流要累加；不要擅自取模。',
    r'时间与空间均为 $O(n+m)$。',tags=['拓扑排序','线性 DP','组合计数'],lessons=G+['dp','counting'])

add('P4017','拓扑累计源点到汇点的路径数，每次加法取模',
    '在无环食物网中，统计从没有前驱的生产者到没有后继的消费者的完整路径数，模 80112002。“最大”指路径两端不能继续延长，不是只统计长度最大的路径。',
    r'''无入边点的 ways 设为一，其余为零。拓扑处理 u 时，沿每条边把 ways[u] 加给后继并取模，待其入度减到零再入队。答案是所有无出边点的 ways 之和并取模。本题按两端不可延长的定义计数，不沿用另一道食物链题额外排除孤立点的规则。''',
    r'''例如一到三、二到三、三到四，两条完整链分别是一三四和二三四，三号应收到两份路径前缀。这是计数问题，而“最大”说明不能再向左或向右延伸，并没有要求它们达到统一的最长长度。

令 ways[v] 为从任意无入边点到 v 的路径数量，只有起点初值为一。任意非起点路径都有唯一的倒数第二个点 u；删去最后边 u→v 后，恰好得到一条计入 ways[u] 的前缀。这构成不重不漏的分类，因而沿出边相加。

当 u 被拓扑队列取出，所有进入它的边都已经处理，它的 ways 已经完整。此时才向后继传播。只有走到无出边点的路径才是完整链，汇总这些点即可；不能把所有中间点也加进答案。

本题的定义只要求没有更早前驱和更晚后继。因此若输入含孤立物种，它自身也同时满足两端条件，初始的一个方案进入答案；不要把 P3183 明写的“孤立物种不算”移到本题。

每一次更新与最后汇总都取模。两个小于模数的数相加仍在 int 范围内，先加再模可行。取模仅改变保存的同余代表，不改变依赖图，也不会使一个有路径但模后为零的点不再处理。''',
    r'''const int MOD=80112002;int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1),ways(n+1);
for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u]){ready.push(u);ways[u]=1;}
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:graph[u]){ways[v]=(ways[v]+ways[u])%MOD;if(--indegree[v]==0)ready.push(v);}}
int answer=0;for(int u=1;u<=n;++u)if(graph[u].empty())answer=(answer+ways[u])%MOD;cout<<answer<<'\n';''',
    '最大链不是最长链；源点初值为一；每条边贡献都累加并取模；模后为零也正常参加拓扑处理。',
    r'时间与空间均为 $O(n+m)$。',tags=['拓扑排序','线性 DP','组合计数'],lessons=G+['dp','modular'])

add('P7113','拓扑传播精确分数，加法先求公分母再约分',
    '前 m 个接收口各有一吨污水，在无环管网中均分到每条出管。按编号输出每个最终排水口的最简分数。附件样例二、三未取得数据，实际原站样例验证只计可读取的第一组。',
    r'''用约分后的分数记录每个结点的水量。拓扑处理 u 时，将它的水量除以出度，并加到每个后继；水量为零也要正常消除其出边。分数相加先用分母最大公约数求最小公倍数，避免直接乘两个大分母。采用 __int128，最后按十进制逐位输出，零统一为 0/1。''',
    r'''水必须先在合流处收齐，再均分出去。例如样例中四号收到两份六分之一，最终为三分之一；五号收到三分之一和两份六分之一，最终为三分之二。若每到一份水就把结点永久标记完成，会丢掉后来的一份。

对每个点保存约分后的 p/q，初始为零比一，前 m 个点改为一比一。入度为零的点全部入队，包含没有接收到水的源点。取出 u 后，若有 d 条出管，它给每条管道的水为 p/(qd)，先约分，再分别加入后继。无出管点不做除法。

两个分数 p/q、r/s 相加时，令 g=gcd(q,s)，公分母为 q(s/g)，分子为 p(s/g)+r(q/g)。这里两项分别是把原来的两份水放到同一种小份单位后，各占多少份。得到新分数后再约分。直接算 qs 会产生完全可以提前消掉的公因子。

为什么数值需要宽整数而仍有上界？一条水路最多经过十个中间点，即最多十一条均分边。每个分流数在一到五之间，只含质因子二、三、五；每步最多给二贡献两次幂，给三或五贡献一次幂。因此每条路径的分母都整除 60 的十一次方，约分后汇总分母也整除它。这个公共上界约为 3.63×10^19，已经超过常见有符号六十四位；总水量至多十吨，使用有符号一百二十八位足够。

上述先求公分母的加法，产生的是这些分母的最小公倍数，仍在同一上界内，不会先乘成两个上界的平方。零分数约为零比一。__int128 是 GCC 扩展，标准流没有直接输出重载，程序自写逐位输出；输入与结点编号仍用普通整数。

原缓存另外两组只写“见附件”，没有伪造为可运行样例；独立校验用精确有理数直接枚举水路，另覆盖深度和大分母。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);vector<Fraction>water(n+1);
for(int u=1;u<=n;++u){int d;cin>>d;while(d--){int v;cin>>v;graph[u].push_back(v);++indegree[v];}}
for(int u=1;u<=m;++u)water[u].p=1;
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();if(graph[u].empty())continue;
    Fraction part{water[u].p,water[u].q*int(graph[u].size())};part.reduce();
    for(int v:graph[u]){water[v].add(part);if(--indegree[v]==0)ready.push(v);}
}for(int u=1;u<=n;++u)if(graph[u].empty()){print128(water[u].p);cout<<' ';print128(water[u].q);cout<<'\n';}''',
    '不使用浮点近似；分数加法先消公因子；无水结点也消除入度；无出边不均分；输出所有排水口，包括零比一。',
    r'设管道数为 e、数值上界为 B，拓扑遍历 $O(n+e)$，每条边另有 $O(\log B)$ 次欧几里得步骤；固定一百二十八位算术下总时间 $O((n+e)\log B)$，空间 $O(n+e)$。',
    tags=['拓扑排序','最大公约数'],lessons=G+['number-theory'],
    declarations=r'''using i128=__int128;
i128 gcd128(i128 a,i128 b){while(b){i128 r=a%b;a=b;b=r;}return a;}
struct Fraction{
    i128 p=0,q=1;
    void reduce(){i128 g=gcd128(p,q);p/=g;q/=g;}
    void add(const Fraction &other){i128 g=gcd128(q,other.q);p=p*(other.q/g)+other.p*(q/g);q=q*(other.q/g);reduce();}
};
void print128(i128 value){if(value==0){cout<<0;return;}string s;while(value){s.push_back(char('0'+value%10));value/=10;}reverse(s.begin(),s.end());cout<<s;}''')

add('P10166','已有环则为零，否则比较补一条边与补两条边',
    '无自环、无重边的有向图中，补 i→j 的代价为 a[i]+a[j]，权值为正。求形成至少两个不同顶点的有向环所需的最小代价。',
    r'''先用拓扑排序判环，原图有环直接输出零。若无环，补一条边成环恰对应原图中存在一条反向路径；拓扑传播每个点所有严格祖先的最小权值，求最小的祖先与当前点权值和。还要比较两点间补双向边的方案，代价为两项最小点权之和的两倍，孤立的便宜点也可能使它更优。''',
    r'''若原图已经有有向环，不需要花钱。否则所有原边构成 DAG，可以按拓扑顺序处理。形成新环可能需要一条或多条新边，不能默认最优方案只补一条。

先看恰补一条 v→u：它能闭合成环，当且仅当原图已有从 u 到 v 的非空路径。费用只由两个端点决定，与路径上其它点的权值无关。令 ancestor[v] 为能沿非空原路径到达 v 的点中，最小的点权；初始为无穷。处理边 u→v 时，将 min(ancestor[u],a[u]) 传给 ancestor[v]。这里既包括 u 的更早祖先，也包括 u 本身，恰好覆盖全部严格祖先。以 a[v]+ancestor[v] 更新补一边答案。

例如权值三、一百、四组成一到二到三的路径，只需补三到一，费用为七。不能只枚举原图中已有一条直接边的两端，否则会漏掉这一跨多条边的便宜闭环。

再看至少补两条边。设全图最小的两个不同顶点权值为 b、c。选这两个点补成二元环，费用至多 2(b+c)；若其中某条方向本就存在，只补另一条会更便宜，并已被上一类覆盖。

任何含至少两条新边的简单环，其新边端点总共出现至少四次，同一顶点在这些端点中最多出现两次。权值为正，四次端点费用至少为两个最便宜不同顶点各出现两次，即 2(b+c)；更多新边不会降低这个下界。因此比较“一条新边”与“两便宜点双向连接”的费用，就涵盖所有最优情况。

孤立便宜点不能被祖先传播发现，却仍可互相补边，所以第二类不能省略。拓扑最终没取满 n 个点时已有环，优先输出零。费用可能超过 int，使用 long long。''',
    r'''int n,m;cin>>n>>m;vector<long long>weight(n+1),ancestor(n+1,LLONG_MAX/4);
long long first=LLONG_MAX/4,second=LLONG_MAX/4;
for(int u=1;u<=n;++u){cin>>weight[u];if(weight[u]<first){second=first;first=weight[u];}else second=min(second,weight[u]);}
vector<vector<int>>graph(n+1);vector<int>indegree(n+1);for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);int removed=0;long long answer=2*(first+second);
while(!ready.empty()){int u=ready.front();ready.pop();++removed;answer=min(answer,weight[u]+ancestor[u]);
    for(int v:graph[u]){ancestor[v]=min(ancestor[v],min(ancestor[u],weight[u]));if(--indegree[v]==0)ready.push(v);}
}cout<<(removed<n?0:answer)<<'\n';''',
    '两个最小权值来自不同顶点；祖先路径必须非空；不能只比较一条现有边；有环直接为零；保留补两条边的候选。',
    r'时间与空间均为 $O(n+m)$。',tags=['拓扑排序','贪心'],lessons=G+['greedy'])

add('UVA10305','按前置任务入度排出一种合法执行顺序',
    '多组任务，每条 i、j 关系要求 i 先于 j。每组输出一种符合全部前置关系的任务顺序；读到 n=m=0 结束。原站 PDF 核对了多组与终止格式。',
    r'''建立 i→j 的依赖边，所有无前驱任务入队。取出一个任务，将其后继的剩余入度减一，减到零的后继入队。每个任务取出时所有前驱已执行，因此得到合法顺序。多种答案都允许，不要按样例唯一文本比较，也不用求字典序最小。''',
    r'''把任务当成顶点，i 必须先于 j 就保存有向边 i→j。一个任务只有在全部前驱已执行后才可进行，因而入度记录它还在等待的前置关系数量。

初始将所有零入度点入队。每次取出 u 输出，沿它的出边逐一给后继减入度。只有恰好减到零的点可以加入队列；只要还有一个前驱没执行，它就继续等待。

按这个规则输出的每个顶点都满足前置条件；处理后剩余任务依然是相同类型的依赖问题。在可执行的依赖图中，过程最终取满 n 个任务。题目只要求一种执行顺序，互不约束的任务可以任选先后。

原站 [Ordering Tasks PDF](https://onlinejudge.org/external/103/10305.pdf) 明确给出多组输入与双零终止。每次读到 n、m 后先判断终止，再为本组新建邻接表和入度。某组 m=0 但 n 非零时仍有任务，必须完整输出，不能把“没有依赖”误认为输入结束。

每组答案占一行。一般工程中还应检查最终输出长度来报告依赖环；本题的输出形式要求给出可执行顺序，没有另设失败标记。''',
    r'''int n,m;while(cin>>n>>m&&(n||m)){vector<vector<int>>graph(n+1);vector<int>indegree(n+1);
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);++indegree[v];}
    queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
    while(!ready.empty()){int u=ready.front();ready.pop();cout<<u<<' ';for(int v:graph[u])if(--indegree[v]==0)ready.push(v);}
    cout<<'\n';
}''',
    '终止条件是两个数都为零；每组重新初始化；输出任意合法排列；不增加题目没有要求的最小字典序目标。',
    r'每组时间与空间均为 $O(n+m)$。',tags=['拓扑排序'],lessons=G,checker='task_order')

add('CF1361A','按期望主题递增写作，并检查每个较小主题都在邻居中出现',
    '写一篇博客时，它的主题自动取为已写邻居中没有出现的最小正整数。给出无向引用图及每篇博客期望主题，构造写作顺序，无法实现则输出负一。',
    r'''期望主题为 t 的点必须有主题 1 到 t−1 的邻居，且不能有同主题邻居。这两条也是充分条件：按主题递增写，所有较小主题邻居已写，大主题未写，同主题之间没有边，得到的最小缺失正整数恰为 t。用时间戳数组统计不同的较小主题，重复邻居主题只计一次。''',
    r'''若一篇博客想得到主题三，已经写好的邻居必须覆盖一和二，同时不能覆盖三。主题一出现很多次也不能代替缺失的主题二。

先看必要条件：为了产生 t，邻居中必须能提供每一种较小主题。若存在一条同主题的边，无论两端谁后写，后者都会看到前者的相同主题，无法再选它，因此直接无解。

只要这两条都满足，按期望主题从小到大处理所有点即可。对当前点 u，小主题邻居全已写，大主题邻居全未写；同主题点虽可能已有部分写好，但彼此没有边，不影响 u。于是它已经看到恰好覆盖一到 t−1 的主题，且尚未看到 t，自动选择的就是 t。

实现时 sort 使用捕获 topic 的 lambda，定义与调用都在 main 中、topic 仍存活，按值读每个顶点的期望主题来比较。相同主题按顶点编号打破平局只是让输出稳定，不是正确性要求。

检查 u 的邻居时，使用 seen[topic[v]]==u 表示“这一轮已经统计过该主题”。顶点编号从一开始，因此数组初始零不会与本轮标记混淆。只统计严格小于 topic[u] 的不同主题，若数量等于 topic[u]−1，便覆盖了整个所需范围；同主题边另外拒绝。每条边只被检查两次，无需为每个顶点清空长度 n 的数组。

输出顺序不是按顶点编号递增，也不能只检查邻居数量是否够多；邻居主题的不同取值才决定能否补齐。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>topic(n+1),order(n),seen(n+1);for(int u=1;u<=n;++u)cin>>topic[u];iota(order.begin(),order.end(),1);
sort(order.begin(),order.end(),[&](int u,int v){return topic[u]!=topic[v]?topic[u]<topic[v]:u<v;});
for(int u:order){int count=0;for(int v:graph[u]){
    if(topic[v]==topic[u]){cout<<-1<<'\n';return 0;}
    if(topic[v]<topic[u]&&seen[topic[v]]!=u){seen[topic[v]]=u;++count;}
}if(count!=topic[u]-1){cout<<-1<<'\n';return 0;}}
for(int u:order)cout<<u<<' ';cout<<'\n';''',
    '主题从一开始取 mex；同主题相邻必无解；较小主题去重后计数；不能只比较度数；顺序按主题而非编号。',
    r'排序 $O(n\log n)$，检查 $O(n+m)$，空间 $O(n+m)$。',tags=['贪心','排序'],lessons=A+['graphs','sort','lambda-local'],checker='blog_order')

add('P1038','等待全部前驱处理完，只有正状态沿出边传递',
    '分层有向神经网络中，输入层使用给定状态，其余结点汇总兴奋前驱的加权信号再减自身阈值。仅输出状态为正的输出层结点，按编号升序；没有则输出 NULL。',
    r'''读完所有边，用入度识别输入层：它们保留给定状态，不减阈值；其余点初值减去阈值。按拓扑顺序处理，只有状态为正才将状态乘边权加给后继，但无论是否兴奋，都消除其依赖。边权可到十的九次方，长链可能超出固定整数，参考代码用有符号十进制高精度做加法及乘小整数。''',
    r'''一个神经元必须收齐全部前驱的信号后，才能判断自己是否兴奋。提前收到一份正信号就传播，可能漏掉另一前驱随后传来的负权贡献。拓扑排序让判断发生在入度减到零之后。

先用原入度区分输入层和其余层。输入层状态已经给出，直接保留；非输入层最初状态为零，先减一次自身阈值，再累加各前驱的贡献。不能把“初始状态非零”当成输入层判据，因为输入层也可能为零或负。

处理 u 时，若当前状态大于零，就沿每条边加上 state[u]×weight。边权允许为负，可能抑制下游。若 u 不兴奋，它对所有后继贡献零，但它的处理仍然已经结束，必须照样消除每条出边的入度；否则下游会永远留在队列外。

不必模拟每一秒，因为本题只求分层网络最后的输出状态，拓扑依赖已经保证所有需要汇集的信号完整。最终只检查无出边的输出层，不把正状态的中间结点也输出。

按当前题面的边权范围，许多连续乘法可能超过 long long，甚至超过一百二十八位。参考代码将绝对值保存为十进制字符串，另存负号。相同符号相加就逐位相加；不同符号相加就用较大绝对值减较小绝对值，符号取较大者。零统一为非负，才能用“非负且不等于零”判断兴奋。

乘法只需要“大整数乘边权这个小整数”：从低位乘起，当前值等于本位数字乘乘数再加进位，个位留存，其余作为新进位。乘数绝对值不超过十的九次方，long long 足以保存单步的数字乘法和进位。输入状态与阈值也读为字符串，不另行假定未写出的窄整数上界。通用高精度基础讲义解释逐位保存与进位，下面的代码再实现符号处理。

例如两个输入分别贡献正五和负六、阈值为零，下游最后为负一，不能因为先看见五就提前向后传播。若所有输出都不兴奋，严格输出大写 NULL。''',
    r'''int n,m;cin>>n>>m;vector<Number>state(n+1),threshold(n+1);for(int u=1;u<=n;++u){string c,t;cin>>c>>t;state[u]=Number(c);threshold[u]=Number(t);}
vector<vector<pair<int,long long>>>graph(n+1);vector<int>indegree(n+1);
for(int i=0;i<m;++i){int u,v;long long w;cin>>u>>v>>w;graph[u].push_back({v,w});++indegree[v];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);else{threshold[u].negative=!threshold[u].negative;state[u]=plus_number(state[u],threshold[u]);}
while(!ready.empty()){int u=ready.front();ready.pop();for(auto [v,w]:graph[u]){
    if(!state[u].negative&&state[u].digits!="0")state[v]=plus_number(state[v],times_small(state[u],w));
    if(--indegree[v]==0)ready.push(v);
}}
bool any=false;for(int u=1;u<=n;++u)if(graph[u].empty()&&!state[u].negative&&state[u].digits!="0"){cout<<u<<' '<<state[u].digits<<'\n';any=true;}if(!any)cout<<"NULL\n";''',
    '输入层不减阈值；负权允许；不兴奋也要消入度；等待全部前驱；只输出正状态汇点；固定整数不保证容纳连续乘积。',
    r'拓扑遍历 $O(n+p)$。设所有中间值最多 D 个十进制位，所用加法、减法与乘小整数均为 $O(D)$，计算时间 $O((n+p)D)$，空间 $O(n+p+nD)$。',
    tags=['拓扑排序','高精度'],lessons=G+['big-integers','strings','string-tools','structures'],
    declarations=r'''struct Number{
    string digits="0";bool negative=false;
    Number()=default;
    Number(string s){if(!s.empty()&&(s[0]=='-'||s[0]=='+')){negative=s[0]=='-';s.erase(s.begin());}
        size_t first=s.find_first_not_of('0');digits=first==string::npos?"0":s.substr(first);if(digits=="0")negative=false;}
};
int absolute_compare(const string &a,const string &b){if(a.size()!=b.size())return a.size()<b.size()?-1:1;return a==b?0:(a<b?-1:1);}
string absolute_add(const string &a,const string &b){string s;int i=int(a.size())-1,j=int(b.size())-1,carry=0;
    while(i>=0||j>=0||carry){int value=carry;if(i>=0)value+=a[i--]-'0';if(j>=0)value+=b[j--]-'0';s.push_back(char('0'+value%10));carry=value/10;}
    reverse(s.begin(),s.end());return s;}
// 前提：a 的绝对值不小于 b。
string absolute_subtract(const string &a,const string &b){string s;int j=int(b.size())-1,borrow=0;
    for(int i=int(a.size())-1;i>=0;--i){int value=a[i]-'0'-borrow-(j>=0?b[j--]-'0':0);borrow=value<0;if(borrow)value+=10;s.push_back(char('0'+value));}
    while(s.size()>1&&s.back()=='0')s.pop_back();reverse(s.begin(),s.end());return s;}
Number plus_number(Number a,Number b){Number result;if(a.negative==b.negative){result.digits=absolute_add(a.digits,b.digits);result.negative=a.negative;}
    else{if(absolute_compare(a.digits,b.digits)<0)swap(a,b);result.digits=absolute_subtract(a.digits,b.digits);result.negative=a.negative;}
    if(result.digits=="0")result.negative=false;return result;}
Number times_small(Number a,long long multiplier){Number result;if(!multiplier||a.digits=="0")return result;
    result.negative=a.negative^(multiplier<0);if(multiplier<0)multiplier=-multiplier;long long carry=0;string s;
    for(int i=int(a.digits.size())-1;i>=0;--i){long long value=(a.digits[i]-'0')*multiplier+carry;s.push_back(char('0'+value%10));carry=value/10;}
    while(carry){s.push_back(char('0'+carry%10));carry/=10;}reverse(s.begin(),s.end());result.digits=s;return result;}''')

add('P3243','从结尾安排当前可做终点的最大编号，再反转',
    '约束 x 必须先于 y；优先让一号的位置最早，在此基础上让二号最早，再依次考虑。输出最优顺序，有环则输出 Impossible!。这个目标不同于直接最小化输出排列的字典序。',
    r'''从序列末尾向前填。当前能放在末尾的点是没有未安排后继的点，在其中选编号最大的点放到最后。用原图出度和反向邻接表维护候选，最大堆取点，最后反转所得序列。尽量把大编号放晚，才能优先改善小编号的位置；若未取满 n 个点则有环。''',
    r'''对限制三先于一，若正向总选当前最小编号，会先做二、再做三、一，令一号落在第三位。但三、一、二把一号放在第二位，按题意更优。所以不能套用“正向小根堆就是最优”的结论。

改为从后往前排。当前没有未安排后继的点，都可以作为剩余序列的末尾。选择其中最大的 v，并固定到当前最后一格。用最大堆保存这些点，取出后沿反向边删除它对前驱出度的影响；某前驱出度归零便成为新候选。

证明这一步安全：假设某个最优剩余顺序没有把 v 放在最后，末尾实际是另一个候选 w。由于 v 是最大候选，w<v。将 v 从原位置抽出，挪到末尾，其后的所有点向前移动一位。v 没有剩余后继，这样移动仍合法；除了 v 变晚，其余受影响点都更早，其中至少有 w 这个比 v 小的编号。因此最小的受影响编号一定得到改善，与原顺序最优矛盾。

固定这一格后，对剩余图重复同一论证，得到全部位置。题目比较的是每个编号各自出现的位置，按编号一、二、三依次优先；并不是直接比较输出排列的第一个数、第二个数。

输入允许重复限制，保存多少条反向边，就对应增加和减少多少次出度，不必为正确性强制去重。若队列空了仍有点未取出，剩余约束含环，输出规定的 Impossible!。每组数据独立初始化。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<vector<int>>previous(n+1);vector<int>outdegree(n+1),reversed;
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;previous[v].push_back(u);++outdegree[u];}
    priority_queue<int>ready;for(int u=1;u<=n;++u)if(!outdegree[u])ready.push(u);
    while(!ready.empty()){int u=ready.top();ready.pop();reversed.push_back(u);for(int v:previous[u])if(--outdegree[v]==0)ready.push(v);}
    if(int(reversed.size())!=n){cout<<"Impossible!\n";continue;}
    reverse(reversed.begin(),reversed.end());for(int u:reversed)cout<<u<<' ';cout<<'\n';
}''',
    '使用反向边与原出度；最大堆取当前汇点；最终反转；不是正向最小字典序；重复边增减次数一致；注意感叹号。',
    r'每组时间 $O(n\log n+m)$，空间 $O(n+m)$。',tags=['拓扑排序','贪心','堆'],lessons=G+['greedy','heap'])

add('P3627','强连通区域汇总现金，缩成 DAG 后求可达最大收益',
    '从指定起点沿单向路行走，可以重复经过点和边，但每个 ATM 的钱只能取一次。最后必须停在一个酒吧，求最多取得多少钱；钱数均非负。',
    r'''能互相到达的一组点可以全部取钱后再从任意出口离开，把它们缩为一个强连通分量，权值为区内现金之和。分量图无环，在其拓扑顺序中从起点分量做最大收益 DP。不可达初值为负一，答案只取有酒吧且可达的分量。用显式栈的两遍 DFS 求分量，避免五十万层递归。''',
    r'''环允许重复经过，不能直接把每条路都当成独立收益，也不能在原图上反复“松弛”现金，否则同一个 ATM 会被多次加钱。

把互相可达的顶点分为一组，称为强连通分量。若进入其中一个点，因为组内任意两点互通，就能依次走到所有 ATM，拿完非负现金，再走到想使用的出口或组内酒吧。允许重复路口，而现金只按顶点汇总一次，所以这一区域的收益恰好是现金总和。

求分量采用两遍 DFS。第一遍在原图中搜索，只有当顶点的所有出边都处理完，才将它加入完成顺序；第二遍按完成顺序的逆序，在反图中扩展并标记同组。为何反图不会把下一组也混入？对分量间原边 A→B，第一遍的最大完成时间满足 A 晚于 B；先处理 A 后，反图没有能从 A 走到尚未处理的 B 的通路。递次取完源分量，恰得到一个个强连通区域。

第一遍必须记录“完成”时间，不能把普通栈出栈顺序直接当作完成时间。代码用每个点的下一条待处理边下标模拟递归，深链也不占用系统调用栈。第二遍只需普通栈，发现时就标记，防止重复入栈。

将原边两端的分量编号不同者加入新图。新图若还有有向环，环上分量便能互相到达，本应是同一组，矛盾，所以新图是 DAG。重边可保留，入度与出边按同样次数处理即可。

令 best[c] 为从起点进入并拿完分量 c 后的最大现金。初始只有起点分量为其区内现金，其余为负一表示不可达。对分量边 c→d，用 best[c]+sum[d] 更新 best[d]，但只有 c 可达时才转移。全图零入度队列决定处理顺序，不能因为某组与起点无关就遗漏入度的消除。

最后只在酒吧所在分量取最大值。经过一个酒吧后可以继续走，所以不需要提前停止。路径不同的区域收益取最大值，不能把无法同时经过的两条支路总和相加。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>graph(n+1),reverse_graph(n+1);vector<pair<int,int>>edges(m);
for(auto &e:edges){cin>>e.first>>e.second;graph[e.first].push_back(e.second);reverse_graph[e.second].push_back(e.first);}
vector<long long>money(n+1);for(int u=1;u<=n;++u)cin>>money[u];int start,p;cin>>start>>p;vector<int>bars(p);for(int &u:bars)cin>>u;
vector<int>seen(n+1),next_edge(n+1),order,stack;
for(int root=1;root<=n;++root)if(!seen[root]){seen[root]=1;stack.push_back(root);
    while(!stack.empty()){int u=stack.back();if(next_edge[u]<int(graph[u].size())){int v=graph[u][next_edge[u]++];if(!seen[v]){seen[v]=1;stack.push_back(v);}}
        else{order.push_back(u);stack.pop_back();}}
}
vector<int>component(n+1);int count=0;vector<long long>sum(1);
for(int at=n-1;at>=0;--at){int root=order[at];if(component[root])continue;++count;sum.push_back(0);component[root]=count;stack.push_back(root);
    while(!stack.empty()){int u=stack.back();stack.pop_back();sum[count]+=money[u];for(int v:reverse_graph[u])if(!component[v]){component[v]=count;stack.push_back(v);}}
}
vector<vector<int>>dag(count+1);vector<int>indegree(count+1);for(auto [u,v]:edges)if(component[u]!=component[v]){dag[component[u]].push_back(component[v]);++indegree[component[v]];}
vector<long long>best(count+1,-1);best[component[start]]=sum[component[start]];queue<int>ready;for(int u=1;u<=count;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();for(int v:dag[u]){if(best[u]>=0)best[v]=max(best[v],best[u]+sum[v]);if(--indegree[v]==0)ready.push(v);}}
long long answer=0;for(int u:bars)answer=max(answer,best[component[u]]);cout<<answer<<'\n';''',
    '组内现金只加一次；第一遍记录完成时间；深图用显式栈；不可达与收益零区分；只在酒吧读最终答案。',
    r'两遍 DFS、缩图与 DP 的时间及空间均为 $O(n+m)$。',tags=['DFS','拓扑排序','线性 DP'],lessons=G+['dp','structures'])

add('P8269','剥掉入树，每个有向环只损失其中最小的访问收益',
    '每头牛按某个排列依次行动，只有想访问的伙伴尚未离开农场时才会出发并得到自己的收益；否则留在原地。每头牛恰有一个不同于自己的目标，收益非负，求最大总收益。',
    r'''先把所有牛的收益加起来。每个有向环至少有一头牛不能成功离开，否则环上的每头都必须比它的目标更早行动，矛盾。删掉环上最小收益的一条需求后，其余牛都可以成功。用入度队列剥去入树，剩余恰为若干环，遍历每环扣掉一个最小收益。''',
    r'''用 i→a[i] 表示 i 想访问的目标。每点只有一条出边，每个弱连通区域由一个有向环及指向环的入树组成。

假设一个环上的牛全部成功离开。对其中每条 i→a[i]，若 a[i] 在 i 之前成功离开，i 就访问失败，所以必须 i 比 a[i] 更早行动。沿环得到一连串严格早于关系，最后回到自己，不可能。因此每环至少损失一头牛的收益，且至少损失该环的最小收益。

这个下界能够达到。每个环选最小收益牛 r 作为失败者，暂时去掉它的出边，剩余需求图无环。按剩余图拓扑顺序让牛行动：任何非 r 的牛都在目标之前行动，目标还在家，访问成功。环上从 a[r] 沿剩余边最终能到 r，所以 a[r] 一定先离开，r 轮到时失败。入树上的牛也都在自己的目标之前成功，不需要额外舍弃。

因此答案是全部收益之和，减去每环的最小值。收益为零时优先损失它也符合公式，不要求所有收益严格为正。

找环无需逐点重新追到已见点。先统计入度，把入度零点反复删除，并给它唯一目标减入度。入树会从叶到根被剥完，环中每点始终保留至少一个环内前驱，最后留下的正入度点恰是环。逐环沿唯一出边走一圈，求最小值并将其标记为已处理。

总收益可到十的十四次方，必须用 long long。不是选一个全图最小值只减一次，互不相交的环各自都需要一个失败者。''',
    r'''int n;cin>>n;vector<int>to(n+1),indegree(n+1);vector<long long>value(n+1);long long answer=0;
for(int u=1;u<=n;++u){cin>>to[u]>>value[u];++indegree[to[u]];answer+=value[u];}
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();if(--indegree[to[u]]==0)ready.push(to[u]);}
for(int root=1;root<=n;++root)if(indegree[root]){long long least=LLONG_MAX;int u=root;while(indegree[u]){least=min(least,value[u]);indegree[u]=0;u=to[u];}answer-=least;}
cout<<answer<<'\n';''',
    '入树无需损失收益；每个环分别扣最小值；零收益合法；剥叶按入度；总和使用六十四位。',
    r'每个点至多剥离或绕环访问一次，时间与空间均为 $O(n)$。',tags=['拓扑排序','贪心'],lessons=G+['greedy'])

add('P11022','把仅由桥连接的顶点染同色，其它区域可以异色',
    '简单无向图要同时有黑白顶点，并让每对异色点之间至少存在两条不同简单路径。两条路径允许共享边和中间点；无法做到则输出负一。',
    r'''图不连通时无解。对连通图先找出桥，但只用桥边组成森林，取其中一个连通块全染黑，其余染白。若桥森林只有一个块，原图是树，无解。理由是两点间只有唯一简单路径，当且仅当它们由全是桥的路径连通；把这样的点染同色，所有异色对就自动有至少两条路径。''',
    r'''本题只要求路径不同，并未要求两条路径边不相交。三角形上再挂一条桥时，跨桥的两条路径完全可以共享这条桥，再从三角形的两侧分别通过。所以不能看到图有桥就直接输出无解，也不能误用“两条边不相交路径”的判据。

先判断连通性。若不同连通块中出现异色对，它们之间甚至没有路径。若全图已有黑点、白点，那么每个点必须与某个异色点相连，迫使所有点在同一个原连通块中。因此原图不连通必无解。

在连通图中，桥是删去后会让图断开的边。如果 u、v 之间存在一条只由桥组成的路径，这条路径上的每条边都不可绕开，而且路径不能离开后又回到同一个点，因此 u、v 的简单路径唯一，必须同色。

反过来，若 u、v 之间的某条简单路径含非桥边 e，那么 e 处在一个环中，删掉 e 后图仍连通，故 u、v 仍有一条路径；它不使用 e，与原路径不同。于是只有“桥森林中属于同一连通块”的点对会被唯一简单路径约束。

注意建的是只保留桥的图，而非删除桥后的图。把一个桥森林连通块染黑，其余染白，异色点不在同一桥森林块中，正好满足条件。若桥森林已覆盖全图，全部原边都是桥，原图为树，任意两点路径唯一，只能同色，违背两种颜色要求。

使用 DFS 访问序 dfn 与子树能经回边到达的最早访问序 low。父子树边 p−u 为桥，当且仅当 low[u]>dfn[p]；等于说明能绕回父亲，不能判为桥。图很深时用显式栈与每点边下标模拟 DFS，在退栈时把 low[u] 交回父亲并判断父边。邻接表保存边编号，跳过父边本身。

最终从一号只沿桥边搜索，将到达的顶点染黑。原图连通且至少有一条非桥边时，一定还有其它桥森林块，可以染白。这样不必穷举所有黑白方案。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<vector<pair<int,int>>>graph(n+1);
    for(int i=0;i<m;++i){int u,v;cin>>u>>v;graph[u].push_back({v,i});graph[v].push_back({u,i});}
    vector<int>dfn(n+1),low(n+1),parent(n+1),parent_edge(n+1,-1),next_edge(n+1),bridge(m),stack{1};int timer=1;dfn[1]=low[1]=1;
    while(!stack.empty()){int u=stack.back();if(next_edge[u]<int(graph[u].size())){auto [v,id]=graph[u][next_edge[u]++];if(id==parent_edge[u])continue;
            if(!dfn[v]){parent[v]=u;parent_edge[v]=id;dfn[v]=low[v]=++timer;stack.push_back(v);}else low[u]=min(low[u],dfn[v]);
        }else{stack.pop_back();if(parent[u]){int p=parent[u];if(low[u]>dfn[p])bridge[parent_edge[u]]=1;low[p]=min(low[p],low[u]);}}}
    if(timer!=n){cout<<-1<<'\n';continue;}
    vector<int>black(n+1);black[1]=1;stack.push_back(1);int count=1;
    while(!stack.empty()){int u=stack.back();stack.pop_back();for(auto [v,id]:graph[u])if(bridge[id]&&!black[v]){black[v]=1;++count;stack.push_back(v);}}
    if(count==n){cout<<-1<<'\n';continue;}
    for(int u=1;u<=n;++u)cout<<(black[u]?'B':'W');cout<<'\n';
}''',
    '两条简单路径可以共用桥；保留桥构造森林，不是删桥；原图不连通必无解；桥判据严格大于；深图不用系统递归栈。',
    r'每组时间与空间均为 $O(n+m)$。',tags=['DFS','图论'],lessons=A+['graphs','queue-stack','structures'],checker='two_paths_color')

add('CF1385E','先排已有有向边，再把无向边顺着同一个拓扑序定向',
    '图有一些已定向边和一些待定向边，不能更改原有方向。为所有无向边定向，使最终图无有向环，或判断不可能；原图可能不连通。',
    r'''只用已定向边建立依赖并拓扑排序。若它们已经成环，任何补方向都无法消环，输出 NO。否则给每个点记录拓扑位置，将每条无向边从位置较早端指向较晚端；原有有向边照原方向输出。最终所有边都严格增加位置，不可能成环。''',
    r'''无向边还没有限制谁先谁后，不能一开始就把它们计入有向入度。先问已有有向边能否共同满足某个先后顺序：建立它们的有向图，用全体零入度点完成拓扑排序。

若最终没有取满 n 个点，已有方向本身含环。新定向只会增加边，不能删除或反转这个环，因而必无解，输出 NO。

若取得完整拓扑顺序，令 position[u] 为顶点 u 的序号。每条已有有向边都从小位置指向大位置。现在也把每条待定向边从小位置端指向大位置端，便让最终全部边满足同一严格递增规则。

沿任意有向路径，position 每走一步都严格增加；若存在环，最后又回到起点，位置就既严格增加又不变，矛盾。因此这种统一定向保证无环。

原图即使有多个连通块或孤立顶点，也一起进入拓扑顺序，跨块任选先后没有影响。两端编号大小不能代替拓扑位置；例如原边三到一会要求三号位置小于一号，不能因为三大于一而反转原边。

输入边完整保存，最后逐条输出。只对原无向边交换两端，原有有向边必须保持不变。构造题允许多种方向组合，验证时检查所有原边身份、保留方向与最终无环，而不逐行比对样例方向。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;vector<array<int,3>>edges(m);vector<vector<int>>graph(n+1);vector<int>indegree(n+1),position(n+1);
    for(auto &e:edges){cin>>e[0]>>e[1]>>e[2];if(e[0]){graph[e[1]].push_back(e[2]);++indegree[e[2]];}}
    queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);int count=0;
    while(!ready.empty()){int u=ready.front();ready.pop();position[u]=++count;for(int v:graph[u])if(--indegree[v]==0)ready.push(v);}
    if(count!=n){cout<<"NO\n";continue;}cout<<"YES\n";
    for(auto e:edges){int u=e[1],v=e[2];if(!e[0]&&position[u]>position[v])swap(u,v);cout<<u<<' '<<v<<'\n';}
}''',
    '只用已有有向边排序；比较拓扑位置；原有方向不能改；输出全部 m 条边；不连通也要排全体顶点。',
    r'每组时间与空间均为 $O(n+m)$。',tags=['拓扑排序','构造'],lessons=G+['structures','construction'],checker='directed_edges')
