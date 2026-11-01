"""Tree states, rerooting, minimax preparation and uniform-frontier expectation."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
T=A+['trees','dp']

add('B4016','两次广度优先搜索找到一条最长路径',
    '无权树中求最长简单路径的边数，路径不能重复经过结点。',
    r'''从任意结点广搜，取一个最远结点A；再从A广搜，最远距离就是直径。树中任意两点路径唯一，从任一点取的最远结点一定可作为某条直径端点。用队列迭代搜索，单结点树距离为零。''',
    r'''直径的长度按边数计算，只有一个结点时是零，而不是一。树上两点间只有一条路径，所以广搜第一次到达的层数就是这条路径的长度。

先从任意起点s出发，找最远点A。树的一个性质是，A可以作为某条直径的端点，因此第二次从A找最远点B，就会得到最长路径。

为什么第一次最远点A一定能作端点？把树以s为根，深度就是第一次广搜距离，A的深度至少与任意其它点一样大。取一条已有直径X到Y，设它们从根出发最后一个公共祖先为t。

先看t不在根到A路径上的情况。A的分支会在t上方的某点q处分开；走A到X需要先上到更高的q。A不比Y浅，而q严格比t浅，因此A到X会比原来的Y到X更长，与原路径为直径矛盾。所以A必在t的子树内。

X、Y中至少有一端与A位于t的不同分支，或这一端就是t。取这一端为X。A到X和Y到X都经过t，而A的深度不小于Y，故前者不短于直径；又不可能超过全树最长长度，只能同长。这样A确实成为某条直径端点，并列最远点任选一个也不影响结论。

第二次搜索直接取所有距离的最大值，无须知道这次端点具体是哪一个。两次队列搜索都各访问每点每边常数次，十万结点的长链也不会产生递归栈过深问题。''',
    r'''int n; cin>>n; vector<vector<int>> g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
auto distances=[&](int start){
    vector<int> d(n,-1); queue<int> q; q.push(start); d[start]=0;
    while(!q.empty()){
        int u=q.front();q.pop();
        for(int v:g[u]) if(d[v]<0){d[v]=d[u]+1;q.push(v);}
    }
    return d;
};
auto d=distances(0);int endpoint=0;
for(int u=1;u<n;++u) if(d[u]>d[endpoint]) endpoint=u;
// 从一个最远端点再搜索，才得到全树直径。
d=distances(endpoint);
int diameter=0;for(int length:d) diameter=max(diameter,length);
cout<<diameter<<'\n';''',
    '长度是边数；最远点可能不唯一但可任选；先找到端点再搜一次；单结点为零；迭代队列避免深递归。',
    r'时间与空间均为 $O(n)$。',tags=['BFS'],lessons=A+['trees','queue-stack','lambda-local','numeric-tools'],key='bfs')

add('B4016','自底向上合并经过每个点的两条最长下行链',
    '求无权树最长简单路径的边数，使用树上自底向上的状态递推。',
    r'''任意选根，down[u]记录从u向子树走的最长边数。处理u时，取不同孩子提供的两条最大下行长度，二者之和就是以u为最高点的最长路径；用它更新全局答案，最大一条保存给父亲。先迭代取得父亲与顺序，再逆序计算。''',
    r'''将树随意定根后，每条简单路径都有唯一的最高点。路径从它往下最多分成两条链，且若两条都非空，必须进入不同的孩子子树，否则两端间的实际路径不会经过这个点。

因此，处理u时，每个孩子v提供一条从u走向它的链，长度为down[v]+1。保留最大的两条first、second；它们相加就是最高点为u的最长路径。若只想取一边，另一条可以为空、长度零，所以单孩子和叶子也由同一公式处理。

传给父亲的只能是一条链，令down[u]=first。不能把两条已经分叉的路径都传上去，否则会形成三叉结构，不再是简单路径。

对每个u都检查一次两链之和，便覆盖所有可能的路径最高点，取全局最大就是直径。根的选择只改变状态的描述，不改变所有简单路径的集合。

先用数组记录从根出发的访问顺序，再反向处理，孩子一定先于父亲完成，避免长链递归。叶子两条链均为零，单结点树自然输出零。''',
    r'''int n; cin>>n; vector<vector<int>> g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int> parent(n,-1),order={0}; parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];
    for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}
}
vector<int> down(n); int answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos],first=0,second=0;
    for(int v:g[u]) if(parent[v]==u){
        int length=down[v]+1;
        if(length>first){second=first;first=length;}
        else second=max(second,length);
    }
    down[u]=first; answer=max(answer,first+second);
}
cout<<answer<<'\n';''',
    '两条链必须来自不同孩子；传给父亲只传一条；路径可只有一边；空链长度零；遍历顺序逆着计算。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T+['numeric-tools'],key='downward')

add('P11249','剪去无宝物的叶子，看剩余部分是否仍有分叉',
    '树上从任意点开始，每条边至多走一次，判断能否收集全部宝物；非宝物结点不必全部经过。',
    r'''树上不重复走边的连续行程只能是一条简单路径。因此把没有宝物的叶子不断删去，得到连接全部宝物的最小子树；若它有度数大于二的结点，任何路径都无法覆盖三条必要分支，答案No，否则它本身就是一条路径或单点，答案Yes。''',
    r'''不能从一个分叉走到叶子后原路返回，因为那会第二次使用同一条边。树没有其它绕路，所以合法的连续行程实际是一条简单路径。

所有宝物之间的唯一路径都必须保留；除此之外的无宝物枝条无需走。反复剪去当前不含宝物的叶子，正好删除这些无关枝条，剩下连接全部宝物的最小子树。

若剩余树中某点连着三条及以上必要分支，一条简单路径在这里最多使用两条边，至少漏掉一条含宝物的分支，无法完成。若所有度数至多二，连通无环的剩余部分就是一条链，或者只剩一个宝物点，从一端走到另一端即可取得全部宝物。

用队列放入所有无宝物且度数至多一的点，弹出后标记删除，并减少仍在的邻居度数；新产生的无宝物叶子继续入队。宝物点绝不删除。每个点边处理常数次。

原题保证至少一个宝物，单个宝物不用移动也可成功。输入有多组，每组重新建立图与队列。''',
    r'''int tests; cin>>tests;
while(tests--){
    int n;cin>>n;vector<int> treasure(n),degree(n);for(int &x:treasure) cin>>x;
    vector<vector<int>>g(n);
    for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);++degree[u];++degree[v];}
    vector<char> alive(n,true); queue<int>q;
    for(int u=0;u<n;++u) if(!treasure[u]&&degree[u]<=1) q.push(u);
    while(!q.empty()){
        int u=q.front();q.pop();if(!alive[u]) continue;alive[u]=false;
        for(int v:g[u]) if(alive[v]){
            --degree[v];if(!treasure[v]&&degree[v]<=1) q.push(v);
        }
    }
    bool possible=true;
    for(int u=0;u<n;++u) if(alive[u]&&degree[u]>2) possible=false;
    cout<<(possible?"Yes":"No")<<'\n';
}''',
    '只需全部宝物；不能走叶子后原路返回；只剪无宝物叶子；检查剪枝后的度数；一个宝物也可成功；多组独立。',
    r'每组时间与空间均为 $O(n)$。',tags=['队列'],lessons=A+['trees','queue-stack'])

add('P15801','每个子树记高度、是否全满、是否完全',
    '有根二叉树保留左、右儿子顺序，统计有多少个结点的整棵子树是完全二叉树。',
    r'''空树高度零，视为全满且完全。若左右等高，左边必须全满、右边完全；若左边恰高一层，左边必须完全、右边全满；其它情况不完全。另记两边等高且都全满时当前也全满。迭代遍历后逆序计算，累计每个子树的完全标记。''',
    r'''完全二叉树按层从上到下、同层从左到右填充，中间不能有空位。只有右儿子没有左儿子就不完全；左右高度差不超过一也远远不够，还要看空位出现在哪一边。

每个子树记录高度h、全满full、完全complete。这里“全满”特指每一层都铺满，不只是每个内点都有两个儿子。空树高度零，两个标记都为真；这样叶子可以直接套用规则。

若左右高度相等，为防止左侧低层有空位而右侧仍有点，左子树必须全满，右子树可以是同高的完全树。若左高恰好一层，左边可以是完全树，但右边必须在较低高度上全满。除此之外，末层不能按从左到右顺序填成。

全满条件更简单：左右都全满且等高。先算两个儿子，再按这两类判当前是否完全，每个真标记贡献一。

左、右儿子不能交换；编号大小也不代表父子处理顺序，所以先从根一记录访问序，再反向计算。零号用作空儿子，初始化其状态即可。''',
    r'''int n;cin>>n;vector<int>left(n+1),right(n+1),height(n+1);
for(int u=1;u<=n;++u) cin>>left[u]>>right[u];
vector<int> order={1};
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];if(left[u]) order.push_back(left[u]);if(right[u]) order.push_back(right[u]);}
vector<char> full(n+1),complete(n+1);full[0]=complete[0]=true;int answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos],l=left[u],r=right[u];
    height[u]=1+max(height[l],height[r]);
    full[u]=full[l]&&full[r]&&height[l]==height[r];
    complete[u]=(complete[l]&&full[r]&&height[l]==height[r]+1)
              ||(full[l]&&complete[r]&&height[l]==height[r]);
    answer+=complete[u];
}
cout<<answer<<'\n';''',
    '完全要求层序左对齐；左、右不可换；全满与完全分别记录；零号为空树；高度相差一仍需检查哪边满；统计所有子树。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T)

add('P1131','子树先同步，再在每条子边上补到最长分支',
    '指定激发器为根，边传播时间只能增加，使所有终止结点收到信号的时刻相同，求最少增加总量。',
    r'''从叶子向根，height[u]表示u子树内部同步后到叶子的最短共同时间。取各孩子的边权加height的最大值H，较短分支统一在连接孩子的那条边上补到H，所补差值加入答案。内部费用已由孩子处理，单次补边可同时延迟该孩子下所有叶子。''',
    r'''若一条短分支下面有很多叶子，应在通往这整个分支的边上补时间，一单位就能同时延迟所有叶子；分别在每个叶子前补会重复花费。

先把树根定在给出的激发器S。叶子下面没有其它终止点，到自身的时间是零。假设每个孩子子树已经用最少费用同步，其共同到达时间为height[v]，从u过去再加边权w。

这些值中的最大值H不能降低，因为边时间只能增加，所以u到所有后代叶子的共同时间至少为H。对每条较短的孩子分支，在u到v这条边上补H-height[v]-w，便让它全部叶子达到H；长分支无需增加。

这个补法达到下界：每个短分支都至少有一条叶子路径缺少这段时间，不在该分支内增加足够时间便不可能追平；而补在子树入口恰好一次完成全部所需延迟。孩子内部先取最优也不吃亏，额外把整棵孩子子树延后只需在入口补。

将每个结点的这些差值累加，便是所有边所需的最小增加次数。N可到五十万，先迭代记父亲与顺序，再逆序处理；路径时间与总费用都使用long long。''',
    r'''int n,root;cin>>n>>root;--root;
struct Edge{int to;long long time;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={root};parent[root]=root;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(auto edge:g[u]) if(edge.to!=parent[u]){parent[edge.to]=u;order.push_back(edge.to);}}
vector<long long>height(n);long long answer=0;
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];long long longest=0;
    for(auto edge:g[u]) if(parent[edge.to]==u) longest=max(longest,height[edge.to]+edge.time);
    for(auto edge:g[u]) if(parent[edge.to]==u) answer+=longest-height[edge.to]-edge.time;
    height[u]=longest;
}
cout<<answer<<'\n';''',
    '根是给定S；时间只可增加；子树内部先同步；在子树入口补差可同时延迟全部后代；不能直接按每叶到根差值求和；六十四位。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T+['structures'])

add('P2458','分清本点设岗、由孩子覆盖、等待父亲覆盖',
    '保安设在一个点能看守自己与相邻点，各点费用不同，求看守全部树结点的最少费用。',
    r'''每点三状态：A本点设岗；B本点不设且由至少一个孩子设岗覆盖；C本点暂未覆盖、等父亲设岗。A可让孩子取三者最小；B让孩子取A或B并强制至少一个A；C禁止孩子设岗，所有孩子须为B。叶子为费用、不可达、零；根不能等待父亲，取A与B较小。''',
    r'''这里要求每点至少被一个保安看到，不要求恰好一个。一个点是否设岗会影响它的父亲与所有孩子，因此只保存“子树已覆盖的最低费用”会丢失边界信息。

设A表示本点设岗，子树全部看守；B表示本点不设，已由某个孩子保安看守，子树也全部看守；C表示本点还没被看守，子树其它点已看守，必须等待父亲设岗。

本点设岗时，它能负责尚未被看守的孩子，故每个孩子可在A、B、C中任选最便宜的，再加本点费用。

本点取B时，父亲不能被依赖，孩子也不能等待本点这个没有保安的父亲，所以每个孩子只能取A或B。先累加它们两者的较小值，再强制至少一个孩子选A：枚举由哪个孩子负责，额外费用是该孩子A减去原先的较小值，取最小增量。叶子没有孩子，这个状态不可达。

本点取C时，为让它确实还未覆盖，不能有孩子设岗；所有孩子都必须自己被下层孩子覆盖，即取B。叶子可以免费等待父亲，所以C为零。

根没有父亲，不能取C，最后只在A与B中取最小。输入按结点编号描述儿子，但行顺序、根编号都不必固定，先用入度找根，再逆序遍历计算。不可达费用用大值并截断累加，不让它溢出成便宜候选。''',
    r'''int n;cin>>n;vector<vector<int>>child(n);vector<int>indegree(n);vector<long long>cost(n);
for(int row=0;row<n;++row){int u,count;cin>>u;--u;cin>>cost[u]>>count;while(count--){int v;cin>>v;--v;child[u].push_back(v);++indegree[v];}}
int root=0;while(indegree[root]) ++root;vector<int>order={root};
for(size_t pos=0;pos<order.size();++pos) for(int v:child[order[pos]]) order.push_back(v);
const long long INF=1000000000000000LL;
vector<long long>guard(n),covered(n),waiting(n);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];guard[u]=cost[u];long long base=0,extra=INF;
    for(int v:child[u]){
        guard[u]+=min({guard[v],covered[v],waiting[v]});
        long long best=min(guard[v],covered[v]);base+=best;
        extra=min(extra,guard[v]-best);
        waiting[u]=min(INF,waiting[u]+covered[v]);
    }
    covered[u]=extra==INF?INF:base+extra;
}
cout<<min(guard[root],covered[root])<<'\n';''',
    '至少覆盖一次；本点设岗才可让孩子等待；由孩子覆盖须强制一个孩子设岗；叶子B不可达、C为零；根不能等待；输入顺序不当拓扑序。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T)

add('P2986','先算一个集会点，再沿边换根调整总路程',
    '树边有长度，每点有若干奶牛，选择某点聚会，使每只牛走来的路程总和最小，输出这个最小值。',
    r'''先选任意根，计算每棵子树奶牛数mass与根处总代价F。把集会点沿长w的边移到孩子v，v子树内奶牛各少走w，其余各多走w，所以新总代价增加w乘总牛数减两倍mass[v]。顺着树算完所有候选点，取最小，数量和费用均用六十四位。''',
    r'''奶牛数是权重。某点住二十只牛、离集会点三米，就贡献六十米，而不是只算一个农场三米。没有奶牛的点仍可作为聚会位置。

先以任意点定根，累计每个点到根的距离，得到根处总代价。逆序把孩子的奶牛数加给父亲，求出每个子树的总奶牛数mass。

设总牛数为C，从父亲u沿长度w的边移到孩子v。树上路径唯一，v子树内的每只牛都少走这条边，减少w乘mass[v]；其它牛都要多走它，增加w乘(C-mass[v])，所以

$$F(v)=F(u)+w(C-2mass[v]).$$

这只改变聚会点，没有真正移动奶牛，所有mass保持原根定义不变。按父亲先于孩子的顺序，便可线性得到每个点的总代价。

把所有点的F取最小，输出费用，不是结点编号。边长与牛数可为零；所有牛数为零时每点费用都是零。十万点时总加权距离可能远超int，使用long long。''',
    r'''int n;cin>>n;vector<long long>cows(n);long long total=0;
for(auto &x:cows){cin>>x;total+=x;}
struct Edge{int to;long long length;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={0};parent[0]=0;
vector<long long>distance(n),mass=cows,value(n);
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];value[0]+=cows[u]*distance[u];
    for(auto edge:g[u]) if(edge.to!=parent[u]){parent[edge.to]=u;distance[edge.to]=distance[u]+edge.length;order.push_back(edge.to);}
}
for(int pos=n-1;pos>0;--pos){int u=order[pos];mass[parent[u]]+=mass[u];}
long long answer=value[0];
for(int u:order){
    for(auto edge:g[u]) if(parent[edge.to]==u){
        int v=edge.to;value[v]=value[u]+edge.length*(total-2*mass[v]);answer=min(answer,value[v]);
    }
}
cout<<answer<<'\n';''',
    '每只牛分别计距离；零牛点也可聚会；换根时固定使用原子树牛数；子树内减、外部加；输出最小费用；六十四位。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T+['structures'])

add('P4084','按本点颜色递推孩子的两种不同色选择',
    '树的部分结点已固定颜色，用三种颜色完成所有结点，使每条边两端不同，求合法方案数模十亿加七。',
    r'''dp[u][c]为u涂颜色c、整个子树合法的方案数。若已有固定颜色不符，状态为零；否则每个孩子可取其余两色，先把孩子两色方案相加，再把不同孩子的选择数相乘。逆序计算，根三色方案相加。''',
    r'''只需禁止直接相连的两个点同色，不要求同一连通树内所有颜色互不相同，也没有“每色至少用一次”的限制。

固定u的颜色c后，不同孩子子树之间没有边，只通过u相连。因此每个孩子v可以选择另外两种颜色，其方案数是这两个状态之和；各孩子可以独立选择，所以这些和相乘。

若u已经涂色，只有相符的那个颜色允许使用，其它状态直接零。未涂色的叶子有三种独立候选，各候选状态初始一；固定色叶子只有一个状态为一。

自叶向根求出所有状态后，根没有父亲限制，三个颜色状态全部相加。固定色冲突会在相邻状态相乘时自然得到零；没有任何预涂色时，也使用同一递推。

模数是十亿加七。每个孩子的两项和先取模，再与当前状态相乘，用long long保存乘法中间值。父子顺序先迭代取得，逆序处理以适应十万点长链。''',
    r'''int n,k;cin>>n>>k;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>fixedColor(n,-1);bool conflict=false;
for(int i=0,u,c;i<k;++i){cin>>u>>c;--u;--c;if(fixedColor[u]>=0&&fixedColor[u]!=c) conflict=true;fixedColor[u]=c;}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
const long long MOD=1000000007;
vector<vector<long long>>dp(n,vector<long long>(3));
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];
    for(int c=0;c<3;++c){
        if(fixedColor[u]>=0&&fixedColor[u]!=c) continue;
        dp[u][c]=1;
        for(int v:g[u]) if(parent[v]==u){
            long long ways=0;for(int other=0;other<3;++other) if(other!=c) ways+=dp[v][other];
            dp[u][c]=dp[u][c]*(ways%MOD)%MOD;
        }
    }
}
cout<<(conflict?0:(dp[0][0]+dp[0][1]+dp[0][2])%MOD)<<'\n';''',
    '只限制相邻两点；固定色状态不可改；孩子颜色选择先加、子树之间再乘；无固定色也合法；冲突输出零；模数十亿加七。',
    r'三色固定，时间与空间均为 $O(n)$。',tags=['树形 DP','组合计数'],lessons=T+['counting','modular'])

add('P9584','旧树点对和不变，只增加新叶子与旧点的双向距离',
    '每次独立地在指定旧点接一条给定费用的新叶子，求新树所有有序点对距离之和，答案模998244353。',
    r'''先按每条旧边两侧点数计算旧树无序点对和S，再用换根预处理每个旧点到全部旧点的距离和F。新叶子接在k、边长w时，旧点间距离不变；新增加的单向距离和为F[k]+nw，有序点对再乘二。每个查询直接把这部分加入旧树的双向和。''',
    r'''每个方案都从原树重新考虑，不会真的留下上个查询的新城市。两旧点之间的路径不变，只需补上新叶子与每个旧点之间的距离；新叶子到自己的距离零。

先数旧树点对。删开某条长w的边，若一侧有s个旧点，另一侧有n-s个，就有s乘(n-s)个无序点对经过这条边。其总贡献为w乘这两侧点数。逐边累加得到无序和S；原题把两个方向都计入，所以旧部分为二倍S。

还需快速求接点k到所有旧点的距离和F[k]。先算任意根的距离总和，再沿边换根：移到大小s的孩子子树时，s个点各近w，其余各远w，总代价变化为w乘(n-2s)。这样线性得到全部F。

新叶子到旧点i的距离是w加dist(k,i)。将n个旧点相加，得到F[k]+nw，再把两个方向都算上：

$$answer=2S+2(F[k]+nw).$$

原树所有点对的完整总和可能超过六十四位，所以S逐条边取模，不能先累加完再取。F本身仅是一个点到其它点的距离总和，在当前范围内long long足够；输出时再取模。

本题只计缓存中取得的两组字面样例；题面引用的第三至第六组附件保留引用，不把未取得附件算作已经验证。''',
    r'''int n,queries;cin>>n>>queries;
struct Edge{int to;long long length;};vector<vector<Edge>>g(n);
for(int i=1,u,v;i<n;++i){long long w;cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<int>parent(n,-1),order={0},size(n,1);parent[0]=0;
vector<long long>depth(n),edgeToParent(n),value(n);
for(size_t pos=0;pos<order.size();++pos){
    int u=order[pos];value[0]+=depth[u];
    for(auto edge:g[u]) if(edge.to!=parent[u]){int v=edge.to;parent[v]=u;depth[v]=depth[u]+edge.length;edgeToParent[v]=edge.length;order.push_back(v);}
}
const long long MOD=998244353;long long pairs=0;
for(int pos=n-1;pos>0;--pos){
    int u=order[pos];
    pairs=(pairs+edgeToParent[u]%MOD*size[u]%MOD*(n-size[u]))%MOD;
    size[parent[u]]+=size[u];
}
for(int u:order) for(auto edge:g[u]) if(parent[edge.to]==u){int v=edge.to;value[v]=value[u]+edge.length*(n-2*size[v]);}
while(queries--){
    int k;long long w;cin>>k>>w;--k;
    long long added=(value[k]%MOD+(n%MOD)*(w%MOD))%MOD;
    cout<<(2*pairs+2*added)%MOD<<'\n';
}''',
    '每个方案独立；旧点距离不变；有序点对计两个方向；新叶自己距离零；旧总和逐边取模；F换根仍按旧树大小。',
    r'预处理 $O(n)$，每次查询 $O(1)$，总时间 $O(n+q)$，空间 $O(n)$。',tags=['树形 DP','组合计数'],lessons=T+['structures','counting','modular'])

add('P13020','固定根时排列各点孩子，再提取所有根的共同乘积',
    '树上起点任意，每点访问邻居次序任意，求不同深度优先遍历序的数量，模十亿。',
    r'''固定根，根的孩子数为度数，其它点少一个父亲，方案数是各点孩子数阶乘之积。n大于一时，提出共同乘积B，即所有点的度数减一的阶乘之积；换成根只多乘该点度数。把所有根相加，度数和是2(n-1)，所以答案为这个度数和乘B。单点树只有一种。''',
    r'''一旦选定根，深度优先遍历必须完整走完某个孩子子树后，才会进入下一个孩子。不同结点编号唯一，因此改变孩子子树的访问顺序，会改变遍历序列中下一批出现的编号，确实得到不同序列。

固定根r时，每点的孩子可以任意排列，各点选择相互独立，所以方案数为孩子数阶乘的乘积。根有deg(r)个孩子，其它点有deg(v)-1个。

对n大于一的树，每点度数至少一。先取共同部分

$$B=\prod_v (deg(v)-1)!.$$

让r作根，只把它的那项换成deg(r)的阶乘，比原项多乘deg(r)。因此固定根r的答案是deg(r)B；不同根的序列第一项不同，不会重复，求和即B乘全部度数之和。

每条树边贡献两个端点度数，度数和为2(n-1)。最终只需预计算阶乘、扫描各点度数，再做这个乘法。模数十亿并非质数；这里没有做除法或求逆元，所以完全不需要假定模数为质数。

n为一时不能访问负一的阶乘，应单独输出一。无需真正模拟所有深搜顺序，也无需逐个换根重算乘积。''',
    r'''int n;cin>>n;vector<int>degree(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;++degree[u];++degree[v];}
if(n==1){cout<<1<<'\n';return 0;}
const long long MOD=1000000000;
vector<long long>factorial(n+1,1);
for(int i=1;i<=n;++i) factorial[i]=factorial[i-1]*i%MOD;
long long product=1;
for(int d:degree) product=product*factorial[d-1]%MOD;
cout<<product*(2LL*(n-1)%MOD)%MOD<<'\n';''',
    '根与非根孩子数差一；不同根序列不重复；孩子子树必须整段访问；模十亿不能随便求逆；单点单独处理。',
    r'时间与空间均为 $O(n)$。',tags=['组合计数'],lessons=A+['trees','counting','modular'])

add('CF337D','自底向上与自顶向下分别求最远已知受害点',
    '已知树上若干地点受到距离不超过d的影响，求可能的源头地点数量；其它地点是否受影响尚未查明。',
    r'''down[u]求u子树里最远已知受害点的距离，没有则不可达；up[u]求子树外最远距离。先逆序求down，再顺序给孩子传up，来源可能是u自身、u的外部或其它孩子，利用最大两项排除当前孩子。每个候选点到所有已知受害点的最远距离不超过d才合法。''',
    r'''只要全部已知受害点落在影响半径内就可以，未被报告的点也可能受影响。不能因为某个未标记点在范围内就排除候选。

判断点u，需要它到全部标记点的最远距离。任意定根，将来源分为u子树内部与外部两类。down[u]记录内部最远值，若u自己标记则可取零，再比较各孩子down加一；完全没有标记的子树必须记为不可达，不能伪造一个零距离标记。

给孩子v计算外部来源时，可以是u自己、u的子树外部，以及v以外的其它孩子子树；这些点从v看都要先经过边v到u，距离再加一。当前v子树的来源一定不能再拿来充当它的外部。

为避免每个孩子都重新扫描所有兄弟，对u保存所有来源的最大、次大距离，以及最大值来自哪个孩子。若最大来自当前孩子，就改用次大；否则继续用最大。并列最大也要保留第二份，否则会错删另一个同样远的合法来源。

父亲先于孩子处理，up依次传下；最后max(down[u],up[u])就是u到全部标记点的最远距离，不超过d便计一个。已有至少一个标记，整树的最终最远值都有意义。''',
    r'''int n,m,limit;cin>>n>>m>>limit;vector<char>marked(n);
for(int i=0,u;i<m;++i){cin>>u;marked[u-1]=true;}
vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
const int NEG=-1000000000;vector<int>down(n,NEG),up(n,NEG);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];if(marked[u]) down[u]=0;
    for(int v:g[u]) if(parent[v]==u&&down[v]>=0) down[u]=max(down[u],down[v]+1);
}
for(int u:order){
    int first=max(up[u],marked[u]?0:NEG),second=NEG,owner=-1;
    for(int v:g[u]) if(parent[v]==u&&down[v]>=0){
        int value=down[v]+1;
        if(value>first){second=first;first=value;owner=v;}
        else second=max(second,value);
    }
    for(int v:g[u]) if(parent[v]==u){int best=owner==v?second:first;if(best>=0) up[v]=best+1;}
}
int answer=0;
for(int u=0;u<n;++u) if(max(down[u],up[u])<=limit) ++answer;
cout<<answer<<'\n';''',
    '标记只列已知受害点；子树无标记用不可达；给孩子传外部时排除自身来源；保留并列最大；比较最远距离而非最近。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T)

add('CF1416C','按最高不同位稳定分组，让异或的每一位独立选择',
    '选非负x统一异或数组，使逆序对最少；最优x有多个时取数值最小者，输出逆序数和x。',
    r'''从高位到低位，只在更高位相同的分组里比较当前位，保持原下标相对顺序。某位不翻转的逆序贡献是先一后零的对数，翻转则为先零后一；各组累加成这一位两种代价。每位独立选较小值，相等选零，保证x最小。分组用稳定划分与一个辅助数组实现。''',
    r'''两个数的大小只由它们最高的不同二进制位决定。统一异或后，更高的相同位仍相同，最高不同位的位置也不会改变，只可能把这位零一翻转，交换大小关系。

因此每个原下标对只需要在最高不同位被统计一次。自高位向下分组，更高位相同的元素留在同组，组内始终保持原输入的先后次序，才能判断谁在前。

扫描某组的当前位，遇到零时，此前的一的数量就是“不翻转”新增逆序数；遇到一时，此前零的数量是“翻转”后的新增逆序数。将全部组对同一位的两种贡献相加，得到keep与flip。

这一位选择只改变由它决定大小的那些对，不影响最高不同位在别处的对，所以各位可以独立取较小值。flip严格更小时，设置x这一位为一；相等时保持零。所有位都取零的平局方案在数值上最小。

计数后，将当前组稳定分成零组、一组继续处理下一位。不能直接排序破坏组内原下标顺序。一个辅助数组即可完成稳定划分，递归最多三十层，与树的结点深度无关。

原数小于二的三十次方，更高位全相同，翻转也不会改变任何相对大小；为让x最小，全部保持零。逆序对数可到数百亿，用long long。''',
    r'''int n;cin>>n;vector<int>a(n),temporary(n);for(int &x:a) cin>>x;
vector<long long>keep(30),flip(30);
function<void(int,int,int)> divide=[&](int l,int r,int bit){
    if(bit<0||r-l<2) return;
    int zeros=0,ones=0;
    for(int i=l;i<r;++i){
        if(a[i]>>bit&1){flip[bit]+=zeros;++ones;}
        else{keep[bit]+=ones;++zeros;}
    }
    int zeroPosition=l,onePosition=l+zeros;
    for(int i=l;i<r;++i){if(a[i]>>bit&1) temporary[onePosition++]=a[i];else temporary[zeroPosition++]=a[i];}
    for(int i=l;i<r;++i) a[i]=temporary[i];
    divide(l,l+zeros,bit-1);divide(l+zeros,r,bit-1);
};
divide(0,n,29);
long long inversions=0;int x=0;
for(int bit=0;bit<30;++bit){
    inversions+=min(keep[bit],flip[bit]);
    if(flip[bit]<keep[bit]) x|=1<<bit;
}
cout<<inversions<<' '<<x<<'\n';''',
    '每对只在最高不同位计数；稳定保留原下标顺序；同位代价需跨全部分组求和；平局选零；重复值不算逆序；六十四位计数。',
    r'值域不超过三十位，时间 $O(30n)$，空间 $O(n)$，另有三十层递归栈。',tags=['分治','位运算'],lessons=A+['bitwise','recursion','lambda-local'])

add('P1453','删一条环边成树，分别禁止它的两个端点',
    '连通单圈图上选若干互不相邻的点开店，点人流量乘公共非负倍率为利润，求最大利润，保留一位小数。',
    r'''并查集读边时，找到一条连接已相连两点的边，暂不加入树。原图只比树多这一条边，合法选点必须至少不选它的一个端点。分别禁止两个端点做两次树最大权独立集：不选u时孩子任选，选u时孩子都不能选。取两次的最大人流量和，最后乘倍率并格式化输出。''',
    r'''不能把环边直接忽略后只算一次树，否则原来相邻的两个断边端点可能同时开店。也不需要枚举整条环的所有开店情况：这条额外边只多出“两个端点不能同时选”一个约束。

用并查集逐条加入边，某条边的两个端点已相连时，它就是使图形成环的额外边；暂不加入邻接表，其余n-1条边组成树。设额外边为u、v。

原图任意合法方案至少有一个端点未选，所以分别求“禁止u”与“禁止v”的最优值，取最大便覆盖全部合法方案；这两个限制下的树方案也都满足被删边约束，不会产生非法候选。

树中为每点记选与不选两种状态。选当前点，就加它的人流量，并让全部孩子不选；不选当前点，孩子可选可不选，各自取更优。禁止的点将选状态置为负无穷。逆序遍历求根的两种值，再取最大。

公共倍率k非负，最大化利润等价于先最大化整数人流量和；只在最后乘一次k，避免把每点浮点利润累加进状态。按C++固定小数输出方式保留一位。输入点编号原本从零开始，不再减一。

图若有平行环边，这个断边思路仍满足同一相邻约束；自环则要求该端点禁选，同一端点两次求解也能处理。''',
    r'''int n;cin>>n;vector<long long>weight(n);for(auto &x:weight) cin>>x;
vector<int>representative(n),componentSize(n,1);iota(representative.begin(),representative.end(),0);
auto find=[&](int x){while(representative[x]!=x){representative[x]=representative[representative[x]];x=representative[x];}return x;};
vector<vector<int>>g(n);int cycleU=-1,cycleV=-1;
for(int i=0,u,v;i<n;++i){
    cin>>u>>v;int a=find(u),b=find(v);
    if(a==b){cycleU=u;cycleV=v;}
    else{if(componentSize[a]<componentSize[b]) swap(a,b);representative[b]=a;componentSize[a]+=componentSize[b];g[u].push_back(v);g[v].push_back(u);}
}
double multiplier;cin>>multiplier;
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
auto solve=[&](int forbidden){
    vector<long long>take(n),skip(n);const long long NEG=LLONG_MIN/4;
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos];take[u]=weight[u];
        for(int v:g[u]) if(parent[v]==u){take[u]+=skip[v];skip[u]+=max(take[v],skip[v]);}
        if(u==forbidden) take[u]=NEG;
    }
    return max(take[0],skip[0]);
};
long long population=max(solve(cycleU),solve(cycleV));
cout<<fixed<<setprecision(1)<<population*multiplier<<'\n';''',
    '原编号从零开始；断边至少一端禁选；树中选父不能选子；倍率非负才可先最大化整数和；最后乘一次并保留一位小数。',
    r'时间 $O(n\alpha(n))$，空间 $O(n)$，其中两遍树递推均为线性。',tags=['树形 DP','并查集'],lessons=T+['dsu','lambda-local','numeric-tools'],exact=True)

add('P3554','二分每轮染色能力，自底向上计算必须提前染黑的点数',
    '树上一号点初始黑，玩家每轮先染黑若干点，对手再沿边走一步，若到白点就输；求保证安全并最终全部染黑的最小每轮能力。',
    r'''固定k，need[u]表示对手刚到已黑u时，其子树中还必须预先准备多少个黑点，才能确保以后安全。每个孩子既要自己黑，又要满足它的预备需求，合计所有孩子的need加一；本轮能补k个，所以剩余需求取合计减k与零的较大值。根需求为零才可行，能力增加不会更差，二分最小k。''',
    r'''不能简单回答最大孩子数。例如根只有一个孩子，这个孩子再有四个叶子：每轮三次就够。第一轮染黑孩子和两个叶子，对手到孩子后，第二轮补另两个叶子即可；无需每轮四次，因为可以提前准备。

[官方原题与解说](https://oi.edu.pl/static/attachment/20140306/oi20.pdf)中，对手可以回头走。但回头只会给染色者更多轮准备时间，若有必胜攻击路径，也可去掉重复经过的绕行而更早到白点。因此判断最坏情况时，可以只考虑从根向下走。

固定每轮能力k。定义need[u]为：对手刚进入已经黑的u，在开始本轮染色之前，u子树中除了u之外最少还需提前染黑的点数。叶子下面没有危险，需求零。

对手下一步可以任意选一个孩子v，所以每个孩子必须黑，而且它的子树还要准备need[v]个点，才能应付抵达后的游戏。不同孩子子树互不相交，准备量应相加，不能只取最大；当前这一轮可补k个，仍欠的才需提前准备：

$$need[u]=\max\left(0,\sum_{v\text{是孩子}}(need[v]+1)-k\right).$$

这些数量不是随意挑的黑点：递推同时给出可实现的准备安排，先满足每个孩子的最小准备，再将其中至多k个安排到当前轮，其余上交父层预先处理。若根仍欠正数，游戏开始前只有根黑，没有地方补这份预付款；若为零，就存在始终不让对手进入白点的策略。k为正时，每轮仍可继续染剩余白点，最终全黑。

越大的k越容易满足，故二分答案，每次按同一个逆序遍历做一次线性判断。单结点已全黑，最小能力为零；三十万点的长链用迭代顺序避免递归栈问题。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
vector<int>need(n);
auto possible=[&](int capacity){
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos],required=0;
        for(int v:g[u]) if(parent[v]==u) required+=need[v]+1;
        need[u]=max(0,required-capacity);
    }
    return need[0]==0;
};
int low=0,high=n;
while(low<high){int mid=low+(high-low)/2;if(possible(mid)) high=mid;else low=mid+1;}
cout<<low<<'\n';''',
    '允许提前准备后代；孩子需求相加而非取最大；本点已黑不再收费；根不能欠预备黑点；回头只给额外时间；单点能力零。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',tags=['树形 DP','二分答案'],lessons=T+['lambda-local'])

add('P5958','沿子树传播的临界比例取较小值，不同起点取最大值',
    '一名未知起点的叛徒会引发公司树上的向上传播，负责人触发后让整棵下属子树加入；求把最坏总人数限制在k以内的临界比例。',
    r'''size[u]为子树人数。令limit[u]为某个起点能使u整棵子树加入的临界比例，叶子为一。若从孩子v开始，需要既能填满v子树，又能让这些人在u的全部下属中达到比例size[v]/(size[u]-1)，所以本条路线取两阈值较小值，全部孩子取最大。最后在size大于k的子树中取最大临界值；本题比例严格超过x才触发，相等时已经安全，按允许误差输出。''',
    r'''最初那名叛徒只使自己加入，不会直接强迫下属加入。随后某个负责人发现已加入的下属比例严格超过x，才会带上整棵子树。相等时不触发，这是本题中文题面与[波兰语原卷](https://szkopul.edu.pl/problemset/problem/CUjJDGGSEZmO7HvdZU4FKrL6/statement/)的定义。同站英文译本使用“至少”，等号边界不同；下面依照本题的严格超过求最小安全值，数值临界值也与英文版误差判定下的极限一致。

一个负责人触发后，其整棵子树都会加入。从单个起点向外传播，所有真正触发的负责人都在它的祖先链上，触发的完整子树相互包含。因此最终人数超过k，当且仅当某棵人数大于k的子树被整体引发。

最坏起点可以考虑叶子。若从某个内点开始就足以触发更大的祖先，把起点放在它的后代叶子上，同样小的比例阈值足以让中间较小子树先后加入，不会降低最坏传播能力。

令limit[u]为能引发u整棵子树的临界比例。叶子自己就是最初叛徒时已经整棵加入，阈值可记为一。对非叶子，先选择一个孩子v作为起点所在分支：要先使v子树整体加入，x必须低于它的临界值；叶子作为起点则不需要这一步触发。此时u的全部直接、间接下属共size[u]-1人，其中已有size[v]人加入，向上触发要求x严格小于

$$R_v=\frac{size[v]}{size[u]-1}.$$

同一路线两个条件都要满足，能力取较小值；可以选任一孩子作最坏起点，取最大：

$$limit[u]=\max_v\min(limit[v],R_v).$$

对非叶子的这条路线，x低于两个比例的较小值才会触发；把x提高到该临界值，至少一个严格不等式就不再成立。因此要阻断全部可能超过k人的完整子树，取所有size[u]大于k的limit最大值；若没有这样的子树，零即可。原题k至少一，单个初始叛徒不会单独超限。

每个临界值始终是某条边的这个比例，或零、一。可以保存整数分子分母，比较正分数时交叉相乘：a除以b小于c除以d，等价于ad小于bc。分子分母至多五十万，乘积在long long内，不必用浮点反复二分。只在最终除法与输出时转换成实数。

父亲编号总比孩子小，先逆序求子树大小，再逆序向父亲汇总临界值，线性完成。''',
    r'''int n,k;cin>>n>>k;vector<int>parent(n,-1),children(n),size(n,1);
for(int u=1;u<n;++u){cin>>parent[u];--parent[u];++children[parent[u]];}
for(int u=n-1;u>0;--u) size[parent[u]]+=size[u];
vector<Ratio>limit(n,{0,1});Ratio answer={0,1};
for(int u=n-1;u>=0;--u){
    if(!children[u]) limit[u]={1,1};
    if(size[u]>k&&lessRatio(answer,limit[u])) answer=limit[u];
    if(u){
        Ratio edge={size[u],size[parent[u]]-1};
        Ratio candidate=lessRatio(limit[u],edge)?limit[u]:edge;
        if(lessRatio(limit[parent[u]],candidate)) limit[parent[u]]=candidate;
    }
}
cout<<fixed<<setprecision(10)<<(long double)answer.numerator/answer.denominator<<'\n';''',
    '最初叛徒不自动带下属；本题严格超过阈值才触发；人数不含负责人自己；同路取最小、孩子取最大；只阻断大于k的子树；按实数误差输出临界值。',
    r'时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T+['structures','basic-arithmetic'],
    declarations=r'''struct Ratio{long long numerator,denominator;};
bool lessRatio(const Ratio &a,const Ratio &b){return a.numerator*b.denominator<b.numerator*a.denominator;}''',checker='critical_fraction')

add('P8916','把祖先的同色边次数压成一个带符号的差值状态',
    '每点可染黑白；父子同色时，父亲必须加上该孩子整棵子树内同色点的全部战力，含负数，求所有最终士气之和最大值。',
    r'''换成按每点战力统计贡献：一个点被自己算一次，还会被路径上每条“两个端点都与它同色”的祖先边多算一次。固定当前点黑色，设祖先黑黑边、白白边次数为B、W，减去常量W乘子树总战力后，只需记差d=B-W。孩子同色转d+1；异色后交换黑白，转-d并补d乘该孩子总战力。根d为零，逆序枚举深度范围内的差值。''',
    r'''必须区分“子树同色”和“同色连通块”。原样例根六、孩子负二和四、负二下面有负七。让根、四、负七同黑，负二白，根只经四这条同色子边增加四，不能越过异色孩子去直接加入负七，最终总和五。

把所有士气相加后，改成看每个原战力w_x被算了几次。它先在自己那里算一次；若某个祖先u与通向x的第一个孩子v同色，而且x也是这个颜色，u就再算一次w_x。因此只需数根到x路径上的黑黑边和白白边；中间整条路径不必同色。

设进入子树u时，路径上已有B条黑黑边、W条白白边。当前点若黑，自己贡献w_u乘(1+B)；若白则乘(1+W)。所有黑白整体交换不改变问题，可以把当前点固定叫作黑色。

若从B和W中同时减去W，每个后代无论选择什么颜色，其贡献都统一少了W乘它的战力。因此原问题等于一个常量W乘子树总战力，加上只依赖差值d=B-W的最优值G_u(d)。d可能为负，它是消掉公共部分后的差，不是实际的边数量。

当前点的归一化贡献是w_u乘(1+d)。对孩子v，若它也黑，新增一条黑黑边，状态变为d+1；若它白，这条边异色，不增加计数，但为继续把孩子叫作“黑”，需要交换两种颜色，差值变成-d，公共部分的变化还需加上d乘子树总战力S_v。

所以对每个孩子独立比较两种选择：

$$G_u(d)=w_u(1+d)+\sum_v M_v(d),$$

$$M_v(d)=\max\bigl(G_v(d+1),G_v(-d)+dS_v\bigr).$$

孩子子树互不相交，状态中的祖先环境已固定，因此最优贡献相加。根没有祖先边，答案为G_根(0)。

深度D的点只有D条祖先路径边，所以只算d从负D到正D。孩子深度多一，d+1与-d都在它的范围中。总时间、空间为平方级，n至多三百；所有负战力也必须选某种颜色，答案可以为负，不能与零取最大。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<long long>weight(n),sum(n);for(auto &x:weight) cin>>x;
vector<int>parent(n,-1),depth(n),order={0};parent[0]=0;
for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;depth[v]=depth[u]+1;order.push_back(v);}}
vector<vector<long long>>dp(n);
for(int pos=n-1;pos>=0;--pos){
    int u=order[pos];sum[u]=weight[u];
    for(int v:g[u]) if(parent[v]==u) sum[u]+=sum[v];
    dp[u].resize(2*depth[u]+1);
    for(int d=-depth[u];d<=depth[u];++d){
        long long value=weight[u]*(1LL+d);
        for(int v:g[u]) if(parent[v]==u){
            long long same=dp[v][d+1+depth[v]];
            long long different=dp[v][-d+depth[v]]+1LL*d*sum[v];
            value+=max(same,different);
        }
        dp[u][d+depth[u]]=value;
    }
}
cout<<dp[0][0]<<'\n';''',
    '加的是整个孩子子树同色战力，不是同色连通块；负数必须加入；按每点贡献计数；异色转移要交换差值并补常量；根状态零；答案可负。',
    r'时间与空间均为 $O(n^2)$。',tags=['树形 DP'],lessons=T)

add('P10767','求每棵签表子树的冠军相对名次区间，再合并同轮位置',
    '满淘汰赛每场指定取强者或弱者，参赛者位置可任意安排；逐问某实力a是否存在安排能进入第b轮，冠军视作进入n加一轮。',
    r'''每个签表子树保存冠军在内部所有选手中的最小、最大可能名次lo、hi。取强者时lo为两子lo相加，hi取一侧hi加另一侧人数的较大值；取弱者时lo取较小、hi为两侧hi之和减一。高度h的比赛可让全局实力a胜出，当且仅当lo≤a≤总人数减子树人数加hi。合并同高度所有位置的可行区间，查询h=b-1即可。''',
    r'''不同询问只问各自是否存在一种安排，可以采用不同的选手分布。实力编号越大越强；进入第二轮表示先赢一场，进入n加一轮才表示夺冠，轮数不能直接当已经获胜次数。

先看某棵含M个选手的签表，忽略全局编号，只按内部实力从小到大排第一至第M。记冠军最小可能名次lo、最大可能名次hi。可能名次之间没有缺口：全体排列可通过交换相邻实力值相互到达，而这种交换让冠军名次至多变化一，所以从最小走到最大会经过每个中间名次。

叶子只有一人，lo与hi都为一。若根比赛取较强者，两侧都要能产生不超过最终冠军的赢家，最小可行名次为lo_L+lo_R；最大名次则让某侧取自己的最高赢家，并把另一侧人数全部放到它下面，取两种位置的较大值。

若根取较弱者，最小名次可取两侧lo的较小者；最大名次为hi_L+hi_R-1。也可通过把所有实力大小反转、同时交换max与min规则，从前一组公式对称得到这一组。

回到全局N个选手，想让实力a在某个M人子树里获胜，至少要能提供lo-1个比它弱的对手，以及M-hi个比它强的对手。可行相对名次是连续区间，因此两个数量条件也充分，等价于

$$lo\le a\le N-M+hi.$$

查询进入第b轮，对应赢下高度h=b-1的某棵子树。若不是整棵签表，M不超过N的一半，每个位置的可行区间都包含M至N-M+1这一段，彼此有交集；所以它们的并集只需保存最小左端与最大右端。整棵签表只有一个位置，也无需额外合并。

输入从冠军赛开始、按层给规则，正好对应二叉堆编号。自底向上求完lo、hi后，按高度汇总两个边界；第一轮尚未比赛，所有实力都可进入。之后每问只需一次区间判断。''',
    r'''int n,queries;cin>>n>>queries;int total=1<<n;
vector<int>rule(total);for(int u=1;u<total;++u) cin>>rule[u];
vector<int>low(2*total,1),high(2*total,1),size(2*total,1);
for(int u=total-1;u>=1;--u){
    int l=2*u,r=l+1;size[u]=size[l]+size[r];
    if(rule[u]==1){low[u]=low[l]+low[r];high[u]=max(high[l]+size[r],high[r]+size[l]);}
    else{low[u]=min(low[l],low[r]);high[u]=high[l]+high[r]-1;}
}
vector<int>leftBound(n+1,1),rightBound(n+1,total);
for(int height=1;height<=n;++height){
    leftBound[height]=total;rightBound[height]=0;
    for(int u=total>>height;u<(total>>(height-1));++u){
        leftBound[height]=min(leftBound[height],low[u]);
        rightBound[height]=max(rightBound[height],total-size[u]+high[u]);
    }
}
while(queries--){int a,b;cin>>a>>b;int height=b-1;cout<<(leftBound[height]<=a&&a<=rightBound[height]?"Yes":"No")<<'\n';}''',
    '全局实力与子树相对名次不同；进入b轮只赢b减一场；输入规则从根往下；同高度区间合并须有重叠理由；询问独立；首轮全部可行。',
    r'N为参赛人数，时间 $O(N+m)$，空间 $O(N)$。',tags=['树形 DP'],lessons=T)

add('UVA1218','非服务器严格由父亲或唯一一个孩子服务',
    '树上选最少服务器，使每个非服务器恰好相邻一个服务器；服务器之间可以相邻。多组输入，零分隔，负一结束。',
    r'''三状态为A本点是服务器、B本点非服务器且由父亲服务、C本点非服务器且由一个孩子服务。A的孩子只能取A或B；B不能再有孩子服务器，所有孩子须取C；C必须恰好一个孩子取A，其余取C，用已选零个或一个服务器孩子的合并状态实现。根取A与C最小，叶子为一、零、不可达。''',
    r'''[原始PDF](https://onlinejudge.org/external/12/1218.pdf)明确要求每个客户恰好由一个相邻服务器服务。服务器自身不属于客户，所以两个服务器相邻允许；一个非服务器夹在两个服务器之间却不允许。这与普通的“至少覆盖一次”树上设岗不同。

定义A：本点是服务器；B：本点不是服务器，由父亲这个服务器服务；C：本点不是服务器，父亲也不是服务器，必须由恰好一个孩子服务器服务。三者都要求子树内其它客户已经满足唯一服务。

本点取A时，孩子若设服务器可取A；若不是，则已经得到父亲服务，只能取B，不能再让它由孩子服务。故对每个孩子取A、B较小者，加上本点一台。

本点取B时，父亲已经负责自己，不能再有任何孩子服务器，否则自己得到两次服务。每个孩子只能是非服务器，而且它的父亲本点也不是服务器，因此必须取C，全部相加。

本点取C时，恰好选一个孩子为A，其余孩子全为C。不要简单把每个孩子的A、C取最小，那可能选出零个或多个服务器。依次合并孩子，保存“至今选了零个”与“至今选了一个”的最小费用：当前孩子选A只能从零个转一个，当前孩子选C则保留数量。

叶子A为一，B为零，C不可能。根没有父亲，不能取B，最终取A、C最小。不可达费用使用大值并截断加法。

案例后面的零不是零个结点的新案例，负一才结束全部输入，程序忽略零分隔符。原卷中两个相邻服务器覆盖六点的例子已核对，不能额外禁止服务器相邻。''',
    r'''int n;
while(cin>>n&&n!=-1){
    if(n==0) continue;
    vector<vector<int>>g(n);
    for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
    vector<int>parent(n,-1),order={0};parent[0]=0;
    for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    const long long INF=1000000000000000LL;
    vector<long long>server(n),byParent(n),byChild(n);
    for(int pos=n-1;pos>=0;--pos){
        int u=order[pos];server[u]=1;long long zero=0,one=INF;
        for(int v:g[u]) if(parent[v]==u){
            server[u]+=min(server[v],byParent[v]);
            one=min(min(INF,one+byChild[v]),min(INF,zero+server[v]));
            zero=min(INF,zero+byChild[v]);
        }
        byParent[u]=zero;byChild[u]=one;
    }
    cout<<min(server[0],byChild[0])<<'\n';
}''',
    '客户恰好一个相邻服务器；服务器可以相邻；父亲已服务时禁止孩子服务器；C恰好选一个；根不能由父服务；零分隔、负一结束。',
    r'每组时间与空间均为 $O(n)$。',tags=['树形 DP'],lessons=T)

add('CF1540B','把每对逆序的概率化为两条路径的公平竞速',
    '先均匀随机选根标记，再每次从与已标记部分相邻的未标点中均匀选一个，求最终标记顺序的逆序数期望，模十亿加七。',
    r'''期望按所有大编号u、小编号v分别累加它们谁先出现的概率。固定起点r，两条分支到u、v的剩余长度为a、b，忽略不推进这两条路径的标记后，每次推进哪边都是二分之一，所以p(a,b)由两个更短状态平均，先到u边界为一，先到v为零。用全点对距离算分叉位置，枚举起点与点对累加，再除起点数n。''',
    r'''生成的遍历序列并非等概率排列，也不一定是深度优先序。直接把全部合法序列当作等概率，会算错期望。可以按逆序对指标的线性性质，分别求大编号u先于小编号v的概率，再相加。

固定初始起点r，已标记点始终连通。两点u、v的路径从某个分叉点w开始分开；在w被标记以前，u、v都不可能先出现。w标记后，通往u和v的路径各有一个“下一步必须标记的点”处于候选前沿。

前沿中可能还有很多其它枝条，但两条关键路径的下一点每次被选中的机会相等。选择其它点只会推迟这次比较，不会移除这两个关键候选；条件在下一次确实推进其中一条路径时，两侧概率仍各一半。推进后继续同样比较，直到某个端点先到。

令p(a,b)为距离u还剩a步、距离v还剩b步时，u先到的概率。a为零，u已经出现，概率一；b为零则为零。两者正时

$$p(a,b)=\frac{p(a-1,b)+p(a,b-1)}2.$$

按a、b递增预处理。这里二分之一在模数域用二的逆元表示，不做整数除法。

还需求a、b。先用每点一次广搜求全部距离。记两点总距离为L，起点到二者的距离差为Delta：

$$L=dist(u,v).$$

$$\Delta=dist(r,u)-dist(r,v).$$

起点到分叉点的共同一段会在相减时消掉，因此a加b等于L、a减b等于Delta，得到

$$a=(L+\Delta)/2,\quad b=L-a.$$

树上这些值必为非负整数。枚举u编号大于v的所有对、以及全部n个等概率起点，累加p(a,b)，最后乘n的模逆元。原题模数为质数，且n至多二百，不会被模数整除，逆元存在。

总计立方时间，无需对每个根重新建立倍增祖先表，更无需枚举全部随机标记过程。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<vector<int>>distance(n,vector<int>(n,-1));
for(int root=0;root<n;++root){
    vector<int>order={root};distance[root][root]=0;
    for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(distance[root][v]<0){distance[root][v]=distance[root][u]+1;order.push_back(v);}}
}
const long long MOD=1000000007,HALF=500000004;
vector<vector<long long>>probability(n+1,vector<long long>(n+1));
for(int b=0;b<=n;++b) probability[0][b]=1;
for(int a=1;a<=n;++a) for(int b=1;b<=n;++b) probability[a][b]=(probability[a-1][b]+probability[a][b-1])*HALF%MOD;
long long answer=0;
for(int root=0;root<n;++root){
    for(int u=0;u<n;++u) for(int v=0;v<u;++v){
        int length=distance[u][v];
        int a=(distance[root][u]+length-distance[root][v])/2,b=length-a;
        answer+=probability[a][b];if(answer>=MOD) answer-=MOD;
    }
}
cout<<answer*modPower(n,MOD-2)%MOD<<'\n';''',
    '不是所有排列等概率；只为大编号先出现计逆序；忽略其它枝条后两关键候选等概率；祖先端点直接用边界；除二和除n均为模逆；距离式须取分叉两侧长度。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['树形 DP','期望与概率'],lessons=T+['probability','modular'],
    declarations=r'''long long modPower(long long base,long long exponent){
    const long long MOD=1000000007;long long answer=1;
    while(exponent){if(exponent&1) answer=answer*base%MOD;base=base*base%MOD;exponent>>=1;}
    return answer;
}''')
