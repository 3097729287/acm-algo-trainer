"""Greedy and constructive problems, with problem-specific exchange arguments."""
from core7_authoring import add

A=['io-basics','arrays','vector','basic-control']
S=A+['sort','iterators']

add('P1031','统计前缀不平衡的分界线','纸牌只能在相邻堆之间搬运，一次可以搬任意张，求把各堆均分的最少搬运次数。',
    '算出平均数 avg，再扫描每条相邻分界线：前 i 堆的总数与 i×avg 不相等，就必须有一次搬运跨过这条线。统计这些非零前缀差即可。',
    r'''样例四堆 [9,8,17,6] 平均每堆十张。前三条分界线左侧分别少一、少三、多四张，因此三条线都必须跨过，答案至少三次。

令 balance 是前 i 堆总数减去 i×avg。纸牌在同一侧内部移动，不改变这一侧的总数；要把 balance 调成零，必须跨过第 i 与 i+1 堆之间的线。一次操作只跨一条线，因此每条非零分界线各贡献至少一次，不能用一次远距离搬运同时解决多条线。

这个下界能达到：把每条线上应流动的净数量设为 balance，正数向右、负数向左。最终各堆的流入流出恰好弥补自己的盈亏。只有一条直线，不存在有向环，按流向的先后先让上游送牌、再让下游转送，保证真正搬出时有足够的牌；每条非零线一次送完。这样既不需要实际把某堆记成负数，也恰好使用所统计的次数。

扫描时加上 a[i]−avg 就更新了 balance，只统计前 n−1 条线；最后的全体总差必为零。''',
    r'''int n;cin>>n;vector<long long>a(n);long long total=0;
for(auto &x:a){cin>>x;total+=x;}long long average=total/n,balance=0;int answer=0;
for(int i=0;i+1<n;++i){balance+=a[i]-average;answer+=balance!=0;}
cout<<answer<<'\n';''',
    '一次只允许跨相邻边界；统计非零边界数，不是搬运的纸牌张数。',
    '时间与保存输入的空间均为 $O(n)$。',tags=['贪心','前缀和'],lessons=A+['prefix','greedy'])

add('P1208','按单价从低到高采购','每个供应商有单价和供应上限，牛奶可以按整数单位分购，求买足需求量的最低费用。',
    '把供应商按单价升序排列，从当前最便宜的供应商尽量购买，数量取剩余需求与其上限的较小值，直到买足。',
    r'''样例中需求一百单位，先买三分的十单位、五分的二十单位、六分的三十单位，剩下四十单位从八分的供应商购买，九分的一点也不需要。

牛奶没有其它区别，也没有“启用某个供应商要先付固定费用”这样的条件。若一个方案还没用完更便宜的供应，却购买了一单位更贵的牛奶，就可以将这一单位换到便宜供应商，不影响总量且不会增加费用。不断交换，就得到按低价先买的方案，因此贪心可行。

当前可以买的量是 min(remaining,available)，不能不顾需求把整批都买下。费用乘数量用 long long，需求为零时总费用就是零，供应量为零也可自然跳过。题目保证总供应足够。''',
    r'''long long need;int m;cin>>need>>m;vector<pair<int,int>>farm(m);for(auto &f:farm)cin>>f.first>>f.second;
sort(farm.begin(),farm.end());long long answer=0;
for(auto f:farm){long long take=min(need,(long long)f.second);answer+=take*f.first;need-=take;if(need==0)break;}
cout<<answer<<'\n';''',
    '允许只买一批的一部分；不按供应量排序，不购买超过需求的牛奶。',
    r'时间 $O(m\log(m+1))$、空间 $O(m)$。',tags=['贪心','排序'],lessons=S+['greedy','integer'])

add('P1478','过滤高度后优先摘低耗苹果','苹果必须能够够到，摘取会消耗有限力气，求剩余力气不变负时最多摘几个。',
    '先保留高度不超过椅子加手长的苹果，再把耗力升序排序，能付得起就摘取；第一次付不起时即可结束。',
    r'''“够得到”和“付得起”是两个独立条件：再省力的苹果，如果高度超过 a+b，也不能选择。因此先过滤高度，后面的优化只面对可摘苹果的耗力。

每个苹果都只贡献一个数量。若选中的某个苹果耗力较高，而一个未选且够得到的苹果耗力更低，交换两者不改变数量，并且更省力。所以摘 k 个的最低耗力，一定是全部可摘苹果中最小的 k 个耗力之和。按升序累加，能取多长的前缀就是最大数量。

某个耗力恰好等于剩余力气也可以摘，摘完变零仍合法；耗力为零的苹果不能遗漏。排序后遇到一个付不起的，后面的耗力只会更大，可以直接停止。''',
    r'''int n,s,a,b;cin>>n>>s>>a>>b;vector<int>cost;
while(n--){int height,energy;cin>>height>>energy;if(height<=a+b)cost.push_back(energy);}
sort(cost.begin(),cost.end());int answer=0;
for(int energy:cost){if(energy>s)break;s-=energy;++answer;}cout<<answer<<'\n';''',
    '高度和力气比较都包含等号；耗力零的可达苹果也能摘。',
    r'时间 $O(n\log(n+1))$、空间 $O(n)$。',tags=['贪心','排序'],lessons=S+['greedy'])

add('P2695','从小头开始匹配最便宜可用骑士','一位骑士至多砍一个不大于其能力的龙头，费用等于其能力，求砍完所有头的最小费用。',
    '头和骑士能力都升序排列。依次处理最小的未砍头，跳过能力不足的骑士，使用第一个够用的骑士。',
    r'''样例头大小四、五，骑士能力四、七、八。先让四砍四，再让七砍五，费用十一；能力不足的骑士不能留下来砍后面更大的头。

设当前最小的头为 h，最小的够用骑士为 c。若某个完整最优方案让更贵的 d 砍 h：c 若没被用，直接替换即可省钱；c 若用于另一个更大的头 t，就交换两人的工作。原来 c≥t，所以 d≥c≥t，d 也能砍 t，交换不影响合法性与总费用。因此总存在一个最优方案使用当前贪心配对。

删去这一对后，剩余问题形式不变，继续即可。若遍历完全部骑士仍有头没砍掉，任何未使用骑士都不存在，必然无解，按题目要求输出固定文本。每人一用，指针匹配后都必须前进。''',
    r'''int n,m;cin>>n>>m;vector<int>head(n),knight(m);for(int &x:head)cin>>x;for(int &x:knight)cin>>x;
sort(head.begin(),head.end());sort(knight.begin(),knight.end());int i=0;long long cost=0;
for(int ability:knight)if(i<n&&ability>=head[i]){cost+=ability;++i;}
if(i==n)cout<<cost<<'\n';else cout<<"you died!\n";''',
    '能力等于头大小就够用；同一骑士不能重复匹配。',
    r'时间 $O(n\log n+m\log m)$、空间 $O(n+m)$。',tags=['贪心','排序','双指针'],lessons=S+['greedy','two-pointers','integer'])

add('P4995','从地面开始交替选择最高与最低','从高度零出发，每块石头恰好跳一次，代价为相邻高度差的平方，求最大总代价。',
    '高度升序排序。从零先跳最高石头，再跳剩余最低、剩余最高，交替取两端，每跳一次累加实际高度差的平方。',
    r'''对于高度三、五、六，从地面依次跳六、三、五，体力为 36+9+4=49。不能每次只取剩余最高，那样会把相近的高石头挨在一起，浪费较大的高度差。

关键是证明交替取两端。假设当前高度 x 不高于所有剩余石头，想先跳最大剩余高度 r。任取一个最优余程，如果 r 尚未在第一位，余程形如 x→v→…→r→w→…，将 v 到 r 这一整段反转，改成 x→r→…→v→w→…。内部各条边只反了方向，平方差完全相同；变化的两条边带来增量

$$ (x-r)^2+(v-w)^2-(x-v)^2-(r-w)^2=2(w-x)(r-v)\ge0. $$

因为 w≥x、r≥v，反转不会减少体力。若 r 原本是最后一项，只需比较第一条边：从最小端 x 跳最大 r 也不会更差。于是可以把最大者放到下一步而不损失最优性。

当前高度成为最大者后，对称地把最小剩余高度 l 提到下一步；同样反转证明的增量为 2(x−w)(v−l)≥0。每步取完的高度又是剩余集合外侧的一端，论证可以反复使用，得到最高、最低交替。左右两个指针负责剩余区间，用 long long 计算差值平方和。''',
    r'''int n;cin>>n;vector<long long>h(n);for(auto &x:h)cin>>x;sort(h.begin(),h.end());
int l=0,r=n-1;long long last=0,answer=0;bool high=true;
while(l<=r){long long next=high?h[r--]:h[l++],difference=next-last;answer+=difference*difference;last=next;high=!high;}
cout<<answer<<'\n';''',
    '第一跳也要计费；不能再次回到地面；平方和使用 long long。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序'],lessons=S+['greedy','integer'])

add('P5639','统计初始开关状态的连续段','所有监控每秒同时翻转开关，初始第一个关闭，一秒可经过任意多个连续关闭监控，求最短通过时间。',
    '第一秒穿过开头整段零；下一段必为一，恰好在下一秒全部变零，如此逐段前进。答案等于初始数组中相同数字连续段的数量。',
    r'''样例 0,0,1,1,0,1 分成四段：[0,0]、[1,1]、[0]、[1]。第一次行动能穿过第一段，但下一段此时开启；下一秒所有开关翻转，第二段关闭，可以继续穿过。段与段的初始状态交替，因此每一次正好接上下一段。

一次行动不能同时穿过初始状态不同的相邻两段，因为任意同一秒，它们的开关仍相反，至少一段开启。所以每一段至少各需要一次通过行动，是一个下界。上述连续行动每秒穿过一整段，恰好达到它，不需要额外原地等候。

读入时只保留前一个开关值：第一个值开启答案的一段，后面每次与前项不同就开始新段。n 最大一百万，无须保存整个数组；即使全部为零，仍要花一秒通过，答案为一。''',
    r'''int n;cin>>n;int previous=-1,answer=0;
for(int i=0;i<n;++i){int x;cin>>x;if(i==0||x!=previous)++answer;previous=x;}cout<<answer<<'\n';''',
    '统计连续段，不是零或一的数量；全零也要一秒。',
    '时间 $O(n)$、额外空间 $O(1)$。',tags=['贪心'],lessons=['io-basics','basic-control','greedy'])

add('B3753','按二进制从高位构造','使用压入一、复制栈顶、弹出两项相加三种操作，用不超过二百条指令得到唯一的目标整数 n。',
    '先压入一，代表 n 的最高二进制位。每处理后面一位，输出 dup、add 把现值翻倍；该位为一时，再输出 1、add 加一。',
    r'''得到十三（二进制 1101）时：先放一；处理下一位一，先翻倍成二再加一成三；处理零，只翻倍成六；最后处理一，翻倍为十二再加一为十三。

若当前栈只有一个数 v，dup 把它变成两个 v，add 再合成 2v；若要加一，就先压入一，此时有 v、一两个数，add 合成 v+1。这两组操作前后栈都恰好只有一项，因此后续每次复制与相加也始终合法，不会出现空栈或不足两项。

按二进制从高到低读下一位 bit，当前前缀的数值更新为 2v+bit，刚好与这些操作一致。n≤十的九次方，不超过三十个二进制位；最高位只需一条，后面每位最多四条，至多 117 条，严格小于二百。代码先用除二提取位，再逆序遍历，不需要真的维护数值栈。''',
    r'''int n;cin>>n;vector<int>bits;while(n){bits.push_back(n%2);n/=2;}
cout<<"1\n";for(int i=(int)bits.size()-2;i>=0;--i){cout<<"dup\nadd\n";if(bits[i])cout<<"1\nadd\n";}''',
    'dup 和 add 必须小写；翻倍后根据下一位决定是否加一，不能把最高位重复处理。',
    r'指令数、时间与位数组空间均为 $O(\log n)$。',tags=['构造','位运算'],lessons=A+['bitwise','construction'],checker='stack_computer')

add('P1056','分别选择能隔开最多对的横纵通道','给出只在相邻位置交谈的同学对，选择规定条数的横向和纵向通道，使未被隔开的交谈对最少。',
    '上下相邻的交谈对只会被它们之间那条横线隔开，左右相邻同理。分别统计每条横线与竖线的收益，各自选收益最大的规定条数，最后按位置升序输出。',
    r'''一对上下相邻的同学，只能由中间的横通道隔开，任何竖通道都不起作用。左右相邻的情况正相反。因此每对交谈唯一归属于一条候选通道，没有同一对被横、竖同时覆盖的重复计算问题。

对上下相邻的行号 x、p，通道编号为 min(x,p)，表示这一行与下一行之间；左右相邻则取列号的较小者。分别累加 row 与 column 的计数。因为每条通道的收益相互独立，若选了低收益线却没选高收益线，交换后会更优，所以直接选最大的 K 条横线与 L 条竖线。

选择依据是收益，但题目输出顺序要求通道编号升序，因此取出编号后还要再排序。K 或 L 为零时对应输出一个空行。题目保证最优方案唯一，不必额外设计不同最优方案间的优先级。''',
    r'''int m,n,k,l,d;cin>>m>>n>>k>>l>>d;vector<int>rows(m),columns(n);
while(d--){int x,y,p,q;cin>>x>>y>>p>>q;if(x!=p)++rows[min(x,p)];else ++columns[min(y,q)];}
print_best(rows,k);print_best(columns,l);''',
    '横通道编号来自行，纵通道来自列；选完按位置输出，不按收益顺序输出。',
    r'时间 $O(d+m\log m+n\log n)$、空间 $O(m+n)$。',tags=['贪心','排序'],lessons=S+['functions','greedy'],
    declarations=r'''void print_best(const vector<int>&counts,int number){
    vector<pair<int,int>>rank;for(int i=1;i<(int)counts.size();++i)rank.push_back({counts[i],i});
    sort(rank.rbegin(),rank.rend());vector<int>answer;for(int i=0;i<number;++i)answer.push_back(rank[i].second);
    sort(answer.begin(),answer.end());for(int i=0;i<number;++i){if(i)cout<<' ';cout<<answer[i];}cout<<'\n';
}''',exact=True)

add('P2431','枚举与上界最高不同的二进制位','每个二的幂重量只有一个，选择总重量在 A 到 B 之间，求最多能选几个月饼。',
    '所选集合与总重量的二进制一位一一对应。考虑 B 本身，再依次将 B 的某个一位改为零、低位全部置一；候选仍不小于 A 时统计一位数，取最大值。',
    r'''重量一、二、四、八……各一份，任意总重量的二进制表示唯一，所以月饼个数就是总重量中一的个数。问题变成在闭区间 [A,B] 内找一位最多的整数，不是让总重量尽可能接近 B。

任意 X<B，找到它与 B 从高到低第一处不同的二进制位 k。这一位一定是 B 为一、X 为零，更高位相同。固定这个共同高位前缀与第 k 位零后，将低 k 位全部设成一，得到候选 Y。它仍小于 B，且 Y≥X，所以若 X≥A，就一定有 Y≥A；这一类中 Y 的低位全是一，一位数量也不会少于 X。因此只需枚举 B 中每一个为一的位置，再加上 B 自身，就覆盖了所有可能最优类别。

第 k 位的低位掩码为 2^k−1，把 B 从第 k 位起全部清零，再接上这个掩码。下界检查不能省略，例如只顾低位填一可能让候选落在 A 以下。使用无符号 64 位，第 k 位最多到六十二，避免有符号最高位移位问题。''',
    r'''unsigned long long A,B;cin>>A>>B;int answer=ones(B);
for(int k=0;k<63;++k)if((B>>k)&1ULL){
    unsigned long long bit=1ULL<<k,low=bit-1,candidate=(B&~(low|bit))|low;
    if(candidate>=A)answer=max(answer,ones(candidate));
}cout<<answer<<'\n';''',
    '优化的是一位个数；候选需满足下界；位移使用 1ULL，不能用 int 的一。',
    '有效位数为 L≤63，手工计位时总时间 $O(L^2)$、额外空间 $O(1)$。',tags=['贪心','位运算'],lessons=['io-basics','basic-control','bitwise','functions','integer'],
    declarations=r'''int ones(unsigned long long x){int count=0;while(x){count+=x&1ULL;x>>=1;}return count;}''')

add('P2949','按截止时间扫描并反悔删除低收益任务','每个任务耗时一个单位且必须按截止时间完成，任务可不做，求能得到的最大总收益。',
    '按截止时间升序读任务，把收益加入小根堆；若所选任务数超过当前截止时间，就删掉堆中收益最小的一项。最终收益总和即答案。',
    r'''截止时间为一的任务，最多保留一个；截止时间为二时，累计最多保留两个。样例两个截止一的任务收益五、七，只保留七；再纳入截止二、收益十的任务，总收益十七。

一组单位耗时任务按截止时间排好后可行，当且仅当第 i 个任务截止时间至少为 i。由此，在已经扫描到截止时间 d 时，候选中最多能保留 d 个。当前堆保存之前保留下来的任务，按截止时间原本可安排；加入新任务后，若数量不超 d，就能排在这些任务之后；若超了，只多出一个，去掉任何一项都能恢复这一轮的容量，删除低收益项最划算。

这是一种允许反悔的选择：早截止的候选一旦争夺同一批有限时隙，应优先保留更高收益者，后来出现同样或更高截止的任务仍可再替换堆里更低收益者。所有早截止的容量限制会在扫描到相应 d 时立即生效，后面的时隙不能弥补已过的截止时间，不能等到最后只按总任务数截断。单位耗时是关键；任务时长不同时，删最小收益不再保证最优。

小根堆使删除当前最小收益为对数时间，加入时给总和加收益，弹出时减去堆顶。截止时间可达十的九次方，不应按时间逐个建槽；堆最多保存 n 项。收益总和用 long long。''',
    r'''int n;cin>>n;vector<pair<int,long long>>jobs(n);for(auto &job:jobs)cin>>job.first>>job.second;sort(jobs.begin(),jobs.end());
priority_queue<long long,vector<long long>,greater<long long>>chosen;long long answer=0;
for(auto job:jobs){chosen.push(job.second);answer+=job.second;
    if((long long)chosen.size()>job.first){answer-=chosen.top();chosen.pop();}
}cout<<answer<<'\n';''',
    '按截止时间排序，堆里按收益最小优先；时间单位为一是本算法的前提。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','堆','排序'],lessons=S+['heap','greedy','integer'])

add('P12041','零代价关系先合并再构造边权','无向图每条边给出其两端之间所有路径的最小 mex，判断能否赋非负边权并构造，允许重边与自环。',
    '单条边本身就是路径，所以给定值只能为零或一。把给定值为零的边两端用并查集合并；若值一的边两端落在同一集合就无解，否则值零的边赋一、值一的边赋零。',
    r'''这是一道普通输入输出构造题，不需要发出交互询问。mex 为零，等价于路径中完全没有权值零。非自环的一条边自身形成的路径，mex 只能为零（边权非零）或一（边权为零），因此任何大于一的给定值都不可能；自环两端相同，还必须满足题目特定的 f(u,u)=0。

把全部非零权边暂时看成可走的“正边”。f(u,v)=0 当且仅当 u、v 能通过正边连通。于是给定值零要求它们属于同一个正边连通块，这种关系具有传递性，用并查集求出所有被强制合并的点。

如果一条给定值一的边两端已经被这些零关系连通，就已经存在不含零边的路径，使最小 mex 为零，与一矛盾，判无解。否则，把给定零的原边全部赋一，它们确实在各个并查集内部提供了正边路径；把给定一的原边全部赋零，不会连接正边连通块。后者的两端没有正边路径，所以代价不能为零；而这条零边自身提供 mex 为一的路径，故最小值恰好为一。所有要求同时满足。

重边逐条输出即可。自环给定零也可赋一，空路径保证 f(u,u)=0；自环给定一会在并查集检查时自然失败。''',
    r'''int n,m;cin>>n>>m;DSU dsu(n);vector<int>u(m),v(m),f(m);bool ok=true;
for(int i=0;i<m;++i){cin>>u[i]>>v[i]>>f[i];--u[i];--v[i];if(f[i]>1)ok=false;if(f[i]==0)dsu.join(u[i],v[i]);}
for(int i=0;i<m;++i)if(f[i]==1&&dsu.find(u[i])==dsu.find(v[i]))ok=false;
if(!ok){cout<<"No\n";return 0;}cout<<"Yes\n";
for(int i=0;i<m;++i)cout<<(f[i]==0?1:0)<<(i+1==m?'\n':' ');''',
    '输入给的是端点最小路径 mex，不是原边权；自环的两端最小值必须为零。',
    r'并查集按大小合并并压缩路径，时间 $O((n+m)\alpha(n))$、空间 $O(n+m)$。',tags=['构造','并查集'],lessons=A+['functions','dsu','construction'],checker='mex_graph',
    declarations=r'''struct DSU{
    vector<int>p,size;
    DSU(int n):p(n),size(n,1){iota(p.begin(),p.end(),0);}
    int find(int x){while(x!=p[x]){p[x]=p[p[x]];x=p[x];}return x;}
    void join(int a,int b){a=find(a);b=find(b);if(a==b)return;if(size[a]<size[b])swap(a,b);p[b]=a;size[a]+=size[b];}
};''')

add('AT_arc161_c','自底向上传递被迫的父亲颜色','树的每个点度数都是奇数，所有点同时改为邻居的多数颜色；给定改色结果，构造改色前的颜色或判断无解。',
    '从叶子向根处理。某点原颜色若未被孩子强制，就优先设成父亲想看到的颜色；数完孩子的颜色，若还差一票就强制父亲颜色，差超过一票则无解。根必须仅靠孩子达到多数。',
    r'''目标 S[u] 约束的是 u 的邻居原颜色，不是 u 自己的原颜色。例如一个叶子只有父亲这一个邻居，因此叶子的目标色必然强制父亲的原颜色。两个叶子要求同一个父亲为不同颜色时，立刻无解。

把题目的一号点作为根，代码将全部编号减一存储。先得到父子关系和一个父亲在孩子之前的遍历顺序，再逆序处理，保证每个点的孩子都处理完。各孩子可能对 u 的原颜色提出“必须为黑／白”的要求；有冲突就无解。若没有要求，u 的原颜色怎样都不妨碍已处理孩子，于是选 S[parent[u]]，给父亲的多数判定提供最有利的一票；根没有父亲，任取一色即可。

接着检查 u 自己的目标。度数为 deg 时，需要 need=(deg+1)/2 个邻居原色等于 S[u]。孩子中有 match 票：若 match≥need，父亲任意；若 match=need−1，必须强制父亲原色为 S[u]；若 match<need−1，父亲最多再加一票也不够，无解。根没有父亲，所以必须直接 match≥need。

为什么孩子未被强制时可以都取有利颜色？孩子的原颜色只参与它父亲及它孩子的多数判定，后者已经确认对它没有额外要求；当前只需尽量帮助父亲，不会损害别的点。对孩子真正被强制的情况则绝不擅改。逐层记录这个自由或被迫状态，便保留了所有可能解所需要的选择。全程用显式遍历顺序，避免二十万点深树递归栈溢出。''',
    r'''int tests;cin>>tests;while(tests--){int n;cin>>n;vector<vector<int>>g(n);
    for(int i=1;i<n;++i){int u,v;cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
    string target;cin>>target;vector<int>parent(n,-1),order(1,0),color(n,-1);parent[0]=-2;
    for(int i=0;i<(int)order.size();++i){int u=order[i];for(int v:g[u])if(v!=parent[u]){parent[v]=u;order.push_back(v);}}
    bool ok=true;
    for(int at=n-1;at>=0&&ok;--at){int u=order[at],p=parent[u];
        if(color[u]<0)color[u]=p<0?0:target[p]=='B';
        int match=0;for(int v:g[u])if(parent[v]==u)match+=color[v]==(target[u]=='B');
        int need=((int)g[u].size()+1)/2;
        if(match>=need)continue;
        if(p<0||match+1<need){ok=false;break;}
        int forced=target[u]=='B';if(color[p]>=0&&color[p]!=forced){ok=false;break;}color[p]=forced;
    }
    if(!ok)cout<<"-1\n";else{for(int c:color)cout<<(c?'B':'W');cout<<'\n';}
}''',
    '约束来自邻居原色，不能把原色直接等同目标色；根没有父亲可补票。',
    '每组时间与空间均为 $O(n)$。',tags=['贪心','构造','DFS'],lessons=A+['strings','trees','construction'],checker='majority_tree')

add('B4225','保留端点后递归设计目标平均值','初始黑板依次为 a 到 b，允许把两个同奇偶数替换成平均数，输出使最终只剩 x 的位置操作，位置会随删除而变化。',
    'x 若为区间端点就无解。若 x 在中间，保留离 x 较近的端点 l，让剩余连续区间先得到 2x−l，最后合并；x 正好居中时先合并两端得到 x，再把内部也化成 x。用待合并栈实现这个递归。',
    r'''任何一次平均都在所选两数之间。要最终变成原始最小值 a，所有较大数都不可能通过平均精确降到 a；最大值 b 同理。因此 x=a 或 x=b 时无解。下面构造说明所有严格内部整数都可达到。

假设当前待处理的、仍保持原样的连续区间是 [l,r]，目标为 x。若 2x<l+r，先不动左端点 l，要求其它数 [l+1,r] 最终得到 y=2x−l。因为 x>l 且 2x<l+r，有 l+1<y<r，所以这是一个更小的同类问题；最后把 l 与 y 合并，它们和为 2x，必定同奇偶，平均正好为 x。若 2x>l+r，则对称地保留右端点 r，内部目标改为 2x−r。

若 2x=l+r，两端同奇偶，可以先把它们合成一个 x，放在原左端位置，再让内部 [l+1,r−1] 也化成 x，最后合并两个 x。内部只剩一个数时它本来就是 x，是终点。以上每次都严格缩短区间，操作数恰好为初始数量减一。

还要正确输出变化中的位置。当前连续区间前面有 left 个已经保留、尚待最终合并的数，所以区间两端的位置为 left 与 left+r−l。居中时立刻输出这两个位置，合成的 x 留在前面，left 加一；保留左端也令 left 加一。把每层保留左端还是右端存到 pending，然后缩小区间继续，避免十万层函数递归。

缩成单点后逆序处理 pending。若本层保留左端，它和内部唯一结果的当前下标为 left−1、left，合并后 left 减一；若保留右端，则两者为 left、left+1。其余尚未合并的外层端点都在这两者外侧，不会夹入中间。这样无需频繁删除大数组，也能在线确定每条操作的真实下标。''',
    r'''int a,b,x;cin>>a>>b>>x;if(x==a||x==b){cout<<"-1\n";return 0;}
int l=a,r=b,left=0;vector<bool>pending;vector<pair<int,int>>operations;
while(l<r){
    if(2*x==l+r){operations.push_back({left,left+r-l});pending.push_back(true);++left;++l;--r;}
    else if(2*x<l+r){pending.push_back(true);++left;x=2*x-l;++l;}
    else{pending.push_back(false);x=2*x-r;--r;}
}
for(int i=(int)pending.size()-1;i>=0;--i){if(pending[i]){operations.push_back({left-1,left});--left;}else operations.push_back({left,left+1});}
for(auto op:operations)cout<<op.first<<' '<<op.second<<'\n';''',
    '位置从零开始，删除后重新编号；必须先输出较小位置，不能输出数值本身。',
    '令 N=b−a+1，时间与额外空间均为 $O(N)$，含输出。',tags=['构造','栈'],lessons=A+['queue-stack','construction'],checker='blackboard')

add('P1650','优先拿下可赢的两端对局','两方各有 n 匹马，胜负收益分别为正负二百、平局零，求田忌能够取得的最大净收益。',
    '两方速度升序排好。自己的最快若能赢对方最快就配这对；否则自己的最慢若能赢对方最慢就配这对；两端都不能这样赢时，用自己最慢消耗对方最快，按实际胜负计分。',
    r'''不能只比较同名次的马，也不能把“牺牲最慢马”无条件记成一负，可能两匹速度相等，应算平局。维护两方尚未使用的最慢、最快四个端点，每次确定一对并移走。

若我方最快 A 能赢对方最快 B，可将 A 配 B。任意方案若 A 配较慢的 b、B 配另一匹 a，交换为 A 对 B、a 对 b 不会降低总分：原先 A 对 b 已是一胜，交换后这一胜仍在；而 b≤B，让 a 的对手变弱，其结果只会改善。

否则最快不能赢对方最快。若我方最慢 a 能赢对方最慢 b，也可以先配这一对：若原方案 a 对其它 B、b 对其它 A，交换后 A 对 B 的结果不比 a 对 B 更差，而 a 对 b 仍保留原先 A 对 b 的胜利。两种情况都能安全拿下一胜。

最后两端都不能直接拿胜时，a≤b 且 A≤B，用 a 对 B。若最优方案已经这样配对就无需改动；否则看其中 a 原来的对手 u、B 原来的对手 v：因为 u≥b≥a、v≤A≤B，这两局原本都不能赢。改为 a 对 B、v 对 u 后，如果原来两局都输，新的两局最差也只输两局；如果其中有平局，则 a=u 或 v=B，交换后 v 对 u 至少能保住相应的平局，若原来两局都平则交换后恰为一胜一负。因此总收益不会降低。若 a=B，则所有剩余马都同速，直接算平即可。每轮只去掉一匹双方马，再对剩余同类问题继续。''',
    r'''int n;cin>>n;vector<int>a(n),b(n);for(int &x:a)cin>>x;for(int &x:b)cin>>x;sort(a.begin(),a.end());sort(b.begin(),b.end());
int al=0,ar=n-1,bl=0,br=n-1,score=0;
while(al<=ar){
    if(a[ar]>b[br]){++score;--ar;--br;}
    else if(a[al]>b[bl]){++score;++al;++bl;}
    else{score+=(a[al]>b[br])-(a[al]<b[br]);++al;--br;}
}cout<<200*score<<'\n';''',
    '允许速度相同，牺牲局也可能是平局；答案是净收益而非赢局数。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序','双指针'],lessons=S+['two-pointers','greedy'])

add('P6155','后到者先放置并反向配对费用','每次只能把 a 中一项加一，单位费用 b 可在修改前任意重排，求所有最终值不同的最小费用，结果模二的六十四次方。',
    '把最终数值看作时间槽，按 a 升序加入已可放置的元素，每个槽优先放 a 最大的候选，记录增量。最后将增量降序、费用升序配对求和，使用精确 64 位无符号自然取模。',
    r'''a=[3,3,4]、b=[3,2,1] 时，普通升序逐项填成三、四、五，增量是 [0,1,1]，重排费用后也要三；若先让一个三占三，再让四占四，最后另一个三变五，增量 [0,0,2] 配最便宜费用一，只需二。费用可以重排，所以不能只追求每个增量看起来都较小。

把最终值 t 看作一个槽，原值 a 只能放入 t≥a 的槽，增量为 t−a。若当前槽有待放元素，故意留空再去更后面只会增大某个增量，不会帮助其它元素，所以最优方案不必空等；没有可放元素时则跳到下一个原值，不能按十的九次方逐个扫描。

固定这些从早到晚的可用槽，考虑两个原值 x≤y，都已能放入较早槽 s，之后另有槽 t>s。若把 x 放 s、y 放 t，增量为 s−x 与 t−y；交换成 y 放 s、x 放 t 后，小增量 s−y 不大于原来任何一个，大增量 t−x 不小于原来任何一个，且总和不变。费用可以交换：两种费用 p≤q 总可让 p 配大增量、q 配小增量。设总增量为 C、大增量为 D，费用就是 qC−(q−p)D，D 增大不会更贵。因此遇到可放的多个元素，优先放原值最大的 y 不劣，可以不断交换得到整个贪心顺序。

a 已升序，按时间加入的原值也升序，栈顶就是当前最大的候选，不必再用堆。每个时间槽弹出栈顶，记录 t−a，再把 t 加一；栈空时跳到下一个 a。所有增量出来后，用同样的两项交换公式可知，大增量必须匹配小费用，所以把两列反向排序配对。

答案要求模 2^64，代码使用 uint64_t（精确六十四位无符号整数）；无符号加法按二的位数次方回绕，正好对应要求。不得用有符号 long long 溢出来模拟取模，因为有符号溢出不是这条规则。''',
    r'''int n;cin>>n;vector<int>a(n);vector<uint64_t>b(n),delta;for(int &x:a)cin>>x;for(auto &x:b)cin>>x;sort(a.begin(),a.end());sort(b.begin(),b.end());
vector<int>waiting;int index=0;long long time=a[0];
while((int)delta.size()<n){
    if(waiting.empty()&&index<n)time=max(time,(long long)a[index]);
    while(index<n&&a[index]<=time)waiting.push_back(a[index++]);
    delta.push_back(time-waiting.back());waiting.pop_back();++time;
}
sort(delta.begin(),delta.end());uint64_t answer=0;
for(int i=0;i<n;++i)answer+=delta[n-1-i]*b[i];cout<<answer<<'\n';''',
    '先生成增量，再重排费用；普通升序逐项加到不重复并非最优；模二的六十四次方需无符号运算。',
    r'时间 $O(n\log n)$、空间 $O(n)$；扫描最多放置 n 次，不按 a 的值域循环。',tags=['贪心','排序','栈'],lessons=S+['queue-stack','greedy','integer','unsigned64'])

add('P11036','用最低一位因子构造公倍数','给定 a，构造受上界限制的正整数 b,c,d，使 a+b+c+d 等于 gcd(a,b) 加 lcm(c,d)。',
    '令 p 为 a 的最大二次幂因子，取 b=a、c=2p、d=a+2p。此时 gcd(c,d)=p，所以 lcm(c,d)=2d，直接代入即可验证等式。',
    r'''设 a=pq，其中 p 是二的幂、q 为奇数。取 c=2p、d=p(q+2)，因为 q+2 仍为奇数，c、d 的最大公约数正好是 p，最小公倍数为 2p(q+2)=2a+4p。

又令 b=a，则 gcd(a,b)=a。等式左边为 a+a+2p+(a+2p)=3a+4p，右边为 a+(2a+4p)，两边相同，且 b、c、d 全为正。p 可以反复除二求，也可用 a&−a 提取最低一位的一；这里使用正整数 long long，负 a 仍在可表示范围内，按常用补码实现提取。

还必须核对题目给的特殊上界，不能只验证等式。a≤十的九次方，所以 p≤2^29。若 p≤2^28，则 d≤十的九次方+2^29=1536870912；若 p=2^29，范围内的奇数倍只能是 a=p，d=3×2^29=1610612736。二者均不超过 1634826193，c≤2^30 也满足。代码用 long long 输出，防止中间相加越过有符号 int。''',
    r'''int t;cin>>t;while(t--){long long a;cin>>a;long long p=a&(-a);cout<<a<<' '<<2*p<<' '<<a+2*p<<'\n';}''',
    '最低二次幂因子不是最大二次幂上界；构造必须同时核对等式和每项上界。',
    '每组时间与额外空间均为 $O(1)$，总时间 $O(t)$。',tags=['构造','最大公约数','位运算'],lessons=['io-basics','basic-arithmetic','number-theory','bitwise','integer','construction'],checker='gcd_lcm')

add('P12676','成对互补与三行奇数底座','构造 n 个一到 m 的排列，使每个数在各行的位置之和都相同；输出排列内容而不是位置数组。',
    '偶数行用升序、降序成对互补。奇数行若 m 偶数无解；m 奇数且至少三行时先构造三行位置和恒定的底座，余下继续成对添加。m=1 单独输出，n=1 且 m>1 无解。',
    r'''先看必要条件。每行位置总和为 m(m+1)/2，n 行合计后平均到 m 个数字，每个数字的位置和必须是 n(m+1)/2。因此 n 奇、m 偶时它不是整数，必定无解。n=1、m>1 时，各数字的唯一位置互不相同，也不可能相等；m=1 时只有数字一，任意行数都可行。

若 n 为偶数，让每两行分别为一到 m 升序和降序。数字 v 在两行的位置是 v 与 m+1−v，合计恒为 m+1，所以所有行按对添加即可。

剩下 n≥3 为奇数、m=2k+1 为奇数。只需设计三行，零基位置和恒为 3k，再附上若干互补对。对数字 v+1（v 从零到 2k），指定第一行位置 p=v，第二行位置 q=(v+k)%m，第三行位置 r=3k−p−q。第一、第二行的位置都是各位置恰好一次。第三行也如此：v≤k 时 r=2k−2v，覆盖全部偶位置；v>k 时 r=4k+1−2v，覆盖全部奇位置。它们不重不漏，范围都在零到 2k，确实能成为排列。

注意 p、q、r 是“某个数字放在哪里”，不能直接把这些位置当作一行答案输出。应把数字 v+1 分别写入 row1[p]、row2[q]、row3[r]。例如 m=5 时三行可为 [1,2,3,4,5]、[4,5,1,2,3]、[3,5,2,4,1]。数字一的位置为一、三、五，合计九；数字二为二、四、三，也合计九；所有数字都满足同样的和。''',
    r'''int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;
    if(m==1){for(int i=0;i<n;++i)cout<<"1\n";continue;}
    if(n==1||(n%2==1&&m%2==0)){cout<<"-1\n";continue;}
    int start=0;
    if(n%2){int k=m/2;vector<int>p(m),q(m),r(m);
        for(int v=0;v<m;++v){int x=v,y=(v+k)%m,z=3*k-x-y;p[x]=q[y]=r[z]=v+1;}
        print_row(p);print_row(q);print_row(r);start=3;
    }
    for(int row=start;row<n;++row){for(int i=1;i<=m;++i)cout<<((row-start)%2==0?i:m+1-i)<<(i==m?'\n':' ');}
}''',
    '指定的是每个数字的位置，输出前要倒填成排列；n=1 与 m=1 分别处理。',
    '有解时含输出时间 $O(nm)$、额外空间 $O(m)$；无解判定为 $O(1)$。',tags=['构造','组合计数'],lessons=A+['functions','counting','construction'],checker='equal_permutations',
    declarations=r'''void print_row(const vector<int>&a){for(int i=0;i<(int)a.size();++i)cout<<a[i]<<(i+1==(int)a.size()?'\n':' ');}''')

add('P2949','从最晚时隙选择最高收益','所有任务耗时一、可从零时刻开工，必须在各自截止时间前完成，求最大总收益。',
    '最多执行 n 项，所以把大于 n 的截止时间压成 n。由最后一个时隙向前扫描，加入所有此时已允许完成的任务，从大根堆取收益最高者放入当前时隙。',
    r'''时隙 t 表示从 t−1 到 t 做一项任务，完成时刻为 t。任务截止时间至少为 t，才有资格放在这里。我们从最晚时隙往前定，后面遇到的新任务截止时间更早，不能占用已经越过的较晚时隙。

为什么当前挑收益最高者安全？考虑任一最优方案在当前最晚尚未确定的时隙做了任务 j，而最高收益的可选任务是 i。如果 i 没被安排，直接用 i 替换 j，收益不减；如果 i 被排在更早的时隙 s，就交换 i、j。i 可以在当前 t 完成，而 j 从 t 提前到 s 不会超出它的截止时间，因此交换合法，收益相同。当前时隙原本空闲时，加入 i 也不坏；所有收益为正，空着没有额外好处。逐个固定时隙，便能保留一个全局最优方案。

截止时间可到十的九次方，但总共只有 n 个任务，任何可行方案都能去掉空闲，把所选任务整体尽量提前，至迟在 n 完成。因此把每个截止时间截成 min(d,n) 不改变最优值。用 n+1 个桶保存同截止时间的收益：从 t=n 降到一，先把桶 t 全加入大根堆，未选任务留在堆中继续竞争更早位置。堆非空时取最大收益，空时跳过。这一做法不必对任务比较排序。''',
    r'''int n;cin>>n;vector<vector<long long>>bucket(n+1);
for(int i=0;i<n;++i){int deadline;long long profit;cin>>deadline>>profit;bucket[min(deadline,n)].push_back(profit);}
priority_queue<long long>available;long long answer=0;
for(int t=n;t>=1;--t){for(long long profit:bucket[t])available.push(profit);if(!available.empty()){answer+=available.top();available.pop();}}
cout<<answer<<'\n';''',
    '倒序扫描完成时刻；先加入本时隙新允许的任务，再取大根堆最高收益；截止时间可压到 n。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','堆'],lessons=A+['heap','greedy','integer'],key='latest-slot')
