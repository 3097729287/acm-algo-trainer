"""Subset, tree, cut-line and state-space models from the search unit."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer']
R=A+['recursion','functions']
T=A+['graphs','trees','bindings']

add('CF55B','按运算时间顺序，枚举每次被合并的两项',
    '黑板上初始四个非负整数，按给定的三个加号或乘号依次操作，每次任选两项合并，求最终最小值。两项不必相邻。',
    r'''递归保存黑板上当前所有数。第 step 层使用第 step 个运算符，枚举当前任意一对下标，把其余数与本次结果组成下一层。剩一个数时更新最小值。四项、三项、两项时分别有六、三、一种选择，共十八种合并计划，完全枚举即可。''',
    r'''运算符的顺序是时间顺序，不能按通常表达式的乘法优先级重排。例如先加、再加、最后乘，必须先完成两次合并加法，最后才能做乘法；但每次可以任选黑板上的两项，不要求它们在原输入中相邻。

当前有 k 个数时，选两个不同下标 i<j，根据本层运算符算出一个结果。未选择的 k−2 个数保持原值，再附上新结果，得到下一层的 k−1 个数。复制出下一层容器使各分支独立，无须手工撤销被删除的数。

任意合法执行计划的第一步都对应一对下标，后面的每步也对应其当前状态下的一对，因此递归枚举了所有合法计划。反过来，递归每一步恰是题目允许的合并，没有额外加入其它运算。数值相同的两项仍是黑板上不同项；重复产生同一数值只会多比较一次，不影响取最小值。

选择数至多六乘三乘一，即十八个完整计划。数最大可由四个一千相乘得到一万亿，使用 long long，不能用 int 保存中间乘积。存在零时也照常枚举，例如把一大组数最后乘零，可能让结果变为零。''',
    r'''vector<long long>numbers(4);for(auto &x:numbers)cin>>x;for(char &c:operation)cin>>c;
cout<<solve(numbers,0)<<'\n';''',
    '运算符按给定时间顺序用；每次任选两项，不限相邻；中间乘积使用 long long。',
    '初始数固定四个，完整合并计划至多十八种，时间、空间均为 $O(1)$。',tags=['DFS','枚举'],lessons=R+['enumeration'],
    declarations=r'''char operation[3];
long long solve(const vector<long long>&numbers,int step){
    if(numbers.size()==1)return numbers[0];
    long long answer=LLONG_MAX;int size=(int)numbers.size();
    for(int i=0;i<size;++i)for(int j=i+1;j<size;++j){
        vector<long long>next;for(int k=0;k<size;++k)if(k!=i&&k!=j)next.push_back(numbers[k]);
        // 本层只执行这一时刻的运算，不改变三个运算符的先后。
        next.push_back(operation[step]=='+'?numbers[i]+numbers[j]:numbers[i]*numbers[j]);
        answer=min(answer,solve(next,step+1));
    }
    return answer;
}''')

add('AT_abc184_f','折半枚举子集和，在另一半二分补足',
    '至多四十道题，每道可选或不选，总用时不超过 T，求能用掉的最大总时间；允许一道也不选。',
    r'''把四十项分成两半，各自枚举全部子集和，规模降为各至多二的二十次方。右半和排序，对每个左半和 x，二分找到不超过 T−x 的最大右半和，更新答案。两半都保留空集和零，覆盖只选一半及完全不选。''',
    r'''直接枚举四十项的所有子集需要二的四十次方种，无法逐个处理。把题目分成前后两半，每半至多二十项，各自的选择只有约一百万种，便可完整列出。

一个原问题子集可以唯一拆成“左半选择、右半选择”。若两者和分别为 x、y，可行条件就是 x+y≤T。固定 x 后，为让总时间最大，只需找右半中不超过 T−x 的最大 y，而不必和全部右半子集一一配对。

右半和排序后，upper_bound(T−x) 找到第一个严格大于余量的位置，其前驱就是所需候选。代码只保留不超过 T 的半边和，且各半都包含零，因此对合法 x，余量非负，前驱一定存在。若所有题单独都超过 T，两边仍有零，答案自然是零。

枚举子集和时，从数组 [0] 开始，加入一个数前先记住原数组长度，只在这些旧项后面追加“旧和加当前数”。旧项表示不选，新项表示选，且不能在同一轮把刚追加的项再使用，否则会把同一道题选择多次。

所有用时为正，半边和一旦超过 T，以后再加别的正数也不会变可行，所以可以不保存它。总和若按所有原用时累计可能超过 int，参考程序使用 long long。''',
    r'''int n;long long limit;cin>>n>>limit;vector<long long>a(n);for(auto &x:a)cin>>x;
auto left=subset_sums(a,0,n/2,limit),right=subset_sums(a,n/2,n,limit);sort(right.begin(),right.end());long long answer=0;
for(long long x:left){auto at=upper_bound(right.begin(),right.end(),limit-x);--at;answer=max(answer,x+*at);}
cout<<answer<<'\n';''',
    '两半都含空集零；每轮只从旧子集扩展；upper_bound 的前驱才是不超过余量的最大值。',
    r'时间 $O(n2^{\lceil n/2\rceil})$、空间 $O(2^{\lceil n/2\rceil})$。',tags=['折半枚举','二分查找','排序'],lessons=A+['functions','sort','bounds','iterators','enumeration'],
    declarations=r'''vector<long long>subset_sums(const vector<long long>&a,int begin,int end,long long limit){
    vector<long long>sums={0};
    for(int i=begin;i<end;++i){size_t previous=sums.size();
        // 本轮只从旧和扩展，不能重复选当前元素。
        for(size_t j=0;j<previous;++j)if(sums[j]+a[i]<=limit)sums.push_back(sums[j]+a[i]);
    }
    return sums;
}''')

add('CF700B','按每条边两侧的大学数累计最大跨边配对数',
    '树上有二倍 k 所大学，把它们两两配对，每所恰用一次，最大化各对树上距离之和。每条边长度一。',
    r'''一条边切开后，两侧分别有 c、2k−c 所大学，跨过该边的配对最多 min(c,2k−c) 个。这个上界可由同一个配对方案对所有边同时达到：按 DFS 顺序排列大学，前半与相隔 k 位的后半配对。因此累加每条边的这个最小值即可。子树大学数按逆遍历顺序计算。''',
    r'''先固定一条边。大学的一对端点若位于不同侧，它们的唯一路径经过这条边一次；位于同侧就不会经过。因此总距离等于每条边被多少对路径经过的次数之和。

边两侧有 c 与 2k−c 所大学，每条跨边配对消耗两侧各一个端点，所以跨边数不可能超过较少的一侧，即 min(c,2k−c)。但只写出各边上界还不够，需要证明这些上界能同时取到。

把大学按一趟 DFS 中出现的顺序编号零到 2k−1，放在一个圆环上，编号 i 与 i+k 配对，其中 i 从零到 k−1。DFS 中每棵子树的大学构成一个连续区间；圆环上它的补集同样是连续弧。对任意一条边，大学较少的一侧对应长度不超过 k 的连续弧，里面不可能同时含相隔 k 位的一对端点。因此这一侧每所大学都与外侧配对，恰有 min(c,2k−c) 对跨边。

同一份“相隔 k 位”配对满足所有子树边的论证，因此各边上界之和确实可达到，而不只是松的上界。程序只需输出最大值，无须实际构造配对，也就不必真的保存这趟大学 DFS 序。

实现用任意根的一份父先子后遍历顺序，逆序把每个子节点的大学数加到父亲。根没有父边，不累加根的贡献。n 可达二十万，显式遍历避免递归深链溢栈，答案使用 long long。''',
    r'''int n,k;cin>>n>>k;vector<int>count(n+1);for(int i=0;i<2*k;++i){int u;cin>>u;count[u]=1;}
vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>parent(n+1),order={1};for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
long long answer=0;
for(int at=n-1;at>0;--at){int u=order[at];
    // 每条父边的贡献是两侧大学数的较小者。
    answer+=min(count[u],2*k-count[u]);count[parent[u]]+=count[u];
}
cout<<answer<<'\n';''',
    '统计大学数而非节点数；距离总和按边计贡献；需说明上界对所有边能同时达到；根不算父边。',
    '时间、空间均为 $O(n)$。',tags=['图论','贪心','结论与计数'],lessons=T+['greedy','counting'])

add('CF1401D','边的点对贡献排序，把额外大质因子集中在最大贡献边',
    '给树边分配正整数，乘积等于给定质因子的乘积，先让标一的边尽量少，再最大化所有点对路径上的边权和，最后对十亿零七取模。',
    r'''切开一边后子树大小为 s，经过它的无序点对数是 s(n−s)，作为这条边权的系数。系数排序；质因子不足边数时补一，足够时每边至少一个，多余因子与最大的因子合到同一组，再按真实大小与系数同序配对。合并组虽计算模值，仍放在最大系数处，不能再按模后的值排序。''',
    r'''一条边分开 s 个点与 n−s 个点，选两侧各一个端点便有一条经过它的路径，共 s(n−s) 个无序点对。交换求和次序后，目标就是“每条边的系数乘分配的边权”之和，与具体路径不再有关。

共有 E=n−1 条边、m 个质因子。m<E 时，为尽量少出现一，必须让 m 条边各拿一个质因子，其余 E−m 条边标一。m≥E 时，每条边至少拿一个，剩余因子需要合并到某些边。

固定一组边权时，先按真实大小与系数同序配对；任意逆序交换的收益是两者差的乘积，非负。以下均按这种次序安排。

为什么把多余因子集中到一组？设最大乘积的一组为 A，另一组 B=pq 至少含两个因子，把因子 p 从 B 移给 A。两组所配系数为 x≥y，且 A≥B≥q，目标变化为

$$ (p-1)(xA-yq)\ge0.$$

一可以始终避免，因为 B 还剩 q。不断把其它复合组的多余因子移过去，就得到只有最大系数的一组含多个因子的方案，目标不会降低。

再看这组中一个较小因子 p，而某单独组拿较大因子 q。令复合组剩余因子积为 R≥2，交换后目标变化是

$$ (q-p)(xR-y)\ge0.$$

所以复合组应收集最大的 m−E+1 个质因子，其余较小因子各自单独。固定最终 E 个边权后，若大系数配小边权、小系数配大边权，交换收益为“系数差乘边权差”，非负，因此同序配对最优。

所有这些大小关系比较都针对真实整数。取模只为输出：最大复合组模十亿零七后可能变成小数值，它仍代表真实最大的组，必须留在末尾配最大系数，不能重新排序模值。子树大小用显式遍历逆序累加，系数的乘法先转 long long。''',
    r'''int tests;cin>>tests;const long long mod=1000000007;
while(tests--){int n;cin>>n;vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
    vector<int>parent(n+1),order={1};for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    vector<long long>size(n+1,1),weight;for(int at=n-1;at>0;--at){int u=order[at];weight.push_back(size[u]*(n-size[u]));size[parent[u]]+=size[u];}
    sort(weight.begin(),weight.end());int m;cin>>m;vector<long long>factor(m);for(auto &p:factor)cin>>p;sort(factor.begin(),factor.end());int edges=n-1;
    if(m<edges){factor.resize(edges,1);sort(factor.begin(),factor.end());}
    else if(m>edges){long long combined=1;for(int i=edges-1;i<m;++i)combined=combined*factor[i]%mod;
        factor.resize(edges);factor.back()=combined; // 模值再小，也仍配给最大系数。
    }
    long long answer=0;for(int i=0;i<edges;++i)answer=(answer+(weight[i]%mod)*factor[i])%mod;
    cout<<answer<<'\n';
}''',
    '先满足最少标一，再最大化；系数是 s(n−s)；最大因子组合取模后不再排序；两点树也要正确合并全部因子。',
    r'每组时间 $O(n\log n+m\log m)$、空间 $O(n+m)$。',tags=['图论','贪心','排序'],lessons=T+['sort','greedy','counting','modular'])

add('P1790','沿格线搜索一条不自交割线，按反向去重',
    '沿小方格边界，把矩形分成两个四向连通部分，两部分都要含原矩形边上的格子，统计分法。两部分没有颜色或名称之分。',
    r'''合法分割的分界线从外边界出发，经内部格点，首次到另一外边界结束，不能重复经过格点。枚举非角边界格点为起点，DFS 向内部走，碰到其它边界就计一种。不能走沿外边界的边，也不能返回起点形成闭线。每条割线从两个方向各数一次，最终除以二。''',
    r'''先看题目所附三乘二的十五种分法：每一块都连通，交换两种颜色只是同一分法。不能把六格任意涂成两种非空颜色，否则会把互不相连的散块也计入，得到错误的三十一。

把原方格看作格子，把分割线的转弯位置看作格点，二者不要混淆。由于两部分连通且都接触外边界，它们之间的分界是一条不自交、从外边界到外边界的格线。若是内部闭线，围出的那块接触不到外边界；若在边界提前碰到后又继续，会切出额外部分。因此一旦首次到达另一边界就应结束。

矩形角点向内部没有一条可直接走的格线，合法起点是四条边上除角点外的格点。从起点只能沿垂直于该边的唯一格线进入。进入后，枚举格点的上下左右邻点，用 visited 禁止再次经过同一格点，回溯时撤销。起点也预先标记，防止立刻走回去或后来绕回形成闭线。

每条这样的简单割线确实将矩形分成两个连通部分，两边都沿分界线的一侧接触原边界；每种合法分割也能还原出自己的分界线。固定从哪端出发后，转弯序列唯一，DFS 不会重复；但换另一端反着走会再得到同一分法，所以总数除以二，不是按旋转或镜像去重。

内部格点数为 (a−1)(b−1)，最多二十五，适合这个小范围的简单路径搜索。a=1 时没有内部格点，一条横跨宽度方向的格线直接连接两边，程序同样能计到 b−1 种。说明使用的“格点”是小格的角，数量与 a*b 个小格不同。''',
    r'''cin>>rows>>columns;
for(int x=1;x<rows;++x){
    visited[x][0]=true;cut(x,1);visited[x][0]=false;
    visited[x][columns]=true;cut(x,columns-1);visited[x][columns]=false;
}
for(int y=1;y<columns;++y){
    visited[0][y]=true;cut(1,y);visited[0][y]=false;
    visited[rows][y]=true;cut(rows-1,y);visited[rows][y]=false;
}
cout<<directed_count/2<<'\n';''',
    '搜索格点间的割线，不是逐格选一块；起点要预标记；碰到另一边界立即结束；只除以反向的二。',
    r'设内部格点数 V=(a−1)(b−1)、边界起点数 P=2(a+b−2)，时间可用 $O(P3^{V+1})$ 作宽松指数上界，实际受网格连接限制远小于它；额外空间 $O(ab)$。',
    tags=['DFS','递归','组合计数'],lessons=R+['coordinates','graphs','counting'],
    declarations=r'''int rows,columns;bool visited[8][8];long long directed_count=0;
void cut(int x,int y){
    if(x==0||x==rows||y==0||y==columns){++directed_count;return;}
    visited[x][y]=true;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];if(!visited[nx][ny])cut(nx,ny);}
    visited[x][y]=false; // 一条割线结束后恢复格点，供其它割线使用。
}''')

add('P4289','十六位掩码保存玩具布局，BFS 搜索交换空位',
    '四乘四棋盘上的玩具完全相同，一步把某个玩具移到四邻空格，求从初始布局到目标布局的最少步数。',
    r'''用十六位整数记录哪些格有玩具。每步选一位一与相邻的一位零，把两位同时翻转得到新布局。每种布局是一个状态，移动代价一，用 BFS 首次到目标即最少次数。玩具相同，不要为每个玩具另编号增加状态。''',
    r'''给十六个格按行编号零到十五，第 i 位为一表示该格有玩具，为零表示空。位掩码只记录占用集合，恰好吻合同种玩具的状态：两个玩具互换身份没有任何可观察差别，不应视作新的布局。

从一个状态枚举每个有玩具的格，再检查它四邻中位于棋盘内的空格。把原格与目标格的两位各翻转一次，等价于玩具搬走、空位放入，用按位异或实现。其它位不变，玩具总数也不变。

共有至多二的十六次方种掩码，每种最多检查十六乘四个移动，足够直接 BFS。每条边是一次实际移动，首次到达状态的步数最少；记录过的掩码不重复入队，搜索有限。

读入时逐个读取 char，可同时兼容每行紧挨的零一数字及空格、空行，因为格式化字符输入自动略过空白。初态等于目标时答案零。若两边玩具数不同，移动不可能改变数量，直接输出负一；正常同数量输入由 BFS 找最短。

位运算只用于表示集合，不是把移动当作任意两位交换；下标必须来自真正相邻的格，不能越过行边界把最右格与下一行最左格当作邻居。''',
    r'''int start=0,target=0,start_count=0,target_count=0;char c;for(int i=0;i<16;++i){cin>>c;if(c=='1'){start|=1<<i;++start_count;}}for(int i=0;i<16;++i){cin>>c;if(c=='1'){target|=1<<i;++target_count;}}
if(start_count!=target_count){cout<<-1<<'\n';return 0;}
vector<int>distance(1<<16,-1);queue<int>todo;todo.push(start);distance[start]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){int state=todo.front();todo.pop();if(state==target){cout<<distance[state]<<'\n';return 0;}
    for(int p=0;p<16;++p)if(state&(1<<p))for(int d=0;d<4;++d){int r=p/4+dr[d],col=p%4+dc[d];if(r<0||r>=4||col<0||col>=4)continue;int q=r*4+col;
        if(state&(1<<q))continue;
        int next=state^(1<<p)^(1<<q); // 一位搬空，另一空位放入，玩具数不变。
        if(distance[next]==-1){distance[next]=distance[state]+1;todo.push(next);}
    }
}
cout<<-1<<'\n';''',
    '同种玩具只记录占用，不编号；必须四向相邻；异或翻转的一位原本为一、另一位原本为零。',
    r'状态数至多 $2^{16}$，时间 $O(16\cdot2^{16})$、空间 $O(2^{16})$。',tags=['BFS','位运算'],lessons=A+['graphs','queue-stack','bitwise'])

add('P10488','迭代加深搜索，用最多修复三个断点作下界',
    '一次可抽走连续一段书，再插入其它位置。求把一到 n 的排列排好所需最少次数；答案至少五时统一输出 5 or more，n 至多十五。',
    r'''依次限定零、一、二、三、四次操作搜索。给排列前后补零与 n+1，统计相邻值没有恰增一的断点数 bad。一次抽段重插等价于交换相邻两块，最多修复三个边界，所以至少还需 ceil(bad/3) 次。已用次数加下界超过本轮限制时剪枝；首个找到解的限制就是最少次数。''',
    r'''把一段移到右边，可以看作把它和中间经过的一段交换；向左移同样如此。因此枚举三个边界 l<mid<r，把相邻两块 a[l:mid]、a[mid:r] 交换，便覆盖所有非空、非原地的抽取再插入操作。

先给排列前后补哨兵零与 n+1。目标中相邻值总恰好增加一；若某处后值不等于前值加一，称为断点。哨兵也参加统计，例如把整段循环移位后，内部可能大半有序，却仍有开头、接缝、末尾的错误，需要被看见。

交换相邻两块时，两块内部的相邻关系都保持，仅有它们与外部、彼此之间的三个接缝改变。因此一步最多消除三个断点，即使这三个都修好，修复 bad 个断点也至少需要 ceil(bad/3) 次。这个估计只会低估剩余步数，不会把可能的短解错剪掉。

本轮限定最多 limit 步，在已走 depth 步的状态，若 depth+ceil(bad/3)>limit，就不再枚举后继；断点为零则已经排好。每次把新排列写到临时容器，递归后恢复原排列，避免一个分支修改另一个分支的起点。

按限制从零递增到四，前面限制均已完整排除，首次成功的次数就是真正最少值。若四次仍不行，题目只要求统一输出 5 or more，不需要继续求五、六或更多。该搜索最坏仍随深度指数增长；启发式下界负责在十五本书的范围内剪去大量无望分支，不能把它称为多项式算法。''',
    r'''int tests;cin>>tests;while(tests--){cin>>n;books.resize(n);for(int &x:books)cin>>x;bool solved=false;
    for(int limit=0;limit<5;++limit)if(search(0,limit)){cout<<limit<<'\n';solved=true;break;}
    if(!solved)cout<<"5 or more\n";
}''',
    '断点包含两端哨兵；下界向上取整；枚举相邻两段交换涵盖抽段重插；每分支恢复原排列。',
    r'每状态分支数 $B=\binom{n+1}{3}$，最多搜索四层，宽松时间上界 $O(nB^4)$；递归各层保存排列，空间 $O(n)$，因深度上限固定四。',
    tags=['DFS','递归'],lessons=R+['enumeration','permutations','iterators','vector-ranges'],exact=True,
    declarations=r'''int n;vector<int>books;
int breaks(){int count=0,previous=0;for(int x:books){if(x!=previous+1)++count;previous=x;}if(previous!=n)++count;return count;}
bool search(int depth,int limit){
    int bad=breaks();if(bad==0)return true;
    if(depth+(bad+2)/3>limit)return false; // 一次操作至多修复三个接缝。
    vector<int>original=books;
    for(int left=0;left<n;++left)for(int middle=left+1;middle<n;++middle)for(int right=middle+1;right<=n;++right){
        vector<int>next;next.reserve(n);
        next.insert(next.end(),original.begin(),original.begin()+left);
        next.insert(next.end(),original.begin()+middle,original.begin()+right);
        next.insert(next.end(),original.begin()+left,original.begin()+middle);
        next.insert(next.end(),original.begin()+right,original.end());
        books=next;
        if(search(depth+1,limit))return true;
        books=original;
    }
    return false;
}''')

add('UVA11367','城市和剩余油量组成状态，Dijkstra 求最少油费',
    '道路双向，每走一单位距离用一单位油，各城油价不同。每个询问从空油箱出发，容量给定，求到目标城的最少购油费用；不能到达输出 impossible。',
    r'''状态为城市 u 与剩余油量 f。若未满箱，可付本城油价买一单位油，转到 (u,f+1)；若油足够走一条路，可不再付钱，转到邻城并扣掉路长。边权非负，Dijkstra 从 (起点,0) 搜索，首次出堆的目标城市状态即最小费用，剩油多少都可。''',
    r'''到同一座城市，花的钱少却没有油，与稍贵但剩很多油，后面能走的路线和购油决策不同。只给城市保存一个最小费用会丢掉必要状态，因此把剩余油量一并保存。

油量在零到容量 C，每个状态有两类动作。购买一单位油付 price[u]，位置不变、油量加一；选择一条长度 d≤f 的道路驶往 v，油量减 d，当前不再产生费用。开车动作的零费用表示油已经在购买动作时付过，不能把路长或邻城油价再加到费用中。

道路长、容量都是整数；从空箱开始，只在整数路长后扣油，为一单位购油建边足以表达最优方案。任何实际行程都可拆成这些买油与行驶动作，反过来状态图上的路径也可直接执行，因此状态图最短路就是最少购油费用。

边权为油价或零，均非负，适用 Dijkstra。优先队列按累计费用取最小，弹出时若与当前 dist 不同就丢掉旧条目。第一次弹出任意目标城市状态时，它已是全部目标油量中的最低费用，可立即输出，不必强制剩油为零，也不必处理完全部状态。

每个询问容量不同，重新建立对应距离表。起点等于终点可不买油直接得到零；若没有道路能在容量内形成连通路线，堆耗尽后输出小写 impossible。完整输入范围已按 [UVa 官方 PDF](https://onlinejudge.org/external/113/11367.pdf)核对，城市编号从零开始。''',
    r'''int n,m;cin>>n>>m;vector<int>price(n);for(int &x:price)cin>>x;vector<vector<pair<int,int>>>graph(n);
for(int i=0;i<m;++i){int u,v,d;cin>>u>>v>>d;graph[u].push_back({v,d});graph[v].push_back({u,d});}
int queries;cin>>queries;const long long inf=LLONG_MAX/4;
while(queries--){int capacity,start,target;cin>>capacity>>start>>target;vector<vector<long long>>distance(n,vector<long long>(capacity+1,inf));
    priority_queue<tuple<long long,int,int>,vector<tuple<long long,int,int>>,greater<tuple<long long,int,int>>>todo;
    distance[start][0]=0;todo.push({0,start,0});long long answer=-1;
    while(!todo.empty()){auto [cost,u,fuel]=todo.top();todo.pop();if(cost!=distance[u][fuel])continue;
        if(u==target){answer=cost;break;}
        // 购油付钱，行驶只扣油；费用不能重复记在道路上。
        if(fuel<capacity&&cost+price[u]<distance[u][fuel+1]){distance[u][fuel+1]=cost+price[u];todo.push({distance[u][fuel+1],u,fuel+1});}
        for(auto [v,length]:graph[u])if(length<=fuel&&cost<distance[v][fuel-length]){distance[v][fuel-length]=cost;todo.push({cost,v,fuel-length});}
    }
    if(answer<0)cout<<"impossible\n";else cout<<answer<<'\n';
}''',
    '初始空箱；城市编号从零开始；同城不同剩油是不同状态；行驶不重复加费用；目标城任意剩油都能结束。',
    r'每问状态 $O(nC)$、转移 $O(C(n+m))$，时间 $O(C(n+m)\log(nC+1))$、空间 $O(C(n+m))$，包含堆中候选。',
    tags=['最短路','堆'],lessons=A+['graphs','shortest-path','heap','bindings'],exact=True)

add('B3625','显式栈遍历连通空地，访问标记永久保留',
    '从矩形迷宫左上角出发，只走四邻空地，判断能否到右下角，两端保证为空地。',
    r'''从左上角用栈搜索所有可达空地，第一次加入栈时标记访问，弹出后检查四邻。若到右下角输出 Yes，否则栈空输出 No。这题只问是否可达，访问标记不撤销；不必枚举同一位置的所有不同走法。''',
    r'''只要找到任意路线即可，路线长短和数量都不重要。到达某个空格后，它可以继续走的四邻只由地图决定，与此前绕了哪条路无关。因此第一次探索后，把这个格永久标记，不再从其它路线重复扩展，仍能找到所有可达格。

使用显式栈保存待处理位置。起点先标记再入栈，弹出一个格后，把棋盘内、为空地、尚未访问的邻格立即标记并压入。若等弹出时才标记，同一个格可能被多个邻居反复压入，虽然仍可修补，但会多做工作。

任何从起点可达的格都能沿某条路线按步数归纳得到：起点已加入，路线前一格被处理时会加入下一格。加入的每格也确实有一条由起点延伸的路线，所以搜索结果恰好是起点所在的空地连通块。目标在其中当且仅当答案为 Yes。

这与统计全部简单路径的题不同：这里标记表示“这个位置的后继已经安排探索”，没有必要返回后撤销。显式栈也避免了在长走廊上使用很深的函数递归。''',
    r'''int n,m;cin>>n>>m;vector<string>grid(n);for(auto &row:grid)cin>>row;vector<vector<bool>>visited(n,vector<bool>(m));
vector<pair<int,int>>todo={{0,0}};visited[0][0]=true;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){auto [x,y]=todo.back();todo.pop_back();if(x==n-1&&y==m-1){cout<<"Yes\n";return 0;}
    for(int d=0;d<4;++d){int nx=x+dr[d],ny=y+dc[d];
        if(0<=nx&&nx<n&&0<=ny&&ny<m&&grid[nx][ny]=='.'&&!visited[nx][ny]){
            visited[nx][ny]=true;todo.push_back({nx,ny}); // 入栈时就标记，本题不撤销。
        }
    }
}
cout<<"No\n";''',
    '只需可达性，不求全部路线；入栈时标记；本题访问标记不回撤；大小写为 Yes、No。',
    '时间、空间均为 $O(nm)$。',tags=['DFS','图论'],lessons=A+['graphs','queue-stack','strings','bindings'])
