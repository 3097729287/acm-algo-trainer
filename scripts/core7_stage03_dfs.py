"""Search-unit articles follow the actual state graph, not the folder's name."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer']
G=A+['graphs','queue-stack','functions']
R=A+['recursion','functions']

add('AT_arc001_2','把温度偏移看成图上的点，广度优先搜索',
    '温度从 A 改为 B，一次可以加减一、五或十度。A、B 都在零到四十，求最少按键次数，中途可以先越过目标再返回。',
    r'''每个温度偏移是一个状态，六种按键各连一条代价一的边，从偏移零开始 BFS，首次到达 B−A 就得到最少次数。直接每次调一度至多四十次，任何最优路径都不超过四十步，每步偏移至多十，因此只搜相对起点 [−400,400] 不会漏掉最优解。''',
    r'''从十九到二十八，差九。先加十再减一只要两次，说明不能只向目标方向按，也不能简单把差分成若干十、五、一后只做同向操作。

以相对起点的温度偏移为顶点，按一次按钮就是偏移加上 −10、−5、−1、1、5、10 中的一个。所有边费用都是一次按键，BFS 按步数从小到大扩展：零步的起点先出队，一步可达状态随后出队，再是两步，因此第一次访问目标就是最少次数。一个状态首次到达后无须再次加入，后到不会更短。

温度没有给出中间状态的边界，不能擅自只搜索 [A,B]。本程序使用有证明的有限范围：因为 |A−B|≤40，连续按一度总有一个不超过四十次的方案。任意不超过四十次的路径，每个中间偏移的绝对值都不超过四百。跑出这个范围的路径不可能优于现有上界，所以删掉它们不会删掉最优解。

数组下标用“偏移加四百”表示，起点下标四百、目标下标 B−A+400。下标只是保存状态的位置，不是额外给温度增加四百度。初始 A=B 时，起点出队立即得到零。

操作、范围和样例已按 [AtCoder 原题](https://atcoder.jp/contests/arc001/tasks/arc001_2)核对。''',
    r'''int a,b;cin>>a>>b;const int shift=400,size=801;
vector<int>distance(size,-1);queue<int>todo;distance[shift]=0;todo.push(shift);
int change[]={-10,-5,-1,1,5,10};
while(!todo.empty()){
    int u=todo.front();todo.pop();
    if(u==b-a+shift){cout<<distance[u]<<'\n';return 0;}
    for(int delta:change){int v=u+delta;
        // 四十次的现成方案给出搜索边界，不限制只能朝目标走。
        if(0<=v&&v<size&&distance[v]==-1){distance[v]=distance[u]+1;todo.push(v);}
    }
}''',
    '允许越过目标；有限边界来自步数上界；相同温度答案为零。',
    '共有八百零一个状态，每个最多六条边；在本题固定范围内时间、空间均为 $O(1)$。',tags=['BFS'],lessons=G,key='bfs')

add('AT_arc001_2','枚举十度与五度的净次数，余差用一度补足',
    '用加减一、五、十的按钮把零到四十之间的 A 调到 B，求最少按键次数。',
    r'''相反方向的同类按键可以相互抵消，最优方案无需同时加十和减十，也无需同时加五和减五。枚举十度净次数 t、五度净次数 f，剩余差 D−10t−5f 用一度补，费用为 |t|+|f|+|D−10t−5f|。最优至多四十次，故 t、f 只需枚举 −40 到 40。''',
    r'''加减操作可以任意交换先后，最终温度只取决于净变化。若某方案同时按了三次加十、一次减十，删掉一对相反按钮后净变化不变，次数却减少二；最优方案不会保留这种抵消。五度与一度按钮同理。

用 t 表示“加十次数减去减十次数”，f 表示五度净次数。它们贡献 10t+5f，剩余净变化必须为 D−10t−5f，其中 D=B−A。实现给定净次数至少需要相应绝对值次，反过来只往净方向按就恰好达到，因此固定 t、f 的最小费用为

$$|t|+|f|+|D-10t-5f|.$$

无需再枚举一度次数，因为它已被总变化等式唯一确定。任意最优按键序列都能消去同类抵消，落入某个枚举项；每个枚举项又确实可以执行，所以取最小值恰是答案。

直接用一度按钮不超过四十次，因此最优方案的十度、五度净次数绝对值也不超过四十，枚举范围足够。枚举中可能出现超过四十次的合法方案，它们只是不会成为最小值，不必额外过滤。温差可以为负，同一个公式直接处理。''',
    r'''int a,b;cin>>a>>b;int difference=b-a,answer=abs(difference);
for(int ten=-40;ten<=40;++ten)for(int five=-40;five<=40;++five){
    // 一度按钮的净次数由总温差决定，不必成为第三重循环。
    int one=difference-10*ten-5*five;
    answer=min(answer,abs(ten)+abs(five)+abs(one));
}
cout<<answer<<'\n';''',
    '净次数允许负数；费用取绝对值；不能把温差的余数全部只往同一个方向补。',
    '枚举八十一乘八十一种净次数，在本题固定范围内时间、空间均为 $O(1)$。',tags=['枚举'],lessons=A+['basic-arithmetic','enumeration'],key='net_counts')

add('P1331','找四连通块，用外接矩形面积检查船形',
    '棋盘上的每艘船应为填满的矩形，船与船不能四向接触；对角接触允许。检查摆放是否合法，合法时统计船数。',
    r'''BFS 找每个 # 的四连通块，统计格数与最小、最大行列。若格数等于外接矩形面积，块内恰填满一个矩形，是一艘合法船；否则有凹口或弯折，输出 Bad placement.。四向接触的 # 已属于同一块，因此不同合法块之间自动满足不接触。''',
    r'''一列连续多个 # 也是合法矩形船，不能要求长宽相等。样例中既有二乘二的船，也有细长船；“方形”应按这种矩形块来检查。只有上下左右接触会连接船，斜对角的 # 不因此合并。

先从一个尚未访问的 # 出发，沿四个方向访问所有相连的 #，得到一个四连通块。访问时记下它的格数 count，以及行最小值、行最大值、列最小值、列最大值。它们围出的外接矩形有 maxRow−minRow+1 行、maxCol−minCol+1 列，面积是这两个数量的乘积。

块中的每个格子都在这个外接矩形内，且各格互不重复，因此格数最多等于面积。相等时没有空余格，恰是一个填满的矩形；小于时必有缺口，不能把它算成一艘矩形船。若想拆成几艘，拆出的船又会四向相接，同样违反规则。

每个合法连通块贡献一艘船。不同块之间不会四向相接，否则 BFS 已把它们放在同一块里。棋盘可能达到一百万格，代码用显式队列而不递归，并把访问过的 # 改成点，避免重复加入。''',
    r'''int rows,columns;cin>>rows>>columns;vector<string>grid(rows);for(auto &row:grid)cin>>row;int ships=0;
int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
for(int r=0;r<rows;++r)for(int c=0;c<columns;++c)if(grid[r][c]=='#'){
    vector<pair<int,int>>todo={{r,c}};grid[r][c]='.';
    int min_r=r,max_r=r,min_c=c,max_c=c;
    for(size_t at=0;at<todo.size();++at){auto [x,y]=todo[at];
        min_r=min(min_r,x);max_r=max(max_r,x);min_c=min(min_c,y);max_c=max(max_c,y);
        for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
            if(0<=nx&&nx<rows&&0<=ny&&ny<columns&&grid[nx][ny]=='#'){grid[nx][ny]='.';todo.push_back({nx,ny});}
        }
    }
    // 四连通块全部位于外接矩形中，格数等于面积才说明没有缺口。
    if((long long)todo.size()!=1LL*(max_r-min_r+1)*(max_c-min_c+1)){cout<<"Bad placement.\n";return 0;}
    ++ships;
}
cout<<"There are "<<ships<<" ships.\n";''',
    '船可以是长方形或单格；只连四方向；输出的大小写和末尾句点要完整。',
    '时间、空间均为 $O(RC)$。',tags=['BFS','连通块计数'],lessons=G+['strings','bindings'],exact=True)

add('P1605','搜索当前路径，返回时撤销访问标记',
    '障碍不可走，每格在一条路径中最多经过一次，统计从起点到终点的全部路径数，路径不要求最短。',
    r'''DFS 枚举下一步四个方向。进入一个非终点格时标记正在当前路径中，递归尝试所有未被占用的邻格，返回前撤销标记；到终点直接贡献一条路径并停止延伸。标记只约束当前路线，不能永久禁止其它路线使用这个格。''',
    r'''两条不同路径可能都经过同一格，只要各自在自己的路线里不重复就合法。因此这里的 visited 不是“历史上搜索到过”，而是“当前递归链已经经过”。一次分支返回后必须撤销，才能尝试另一条路线。

在位置 (x,y) 依次检查上下左右。下一格需在棋盘内、没有障碍、没有出现在当前路径中。每个合法方向递归计算后续路径数并相加。到达终点时已经形成一条完整方案，贡献一并立即返回，不能继续绕开终点再回来计数。

为什么不重不漏？任意合法路径的第一步必是枚举的某个邻格，之后的每一步也都会被相同规则保留，所以它会被搜到。不同搜索分支首次分歧处走向不同格，得到的完整路径不同，因此每条恰数一次。

每格最多一次使递归深度不超过 N*M，n、m 至多五，适合在小网格上搜索；路径数量与尝试量仍是指数级，不能把这种计全部简单路径的方法说成线性 BFS。若起终点相同，零步路线贡献一；若终点为障碍且与起点不同，任何分支都不会进入它，答案为零。''',
    r'''cin>>rows>>columns>>obstacles;int sx,sy;cin>>sx>>sy>>finish_x>>finish_y;
for(int i=0;i<obstacles;++i){int x,y;cin>>x>>y;blocked[x][y]=true;}
cout<<walk(sx,sy)<<'\n';''',
    'visited 只表示当前路径，返回时撤销；求全部方案不是最短路；到终点不继续扩展。',
    r'设空格数为 V，搜索树最坏为指数级，可用 $O(4^V)$ 作宽松上界；递归与标记空间 $O(NM)$。',
    tags=['DFS','递归'],lessons=R+['graphs','arrays'],
    declarations=r'''int rows,columns,obstacles,finish_x,finish_y;
bool blocked[7][7],visited[7][7];
long long walk(int x,int y){
    if(x==finish_x&&y==finish_y)return 1;
    visited[x][y]=true;long long answer=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
        if(1<=nx&&nx<=rows&&1<=ny&&ny<=columns&&!blocked[nx][ny]&&!visited[nx][ny])answer+=walk(nx,ny);
    }
    visited[x][y]=false; // 退出当前路线，把格子还给其它分支。
    return answer;
}''')

add('P2802','把剩余血量加入状态，按步数广度优先搜索',
    '初始六点血，每移动一格先减一；到鼠标格且仍活着时补回六，鼠标可反复取。求最少步数安全到家，血量变零时即使在补给或家门口也失败。',
    r'''状态为位置与剩余血量，BFS 每次走一格。血量只有一时不能再移动；否则先减一，到鼠标格再设为六。不同血量的同一位置是不同状态，分别记录访问。所有移动都费一步，首次到家即最短，搜索耗尽则输出负一。''',
    r'''离补给还有一步但只剩一点血时，不能用“到了就补满”救活：这一步先让血量变零，角色已经死亡。到家同样必须还剩正血量。反过来，鼠标格允许重复补给，不能拿一次就从地图删掉。

只按位置标记会出错。两条路线可能先后到同一格，先到时只剩一点血，后到时剩五点，后者才能继续走更远。于是保存 (行,列,血量) 三项，血量只取一到六。相同三元状态首次到达的步数最少，未来可选行动也完全相同，因此后到者无需再扩展。

从一个状态尝试相邻格时，先检查边界和障碍，再让新血量等于旧血量减一。只有它大于零，才允许踏入；踏入鼠标格后再补到六。起点状态血量六、步数零，普通格、起点和家都不补血。

每个合法状态的每条边都是一次移动，BFS 按步数分层，第一次出队的家状态就是最少时间。即使路线经过环，也只可能产生有限的六倍格数个状态，搜索会结束。''',
    r'''int n,m;cin>>n>>m;vector<vector<int>>grid(n,vector<int>(m));int sx=0,sy=0;
for(int i=0;i<n;++i)for(int j=0;j<m;++j){cin>>grid[i][j];if(grid[i][j]==2){sx=i;sy=j;}}
vector<vector<vector<int>>>distance(n,vector<vector<int>>(m,vector<int>(7,-1)));
queue<tuple<int,int,int>>todo;todo.push({sx,sy,6});distance[sx][sy][6]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y,hp]=todo.front();todo.pop();int steps=distance[x][y][hp];
    if(grid[x][y]==3){cout<<steps<<'\n';return 0;}if(hp==1)continue;
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(nx<0||nx>=n||ny<0||ny>=m||grid[nx][ny]==0)continue;
        int next_hp=hp-1; // 先扣血，存活后才能拾取补给。
        if(grid[nx][ny]==4)next_hp=6;
        if(distance[nx][ny][next_hp]==-1){distance[nx][ny][next_hp]=steps+1;todo.push({nx,ny,next_hp});}
    }
}
cout<<-1<<'\n';''',
    '先扣血再补给；家也不能零血到达；血量不同的同格状态不能混在一个 visited 中。',
    '至多六倍格数个状态，时间、空间均为 $O(nm)$。',tags=['BFS'],lessons=G+['bindings','arrays'])

add('CF1059B','把所有合法印章的边框取并集',
    '一次只能在完整三乘三区域的八格边框涂墨，中心不涂。判断能否从全空白得到目标图。',
    r'''枚举每个合法中心，若它周围八格在目标中全为 #，就可以盖这个章，把八格记入新图。最后新图与目标完全相同则 YES，否则 NO。盖合法章只增加目标本来要黑的格，章之间可以重叠，所以把所有合法章都盖上不会造成冲突。''',
    r'''一个合法印章的中心可以在目标中是点，也可以是 #：本次盖章不影响中心，中心为黑可能由另一个章的边框覆盖。不能把“中心不涂”误解为“目标中心必须白”。

先找所有八格边框都位于目标 # 的三乘三区域。只要某个边框位置在目标中是点，这个章就永远不能使用，因为墨不能擦除。于是任何正确盖章方案使用的章，必然全在上述候选中。

把全部候选章都盖到一个新空白图上。每次只染目标中本来为黑的位置，所以不会把目标中的点染黑。不同章重叠只是重复涂墨，不妨碍其它操作。因此若并集恰好覆盖全部目标 #，按这个顺序全部盖章就得到一个具体可行方案。

若还有一个目标 # 没被并集覆盖，意味着所有允许使用的章都碰不到它，任何候选子集也无法覆盖，因此一定无解。这同时证明了必要性与充分性，无须回溯选择盖哪些章。每个中心最多检查八格、涂八格，总成本为网格面积的常数倍。''',
    r'''int n,m;cin>>n>>m;vector<string>target(n),painted(n,string(m,'.'));for(auto &row:target)cin>>row;
for(int r=1;r+1<n;++r)for(int c=1;c+1<m;++c){bool allowed=true;
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy)if((dx||dy)&&target[r+dx][c+dy]!='#')allowed=false;
    if(!allowed)continue;
    // 中心不涂，也不要求它在目标图中必须为空。
    for(int dx=-1;dx<=1;++dx)for(int dy=-1;dy<=1;++dy)if(dx||dy)painted[r+dx][c+dy]='#';
}
cout<<(painted==target?"YES":"NO")<<'\n';''',
    '中心不参与边框检查；盖章必须完整在网格内；合法章可以全部盖，不必寻找互不重叠的一组。',
    '时间、空间均为 $O(nm)$。',tags=['枚举','构造'],lessons=A+['strings','enumeration','construction'])

add('P1019','最短合法重叠的记忆化搜索，用剩余增长作上界',
    '每个给定单词最多用两次，相邻词须有非空首尾重叠，重叠不能吞掉任意一整词。从指定首字母开始，求最长接龙长度。原题已标注最坏数据下搜索性能没有保证。',
    r'''预处理每对词最短的正重叠，长度严格小于两词长度；它增长最多，后续能接什么词只取决于末词，不受本次重叠长度影响。DFS 记录末词和各词已用零、一、二次。缓存每个状态还能接出的最大增长，并用剩余次数能贡献的乐观增长作分支上界。算法求值精确，最坏状态仍指数级，不能承诺所有二十词输入都在原时限内通过。''',
    r'''把 beast 接 astonish，共用 ast 后只增加后词剩下的部分。若两词有多种重叠，选择更短的那个会留下更长接龙，而末尾仍然是同一个完整后词，已使用次数也相同，后续选择没有改变。因此只保留最短的合法正重叠不会损失最优解。

合法长度 k 必须满足 1≤k<min(两词长度)，并且前词长度 k 的后缀等于后词长度 k 的前缀。不能用零长度把无关单词拼上，也不能让重叠吞掉任意一整词。一个单词仍可与自己相接，只要有合法的真前后缀重叠，而且其使用次数还不足二。

搜索状态需要末词 last 与每个输入位置的使用次数 used。末词决定可接的后继，各词次数决定剩余名额，接龙更早的字符不会再影响合法性。每种次数只有三种值，可用三进制数编码整个计数向量；例如三词的使用次数 [1,0,2] 编成 1+0*3+2*9=19，再用第二词一次只需给编码加三。n≤20，三进制编码乘 n 后仍在 long long 内。把键写成 code*n+last，整除 n 可恢复 code、余数恢复 last，不会把不同状态混在一起。缓存的是“从当前状态继续接龙，最多还能增加多少长度”，不含已经拼好的前缀长度。相同状态的后续问题完全一致，可以直接复用这个值。每个转移都增加某词使用次数，状态不会成环。

再为每个后继词 j 预处理所有入边里最大的增长 gain[j]。把每个词剩余次数乘 gain[j] 后求和，得到当前状态剩余增长的乐观上界 upper：它假定每次都能挑到最有利前驱，可能做不到，却绝不会低估。当前选择 j 后，该分支的上界为本次实际增长加 upper−gain[j]。若它已不超过本状态已找到的最佳后续增长，就无须再搜该分支。缓存只在本状态所有可能更优的分支处理完后写入，保存的是精确值。优先试增长大的边，有助于尽早得到强的局部下界。

**原题的数据提醒须保留。** 这些剪枝只减少实际搜索，不改变最坏的指数性质。若实际访问 S 个状态，状态扩展约 O(nS)，而可能状态数上界 n*3^n 对 n=20 仍很大。这里提供原语义的精确搜索与可复查的小域验证，不把通过本地测试表述为所有最大输入均能满足时限。''',
    r'''cin>>n;words.resize(n);for(auto &word:words)cin>>word;char first;cin>>first;
edges.resize(n);used.assign(n,0);maximum_gain.assign(n,0);power.resize(n);long long value=1;
for(int i=0;i<n;++i){power[i]=value;value*=3;}
for(int i=0;i<n;++i)for(int j=0;j<n;++j){
    for(int overlap=1;overlap<(int)min(words[i].size(),words[j].size());++overlap)
        if(words[i].substr(words[i].size()-overlap)==words[j].substr(0,overlap)){
            int gain=(int)words[j].size()-overlap;edges[i].push_back({gain,j});maximum_gain[j]=max(maximum_gain[j],gain);break;
        }
}
for(auto &list:edges)sort(list.rbegin(),list.rend());
for(int i=0;i<n;++i)if(words[i][0]==first){used[i]=1;answer=max(answer,(int)words[i].size()+continuation(i,power[i]));used[i]=0;}
cout<<answer<<'\n';''',
    '每个输入词单独有两次名额；只保留最短合法正重叠；剪枝是性能优化，不构成最坏时间保证。',
    r'最长词长 L 时预处理 $O(n^2L^2)$；若实际访问 S 个状态，哈希平均条件下搜索 $O(nS)$、缓存空间 $O(S+n^2)$，最坏状态数仍为 $n3^n$。',
    tags=['DFS','记忆化搜索','递归'],lessons=R+['strings','string-tools','maps','sort','dp','bindings'],
    declarations=r'''int n,answer=0;vector<string>words;vector<vector<pair<int,int>>>edges;
vector<int>used,maximum_gain;vector<long long>power;
unordered_map<long long,int>memo;
int continuation(int last,long long code){
    long long key=code*n+last;auto at=memo.find(key);
    if(at!=memo.end())return at->second;
    int upper=0,best=0;for(int i=0;i<n;++i)upper+=(2-used[i])*maximum_gain[i];
    for(auto [gain,next]:edges[last])if(used[next]<2){
        // 去掉本次使用的乐观增长，再加上这条边的实际增长。
        if(gain+upper-maximum_gain[next]<=best)continue;
        ++used[next];best=max(best,gain+continuation(next,code+power[next]));--used[next];
        if(best==upper)break;
    }
    return memo[key]=best; // 此处缓存精确的后续增长，与此前的拼接长度无关。
}''')

add('P1219','逐行放皇后，按列递增搜索保证字典序',
    '每行每列恰放一个皇后，任意对角线至多一个。按列序列的字典序输出前三种方案，并统计全部方案数，n 在六到十三。',
    r'''按行递归，每行从小到大试列，列、行加列、行减列分别标记占用。到第 n 行后得到完整方案，前三个立即输出，同时总数加一。列递增且每次先完整搜索当前前缀，所以完整方案自然按字典序出现，无须存下全部方案再排序。''',
    r'''两个皇后互不同行由“每层只处理一行”保证。剩下需检查同列与两种斜线：一条斜线上的行加列相同，另一方向的行减列相同，因此用三组布尔标记就能常数时间判断新位置是否合法。

代码行列从零计数。行加列在零到 2n−2，行减列可能为负，加 n 后平移到非负数组下标。这个平移只为存储方便，不改变“差相同就在同一斜线”的判断。

进入一个选择后把三项占用标真，递归处理下一行，返回时撤销。不能只撤销列而忘记斜线，否则后续分支会把已经拿走的皇后仍当作障碍。

字典序比较先看第一行列号，再看第二行，依此类推。搜索恰按这种顺序：第一行先试最小列，其全部后续先搜完，再尝试第一行更大的列；每个深层也如此。因此前三个完整方案就是题目要的前三个，可直接输出后不保存其它方案。但搜索仍须继续，才能统计总数，不能输出三种后提前结束。

例如 n=6，共四个方案，只输出其中前三行摆法，最后再输出总数四。输出列号需把零起始值加一。''',
    r'''cin>>n;place(0);cout<<solutions<<'\n';''',
    '列和两组斜线都要撤销；输出三种后仍统计其余；列号输出加一。',
    r'每行列不重复，搜索节点可用 $O(n\cdot n!)$ 作宽松上界，剪去斜线冲突后实际更少；额外空间 $O(n)$。',
    tags=['DFS','递归'],lessons=R+['arrays','enumeration'],exact=True,
    declarations=r'''int n,position[15];bool column[15],downward[30],upward[30];long long solutions=0;
void place(int row){
    if(row==n){
        if(solutions<3)for(int i=0;i<n;++i)cout<<position[i]+1<<(i+1==n?'\n':' ');
        ++solutions;return;
    }
    for(int c=0;c<n;++c)if(!column[c]&&!downward[row+c]&&!upward[row-c+n]){
        position[row]=c;column[c]=downward[row+c]=upward[row-c+n]=true;
        place(row+1);
        column[c]=downward[row+c]=upward[row-c+n]=false; // 完整撤销本行占用。
    }
}''')

add('P1825','把踏入传送门与瞬移合成一次移动',
    '四向移动花一时间，踏入大写字母格必须立刻传到同字母另一格，传送不花时间。求从 @ 到 = 的最短时间。',
    r'''先记录每对传送端。BFS 扩展相邻格，若是字母，就把本次移动的终点替换为另一端，整条边仍只花一时间。访问标记与距离记在传送后的落脚点；到达另一端后可以走离它，不会在同一次移动里无限传回。''',
    r'''样例先向右走到 W，花一时间，立即到上面的 W，不额外花时间；再向右、向上，各花一，共三。若把传送也算一步，就会多算；若允许踏入 W 后不传送，又加入了题目没有的选择。

一次完整行动是“走到相邻格；若它是入口，立刻传到配对位置”。把这个行动合并成一条代价一的边，就仍是一张等权有向图，可以普通 BFS，不必把门另画成可选的零费用边而漏掉强制性。

站在传送后的端点时，这一次瞬移已经结束，下一步可以走到它旁边。只有以后再次从相邻格踏入某个端点，才触发新一次传送，不能立刻把刚落脚的位置反复当作新入口。代码在选出邻格后最多替换一次坐标，正好表达这个规则。

同一个门的两端仍是两个不同状态。从 A 端进入会落在 B 端，反过来则落在 A，接下来可走的邻格不同，所以不能把两端一起标成“门已使用”。每个落脚格首次到达最短，后续无须重复入队。''',
    r'''int n,m;cin>>n>>m;vector<string>grid(n);vector<pair<int,int>>port[26];int sx=0,sy=0;
for(int i=0;i<n;++i){cin>>grid[i];for(int j=0;j<m;++j){char c=grid[i][j];if(c=='@'){sx=i;sy=j;}if('A'<=c&&c<='Z')port[c-'A'].push_back({i,j});}}
vector<vector<int>>distance(n,vector<int>(m,-1));queue<pair<int,int>>todo;todo.push({sx,sy});distance[sx][sy]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y]=todo.front();todo.pop();if(grid[x][y]=='='){cout<<distance[x][y]<<'\n';return 0;}
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(nx<0||nx>=n||ny<0||ny>=m||grid[nx][ny]=='#')continue;
        char c=grid[nx][ny];
        if('A'<=c&&c<='Z'){
            auto &ends=port[c-'A'];pair<int,int>entered={nx,ny};auto destination=(ends[0]==entered?ends[1]:ends[0]);
            nx=destination.first;ny=destination.second; // 同一次行动只传送一次。
        }
        if(distance[nx][ny]==-1){distance[nx][ny]=distance[x][y]+1;todo.push({nx,ny});}
    }
}
cout<<-1<<'\n';''',
    '踏入门必须传送且只传一次；两端是不同落脚状态；访问标记放在传送后位置。',
    '时间、空间均为 $O(nm)$。',tags=['BFS'],lessons=G+['strings','bindings'])

add('P2895','记录各格最早毁灭时刻，搜索首次到达永久安全点',
    '陨石在指定时刻毁掉自身及四邻格，毁灭不可恢复。起点为原点，每秒向第一象限四邻移动，求最早逃到永不毁灭的位置。',
    r'''每格记录所有影响它的陨石时刻的最小值，未受影响记为无穷。BFS 到达邻格的时刻必须严格小于它的毁灭时刻；首次到毁灭时刻为无穷的格，立刻返回时间。不是只要暂时活着就算逃出。影响范围最多到坐标三百零一，搜零到三百零二即可。''',
    r'''同一个格子被多颗陨石影响时，最早一次已经把它永久毁掉，后来的时刻没有恢复作用，故必须取最小值。到达时刻恰好等于毁灭时刻也会被击中，判定是严格小于。

当前安全与永久安全不同。一个时刻五才毁掉的格，时刻二可以经过，却不能在这里结束逃生。BFS 只有到达从未受任何陨石影响的格，才能报告成功。

对固定格，越早到达越有利：所有通行约束都是“到达时间早于某个上限”，后到不会得到任何新通路。所以每格只保存首次到达，不必把时间加入无限状态。初始原点若时刻零已毁灭，不能先移动逃走；若原点永远安全，答案就是零。

坐标范围为什么有限？陨石坐标不超过三百，四邻影响最多到三百零一。因此横坐标或纵坐标达到三百零二的格一定永久安全。任何往更远处逃的路径，之前就已走过这种安全格；搜索零到三百零二的方框足以找到最优终点，不会漏掉更远处的更优答案。

第一象限包含两条坐标轴，坐标零可以走，负坐标不能走。''',
    r'''const int size=303,inf=1000000000;vector<vector<int>>destroy(size,vector<int>(size,inf));int m;cin>>m;
int dr[]={0,1,-1,0,0},dc[]={0,0,0,1,-1};
for(int i=0;i<m;++i){int x,y,t;cin>>x>>y>>t;for(int d=0;d<5;++d){int nx=x+dr[d],ny=y+dc[d];if(0<=nx&&nx<size&&0<=ny&&ny<size)destroy[nx][ny]=min(destroy[nx][ny],t);}}
if(destroy[0][0]==0){cout<<-1<<'\n';return 0;}
vector<vector<int>>distance(size,vector<int>(size,-1));queue<pair<int,int>>todo;todo.push({0,0});distance[0][0]=0;
while(!todo.empty()){auto [x,y]=todo.front();todo.pop();if(destroy[x][y]==inf){cout<<distance[x][y]<<'\n';return 0;}
    for(int d=1;d<5;++d){int nx=x+dr[d],ny=y+dc[d],arrival=distance[x][y]+1;
        // 等于毁灭时刻也来不及，只有严格更早才能进入。
        if(0<=nx&&nx<size&&0<=ny&&ny<size&&distance[nx][ny]==-1&&arrival<destroy[nx][ny]){distance[nx][ny]=arrival;todo.push({nx,ny});}
    }
}
cout<<-1<<'\n';''',
    '毁灭取最早时刻；到达需严格早于毁灭；永久安全才是终点；原点时刻零已毁灭直接失败。',
    r'设固定网格边长为 L=303，时间 $O(M+L^2)$、空间 $O(L^2)$。',tags=['BFS'],lessons=G+['coordinates','bindings'])

add('SP4580','等式拆成两个有序三元组，二分统计重数',
    '从给定互异整数集合中选有序六元组，元素允许重复，满足 (a*b+c)/d−e=f 且 d 非零，统计方案数。',
    r'''等式等价于 a*b+c=d*(e+f)。枚举所有左三元组的值并排序；再枚举 d、e、f，跳过 d=0，二分查右值在左数组中的出现次数并累加。同值的不同三元组必须保留，不能去重，答案用 long long。''',
    r'''逐个枚举六个数有 n⁶ 种，n=100 时不可行。把等式移项并乘以非零 d，可得到

$$ab+c=d(e+f).$$

这里是有序六元组，a、b 交换即使数值相同也代表对相应位置的另一种选择；同一个集合元素还可以在多个位置使用。因此三重循环每个位置都完整枚举集合，不限制下标顺序，不排除相同值。

先把每个 (a,b,c) 的结果存入数组 left，排序但不去重。右侧每个 (d,e,f) 算出 target 后，upper_bound 与 lower_bound 的下标之差，恰是满足左式等于 target 的三元组个数。这些左三元组分别与当前右三元组组合，贡献相应数量。

每个完整六元组有唯一的左三元组和右三元组，两个枚举的组合既不会漏掉，也不会重复把同一位置选择计两次。d=0 时原式无定义，不能因为移项后两边碰巧同为零而把它加进答案。

每个值在三万以内，乘法先用 long long，避免把一般乘法习惯写成 int；答案最多 n⁶，可达一万亿，明确超出三十二位。原图中的除式按非零 d 的有理数等式处理，没有整数截断除法。''',
    r'''int n;cin>>n;vector<long long>values(n);for(auto &x:values)cin>>x;vector<long long>left;left.reserve(n*n*n);
for(long long a:values)for(long long b:values)for(long long c:values)left.push_back(a*b+c);
sort(left.begin(),left.end());long long answer=0;
for(long long d:values)if(d!=0)for(long long e:values)for(long long f:values){
    long long target=d*(e+f);
    // 相同值的三元组各算一次，不把 left 去重。
    answer+=upper_bound(left.begin(),left.end(),target)-lower_bound(left.begin(),left.end(),target);
}
cout<<answer<<'\n';''',
    '六个位置可重复选值；保留三元组重数；d=0 一律不计；不能用 C++ 整数除法判断原等式。',
    r'时间 $O(n^3\log(n+1))$、空间 $O(n^3)$。',tags=['折半枚举','二分查找','排序'],lessons=A+['sort','iterators','bounds','enumeration'])
