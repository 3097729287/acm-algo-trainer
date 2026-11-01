"""Resource meanings, finite copies, signed sums and FIFO deletion plans."""
import json
from core7_authoring import add,SPECS,CONTENT,Method

A=['io-basics','basic-control','vector','integer','functions']
D=A+['dp','knapsack']


def retained_method(pid,title,meaning,brief,detail,pitfalls,complexity,lessons):
    old=json.loads((CONTENT/pid/'retained.json').read_text('utf-8'))
    SPECS.append(Method(pid,'reference',title,meaning,brief,detail,old['referenceProgram'],
                        pitfalls,complexity,['背包 DP'],lessons,images=old['solutions']['images'].copy()))


retained_method('P1048','把每株草药作为只能取一次的物品',
    '总时间T以内采药，每株耗时和价值已知，每株最多采一次，求最大总价值。',
    r'''dp[c]表示时间上限为c时的最大价值，初始为零。读入耗时t、价值v的草药后，时间c从T倒序到t，比较不采的dp[c]与采它的dp[c-t]+v。倒序保证所读的较小时间尚未加入这株草药；答案为dp[T]，不要求把时间用完。''',
    r'''若只有一株耗时二、价值三的草药，总时间四，最多仍只能得到三。若时间正序更新，先得到dp[2]=3，再用它更新dp[4]=6，相当于重复采了同一株。

令 $f_i(c)$ 表示只考虑前i株、总耗时不超过c的最大价值。最优方案分为不采第i株，以及采它两种；后一种去掉它后，剩余耗时不超过c-t，所以

$$f_i(c)=\max(f_{i-1}(c),f_{i-1}(c-t)+v).$$

时间不足t时只能不采。两类方案覆盖全部可能，并且每个候选都能实际采到，所以比较它们即可。

压成一维后，让c从大到小枚举。更新c时，c-t较小，还没被当前草药更新，仍代表上一层；于是每株最多使用一次。全部状态初始为零，表示一个草药也不采，这与“时间上限”相符。若题目要求恰好用完，才需要把非零耗时初始设为不可达。

T最多一千、草药最多一百，直接扫描所有时间上限足够。''',
    '每株只能采一次，时间倒序；时间不必用满；容量状态保存最优价值，不保存剩余时间；最终读取T。',
    r'时间 $O(MT)$，空间 $O(T)$。',D)

retained_method('P2392','每科独立分给两脑，找最接近一半的可达耗时',
    '四科必须逐科完成，同一科内两脑可同时做不同题，一道题不能拆开，求四科合计最短时间。',
    r'''每科总耗时为S。若分给一脑的题目耗时x不超过S的一半，另一脑需S-x，完成时间就是S-x。因此用零一背包求不超过S/2的最大可达和best，本科最短时间为S-best；四科分别求解后相加。''',
    r'''一科三道题都需三分钟，总共九分钟，但两脑不能把一道题拆成一半。只能分成三和六，本科用六分钟，不能把九直接除二取整得到五。

把一科所有题的总耗时记为S，分给左脑的题目耗时为x，右脑为S-x。两脑并行，完成这科需要两者的较大值。交换左右不改变完成时间，所以只考虑 $x\le\lfloor S/2\rfloor$，此时较慢的一边用S-x；要让它最小，就让x尽可能大。

令dp[c]为容量上限c以内、可由已处理题目凑出的最大耗时。每题的“重量”和“价值”都等于该题时间，按容量倒序做零一背包。dp[H]便是最接近但不超过一半的子集和，另一脑取得剩余题，得到合法的S-dp[H]。

四科不能交错做，故总时间是四个独立最优时间之和。各科重新建立数组，不能把上一科剩余的题目组合接到下一科。程序中的array保存恰好四个题数，其元素会由输入逐个写入；后面的vector才是按每科总时间建立的背包表。

输入先给四科各自的题数，再逐科给出每题时间；程序按这个顺序独立计算。''',
    '一道题不可拆；两脑同时做同科；四科时间相加；每科重新初始化；不能直接用总时间除二。',
    r'第s科有 $n_s$ 题、总时间 $S_s$，时间 $O(\sum_s n_sS_s)$，额外空间 $O(\max_s S_s)$。',D+['standard-array'])

add('P1679','把正整数的四次方作为无限使用的面额',
    '把正整数m写成若干个正整数四次方的和，求最少项数。相同的四次方可以重复出现。',
    r'''先列出不大于m的所有正整数四次方。令dp[s]为凑成s的最少项数，dp[0]=0；按s递增，枚举最后一个四次方v，用dp[s-v]+1更新。每次转移的和都变小，且一的四次方保证有解。''',
    r'''十七可以写成十六加一，即二的四次方加一的四次方，只用两项；不能把“底数只能取一次”当作限制。例如三只能由三个一组成。

设最优表示的最后一项为v，去掉它后剩下s-v。剩余部分也必须用最少项数，否则替换它便能减少原方案的项数。因此比较所有 $v=i^4\le s$：

$$dp[s]=\min_{i^4\le s}(dp[s-i^4]+1).$$

反过来，每个候选都可在s-v的合法表示后加一项v，故不会产生不存在的方案。所有v为正，s-v严格更小，按和递增即可。初始零用零项，其它状态先设为较大值。

只生成v不超过m的底数即可。m至多十万，候选四次方很少；程序用long long计算底数的四次方，避免乘法在生成边界附近产生类型问题。''',
    r'''int m; cin>>m;
vector<int> power;
for(long long i=1;i*i*i*i<=m;++i) power.push_back(i*i*i*i);
vector<int> dp(m+1,m+1); dp[0]=0;
// 枚举最后一项，所依赖的更小和已经算好。
for(int sum=1;sum<=m;++sum){
    for(int v:power){
        if(v>sum) break;
        dp[sum]=min(dp[sum],dp[sum-v]+1);
    }
}
cout<<dp[m]<<'\n';''',
    '四次方可重复；底数为正；零的初值是零项；必须恰好得到m；生成乘积使用足够宽的类型。',
    r'时间 $O(m\sqrt[4]{m})$，空间 $O(m)$。',tags=['背包 DP'],lessons=D)

add('P1855','同时保留金钱与时间两种容量',
    '每个愿望分别消耗金钱和时间，每个最多实现一次，两个总额都不能超出，求最多愿望数。',
    r'''dp[m][t]表示金钱上限m、时间上限t内能实现的最多愿望数。每个愿望收益为一，分别在金钱和时间上倒序，比较不选与dp[m-cost][t-duration]+1。所有容量初始为零，答案取全部预算处。''',
    r'''金钱与时间不能合成一种资源。一个愿望很便宜却很耗时，另一个很快却昂贵，它们能否同时实现取决于两条限制都满足。

处理完前i个愿望，令 $f_i(m,t)$ 表示两种预算上限分别为m、t时的最大数量。不选第i个愿望保留旧状态；选它则先从两种预算各扣去对应消耗，再给愿望数加一。

把层数压掉后，两种容量均倒序枚举，保证读取的是未包含当前愿望的方案。某一消耗为零也适用：若金钱为零而时间为正，时间倒序防止重复；若两种消耗都为零，每个格子仍只更新一次，恰好加一，不会无限增加。

初始全部为零，允许不实现任何愿望；不要求金钱或时间正好耗尽。n最多一百、两种预算至多二百，二维容量表足够。''',
    r'''int n,m,t; cin>>n>>m>>t;
vector<vector<int>> dp(m+1,vector<int>(t+1));
for(int i=0,cost,duration;i<n;++i){
    cin>>cost>>duration;
    // 两种容量都倒序；即便两种消耗都是零，每格也只加一次。
    for(int money=m;money>=cost;--money){
        for(int time=t;time>=duration;--time){
            dp[money][time]=max(dp[money][time],dp[money-cost][time-duration]+1);
        }
    }
}
cout<<dp[m][t]<<'\n';''',
    '金钱与时间分别限制；两个容量均倒序；每个愿望收益为一；零费用愿望仍只能处理一次；允许剩余预算。',
    r'时间 $O(nMT)$，空间 $O(MT)$。',tags=['背包 DP'],lessons=D)

add('P2639','记录每个草料总重能否由若干捆恰好组成',
    '每捆草料最多取一次，背包最多装H，求不超过H的最大总重量。相同重量的不同捆仍可各取一次。',
    r'''reachable[s]记录能否恰好组成总重s，只把零初始化为真。每读一捆重量w，从H倒序到w，把reachable[s-w]合入reachable[s]。最后从H向零找第一个可达值。''',
    r'''容量十，只有一捆重六，即使还剩四也不能把这捆拆开或再拿一次。若有两捆重五，则可以各拿一捆装满；不要把相同重量去重。

对当前捆，凑成s的方案要么不拿它，要么从此前的s-w补上它。因此只需保存每个精确总重是否可达。初始仅零可达，表示空集合；其它重量不能凭空出现。

总重倒序时，读取的s-w尚未被当前捆修改，所以每捆至多一次。处理完全部捆后，所有合法总重都已记录，向下扫描第一个可达值就是最大不超容量的装法。

H最多四万五千、捆数最多五百，按数值容量递推可以通过；不需要穷举所有捆的子集。''',
    r'''int h,n; cin>>h>>n;
vector<char> reachable(h+1); reachable[0]=true;
for(int i=0,w;i<n;++i){
    cin>>w;
    // 倒序读取未使用当前捆的旧状态。
    for(int sum=h;sum>=w;--sum){
        if(reachable[sum-w]) reachable[sum]=true;
    }
}
for(int sum=h;sum>=0;--sum){
    if(reachable[sum]){cout<<sum<<'\n';break;}
}''',
    '每捆一次；同重不去重；只初始化总重零；不要求装满；总重倒序。',
    r'时间 $O(NH)$，空间 $O(H)$。',tags=['背包 DP'],lessons=D)

add('P11246','以最后一项平方数递推最少项数',
    '将n表示成若干正整数平方的和，求最少平方数个数，同一个平方数可以使用多次。',
    r'''令dp[s]表示恰好组成s的最少项数，dp[0]=0。按s递增，枚举所有j²不超过s，以dp[s-j²]+1更新。平方数可以重复，因为更小和的状态不限制已经使用过哪些底数。''',
    r'''十二若先取最大平方九，再补三个一，需要四项；实际上四加四加四只需三项。因此不能每次贪心减去最大的平方。

任意非空表示都有最后一个平方数j²。去掉它后是s-j²的表示；若剩余部分不是最少项数，可替换得到更好的原方案。反之，给任意更小和的最优表示补上j²都合法，所以

$$dp[s]=\min_{1\le j^2\le s}(dp[s-j^2]+1).$$

所有平方数为正，依赖项已在较小s处算好。初始dp[0]=0，且一可重复使用，保证每个正整数都有有限答案。

n至多十万，所有状态合计需要 $O(n\sqrt n)$ 次平方枚举；无需引入更难证明的数论分类。''',
    r'''int n; cin>>n;
vector<int> dp(n+1,n+1); dp[0]=0;
for(int sum=1;sum<=n;++sum){
    // 不限制旧状态用过什么底数，因此同一平方可重复。
    for(int j=1;j*j<=sum;++j) dp[sum]=min(dp[sum],dp[sum-j*j]+1);
}
cout<<dp[n]<<'\n';''',
    '目标是最少项数；允许重复平方；不能贪心拿大平方；只枚举正底数；dp[0]为零。',
    r'时间 $O(n\sqrt n)$，空间 $O(n)$。',tags=['背包 DP'],lessons=D)

add('B3873','把超过需求的总容量统一合并到达标状态',
    '每种饮料最多买一瓶，购买容量至少L，求最少费用；无法达标输出no solution。',
    r'''dp[v]为已买容量压到min(实际容量,L)后，达到该状态的最少费用。初始dp[0]=0，其它不可达。每瓶用独立新数组，保留不买，并把旧v转到min(L,v+容量)，费用加售价。最终dp[L]就是所有达标方案的最小费用。''',
    r'''需要一百毫升时，一瓶一百一十毫升也合法，不能只接受恰好一百。另一方面，容量可大到一百万，按所有瓶容量之和开数组没有必要。

把状态v小于L解释为精确容量；状态L解释为已经达到或超过L。达到L以后，再多的容量对是否满足要求没有区别，所以可以合并；在相同状态下，只保留更低费用，未来购买相同饮料时不会更差。

每瓶分成不买、买两种。新数组先复制旧数组保存不买，买时从旧v转到 $\min(L,v+l_i)$，费用加c_i。这次转移只读取旧数组，保证每种最多一瓶，也避免在饱和的L状态上反复使用同瓶。

初始只有容量零、费用零，其余为无穷。处理完所有种类后，L状态不可达便按原格式输出no solution，否则输出其最小费用。费用和用long long保存。''',
    r'''int n,l; cin>>n>>l;
const long long INF=LLONG_MAX/4;
vector<long long> dp(l+1,INF); dp[0]=0;
for(int i=0,cost,volume;i<n;++i){
    cin>>cost>>volume;
    auto next=dp; // 先保留不买，只读取未含本瓶的旧数组。
    for(int v=0;v<=l;++v){
        if(dp[v]==INF) continue;
        int to=min(l,v+volume); // 所有已达标容量合并。
        next[to]=min(next[to],dp[v]+cost);
    }
    dp.swap(next);
}
if(dp[l]==INF) cout<<"no solution\n";
else cout<<dp[l]<<'\n';''',
    '至少L而非恰好L；容量超过需求后合并；每瓶读旧数组；不可达不能参与加法；无解输出小写及中间空格。',
    r'时间 $O(NL)$，空间 $O(L)$。',tags=['背包 DP'],lessons=D)

add('P1466','先统计和为总和一半的子集，再消除左右对称',
    '把一到N分成两个和相等、互不相交且覆盖全部数的集合，两个集合交换顺序不算新方案。',
    r'''总和S为奇数时无解。否则用零一计数背包统计和为S/2的子集数：dp[0]=1，各数处理时总和倒序累加dp[s-x]。每个这样的子集唯一确定补集，一组无序划分被两侧各统计一次，故最后除以二。''',
    r'''N为三时，选子集{1,2}与选子集{3}都得到和三，但它们代表同一组划分，答案是一而不是二。

总和为 $S=N(N+1)/2$，两边相等必须各为S/2。如果S是奇数，立即输出零；否则只需数有哪些子集精确达到这个和。

令dp[s]为用已处理整数凑成s的子集数。初始dp[0]=1，对应一个空子集。处理数x时，每个包含x的新子集唯一对应一个此前和为s-x的子集；加上不含x的旧方案，容量倒序累加，保证每个整数只使用一次。

一个和为S/2的子集与它的补集配成一组，交换两个集合不会改变划分。N为正，子集不可能等于自己的补集，因此每组恰好被数两次，最后做整数除二。

计数不用取模，使用long long。N最多三十九，所有子集总数为二的三十九次方，足以保证计数落在六十四位有符号整数范围内。''',
    r'''int n; cin>>n;
int total=n*(n+1)/2;
if(total%2){cout<<0<<'\n';return 0;}
int target=total/2;
vector<long long> dp(target+1); dp[0]=1;
for(int x=1;x<=n;++x){
    for(int sum=target;sum>=x;--sum) dp[sum]+=dp[sum-x];
}
// 每个无序划分由两个互补子集各计数一次。
cout<<dp[target]/2<<'\n';''',
    '总和奇数无解；每个整数一次；dp[0]为一种；两个集合无序；最后除二而非取模逆元；计数六十四位。',
    r'时间 $O(N^3)$，空间 $O(N^2)$，因为目标和为 $O(N^2)$。',tags=['背包 DP','组合计数'],lessons=D+['counting'])

add('P2170','把整个朋友连通块作为一件物品，合并同大小块',
    '朋友关系经传递后必须同选或同不选。选出人数尽量接近m，差相同时选人数较少的方案。',
    r'''先用并查集求每个连通块的人数。每块不可拆，做子集和。为加速，同大小块计数后拆成一、二、四等批次及剩余批次，每批作为零一物品。得到所有可达人数后从小到大扫描，仅在误差严格变小时改答案，自然保留较少人数。''',
    r'''三个人形成一个朋友连通块，即使目标为二，也不能单独选其中两人。先把所有直接或间接相连的人压成一个整体，其人数就是这件物品的重量。

若直接逐块做背包，最坏有两万个单人块。注意相同大小的块在“可达人数”上没有区别：若大小s出现c次，只需能选择零到c个这样的块。

将c拆成一、二、四等批次，最后不足下一批的部分单独一批。例如十三拆成一、二、四、六；这些批次数的子集可以覆盖零到十三的全部数量，且总数恰为十三，不会超选。把每批人数作为一件只能取一次的物品，倒序更新可达总人数。

这种合并只用于可达性；不同批次可能表达同样的块数，所以不能直接拿它统计具体选人方案数。这里仅求人数，完全足够。

得到所有可达人数后，按零到n扫描。只有绝对差严格更小时才替换；相同差时已经保存的数更小，满足原题的平局规则。目标为零、所有人一个块、没有朋友边都由同一流程处理。''',
    r'''int n,target,k; cin>>n>>target>>k;
vector<int> parent(n),size(n,1); iota(parent.begin(),parent.end(),0);
auto find=[&](int x){
    while(parent[x]!=x){parent[x]=parent[parent[x]];x=parent[x];}
    return x;
};
for(int i=0,u,v;i<k;++i){
    cin>>u>>v; u=find(u-1); v=find(v-1);
    if(u==v) continue;
    if(size[u]<size[v]) swap(u,v);
    parent[v]=u; size[u]+=size[v];
}
vector<int> frequency(n+1);
for(int i=0;i<n;++i) if(find(i)==i) ++frequency[size[i]];
vector<char> reachable(n+1); reachable[0]=true;
for(int s=1;s<=n;++s){
    int left=frequency[s];
    // 同大小的连通块拆成若干整批，覆盖零到原数量。
    for(int batch=1;left;batch*=2){
        int count=min(batch,left); left-=count;
        int weight=s*count;
        for(int sum=n;sum>=weight;--sum){
            if(reachable[sum-weight]) reachable[sum]=true;
        }
    }
}
int answer=0;
for(int sum=1;sum<=n;++sum){
    // 只在严格更近时更新，平局留下先遇到的较小人数。
    if(reachable[sum]&&abs(sum-target)<abs(answer-target)) answer=sum;
}
cout<<answer<<'\n';''',
    '连通块整体选择；同大小块先计数；二进制批次只用于可达性；误差相同时取小人数；零人数也是候选。',
    r'拆出的批次数为B，时间 $O((n+k)\alpha(n)+nB)$，空间 $O(n)$；$B=\sum_{s:c_s>0}O(\log(c_s+1))$。',tags=['背包 DP','并查集'],lessons=D+['dsu','lambda-local'])

add('P2725','逐个检查邮资，停在第一个超过张数限制的金额',
    '每种邮票无限张，每个邮资最多使用k张，求从一开始能连续组成的最大邮资终点。',
    r'''求dp[s]：组成邮资s的最少邮票数。枚举最后一张的面额，以dp[s-v]+1更新。按金额从一递增，首次最少张数超过k时，连续区间便在s-1结束；不是取所有可达金额里的最大值。上界为k乘最大面额。''',
    r'''面额一与三，最多两张时，一、二、三、四都能组成，五需要三张，虽然六可以用两个三组成，连续答案仍只有四。

一种邮资能用不超过k张组成，当且仅当它的最少张数不超过k。对s枚举最后一张面额v，剩下的s-v已经处理，故可以按金额递增求最少张数。

数组中把超过k的张数统一记为k+1即可。因为继续加邮票只会增加张数，区分更大的值对判断是否合法没有帮助。dp[0]=0，其余初始k+1。

在求出每个正金额后立即检查。第一个失败的金额s是连续覆盖的缺口，后面即使有可达金额也不能越过它，直接返回s-1。任意k张的总面额不超过k乘最大面额，因此枚举到这个界限足够；若此前都没有缺口，输出界限本身。

面额排序后，当前面额大于s就结束内层枚举。面额重复不影响最小值，不必为重复值引入不同含义。''',
    r'''int k,n; cin>>k>>n;
vector<int> coin(n); for(int &x:coin) cin>>x;
sort(coin.begin(),coin.end());
int bound=k*coin.back();
vector<int> dp(bound+1,k+1); dp[0]=0;
for(int sum=1;sum<=bound;++sum){
    for(int v:coin){
        if(v>sum) break;
        dp[sum]=min(dp[sum],dp[sum-v]+1);
    }
    // 连续覆盖不能跨过缺口，立即结束。
    if(dp[sum]>k){cout<<sum-1<<'\n';return 0;}
}
cout<<bound<<'\n';''',
    '每种无限张；限制总张数；求连续前缀而非最大可达数；缺少面额一时答案零；不能越过第一个缺口。',
    r'上界 $U=k\max(v)$，最坏时间 $O(nU+n\log n)$，空间 $O(U)$。',tags=['背包 DP'],lessons=D+['sort'])

add('P5365','以费用为容量，分英雄比较能得到的展示策略数',
    '第i个英雄最多买Ki款皮肤，每款同价Ci；没买的英雄不参与乘积，求展示策略至少M种时的最少费用。',
    r'''先按输入顺序给若干英雄买齐皮肤，直到策略乘积达到M，得到一个可行费用上界B。再用分组背包，dp[c]为精确费用c下的最大策略数，乘积达到M即截为M。每个英雄买零款，或买二到Ki款，从旧数组转移；买一款只花钱而不增乘积，可以舍去。最终取dp[c]达到M的最小费用。''',
    r'''某英雄买零款不参与展示，乘积因子应是一，不能变为零；买一款同样只有一种选择，却花正费用，所以永远不会优于不买。目标为一种策略时，什么都不买即可。

M可到十的十七次方，不能按策略数开数组。费用相对小得多：先沿输入顺序给Ki大于一的英雄买齐，乘积不断扩大，首次达到M时累计费用为B。它只是一个可行方案，作用是证明最优费用不超过B；不能把这个购买顺序当作最优贪心。

每次参与上界构造的英雄至少让乘积翻倍，且每个英雄买齐至多花十乘一百九十九。二的五十七次方已经超过目标上限，所以最多使用五十七个这样的英雄，上界B不会超过十一万三千四百三十；实际构造通常更小。

令dp[c]为处理完此前英雄、恰好花c费用的最大展示策略数。空购买的乘积为一，故dp[0]=1；其余费用初始零，表示不可达。处理一个英雄时，选择零款就保留旧值；选择x款，范围二到Ki，费用增加xCi，策略数乘x。

所有方案只关心乘积是否达到M，所以超过M后统一截为M。同样费用下，更大的乘积以后不会更差，保留最大值足够。每轮读旧数组，确保同一英雄只选一种购买数量。

求上界时用到的英雄只是前缀，背包仍须处理全部英雄，后面可能更便宜。每次相乘以前的数最多M、因子最多十，中间值不超过十的十八次方，用long long足够。''',
    r'''int n; long long target; cin>>n>>target;
vector<int> k(n),cost(n);
for(int &x:k) cin>>x;
for(int &x:cost) cin>>x;
if(target<=1){cout<<0<<'\n';return 0;}
// 先取得可行费用上界，随后仍对全部英雄做最优化。
int bound=0; long long product=1;
for(int i=0;i<n&&product<target;++i){
    if(k[i]>1){bound+=k[i]*cost[i];product=min(target,product*k[i]);}
}
vector<long long> dp(bound+1); dp[0]=1;
for(int i=0;i<n;++i){
    auto next=dp; // 不买；购买一款被不买支配。
    for(int used=0;used<=bound;++used){
        if(!dp[used]) continue;
        for(int buy=2;buy<=k[i]&&used+buy*cost[i]<=bound;++buy){
            int to=used+buy*cost[i];
            next[to]=max(next[to],min(target,dp[used]*buy));
        }
    }
    dp.swap(next);
}
for(int used=0;used<=bound;++used){
    if(dp[used]>=target){cout<<used<<'\n';break;}
}''',
    '不买的乘积因子是一；买一款被不买支配；上界方案不是最优贪心；仍处理全部英雄；乘积截断在目标。',
    r'令可行费用上界为B、最大皮肤数为K，时间 $O(NBK)$，空间 $O(B)$。',tags=['背包 DP'],lessons=D)

add('P14920','交换背包维度，保存每个攻击力所需的最少金币',
    '每件道具最多买一次，预算可能很大，但单件攻击力至多五百，求能购买到的最大总攻击力。',
    r'''所有道具攻击力之和至多二十五万，改为dp[a]表示恰好增加a攻击力的最少费用。dp[0]=0，其它无穷；每件道具按攻击力倒序，用dp[a-增益]+价格更新。最后从大到小找费用不超过预算的攻击力。''',
    r'''金币上限可达十亿，按金币开表不可行。道具最多五百件，每件攻击力最多五百，全部买下也只增加二十五万点；把更小的总攻击力放到数组下标。

令dp[s]为恰好取得s攻击力的最少费用。若两个选择得到同样攻击力，费用更低的那个在未来永远不差，只保留它即可。每件增益a、价格c的道具，要么不买保留旧状态，要么由旧s-a补上它，候选费用dp[s-a]+c。

攻击力倒序更新，保证每件只买一次。不可达状态不能参与加法，初始只有零攻击力、零费用。处理若干件后，不必扫描超过它们攻击力总和的下标，代码用used限定本轮范围。

最后从总攻击力向零扫描，首个最少费用不超过预算的状态就是答案。这里求的是精确攻击力的最小费用，不能把各项初始都设为零。累计费用最多五百乘十亿，用long long保存。''',
    r'''int n; long long budget; cin>>n>>budget;
vector<int> attack(n); vector<long long> cost(n); int total=0;
for(int i=0;i<n;++i){cin>>attack[i]>>cost[i];total+=attack[i];}
const long long INF=LLONG_MAX/4;
vector<long long> dp(total+1,INF); dp[0]=0; int used=0;
for(int i=0;i<n;++i){
    used+=attack[i]; // 本轮最多只能达到已读道具的总攻击力。
    for(int sum=used;sum>=attack[i];--sum){
        if(dp[sum-attack[i]]!=INF){
            dp[sum]=min(dp[sum],dp[sum-attack[i]]+cost[i]);
        }
    }
}
for(int sum=total;sum>=0;--sum){
    if(dp[sum]<=budget){cout<<sum<<'\n';break;}
}''',
    '金币大，换成总攻击力维度；状态是最少费用；非零攻击力初始不可达；每件一次；费用六十四位。',
    r'总攻击力为A，时间 $O(nA)$，空间 $O(A)$，且 $A\le250000$。',tags=['背包 DP'],lessons=D)

add('P1156','每个高度只保留最晚死亡时刻，按垃圾落下顺序处理',
    '初始能活十个时间单位，每件垃圾可吃掉延长生命或垫高；求最早出井时刻，若不能出井，求最长存活时长。',
    r'''把垃圾按落下时刻排序。dp[h]为达到高度h时最晚的死亡时刻，初始dp[0]=10。只有dp[h]不早于当前时刻的状态能使用垃圾：吃掉使死亡时刻加食物值，垫高则提高高度而保持死亡时刻。每件读旧数组；首次可垫到井口便返回当前时刻。最终无法出井时，dp[0]是只吃不垫的最长生命。''',
    r'''第十时刻落下一件食物时，初始生命刚好耗尽，题目仍允许立刻吃掉它；可用条件是死亡时刻不小于落下时刻，不能写成严格大于。

同样高度下，死得更晚的状态能完成较早死亡状态以后的一切动作，所以只保留最晚死亡时刻，不必再展开一维生命值。dp保存的是绝对时刻，例如死亡时刻十、当前时刻七表示还能活三，并不是还剩十。

按事件时刻排序后，对当前垃圾有三种选择：忽略，保留原值；吃掉，保持高度而把死亡时刻加食物值；垫在脚下，高度加垃圾高度而死亡时刻不变。后两种都要求旧死亡时刻至少为当前时刻。独立的新数组保证一件垃圾不能既吃又垫，也不能垫多次。

事件按时间递增，第一次能达到井深D时，就是最早出井时刻。达到D及以上都直接成功，不需要把越界高度存进表。同一时刻的垃圾依次处理也合法，各动作不耗额外时间。

若始终不能逃出，只求活多久，垫高没有生命收益；把原方案中每次垫高都改成吃掉，生命只会更多，原本可用的后续垃圾仍可用。因此最长存活由高度零的“全部可吃便吃”状态给出。''',
    r'''int depth,n; cin>>depth>>n;
struct Trash{int time,food,height;};
vector<Trash> a(n);
for(auto &x:a) cin>>x.time>>x.food>>x.height;
sort(a.begin(),a.end(),[](const Trash &x,const Trash &y){return x.time<y.time;});
vector<int> dp(depth,-1); dp[0]=10;
for(auto x:a){
    auto next=dp;
    for(int h=0;h<depth;++h){
        if(dp[h]<x.time) continue; // 刚好等于落下时刻仍然能使用。
        if(h+x.height>=depth){cout<<x.time<<'\n';return 0;}
        next[h]=max(next[h],dp[h]+x.food); // 吃：只延长生命。
        next[h+x.height]=max(next[h+x.height],dp[h]); // 垫：只增加高度。
    }
    dp.swap(next);
}
cout<<dp[0]<<'\n';''',
    '死亡时刻等于事件时刻仍可操作；吃与垫只能选一；输入先排序；到达或超过井口即成功；失败输出存活时长。',
    r'时间 $O(G\log G+GD)$，空间 $O(G+D)$。',tags=['背包 DP'],lessons=D+['sort','structures','lambda-local'])

add('P1776','把每类有限件数拆成若干只能取一次的整批',
    '每种宝物有有限件数，单件重量和价值固定，车载重不超过W，求最大总价值。',
    r'''每种最多能装W/重量件，先把件数截到这个上限，再拆成一、二、四等批及最后剩余批。整批的重量和价值都乘批内件数，对每批做容量倒序的零一背包。批次数只随件数的对数增长。''',
    r'''十三件相同宝物可拆成一、二、四、六件四批。前面三批能表示零到七件，加最后六件得到六到十三，两段有重叠但没有缺口，恰好覆盖所有允许数量。

一般地，若之前的批次可以组成零到R件，新批不超过R+1，就能组成零到R加新批的全部数量。按一、二、四翻倍拆，最后一批取余数，始终满足这个条件；所有批次件数之和等于原上限，因此不会超选。

一批要么整批选、要么不选，变成零一物品，批重量为单重乘件数、批价值为单价乘件数。对每批按载重倒序更新最大价值，避免一批反复加入。容量初始为零，表示允许空装且不用装满。

原件数很大时，超过W除以单重的部分再多也装不下，可以先截掉；单重超过W的种类直接没有可选批次。W为零时也输出零。总价值使用long long。''',
    r'''int n,capacity; cin>>n>>capacity;
vector<long long> dp(capacity+1);
for(int i=0,value,weight,count;i<n;++i){
    cin>>value>>weight>>count;
    count=min(count,capacity/weight); // 装不下的多余件数无需拆分。
    for(int batch=1;count;batch*=2){
        int copies=min(batch,count); count-=copies;
        int w=weight*copies;
        long long v=1LL*value*copies;
        for(int c=capacity;c>=w;--c) dp[c]=max(dp[c],dp[c-w]+v);
    }
}
cout<<dp[capacity]<<'\n';''',
    '有限件数先截容量上限；最后余数也要成一批；整批重量价值均乘件数；批次倒序；允许不装满。',
    r'截断后的件数为 $m_i$，时间 $O(W\sum_i\log(m_i+1))$，空间 $O(W)$。',tags=['背包 DP'],lessons=D)

add('P4912','状态同时记最后一种魔法与带符号的总咒语长度',
    '每种魔法至多一次且使用编号严格递增，后一种威力还受紧邻的前一种影响；咒语长度可为负，求总长为m的最大威力。',
    r'''dp[i][s]表示最后施放i、总长度恰为s的最大威力。先放入单独施放i的状态；再枚举更早的最后魔法j，从dp[j][s-a[i]]加b[i]+w[j][i]。按最后编号递增计算，不依赖长度正负。长度范围取负五十n到正五十n，统一偏移下标。''',
    r'''只记总长度不够：以不同魔法结尾，接同一种新魔法时的附加威力可能不同，当前分数较低的结尾也可能在下一步反超。因此需要保留“最后施放哪一种”。

编号不下降且同种不可重复，实际施放编号严格递增。把最后编号i作为计算顺序，就不存在循环，即便咒语长度为零或负数，也能由更早的编号转移。

令 $f_i(s)$ 表示至少施放一种、最后为i且总长度精确为s的最大威力。仅施放i时，总长a_i、威力b_i，不加任何前驱影响。若此前最后为j且j小于i，则

$$f_i(s)=\max_{j<i}\bigl(f_j(s-a_i)+b_i+w_{j,i}\bigr),$$

同时保留单个魔法的候选。只有紧挨着的j影响i，不把更早魔法对i的影响全部累加。

总长可能先超过m再用负长度降回，也可能先负后正，不能把状态裁成零到m。每个长度绝对值至多五十、最多n种，整个合法范围包含在负五十n到正五十n之间，存储时加统一偏移。

原题输入将目标m写为正整数；算法的状态仍须容纳中途负长度。最后在所有结尾的目标长度状态中取最大值，全部不可达才输出负一。合法最大威力本身可以是负数，不能把不可达与负分混为一谈。''',
    r'''int n,target; cin>>n>>target;
vector<int> a(n),b(n);
for(int i=0;i<n;++i) cin>>a[i]>>b[i];
vector<vector<int>> w(n,vector<int>(n));
for(auto &row:w) for(int &x:row) cin>>x;
int bound=50*n,span=2*bound+1;
const int NEG=-1000000000;
vector<vector<int>> dp(n,vector<int>(span,NEG)); int answer=NEG;
for(int i=0;i<n;++i){
    dp[i][a[i]+bound]=b[i]; // 只用一个魔法，没有前驱影响。
    for(int j=0;j<i;++j){
        for(int index=0;index<span;++index){
            if(dp[j][index]==NEG) continue;
            int to=index+a[i]; // 两边使用同一偏移，直接加本次长度。
            if(to>=0&&to<span){
                dp[i][to]=max(dp[i][to],dp[j][index]+b[i]+w[j][i]);
            }
        }
    }
    if(target>=-bound&&target<=bound) answer=max(answer,dp[i][target+bound]);
}
cout<<(answer==NEG?-1:answer)<<'\n';''',
    '编号严格递增；状态保留最后魔法；允许中途负长度；首个魔法没有附加值；只有相邻影响；合法负威力不是不可达。',
    r'长度范围宽度为 $O(nA)$、$A=50$，时间 $O(n^3A)$，空间 $O(n^2A)$。',tags=['背包 DP'],lessons=D)

add('P13018','把酸甜之差作为带正负的背包下标',
    '每种食材可放或不放，使总酸度等于总甜度，并最大化两者之和；空集合也满足平衡。',
    r'''每种食材贡献差a-b、收益a+b。dp[d]表示精确差为d的最大收益，初始只有dp[0]=0。每种食材从旧数组转移到差d+a-b，也保留不选；正负差统一加偏移。最终差零处即答案。''',
    r'''一份酸一甜二的食材差为负一，另一份酸二甜一差为正一，合起来差为零、总风味六。只保存非负差，会在第一步丢掉这个最优组合。

平衡等价于所选食材的酸甜差之和为零。令每种差值为d_i、收益为v_i，其中 $d_i=a_i-b_i$、$v_i=a_i+b_i$。相同差值下，收益更大的选择以后更优，因为再加同样食材，平衡关系相同。

以dp[d]保存精确差d的最大收益。每轮新数组先保留不选当前食材，再从旧d转到d+d_i，收益加v_i。差值可正、可负、也可零，采用独立新数组最直接，不必为不同符号猜原地循环方向。

所有可能差的绝对值不超过各食材绝对差之和S，存到下标d+S。初始仅差零可达、收益零；其余用负无穷。最终读取差零，既包含合法的非空配方，也包含什么都不放的零分方案。

每个酸甜值至多五百、n最多一百，S至多四万九千九百，范围足够小。''',
    r'''int n; cin>>n;
vector<int> difference(n),value(n); int bound=0;
for(int i=0,a,b;i<n;++i){
    cin>>a>>b; difference[i]=a-b; value[i]=a+b; bound+=abs(difference[i]);
}
const int NEG=-1000000000;
vector<int> dp(2*bound+1,NEG); dp[bound]=0; // 下标bound表示差零。
for(int i=0;i<n;++i){
    auto next=dp;
    for(int index=0;index<(int)dp.size();++index){
        if(dp[index]==NEG) continue;
        int to=index+difference[i];
        if(to>=0&&to<(int)dp.size()) next[to]=max(next[to],dp[index]+value[i]);
    }
    dp.swap(next); // 读旧数组，正差、负差都不会重复使用当前食材。
}
cout<<dp[bound]<<'\n';''',
    '平衡是差为零；收益是酸甜之和；负差必须保留；每轮读旧数组；零差食材也只选一次；空集合收益零。',
    r'$S=\sum_i|a_i-b_i|$，时间 $O(nS+n)$，空间 $O(S+n)$。',tags=['背包 DP'],lessons=D)

add('P11274','确定第一个最终保留的格子，倒序背包选择后缀',
    '从左到右选格子，每次选i先删掉已有队列最前面的至多bi个，再加入i。可有负分，须输出整段选择过程及最终最大得分。',
    r'''最终留下的是全部所选编号的一个后缀。若第一个最终保留格子为i，其后选中格子的删除数之和为W：W为零时可直接从i开始；W为正时，i之前必须能准备bi+W个待删除格子。先求每个前缀最多能留下的数量C，再从右到左用零一背包记录后缀“删除数和为W的最大得分”。在W=0或1≤W≤C[i-1]-bi的状态中选最优，并保存选择标记，恢复后缀及被删的前缀格子。''',
    r'''被删的格子也可能必须选，并且要写进输出过程。考虑得分为负九、五、六，删除数为零、零、一：依次选择三格，最后删除第一格，留下五加六得十一；若只输出最终两格，第三格会把第二格删掉，只剩六。

先观察队列：删除永远发生在最前面，所以最终剩下的格子一定是全部选择序列的一个后缀。若最早最终留下的是i，那么i之后选中的每个格子都必须留下；否则被删掉的更早格子i也已经被删，产生矛盾。

设i后选中格子的删除数之和为W。若W为零，可以什么前缀都不选，直接从i开始。若W大于零，这些删除操作不能碰到i，必须由i之前的旧格子承担；而这些旧格子最终又必须全被清掉。因此选i并完成它自己的删除后，队列中必须恰有W个旧格子。

当W大于零，选i之前的旧格子数量必为b_i+W；否则剩得少会删到i，剩得多则最终仍有更早格子。每次后缀删除都是非负的，任意前缀删除量不超过W，所以只要备足这W个旧格子，整个后续过程都不会删到i。

接下来求前缀能准备多少个旧格子。令C_i为前i格处理后能留在队列中的最大数量，C_0=0。忽略i保留C_{i-1}，选择i则先删至多b_i个，再加入自己：

$$C_i=\max\bigl(C_{i-1},\max(0,C_{i-1}-b_i)+1\bigr).$$

不仅最大数量可达，零到C_i的每个数量都可达。归纳看，忽略i保留旧区间；选择后的数量仍随旧数量单调连续变化，从一开始，并至多在旧最大值上增加一，因此合起来没有缺口。于是W为正的可行条件正是

$$1\le W\le C_{i-1}-b_i.$$

从右到左枚举i。在把i加入背包之前，dp[W]表示只在i后选择、删除数恰好为W的最大得分。把b作为重量、a作为价值，初始dp[0]=0，其余不可达。先用W为零及上述正W范围评估a_i+dp[W]，再将i作为零一物品按重量倒序加入。删除数为零时，每个状态也只更新一次，负分可以不选。

恢复方案需要保存take[i][W]：处理i时，最优状态是否通过选择i而严格改善。确定最优的首格与W后，从它的后一格向右查看标记，选了便从W扣去b_i，得到完整最终后缀。

若原W为正，还要在首格之前恢复恰好b_i+W个旧格子。倒着看前缀，当前需要q个：如果不选当前格也能达到q，即q不超过更短前缀的C，直接跳过；否则必须选它。若q等于一，可让前面为空；若q大于一，前一步必须准备q-1+b_i个。记录后反转，就得到按编号递增的前缀选择。

输出这个前缀、首个最终保留格子、最后后缀的全部编号。若最优不超过零，可输出空过程。分数总和可到三千乘一亿，使用long long；删除数只需记到n，因为可准备的旧格子不超过n。''',
    r'''int n; cin>>n;
vector<long long> a(n); vector<int> b(n),capacity(n+1);
for(auto &x:a) cin>>x;
for(int &x:b) cin>>x;
for(int i=0;i<n;++i){
    capacity[i+1]=max(capacity[i],max(0,capacity[i]-b[i])+1);
}
const long long NEG=LLONG_MIN/4;
vector<long long> dp(n+1,NEG); dp[0]=0;
vector<vector<unsigned char>> take(n,vector<unsigned char>(n+1));
long long best=0; int first=-1,weight=0;
for(int i=n-1;i>=0;--i){
    // 先把i当作最终首格：W=0始终可行，正W受前缀数量约束。
    int upper=max(0,capacity[i]-b[i]);
    for(int w=0;w<=upper;++w){
        if(dp[w]!=NEG&&a[i]+dp[w]>best){best=a[i]+dp[w];first=i;weight=w;}
    }
    // 再把i放入后缀背包；零重量也仅处理一次。
    for(int w=n;w>=b[i];--w){
        if(dp[w-b[i]]!=NEG&&dp[w-b[i]]+a[i]>dp[w]){
            dp[w]=dp[w-b[i]]+a[i]; take[i][w]=1;
        }
    }
}
if(first<0){cout<<"0\n\n0\n";return 0;}
vector<int> suffix,prefix; int remaining=weight;
for(int i=first+1;i<n;++i){
    if(take[i][remaining]){suffix.push_back(i);remaining-=b[i];}
}
// 恢复将来被删的旧格子，这些也必须写进完整选择过程。
int needed=weight?b[first]+weight:0;
for(int i=first-1;i>=0;--i){
    if(needed>capacity[i]){
        prefix.push_back(i);
        needed=needed==1?0:needed-1+b[i];
    }
}
reverse(prefix.begin(),prefix.end());
vector<int> chosen=prefix; chosen.push_back(first);
chosen.insert(chosen.end(),suffix.begin(),suffix.end());
cout<<chosen.size()<<'\n';
for(int i:chosen) cout<<i+1<<' ';
cout<<'\n'<<best<<'\n';''',
    '先删旧格再加入自己；删除只从队首；被删的辅助格子也要输出；零删除数物品仅取一次；所有负分可空选；输出完整过程。',
    r'时间 $O(n^2)$；滚动最优值用 $O(n)$，方案标记用 $O(n^2)$ 字节，总空间 $O(n^2)$。',tags=['背包 DP'],lessons=D,checker='fifo_selection')
