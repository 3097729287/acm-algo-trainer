"""Bounded state ranges, gcd states and optimized partition transitions."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(232853,2100,['动态规划','状态范围优化'],'向东跳，跳长每次至多改变1，收集最多宝石。',
        'dp[position][jump]表示最后一次跳长为jump时的最多宝石。下一跳尝试jump−1、jump、jump+1，正长度且不越界即可。关键是限制跳长范围：从初始d增加或减少250，必须经历至少250次逐级变化，仅这些跳长的最小总和就超过30000；减小的情况还要求d≥251。因此只需保存jump∈[d−250,d+250]与正整数的交集。\n\n位置严格增加，按位置升序转移。总宝石至30000，16位有符号数足够存答案及−1不可达标记，约30MB。',
        r'''int n,d; cin >> n >> d; const int limit=30000,width=501; vector<int> gem(limit+1); for (int i=0;i<n;i++) { int p; cin >> p; gem[p]++; } vector<int16_t> dp((limit+1)*width,-1); dp[d*width+250]=gem[d]; int answer=0; for (int p=d;p<=limit;p++) for (int index=0;index<width;index++) { int current=dp[p*width+index]; if (current<0) continue; answer=max(answer,current); int jump=d+index-250; for (int change=-1;change<=1;change++) { int next=index+change,length=jump+change; if (next>=0 && next<width && length>0 && p+length<=limit) { auto &value=dp[(p+length)*width+next]; value=max((int)value,current+gem[p+length]); } } } cout << answer;''',
        '同一个位置可能有多颗宝石，必须累计频数。第一次强制跳到d，不能从0随意选择第一跳。',
        complexity=r'时间 $O(30000\sqrt{30000})$，空间同状态数，每状态16位。')
    put(232854,2000,['最大公约数','裴蜀定理','状态压缩'],'付费学若干双向跳长，要求能到达全部整数位置。',
        '可正反向使用跳长，能到达的位置恰是所选跳长gcd的倍数，所以目标是选出gcd=1的最小费用。dp[g]记录已处理卡片选择子集gcd为g的最少费用，空集用g=0。对每张卡，用旧表副本保留不选，再用gcd(g,l)更新选卡状态。相同gcd仅保留费用最小者。',
        r'''int n; cin >> n; vector<int> length(n),cost(n); for (int &x:length) cin >> x; for (int &x:cost) cin >> x; map<int,long long> dp={{0,0}}; for (int i=0;i<n;i++) { auto next=dp; for (auto [g,value]:dp) { int target=gcd(g,length[i]); long long candidate=value+cost[i]; auto it=next.find(target); if (it==next.end() || candidate<it->second) next[target]=candidate; } dp.swap(next); } cout << (dp.count(1)?dp[1]:-1);''',
        '允许反向跳，所以使用整数线性组合，不是非负背包。不能仅检查是否存在两张互素卡，可能需要更多张。',
        complexity=r'设最多S个不同gcd状态，时间 $O(nS(\log U+\log S))$，空间 $O(S)$。')
    put(210734,1800,['最大子段和','分组DP'],'选择恰好m个互不重叠非空连续段，最大总和。',
        'end[k]为当前前缀中选k段且最后一段以当前元素结尾的最大值，best[k]为当前前缀任意位置结束的最优值。加入x时，end[k]=max(旧end[k]+x,旧best[k−1]+x)，分别代表延长最后一段、从当前元素新开一段；best[k]取原值与新end[k]较大者。k倒序，保证best[k−1]还未使用当前元素。',
        r'''int n,m; cin >> n >> m; const long long negative=LLONG_MIN/4; vector<long long> ending(m+1,negative),best(m+1,negative); best[0]=0; for (int i=1;i<=n;i++) { long long x; cin >> x; for (int k=min(i,m);k>=1;k--) { ending[k]=max(ending[k],best[k-1])+x; best[k]=max(best[k],ending[k]); } } cout << best[m];''',
        '恰好m段，不能把所有状态初始化0；全负数组仍必须选够。原任务需要m≤n才有合法方案。',
        complexity=r'时间 $O(nm)$，空间 $O(m)$。')
    put(210805,2200,['动态规划','根号优化','最近出现位置'],'分割数组，每段代价为不同数字数的平方，最小总代价。',
        'dp[i]是前i项最小代价，且dp随i不减：任意前i项方案删掉末项后仍是前i−1项可行方案，代价不会增加。固定右端i，若最后一段允许至多k种数，最佳左端应尽量早，因为此前dp更小。\n\n按各数最近一次出现位置从新到旧排列。第k+1新的出现位置p之后，至i恰好只含最近k种数，因此候选为dp[p]+k²；若不足k+1种则p=0。维护一个最近使用链表，每次把当前数移到表头，即可依次得到所有p。\n\n逐个枚举k，若k²已经不小于当前答案就停止；总答案≤i（每个元素单独一段），所以只需O(sqrt n)个k，不会因相同数字连续出现而回扫很长区间。',
        r'''int n; cin >> n; vector<int> a(n),coordinate; for (int &x:a) cin >> x; coordinate=a; sort(coordinate.begin(),coordinate.end()); coordinate.erase(unique(coordinate.begin(),coordinate.end()),coordinate.end()); list<int> recent; vector<list<int>::iterator> where(coordinate.size()); vector<bool> present(coordinate.size()); vector<int> dp(n+1); for (int i=1;i<=n;i++) { int id=lower_bound(coordinate.begin(),coordinate.end(),a[i-1])-coordinate.begin(); if (present[id]) recent.erase(where[id]); recent.push_front(i); where[id]=recent.begin(); present[id]=true; dp[i]=dp[i-1]+1; auto it=recent.begin(); for (int k=1;it!=recent.end() && k*k<dp[i];k++) { it++; int previous=it==recent.end()?0:*it; dp[i]=min(dp[i],dp[previous]+k*k); } } cout << dp[n];''',
        '直接向左扫描直到sqrt n种数，在全相同数组上仍会退化平方时间；这里遍历的是不同数的最近位置链表。',
        complexity=r'时间 $O(n\log n+n\sqrt n)$，空间 $O(n)$。')
    put(232855,2100,['动态规划','单调队列','交换论证'],'每段免费去掉最小floor(长度/c)项，求分割后的最小收费和。',
        '先求最大折扣，再用总和减去。长度kc+r的段，原折扣是该段最小k项之和。把其中连续kc项分成k个长度c的块，剩下r项单独处理，每块各免其最小值，相当于从原段选了k项；任意k项之和不少于全局最小k项，因此这样细分折扣只会更大。\n\n所以只需考虑互不重叠的长度c块。f[i]=max(f[i−1],f[i−c]+min(a[i−c+1..i]))，分别不以i结束块、选择该块。用单调队列维护长度c的滑动最小值。',
        r'''int n,c; cin >> n >> c; vector<long long> a(n+1),dp(n+1); long long sum=0; deque<int> queue; for (int i=1;i<=n;i++) { cin >> a[i]; sum+=a[i]; while (!queue.empty() && a[queue.back()]>=a[i]) queue.pop_back(); queue.push_back(i); while (!queue.empty() && queue.front()<=i-c) queue.pop_front(); dp[i]=dp[i-1]; if (i>=c) dp[i]=max(dp[i],dp[i-c]+a[queue.front()]); } cout << sum-dp[n];''',
        '不是每c个元素固定一组，可以跳过部分元素选择更好的不重叠块。c=1时所有元素免费，答案0。',
        complexity=r'时间、空间均 $O(n)$。')
    put(232856,2100,['差分','动态规划','单调队列'],'长度2A到2B的装置恰铺满[0,L]，指定区间不能被切开。',
        '装置半径为整数，覆盖长度为偶数，所以从0开始所有分界都为偶数。令dp[i]表示覆盖到2i的最少装置数；若2i严格位于某个指定(S,E)内，此处不能作为分界。用差分标记全部禁用整数分界，端点S、E本身允许。\n\n对允许的i，dp[i]=1+min(dp[j])，j∈[i−B,i−A]且j允许。维护这个移动窗口中dp递增的单调队列，dp[0]=0，答案dp[L/2]。',
        r'''int n,length,a,b; cin >> n >> length >> a >> b; vector<int> difference(length+2); for (int i=0;i<n;i++) { int s,e; cin >> s >> e; difference[s+1]++; difference[e]--; } vector<bool> allowed(length/2+1); int active=0; for (int x=0;x<=length;x++) { active+=difference[x]; if (x%2==0) allowed[x/2]=active==0; } int target=length/2,inf=1000000000; vector<int> dp(target+1,inf); dp[0]=0; deque<int> queue; for (int i=1;i<=target;i++) { int enter=i-a; if (enter>=0 && allowed[enter] && dp[enter]<inf) { while (!queue.empty() && dp[queue.back()]>=dp[enter]) queue.pop_back(); queue.push_back(enter); } while (!queue.empty() && queue.front()<i-b) queue.pop_front(); if (allowed[i] && !queue.empty()) dp[i]=dp[queue.front()]+1; } cout << (dp[target]==inf?-1:dp[target]);''',
        '禁止切的是区间内部，不是两端；重叠约束用覆盖次数并集处理，不能只逐条判断。',
        complexity=r'时间 $O(L+N)$，空间 $O(L)$。')
    put(210807,2000,['区间DP'],'按顺序删除怪物，每次受自身攻击及当时两邻增益伤害，求最小总伤害。',
        '设dp[l][r]为删除区间[l,r]且两侧l−1、r+1暂不删除的最小伤害。枚举区间内最后删除的k，之前左右两段独立删除，最后k只受固定边界增益b[l−1]+b[r+1]及自身a[k]。转移dp[l][r]=min_k(dp[l][k−1]+dp[k+1][r]+a[k]+b[l−1]+b[r+1])。两端增设0增益哨兵，按长度递增计算。',
        r'''int n; cin >> n; vector<long long> a(n+2),b(n+2); for (int i=1;i<=n;i++) cin >> a[i]; for (int i=1;i<=n;i++) cin >> b[i]; vector<vector<long long>> dp(n+2,vector<long long>(n+2)); for (int len=1;len<=n;len++) for (int l=1;l+len-1<=n;l++) { int r=l+len-1; dp[l][r]=LLONG_MAX/4; for (int k=l;k<=r;k++) dp[l][r]=min(dp[l][r],dp[l][k-1]+dp[k+1][r]+a[k]+b[l-1]+b[r+1]); } cout << dp[1][n];''',
        '枚举最后删除者，边界才固定；枚举第一个删除者不能把剩余两边直接独立相加。',
        complexity=r'时间 $O(n^3)$，空间 $O(n^2)$。')
    put(19982,2100,['区间DP','加权区间调度'],'每人声称比自己高、低分人数，最少说谎人数。',
        '声称(a,b)的人若说真话，其所在同分组占据排序名次[a+1,n−b]，长度为n−a−b。相同声明可同时为真，但至多选该长度的人数，权重为min(声明次数,区间长度)。不同真实同分组的名次区间必须互不重叠。\n\n因此合并相同声明后，变成带权区间调度：dp[r]为前r个名次最多真实人数，dp[r]先继承dp[r−1]，再对所有以r结束的组更新dp[l−1]+weight。未选名次由说谎者补齐，不影响已选组。答案n−dp[n]。',
        r'''int n; cin >> n; map<pair<int,int>,int> count; for (int i=0;i<n;i++) { int a,b; cin >> a >> b; if (a+b<n) count[{a+1,n-b}]++; } vector<vector<pair<int,int>>> ending(n+1); for (auto [interval,frequency]:count) { auto [l,r]=interval; ending[r].push_back({l,min(frequency,r-l+1)}); } vector<int> dp(n+1); for (int r=1;r<=n;r++) { dp[r]=dp[r-1]; for (auto [l,w]:ending[r]) dp[r]=max(dp[r],dp[l-1]+w); } cout << n-dp[n];''',
        'a+b≥n时同分组长度非正，该声明必假。相同声明人数超过组大小，只能让其中一部分为真。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')


if __name__ == '__main__': run()
