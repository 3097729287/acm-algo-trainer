from core7_completion import add, DSU, SCC
from core7_completion_graph import LOWLINK

HLD=r'''
struct HLD{
 int n;vector<int>parent,depth,size,heavy,head,pos,at,order;
 HLD(const vector<vector<int>>&g,int root=0):n(g.size()),parent(n,-1),depth(n),size(n,1),heavy(n,-1),head(n),pos(n),at(n){
 parent[root]=root;order={root};for(int i=0;i<(int)order.size();i++){int v=order[i];for(int u:g[v])if(parent[u]<0){parent[u]=v;depth[u]=depth[v]+1;order.push_back(u);}}
 for(int i=n-1;i>0;i--){int v=order[i],p=parent[v];size[p]+=size[v];if(heavy[p]<0||size[v]>size[heavy[p]])heavy[p]=v;}
 vector<pair<int,int>>st={{root,root}};int timer=0;while(!st.empty()){auto [v,h]=st.back();st.pop_back();for(;v>=0;v=heavy[v]){head[v]=h;pos[v]=timer;at[timer++]=v;for(int u:g[v])if(parent[u]==v&&u!=heavy[v])st.push_back({u,u});}}
 }
 int lca(int a,int b)const{while(head[a]!=head[b]){if(depth[head[a]]<depth[head[b]])swap(a,b);a=parent[head[a]];}return depth[a]<depth[b]?a:b;}
 int jump(int v,int d)const{while(d>depth[v]-depth[head[v]]){d-=depth[v]-depth[head[v]]+1;v=parent[head[v]];}return at[pos[v]-d];}
 int distance(int a,int b)const{return depth[a]+depth[b]-2*depth[lca(a,b)];}
};
'''

add('P1451','四方向连通块计数',
    '每次找到尚未访问的非零格，就发现一个新细胞。用队列把与它四方向连通的所有非零格标记，最后统计启动搜索的次数。',
    '数字的具体大小不影响连接，只有零与非零的区别。按行列扫描，每遇到未标记的非零格，答案加一，从它开始广搜。\n\n搜索只走上下左右四个方向，不能走对角线；发现新格时立即标记，避免重复入队。一次搜索恰好遍历一个连通块，扫描会为每个块启动且仅启动一次，所以启动次数就是细胞数量。',
    '时间 O(nm)，空间 O(nm)。','字符零是 \'0\'；只走四方向；入队时标记。',r'''
int n,m;cin>>n>>m;vector<string>a(n);for(auto&s:a)cin>>s;int ans=0;int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};for(int i=0;i<n;i++)for(int j=0;j<m;j++)if(a[i][j]!='0'){ans++;queue<pair<int,int>>q;q.push({i,j});a[i][j]='0';while(!q.empty()){auto[x,y]=q.front();q.pop();for(int d=0;d<4;d++){int nx=x+dx[d],ny=y+dy[d];if(nx>=0&&nx<n&&ny>=0&&ny<m&&a[nx][ny]!='0'){a[nx][ny]='0';q.push({nx,ny});}}}}cout<<ans<<'\n';
''')

add('P1683','从入口搜索可达的安全格',
    '从 @ 开始进行四方向广搜，只经过安全格。每个格只计数一次，得到的就是能走过的最多瓷砖数。',
    '题目允许重复走同一块瓷砖，因此不需要求最长简单路径。只要格子与入口在同一个安全连通块中，就可以通过来回行走到达它。\n\n找到 @ 后入队并标记，每次取出一个格子计数，再把四邻中尚未访问的安全格入队。搜索结束时，这个连通块中的全部格子都已计算，障碍或其它安全块都不会被计入。输入先给宽 W 再给高 H，接下来读 H 行。',
    '时间 O(WH)，空间 O(WH)。','入口本身也计数；输入是宽、高；不能斜走。',r'''
int w,h;cin>>w>>h;vector<string>a(h);queue<pair<int,int>>q;for(int i=0;i<h;i++){cin>>a[i];for(int j=0;j<w;j++)if(a[i][j]=='@'){q.push({i,j});a[i][j]='#';}}int ans=0;int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};while(!q.empty()){auto[x,y]=q.front();q.pop();ans++;for(int d=0;d<4;d++){int nx=x+dx[d],ny=y+dy[d];if(nx>=0&&nx<h&&ny>=0&&ny<w&&a[nx][ny]=='.'){a[nx][ny]='#';q.push({nx,ny});}}}cout<<ans<<'\n';
''')

add('P6566','先找星座，再按大小汇总星系',
    '八方向搜索每个星座，得到它包含的星星数 s。令 count[s] 表示大小为 s 的星座个数，那么该星系大小为 s·count[s]。统计出现的 s 的数量及最大乘积。',
    '星座由位置连接决定，星系由星座大小决定，这两个步骤必须分别处理。先对所有 * 做八方向连通块搜索，每个块的格子数就是星座大小。\n\n得到一个大小 s 后令 count[s] 加一。大小相同但位置不同的星座属于同一星系，因此这个星系共含 s·count[s] 颗星；不同的 s 对应不同星系。遍历计数表，非零项数是星系数，最大乘积是最大星系大小。没有星星时两者都是零。\n\n矩阵可达一千五百行，使用显式队列，避免递归深度随星座大小增长。',
    '时间 O(NM)，空间 O(NM)。','相邻有八方向；最大的是星系总星数，不是单个星座大小；计数表按大小归类。',r'''
int n,m;cin>>n>>m;vector<string>a(n);for(auto&s:a)cin>>s;vector<int>cnt(n*m+1);for(int i=0;i<n;i++)for(int j=0;j<m;j++)if(a[i][j]=='*'){vector<int>q={i*m+j};a[i][j]='.';for(int k=0;k<(int)q.size();k++){int x=q[k]/m,y=q[k]%m;for(int dx=-1;dx<=1;dx++)for(int dy=-1;dy<=1;dy++){int nx=x+dx,ny=y+dy;if(nx>=0&&nx<n&&ny>=0&&ny<m&&a[nx][ny]=='*'){a[nx][ny]='.';q.push_back(nx*m+ny);}}}cnt[q.size()]++;}int systems=0,best=0;for(int s=1;s<=n*m;s++)if(cnt[s]){systems++;best=max(best,s*cnt[s]);}cout<<systems<<' '<<best<<'\n';
''')

add('P1123','按行枚举互不相邻的掩码',
    '每行用二进制掩码表示选中的列，先排除本行相邻的选择。相邻两行的掩码还必须在同列及左右斜列都不冲突，再做最大和动态规划。',
    '一行最多六格，能用一个小整数完整表示选择。若 mask 与 mask<<1 有公共位，说明同一行有相邻格，不能使用。\n\n设上一行选 prev，本行选 cur。竖直、左斜、右斜冲突分别对应 cur&prev、cur&(prev<<1)、cur&(prev>>1)，三者都必须为零。不相邻的行之间没有限制，所以状态只需记上一行的掩码。\n\n令 dp[mask] 为处理完上一行、其选择为 mask 的最大和；枚举所有相容的前后掩码更新。初始空行只允许掩码零，答案是最后一行所有状态的最大值。这个转移覆盖所有合法选择，并只产生合法选择。',
    '设合法行状态数为 S，时间 O(T·N·S²)，空间 O(S+NM)。','对角线也算相邻；允许一格不选；每组数据清空状态。',r'''
int T;cin>>T;while(T--){int n,m;cin>>n>>m;vector<vector<int>>a(n,vector<int>(m));for(auto&r:a)for(int&x:r)cin>>x;vector<int>states;for(int s=0;s<(1<<m);s++)if(!(s&(s<<1)))states.push_back(s);int z=states.size();vector<long long>dp(z,LLONG_MIN/4);dp[0]=0;for(int i=0;i<n;i++){vector<long long>ndp(z,LLONG_MIN/4);for(int j=0;j<z;j++){int cur=states[j];long long sum=0;for(int c=0;c<m;c++)if(cur>>c&1)sum+=a[i][c];for(int k=0;k<z;k++){int pre=states[k];if(!(cur&pre)&&!(cur&(pre<<1))&&!(cur&(pre>>1)))ndp[j]=max(ndp[j],dp[k]+sum);}}dp.swap(ndp);}cout<<*max_element(dp.begin(),dp.end())<<'\n';}
''')

add('P1256','全部白点同时开始广搜',
    '把所有白色像素作为距离零的起点一起入队。四方向广搜中第一次到达一个格子时，就得到它到最近白点的曼哈顿距离。',
    '单个白点到任意格子的最短四方向步数等于曼哈顿距离。若分别为每个黑点搜索，会重复遍历大量格子；将所有白点放在同一个队列中，相当于让距离一、二、三的波前同时扩展。\n\n所有起点距离设零，其余设为未访问。每次从距离 d 的格子扩展到未访问邻居，令其距离为 d+1。BFS 按距离非降序处理，因此不存在另一个白点能在首次赋值之后提供更短路线。',
    '时间 O(NM)，空间 O(NM)。','所有白点必须先入队；白点自身输出零；入队时赋距离。',r'''
int n,m;cin>>n>>m;vector<vector<int>>d(n,vector<int>(m,-1));queue<pair<int,int>>q;for(int i=0;i<n;i++)for(int j=0;j<m;j++){char c;cin>>c;if(c=='1'){d[i][j]=0;q.push({i,j});}}int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};while(!q.empty()){auto[x,y]=q.front();q.pop();for(int k=0;k<4;k++){int nx=x+dx[k],ny=y+dy[k];if(nx>=0&&nx<n&&ny>=0&&ny<m&&d[nx][ny]<0){d[nx][ny]=d[x][y]+1;q.push({nx,ny});}}}for(auto&r:d){for(int j=0;j<m;j++)cout<<r[j]<<(j+1==m?'\n':' ');}
''')

add('AT_abc271_f','在中间对角线连接两半异或路径',
    '从左上角走 n−1 步，按终点记录路径异或值的频次；再从右下角反向走 n−1 步。两半在同一个格子相遇时，结合中心格异或值即可查表累计答案。',
    '完整路径长二 n 减二，直接枚举有接近四的 n 次方种可能。所有完整路径都会恰好经过一个 i+j=n−1 的格子，可以在这里分成两半，每半最多二的 n−1 次方条路径。\n\n前半异或 A、后半异或 B 都包含中心格的值 x，所以整条路径异或为 A xor B xor x。要使它为零，需要 A=B xor x。为每个中心格分别记录前半异或频次，反向枚举后半时查对应频次并相加。\n\n每条路径由两半唯一确定，查表不会重复计数。路径数量可能超过三十二位，频次和答案使用 long long。',
    '平均时间 O(2^n)，空间 O(2^n)。','频次按相遇格区分；中心格不能重复异或两次；答案用六十四位。',r'''
int n;cin>>n;vector<vector<int>>a(n,vector<int>(n));for(auto&r:a)for(int&x:r)cin>>x;vector<unordered_map<int,long long>>cnt(n);function<void(int,int,int)>go=[&](int x,int y,int v){v^=a[x][y];if(x+y==n-1){cnt[x][v]++;return;}if(x+1<n)go(x+1,y,v);if(y+1<n)go(x,y+1,v);};go(0,0,0);long long ans=0;function<void(int,int,int)>back=[&](int x,int y,int v){v^=a[x][y];if(x+y==n-1){auto it=cnt[x].find(v^a[x][y]);if(it!=cnt[x].end())ans+=it->second;return;}if(x)back(x-1,y,v);if(y)back(x,y-1,v);};back(n-1,n-1,0);cout<<ans<<'\n';
''')

add('P1363','同一周期格记录首次到达的真实坐标',
    '在有限周期网格上搜索，却为每格保留第一次到达时的无限平面坐标。如果再次到达同一周期格、真实坐标却不同，就找到可以不断重复的跨周期路线。',
    '只记录行列取模后的访问状态会漏掉跨周期移动。为每个周期格记录首次到达的真实整数坐标，扩展时真实坐标加方向，再用规范化取模判断对应格是否为墙。\n\n如果新坐标与某格保存的真实坐标不同，两者相差一个非零周期平移。连接这两种到达方式得到一条跨周期路线；地图周期重复，这条路线可以平移后不断重走，于是能够走到无限远。\n\n反之，如果每个周期格始终只有同一个真实坐标可达，实际可达位置最多 nm 个，无法无限走远。因此发现这种冲突就输出 Yes，全部搜索完仍无冲突则输出 No。多组地图读到文件结束。',
    '每组时间 O(nm)，空间 O(nm)。','负坐标的余数要规范化；比较真实坐标；输入直到 EOF。',r'''
int n,m;while(cin>>n>>m){vector<string>a(n);pair<int,int>start;for(int i=0;i<n;i++){cin>>a[i];for(int j=0;j<m;j++)if(a[i][j]=='S')start={i,j};}vector<char>seen(n*m);vector<pair<int,int>>first(n*m);queue<pair<int,int>>q;q.push(start);seen[start.first*m+start.second]=1;first[start.first*m+start.second]=start;bool yes=false;int dx[4]={1,-1,0,0},dy[4]={0,0,1,-1};while(!q.empty()&&!yes){auto[x,y]=q.front();q.pop();for(int d=0;d<4;d++){int nx=x+dx[d],ny=y+dy[d],r=(nx%n+n)%n,c=(ny%m+m)%m,id=r*m+c;if(a[r][c]=='#')continue;if(seen[id]){if(first[id]!=pair<int,int>{nx,ny}){yes=true;break;}}else{seen[id]=1;first[id]={nx,ny};q.push({nx,ny});}}}cout<<(yes?"Yes":"No")<<'\n';}
''')

add('P2024','三个副本维护食物链关系',
    '为每种动物建立本类、它吃的类、吃它的类三个副本。每句话先查矛盾，合法时合并三组对应关系；不合法只计数，不改并查集。',
    '食物链有三种循环关系，用 x、x+n、x+2n 表示 x 所在类及循环向后的两类。统一约定“x 吃 y”对应 x 与 y+n 同类。\n\n同类语句若发现 x 已与 y+n 或 y+2n 相连，就有矛盾；否则将三组同偏移副本合并。“x 吃 y”若发现 x 与 y 或 y+2n 同类，也有矛盾；否则合并 (x,y+n)、(x+n,y+2n)、(x+2n,y)。\n\n编号越界，以及说自己吃自己，立即作为假话。必须先检查再合并，错误语句不能污染后续判断。并查集的等价关系完整保留所有已接受语句的传递推论。',
    '时间 O((n+k)α(n))，空间 O(n)。','三个副本方向一致；假话不合并；编号越界也是假话。',r'''
int n,k;cin>>n>>k;DSU d(3*n);int ans=0;while(k--){int type,x,y;cin>>type>>x>>y;x--;y--;if(x<0||x>=n||y<0||y>=n){ans++;continue;}if(type==1){if(d.find(x)==d.find(y+n)||d.find(x)==d.find(y+2*n)){ans++;continue;}for(int j=0;j<3;j++)d.join(x+j*n,y+j*n);}else{if(d.find(x)==d.find(y)||d.find(x)==d.find(y+2*n)){ans++;continue;}d.join(x,y+n);d.join(x+n,y+2*n);d.join(x+2*n,y);}}cout<<ans<<'\n';
''',DSU)

add('P2835','缩点后统计入度为零的分量',
    '互相可达的人中只需给一张光盘。将强连通分量缩成有向无环图，每个入度为零的分量必须直接获得一张，且这些光盘足以传播给所有人。',
    '若两名营员互相可达，资料可以沿转交链在他们之间传播，因此整个强连通分量只需一个人先获得资料。缩点后不再有环。\n\n入度为零的分量没有外部资料来源，必须至少刻录一张给它，这给出下界。反过来，DAG 的每个结点都可以沿反向边追溯到某个源点，所以给所有源分量各一张即可覆盖全图，达到这个下界。\n\n按调查表方向建边：i 愿意让 j 拷贝，就建 i 到 j。多条跨分量边不影响“入度是否为零”的判断。',
    '时间 O(N+E)，空间 O(N+E)。','有向边按资料传播方向；统计源分量，不是汇分量；每行以零结束。',r'''
int n;cin>>n;SCC s(n);for(int i=0;i<n;i++){int x;while(cin>>x&&x)s.edge(i,x-1);}s.build();vector<char>in(s.count);for(int i=0;i<n;i++)for(int j:s.g[i])if(s.component[i]!=s.component[j])in[s.component[j]]=1;cout<<count(in.begin(),in.end(),0)<<'\n';
''',SCC)

add('P3385','从一号点执行 Bellman–Ford',
    '只让一号点距离为零，其余保持不可达，进行至多 n 轮松弛。第 n 轮仍能更新，说明存在从一号点可达的负环；提前没有更新则不存在。',
    '从一号点出发的最短简单路径至多包含 n−1 条边。如果不存在可达负环，所有有效最短路都可去掉非负回路，因此 n−1 轮松弛已足够。第 n 轮仍能改进的路径必然借助某个可达负环。\n\n初始化只有顶点一可达，松弛前跳过不可达起点，这样不会把其它连通区域的负环误报。非负输入边要添加两个方向，负边只添加输入方向；m 是输入记录数，不是最终边数。\n\n每轮按边顺序原地松弛可能传播多条边，但不会使无负环图在第 n 轮产生更新。没有更新时可以提前结束。',
    '时间 O(Tnm)，空间 O(n+m)。','仅判断一号点可达的负环；负边不自动反向；距离用 long long。',r'''
int T;cin>>T;while(T--){int n,m;cin>>n>>m;vector<tuple<int,int,int>>e;while(m--){int u,v,w;cin>>u>>v>>w;u--;v--;e.push_back({u,v,w});if(w>=0)e.push_back({v,u,w});}const long long INF=1LL<<60;vector<long long>d(n,INF);d[0]=0;bool negative=false;for(int round=1;round<=n;round++){bool changed=false;for(auto[u,v,w]:e)if(d[u]!=INF&&d[v]>d[u]+w){d[v]=d[u]+w;changed=true;}if(!changed)break;if(round==n)negative=true;}cout<<(negative?"YES":"NO")<<'\n';}
''')

add('P11280','比较两人到根的最短距离',
    '从根广搜得到所有距离。Terry 到根的距离不大于 Jom 时输出 Terry，否则输出 Jom。相等时 Terry 先移动，能先到根。',
    '记两人到根距离为 da、db。若 da≤db，Terry 每步沿最短路前进。在 Terry 的第 t 步之前，Jom 到根的距离至少是 db−t+1，而 Terry 要走到的点距根为 da−t，后者严格更小，因此不会走进 Jom 所在位置，最终能先到根。\n\n若 da>db，Jom 每步沿最短路到根，然后一直停在那里。Terry 无论走哪条路都至少需要 da 步，无法在 Jom 之前到根，此后根被占据，Terry 也不能进入。因此这个判据充分且必要。\n\n重边与自环不会改变 BFS 的正确性。开头按题目要求输出固定的 I\'m here!，再回答全部询问。',
    '预处理时间 O(n+m)，每问 O(1)，空间 O(n+m)。','相等由先手获胜；先输出指定问候语；Jom 主动走到 Terry 位置不算捕获。',r'''
int n,m,r;cin>>n>>m>>r;r--;vector<vector<int>>g(n);while(m--){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}vector<int>d(n,-1),q={r};d[r]=0;for(int i=0;i<(int)q.size();i++)for(int u:g[q[i]])if(d[u]<0){d[u]=d[q[i]]+1;q.push_back(u);}cout<<"I'm here!\n";int Q;cin>>Q;while(Q--){int a,b;cin>>a>>b;cout<<(d[a-1]<=d[b-1]?"Terry":"Jom")<<'\n';}
''')

add('P1606','消去已有荷叶路线后计算最短方案数',
    '把水面、起点和终点作为新图结点。从每个结点经过任意已有荷叶，找到下一片需新增荷叶的水面或终点，并只连一条边。在新图上 BFS，最短边数减一是新增数量，最短路条数是摆放方案数。',
    '不能直接对原网格最短跳跃计数：已有荷叶间可以绕行，同一组新增荷叶会对应许多跳跃路线。应消去这些不花代价的内部路线。\n\n新图只保留所有水面、起点和终点。对每个源结点，沿马步遍历可直接或经已有荷叶到达的位置；遇到其它水面或终点就记录为下一站，不继续穿过该水面。同一目标只连一条边，所以经过已有荷叶的不同走法被合并。\n\n新图的一条起终路径每经过一个内部结点就新增一片荷叶，因此新增数是路径边数减一。用 BFS 求最短边数，并在相同最短距离时累加条数。最小摆放方案不含多余水面；若同一最小水面集合能以两种不同次序连接起终点，就能从分歧处绕去至少一个水面，与最小性矛盾。因此这种压缩后的最短路径与最小摆放方案一一对应。',
    '设格子数 V=MN，时间 O(V²)，空间 O(V²)。','同一源目标只能连一次；已有荷叶不是新增荷叶；无解只输出 −1。',r'''
int n,m;cin>>n>>m;int N=n*m,start=-1,goal=-1;vector<int>a(N),id(N,-1),cells;for(int i=0;i<N;i++){cin>>a[i];if(a[i]==3)start=i;if(a[i]==4)goal=i;if(a[i]==0||a[i]>=3){id[i]=cells.size();cells.push_back(i);}}int z=cells.size();vector<vector<int>>g(z);int dx[8]={1,1,-1,-1,2,2,-2,-2},dy[8]={2,-2,2,-2,1,-1,1,-1};for(int k=0;k<z;k++){vector<char>seen(N);vector<int>q={cells[k]};seen[cells[k]]=1;for(int h=0;h<(int)q.size();h++){int v=q[h],x=v/m,y=v%m;for(int d=0;d<8;d++){int nx=x+dx[d],ny=y+dy[d];if(nx<0||nx>=n||ny<0||ny>=m)continue;int u=nx*m+ny;if(a[u]==2||seen[u])continue;seen[u]=1;if(id[u]>=0)g[k].push_back(id[u]);else q.push_back(u);}}}int s=id[start],t=id[goal];vector<int>d(z,-1),q={s};vector<long long>ways(z);d[s]=0;ways[s]=1;for(int i=0;i<(int)q.size();i++){int v=q[i];for(int u:g[v]){if(d[u]<0){d[u]=d[v]+1;q.push_back(u);}if(d[u]==d[v]+1)ways[u]+=ways[v];}}if(d[t]<0)cout<<-1<<'\n';else cout<<d[t]-1<<'\n'<<ways[t]<<'\n';
''')

add('P2656','强连通块收集完后做 DAG 最长路',
    '同一个强连通块里的每条边都能反复经过，将其衰减到零前的蘑菇总数计入块权。跨块边只能经过一次，保留初始数量，缩点后从起点做最长路。',
    '在强连通块内，可以从任意位置绕回任意边，也能在收集完后到达指定出口。恢复系数小于一，非零蘑菇在有限次经过后归零，因此能收完全部内部边，不存在互斥选择。逐边模拟 w=floor(w·k) 的衰减，把所有采集值相加为块权。\n\n跨块边不能再返回，否则两个块应当属于同一个 SCC，所以只能使用一次，贡献是初始 w。缩点图为 DAG，设 dp[c] 是到达 c 并收完 c 内蘑菇的最大总数，用 dp[next]=max(dp[next],dp[c]+跨边数量+块权[next]) 转移。只初始化起点所属块，其它块保持不可达。\n\n恢复系数最多一位小数，将它转成整数十分比再乘除，避免 0.7 等浮点误差影响向下取整。',
    '时间 O(n+m log W)，其中 W 为初始边权上界；空间 O(n+m)。','内部边累加全部衰减值；跨块边只取一次；不可达块不参与转移。',r'''
int n,m;cin>>n>>m;SCC s(n);struct E{int u,v,w,k;};vector<E>edges;for(int i=0;i<m;i++){int u,v,w;string k;cin>>u>>v>>w>>k;u--;v--;int rate=0;auto dot=k.find('.');if(dot!=string::npos&&dot+1<k.size())rate=k[dot+1]-'0';edges.push_back({u,v,w,rate});s.edge(u,v);}int start;cin>>start;start--;s.build();vector<long long>value(s.count),dp(s.count,LLONG_MIN/4);vector<vector<pair<int,int>>>g(s.count);vector<int>in(s.count);for(auto e:edges){int u=s.component[e.u],v=s.component[e.v];if(u==v){long long w=e.w;while(w){value[u]+=w;w=w*e.k/10;}}else{g[u].push_back({v,e.w});in[v]++;}}queue<int>q;for(int i=0;i<s.count;i++)if(!in[i])q.push(i);dp[s.component[start]]=value[s.component[start]];long long ans=dp[s.component[start]];while(!q.empty()){int v=q.front();q.pop();ans=max(ans,dp[v]);for(auto[u,w]:g[v]){if(dp[v]>=0)dp[u]=max(dp[u],dp[v]+w+value[u]);if(!--in[u])q.push(u);}}cout<<ans<<'\n';
''',SCC)

add('P4822','已用卡数分层的 Dijkstra',
    '状态记录城市和已使用卡片数。走一条路可以保持层数、支付原价，也可以在卡片够用时进入下一层、支付一半。对这些状态跑 Dijkstra，取终点各层的最小距离。',
    '同一座城市已经用掉多少卡，会影响后续可选择的路线，因此不能只为城市保存一个距离。把状态写为 (城市,used)，used 从零到 K。\n\n每条原边产生两种转移：不用卡走到 (邻点,used)，花费 w；若 used<K，使用一张卡走到 (邻点,used+1)，花费 w/2。每条路最多用一张卡，恰好对应一次转移最多跨一层。所有费用非负，可以用 Dijkstra。\n\n题目不要求用完卡，所以答案取终点所有层的最小值。原边保证偶数，除二是精确整数。',
    '时间 O((nK+mK) log(nK))，空间 O(nK+m)。','同一条路不能连续叠卡；允许少用卡；道路双向。',r'''
int n,m,K;cin>>n>>m>>K;vector<vector<pair<int,int>>>g(n);while(m--){int u,v,w;cin>>u>>v>>w;u--;v--;g[u].push_back({v,w});g[v].push_back({u,w});}const long long INF=1LL<<60;vector<long long>d(n*(K+1),INF);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[0]=0;q.push({0,0});while(!q.empty()){auto[dist,state]=q.top();q.pop();if(dist!=d[state])continue;int used=state/n,v=state%n;for(auto[u,w]:g[v])for(int take=0;take<=1&&used+take<=K;take++){int next=(used+take)*n+u;long long nd=dist+(take?w/2:w);if(nd<d[next]){d[next]=nd;q.push({nd,next});}}}long long ans=INF;for(int k=0;k<=K;k++)ans=min(ans,d[k*n+n-1]);cout<<ans<<'\n';
''')

add('P6833','枚举三条最短路的公共汇合点',
    '分别从 O、A、B 跑三次带点权的 Dijkstra，距离包含起终点权。枚举分叉格 v，答案为 min(dO[v]+dA[v]+dB[v]−2R[v])。',
    '两条路径的并集可以去掉环，得到连接 O、A、B 的树。在这棵树中，存在一个汇合点 v，使到三个端点的三条分支内部互不相交。最优树的分支费用至少是对应最短路距离，三个距离都包含 v，故要减去两次 R[v]。这给出某个候选值不大于最优费用。\n\n反过来，对任意 v 取三条最短路，它们的并集连通且覆盖三个端点。因为所有点权非负，并集费用不会超过三个距离之和减去重复计算的两次 R[v]，所以最优费用又不大于每个候选值。上下界一致，公式成立，即使最短路额外重叠也不影响证明。\n\n移动到邻格的代价取邻格点权，源距离初始化为源点权。数据规模要求六十四位距离。',
    '时间 O(nm log(nm))，空间 O(nm)。','三份距离都含起点；汇合点减两次权；允许零权格；答案用 long long。',r'''
int n,m,a,b,c;cin>>n>>m>>a>>b>>c;int N=n*m;vector<long long>w(N);for(auto&x:w)cin>>x;auto dijkstra=[&](int s){const long long INF=1LL<<62;vector<long long>d(N,INF);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[s]=w[s];q.push({d[s],s});while(!q.empty()){auto[dist,v]=q.top();q.pop();if(d[v]!=dist)continue;int x=v/m,y=v%m;for(int u:{x? v-m:-1,x+1<n?v+m:-1,y?v-1:-1,y+1<m?v+1:-1})if(u>=0&&d[u]>dist+w[u]){d[u]=dist+w[u];q.push({d[u],u});}}return d;};auto x=dijkstra(a-1),y=dijkstra((n-1)*m+b-1),z=dijkstra((n-1)*m+c-1);long long ans=LLONG_MAX;for(int v=0;v<N;v++)ans=min(ans,x[v]+y[v]+z[v]-2*w[v]);cout<<ans<<'\n';
''')

add('P9813','累计损伤作为最短路的第二维',
    '把状态设为顶点和累计损伤，只扩展新损伤严格小于 k 的边。按时间跑 Dijkstra，取终点所有合法损伤状态的最短时间。',
    '最快到达某点的路线可能损伤很高，后面无法继续，因此每点需要分别保留不同损伤值的最佳时间。k 不超过二百，直接建立 n·k 个状态。\n\n从 (v,h) 沿边走到 (u,h+损伤)，仅当新损伤<k 时允许；距离增加边的时间。边时间为正，可以使用 Dijkstra。任意合法原路线与状态图路线一一对应，最终对终点所有损伤取最小即可。\n\n损伤为零的边同样合法，不能要求损伤每步严格上升。没有终点状态可达时输出 −1。',
    '时间 O((nk+mk) log(nk))，空间 O(nk+m)。','限制是严格小于 k；道路双向；零损伤边保留。',r'''
int K,n,m;cin>>K>>n>>m;vector<vector<array<int,3>>>g(n);while(m--){int u,v,t,h;cin>>u>>v>>t>>h;u--;v--;g[u].push_back({v,t,h});g[v].push_back({u,t,h});}int s,t;cin>>s>>t;s--;t--;const long long INF=1LL<<60;vector<long long>d(n*K,INF);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[s]=0;q.push({0,s});while(!q.empty()){auto[dist,state]=q.top();q.pop();if(d[state]!=dist)continue;int h=state/n,v=state%n;for(auto[u,cost,damage]:g[v])if(h+damage<K){int next=(h+damage)*n+u;if(d[next]>dist+cost){d[next]=dist+cost;q.push({d[next],next});}}}long long ans=INF;for(int h=0;h<K;h++)ans=min(ans,d[h*n+t]);cout<<(ans==INF?-1:ans)<<'\n';
''')

add('UVA116','从右向左 DP，并按下一行编号打破平局',
    'dp[r][c] 表示从该格走到最后一列的最小代价。把下一列的三个可选行排序，费用相同时选编号最小者，记录路径；最后选择最小费用且起始行最小的起点。',
    '从右到左计算，转移到下一列的上一行、本行、下一行，行号首尾循环。先将三个候选行按编号排序，只在费用严格更小时替换选择，这样平价时保留行号最小的候选。\n\n为什么只看下一行即可得到字典序最小路径？当前位置固定，第一处可能不同就是下一行；下一行较小的路径字典序必较小。同一下一行的后缀已由 DP 保证最优且字典序最小。因此局部打破平局可以归纳到整条路径。\n\n起点也从小行号扫描，只在费用严格降低时替换。读到文件结束，每组输出一行从一开始的行号序列，再输出总费用。',
    '每组时间 O(mn)，空间 O(mn)。','行循环取模；负权也能 DP；费用相等按行号而非几何方向选择。',r'''
int m,n;while(cin>>m>>n){vector<vector<long long>>a(m,vector<long long>(n)),dp=a;vector<vector<int>>next(m,vector<int>(n));for(auto&r:a)for(auto&x:r)cin>>x;for(int r=0;r<m;r++)dp[r][n-1]=a[r][n-1];for(int c=n-2;c>=0;c--)for(int r=0;r<m;r++){array<int,3>rows={(r+m-1)%m,r,(r+1)%m};sort(rows.begin(),rows.end());int best=rows[0];for(int u:rows)if(dp[u][c+1]<dp[best][c+1])best=u;dp[r][c]=a[r][c]+dp[best][c+1];next[r][c]=best;}int root=0;for(int r=1;r<m;r++)if(dp[r][0]<dp[root][0])root=r;int r=root;for(int c=0;c<n;c++){cout<<r+1<<(c+1==n?'\n':' ');if(c+1<n)r=next[r][c];}cout<<dp[root][0]<<'\n';}
''')

add('CF59E','BFS 状态保留前两个顶点',
    '下一步是否合法取决于上一个点和当前点，因此用 (prev,cur) 作为状态。沿未被禁止的三元组转移并保存前驱，第一次到终点时还原最短路线。',
    '仅记录当前点会把不同来路混在一起：同一顶点从不同前驱进入，允许的下一步可能不同。状态 (prev,cur) 足以检查禁止三元组 (prev,cur,next)。起点使用一个虚拟前驱，第一次走边不受三元组约束。\n\n每次转移走一条边，普通 BFS 给出最短边数。前驱数组同时作为访问标记，记录从哪个状态到达，以便逆序恢复顶点。终点可以由任意前驱进入，第一次出队的终点状态就是最短答案。\n\n禁止三元组按三进制位置式编码成六十四位整数后存哈希集合；状态用整数编码，避免为每条候选路线复制完整路径。',
    '时间 O(n²+Σdeg(v)²+k)，空间 O(n²+m+k)；实际只扩展可达的有向边状态。','状态不能只记当前点；禁止关系有方向；无解输出 −1。',r'''
int n,m,k;cin>>n>>m>>k;vector<vector<int>>g(n);while(m--){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}unordered_set<long long>bad;auto key=[&](int a,int b,int c){return (1LL*a*n+b)*n+c;};while(k--){int a,b,c;cin>>a>>b>>c;bad.insert(key(a-1,b-1,c-1));}vector<int>parent((n+1)*n,-2),q={n*n};parent[n*n]=-1;int goal=-1;for(int i=0;i<(int)q.size();i++){int state=q[i],pre=state/n,v=state%n;if(v==n-1){goal=state;break;}for(int u:g[v])if(!bad.count(key(pre,v,u))){int next=v*n+u;if(parent[next]==-2){parent[next]=state;q.push_back(next);}}}if(goal<0){cout<<-1<<'\n';return 0;}vector<int>path;for(int s=goal;s>=0;s=parent[s])path.push_back(s%n+1);reverse(path.begin(),path.end());cout<<path.size()-1<<'\n';for(int i=0;i<(int)path.size();i++)cout<<path[i]<<(i+1==(int)path.size()?'\n':' ');
''',checker='forbidden-triples')

add('P3403','同余最短路统计可达楼层',
    '以最小步长 x 为模数，求每个余数最小可达楼层。之后不断加 x，得到该余数的全部可达楼层，用等差数列计数。',
    '任意可达楼层再加 x 仍可达，因此对每个模 x 余数，只需知道最小可达值 dist[r]。从一楼出发，对“加 y”“加 z”建立余数图边，边权就是实际增加的楼层数；加 x 不改变余数且不会改善最小值，可以省略。\n\n用 Dijkstra 求余数图最短路，初始 dist[1%x]=1。若 dist[r]≤h，该余数贡献 floor((h−dist[r])/x)+1。不同余数不重叠，直接求和。\n\n把三种步长排序以减小状态数。h 可能达到有符号六十四位上界，松弛时先判断 dist≤h−step，避免加法溢出；超过楼顶的状态无须访问。',
    '设 x 为最小步长，时间 O(x log x)，空间 O(x)。','从一楼开始；不会把零楼算入；大整数加法先检查上界。',r'''
long long h;array<int,3>a;cin>>h>>a[0]>>a[1]>>a[2];sort(a.begin(),a.end());int x=a[0];vector<long long>d(x,-1);priority_queue<pair<long long,int>,vector<pair<long long,int>>,greater<pair<long long,int>>>q;d[1%x]=1;q.push({1,1%x});while(!q.empty()){auto[v,r]=q.top();q.pop();if(d[r]!=v)continue;for(int step:{a[1],a[2]})if(h>=step&&v<=h-step){long long nd=v+step;int nr=(r+step)%x;if(d[nr]<0||nd<d[nr]){d[nr]=nd;q.push({nd,nr});}}}long long ans=0;for(long long v:d)if(v>=0&&v<=h)ans+=(h-v)/x+1;cout<<ans<<'\n';
''')

add('P3398','检查路径的 LCA 是否在另一条路径上',
    '两条树路径相交，当且仅当至少一条路径的 LCA 位于另一条路径上。用距离等式判断点是否在路径上，树链剖分预处理后每问对数时间。',
    '设两条路径为 a—b 与 c—d，最高点分别为 x=lca(a,b)、y=lca(c,d)。若它们相交，取交集中的一个点 z。x、y 都是 z 的祖先，必然可比较深度；较深的那个最高点位于从较浅最高点到 z 的路径上，所以属于两条路径的交集。反向结论显然成立。\n\n点 v 在 u—w 路径上，等价于 dist(u,v)+dist(v,w)=dist(u,w)。树上路径唯一，走出路径再折回一定多走正步数。\n\n代码用重链维护 LCA，避免递归遍历深链。若 x 在 c—d 上或 y 在 a—b 上，输出 Y，否则输出 N。',
    '预处理 O(n)，每问 O(log n)，空间 O(n)。','距离按边数；端点相交也算；输出大写 Y 或 N。',r'''
int n,q;cin>>n>>q;vector<vector<int>>g(n);for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}HLD tree(g);auto on=[&](int v,int a,int b){return tree.distance(a,v)+tree.distance(v,b)==tree.distance(a,b);};while(q--){int a,b,c,d;cin>>a>>b>>c>>d;a--;b--;c--;d--;cout<<(on(tree.lca(a,b),c,d)||on(tree.lca(c,d),a,b)?'Y':'N')<<'\n';}
''',HLD)

add('CF796D','多源 BFS 为每个城市划分警局',
    '将所有不同的警局城市同时入队，为每个城市分配最近警局。两个不同归属区域之间的树边全部关闭，区域内部保留搜索树边。',
    '设有 s 个不同的警局城市。关闭 r 条树边会产生 r+1 个连通块，每块至少含一个警局，因此 r≤s−1。\n\n从所有警局同时 BFS，第一次访问城市时继承前驱的归属。这个城市到所属警局的路线是原树最短路，题目保证最近警局距离不超过 d，所以归属区域内也满足距离限制。不同归属的端点之间的边关闭后，恰好得到 s 个连通区域，共关闭 s−1 条边，达到上界。\n\n重复警局只放入队列一次。距离 d 无须参与扩展上限：完整多源 BFS 已分配给每个点最近的警局，原题保证的覆盖条件确保所有分配合法。',
    '时间 O(n+k)，空间 O(n)。','同城多个警局只算一个源；保留首次访问的归属；输出原边编号。',r'''
int n,k,d;cin>>n>>k>>d;vector<int>owner(n,-1),q;for(int i=0;i<k;i++){int p;cin>>p;p--;if(owner[p]<0){owner[p]=p;q.push_back(p);}}vector<vector<pair<int,int>>>g(n);vector<pair<int,int>>e;for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;e.push_back({a,b});g[a].push_back({b,i});g[b].push_back({a,i});}for(int i=0;i<(int)q.size();i++){int v=q[i];for(auto[u,id]:g[v])if(owner[u]<0){owner[u]=owner[v];q.push_back(u);}}vector<int>cut;for(int i=0;i<n-1;i++)if(owner[e[i].first]!=owner[e[i].second])cut.push_back(i+1);cout<<cut.size()<<'\n';for(int i=0;i<(int)cut.size();i++)cout<<cut[i]<<(i+1==(int)cut.size()?'\n':' ');if(cut.empty())cout<<'\n';
''',checker='police-forest')

add('P2324','错位棋子下界剪枝的 IDA*',
    '逐步增加允许移动次数，用“不在目标位置的非空棋子数”作为剩余步数下界。每次交换空格和一个马步可达棋子，跳过立即撤销上一步的移动。最多搜索到十五步。',
    '每次只移动一个非空棋子，因此最多修正一个错位棋子；错位非空棋子数 h 不会大于真正剩余步数，是可用的剪枝下界。空格不计入 h，避免一次交换被错误地当成需要两步。\n\n对限制 limit 进行深搜，若 used+h>limit 立即返回。交换时只更新被移动棋子的错位贡献；回溯时恢复棋盘。限制从 h 开始递增，第一次找到目标的限制即为最短解。\n\n马步会改变空格的棋盘颜色，所以解长奇偶等于初始空格到中心的颜色差，可只枚举对应奇偶的 limit。禁止立即退回上一步可以去掉无用往返，不会删掉任何最短解。十五步仍找不到时输出 −1。',
    '最坏指数时间，深度最多十五且使用可采纳下界剪枝；空间 O(25+15)。','下界不计空格；每次交换后恢复；目标中心为 *。',r'''
int T;cin>>T;string goal="111110111100*110000100000";while(T--){string a;for(int i=0;i<5;i++){string row;cin>>row;a+=row;}int hole=a.find('*'),h=0;for(int i=0;i<25;i++)if(a[i]!='*'&&a[i]!=goal[i])h++;vector<vector<int>>g(25);for(int i=0;i<25;i++)for(auto[dx,dy]:vector<pair<int,int>>{{1,2},{1,-2},{-1,2},{-1,-2},{2,1},{2,-1},{-2,1},{-2,-1}}){int x=i/5+dx,y=i%5+dy;if(x>=0&&x<5&&y>=0&&y<5)g[i].push_back(x*5+y);}function<bool(int,int,int,int,int)>dfs=[&](int p,int prev,int used,int lower,int limit){if(used+lower>limit)return false;if(a==goal)return true;if(used==limit)return false;vector<pair<int,int>>moves;for(int u:g[p])if(u!=prev)moves.push_back({lower-(a[u]!=goal[u])+(a[u]!=goal[p]),u});sort(moves.begin(),moves.end());for(auto[nh,u]:moves){swap(a[p],a[u]);bool found=dfs(u,p,used+1,nh,limit);swap(a[p],a[u]);if(found)return true;}return false;};int parity=(hole/5+hole%5)%2,ans=-1;for(int limit=h;limit<=15;limit++)if(limit%2==parity&&dfs(hole,-1,0,h,limit)){ans=limit;break;}cout<<ans<<'\n';}
''')

add('CF231E','压缩环后统计路径上的环数',
    '将每个环压成一个结点，得到树。环结点权值为一，其它结点为零。查询压缩树路径上的权值和 c，答案为 2^c。',
    '本题的 simple path 特别定义为“边不能重复”，允许顶点重复。这意味着主路线经过一个环时，可以选择环的两个方向；即使进入和离开用同一个环上顶点，也可以选择不绕环或绕完整环。这两种选择对应不同边集。\n\n每个顶点最多属于一个环，因此把非桥边连接的顶点合并，就把每个环压成独立结点，桥构成一棵树。沿压缩后两点之间的唯一路线，所有环各自独立贡献两种选择；树外分支要来回经过同一条桥，违反边不重复，所以不产生额外选择。答案是二的环数次方。\n\n预处理根到各点的环数前缀和。路径环数为 pref[u]+pref[v]−2pref[lca]+weight[lca]，包含路径端点所在环。用重链查询 LCA。',
    '预处理 O(n+m)，每问 O(log n)，空间 O(n+m)。','按题面允许顶点重复；端点所在环也计数；LCA 权值补回一次。',r'''
int n,m;cin>>n>>m;Lowlink graph(n);for(int i=0;i<m;i++){int a,b;cin>>a>>b;graph.edge(a-1,b-1);}graph.build();DSU d(n);for(int i=0;i<m;i++)if(!graph.bridge[i])d.join(graph.edges[i].first,graph.edges[i].second);vector<int>id(n,-1),belong(n);int z=0;for(int i=0;i<n;i++){int r=d.find(i);if(id[r]<0)id[r]=z++;belong[i]=id[r];}vector<int>w(z);for(int i=0;i<n;i++)if(d.size[d.find(i)]>1)w[belong[i]]=1;vector<vector<int>>g(z);for(int i=0;i<m;i++)if(graph.bridge[i]){int a=belong[graph.edges[i].first],b=belong[graph.edges[i].second];g[a].push_back(b);g[b].push_back(a);}HLD tree(g);vector<int>pref(z),power(n+1,1);for(int v:tree.order)pref[v]=w[v]+(v?pref[tree.parent[v]]:0);for(int i=1;i<=n;i++)power[i]=2LL*power[i-1]%1000000007;int q;cin>>q;while(q--){int a,b;cin>>a>>b;int u=belong[a-1],v=belong[b-1],l=tree.lca(u,v);cout<<power[pref[u]+pref[v]-2*pref[l]+w[l]]<<'\n';}
''',LOWLINK+DSU+HLD)

add('CF576B','用树中心给出必要条件与构造',
    '若置换有不动点，以它为中心建星形树。否则必须存在一个二元环，且所有置换环长度均为偶数；用该二元环作中心边，其它偶环的点交替连向两个中心。',
    '树的中心是一个顶点或一条边，任何保持边关系的置换都必须保持中心。若中心是顶点，它必须是不动点，有不动点时直接建星形树即可。\n\n没有不动点时，中心只能是一条被交换端点的边，因此必须有一个二元环。删除中心边得到两半树，置换每次交换两半，于是所有顶点的置换周期必须为偶数。这给出必要条件。\n\n条件成立时取二元环 (a,b) 为中心边。对每个其它偶长置换环，沿置换顺序交替把点连到 a、b。置换会同时交换中心并走到下一个环点，所以每条边被映成另一条已存在的边。图连通且有 n−1 条边，因此是一棵满足条件的树。',
    '时间 O(n)，空间 O(n)。','没有不动点时二元环必需；其它奇环不可行；中心二元环不再重复挂边。',r'''
int n;cin>>n;vector<int>p(n);int fixed=-1;for(int i=0;i<n;i++){cin>>p[i];p[i]--;if(p[i]==i)fixed=i;}if(fixed>=0){cout<<"YES\n";for(int i=0;i<n;i++)if(i!=fixed)cout<<fixed+1<<' '<<i+1<<'\n';return 0;}vector<char>seen(n);vector<vector<int>>cycles;int center=-1;bool ok=true;for(int i=0;i<n;i++)if(!seen[i]){vector<int>c;for(int v=i;!seen[v];v=p[v]){seen[v]=1;c.push_back(v);}if(c.size()%2)ok=false;if(c.size()==2)center=cycles.size();cycles.push_back(c);}if(!ok||center<0){cout<<"NO\n";return 0;}int a=cycles[center][0],b=cycles[center][1];cout<<"YES\n"<<a+1<<' '<<b+1<<'\n';for(int j=0;j<(int)cycles.size();j++)if(j!=center)for(int i=0;i<(int)cycles[j].size();i++)cout<<cycles[j][i]+1<<' '<<(i%2?b:a)+1<<'\n';
''',checker='invariant-tree')

add('P4408','直径两端与第三点的最坏绕行',
    '求树直径端点 A、B，保留所有点到两端的距离。答案是直径长度加上 max_v min(dist(A,v),dist(B,v))。',
    '给定三处位置 A、B、C，先去较近朋友家再去另一家，最坏耗时为 dist(A,B)+min(dist(C,A),dist(C,B))。要让这个值最大，可以将朋友家取为一组树直径端点。\n\n使用树的直径替换引理：对任意三点形成的三叉子树，若两处朋友不是直径端点，将分支延伸或替换到直径两端，不会减小“朋友间距离加家到较近朋友距离”的最大值。也可以把三点投影到直径路径证明：直径外任意分支高度不超过其投影到直径两端距离的较小者，否则会产生更长直径；把这个上界代入三叉子树的三段长度即可得到公式的上界。取朋友为直径两端又能达到公式，因此上下界相等。\n\n从任一点找最远点 A，再从 A 找最远点 B，得到直径。树上只有一条路，遍历累加边权即可求距离，不需要 Dijkstra。再从 B 遍历一次，枚举 C 即可。',
    '时间 O(n)，空间 O(n)。','边权可为零；答案和路径长度用 long long；按较近的朋友先找。',r'''
int n,m;cin>>n>>m;vector<vector<pair<int,long long>>>g(n);while(m--){int a,b;long long w;cin>>a>>b>>w;a--;b--;g[a].push_back({b,w});g[b].push_back({a,w});}auto distances=[&](int s){vector<long long>d(n,-1);vector<int>q={s};d[s]=0;for(int i=0;i<(int)q.size();i++)for(auto[u,w]:g[q[i]])if(d[u]<0){d[u]=d[q[i]]+w;q.push_back(u);}return d;};auto d=distances(0);int A=max_element(d.begin(),d.end())-d.begin();auto x=distances(A);int B=max_element(x.begin(),x.end())-x.begin();auto y=distances(B);long long extra=0;for(int i=0;i<n;i++)extra=max(extra,min(x[i],y[i]));cout<<x[B]+extra<<'\n';
''')

add('P2783','去重后缩环为树，再查询路径点数',
    '先合并重复边，再用桥判断找出所有处于环中的连接，将这些非桥边两端合并。压缩图上两点路径的顶点数等于距离加一，最后转成二进制输出。',
    '题目特别规定两个点之间的平行边不构成环。因此先将端点排序、去掉重复无向边，之后才做 lowlink；直接把重边当返祖边会错误合并两个碳。\n\n简单无向图中，一条边不是桥当且仅当它位于某个环上。合并所有非桥边的端点，正好执行“同环顶点合并”，多个相交环也会按传递性合为一个结点。剩下的桥构成树。\n\n原点映射到压缩结点，路径边数为 depth[u]+depth[v]−2depth[lca]，题目统计包含两端的顶点数，所以加一。反复取最低二进制位后倒序输出，不能把十进制数字当作二进制拼接。',
    '时间 O(m log m+(n+q) log n)，空间 O(n+m)。','先去重再判桥；相同压缩点的答案为二进制 1；路径点数需要加一。',r'''
int n,m;cin>>n>>m;vector<pair<int,int>>e;while(m--){int a,b;cin>>a>>b;a--;b--;if(a>b)swap(a,b);if(a!=b)e.push_back({a,b});}sort(e.begin(),e.end());e.erase(unique(e.begin(),e.end()),e.end());Lowlink graph(n);for(auto[a,b]:e)graph.edge(a,b);graph.build();DSU d(n);for(int i=0;i<(int)e.size();i++)if(!graph.bridge[i])d.join(e[i].first,e[i].second);vector<int>ids(n,-1),belong(n);int z=0;for(int i=0;i<n;i++){int r=d.find(i);if(ids[r]<0)ids[r]=z++;belong[i]=ids[r];}vector<vector<int>>g(z);for(int i=0;i<(int)e.size();i++)if(graph.bridge[i]){int a=belong[e[i].first],b=belong[e[i].second];g[a].push_back(b);g[b].push_back(a);}HLD tree(g);int q;cin>>q;while(q--){int a,b;cin>>a>>b;int value=tree.distance(belong[a-1],belong[b-1])+1;string ans;while(value){ans+=char('0'+value%2);value/=2;}reverse(ans.begin(),ans.end());cout<<ans<<'\n';}
''',LOWLINK+DSU+HLD)

add('P8025','把一次移动拆成向上和向下两段',
    '设当前位置为 u，目标为 v，公共祖先为 l。步数够走完整条路径就到 v；否则若步数不超过 u 到 l 的距离，直接向上跳；再否则从 v 反向跳到本次应停的位置。',
    '树上最短路唯一，由 u 向上到 lca(u,v)，再向下到 v。记两段长度为 A、B，总长 D=A+B。若 t≥D，当前位置变为 v。\n\n当 t<D 且 t≤A，答案是 u 的第 t 级祖先；当 A<t<D，答案在向下段，等价于 v 的第 D−t 级祖先。这样每条指令只需一次 LCA 与一次祖先查询。\n\n重链上的顶点按深度连续编号。在一条链内可以直接用数组定位祖先，跨链时跳到链首的父亲；每次跨过轻边，所在子树大小至少翻倍，所以最多跨 O(log n) 条链。全部预处理采用迭代遍历，以适应百万点长链。',
    '预处理 O(n)，每条指令 O(log n)，空间 O(n)。','t 可能超过路径长；每条指令以上一次停点为起点；数组编号从零转换。',r'''
int n,u,k;cin>>n>>u>>k;u--;vector<vector<int>>g(n);for(int i=1;i<n;i++){int a,b;cin>>a>>b;a--;b--;g[a].push_back(b);g[b].push_back(a);}HLD tree(g);while(k--){int v;long long t;cin>>v>>t;v--;int l=tree.lca(u,v),A=tree.depth[u]-tree.depth[l],D=A+tree.depth[v]-tree.depth[l];if(t>=D)u=v;else if(t<=A)u=tree.jump(u,t);else u=tree.jump(v,D-t);cout<<u+1<<(k?' ':'\n');}
''',HLD)
