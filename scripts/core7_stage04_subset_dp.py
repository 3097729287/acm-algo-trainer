"""Literal choices, exact arithmetic and compressed subset transitions."""
from core7_authoring import add
A=['io-basics','basic-control','vector','integer','functions']
D=A+['bitwise','dp','subset-dp']

add('P12593','用剩余点集合描述删点后的真实图',
    '删除一个点时，费用为当时与它相连的边数乘这些边权和；删光所有点，求最小总费用。',
    r'''删过的点之间怎样排序不再影响余图，只需记剩余集合S。枚举下一次删除u，直接在S中数u的邻居与边权和，付本次费用后转到去掉u的集合。空集合费用零，按掩码递增计算，因为去一位后总会变小。边权可十亿，用long long。''',
    r'''费用只取决于当前还在的边。比如三点链两边权二、五，先删中点要付二乘七，先删两个端点则分别付二、五，后删中点已经没有边。每条边虽然只删除一次，但本次同时删除的条数会改变乘数，不能只把原边权相加。

把仍然存在的点组成集合S。任意两个保留点之间的原边也一定还在，除此之外没有边；因此当前图由S唯一确定，不必另存每条边是否删除。令f[S]为把这张余图删空的最少后续费用。

下一步可以选S中的任意u。扫描其它保留点，设与u相连的有cnt条，权和sum；本次付cnt乘sum，后面的最优值是f[S去掉u]。对所有u取最小，覆盖所有可能的第一步。

f[空集]为零。删去一个置一位后掩码数值严格减小，所以从小到大枚举S时，所有来源都已确定。用原图权值矩阵，零表示没有边，原题边权全正，不会混淆。

最多八点，可以直接在每个状态、候选点中扫描所有邻居。费用在六十四位中计算，特别要先把边权和保存成long long，再乘条数。删除后不要求余图连通，孤立点费用为零。''',
    r'''int n,m;cin>>n>>m;vector<vector<long long>>weight(n,vector<long long>(n));
for(int i=0,u,v;i<m;++i){long long w;cin>>u>>v>>w;--u;--v;weight[u][v]=weight[v][u]=w;}
int states=1<<n;vector<long long>dp(states,LLONG_MAX/4);dp[0]=0;
for(int mask=1;mask<states;++mask){
    for(int u=0;u<n;++u) if(mask>>u&1){
        int count=0;long long sum=0;
        for(int v=0;v<n;++v) if((mask>>v&1)&&weight[u][v]){++count;sum+=weight[u][v];}
        dp[mask]=min(dp[mask],dp[mask^(1<<u)]+count*sum);
    }
}
cout<<dp.back()<<'\n';''',
    '只数当前余图的边；条数乘边权和；空图为零；孤立点免费；不要求中间连通；六十四位。',
    r'时间 $O(n^2 2^n)$，空间 $O(n^2+2^n)$。',tags=['状压 DP'],lessons=D)

add('P2622','把灯的开关状态当作图结点，广搜最少按钮数',
    '所有灯初始开启；按钮可分别强制某灯开、关或不变，求全关的最少按键次数，不能达到输出负一。',
    r'''一位一表示灯开。每个按钮预存强制关的off与强制开的on，按下后的状态是先清off位、再置on位。把每个完整灯状态当成结点，每按一次当作一条等长边，从全一广搜到零，第一次距离就是最少次数。按钮不是翻转，不能直接用异或。''',
    r'''按钮写一表示“已经开着就关掉”，再按也不会打开；写负一则强制打开；零保持原样。它们不是同一个翻转操作。例如一盏已经关的灯，遇到关灯按钮后仍关，异或却会把它打开。

令掩码S的第j位为一当且仅当第j盏灯开着。对一个按钮，off记录输入为一的位，on记录输入为负一的位；这两个集合不相交。转移为先清除off中的位，再把on中的位置一：

$$next=(S\mathbin{\&}\mathord{\sim}off)\mathbin{|}on.$$

取反会使高位为一，但它只与原来只含n位的S按位与，因此不会凭空引入高位。

现在把每个完整状态看成图结点，一个按钮形成一条边。各次按键费用都为一，广度优先搜索按距离逐层扩展；某状态第一次入队时，就是到它的最少按键数。之后再次到达不可能更短，无须重复入队。

从全一掩码开始，零是目标。按钮可能没有改变状态，照样由已访问标记处理。若搜索完零仍未访问，输出负一。虽然按钮可以重复用，有限个完整状态足以包含全部有用的中间情况。''',
    r'''int n,m;cin>>n>>m;vector<int>off(m),on(m);
for(int i=0;i<m;++i) for(int j=0,value;j<n;++j){cin>>value;if(value==1) off[i]|=1<<j;else if(value==-1) on[i]|=1<<j;}
int states=1<<n;vector<int>distance(states,-1);queue<int>ready;distance[states-1]=0;ready.push(states-1);
while(!ready.empty()){
    int mask=ready.front();ready.pop();
    for(int i=0;i<m;++i){
        int next=(mask&~off[i])|on[i];
        if(distance[next]<0){distance[next]=distance[mask]+1;ready.push(next);}
    }
}
cout<<distance[0]<<'\n';''',
    '强制开关不等于翻转；初始全开；每个完整状态只入队一次；无变化按钮不形成死循环；无解输出负一。',
    r'预处理 $O(mn)$，广搜 $O(m2^n)$，空间 $O(m+2^n)$。',tags=['BFS','位运算'],lessons=A+['bitwise','graphs','queue-stack'])

add('AT_abc359_d','只保存末尾若干位，拒绝刚形成的定长回文',
    '将问号独立替换为A或B，统计没有长度恰好K的回文子串的结果数，答案模998244353。',
    r'''从左到右填字符，之前所有长度K窗口都已检查；新加入一字只会产生一个新的末尾窗口。因此状态只需记最近K减一个字符。预先标记全部K位掩码是否回文，尝试当前允许的A、B，窗口已满时拒绝回文，再只保留低K减一位继续。开始不足K字时不能把前导补零当真字符。''',
    r'''要求禁止的是长度恰好K的连续回文，不是禁止所有回文，也不是检查任意子序列。比如K为四时，单个字符当然可以出现。

按从左到右的顺序填问号。假设旧前缀已经合格，加入一个新字符后，唯一尚未检查的长度K窗口就是最后K字；其它窗口完全没变。所以未来只需要知道最近K减一字，再早的字符不影响下一次检查。

用零代表A、一代表B，保存末尾K减一位。加入c后，将旧状态左移一位并接上c，得到窗口bits；按对称位置逐一比较，预先求出每个K位bits是否回文。若当前已处理长度至少K且它是回文，就拒绝这一条转移。

最初真实长度还不够K减一，掩码高位的零只是占位。必须等已处理字数至少K时才判回文；否则会误把并不存在的A补进窗口。由于计算到第几位由外层循环固定，不必再把真实长度放进状态。

f[mask]记录合格旧前缀的数量。固定字母只允许对应位，问号允许零、一两个不同结果；把合法数量加到新表的低K减一位。每一位都重建新表，不从本轮刚写入的数量继续延长。

全部字符填完，所有尾状态相加。不同问号替换若汇入同一个末尾状态，仍是不同完整字符串，应累加，不能只记是否可达。''',
    r'''int n,k;string s;cin>>n>>k>>s;const int MOD=998244353;
int states=1<<(k-1),keep=states-1;vector<char>palindrome(1<<k,true);
for(int bits=0;bits<(1<<k);++bits) for(int i=0;i<k/2;++i) if(((bits>>i)&1)!=((bits>>(k-1-i))&1)) palindrome[bits]=false;
vector<int>dp(states),next(states);dp[0]=1;
for(int pos=0;pos<n;++pos){
    fill(next.begin(),next.end(),0);
    for(int mask=0;mask<states;++mask) if(dp[mask]) for(int c=0;c<2;++c){
        if(s[pos]!='?'&&s[pos]!=char('A'+c)) continue;
        int bits=(mask<<1)|c;if(pos+1>=k&&palindrome[bits]) continue;
        int target=bits&keep;next[target]+=dp[mask];if(next[target]>=MOD) next[target]-=MOD;
    }
    dp.swap(next);
}
int answer=0;for(int value:dp){answer+=value;if(answer>=MOD) answer-=MOD;}
cout<<answer<<'\n';''',
    '禁止恰长K的连续子串；短前缀不查补零；固定字符不可改；每轮读旧表写新表；相同尾状态的不同前缀仍累加。',
    r'时间 $O(K2^K+N2^K)$，空间 $O(2^K)$。',tags=['状压 DP'],lessons=D+['strings','numeric-tools'])

add('P1441','枚举删掉的砝码，用位集并行记录保留者的可达重量',
    '从至多二十个砝码中恰好去掉m个，剩余砝码只能放同一边，求最多能组成几种正重量。',
    r'''只枚举恰好m个删除编号，m至多四。每组删除方案从重量零开始，把每个保留重量w的旧位集左移w，再按位或并回，表示选或不选这一枚砝码。所有可达位中除去零位，便是这组能称的不同正重量，取最大。相同重量的不同组成不重复计数。''',
    r'''先分开两个问题：外层选择丢掉哪几枚，内层判断剩余砝码能组成哪些重量。题目让砝码只放一边，不能把同一个砝码放到另一边做减法；剩余者也不要求每次全部使用。

删除编号按递增顺序枚举，每个大小为m的集合只出现一次。当前还需删left个，下一编号最多取到n-left，保证后面仍有足够对象；left为零便立刻评价，不会继续多删。m为零时直接评价原全集一次。

对一组保留者，令possible的第s位表示能否恰好组成重量s。初始只有零位为一。加入一枚重w的砝码，旧可达s若选择它会产生s加w，因此全部新重量就是旧位集左移w；与旧状态按位或，合并“不选它”的情况。

右侧移位先得到一个旧状态的副本，再整体并回，所以这一轮每枚砝码只使用一次。两枚等重者可以分别参与两轮，但某个重量始终只有一位，不会按组成清单重复计数。

所有原重量的和至多二千，保留零至二千共二千零一位足够。最后count统计一的数量，减去始终可达的零位。每组必须重新建立位集，防止混入上一组删法。

外层最多只有二十取四组，位集在常用标准库里按机器字并行移位，不需要为每组重新逐个重量扫描二维背包。递归只承担枚举删除集，深度至多四。''',
    r'''int n,m;cin>>n>>m;vector<int>weight(n);for(int &x:weight) cin>>x;int answer=0;
auto evaluate=[&](int removed){
    bitset<2001>possible;possible[0]=1;
    for(int i=0;i<n;++i) if(!(removed>>i&1)) possible|=possible<<weight[i];
    answer=max(answer,int(possible.count())-1);
};
function<void(int,int,int)> choose=[&](int start,int left,int removed){
    if(left==0){evaluate(removed);return;}
    for(int i=start;i<=n-left;++i) choose(i+1,left-1,removed|(1<<i));
};
choose(0,m,0);cout<<answer<<'\n';''',
    '恰好删m枚；相同重量仍是不同砝码；重量只加不减；每枚用至多一次；按可达重量去重；清空每组状态并排除零。',
    r'设总重上界为W，时间按打包机器字估算为 $O(\binom nm n\lceil(W+1)/B\rceil)$，B为机器字位数；位集空间 $O(W/B)$，另有 $O(n)$ 输入与枚举空间。',tags=['背包 DP','枚举'],lessons=D+['bitset-states','recursion','lambda-local'])

add('P2210','把每条线路长度拆成它跨过的队列分界',
    '每头牛恰有三个朋友，将牛任意排成一列，朋友对之间分别接线，求全部线路长度之和最小。',
    r'''一条朋友边跨过几个相邻位置分界，它的线路就有多长。排好前缀集合S后，当前这个分界贡献是S与外部之间的朋友边数cut[S]，与前缀内部顺序无关。状态f[S]取前缀已经付出的最小总分界费，追加一头牛v后加cut[S加v]。最后全集没有外部，末项贡献为零。''',
    r'''若两头朋友牛排在第四与第七位置，线路长度三，正好经过第四至第五、第五至第六、第六至第七这三个分界。把所有朋友边按分界重新计数，线路总长等于每个分界两侧朋友边数之和。

从左往右放牛。已经放入集合S时，这条前后分界的费用cut[S]只取决于哪些牛已经在左边，不取决于左边内部的具体排列。令f[S]为排好这些牛、并计入其后分界的最小费用；空前缀费用零。

下一头任选外部v，形成newS，费用增加cut[newS]，来源f[S]取最小。放入全部牛时外部为空，cut为零，所以统一算这一项也不会多收费。

cut可用小集合递推。把v从外部移到内部，它原本连接S中朋友的边不再跨界，连接剩余外部朋友的边开始跨界。因为总度数三，变化是三减去两倍的S内朋友数。

先为每个集合求cut，再计算f。输入每段友情在两头牛的列表中各出现一次，计算跨界时只看一个新增点的三个朋友；不要把同一朋友边的线路费额外乘二。不同边即使部分共用位置，也按题意分别付费。''',
    r'''int n;cin>>n;vector<vector<int>>friends(n,vector<int>(3));
for(auto &row:friends) for(int &v:row){cin>>v;--v;}
int states=1<<n;vector<int>cut(states),dp(states,1000000000);dp[0]=0;
for(int mask=1;mask<states;++mask){
    int v=0;while(!(mask>>v&1)) ++v;int rest=mask^(1<<v),inside=0;
    for(int u:friends[v]) if(rest>>u&1) ++inside;
    cut[mask]=cut[rest]+3-2*inside;
}
for(int mask=1;mask<states;++mask) for(int v=0;v<n;++v) if(mask>>v&1) dp[mask]=min(dp[mask],dp[mask^(1<<v)]+cut[mask]);
cout<<dp.back()<<'\n';''',
    '线路按不同朋友对分别算；输入双向列表不代表两条边；每条边按跨过分界数计长度；同集合前缀长度固定；全集cut零。',
    r'时间 $O(n2^n)$，空间 $O(n+2^n)$。',tags=['状压 DP'],lessons=D+['graphs'])

add('P5911','枚举同一批过桥者，费用是这批最慢者的时间',
    '所有人分成若干批依次过桥，每批总重不超限，耗时等于该批最大个人时间，求全部过桥最短总时间。',
    r'''预处理每个子集的重量和与最大时间。f[S]表示把S中的人全部送过桥的最短时间，枚举其中一批group，只要不超重就尝试f[S去掉group]加group的最大时间。各批没有额外先后限制，可固定当前批包含S最小编号的人，避免枚举同一划分的多种批次顺序。空集为零。''',
    r'''同批并行过桥，三个人分别需要二十四、十、十八时间，这批只花二十四，不是相加；但重量要相加。不同批必须前一批完全离桥才开始，所以各批耗时才相加。

用集合S表示仍需安排的人，f[S]为安排完的最低总时间。挑出一批group，若其重量不超过W，就付这批最慢者的时间，再安排S除去group。

各个人都恰好属于一批。任意划分中，S最小编号的人必在某一批；把这批换到最前，不改变批重和总时间。因此只枚举包含该人的group仍覆盖全部划分，不必枚举空批或同一划分的重复批次顺序。

预处理子集时，从S去掉任意一个人v：总重加他的重量，最大时间与他的时间取大。去掉置一位后掩码变小，两个表以及f都能按数值递增计算。

group枚举采用子集递减式，每次从当前子集减一后与S按位与；它会依次枚举S的全部非空子集。这个写法与每次删一个人不同，必须把整批人一起从剩余集合移走。独立基础课解释这个枚举边界。

原题每个人重量不超过桥的容量，单人批永远可行。n至多十六，所有集合与其子集的总枚举量为三的n次方量级；不是每个集合都再枚举二的n次方个任意掩码。''',
    r'''int capacity,n;cin>>capacity>>n;vector<int>time(n),weight(n);for(int i=0;i<n;++i) cin>>time[i]>>weight[i];
int states=1<<n;vector<int>sum(states),slowest(states),dp(states,1000000000);dp[0]=0;
for(int mask=1;mask<states;++mask){
    int v=0;while(!(mask>>v&1)) ++v;int rest=mask^(1<<v);
    sum[mask]=sum[rest]+weight[v];slowest[mask]=max(slowest[rest],time[v]);
}
for(int mask=1;mask<states;++mask){
    int anchor=mask&-mask;
    for(int group=mask;group;group=(group-1)&mask) if((group&anchor)&&sum[group]<=capacity) dp[mask]=min(dp[mask],dp[mask^group]+slowest[group]);
}
cout<<dp.back()<<'\n';''',
    '批重相加、时间取最大；各批时间才相加；一人仅一批；子集必须非空；固定最小成员所在批仍覆盖所有划分。',
    r'时间 $O(n2^n+3^n)$，空间 $O(n+2^n)$。',tags=['状压 DP'],lessons=D+['subset-enumeration'])

add('P10865','每个鱼格用两位记录剩余条数，一次爆炸各减一',
    '在网格投十字形炸弹，每个覆盖鱼格抓走一条鱼；每格一至三条，求抓光全部鱼的最少炸弹数，位置可以重复使用。',
    r'''炸弹只有落在某个鱼格或它的四邻格才可能有效，枚举这些中心的覆盖集合。每个鱼格剩余零至三条，用一个四进制位，即两二进制位保存。对一次爆炸，只在覆盖且当前非零的位上减一；将全部减少量合成一个掩码，同时减去，不会向其它位借位。f[S]为抓光剩余状态的最少次数，枚举有效炸弹并转向更小状态。''',
    r'''原样例在一一格有两条鱼，所以覆盖它的一次爆炸只能抓一条，还要再炸；不能把“覆盖一个格子”误当“一次清空这格”。同一个中心可以多次投弹，每次对各覆盖格分别抓走至多一条。

一次爆炸覆盖中心和上下左右四格。若它碰不到任何鱼，投下必无帮助；否则中心一定是某个鱼格自身或它的四邻格。因此至多枚举五倍鱼格数个中心，合并相同覆盖集合即可。边界外的中心即使允许，也至多覆盖边界的单个鱼格，不优于直接炸这个鱼格，所以只枚举网格内中心足够。

对第i个鱼格用两位保存剩余数，合法值为零一二三。整个状态S是这些四进制位拼成的整数。S减掉某个非零四进制位上的一，只会令这格鱼数减一，不会向另一格借位。

怎样一次取出所有非零位？每格的低二进制位，或上它的高位右移一位，便表示这格是否非零；再用lowBits仅保留每格的低位。于是nonzero在每个有鱼格的低位为一。与炸弹覆盖的低位掩码cover相交，得到这次实际扣减量dec。

若dec为零，这颗炸弹没有抓鱼，跳过；否则下个状态为S减dec，数值严格小于S。令f[零]为零，从小到大枚举剩余状态，比较一加f[下个状态]。

即使完整编码表里有些状态的鱼数大于输入，该状态也不会由真实起点减鱼到达，不会影响所问答案。表最多四的十次方个状态，每次炸弹用常数次位运算完成同时扣减。''',
    r'''int n,m,k;cin>>n>>m>>k;vector<int>x(k),y(k),fish(k);for(int i=0;i<k;++i) cin>>x[i]>>y[i]>>fish[i];
set<pair<int,int>>centers;int dx[5]={0,1,-1,0,0},dy[5]={0,0,0,1,-1};
for(int i=0;i<k;++i) for(int d=0;d<5;++d){int a=x[i]+dx[d],b=y[i]+dy[d];if(a>=1&&a<=n&&b>=1&&b<=m) centers.insert({a,b});}
set<int>unique;for(auto center:centers){int cover=0;for(int i=0;i<k;++i) if(abs(x[i]-center.first)+abs(y[i]-center.second)<=1) cover|=1<<(2*i);unique.insert(cover);}
vector<int>actions;for(int cover:unique) actions.push_back(cover);int lowBits=0,full=0;
for(int i=0;i<k;++i){lowBits|=1<<(2*i);full|=fish[i]<<(2*i);}
vector<int>dp(full+1,1000000000);dp[0]=0;
for(int state=1;state<=full;++state){
    int nonzero=(state|(state>>1))&lowBits;
    for(int cover:actions){int decrement=nonzero&cover;if(decrement) dp[state]=min(dp[state],1+dp[state-decrement]);}
}
cout<<dp[full]<<'\n';''',
    '一次每个覆盖格只抓一条；同中心可重复炸；每格两位而非一位；只扣非零位，避免借位；网格边界；无效炸弹跳过。',
    r'候选中心至多5k个，时间 $O(k^2+k4^k)$，空间 $O(4^k+k)$。',tags=['状压 DP','位运算'],lessons=D+['sets','bindings','coordinates'])

add('P1450','先求无限硬币方案，再容斥扣掉各类数量超限者',
    '四种面值固定，每次给四种可用枚数与目标总额，求按各类硬币枚数区分的付款方案数。',
    r'''预处理四类硬币无限供应时恰好凑出每个总额的方案数。某类超限意味着至少用了d加一枚，把这部分固定拿走后，剩余仍是无限硬币问题。枚举十六个超限种类子集，奇数类减、偶数类加，对剩余非负总额查表，得到每次全部上限同时满足的数量。''',
    r'''付款方案只看四类各用了多少枚，不看把硬币交给店员的先后。先不考虑每次携带数量，用完全背包预处理ways[s]：ways[零]为一，依次加入四个面值，对金额从小到大累加同一层的ways[s减面值]。

为什么无限方案能处理有限库存？对某一类，超限就是用了至少d加一枚。把这固定的d加一枚先取走，剩下仍允许该类任意非负枚数；它与原超限方案一一对应。所以这一类的坏方案数量，就是无限表在原目标减掉这批固定面额后的值。

同时超限两类时，要取走两批固定硬币，再查一次剩余金额。四类坏事件做容斥：总数减单类坏，补回双类交集，再减三类，最后加四类。十六个子集包含空集，空集便是原总数。

若取走的固定金额已经超过目标，交集不存在，贡献零。乘积(d加一)乘面值可到十的十次方，要用六十四位计算，即使目标只到十万也不能先用int做乘法。

各次购买互相独立，面值相同的不同种类仍按四个枚数分别区分。答案没有取模；无限四类非负枚数的数量最多是金额加三选三，在当前范围内long long足够。''',
    r'''vector<int>coin(4);for(int &c:coin) cin>>c;int queries;cin>>queries;
vector<array<int,5>>data(queries);int maximum=0;for(auto &q:data){for(int &x:q) cin>>x;maximum=max(maximum,q[4]);}
vector<long long>ways(maximum+1);ways[0]=1;
for(int c:coin) for(int sum=c;sum<=maximum;++sum) ways[sum]+=ways[sum-c];
for(auto q:data){
    long long answer=0;
    for(int mask=0;mask<16;++mask){
        long long remaining=q[4];int selected=0;
        for(int i=0;i<4;++i) if(mask>>i&1){remaining-=1LL*(q[i]+1)*coin[i];++selected;}
        if(remaining>=0){if(selected%2) answer-=ways[remaining];else answer+=ways[remaining];}
    }
    cout<<answer<<'\n';
}''',
    '区分枚数而非付款顺序；超限阈值为d加一；坏事件交集容斥；负剩余贡献零；乘法先升六十四位；无需取模。',
    r'设最大目标为S、询问q次，时间 $O(S+16q)$，空间 $O(S+q)$。',tags=['背包 DP','容斥'],lessons=D+['knapsack','counting','standard-array'])

add('P2167','交集方案乘组合系数，容斥留下恰好匹配K个者',
    '若干等长小写字母问号模式，求与其中恰好K个模式匹配的普通小写字符串数，模式重复也分别算一个，模1000003。',
    r'''先求每个模式子集全部同时匹配的字符串数：某位置没有固定字母可选二十六种，固定字母唯一可选一种，冲突则零；各位置相乘。对子集大小j，乘组合数C(j,K)，再按j减K的奇偶做带符号求和。对于实际匹配t个模式的某串，这些权重相加为t选K乘(1-1)的t减K次方，只有t=K留下一个。''',
    r'''先求“同时匹配一个给定集合”比直接要求“恰好”容易。看一个位置：被选模式全写问号，就可任意选二十六字母；有固定字母且全部相同，就只有这个字母；出现两个不同固定字母便冲突，无解。不同位置独立，把各位置选择数相乘，得到ways[S]。

用子集去掉最低置一位的来源，按位置维护“没有固定字母”“指定一种字母”“已冲突”三类值，即可对所有子集线性递推，避免为每个子集重新扫描全部模式。

接着求恰好K个。对每个大小j至少K的集合S，把ways[S]乘j选K，再以j减K为奇数时减、偶数时加：

$$answer=\sum_{|S|\ge K}(-1)^{|S|-K}\binom{|S|}K ways[S].$$

只看一个具体字符串，它若实际匹配t个模式，会被每个选自这t个的集合统计一次。大小j的集合有t选j个，再乘j选K，可改数成“先选K个，再从余下t减K个任选”，因此总权重为

$$\binom tK\sum_{r=0}^{t-K}(-1)^r\binom{t-K}r.$$

若t大于K，这个交错和是(1减1)的正整数次方，为零；t等于K时只有空选择留下一个；t小于K则从未被计入。这样不多不少保留恰好匹配者。

模式即使文本相同，也有不同编号，必须在子集中占不同位。K大于模式数时输出零。组合数用小范围帕斯卡递推即可，不需假定逆元存在；全部运算模一百万零三，减法后正规化。''',
    r'''int tests;cin>>tests;const int MOD=1000003;
while(tests--){
    int n,k;cin>>n>>k;vector<string>s(n);for(string &x:s) cin>>x;
    if(k<0||k>n){cout<<0<<'\n';continue;}
    int states=1<<n,length=s[0].size();vector<int>ways(states,1),size(states),index(states),required(states);
    for(int i=0;i<n;++i) index[1<<i]=i;
    for(int mask=1;mask<states;++mask) size[mask]=size[mask&(mask-1)]+1;
    for(int pos=0;pos<length;++pos){
        required[0]=0;ways[0]=1LL*ways[0]*26%MOD;
        for(int mask=1;mask<states;++mask){
            int bit=mask&-mask,old=required[mask^bit],letter=s[index[bit]][pos]=='?'?0:s[index[bit]][pos]-'a'+1;
            int value=old;
            if(old==-1) value=-1;
            else if(letter){if(old&&old!=letter) value=-1;else value=letter;}
            required[mask]=value;
            if(value<0) ways[mask]=0;else if(value==0) ways[mask]=1LL*ways[mask]*26%MOD;
        }
    }
    vector<vector<int>>choose(n+1,vector<int>(n+1));choose[0][0]=1;
    for(int i=1;i<=n;++i){choose[i][0]=choose[i][i]=1;for(int j=1;j<i;++j) choose[i][j]=(choose[i-1][j-1]+choose[i-1][j])%MOD;}
    long long answer=0;
    for(int mask=0;mask<states;++mask) if(size[mask]>=k){long long value=1LL*choose[size[mask]][k]*ways[mask]%MOD;if((size[mask]-k)%2) answer-=value;else answer+=value;answer%=MOD;}
    cout<<(answer+MOD)%MOD<<'\n';
}''',
    '交集按位置检查冲突；全问号位置有二十六种；相同文本的不同编号分别占位；容斥乘子为子集大小选K；K超范围为零；模减正规化。',
    r'每组长度L，时间 $O(L2^n+n^2)$，空间 $O(2^n+n^2+nL)$。',tags=['状压 DP','容斥'],lessons=D+['strings','counting','modular','subset-enumeration'],key='intersections')

add('P2473','观察本次宝物后决策，再对各种出现情况求平均',
    '独立均匀抛出若干次宝物，可吃或放弃；吃某类前要吃过全部前提类，允许重复得分，求最优策略下总得分期望。',
    r'''f[r][S]表示已吃过种类集合S、还剩r次时的最大未来期望。观察到种类j后，先检查前提，再比较放弃与“本次得分加剩余r减一次的期望”；重复吃仍能得分，只是集合不变。对每种观察分别选好，再按相同概率平均。时间层只读上一层，可滚动数组。''',
    r'''选择发生在看到本次宝物以后，所以不是提前决定“最想吃哪一类”。即使某个宝物当前不允许吃，它出现的概率也没有消失，这次机会只能浪费，仍要计入平均的分母。

短期负分也未必该放弃。例如只抛两次，两类等概率：A得负一且无前提，B得一百但要求先吃A。若第一次看到A，吃它后第二次有一半机会得一百，未来期望五十，合计四十九；直接放弃则以后来不及先解锁再吃B，只能得零。

令f[r][S]回答还剩r次、集合S内的类至少吃过一次时，最大未来期望。零次时所有状态都是零，因为过去得分不在这个状态内重复统计。

若本次观察到j，放弃后是f[r减一][S]。若它的全部前提在S中，吃后候选是p_j加f[r减一][S并入j]；即使j此前已经吃过，本次仍赚p_j，只有解锁集合保持不变。两者选较大。

所有j的出现概率均为一除n，对每个观察各自取得的最优候选求和，再除n。这一步平均的是“观察后已经作出的最佳应对”，不能先把不同宝物分数平均再决定吃不吃。

按剩余次数从零到k计算，两张表滚动。最后读集合为空、还剩k次的值，按题意保留六位小数。环状前提也由可吃条件自然处理，不需要强行把所有种类都解锁。''',
    r'''int throws,n;cin>>throws>>n;vector<int>score(n),required(n);
for(int i=0;i<n;++i){cin>>score[i];int item;while(cin>>item&&item) required[i]|=1<<(item-1);}
int states=1<<n;vector<double>dp(states),next(states);
for(int r=1;r<=throws;++r){
    for(int mask=0;mask<states;++mask){
        double sum=0;
        for(int j=0;j<n;++j){
            double best=dp[mask];
            if((mask&required[j])==required[j]) best=max(best,score[j]+dp[mask|(1<<j)]);
            sum+=best;
        }
        next[mask]=sum/n;
    }
    dp.swap(next);
}
cout<<fixed<<setprecision(6)<<dp[0]<<'\n';''',
    '先观察再选择；不允许吃的出现也占一次机会；负分可解锁后续；重复吃仍得分；只记录至少吃过；读旧时间层。',
    r'时间 $O(kn2^n)$，空间 $O(2^n+n)$。',tags=['状压 DP','期望与概率'],lessons=D+['probability'],checker='reward_fraction')

add('P2831','用两点确定下开口轨迹，再按剩余猪集合递推',
    '从原点发射下开口抛物线，可消灭轨迹上的全部猪，求最少发射数；坐标严格为正且保留两位小数。',
    r'''有用的一条轨迹若至少打中两只横坐标不同的猪，就由这两只唯一确定；只打一只的情况单独保留。预处理每种有效轨迹覆盖的猪集合，f[S]枚举必须打中S最小编号猪的下一发，再转去余下者。把两位小数统一放大成整数，用交叉相乘精确判断同一轨迹，避免误差把接近的点当作共线。''',
    r'''原点、点一三和点三三可以落在同一条下开口曲线上，例如负x平方加四x；这时两只猪只需一发。反之，若两只横坐标相同、纵坐标不同，一条函数曲线不可能同时经过它们。

所有猪横坐标为正，把轨迹等式除以x，得到y除x等于ax加b。任意两只横坐标不同的猪由这个一次关系唯一确定a、b；只有a严格负才是合法轨迹。单个猪总能选一条合法曲线经过，作为单点覆盖保留。

输入保证小数点后两位，将坐标小数点去掉便得到整数X、Y；放大后的曲线仍可写成Y等于AX平方加BX。对两点i、j，记

$$C=Y_iX_j-Y_jX_i.$$

系数A的符号由C除以X_i减X_j的符号决定，因为其它两个X因子都正；所以分子非零且二者异号，轨迹才向下。

对第三点k，不必真的求浮点系数。比较两个斜率后交叉相乘，精确条件为

$$U=Y_kX_i-Y_iX_k,$$

$$U X_j(X_i-X_j)=C X_k(X_k-X_i).$$

三个点满足这个整数等式，便在同一条轨迹上。放大坐标小于一千，乘积在long long范围内。这样极接近却不相等的曲线不会因任意epsilon合并。

令f[S]为消灭剩余集合S的最少发数。选S内任意固定的一只猪p，最终必有某发经过它；把那一发放最前不改变其它轨迹的效果，因此只枚举经过p的候选即可。下一集合是S中删去该轨迹全部覆盖者，严格更小，空集为零。

神秘指令只保证某些数据结构，未增加可用的发射动作；通用算法直接适用所有三种指令。打中后轨迹继续飞行，所以覆盖集合包含它上面的全部猪，不是只算选来定曲线的那两只。''',
    r'''int tests;cin>>tests;
while(tests--){
    int n,command;cin>>n>>command;vector<long long>x(n),y(n);
    for(int i=0;i<n;++i){x[i]=readHundredths();y[i]=readHundredths();}
    vector<vector<int>>cover(n,vector<int>(n));
    for(int i=0;i<n;++i){
        cover[i][i]=1<<i;
        for(int j=0;j<n;++j) if(x[i]!=x[j]){
            long long c=y[i]*x[j]-y[j]*x[i];
            if(c==0||((c>0)==(x[i]>x[j]))) continue;
            for(int k=0;k<n;++k){
                long long u=y[k]*x[i]-y[i]*x[k];
                if(u*x[j]*(x[i]-x[j])==c*x[k]*(x[k]-x[i])) cover[i][j]|=1<<k;
            }
        }
    }
    int states=1<<n;vector<int>dp(states,n);dp[0]=0;
    for(int mask=1;mask<states;++mask){
        int first=0;while(!(mask>>first&1)) ++first;
        for(int other=0;other<n;++other) if(cover[first][other]) dp[mask]=min(dp[mask],1+dp[mask&~cover[first][other]]);
    }
    cout<<dp.back()<<'\n';
}''',
    '开口必须严格向下；同横坐标不同高度不能同一发；单点也可发射；精确两位小数缩放；覆盖所有同曲线猪；指令只是数据保证。',
    r'每组时间 $O(n^3+n2^n)$，空间 $O(n^2+2^n)$。',tags=['状压 DP','计算几何'],lessons=D+['strings','geometry'],
    declarations=r'''long long readHundredths(){
    // 原题保证正数且恰好两位小数，去掉小数点即为放大一百倍。
    string text;cin>>text;long long value=0;
    for(char c:text) if(c!='.') value=value*10+c-'0';
    return value;
}''')

add('P3694','按已放乐队集合确定下个整块的位置与错位人数',
    '重新把各乐队成员排成连续块，可让部分人离开后填回原空位，求最少离队人数，乐队块的顺序可自由选择。',
    r'''选定块顺序后，每队的块长就是它的人数；原位置与目标块不符者必须离队，其余全可留，因此费用是错位人数。f[S]表示已经从左放好乐队集合S的最少费用，前缀长度由这些队的人数和确定。接上j队，新增费用等于队伍人数减去这段原来就是j的人数，前缀计数可常数查询。''',
    r'''离队后回到的必须是留下的空位，不能让未离队者整体向左挤。比如目标某段属于一队，这段里原本就在的一队成员可以全部不动；其它成员必须先离队，之后恰好用全部错位者填好各队的空位。因此最少离队数正好是目标队列与原队列不同的位置数。

每队都要连续，块长是这队总人数，唯一未定的是各块顺序。用S记已经摆在左侧的乐队集合。无论S内如何排序，左边总长len[S]都相同，等于这些队的人数和。

接上还未放的j，它的目标段便是len[S]之后、长度count[j]的一段。用j队原位置的前缀计数，求这一段已经有多少j队成员；这些人留下，剩下count[j]减去这个数量必须离队。

令f[S]为构成左侧这些整块的最少离队人数，对每个j转移到S并入j并加这段费用。各块位置互不重叠，计费恰好覆盖全部错位者，没有重复收费。

每个队至少一人，故集合变大时长度也增加；按掩码递增计算即可。最后读全集。这里费用不是相邻交换次数，也不是逆序对数；一次离队后可以填任意空位。''',
    r'''int n,m;cin>>n>>m;vector<int>a(n+1),count(m);for(int i=1;i<=n;++i){cin>>a[i];--a[i];++count[a[i]];}
vector<vector<int>>prefix(m,vector<int>(n+1));
for(int j=0;j<m;++j) for(int i=1;i<=n;++i) prefix[j][i]=prefix[j][i-1]+(a[i]==j);
int states=1<<m;vector<int>length(states),dp(states,n+1);dp[0]=0;
for(int mask=1;mask<states;++mask){int j=0;while(!(mask>>j&1)) ++j;length[mask]=length[mask^(1<<j)]+count[j];}
for(int mask=0;mask<states;++mask) for(int j=0;j<m;++j) if(!(mask>>j&1)){
    int left=length[mask],right=left+count[j];
    int displaced=count[j]-(prefix[j][right]-prefix[j][left]);
    dp[mask|(1<<j)]=min(dp[mask|(1<<j)],dp[mask]+displaced);
}
cout<<dp.back()<<'\n';''',
    '未离队者保持原位置；目标段长固定；只枚举乐队块顺序；每块扣除原地正确者；费用不是交换次数。',
    r'时间 $O(nm+m2^m)$，空间 $O(nm+2^m)$。',tags=['状压 DP'],lessons=D+['prefix'])

add('P3786','同时保存所在格与已经抱走的西瓜，逐时刻求最少移动',
    '在小网格随时间移动，收集全部指定小西瓜并避开大西瓜，需安全度过所有时刻，求最少移动次数；第一时刻不能移动。',
    r'''预存每时刻每格是否危险、出现哪个可收集西瓜。f[格子][集合]记录当前时刻安全抵达并收集这些西瓜的最少移动；下一刻可原地或到四邻格，只检查新时刻目的格，安全后并入该格小西瓜。初始在给定格检查危险并收集，费用零；一直推到最后时刻，再在已集齐状态中取最小。''',
    r'''时间一已经站在起点，不能先走一步来躲开这一时刻的大西瓜；起点若有小西瓜，则此时就能抱走。以后每个时刻可原地不动，费用零，或走到一个相邻格，费用一。

西瓜可以瞬移，萃香与它同时到达各自新位置，只在每个时刻的最终格子判断相遇；不检查两次位置之间的线段相交，也不因双方途中交换格子而额外判撞。

已经抱走的小西瓜不会再形成新目标，用一个独立编号位记是否得到。即使输入轨迹后来仍在某格列出它，重复并入同一位也不增加任何东西，等价于它已被抱走。

状态f[p][S]描述当前时刻人在格p，已经得到集合S，并且此前全部安全的最少移动数。枚举原地与四邻格q，若下一时刻q危险就拒绝，否则把q此时的小西瓜位并入S，移动费用为q不等于p时的一。

不同时间不能混在同一张表里继续更新，所以每轮写到清空的新表，再交换。到时刻T后，只从包含全部m个目标的状态取最小；找不到就输出负一。

抱齐后仍然要避开之后的大西瓜，不能提前结束；m为零时依然是完整的生存问题。网格最多二十五格，收集位最多十个，按时间扩展完整状态已经足够，不需要只在西瓜出现点之间建不可靠的静态距离。''',
    r'''int h,w,total,sx,sy;cin>>h>>w>>total>>sx>>sy;int n,m;cin>>n>>m;int cells=h*w;
vector<vector<char>>danger(total+1,vector<char>(cells));vector<vector<int>>fruit(total+1,vector<int>(cells));int fruitIndex=0;
for(int i=0;i<n;++i){
    int begin,end,small;cin>>begin>>end>>small;int bit=small?1<<fruitIndex++:0;
    for(int t=begin;t<end;++t){int x,y;cin>>x>>y;int p=(y-1)*w+x-1;if(small) fruit[t][p]|=bit;else danger[t][p]=true;}
}
int start=(sy-1)*w+sx-1;
if(danger[1][start]){cout<<-1<<'\n';return 0;}
vector<vector<int>>neighbors(cells);
for(int u=0;u<cells;++u) for(int v=0;v<cells;++v) if(abs(u/w-v/w)+abs(u%w-v%w)<=1) neighbors[u].push_back(v);
int states=1<<m,INF=1000000000;vector<int>dp(cells*states,INF),next(cells*states,INF);dp[start*states+fruit[1][start]]=0;
for(int t=2;t<=total;++t){
    fill(next.begin(),next.end(),INF);
    for(int u=0;u<cells;++u) for(int mask=0;mask<states;++mask) if(dp[u*states+mask]<INF){
        for(int v:neighbors[u]) if(!danger[t][v]){
            int target=v*states+(mask|fruit[t][v]);next[target]=min(next[target],dp[u*states+mask]+(u!=v));
        }
    }
    dp.swap(next);
}
int answer=INF;for(int p=0;p<cells;++p) answer=min(answer,dp[p*states+states-1]);cout<<(answer==INF?-1:answer)<<'\n';''',
    '第一刻检查起点且不移动；仅检查同时到达后的格子；目标位表示已收集；集齐也要活到最后；无小西瓜仍需避险；坐标x是列。',
    r'轨迹总输入量为Q，时间 $O(Q+Thw2^m)$，空间 $O(Thw+hw2^m)$。',tags=['状压 DP'],lessons=D+['coordinates','numeric-tools'])

add('P3947','集合确定已用时间，最优后缀的排名确定字典序',
    '每首歌恰好完成一次，得分为开放剩余时间减完成时刻与零的较大值；在活动期限内达到目标，输出最高分和字典序最小的完整歌名序列，否则输出No Answer。',
    r'''歌曲集合S的总时长固定，下一首j在这个时刻之后完成，其得分可以直接计算。f[S]保存已经唱过S后能再取得的最高分，枚举下一首，从全集零分向前递推。若时间或总分不达标则无解。重建时对保留最优分的候选，比较下一歌名和其后最优序列排名；逐层压成排名，连同名歌曲也能正确比较。''',
    r'''每首只唱一次，所有歌曲的总时长与顺序无关；若它已经超过活动剩余时间，无论怎样排序都失败。顺序只改变每首完成的时刻，进而改变得分，不能因为某首过了开放时间就不唱它。

设elapsed[S]为唱完集合S的总时长，f[S]为从这时开始，把其余歌全部唱完最多还能赚的分。下一首选j，完成时刻是elapsed[S]加T_j，本次分数为M_j减这个时刻与零取较大；再加f[S并入j]，全部候选取最大。

全集之后没有歌，f[全集]为零；按掩码从大到小计算，来源都是增加了一位的更大集合。最后f[空集]便是最高分，若它仍小于奖励线，也要输出无解。

还要在最优总分内选歌名序列的字典序最小者。只看能达到f[S]的下一首。若下一歌名不同，较小者立即更好；如果名字相同，则要比较后续序列，不能仅因输入编号较小就决定。题面没有必要的重名限制，程序也不依赖这一假定。

按剩余歌曲数逐层处理，每个下一状态的最优后缀已经有排名rank。一个候选序列可以用二元组“下一歌名的编号、下一状态后缀排名”比较；取最小二元组，同时记录选哪首歌。将本层这些二元组排序、相同者赋相同排名，便得到本层正确的后缀字典序。

代码用无符号六十四位整数保存二元组：名字编号放高三十二位，后缀排名放低三十二位。两个编号都小于二的三十二次方，高段比较先决定名字先后，高段相同才比较低段，所以整数比较正好等于二元组的字典序。

歌名已经按字典序输入，可先给连续相同名字赋相同编号。排名只在同长度的序列间比较，不同层各自重新从零编号。根状态记录的选择再接着下一状态的选择，得到完整最优输出。

总共有二的n次方个集合；排序总成本不超过状态数乘其对数，也在n乘二的n次方量级。时间表用题面保证不溢出的int，总分用long long，避免在收益相加时缩窄。''',
    r'''int n;long long target,deadline;cin>>n>>target>>deadline;
vector<string>name(n);vector<int>duration(n),open(n),nameRank(n);long long totalTime=0;
for(int i=0;i<n;++i){cin>>name[i]>>duration[i]>>open[i];totalTime+=duration[i];if(i) nameRank[i]=nameRank[i-1]+(name[i]!=name[i-1]);}
if(totalTime>deadline){cout<<"No Answer\n";return 0;}
int states=1<<n,full=states-1;vector<int>elapsed(states);vector<unsigned char>count(states);vector<vector<int>>layer(n+1);
layer[0].push_back(0);
for(int mask=1;mask<states;++mask){
    int first=0;while(!(mask>>first&1)) ++first;int rest=mask^(1<<first);
    elapsed[mask]=elapsed[rest]+duration[first];count[mask]=count[rest]+1;layer[count[mask]].push_back(mask);
}
vector<long long>dp(states);
for(int mask=full-1;mask>=0;--mask) for(int j=0;j<n;++j) if(!(mask>>j&1)){
    long long gain=max(0LL,1LL*open[j]-elapsed[mask]-duration[j]);dp[mask]=max(dp[mask],gain+dp[mask|(1<<j)]);
}
if(dp[0]<target){cout<<"No Answer\n";return 0;}
vector<int>rank(states);vector<unsigned char>choice(states,255);
for(int used=n-1;used>=0;--used){
    vector<pair<unsigned long long,int>>keys;keys.reserve(layer[used].size());
    for(int mask:layer[used]){
        unsigned long long best=ULLONG_MAX;int selectedName=-1;
        for(int j=0;j<n;++j) if(!(mask>>j&1)){
            if(selectedName>=0&&nameRank[j]>selectedName) break;
            int next=mask|(1<<j);long long gain=max(0LL,1LL*open[j]-elapsed[mask]-duration[j]);
            if(gain+dp[next]!=dp[mask]) continue;
            unsigned long long key=(static_cast<unsigned long long>(nameRank[j])<<32)|static_cast<unsigned int>(rank[next]);
            if(key<best){best=key;choice[mask]=j;selectedName=nameRank[j];}
        }
        keys.push_back({best,mask});
    }
    sort(keys.begin(),keys.end());int current=0;
    for(size_t i=0;i<keys.size();++i){if(i&&keys[i].first!=keys[i-1].first) ++current;rank[keys[i].second]=current;}
}
cout<<dp[0]<<'\n';int mask=0;
while(mask!=full){int j=choice[mask];cout<<name[j]<<'\n';mask|=1<<j;}''',
    '全部歌曲都要完成；过开放期仅得零分；时间总和先判；分数仍需达线；同名时还要比较后缀；后缀排名只在同长度层内比较。',
    r'歌名最大长度L，时间 $O(n2^n+nL)$，空间 $O(2^n+nL)$；按常数次机器字比较排名二元组。',tags=['状压 DP'],lessons=D+['strings','sort','bindings','unsigned64'],exact=True)

DECIMAL_NUMBER=r'''struct Number{
    string digits="0";bool negative=false;
    Number()=default;
    Number(string text){
        size_t pos=0;
        if(!text.empty()&&(text[0]=='-'||text[0]=='+')){negative=text[0]=='-';++pos;}
        while(pos<text.size()&&text[pos]=='0') ++pos;
        digits=pos==text.size()?"0":text.substr(pos);
        if(digits=="0") negative=false;
    }
};
int absoluteCompare(const string &a,const string &b){
    if(a.size()!=b.size()) return a.size()<b.size()?-1:1;
    return a==b?0:(a<b?-1:1);
}
bool lessNumber(const Number &a,const Number &b){
    if(a.negative!=b.negative) return a.negative;
    int order=absoluteCompare(a.digits,b.digits);
    return a.negative?order>0:order<0;
}
string absoluteAdd(const string &a,const string &b){
    string result;int i=int(a.size())-1,j=int(b.size())-1,carry=0;
    while(i>=0||j>=0||carry){
        int value=carry;if(i>=0) value+=a[i--]-'0';if(j>=0) value+=b[j--]-'0';
        result.push_back(char('0'+value%10));carry=value/10;
    }
    reverse(result.begin(),result.end());return result;
}
// 前提：a 不小于 b；两个参数都只含绝对值数字。
string absoluteSubtract(const string &a,const string &b){
    string result;int j=int(b.size())-1,borrow=0;
    for(int i=int(a.size())-1;i>=0;--i){
        int value=a[i]-'0'-borrow-(j>=0?b[j--]-'0':0);borrow=value<0;
        if(borrow) value+=10;result.push_back(char('0'+value));
    }
    while(result.size()>1&&result.back()=='0') result.pop_back();
    reverse(result.begin(),result.end());return result;
}
Number plusNumber(const Number &a,const Number &b){
    Number result;
    if(a.negative==b.negative){result.digits=absoluteAdd(a.digits,b.digits);result.negative=a.negative;}
    else if(absoluteCompare(a.digits,b.digits)>=0){result.digits=absoluteSubtract(a.digits,b.digits);result.negative=a.negative;}
    else{result.digits=absoluteSubtract(b.digits,a.digits);result.negative=b.negative;}
    if(result.digits=="0") result.negative=false;return result;
}
Number timesSmall(const Number &a,int multiplier){
    Number result;if(!multiplier||a.digits=="0") return result;
    result.negative=a.negative^(multiplier<0);long long factor=multiplier;if(factor<0) factor=-factor;
    long long carry=0;string digits;
    for(int i=int(a.digits.size())-1;i>=0;--i){
        long long value=(a.digits[i]-'0')*factor+carry;digits.push_back(char('0'+value%10));carry=value/10;
    }
    while(carry){digits.push_back(char('0'+carry%10));carry/=10;}
    reverse(digits.begin(),digits.end());result.digits=digits;return result;
}'''

add('P4928','按每件衣服还需等待的天数压缩状态，逐日选择',
    '每天必须穿一件未在清洗的衣服，收益为颜色值乘当天可正可负的天气；求全程最高总舒适度，必有一天无衣可穿则输出指定文字。',
    r'''每件衣服记录今天还需跳过几天，零表示可穿，最多六，用七进制合成状态。穿i后，下一天它的计数设为清洗时间，其余正计数减一。逐日最大收益DP，必须选一件，不能因天气负数跳过。用独立可达标记区分负收益和无解；颜色上界未给出，程序用十进制有符号大整数，避免自行设限。''',
    r'''清洗一日的衣服，第一天穿过后第二天不能穿，第三天才可再穿，与原样例一致。因此从“今天早上”转到“明天早上”时，刚穿的衣服计数应设成y，其余衣服则把已有正计数减一，不能把刚设的y也同时减掉。

为每件衣服记一个零至六的计数，零表示此刻可穿，正数表示还需跳过这么多个早上的机会。把这些计数作为七进制各位，n最多四，状态至多七的四次方。

转移可提前预处理。解码一个状态，先让各件旧计数减一到不低于零；对原来为零的衣服i，允许今天穿它，再把它在明天的位设成y_i，得到下一状态。原来非零的衣服今天不能穿，即使经过一晚后会变零也不能提前使用。

f[S]是今天之前已经安全穿完所有天、今早状态为S的最大舒适度。选择可穿i，加上颜色值乘今天的天气，再更新明天的状态。必须每天穿一件，即使今天所有候选收益均负也不能不穿；因此用另一张真假表记可达，不能用零充当所有状态的初值。

若某天没有任何下一状态，全程无解；否则一直完成m天，取所有可达末状态中的最大值。所有衣服的清洗状态最初均零，不需在最后一天后等它们洗完。

原题没有给颜色值上界，而天气绝对值至多一亿。为避免凭空假定总分能放进long long，代码把颜色直接读成十进制字符串，使用符号、绝对值数字串的加法、比较，以及乘有界小整数；不会把极大整数先转成浮点。对应的独立基础课解释全部运算。

这也保留负天气与负总分的准确比较。位数L计入复杂度；颜色再大只会增加逐位运算长度，不会改变清洗状态与选择逻辑。''',
    r'''int n,m;cin>>n>>m;vector<Number>color(n);for(auto &value:color){string text;cin>>text;value=Number(text);}
vector<int>wash(n),weather(m);for(int &x:wash) cin>>x;for(int &x:weather) cin>>x;
vector<int>power(n,1);int states=1;for(int i=0;i<n;++i){power[i]=states;states*=7;}
vector<vector<int>>transition(states,vector<int>(n,-1));
for(int state=0;state<states;++state){
    vector<int>age(n);int value=state,decayed=0;
    for(int i=0;i<n;++i){age[i]=value%7;value/=7;decayed+=max(0,age[i]-1)*power[i];}
    for(int i=0;i<n;++i) if(age[i]==0) transition[state][i]=decayed+wash[i]*power[i];
}
vector<Number>dp(states),next(states);vector<char>reachable(states),nextReachable(states);reachable[0]=true;
for(int day=0;day<m;++day){
    fill(nextReachable.begin(),nextReachable.end(),false);vector<Number>gain(n);
    for(int i=0;i<n;++i) gain[i]=timesSmall(color[i],weather[day]);
    bool any=false;
    for(int state=0;state<states;++state) if(reachable[state]) for(int i=0;i<n;++i){
        int target=transition[state][i];if(target<0) continue;
        Number candidate=plusNumber(dp[state],gain[i]);
        if(!nextReachable[target]||lessNumber(next[target],candidate)){next[target]=candidate;nextReachable[target]=true;any=true;}
    }
    if(!any){cout<<"gcd loves her clothes!\n";return 0;}
    dp.swap(next);reachable.swap(nextReachable);
}
Number answer;bool found=false;
for(int state=0;state<states;++state) if(reachable[state]&&(!found||lessNumber(answer,dp[state]))){answer=dp[state];found=true;}
if(answer.negative) cout<<'-';cout<<answer.digits<<'\n';''',
    '计数零才允许今天穿；刚穿者明天设y，其余计数才递减；负天气仍须穿；负收益不能与零取最大；清洗时间一隔一天再用；颜色读字符串。',
    r'设运算最大位数L，时间 $O(mn7^n L)$，空间 $O(7^n(L+n)+m+nL)$。',tags=['状压 DP','高精度'],lessons=D+['strings','string-tools','structures','decimal-signed','numeric-tools'],declarations=DECIMAL_NUMBER,exact=True)

add('P7296','把字母歌顺序变成最后一个字母的子集递推',
    '自选牛文字母表顺序，反复唱整张表，听到的给定串可以漏字，求最少唱几遍。',
    r'''固定字母顺序后，连续听到的后字若排在前字之前或等于它，就必须开始下一遍；否则可接在同一遍。统计所有相邻字母对次数，f[S]枚举S中哪个字母最后安排，新增它到S内各字母的相邻对次数，初值一遍。行内子集和拆成两半预处理，使每个转移只查两次表，避免每次再扫所有字母。''',
    r'''固定一张字母表后，按听到的字符贪心推进：下一个字母若在当前字母后面，可以在本遍继续；若排在前面，或者与当前相同，就要等下一遍。相同字母在一遍表里也只出现一次，所以等号同样增加遍数。

设count[x][y]为原串中相邻的x后接y的次数。某个字母表顺序的代价，是一加全部“后字不晚于前字”的相邻对次数。没有听到的字母可插入任意空隙，不会影响已听字母的相对顺序，因此只处理出现过的种类。

令f[S]为把集合S的字母排好时，上述相邻对费用的最小值。不是把原串删除其它字母后重新产生相邻对，count始终来自原完整字符串；f只是对这个固定目标式逐步安排字母。

若x排在S最后，它到S内每个字母y的相邻对都会倒退或相等，应增加count[x][y]。S内其它字母之间的费用已在f[S去掉x]中；未进入S的字母稍后再处理。所以枚举x取最小，空集初值一，表示第一遍。

一个转移需要一整行的子集和。将字母分成两半，分别预处理每行在各半子集中的总次数；求完整S时，只查低半与高半两个值相加。每半最多十个字母，两张小表比保存每一行的全部二的二十次方项省空间。

[原站分析](https://usaco.org/current/data/sol_prob1_gold_jan21.html)与题面测试点性质给出的种类数上界要读清：前五个测试点只使用两个名字中的至多八种字母；其余测试点排除Mildred中的六种，至多二十种。这个保证来自测试组，不是因为英文一共只有二十个字母。

输入长度只用于统计相邻对；之后指数项取决于字母种类数，不能把十万长度误当成子集维度。''',
    r'''string text;cin>>text;vector<int>index(26,-1);int n=0;
for(char c:text) if(index[c-'a']<0) index[c-'a']=n++;
vector<vector<int>>count(n,vector<int>(n));
for(size_t i=1;i<text.size();++i) ++count[index[text[i-1]-'a']][index[text[i]-'a']];
int half=n/2,leftStates=1<<half,rightStates=1<<(n-half);
vector<vector<int>>left(n,vector<int>(leftStates)),right(n,vector<int>(rightStates));
for(int row=0;row<n;++row){
    for(int mask=1;mask<leftStates;++mask){int bit=0;while(!(mask>>bit&1)) ++bit;left[row][mask]=left[row][mask^(1<<bit)]+count[row][bit];}
    for(int mask=1;mask<rightStates;++mask){int bit=0;while(!(mask>>bit&1)) ++bit;right[row][mask]=right[row][mask^(1<<bit)]+count[row][half+bit];}
}
int states=1<<n;vector<int>dp(states,text.size()+1);dp[0]=1;
for(int mask=1;mask<states;++mask) for(int last=0;last<n;++last) if(mask>>last&1){
    int added=left[last][mask&(leftStates-1)]+right[last][mask>>half];
    dp[mask]=min(dp[mask],dp[mask^(1<<last)]+added);
}
cout<<dp.back()<<'\n';''',
    '相等也要下一遍；只统计原串已有相邻对；不重新拼接过滤串；出现种类数由测试性质至多二十；子集和包括自身。',
    r'种类数为q、输入长L，时间 $O(L+q2^q)$，空间 $O(2^q+q2^{\lceil q/2\rceil}+q^2)$。',tags=['状压 DP'],lessons=D+['strings'])

add('P9017','分离初始开关的影响，再按循环旋转合并可达效果',
    '每步先翻一个开关、按当前全部开关翻灯、最后右旋开关；多组相同长度，求灯全灭的最少步数，最终开关可以任意。',
    r'''固定步数k，将初始开关自然产生的灯光变化先异或掉，剩下只问初始开关全零时可产生哪些效果。一次在最前翻的开关会在后面k步影响连续旋转的k个位置；这些效果的可达集合对整体旋转不变，用旋转轨道代表元存真假，转移仍扫描每种实际位形，保留相对朝向。预处理至3N步，每问按步数从零尝试并更新初始开关基线。''',
    r'''一步的顺序不能交换：先选一个开关翻转，再让所有活跃开关翻对应灯，最后开关整体右移。灯本身不旋转，结束只要求灯全灭，并不要求开关全关。

先给步数一个上界。[原站分析](https://usaco.org/current/data/sol_prob2_gold_jan23.html)采用如下构造：不断选择活跃开关将其关闭，至多N步能让开关全零，旋转不会改变活跃数量。然后逐个处理仍亮的灯：把对应开关打开，下一步把旋转后这个唯一活跃开关关掉，两步只把指定灯翻一次。因此总能在至多3N步完成。

把全部变化看成异或。若完全不再手动翻开关，初始开关S在前k步造成的灯光变化是S、旋转一次S、直到旋转k减一次S的异或。称它为base_k，便可把一个询问化为：初始开关全零时，恰好k步能否产生lights异或base_k这个效果。

再看零开关的可达效果。第一步翻某个位置后，这次翻转的影响会在之后每一步随开关旋转，一共影响k个连续位置，重复绕圈时按异或抵消。去掉这次翻转，其余k减一步仍能任意选择，因此可以从上一层的可达效果，异或上一个任意朝向的“连续k次翻转”图形。

所有位置地位相同，若一个效果可达，它的任何整体旋转也可达。把循环旋转互相可达的位串归为一组，每组取一个代表，仅为代表保存可达真假；计算新层时，固定新增图形的一个朝向，再扫描上一层每种实际旋转位形，便枚举了所有相对朝向。最终只需把结果归回代表组。

不能只对上一层的代表本身转移一次。例如N为三，前层能产生任意一个亮位；固定新增图形011，与实际位形100异或可以得到111。若只拿代表001异或，就只得到010，漏掉111。因此代码仍遍历所有实际mask，查询其组的真假。

预处理can[k][代表]，零步只有零效果。固定朝向的图形每增加一步，就再异或第(k减一)模N位；这同时正确处理绕圈。每层只扫描二的N次方个mask，不再额外枚举N个新图形朝向。

查询从零至3N逐个尝试，首次可行即最少。恰好步数的可达性不单调，不能二分。字符串左起第一位编码为最低位时，题目的字符串右旋对应整数的左移加高位绕回，方向需要与编码一起确定。''',
    r'''int tests,n;cin>>tests>>n;int states=1<<n,full=states-1;
auto rotate=[&](int mask){return ((mask<<1)&full)|(mask>>(n-1));};
auto parse=[&](const string &s){int mask=0;for(int i=0;i<n;++i) if(s[i]=='1') mask|=1<<i;return mask;};
vector<int>representative(states,-1);
for(int mask=0;mask<states;++mask) if(representative[mask]<0){
    int current=mask;while(representative[current]<0){representative[current]=mask;current=rotate(current);}
}
vector<vector<unsigned char>>can(3*n+1,vector<unsigned char>(states));can[0][representative[0]]=true;int pad=0;
for(int steps=1;steps<=3*n;++steps){
    pad^=1<<((steps-1)%n);
    for(int mask=0;mask<states;++mask) if(can[steps-1][representative[mask]]) can[steps][representative[mask^pad]]=true;
}
while(tests--){
    string a,b;cin>>a>>b;int lights=parse(a),switches=parse(b),baseline=0,answer=-1;
    for(int steps=0;steps<=3*n;++steps){
        if(can[steps][representative[lights^baseline]]){answer=steps;break;}
        baseline^=switches;switches=rotate(switches);
    }
    cout<<answer<<'\n';
}''',
    '先翻开关再翻灯再旋开关；灯不旋转；最终开关不受限；初始开关基线需逐步旋转；同轨道转移仍遍历实际朝向；精确步数不能二分；零步可行。',
    r'长度N、询问T次，时间 $O(N2^N+TN)$，空间 $O(N2^N)$；可达表使用每项一字节。',tags=['状压 DP','位运算'],lessons=D+['strings','lambda-local'])

add('CF11D','固定环的最小编号为起点，计路径后除去反向重复',
    '简单无向图，统计不重复顶点的简单环数；同一环换起点或反向经过视为同一个，长度至少三。',
    r'''dp[S][last]记录从S的最小编号点出发、恰好走过S且结束于last的简单路径数。单点路径为一，只向大于起点的未访问邻居扩展，保证起点始终最小；若至少三点且last与起点相邻，就能闭合。这样每个环只留下最小点这个起点，但正反两个方向仍各计一次，最终除二。''',
    r'''四点完全图的三角环有四个、四边环有三个，共七个。仅按走法逐次计数，会把同一个环的每个起点、每个方向重复算进去；需要明确消掉哪种重复。

规定环中编号最小的点为唯一起点。状态dp[S][last]是从min(S)出发、每点恰好用一次、经过集合S并停在last的路径数。每个单点集合在自己那里有一条长度零路径。

扩展时只允许访问未在S中的邻居，而且这个邻居必须比起点编号大。这样不会在中途引入更小点改变起点，任意一条以最小点开始的简单环仍能沿某个方向走完，因此限制没有漏掉合法环。

至少走过三点后，若last与起点有边，可闭合成简单环，累加当前路径数。两点来回只重复同一条无向边，不是简单环，不能计入。

最小起点已经去掉轮换起点的重复，但沿顺时针和逆时针走，仍是两条不同路径；它们对应同一个无向环，且长度至少三时两个方向不同。因此全部累加后恰好除二。

去掉最低置一位可预处理集合大小，独立记录每个单独位对应的编号，枚举候选位时不需要编译器特有函数。把二维表铺成一维长数组，位置mask乘n加last；十九点时约七十六MiB，避免额外的逐行容器开销。

环数以及中间路径数都用long long。可以包含额外弦边，简单环只要求当前环本身不重顶点，不要求它是诱导环。图不连通也直接由同一状态递推处理。''',
    r'''int n,m;cin>>n>>m;vector<int>adjacent(n);
for(int i=0,u,v;i<m;++i){cin>>u>>v;--u;--v;adjacent[u]|=1<<v;adjacent[v]|=1<<u;}
int states=1<<n;vector<int>index(states);vector<unsigned char>size(states);
for(int i=0;i<n;++i) index[1<<i]=i;
for(int mask=1;mask<states;++mask) size[mask]=size[mask&(mask-1)]+1;
vector<long long>dp(size_t(states)*n);for(int i=0;i<n;++i) dp[size_t(1<<i)*n+i]=1;
long long directedCycles=0;
for(int mask=1;mask<states;++mask){
    int first=index[mask&-mask],greater=~((1<<(first+1))-1);
    for(int lastBits=mask;lastBits;lastBits&=lastBits-1){
        int last=index[lastBits&-lastBits];long long ways=dp[size_t(mask)*n+last];if(!ways) continue;
        if(size[mask]>=3&&(adjacent[last]>>first&1)) directedCycles+=ways;
        int candidates=adjacent[last]&~mask&greater;
        while(candidates){int bit=candidates&-candidates;candidates^=bit;int next=index[bit];dp[size_t(mask|bit)*n+next]+=ways;}
    }
}
cout<<directedCycles/2<<'\n';''',
    '环至少三点；只向大于最小起点者扩展；加入者必须未访问；闭合后仍可继续形成更长环；仅除反向二重，不再除长度；弦边不妨碍简单环。',
    r'时间 $O(n^2 2^n)$，空间 $O(n2^n)$。',tags=['状压 DP','组合计数'],lessons=D+['graphs','counting','subset-enumeration'])
