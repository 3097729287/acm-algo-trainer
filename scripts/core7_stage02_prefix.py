"""Prefix states, difference arrays, interval geometry and their applications."""
from core7_authoring import add

A=['io-basics','basic-control','arrays','vector','functions','integer']
S=A+['sort','iterators']
P=A+['prefix']
D=A+['difference']

add('P8649','统计相同前缀余数的此前出现次数',
    '统计数组中元素和为 K 的倍数的非空连续区间数量。',
    r'''区间和可被 K 整除，当且仅当它两端的前缀和对 K 取余相同。扫描当前前缀余数 r，答案增加此前 r 的出现次数，再把其频次加一。先登记空前缀余数零出现一次。''',
    r'''样例 [1,2,3,4,5]、K=2，含空前缀的余数为 [0,1,1,0,0,1]。零与一各出现三次，各自任选两个按下标先后配对，得到三段，总计六段。

令 S[i] 为前 i 项之和。区间 [l,r] 的和是 S[r]−S[l−1]，可被 K 整除等价于 S[r] 与 S[l−1] 同余。每对不同下标的同余前缀恰好对应一个非空区间，因此不必真的枚举区间或保存全部前缀和。

当前前缀到来时，频次数组只存此前位置。若相同余数已有 c 次，就有 c 个可选左边界，答案加 c，再登记当前一次。先查后加排除自己和自己配出的空区间；初始 cnt[0]=1 则包含从首项开始的区间。

维护余数时每次加新值再对 K 取模即可。输入是正数，无负余数问题；若推广到负输入，应做非负归一。最多 N(N+1)/2 段，答案用 long long，而不是只看单个 A_i 的大小选 int。''',
    r'''int n,k;cin>>n>>k;vector<long long>count(k);count[0]=1;int remainder=0;long long answer=0;
for(int i=0;i<n;++i){int x;cin>>x;remainder=(remainder+x)%k;answer+=count[remainder];++count[remainder];}
cout<<answer<<'\n';''',
    '空前缀先登记一次；先加此前次数再插入自己；区间数用 long long。',
    '时间 $O(n+k)$、频次数组空间 $O(k)$。',tags=['前缀和','取模与同余'],lessons=P+['modular'])

add('B3799','排序原值，用统一偏移量求所有正数之和',
    '支持全体元素加一个整数，以及查询允许为空、无需连续的最大子序列和。',
    r'''子序列不要求连续，最优选择恰好是全部正数。所有加法只改变统一偏移 delta，不改变相对次序，故原数组排序后不再修改。二分找到原值大于 −delta 的后缀，用原值前缀和加上后缀长度乘 delta 得答案。''',
    r'''样例最初 [-5,12,-7,2,8] 的最优子序列是 12、2、8，和二十二；负数可以直接跳过，不能误当成“最大连续子数组”。没有正数时选择空子序列，答案为零。

先把原值排成 b，并保存前缀和。经历若干全局加法后，每个实际值都为 b[i]+delta。某项应被选取，当且仅当 b[i]>−delta。加同一个数不会打乱大小顺序，故所有正值始终是一个后缀，无需每轮重新排序。

`upper_bound(b.begin(),b.end(),-delta)` 返回首个严格大于阈值的位置 p。p 前的实际值均不正，p 到 n−1 的原值和为 prefix[n]−prefix[p]，实际和还要加 (n−p)×delta。等于零的值选不选都不影响和，使用严格大于能让解释与代码一致。

更新只令 delta+=k，查询才二分。delta 最坏可达约 2.5×10¹¹，最终和还要乘数量，偏移、前缀及答案统一用 long long。二分阈值也必须保持 long long，不能先截成 int。''',
    r'''int n,m;cin>>n>>m;vector<long long>a(n),prefix(n+1);for(auto &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)prefix[i+1]=prefix[i]+a[i];long long delta=0;
while(m--){int op;cin>>op;if(op==1){long long k;cin>>k;delta+=k;}
    else{int p=(int)(upper_bound(a.begin(),a.end(),-delta)-a.begin());cout<<prefix[n]-prefix[p]+(n-p)*delta<<'\n';}}
''',
    '子序列可以不连续且可以为空；全局加法只改偏移，不改排序数组。',
    r'预处理 $O(n\log n)$，更新 $O(1)$，查询 $O(\log n)$，空间 $O(n)$。',
    tags=['排序','前缀和','二分查找'],lessons=S+['prefix','bounds'])

add('P1496','按左端点排序并合并相交区间',
    '给定左闭右开的燃烧区间，求它们并集的总长度，重复覆盖只算一次。',
    r'''按左端点升序排序，维护当前合并段 [left,right)。下一段左端点不超过 right 时扩展右端点；否则结算 right−left 并另起一段。扫描结束再结算最后一段。''',
    r'''样例区间 [−1,1)、[5,11)、[2,9) 排序后为 [−1,1)、[2,9)、[5,11)。后两段合并成 [2,11)，长度九，加上第一段长度二，得到十一。不能把各段长度直接相加，否则重叠的 [5,9) 会多算。

处理完前若干段，已经结算的并集与当前段严格分开。新段按左端点到来：若它的左端点≤当前右端点，两段相交或首尾相接，并集仍是一段，只需取更大的右端点。若左端点更大，中间已有空隙，后续左端点只会更大，旧段不会再被延伸，便可安全结算。

输入坐标可在整个有符号三十二位范围内，虽然题目保证总答案小于 2³¹，计算端点差前仍应先用 long long 保存。左闭右开的长度是 r−l，不加一；两个相接区间可合并，也不会凭空增加长度。''',
    r'''int n;cin>>n;vector<pair<long long,long long>>segments(n);for(auto &s:segments)cin>>s.first>>s.second;
sort(segments.begin(),segments.end());long long left=segments[0].first,right=segments[0].second,answer=0;
for(int i=1;i<n;++i){
    if(segments[i].first<=right)right=max(right,segments[i].second);
    else{answer+=right-left;left=segments[i].first;right=segments[i].second;}
}
cout<<answer+right-left<<'\n';''',
    '求实数轴长度，不按整数点计数；最后一段必须结算。',
    r'时间 $O(n\log n)$、保存区间空间 $O(n)$。',tags=['排序','贪心'],lessons=S+['greedy','coordinates'])

add('P3131','每个模七前缀保存最早位置',
    '找编号和可被七整除的最长连续牛群长度；不存在非空合法段时输出零。',
    r'''维护前缀和对七的余数。相同余数的两个前缀之间就是合法段；固定当前右端点，应选最早的相同余数位置。只存七种余数的首次位置，初始零余数在位置零。''',
    r'''“Subsequences”在标题里容易误导，但题意明确要求连续牛群。样例的 [5,1,6,2,14] 是一整段，和二十八、长度五，不能随意从各处挑牛。

区间和是两端前缀的差，可被七整除等价于两个前缀余数相同。当前右端点为 i，若余数 r 最早在 j 出现，就得到长度 i−j。使用更晚位置只会更短，因此余数第一次出现时记录，之后永远不覆盖。

与统计区间数量的做法不同，这里不需要频次，也不需要把所有配对累加，只需要每个余数的最远跨度。用 −1 表示尚未出现，避免和合法的前缀零位置混淆；空前缀使从第一头牛起的合法群也能被识别。每次只保存余数，不会累加出很大的编号总和。''',
    r'''int n;cin>>n;int first[7];fill(first,first+7,-1);first[0]=0;int remainder=0,answer=0;
for(int i=1;i<=n;++i){int id;cin>>id;remainder=(remainder+id)%7;
    if(first[remainder]==-1)first[remainder]=i;else answer=max(answer,i-first[remainder]);}
cout<<answer<<'\n';''',
    '要求连续；保存首次位置而非最近位置；零余数的空前缀必须存在。',
    '时间 $O(n)$、额外空间 $O(1)$（七个状态）。',tags=['前缀和','取模与同余'],lessons=P+['modular'])

add('P7714','在前缀最大值等于位置处切分排列',
    '一次可以按区间长度付费，把该区间升序排序，求将整个排列排成一到 n 的最小总费用。',
    r'''扫描前缀最大值 maximum。若 maximum=i，则前 i 个数恰为一到 i，可以在这里切开。相邻切点形成互不依赖的最小块：长度一已就位，不付费；其余块整体排序一次，费用等于长度。累加这些非平凡块的长度。''',
    r'''排列 [2,1,3,5,4] 可分成 [2,1]、[3]、[5,4]。中间的三已正确，其余两块各排序一次，费用二加二为四；把从第一个错位到最后一个错位的整段直接排序则要五。

一个边界 i 能把问题分开，当且仅当前 i 项的集合就是一到 i。因为输入是排列，前缀有 i 个不同正数，只要最大值等于 i 就恰好满足；不需要另建集合或求元素和。相邻可切边界之间再无可切点，称为最小块。

为什么一个长度大于一的最小块至少花它的长度？若某条内部相邻分界线从未被任何排序操作跨过，线两侧的元素就永远无法交换，最后正确要求原前缀已经包含一到该位置，与块内不可切矛盾。所以每条内部线都必须被某个操作跨过。把相交的操作区间连成组件，每个最小块内必须有一个连通组件横跨全部内部线，其覆盖跨度至少等于块长，操作长度之和当然不小于其并集跨度。跨多个块操作也不能节省这个下界。

对每个非平凡块直接整体排序，恰好达到块长，长度一的块原本就是正确值。代码只计算费用，无需真实排序或输出操作。多组数据的 maximum、上一个切点都要重置。''',
    r'''int tests;cin>>tests;while(tests--){
    int n;cin>>n;int maximum=0,previous=0,answer=0;
    for(int i=1;i<=n;++i){int x;cin>>x;maximum=max(maximum,x);
        if(maximum==i){int length=i-previous;if(length>1)answer+=length;previous=i;}}
    cout<<answer<<'\n';
}''',
    '长度一的块费用为零；不能只数错位元素，操作区间中的正确位置也可能必须付费。',
    '每组时间 $O(n)$、额外空间 $O(1)$。',tags=['连续段','贪心'],lessons=A+['greedy','permutations'])

add('P9749','按累计路程的整数升需求分配最低价格',
    '油箱无限大，每站只卖整数升，每升能行驶 d 公里，求从第一站到最后一站的最低购油费用。',
    r'''到下一站前，累计至少需要 ceil(累计路程/d) 升油。维护此前最低单价，以及已经分配过的整数升数；本段新增的需求升数全部按此前最低单价计费。最后一站的油价不参与任何行驶需求。''',
    r'''整数升限制要放在累计路程上。例如每升走四公里，连续两段各十公里：第一段前需要三升，第二段累计二十公里只需五升，新增两升；若对每段单独上取整，会错误地买六升。

把最终购买的每一升按编号一、二、三……区分。某段行驶前累计路程从 old 增为 distance，必须新增的升数是 ceil(distance/d)−ceil(old/d)。这些升油最迟必须在当前出发站买到，但可以在更早任一站购买，且没有容量限制，因此每升都可独立选择这些站中的最低单价。

代码中的“按此前最低价格计费”是在计算一份离线购油分配，不是说汽车此刻能够开回过去。把归给早站的所有升数在经过该站时一次买足，就是实际可行方案；额外提前存油没有上限。反过来，每升的购买地点都不能晚于它第一次必需的路段，价格至少为此前最低价，故该分配也达到下界。

读入全部路段和油价后，按出发站 i 更新最低价，再累计第 i 段距离、结算新增整升。不能把终点价格提前用于上一段，否则相当于没油也能先到终点。距离、升数和乘单价后的总费用都用 long long。''',
    r'''int n;long long d;cin>>n>>d;vector<long long>road(max(0,n-1)),price(n);
for(auto &x:road)cin>>x;for(auto &x:price)cin>>x;
long long distance=0,litres=0,cheapest=LLONG_MAX,answer=0;
for(int i=0;i+1<n;++i){
    cheapest=min(cheapest,price[i]);distance+=road[i];long long need=(distance+d-1)/d;
    answer+=(need-litres)*cheapest;litres=need;
}
cout<<answer<<'\n';''',
    '对累计路程上取整；只能使用当前站及之前的价格；终点无须再买油。',
    '时间与保存输入空间均为 $O(n)$。',tags=['贪心','前缀和'],lessons=P+['greedy','basic-arithmetic'])

add('P14028','差分统计调整次数，再比较可达区间',
    '每次给一个下标区间，区间内每项可各自加一、减一或不变，求全部操作后数组最大值减最小值的最小可能值。',
    r'''差分求每个位置被操作 c[i] 次，则它独立可达到 [a[i]−c[i],a[i]+c[i]] 中任一整数。令 L 为所有下界的最大值，R 为所有上界的最小值，答案为 max(0,L−R)。''',
    r'''一个位置被选中 c 次，每轮都能独立选加一、减一或不动，因此最终偏移可以是 −c 到 c 中任意整数。允许不动消除了奇偶限制，而且同一次区间操作内不同元素也可分别选择，没有总增量预算。故每个位置只剩一个独立可达区间。

用差分统计次数：每个 [l,r] 在 l 加一、r+1 减一，前缀还原得到 c[i]。定义 L=max(a[i]−c[i])、R=min(a[i]+c[i])。若 L≤R，所有可达区间有共同整数，全部取该数，极差零。

若 L>R，某项的下界为 L，所以最终最大值至少 L；某项的上界为 R，所以最终最小值至多 R，极差至少 L−R。这个下界可以达到：把每项选在自身区间与 [R,L] 的交集中。因为每个下界≤L、每个上界≥R，这个交集一定非空；所有选值都位于 [R,L]，极差不会超过 L−R。两端约束又迫使实际达到这两个极值。

不需要二分极差，也不需要决定每次具体怎样操作。所选偏移 d 满足 |d|≤c，任取 |d| 次选对应方向，其余不动，就可实现。每组重新清空差分，端点 r+1 应预留一个位置。''',
    r'''int tests;cin>>tests;while(tests--){
    int n,m;cin>>n>>m;vector<long long>a(n+1);for(int i=1;i<=n;++i)cin>>a[i];vector<int>difference(n+2);
    while(m--){int l,r;cin>>l>>r;++difference[l];--difference[r+1];}
    int count=0;long long lower=LLONG_MIN,upper=LLONG_MAX;
    for(int i=1;i<=n;++i){count+=difference[i];lower=max(lower,a[i]-count);upper=min(upper,a[i]+count);}
    cout<<max(0LL,lower-upper)<<'\n';
}''',
    '每个位置可独立调整；不变也合法，所以没有奇偶限制；求最大下界与最小上界。',
    '每组时间 $O(n+m)$、空间 $O(n)$。',tags=['差分','贪心'],lessons=D+['greedy','coordinates'])

add('UVA11059','枚举左端点并逐项扩展乘积',
    '求非空连续区间的最大正乘积，没有正乘积时答案为零。多组读到 EOF，原题约束 n≤18、每项在负十到十之间。',
    r'''枚举区间左端点，乘积从一开始，右端点每向右一步就乘一个新值并更新答案。答案初始零，自动排除负乘积。只需 n(n+1)/2 次扩展，不用前缀乘积除法。''',
    r'''负数会改变乘积正负，零会让跨过它的区间乘积归零，因此不能像正数滑窗一样只按大小移动左端点。n 至多十八，直接枚举全部连续区间最清楚：固定 l，依次扩展 r，当前 product 始终等于 a[l] 到 a[r] 的乘积。

乘积在每个新左端点重新设一，这个一只是相乘的起始值，尚不作为一个空区间候选。只有乘入至少一个数后才更新答案，故没有错误地把空段乘积一输出。答案从零开始，对应题目“没有正结果则输出零”的约定；例如单个负数答案零，两个负数的乘积则可能最优。

绝对值最大 10¹⁸，在有符号 long long 范围内；int 会溢出。逐项相乘也避开了前缀乘积遇零不能相除的问题。按 EOF 处理多组，编号从一开始，句点和每组后的空行照原题输出。

题面来源与完整约束：[UVa 11059 官方 PDF](https://onlinejudge.org/external/110/11059.pdf)。''',
    r'''int n,test=0;while(cin>>n){
    vector<long long>a(n);for(auto &x:a)cin>>x;long long answer=0;
    for(int l=0;l<n;++l){long long product=1;for(int r=l;r<n;++r){product*=a[r];answer=max(answer,product);}}
    cout<<"Case #"<<++test<<": The maximum product is "<<answer<<".\n\n";
}''',
    '答案初始零而非一；每个左端点重置乘积；保留输出句点与组间空行。',
    '每组时间 $O(n^2)$、保存输入空间 $O(n)$。',tags=['枚举'],lessons=A+['enumeration'],exact=True)

add('P1719','枚举上下边界，压成非空最大子段和',
    '求整数方阵中非空、边与网格平行的子矩形最大元素和，允许所有元素都是负数。',
    r'''枚举上边 top，再逐行向下扩展 bottom，维护每一列在两行之间的总和。固定上下边后，找最佳左右边等价于求这个列和数组的最大非空连续子段和，用“在本列重新开始，或延长上一段”线性递推。''',
    r'''样例最佳矩形取第二到第四行、第一到第二列。压缩后的两列分别为 9−4−1=4、2+1+8=11，相加十五。一般地，只要上下两行固定，任意左右边界的矩形和就是对应连续列和。

对固定 top，将列和清零，bottom 每增加一行，就给每一列加上这一行的值，避免重新计算整个高度。随后扫描列，令 ending 表示“必须以当前列结束”的最大非空段和。当前列值 x 必须选入：要么从 x 重新开始，要么把 x 接到前一列最佳结束段后面，因此 ending=max(x,ending+x)。用另一个全局答案接收所有 ending。

例如列和 [−5,−2,−7]，非空答案应为 −2，而不是零。因此每次新扫描的首列直接设 ending=column_sum[0]，全局答案初始为最小整数；不能把“允许空段”的版本照搬过来。

每个矩形有唯一上下边界，固定它们后线性递推检查所有可能的右边界，已覆盖最佳左右边界，因此没有遗漏。n≤120，三层规模约 n³ 可以处理；枚举四个边界的 n⁴ 则做了不必要的工作。''',
    r'''int n;cin>>n;vector<vector<long long>>a(n,vector<long long>(n));for(auto &row:a)for(auto &x:row)cin>>x;
long long answer=LLONG_MIN;
for(int top=0;top<n;++top){vector<long long>sum(n);
    for(int bottom=top;bottom<n;++bottom){
        for(int column=0;column<n;++column)sum[column]+=a[bottom][column];
        long long ending=sum[0];answer=max(answer,ending);
        for(int column=1;column<n;++column){ending=max(sum[column],ending+sum[column]);answer=max(answer,ending);}
    }
}
cout<<answer<<'\n';''',
    '矩形不能空；全负数组应返回最大单格值；每换上边界重新清空列和。',
    '时间 $O(n^3)$、输入矩阵空间 $O(n^2)$，列和额外空间 $O(n)$。',
    tags=['枚举','线性 DP'],lessons=A+['enumeration','dp','prefix'])

add('P2879','可见区间去重后给内部位置统一减一',
    '已知最高奶牛的身高 H 及若干可见关系，求每个位置的最大可能身高，输入保证所有约束可同时满足。',
    r'''开始把全部奶牛看作 H。每条不同的可见端点对 (l,r)，让严格内部 [l+1,r−1] 的身高上界降一，端点不降。用差分一次处理区间减一，注意相同关系必须去重，最后前缀还原。''',
    r'''若一头牛能看见另一头，中间所有牛必须比两个端点都矮，至少矮一。样例关系一看见三，使位置二至少低一层；三看见七，又使四、五、六低一层；五看见三相当于三到五内部的四再低一层，便得到 H=5 时的 [5,4,5,3,4,4,5,5,5]。

为何多条关系可以每条各减一，而不是只减一次？对一头牛，包含它的可见区间只能嵌套或共享端点地套起来。若两个区间交叉，如 l₁<l₂<r₁<r₂，第一条迫使 l₂ 比 r₁ 矮，第二条却迫使 r₁ 比 l₂ 矮，矛盾；可行输入排除了它们。每深入一层，都能沿一个位于外层内部的端点再严格降一级，所以身高至多为 H 减覆盖它的不同区间数。

将每个位置实际设为这个上界也能实现：外层对整段一致降低，某可见区间又让内部比端点多降低至少一级，内层只会继续降低其中位置，不会破坏可见性。原题带方向的关系还要求被看者不矮于看者；若某个区间覆盖被看者却不覆盖看者，就会反向强制它更矮，与该关系矛盾，故可行性同样排除这种情形。

相同端点对重复提供的是同一约束，不能每出现一次都多降低一层。先把端点归为 l<r，用 set 去重；成功插入才在 l+1 减一、r 加一。相邻端点内部为空，可直接跳过。已知最高牛的下标不需另参与运算：输入保证它不会处在某条可见区间的严格内部，否则它就不可能最高。''',
    r'''int n,highest,height,relations;cin>>n>>highest>>height>>relations;vector<int>difference(n+2);set<pair<int,int>>seen;
while(relations--){int l,r;cin>>l>>r;if(l>r)swap(l,r);
    if(seen.insert({l,r}).second&&l+1<r){--difference[l+1];++difference[r];}}
int change=0;for(int i=1;i<=n;++i){change+=difference[i];cout<<height+change<<'\n';}''',
    '只降低严格内部；重复关系去重；输入保证可行是层数构造成立的前提。',
    r'R 条关系下，时间 $O(n+R\log(R+1))$、空间 $O(n+R)$。',
    tags=['差分'],lessons=D+['sets'])

add('P3948','差分承接修改，少量在线询问扫描，末尾询问用前缀计数',
    '初始全零数组支持区间加和条件计数；在线计数至多一千次，最后还有大量只查询、不再修改的区间询问。取余按 C++ 的负数规则。',
    r'''区间加只改差分两端。每次在线 Q 从位置一还原到 R，检查 [L,R] 内 (a[i]×i)%mod 是否落在闭区间内。所有修改结束后一次还原全数组，生成“满足条件记一”的前缀和，最后每次查询只做一次前缀相减。''',
    r'''本题的关键限制是在线 Q 最多一千次，之后的 Final 次询问之间不再有修改。不能把所有操作都当成同样频繁的动态查询，也不需要为一般取模条件设计复杂平衡树。

差分 difference[L]+=X、difference[R+1]−=X 可以常数时间登记一次区间加。在线查询时，当前数组值要从差分位置一开始累加；即使只问 [L,R]，也不能从 L 把累计值清零，否则会漏掉此前开始的修改。扫到 R 即可停止，只对 i≥L 的值判定条件。

累计 a[i] 最坏约为操作数乘 int 上限，long long 能保存，但再乘下标可能溢出。先算 (a[i]%mod)×i，再对 mod 取余，乘积绝对值至多约 2³¹×80000，安全。i 为正数，这样计算与直接精确求 a[i]×i 的 C++ 余数一致；负余数不能擅自加 mod 转为非负，因为题面明确使用向零截断的负余数规则。

读完全部 opt 操作后，差分不再改变。还原一次并令 good[i] 表示当前位置是否满足 min≤余数≤max，构造 prefix[i]=prefix[i−1]+good[i]。于是 Final 阶段任意闭区间答案都是 prefix[R]−prefix[L−1]，不用再次扫描。海量询问逐条读取输出，不保存全部输入，也不使用每行强制刷新的 endl。模运算的除数必须非零，这是余数定义本身的前提。''',
    r'''int n,operations;long long modulus,minimum,maximum;cin>>n>>operations>>modulus>>minimum>>maximum;
vector<long long>difference(n+2);
while(operations--){char type;int l,r;cin>>type>>l>>r;
    if(type=='A'){long long x;cin>>x;difference[l]+=x;difference[r+1]-=x;}
    else{long long value=0;int answer=0;
        for(int i=1;i<=r;++i){value+=difference[i];if(i>=l){long long rem=(value%modulus)*i%modulus;answer+=minimum<=rem&&rem<=maximum;}}
        cout<<answer<<'\n';
    }
}
vector<int>prefix(n+1);long long value=0;
for(int i=1;i<=n;++i){value+=difference[i];long long rem=(value%modulus)*i%modulus;prefix[i]=prefix[i-1]+(minimum<=rem&&rem<=maximum);}
int final_queries;cin>>final_queries;while(final_queries--){int l,r;cin>>l>>r;cout<<prefix[r]-prefix[l-1]<<'\n';}''',
    '在线还原必须从位置一开始；负余数遵循 C++；先取余再乘下标避免溢出。',
    '设在线查询 Q≤1000、末尾查询 F，总时间 $O(opt+nQ+n+F)$、空间 $O(n)$。',
    tags=['差分','前缀和'],lessons=D+['prefix','modular'])

add('P5542','二维差分还原每个单位方格的涂层数',
    '多次给平面中的整数坐标矩形涂一层漆，求最终恰有 K 层漆的面积，矩形边界不额外贡献面积。',
    r'''把每个矩形看作 [x1,x2)×[y1,y2)。在四个角登记 +1、−1、−1、+1 的二维差分，做二维前缀还原。每个整数格代表一个单位正方形，覆盖层数恰为 K 时面积加一。''',
    r'''左下角 (1,1)、右上角 (5,5) 的矩形包含横坐标一到五之间、纵坐标一到五之间的区域，面积十六。它覆盖的是 x=1,2,3,4 与 y=1,2,3,4 对应的十六个单位格，不是把五乘五个格点都算入。

在差分表中，(x1,y1) 加一，表示从这里往右、往上都多一层；(x2,y1) 与 (x1,y2) 各减一，分别在横向、纵向终点撤销；(x2,y2) 加一，补回被两次撤销的右上区域。做二维前缀和后，仅原矩形内保留一层，矩形外抵消为零。

还原公式为 value[x][y]=diff[x][y]+value[x−1][y]+value[x][y−1]−value[x−1][y−1]。左、下两块都包含左下重叠部分，所以要减一次，不能把两个前缀直接相加。坐标范围零到一千，对应单位格左下角零到九百九十九，扫描这些格，值为 K 就加一面积。

涂漆次数只影响差分记录，最终只需一次固定网格扫描。K 至少一，因此无需考虑无限平面中没有涂漆的区域；边界线面积为零，统一用半开矩形处理即可。''',
    r'''int n,k;cin>>n>>k;const int LIMIT=1000,SIZE=1001;vector<vector<int>>difference(SIZE,vector<int>(SIZE));
while(n--){int x1,y1,x2,y2;cin>>x1>>y1>>x2>>y2;++difference[x1][y1];--difference[x2][y1];--difference[x1][y2];++difference[x2][y2];}
int area=0;
for(int x=0;x<LIMIT;++x)for(int y=0;y<LIMIT;++y){
    if(x>0)difference[x][y]+=difference[x-1][y];if(y>0)difference[x][y]+=difference[x][y-1];
    if(x>0&&y>0)difference[x][y]-=difference[x-1][y-1];area+=difference[x][y]==k;
}
cout<<area<<'\n';''',
    '右上边界不另加一；统计单位格面积，不统计格点；二维还原要扣重叠前缀。',
    '坐标上限 M=1000，时间 $O(n+M^2)$、空间 $O(M^2)$。',
    tags=['差分','前缀和'],lessons=A+['rectangle-difference'])

add('P9533','零异或翻转只重排前缀异或值，答案不变',
    '可以任意次翻转异或和为零的连续区间，求操作后最多能有多少个零异或区间。',
    r'''零异或区间的两个端点前缀异或相同。翻转一个零异或区间，只会将其内部前缀异或值反序，不改变全部前缀值的频次，因此零异或区间总数始终不变。直接统计原数组相同前缀异或的配对数即可。''',
    r'''样例 [3,1,2,3] 的前缀异或是 [0,3,2,0,3]。翻转前三项后为 [2,1,3,3]，前缀异或变成 [0,2,3,0,3]，只是内部的三与二换了顺序；零出现两次、三出现两次，仍有两个合法区间。

令 P[i] 为前 i 项异或，P[0]=0。区间 [l,r] 的异或为 P[r] xor P[l−1]，为零当且仅当两值相等。所以只要知道每个前缀值出现几次，答案就是每组任取两个下标的配对数，与这些值排列在前缀序列中的先后无关。

现翻转一个允许的区间 [l,r]。由于它整体异或零，P[l−1]=P[r]。对内部位置 j，翻转后的局部前缀等于原区间一个后缀的异或；用整体零消去该后缀以外的部分，可得新 P[j]=旧 P[l+r−1−j]。因此内部前缀值被逆序，两端相等值与区间外前缀不变，全部值的多重集合保持不变。

任意次操作都是上述不变操作的复合，故不可能提高或降低答案，零次操作已达到最大。扫描时先登记空前缀零，每个新前缀值出现时累加此前同值次数，再增频。a[i]<2²⁰，所有前缀异或也在该范围，直接开频次数组即可。''',
    r'''int n;cin>>n;vector<long long>count(1<<20);count[0]=1;int prefix=0;long long answer=0;
for(int i=0;i<n;++i){int x;cin>>x;prefix^=x;answer+=count[prefix];++count[prefix];}
cout<<answer<<'\n';''',
    '不必真实执行翻转；统计所有前缀含空前缀；频次配对数用 long long。',
    '值域 U=2²⁰，时间 $O(n+U)$、空间 $O(U)$。',tags=['前缀和','位运算'],lessons=P+['bitwise','counting'])

add('P10719','枚举行带，再用非负列计数做滑窗',
    '求至少包含 k 个黑格的最小非空轴平行子矩形面积，不存在则输出零。',
    r'''固定上边并逐行扩展下边，维护各列黑格数。固定行带后，各列计数非负，用双指针寻找和至少 k 的最短连续列段，每找到一段用高度乘宽度更新面积。枚举全部上下边覆盖所有矩形。''',
    r'''把第二到第四行压成每列黑格数量后，选某段连续列的总黑格数，就是对应矩形黑格数。只要上下边固定，高度不变，面积最小等价于列区间最短。

右指针依次纳入新列，窗口黑格总数随之增加或不变。若总数已经达到 k，当前窗口合法，先记录面积，再删掉最左列尝试缩短；只要仍达到 k 就继续。这是非负性保证的：删左列不会增加总数，因此某个右端点下，第一次不够后无需再删。

零黑格列也应正常删掉，它们不提供数量却占宽度。k≥1，空窗口永不满足条件，不会得到面积零的伪答案。对每个上下边组合，左右指针各至多走 m 步，窗口处理线性；下边每加一行只给列计数加这一行，不重新扫描整个行带。

全局答案初始为 n×m+1。若所有行带都没有达到 k，输出零。n、m≤100，O(n²m) 足够。与最大矩形和不同，本题列计数没有负数，正是可以使用滑动窗口的原因。''',
    r'''int n,m,k;cin>>n>>m>>k;vector<string>grid(n);for(auto &row:grid)cin>>row;int answer=n*m+1;
for(int top=0;top<n;++top){vector<int>columns(m);
    for(int bottom=top;bottom<n;++bottom){
        for(int c=0;c<m;++c)columns[c]+=grid[bottom][c]=='1';
        int left=0,black=0;
        for(int right=0;right<m;++right){black+=columns[right];
            while(left<=right&&black>=k){answer=min(answer,(bottom-top+1)*(right-left+1));black-=columns[left++];}
        }
    }
}
cout<<(answer==n*m+1?0:answer)<<'\n';''',
    '面积为高度乘宽度；零黑格列应允许收缩；无解输出零。',
    '时间 $O(n^2m)$、输入空间 $O(nm)$，辅助列数组 $O(m)$。',
    tags=['枚举','双指针'],lessons=A+['enumeration','two-pointers'])

add('P12674','分别累计划分数量、旧贡献及候选末块乘积',
    '把序列完整划分成若干连续块，每块两端值相等；每种划分贡献为各块元素乘积之和，求所有合法划分贡献总和取模。',
    r'''令 ways、total 是此前前缀的合法划分数及贡献总和。按候选末块的左端值 v，分别累计其左侧划分数 C[v]、左侧旧贡献 S[v]、左侧划分数乘当前末块乘积 W[v]。读 x 后先新增左端为当前位的候选，再给所有 W 乘 x，当前 ways=C[x]、total=S[x]+W[x]。值域仅四十，逐组更新即可。''',
    r'''每次在末尾放一个新块，整份划分的贡献等于“左侧已有各块的贡献”加上“新块的乘积”。后者对每一种左侧划分都要加一次，因此既要记贡献总和，也要记划分数量，不能只维护一个答案。

设候选末块左端为 l，当前右端为 i。若 A[l]=A[i]，它可作为最后一块。此前前缀 [1,l−1] 的 ways[l−1] 种合法划分，每种均可接这同一末块，合计贡献为

$$total[l-1]+ways[l-1]\prod_{j=l}^{i}A[j].$$

对所有左端值相同的候选分组。C[v] 保存这些 ways[l−1] 的和，S[v] 保存 total[l−1] 的和，W[v] 保存 ways[l−1] 乘已读末块乘积的和。新读 x 时，先把以当前位置为左端的候选加入组 x：它的左侧状态就是上一轮 ways、total，新块暂按空乘积一计；随后所有候选块都多包含当前 x，故全部 W[v] 乘 x。

更新后，只需选择左端值等于当前右端 x 的组。合法划分数为 C[x]，贡献总和为 S[x]+W[x]。S 是每个左端只加入一次的旧贡献，不能跟着乘 x；只有末块乘积 W 要乘。初始化空前缀 ways=1、total=0，使单个块能自然从空前缀开始。

样例 [1,2,2,1] 的三种合法划分贡献分别为六、六、四，总数十六。值域最大四十，直接每轮扫描四十组，避免对前缀乘积求逆或处理除法，复杂度可接受。''',
    r'''const long long MOD=998244353;int n;cin>>n;long long count[41]={},sum[41]={},weighted[41]={};
long long ways=1,total=0;
for(int i=0;i<n;++i){int x;cin>>x;
    count[x]=(count[x]+ways)%MOD;sum[x]=(sum[x]+total)%MOD;weighted[x]=(weighted[x]+ways)%MOD;
    for(int v=1;v<=40;++v)weighted[v]=weighted[v]*x%MOD;
    ways=count[x];total=(sum[x]+weighted[x])%MOD;
}
cout<<total<<'\n';''',
    '旧贡献 S 不乘当前值；候选左端先加入再更新乘积；空前缀有一种划分。',
    '值域 V=40，时间 $O(nV)$、额外空间 $O(V)$。',tags=['线性 DP','组合计数'],lessons=A+['dp','counting','modular'])

add('P13787','二维差分还原覆盖数后逐格异或累加',
    '给定许多覆盖闭区间格子的矩形地毯，求所有格子的 (行号+列号) xor 覆盖次数之和。',
    r'''闭矩形 [x1,x2]×[y1,y2] 的差分撤销点在 x2+1、y2+1。四角登记后做二维前缀还原，每个格子得到覆盖数 F，再把 ((i+j) xor F) 加到 long long 答案。''',
    r'''这次坐标代表格子编号，右下角的格子也被覆盖，所以与连续面积题不同，撤销必须放在终点的下一格：左上加一，(x2+1,y1) 与 (x1,y2+1) 减一，(x2+1,y2+1) 加一。

二维还原时，当前覆盖数等于原差分加上上一行已还原值、左边已还原值，再减左上角已还原值，因为那部分被前两项重复包含。按行从上到下、列从左到右扫描，三份来源都已算好，可直接在差分数组原地保存最终覆盖数。

题目最后的“和”是普通加法，只有每个格子内部把 i+j 与 F 做按位异或。代码必须明确写 `answer+=((i+j)^coverage)`，不能把所有格子也整体异或起来，更不能把 xor 当乘方。最大单格覆盖数为 m，但 n² 个格子相加可能远超 int。

n≤5000，二维 int 数组约一亿字节。使用连续的一维 vector 按 row×stride+column 索引，保留 n+2 的行列边界，避免再复制一份同规模前缀表。地毯条数只影响四角更新，总扫描仍是 n²。''',
    r'''int n,m;cin>>n>>m;int stride=n+2;vector<int>grid((size_t)stride*stride);
while(m--){int x1,y1,x2,y2;cin>>x1>>y1>>x2>>y2;
    ++grid[(size_t)x1*stride+y1];--grid[(size_t)(x2+1)*stride+y1];
    --grid[(size_t)x1*stride+y2+1];++grid[(size_t)(x2+1)*stride+y2+1];
}
long long answer=0;
for(int i=1;i<=n;++i)for(int j=1;j<=n;++j){size_t at=(size_t)i*stride+j;
    grid[at]+=grid[at-stride]+grid[at-1]-grid[at-stride-1];answer+=((i+j)^grid[at]);
}
cout<<answer<<'\n';''',
    '闭区间在终点后一格撤销；每格先异或再普通求和；只保留一份二维数组。',
    '时间 $O(m+n^2)$、空间 $O(n^2)$。',tags=['差分','前缀和','位运算'],lessons=A+['rectangle-difference','bitwise'])

add('P14520','兵力优势可撤退保全，劣势方只剩立即攻占',
    '两方在一条城市线上交替转移或攻占，左方先手且攻占须严格更多兵力，右方允许相等；对每个初始分界求赢家。',
    r'''当前轮到的一方若总兵力有优势，就可把前线兵力逐城向后撤并汇合，保住全部兵力后反攻；左方须总兵力严格更大，右方相等也能胜。若初始左方没有优势，只有立即攻占能改变总量。检查这次攻占是否使左方总兵力反超，再检查右方下一城是否能立即反击；反击会在左方前线留下空城，右方必胜。每个分界只需常数次比较。''',
    r'''先看为什么“只比较初始两边兵力总和”不够。[3,3 | 2,4] 中两边各六，左方却能先用前线三攻占二，变成左方八、右方四；右方前线四打不过合并后的五，左方可保住优势，最终胜。初始相等不一定就是右方胜。

关键策略是当前轮到的一方如何保全总兵力。把前线部队向己方后方相邻城市移动并汇合，前线只留下零兵空城。对手一回合最多向前攻占一城，追不上每回合后撤一城的主力；撤到最远端时己方兵力已全部汇合。若左方总数大于右方，它最终能严格压过对方任一部队；右方则只需不小于。之后逐城反攻即可。因此，轮到左方且 L>R 时左胜；轮到右方且 R≥L 时右胜。

现在轮到初始左方，若 L≤R，转移或跳过都不改变两边总数，右方下一回合就能采用上述保全策略获胜。唯一可能改变结果的是立刻攻占右边第一城。记左前线 a、右第一城 b、右第二城 c（不存在视为零）。必须 a>b 才能发动；发动后总数变成 L+b、R−b，左方前线部队变成 a+b。

此时轮到右方。若 R−b≥L+b，它仍有总量优势，右胜。否则右方只有立即反攻才可能改变败局：若 c≥a+b，它可吞掉合并前线。左方被夺回后，原来前线位置已经在首次攻占时清空，当前最前城兵力为零，无法立即再攻占；两边总量成为 L−a 与 R+a，而初始 L≤R，右方显然占优。右方下一回合即可保全取胜。若 c<a+b，则右方不能反击，其它行动又无法阻止已反超的左方在下一回合保全，故左胜。

例如 [4,3 | 2,5] 初始也相等，左方攻占后前线为五，但右方下一城也是五，允许相等的右方能反击，所以这次是右胜。严格与非严格比较不可互换。用前缀和得到每个分界的 L、R，再执行以上三个条件；不实际模拟每一回合，也不修改初始数组。''',
    r'''int tests;cin>>tests;while(tests--){int n;cin>>n;vector<long long>a(n+2),prefix(n+1);
    for(int i=1;i<=n;++i){cin>>a[i];prefix[i]=prefix[i-1]+a[i];}
    string answer;
    for(int m=1;m<n;++m){long long left=prefix[m],right=prefix[n]-left;
        bool win=left>right;
        if(!win&&a[m]>a[m+1]&&left+a[m+1]>right-a[m+1]&&a[m]+a[m+1]>a[m+2])win=true;
        answer.push_back(win?'1':'0');
    }
    cout<<answer<<'\n';
}''',
    '优势策略只在轮到自己时成立；左攻占严格大于，右反击包含等号；第一次攻占后原前线是空城。',
    '每组时间、空间均为 $O(n)$。',tags=['博弈论','前缀和'],lessons=P+['games'])

add('UVA1210','筛出素数后预统计全部连续素数段',
    '对二到一万之间的整数，求它能写成多少种一个或多个连续素数的和；输入零结束。',
    r'''筛出不超过一万的完整素数表。枚举一段的起始素数，依次向右累加，和不超过一万时给该和值的方案数加一，超过就停止。预处理后每个询问直接查表。''',
    r'''四十一有三种表示：2+3+5+7+11+13、11+13+17，以及单独的四十一。连续指素数表中的相邻项，7+13 跳过十一，不算合法；同一素数也不能反复取。

先用埃氏筛求完整素数表。对每个尚未标记的 p，从 p² 起按步长 p 标记合数；更小的倍数已被更小质因子处理。零和一不是素数。只取到一万即可，因为任何合法段的各项都为正，超过一万的素数不可能参与和值不超过一万的段。

固定左端点 l，令 sum 从零起，依次加入 primes[r]，每个不超过上限的和值都对应唯一的连续段，ways[sum] 加一。素数全为正，若和超过上限，再扩展只会更大，可以立即 break。所有段按唯一左右端点枚举一次，没有重计。

输入询问数未给固定上界，预统计使之后每次只查数组。不要为终止零输出答案，也不要遗漏单个素数形成的长度一段。官方完整题面与样例：[UVa 1210 PDF](https://onlinejudge.org/external/12/1210.pdf)。''',
    r'''const int LIMIT=10000;vector<bool>prime(LIMIT+1,true);prime[0]=prime[1]=false;
for(int p=2;p*p<=LIMIT;++p)if(prime[p])for(int multiple=p*p;multiple<=LIMIT;multiple+=p)prime[multiple]=false;
vector<int>primes,ways(LIMIT+1);for(int x=2;x<=LIMIT;++x)if(prime[x])primes.push_back(x);
for(int l=0;l<(int)primes.size();++l){int sum=0;for(int r=l;r<(int)primes.size();++r){sum+=primes[r];if(sum>LIMIT)break;++ways[sum];}}
int n;while(cin>>n&&n!=0)cout<<ways[n]<<'\n';''',
    '素数必须在完整素数表中连续；一个素数也算一段；零是终止符。',
    r'上限 M、素数个数 P、询问数 T 下，时间上界 $O(M\log\log M+P^2+T)$、空间 $O(M)$。',
    tags=['素数','枚举'],lessons=A+['number-theory','prime-sieve','enumeration'],exact=True)
