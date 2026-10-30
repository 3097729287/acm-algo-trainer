"""Reviewed algorithms for the binary-search unit; do not force binary search."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer']
S=A+['sort','iterators']
B=S+['bounds']

add('B3691','有序切割值查找，统计保留段的起点',
    '删除数组中所有值属于给定切割集合的位置，求剩余的非空连续片段数量。',
    r'''将切割值排序，每个原元素用 lower_bound 判断是否需要删除。维护上一位置是否仍在保留段中：当前不删除且前一位置不在段内时，开始一个新片段，答案加一；删除则结束当前段。''',
    r'''样例 [3,4,3,5,2,6] 删除值四与五后，剩下 [3]、[3]、[2,6] 三段。相邻两个删除位置之间没有元素，不应额外算一个空片段，删除首尾也不会制造片段。

先排序切割集合。`lower_bound` 找到第一个不小于 x 的位置；只有它没有越过 end 且所指值恰好等于 x，才说明 x 属于集合。二分前提是切割值已排序，与原数组是否有序无关，不能为了查找把原数组也排序，原位置决定了连续关系。

扫描原数组时，inside 表示上一位置是否处于尚未结束的保留段。当前保留而 inside 为假，恰好是一个非空段的第一个元素，计数一次。当前被删就把 inside 设假；连续删除只会重复设假，不会增加答案。每个保留段有唯一开头，因此不漏不重。''',
    r'''int n,m;cin>>n>>m;vector<int>a(n),cuts(m);for(int &x:a)cin>>x;for(int &x:cuts)cin>>x;sort(cuts.begin(),cuts.end());
// 只在一个非空保留段的开头计数。
int answer=0;bool inside=false;
for(int x:a){auto found=lower_bound(cuts.begin(),cuts.end(),x);bool removed=found!=cuts.end()&&*found==x;
    if(!removed&&!inside)++answer;inside=!removed;
}
cout<<answer<<'\n';''',
    '不排序原序列；查找结果需检查 end；空段不计数。',
    r'时间 $O(m\log m+n\log(m+1))$、空间 $O(n+m)$。',tags=['二分查找','连续段'],lessons=B)

add('P1678','二分学校分数，只比较分界两侧',
    '每位学生独立选择与估分最接近的学校分数线，求全部最小绝对分差之和。',
    r'''学校分数排序。对学生分数 x，lower_bound 找第一个≥x 的学校，只需比较该校与其前一个学校；更远两侧的差都不会更小。没有某侧候选时只检查存在的一侧。''',
    r'''学校分数 [513,567,598,689]，学生估分六百。第一个不小于六百的是六百八十九，左邻五百九十八离他更近，差二；再向左只会更远，再向右也不会更近。

对任意 x，有序数组在二分位置分为两侧：左侧都小于 x，越靠右差 x−a 越小，因此只需最后一个；右侧都不小于 x，越靠左差 a−x 越小，因此只需第一个。两侧取较小者就是全体最优。

若 x 比全部学校低，二分下标为零，没有前驱；若比全部学校高，下标为 m，没有右侧元素，不能解引用尾后位置。学生间没有录取容量竞争，同一学校可被多人选择，因此每人单独查找后累加，不需要给学校做匹配或删除。

单个分差虽不超过一百万，十万名学生的总和可达十的十一次方，答案使用 long long。''',
    r'''int m,n;cin>>m>>n;vector<long long>schools(m);for(auto &x:schools)cin>>x;sort(schools.begin(),schools.end());long long answer=0;
// 二分位置及前驱是两侧各自最近的学校。
while(n--){long long x;cin>>x;int p=(int)(lower_bound(schools.begin(),schools.end(),x)-schools.begin());long long best=LLONG_MAX;
    if(p<m)best=min(best,schools[p]-x);if(p>0)best=min(best,x-schools[p-1]);answer+=best;
}
cout<<answer<<'\n';''',
    '学生可共同选择一校；二分结果为 m 时没有右候选，为零时没有左候选。',
    r'时间 $O(m\log m+n\log(m+1))$、空间 $O(m)$。',tags=['排序','二分查找'],lessons=B)

add('P7713','固定被删最小值，均衡其余分数的最大值',
    '最多给评分增加 m 个单位，删掉一个最高分和一个最低分，求剩下 n−2 个分数的最大总和。',
    r'''可以保持原最小分不动。设 S=原总和−原最小+m，其余 n−1 项的最终总和就是 S；它们的最高分至少为原最高，也至少为 ceil(S/(n−1))，两者最大值 H 可以达到。答案 S−H。''',
    r'''样例 [1,2,2,3] 有三次增加。保留最低的一不动，其余三项原和七，增加后总和十；它们的最高值至少为上取整的 10/3，即四，可分配成 [3,3,4]，删四后得到六。目标是剩余总和，不用再除以 n−2。

为什么能固定原最小者？先看任意最终合法评分方案。若原最小者没拿到最终最低分，可以把它与最终最低者的终值交换：原最小者接收较小值仍不低于原分；另一人的原分不超过它原来的最低终值，接收更大值也合法。总增量与最终分数多重集合不变。

现在原最小者已经是最终最低者，把加在它身上的增量全部转给一名最高者。最低值下降多少，最高值最多上升多少，删去这两项后的和不会降低。因此总存在最优解，完全不增加原最小分。其余位置均可继续加分，所以最多 m 次可以全部使用。

其余 n−1 项总和为 S。它们不能低于各自原分，最高者至少为原最高；平均值又给出下界 ceil(S/(n−1))。取 H 为二者最大值后，所有原分≤H，而且总可填容量 (n−1)H−原其余总和至少 m，故可把 m 次增加分配到这些上限中，使最高值不超过 H。于是下界可达到，剩余和就是 S−H，无需逐次加分或二分。''',
    r'''int n;long long m;cin>>n>>m;long long sum=0,minimum=LLONG_MAX,maximum=LLONG_MIN;
for(int i=0;i<n;++i){long long x;cin>>x;sum+=x;minimum=min(minimum,x);maximum=max(maximum,x);}
// 最小值保持不变，其余项的最高值受原最大值与平均值共同限制。
long long retained_total=sum-minimum+m,highest=max(maximum,(retained_total+n-2)/(n-1));
cout<<retained_total-highest<<'\n';''',
    '输出剩余总和，不输出平均值；上取整的分母为 n−1；总和使用 long long。',
    '时间 $O(n)$、额外空间 $O(1)$。',tags=['贪心'],lessons=A+['greedy','basic-arithmetic'])

add('P11962','按树的二分颜色统计偶数步终点',
    '对树上每个起点，求经过任意偶数步、允许重复节点后能停下的不同节点数量，零步也合法。',
    r'''给树相邻点染不同颜色。每走一步颜色翻转，偶数步只能到同色点；任意同色两点的唯一简单路径长度也为偶数，所以全部同色点都能到。统计两种颜色总数，每点输出自己颜色的数量。''',
    r'''样例三点的边为一到三、二到三。一、二同色，三为另一色，因此从一或二出发的偶数步终点有两个，从三出发只有自己。

树没有环，指定根后，按深度奇偶即可给相邻点不同颜色。任意一条边都翻转颜色，即使来回走同一条边，仍是每步翻转一次，所以偶数步不可能到异色点。反过来，同色两点在树中的简单路径必有偶数条边，直接沿它走就能结束，不需要额外绕路。

题目不要求恰好走某个固定偶数步数，只要存在一种偶数长度走法即可。零步使起点自己也计入答案，不能把同色总数减一。n 可达二十万，链状树递归深度太大，代码使用父先子后的显式队列顺序染色，避免深递归。''',
    r'''int n;cin>>n;vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>color(n+1,-1),order={1};color[1]=0;int count[2]={1,0};
// 显式遍历染色，不使用可能在深链上溢栈的递归。
for(size_t at=0;at<order.size();++at){int u=order[at];for(int v:graph[u])if(color[v]==-1){color[v]=color[u]^1;++count[color[v]];order.push_back(v);}}
for(int i=1;i<=n;++i)cout<<count[color[i]]<<(i==n?'\n':' ');''',
    '零步包含自己；求可到的不同节点数，不是走法数量；避免在深链上递归。',
    '时间、空间均为 $O(n)$。',tags=['BFS','图论'],lessons=A+['graphs','trees'])

add('CF1967A','先抬高最低频数，再增加不同的额外类型',
    '可购买 k 张任意类型卡片，重新排列全部卡片，最大化长度为 n 且恰含每种类型一次的连续窗口数量。',
    r'''二分最大 h，使补齐所有类型到至少 h 张的代价不超过 k。设补齐后剩余 r 枚钱、原本多于 h 张的类型有 z 种，则最优分数为 (h−1)n+1+z+r。先放 h 份相同排列，再接有额外卡的 z+r 种类型即可达到。''',
    r'''若每种类型各有 h 张，把同一个排列连续重复 h 遍，就有 hn−n+1 个合法窗口：相邻窗口移出与移入的类型相同。若另有 z 种类型各多一张，把这 z 种排在周期排列的开头，再在末尾接它们的一份前缀，还能增加 z 个合法窗口。

这个构造已经最优。固定各类型数量，设最低频数为 h，有 r0 种类型恰好 h 张。选这些最低频类型中“第一张出现得最早”的类型 X。含 X 第一张的合法窗口还必须覆盖其它 r0−1 种最低频类型的第一张，它们都在 X 第一张右边，至少跨 r0−1 个位置，所以这样的窗口至多 n−r0+1 个。X 其余 h−1 张每张至多属于 n 个窗口，而每个合法窗口恰有一张 X，因此总数至多 hn−r0+1=(h−1)n+1+z，其中 z=n−r0。

因此优先让最低频数尽量大：最低频数为 h−1 的任何方案分数至多 (h−1)n，而最低频数 h 即使没有额外卡也能得 (h−1)n+1，严格更好。补齐到 h 的代价是 Σmax(0,h−a[i])，随 h 单调增加，可二分最大可行 h，范围从原最小频数到原最小频数加 k。

补齐后，原本 a[i]>h 的类型已经有额外卡；剩余每枚钱应让一个恰好 h 张的类型再多一张。因为 h 已最大，剩钱必不足以把全部最低频类型都提升，否则还能补到 h+1，所以新增类型数正好是剩钱 r。代入构造与上界即得公式。多余卡可以放在构造块之外，不会减少块内已有窗口。计数、代价和乘积全部用 long long。''',
    r'''int tests;cin>>tests;while(tests--){int n;long long k;cin>>n>>k;vector<long long>a(n);long long minimum=LLONG_MAX;
    for(auto &x:a){cin>>x;minimum=min(minimum,x);}long long lo=minimum,hi=minimum+k;
    while(lo<hi){long long mid=lo+(hi-lo+1)/2,cost=0;for(long long x:a){if(x<mid)cost+=mid-x;if(cost>k)break;}
        if(cost<=k)lo=mid;else hi=mid-1;
    }
    // 先抬满最低频数，余钱再给不同的最低频类型。
    long long used=0,extra=0;for(long long x:a){if(x<lo)used+=lo-x;else if(x>lo)++extra;}
    cout<<(lo-1)*n+1+extra+(k-used)<<'\n';
}''',
    '最大化的是滑动窗口数；先最大化最低频数，再把余钱分给不同的最低频类型。',
    r'时间 $O(n\log(k+2))$、空间 $O(n)$。',tags=['二分答案','组合计数','贪心'],lessons=A+['binary-answer','counting','greedy','permutations'])

add('P1570','整数比较比率阈值，精确舍入到三位小数',
    '必须恰选 m 种调料，最大化总美味度除以总耗时，输出三位小数。所有耗时为正，答案不超过一千。',
    r'''判断最优比率是否≥p/q，把每项变为 q*v−p*c，取最大的 m 项，其和≥0 就可行。先二分最大整数 t，使最优值≥t/1000，再用阈值 (2t+1)/2000 判断是否需要四舍五入进一。全程整数，不受浮点半点误差影响。''',
    r'''样例恰选两项，选美味度二、三，耗时二、一，总比率五除三。不能逐项按 v/c 排序选最大的 m 个，因为组合目标是总和的比率，耗时会给每项不同的权重。

要判断能否达到目标 p/q，由于总耗时为正、q 为正，

$$\frac{\sum v}{\sum c}\ge\frac pq\iff\sum(qv-pc)\ge0.$$

固定 p、q 后，每项有一个独立整数得分，必须恰选 m 项，最大的 m 项之和就是所有合法选择中最大者。不能只选正项或不足 m 项。阈值增大，每项得分不增，故判定单调，可以二分。

输出只需三位小数，无需先求一个不确定误差的实数。令 t=⌊1000×最优比率⌋，在零到一百万中二分可行阈值 t/1000。确定整数部分后，再判断最优值是否至少 (t+1/2)/1000，也就是 (2t+1)/2000。达到半点就把 t 加一，再按 t/1000 与三位补零的 t%1000 输出。

最大比较项约二乘十的十次方，二百项相加仍在 long long 范围内。排序只针对当前阈值的得分，不会修改调料原本配对的美味度与时间。''',
    r'''int n,m;cin>>n>>m;vector<long long>value(n),cost(n);for(auto &x:value)cin>>x;for(auto &x:cost)cin>>x;
long long lo=0,hi=1000000;
while(lo<hi){long long mid=(lo+hi+1)/2;if(possible(value,cost,m,mid,1000))lo=mid;else hi=mid-1;}
// 精确比较半个千分位，达到半点时进一。
if(possible(value,cost,m,2*lo+1,2000))++lo;
cout<<lo/1000<<'.'<<setw(3)<<setfill('0')<<lo%1000<<'\n';''',
    '必须恰选 m 项；比的是总和比率；四舍五入使用半个千分位的精确阈值。',
    r'设千分位上界 U=10⁶，时间 $O(n\log n\log(U+1))$、空间 $O(n)$。',
    tags=['二分答案','贪心','排序'],lessons=S+['functions','binary-answer','greedy'],exact=True,
    declarations=r'''bool possible(const vector<long long>&value,const vector<long long>&cost,int chosen,long long p,long long q){
    // 固定阈值后，选转换得分最高的恰好 m 项。
    vector<long long>score(value.size());for(size_t i=0;i<value.size();++i)score[i]=q*value[i]-p*cost[i];
    sort(score.rbegin(),score.rend());long long sum=0;for(int i=0;i<chosen;++i)sum+=score[i];return sum>=0;
}''')

add('P2005','十进制乘候选小整数，二分有界商',
    '两个正整数可大到 6250 的阶乘，求向下整除的商；题目保证商不超过 13 的阶乘。',
    r'''N、M 用十进制字符串保存，商的上限 13!=6227020800 仍可用 long long。对候选商 q，逐位计算 M*q，与 N 比较，判断是否不超过 N；按这个单调条件二分最大 q。''',
    r'''被除数与除数可能有两万多位，不能读入 long long，也不能用浮点近似再相除；但商至多 13!=6227020800，可以作为普通 64 位整数枚举。问题从大整数除法变成了大整数乘一个不太大的候选数。

对正 M，M*q≤N 当且仅当 q 不超过真实向下整除的商，条件随 q 单调。二分范围零到 13!，每次只做一次十进制逐位乘法与比较，总共约三十三轮。

乘法从 M 的个位向高位走，当前数字 digit 乘 q 再加 carry，个位写入结果，除十得到下一位进位。q 可大于 int，digit*q 和 carry 都用 long long：进位始终小于 q，单轮和小于 10q，约六百多亿，仍安全。结果先按低位到高位追加，最后反转；q=0 单独返回字符串零。

规范化前导零后，非负十进制整数先按长度比较，长度相同才按字符字典序比较。不能直接对不同位数的字符串用字典序，例如九在字典序上反而大于一百。若 N<M，二分自然返回零。''',
    r'''string n,m;cin>>n>>m;n=normalize(n);m=normalize(m);long long lo=0,hi=1;
// 被除数很长，但商有 13! 这个可用 64 位整数保存的上限。
for(int i=2;i<=13;++i)hi*=i;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;string product=multiply(m,mid);
    bool fits=product.size()<n.size()||(product.size()==n.size()&&product<=n);
    if(fits)lo=mid;else hi=mid-1;
}
cout<<lo<<'\n';''',
    '输入用字符串，商用 long long；不同位数先比较长度；乘法的进位不能用 int。',
    r'位数上界 L、商上界 Q=13! 时，时间 $O(L\log(Q+1))$、额外空间 $O(L)$。',
    tags=['高精度','二分答案'],lessons=A+['strings','string-tools','functions','big-integers','binary-answer'],
    declarations=r'''string normalize(const string&s){size_t i=0;while(i+1<s.size()&&s[i]=='0')++i;return s.substr(i);}
string multiply(const string&a,long long factor){
    if(factor==0)return "0";string result;long long carry=0;
    for(int i=(int)a.size()-1;i>=0;--i){long long value=(a[i]-'0')*factor+carry;result.push_back(char('0'+value%10));carry=value/10;}
    while(carry){result.push_back(char('0'+carry%10));carry/=10;}
    reverse(result.begin(),result.end());return result;
}''')

add('P2920','截止时间升序，取所有前缀的最小余量',
    '所有任务都必须完成且不能中断，每个有耗时与截止时间，求非负的最晚开工时刻，不可行则输出负一。',
    r'''任务按截止时间升序做。累计处理时间 prefix，开工时间 start 必须满足 start+prefix≤当前截止，所以 start≤deadline−prefix。取全部前缀余量的最小值；若它小于零，则从零开始也来不及。''',
    r'''样例按截止时间排序后，耗时是三、八、一、五，截止是五、十四、十六、二十。累计耗时为三、十一、十二、十七，对开工时间的限制分别是不晚于二、三、四、三，所以最迟为二。

先证明按截止时间做不会更差。若相邻两任务先做晚截止的 A、后做早截止的 B，在一个可行安排中将两者交换：B 提前完成，不会错过它的截止；A 的新完成时刻等于交换前 B 的完成时刻，而它的截止更晚，也仍来得及。不断交换逆序，就得到截止时间升序的可行安排。相同截止次序任意。

固定这个顺序后，不安排中间空闲只会更早完成，不会损害可行性。第 i 个任务在 start+prefix[i] 完成，每个截止分别给出一个 start 的上界，全部满足等价于取最小上界。该最小值可以达到，因为按它开工后所有完成时刻都不超过对应截止。

负结果不是要求在过去开工：现在为零，负数表示已经无解，应统一输出 −1。开始时间零恰好可行时必须输出零。''',
    r'''int n;cin>>n;vector<pair<long long,long long>>jobs(n);for(auto &job:jobs){cin>>job.second>>job.first;}sort(jobs.begin(),jobs.end());
// 每个截止前缀都对开工时间提出一个上限。
long long elapsed=0,latest=LLONG_MAX;
for(auto job:jobs){elapsed+=job.second;latest=min(latest,job.first-elapsed);}
cout<<(latest<0?-1:latest)<<'\n';''',
    '按截止而非耗时排序；全部任务必须做；余量为零是合法结果。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序','前缀和'],lessons=S+['greedy','prefix'])

add('P8873','二分所在波段，再按段内折线求值',
    '序列从 [0] 开始，第 i 段依次从零升到 i、降到负 i、再升回零，i 从零计，回答给定位置的值。',
    r'''第 i 段长度 4i+1，前零到 i 段总长度 F(i)=(i+1)(2i+1)。二分最小 i 使 F(i)≥k，再求零起始段内偏移 t。t≤i 时值为 t，i<t≤3i 时值为 2i−t，其余为 t−4i。''',
    r'''最前面的独立零是第零段，长度一；下一段 i=1 为 [0,1,0,−1,0]，长度五，两段累计六项。因此段号不能从一开始套长度公式，否则所有位置都会错开。

第 i 段走过从零到正峰、到负峰、再回零的四倍 i 个步长，加上起点零，共 4i+1 项。累加得到

$$F(i)=\sum_{j=0}^{i}(4j+1)=(i+1)(2i+1).$$

F 严格递增，可二分包含第 k 项的第一段。取上界二十亿足以覆盖 k≤4×10¹⁸，且整个 F 上界约八乘十的十八次方，仍在有符号 long long 范围内。计算中段号也须先是 long long，不能让 2i 在 int 中溢出。

第 i 段之前共有 F(i−1)=i(2i−1) 项，于是段内零起始偏移 t=k−i(2i−1)−1。在偏移零到 i 的上坡，每次加一，值等于 t；从 i 到 3i 以斜率负一下降，值为 2i−t；最后从 −i 回零，值为 t−4i。两个峰的端点归入相邻哪段都可，只需公式一致。i=0、k=1 自动得到零。''',
    r'''int queries;cin>>queries;while(queries--){long long k;cin>>k;long long lo=0,hi=2000000000LL;
    while(lo<hi){long long mid=(lo+hi)/2;if((mid+1)*(2*mid+1)>=k)hi=mid;else lo=mid+1;}
    // 找到波段后，转换为从零开始的段内偏移。
    long long i=lo,t=k-i*(2*i-1)-1;
    if(t<=i)cout<<t<<'\n';else if(t<=3*i)cout<<2*i-t<<'\n';else cout<<t-4*i<<'\n';
}''',
    '第零段只有一个零；段内偏移要减一；平方级乘积先用 long long。',
    r'每次查询时间 $O(\log k)$、额外空间 $O(1)$。',tags=['二分查找','递推'],lessons=A+['bounds','prefix','basic-arithmetic'])

add('P14115','二分最低高度，优先使用不浪费的长木板',
    '每块原木板可加装若干高一或高 h 的木板，两类数量有限，求最终最低高度的最大值。',
    r'''二分目标高度 T。每处缺口 d=max(0,T−a) 可先用 floor(d/h) 块长板，每块完整节省 h 块短板。若长板不够这些整份缺口，短板需求为总缺口−k*h；否则先填整份，再把剩余长板分给最大的正余数，每处最多再节省该余数的短板。检查剩余短板需求是否≤m。''',
    r'''一块高度三的长板填缺口八，前两块各实实在在补足三，第三块只能替代剩余两块短板，超出的一点无法挪给其它位置。因此应先使用所有“不浪费”的完整三，再考虑用长板覆盖各处余数。

固定 T，每处缺口 d 分成 q=floor(d/h) 个完整 h 和余数 r=d%h。前 q 块长板每块节省 h，额外再加一块至多节省 r，再多就不再减少短板需求。所有完整 h 的收益都大于任何正余数，故有限长板优先填完整份额；完整份额相互等价，可任意分配。

若全体完整份额至少 k，使用 k 块长板正好节省 k*h，最少短板为 Σd−k*h。否则填完所有完整份额，余下长板应选最大的若干正余数，因为每处独立且只需一块就覆盖该余数。`nth_element` 将最大的 take 个放到数组前部，不要求它们内部有序；只加总这些值即可。若长板已足够覆盖全部正余数，短板需求为零。

目标越高，能达到它的方案越少，因此可二分最大可行高度。上界使用总高度守恒：最终所有木板至少为 T，则 n*T≤原总高度+m+k*h。以右侧总量除 n 为上界，不但更紧，也保证检查中总缺口≤n*T，所有累计量都不超过约 1.001×10¹⁸，可安全用 long long。无需给答案取任何额外模数。

长板或短板可以不用完，覆盖余数时允许高出 T；目标只要求最低高度达到 T，不要求每块最后都恰好相等。''',
    r'''int n;long long m,k,h;cin>>n>>m>>k>>h;vector<long long>a(n);long long sum=0,lo=LLONG_MAX;
for(auto &x:a){cin>>x;sum+=x;lo=min(lo,x);}long long hi=(sum+m+k*h)/n;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;if(enough(a,m,k,h,mid))lo=mid;else hi=mid-1;}
cout<<lo<<'\n';''',
    '先完整份额再余数；长板盖住一个余数后的浪费不能转移；上界与累计量用 long long。',
    r'nth_element 平均线性，设二分高度上界 U，总平均时间 $O(n\log(U+1))$、空间 $O(n)$。',
    tags=['二分答案','贪心'],lessons=A+['functions','binary-answer','greedy','order-selection'],
    declarations=r'''bool enough(const vector<long long>&a,long long small,long long large,long long height,long long target){
    long long total=0,full=0;vector<long long>remainders;
    for(long long x:a){long long need=max(0LL,target-x);total+=need;full+=need/height;if(need%height)remainders.push_back(need%height);}
    // 不浪费的整份收益最大；只有它们填完后才覆盖余数。
    if(full>=large)return total-large*height<=small;
    long long take=large-full;if(take>=(long long)remainders.size())return true;
    long long remaining=total-full*height;
    nth_element(remainders.begin(),remainders.begin()+take,remainders.end(),greater<long long>());
    for(long long i=0;i<take;++i)remaining-=remainders[i];return remaining<=small;
}''')

add('P14635','拆成最便宜的糖果对与不同种类的单颗',
    '每种糖果购买奇数颗时价格 x、偶数颗时价格 y，均可无限购买，给定预算，求最多糖果数。',
    r'''每种购买量可拆成若干对加至多一颗单糖，一对价格 x+y，单颗价格 x。所有对都选最便宜的对价 C，剩余单颗来自不同种类。将 x 排序，枚举选最便宜的 r 颗单糖，剩余钱尽量买对，候选为 r+2*floor((m−prefixX[r])/C)。''',
    r'''某种糖买 2p 颗，费用为 p(x+y)；买 2p+1 颗，费用为 p(x+y)+x。这个拆法只记录该种数量的奇偶，不要求真正购买时先拿“单糖”再拿“糖果对”，所以同一种可以既贡献一颗单糖，也承接许多对，仍按原交替价收费。

固定所有种类的奇偶后，单颗的每种最多一颗；所有配对部分都能转移到全市场最便宜的对价 C=min(x_i+y_i)，不会增加费用。单颗有 r 种时，选择最便宜的 r 个 x 也不会更贵。于是每个最优方案都可整理成“最便宜的 r 个单颗加任意多最便宜的对”，而 r 只需从零到 n 枚举。

排序后前缀和 prefixX[r] 是这 r 颗费用。若已经超预算，后续前缀只会更大，可停止。否则剩余预算能买 floor((m−prefixX[r])/C) 对，每对增加两颗。不同 r 的奇偶不同，不可只看纯买对，也不可因为某种第一颗便宜就假定以后每一颗都同价。

样例二单颗价一、二、三，最低对价四。取前两颗单糖花三，剩十二买三对，总数八。金额可达十的十八次方，预算、前缀和与答案均用 long long；每颗价格至少一，也保证答案不会超过预算。''',
    r'''int n;long long money;cin>>n>>money;vector<long long>single(n);long long pair_price=LLONG_MAX;
for(auto &x:single){long long y;cin>>x>>y;pair_price=min(pair_price,x+y);}sort(single.begin(),single.end());
long long prefix=0,answer=0;
// r 种各留一颗单糖，其余全部按最便宜的对价购买。
for(int r=0;r<=n;++r){if(r>0)prefix+=single[r-1];if(prefix>money)break;answer=max(answer,(long long)r+2*((money-prefix)/pair_price));}
cout<<answer<<'\n';''',
    '单颗每种至多一份，对可以无限份；同一种同时含单颗与若干对完全合法。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序','前缀和'],lessons=S+['greedy','prefix'])

add('UVA10125','两数和排序，倒序枚举结果并排除重复下标',
    '从互不相同的整数集合中找四个不同元素 a、b、c、d，满足 a+b+c=d，使 d 最大；多组零结束。',
    r'''预存所有不同下标对的和，按和排序。d 从大到小、c 任取不同下标，二分寻找 a+b=d−c。检查匹配和值的至多前三对，找一对不含 c、d 的即可。固定和值时各下标对互不相交，两个禁用下标最多挡住两对，所以三对足够。''',
    r'''把四数式改成 a+b=d−c。先计算所有 i<j 的两数和并保留这两个下标，便能在枚举 d、c 后二分查找剩余两数。只比较和值不够：例如某对含 d 或 c，即使等式数值成立，也重复使用了同一个元素。

同和值可能有很多对，不能每次都把整组扫描完。输入所有值不同，对于固定和值 X，一个值 a 的搭档只能是 X−a，所以同和值的不同合法下标对之间不共享下标。禁用 c 至多挡住一对，禁用 d 也至多挡住一对。因此检查组内前三对，就一定能找到合法者，或者确认整个组不足三对且都非法；不存在前三对全被两个下标挡住、第四对才合法的情况。

d 按数值从大到小枚举，第一次找到合法组合即可输出该 d。不需要最大化 a、b、c，也不能把它们限制为正数。集合不足四个元素时，下标检查会自然得到无解。

原题完整约束与输入输出：[UVa 10125 官方 PDF](https://onlinejudge.org/external/101/10125.pdf)。零终止，不为零输出；无解文本为 `no solution`。''',
    r'''int n;while(cin>>n&&n){vector<long long>a(n);for(auto &x:a)cin>>x;sort(a.begin(),a.end());vector<PairSum>pairs;
    for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)pairs.push_back({a[i]+a[j],i,j});sort(pairs.begin(),pairs.end(),less_sum);
    bool found=false;long long answer=0;
    for(int d=n-1;d>=0&&!found;--d)for(int c=0;c<n&&!found;++c)if(c!=d){
        long long target=a[d]-a[c];auto at=lower_bound(pairs.begin(),pairs.end(),PairSum{target,-1,-1},less_sum);
        // 固定和值下每个下标只出现一次，两个禁用下标最多排除两对。
        for(int inspected=0;at!=pairs.end()&&at->value==target&&inspected<3;++at,++inspected)
            if(at->first!=c&&at->second!=c&&at->first!=d&&at->second!=d){found=true;answer=a[d];break;}
    }
    if(found)cout<<answer<<'\n';else cout<<"no solution\n";
}''',
    '四个下标必须不同；和值排序时保留端点；三对上界依赖输入值互不相同。',
    r'时间 $O(n^2\log(n+1))$、空间 $O(n^2)$。',tags=['折半枚举','二分查找','排序'],lessons=B+['structures','enumeration'],exact=True,
    declarations=r'''struct PairSum{long long value;int first,second;};
bool less_sum(const PairSum&a,const PairSum&b){return a.value<b.value;}''')

add('P3611','二分同时表演数，用小根堆模拟最早空位',
    '奶牛按固定顺序上台，空出位置就立即由下一头接上，求在时限内结束所需的最小舞台容量。',
    r'''判定容量 K 时，用小根堆保存 K 个位置当前任务的结束时刻。下一头在最早结束的位置开始，把堆顶加上它的时长后重新入堆。所有结束时刻最大值不超过时限则可行；容量越大不会延后任何奶牛，可二分最小可行 K。''',
    r'''奶牛不能按时长重新排序，也不能在每次上台时任意挑一头。前 K 头同时从零开始，之后每次取结束最早的位置，让输入中的下一头立即接上，这正是小根堆维护的过程。

堆里的数是结束时刻，而不是单头奶牛时长。若最早空位在时刻 t，下一头需要 d，那么新结束时刻是 t+d；其它位置不变。开始时放 K 个零时刻空位，可以让前 K 次弹出分别占用这些位置，统一整个模拟流程。

容量可行性单调。按输入编号归纳，容量增加后此前每头的开始与结束都不会更晚：第 i 头开始需等待的此前完成数量变少，且此前相同奶牛的完成时刻均不更晚，故它也不会更晚。于是全部结束的最大值不增，可以二分最小容量。

只要某个新完成时刻已经大于时限，最终表演一定超时，可以提前判不可行。题目保证 K=n 时可行，所以二分右端有现成的可行边界。完成时间可能累加很多时长，用 long long。''',
    r'''int n;long long limit;cin>>n>>limit;vector<long long>duration(n);for(auto &x:duration)cin>>x;int lo=1,hi=n;
while(lo<hi){int mid=(lo+hi)/2;if(finishes(duration,mid,limit))hi=mid;else lo=mid+1;}
cout<<lo<<'\n';''',
    '不改变上台顺序；堆保存完成时间；二分找最小可行容量。',
    r'一次判定 $O(n\log(K+1))$，总时间 $O(n\log^2(n+1))$、空间 $O(n)$。',
    tags=['二分答案','堆'],lessons=A+['functions','binary-answer','heap'],
    declarations=r'''bool finishes(const vector<long long>&duration,int capacity,long long limit){
    priority_queue<long long,vector<long long>,greater<long long>>ends;
    for(int i=0;i<capacity;++i)ends.push(0);
    // 堆顶是最早空位的完成时刻，而非单头表演时长。
    for(long long d:duration){long long finish=ends.top()+d;ends.pop();if(finish>limit)return false;ends.push(finish);}
    return true;
}''')

add('P10445','扫描两种时间预算，用最小对称差编号比较方案',
    '数轴上从原点出发签到后返回，访问礼物点可多用五个时间单位；先最多签到，再最小化所选编号集合的字典序，输出实际访问顺序。',
    r'''任何最优路线都可整理为访问一个包含原点的坐标区间 [L,R]，往返耗时为 2(R−L)，区间内站点都可顺路签到。分别按预算 m、预算 m+5 扫描最大窗口，后者必须包含礼物点。同数量方案比较最小的不同编号：含这个编号的集合字典序更小。用静态区间最小值结构查询两个坐标窗口差集的最小编号。''',
    r'''样例二按坐标排序后，编号依次是 [2,1,3,4,5]，坐标 [−10,−5,0,5,10]。礼物在编号三，预算可为二十。选区间 [−10,0] 得集合 {1,2,3}，选 [−5,5] 得 {1,3,4}，都签到三个；最小不同编号是二，属于前者，所以应选前者。

从原点出发访问最左 L≤0 与最右 R≥0，再返回，至少走过 [L,R] 两次，最短时间为 2(R−L)，按 0→L→R→0 正好达到。两端之间所有站点都可以零额外代价签到，故最优集合一定包含整个区间中的站点，同坐标的多个编号也全选。

加入一个不计站点数的原点虚拟点并排序。扫描右端，左端在宽度超预算的一半时右移，得到此右端下最靠左、包含站点最多的合法窗口。只考虑包含虚拟原点的窗口。第一遍用 floor(m/2)，第二遍用 floor((m+5)/2) 且额外要求礼物编号在窗口中。这样覆盖未拿礼物及拿到礼物两种情况；题目允许在时刻 m 之后才拿到礼物，只需最终在 m+5 前返回，不能额外限制拿礼物的时刻。

难点在同数量的编号集合比较，而非行动序列比较。两集合共同编号对字典序没有影响，最小的对称差编号决定结果：谁含它，谁的升序编号序列更小。两个坐标窗口各自减去另一窗口，都至多剩左右两段，故只需查询这些差段中的最小原编号，无须真正生成并排序两份大集合。

用迭代线段树维护坐标数组上每段的最小编号。空区间返回无穷，虚拟原点也记无穷，不参与集合比较。查询闭区间时，把两端移到叶子；左端为右孩子、右端为左孩子时取其边缘节点，再向上合并，每层只取常数块，总 O(log n)。每个同数量候选最多四次查询。

最终按选中窗口的坐标升序输出编号，跳过虚拟点，即实现 0→L→R→0 的最短路线。输出行的先后是访问顺序，不要求编号升序；被优化的是这些编号组成的集合。总路长与坐标差都用 long long，给定范围内最大往返长度四乘十的十八次方仍安全。''',
    r'''int n,p;long long budget;cin>>n>>budget>>p;vector<Location>points;points.reserve(n+1);
for(int id=1;id<=n;++id){long long x;cin>>x;points.push_back({x,id});}points.push_back({0,n+1});sort(points.begin(),points.end(),by_position);
int origin=0,gift=0;for(int i=0;i<=n;++i){if(points[i].id==n+1)origin=i;if(points[i].id==p)gift=i;}
RangeMin minimum(points,n);int best_left=origin,best_right=origin,best_count=0;
for(int pass=0;pass<2;++pass){long long width=(budget+(pass?5:0))/2;int left=0;
    for(int right=0;right<=n;++right){while(points[right].x-points[left].x>width)++left;
        if(!(left<=origin&&origin<=right))continue;
        if(pass&&!(left<=gift&&gift<=right))continue;
        int count=right-left; // 窗口内含一个不计数的虚拟原点
        if(count>best_count||(count==best_count&&lex_better(left,right,best_left,best_right,minimum))){best_count=count;best_left=left;best_right=right;}
    }
}
cout<<best_count<<'\n';bool first=true;
for(int i=best_left;i<=best_right;++i)if(points[i].id<=n){if(!first)cout<<' ';first=false;cout<<points[i].id;}cout<<'\n';''',
    '比较编号集合，输出实际路线；同坐标站点全部计数；礼物可以晚于原期限才取得。',
    r'排序及比较总时间 $O(n\log n)$、空间 $O(n)$。',
    tags=['双指针','排序','线段树'],lessons=S+['structures','functions','coordinates','two-pointers','segment-tree','bitwise'],checker='sign_route',
    declarations=r'''struct Location{long long x;int id;};
bool by_position(const Location&a,const Location&b){return a.x!=b.x?a.x<b.x:a.id<b.id;}
struct RangeMin{
    int base=1;vector<int>tree;
    RangeMin(const vector<Location>&points,int original){
        while(base<(int)points.size())base*=2;tree.assign(2*base,INT_MAX);
        for(int i=0;i<(int)points.size();++i)if(points[i].id<=original)tree[base+i]=points[i].id;
        for(int i=base-1;i>0;--i)tree[i]=min(tree[2*i],tree[2*i+1]);
    }
    int query(int l,int r)const{
        if(l>r)return INT_MAX;int answer=INT_MAX;l+=base;r+=base;
        while(l<=r){if(l&1)answer=min(answer,tree[l++]);if(!(r&1))answer=min(answer,tree[r--]);l/=2;r/=2;}
        return answer;
    }
};
bool lex_better(int l,int r,int old_l,int old_r,const RangeMin&minimum){
    int added=min(minimum.query(l,min(r,old_l-1)),minimum.query(max(l,old_r+1),r));
    int removed=min(minimum.query(old_l,min(old_r,l-1)),minimum.query(max(old_l,r+1),old_r));
    return added<removed;
}''')

add('P13824','双人状态的最小瓶颈递推，再按阈值查询最长路径',
    '两人在树上某活动路径的端点，每次可一人或两人各向根走一条边，位置平方距离不得超过给定阈值，求能成功会合的最长活动路径及最小端点编号。',
    r'''令 B[u][v] 为从两位置成功会合所需的最小阈值。B[u][u]=0；其它状态取当前平方距离与“所有合法下一状态的最小 B”之间的最大值。合法转移包括左人走、右人走、两人同时走，不能越过活动路径的最高点。按父先子后次序枚举 u、v 即可递推全部状态。将每对起点的阈值和树路径长度排序，前缀保留最长且编号最小者，查询二分阈值。''',
    r'''先看三点树：根坐标 (0,0)，两个孩子为 (10,0)、(10,1)。两人在孩子位置时，NC2 距离只有一；两人同时回根便会合，阈值一已经够用。若只允许一次移动一人，中间距离会达到一百或一百零一，反而错判。活动路径的两条通道长度却为一百与一百零一，总长二百零一；投掷距离与通道路径长是两种量。

定义 B[u][v] 回答一个独立问题：两人当前位于 u、v，在它们之间的活动路径内向根走，最少需要允许多大的投掷阈值，才能最终会合？同点已经成功，值零。其它状态必须先满足当前位置的 NC2 距离 D2(u,v)，之后至少一人移动，故

把当前位置平方距离记为 d，把所有合法下一状态中 B 的最小值记为 m，则

$$B[u][v]=\max(d,m).$$

固定一次下一步，整段计划所需阈值是当前距离与后续所需阈值的较大者；为让它尽量小，选择后续 B 最小的一步。这里不能把当前距离与后续阈值相加，因为约束是每次都不超过同一个上限。

u 可以移动到 parent[u]，当且仅当 u 不是 v 的祖先；若 u 已是祖先，它就是活动路径的最高点，再向上会离开路径。v 同理。两边都能走时，除了分别单走，还必须考虑同时走。每一步父节点深度更小，状态不会成环。

先求父节点、父先子后的顺序与祖先表。外层按这个顺序枚举 u，内层同序枚举 v，则 B[parent[u]][v] 已在更早外层算好，B[u][parent[v]] 已在当前外层更早内层算好，双人父状态也已存在，无需对一百万个状态递归。祖先表可让每个点沿父链标记，n≤1000，总成本至多 n²。

另存树上通道路径长 length[u][v]：若 u 能向父走，路径先经过这一条边，所以等于 edge_length[u]+length[parent[u]][v]；否则让 v 向父递推。边长使用坐标平方距离，绝不取平方根。

对每个 p≤q，得到所需阈值 B、路径长 length 和端点编号。按 B 排序，扫描维护“长度最大，其次 p 最小、再 q 最小”的前缀最佳答案。查询 d 时，upper_bound 找最后一个阈值≤d 的位置，读取该前缀最佳。对角状态阈值零、长度零，总有可行方案。''',
    r'''int n,queries;cin>>n>>queries;vector<Point>point(n+1);for(int i=1;i<=n;++i)cin>>point[i].x>>point[i].y;
vector<vector<int>>graph(n+1);for(int i=1;i<n;++i){int u,v;cin>>u>>v;graph[u].push_back(v);graph[v].push_back(u);}
vector<int>parent(n+1),order={1};vector<long long>edge_length(n+1);
for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:graph[u])if(v!=parent[u]){parent[v]=u;edge_length[v]=distance2(point[u],point[v]);order.push_back(v);}}
vector<vector<int>>ancestor(n+1,vector<int>(n+1));
for(int v=1;v<=n;++v)for(int u=v;u!=0;u=parent[u])ancestor[u][v]=1;
vector<vector<long long>>required(n+1,vector<long long>(n+1)),length(n+1,vector<long long>(n+1));
for(int u:order)for(int v:order)if(u!=v){
    bool move_u=!ancestor[u][v],move_v=!ancestor[v][u];long long next=LLONG_MAX;
    if(move_u)next=min(next,required[parent[u]][v]);if(move_v)next=min(next,required[u][parent[v]]);
    if(move_u&&move_v)next=min(next,required[parent[u]][parent[v]]); // 两人同时移动不能漏
    required[u][v]=max(distance2(point[u],point[v]),next);
    if(move_u)length[u][v]=edge_length[u]+length[parent[u]][v];
    else length[u][v]=edge_length[v]+length[u][parent[v]];
}
vector<Option>options;options.reserve(n*(n+1)/2);
for(int u=1;u<=n;++u)for(int v=u;v<=n;++v)options.push_back({required[u][v],length[u][v],u,v});
sort(options.begin(),options.end(),by_requirement);vector<long long>threshold;vector<int>best_u,best_v;
threshold.reserve(options.size());best_u.reserve(options.size());best_v.reserve(options.size());long long best_length=-1;int p=1,q=1;
for(auto option:options){
    if(option.length>best_length||(option.length==best_length&&(option.u<p||(option.u==p&&option.v<q)))){best_length=option.length;p=option.u;q=option.v;}
    threshold.push_back(option.required);best_u.push_back(p);best_v.push_back(q);
}
while(queries--){long long d;cin>>d;int at=(int)(upper_bound(threshold.begin(),threshold.end(),d)-threshold.begin())-1;cout<<best_u[at]<<' '<<best_v[at]<<'\n';}''',
    '平方距离不取根；两人同时走是一种独立选择；祖先端不能继续向根离开活动路径。',
    r'时间 $O(n^2\log(n+1)+t\log(n+1))$、空间 $O(n^2)$。',
    tags=['递推','二分查找','图论'],lessons=B+['structures','functions','graphs','trees','dp'],
    declarations=r'''struct Point{long long x,y;};
long long distance2(const Point&a,const Point&b){long long x=a.x-b.x,y=a.y-b.y;return x*x+y*y;}
struct Option{long long required,length;int u,v;};
bool by_requirement(const Option&a,const Option&b){return a.required<b.required;}''')

add('P6465','按相邻不同段扫描，统计已允许的左端点',
    '统计长度至少 l、相邻课程不同且首尾课程也不同的连续课程序列；长度一始终非法。',
    r'''先把有效最小长度设为 max(l,2)。扫描右端点，遇相邻相同则开启新段、清空此前左端计数。把当前长度限制下新允许的左端点逐个加入频次，答案增加允许左端总数减去与右端课程相同的频次。''',
    r'''以 [1,2,3,1,2]、最小长度三为例，右端在最后一个二时，允许左端为位置一、二、三。位置二的课程也是二，首尾相同必须排除，因此这一轮贡献两段，而不是三段。

任何包含相邻相同课程的区间都非法，因此一旦 c[i]=c[i−1]，新右端的合法区间只能从 i 或以后开始，上一段的左端计数全部丢弃。段内其它位置都已保证相邻不同，只剩长度与首尾限制。

对右端 i，长度至少 L 等价于左端≤i−L+1。在当前段内，从上次加入位置继续向右，把新允许的左端点加入频次。设允许左端总数为 eligible，课程 c[i] 的出现次数为 frequency[c[i]]，恰是首尾相同的非法左端数量，当前贡献为两者之差。

频次清空不用每次扫整个值域。另记本段真正出现过的课程编号 touched，开新段时只把这些频次归零。每个编号只有从零变为非零时登记一次，各段清空总成本不超过加入左端的次数。左右指针都只前进，总时间线性。长度 L=max(l,2)，明确排除了长度一；答案最多约 n²/2，使用 long long。''',
    r'''int tests;cin>>tests;while(tests--){int n,l;cin>>n>>l;l=max(l,2);vector<int>course(n),frequency(n+1),touched;for(int &x:course)cin>>x;
    int next_left=0,eligible=0;long long answer=0;
    for(int right=0;right<n;++right){
        if(right>0&&course[right]==course[right-1]){for(int x:touched)frequency[x]=0;touched.clear();next_left=right;eligible=0;}
        // 加入刚达到最小长度的左端，再排除首尾同值者。
        while(next_left<=right-l+1){int x=course[next_left++];if(frequency[x]==0)touched.push_back(x);++frequency[x];++eligible;}
        answer+=eligible-frequency[course[right]];
    }
    cout<<answer<<'\n';
}''',
    '长度一无论 l 为多少都非法；相邻重复要清段；首尾相同的左端单独扣除。',
    '每组时间、空间均为 $O(n)$。',tags=['连续段','双指针'],lessons=A+['two-pointers','counting'])

add('UVA11134','横纵分开，按右端优先分配最小可用坐标',
    '每个车只能位于给定闭矩形内，要求任意两车不同行也不同列，构造一种摆法或报告无解。多组零结束。',
    r'''横坐标、纵坐标独立处理。每个方向把允许区间按右端升序排列，用 set 保存未用坐标一到 n；给当前区间分配不小于左端的最小可用坐标，若不存在或超过右端则无解。两方向都成功后按原车编号组合输出。''',
    r'''矩形约束是“横坐标在某区间、纵坐标在另一段区间”，没有额外耦合。因此只要分别给所有车选到不同的合法横坐标、不同的合法纵坐标，两份选择组合后就得到矩形内互不攻击的摆法。

看一个方向。先处理右端最小、最紧迫的区间 I。令 p 为它当前最小可用位置。若某个完整解把 I 放在 q≥p：p 若没用，直接改到 p；p 若分配给尚未处理的 J，就让 I 用 p、J 改用 q。因为 J 原来能用 p，所以它的左端≤p≤q；它的右端不小于 I 的右端，又有 q≤I 的右端，所以 q 对 J 也合法。交换后仍有完整解，因此这一贪心选择不会破坏可行性。

`set.lower_bound(l)` 返回最小的未用坐标≥l，是有序集合自己的对数时间成员函数。分配后删除该坐标，防止重复。不能用某个任意空位或先处理左端，否则可能把紧区间仅有的位置占走。每个方向的结果保存到原始 id，输出仍按输入顺序。

官方完整题面：[UVa 11134 PDF](https://onlinejudge.org/external/111/11134.pdf)。每组可有多种正确摆法，程序无需与样例逐行相同；任一方向失败就输出 `IMPOSSIBLE`。''',
    r'''int n;while(cin>>n&&n){vector<Interval>x(n),y(n);for(int i=0;i<n;++i){cin>>x[i].left>>y[i].left>>x[i].right>>y[i].right;x[i].id=y[i].id=i;}
    // 两个方向各做一次独立匹配，结果仍按原车编号保存。
    vector<int>row(n),column(n);
    if(!assign_positions(x,n,row)||!assign_positions(y,n,column)){cout<<"IMPOSSIBLE\n";continue;}
    for(int i=0;i<n;++i)cout<<row[i]<<' '<<column[i]<<'\n';
}''',
    '两个方向独立、各坐标只能用一次；调用 set 成员 lower_bound；按原编号输出。',
    r'每组时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序'],lessons=B+['sets','structures','functions','greedy'],checker='rooks',
    declarations=r'''struct Interval{int left,right,id;};
bool by_right(const Interval&a,const Interval&b){return a.right<b.right;}
bool assign_positions(vector<Interval>intervals,int n,vector<int>&answer){
    sort(intervals.begin(),intervals.end(),by_right);set<int>available;for(int i=1;i<=n;++i)available.insert(i);
    for(auto interval:intervals){auto at=available.lower_bound(interval.left);
        if(at==available.end()||*at>interval.right)return false;
        answer[interval.id]=*at;available.erase(at);
    }
    return true;
}''')
