"""Cardinality closure, linear algebra moments and functional-graph independent sets."""
from nowcoder_editorials import CONTENT, add, read


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(210732,2200,['期望线性性','GF(2)线性方程'],'随机各开关按或不按，求亮灯数三次方的总和。',
        '令Y[i]为第i灯是否亮，则X³=Σ(i,j,k)Y[i]Y[j]Y[k]，三重求和允许下标重复。每灯状态是m个开关选择位的线性异或式，用64位掩码保存系数。某有序三元组对总和的贡献，恰为令这三个灯都亮的开关方案数。\n\n对三条方程mask·choice=1做二进制高斯消元。若出现0=1则贡献0；否则秩为r，方案数2^(m−r)。枚举n³个三元组并相加即可，直接得到E(X³)*2^m，不必算概率逆元。',
        r'''int n,m; cin >> n >> m; vector<unsigned long long> mask(n); for (int s=0;s<m;s++) { int k; cin >> k; while (k--) { int lamp; cin >> lamp; mask[lamp-1]^=1ULL<<s; } } const long long mod=1000000007; vector<long long> power(m+1,1); for (int i=1;i<=m;i++) power[i]=power[i-1]*2%mod; long long answer=0; for (int i=0;i<n;i++) for (int j=0;j<n;j++) for (int k=0;k<n;k++) { array<unsigned long long,50> basis={}; int rank=0; bool valid=true; for (int lamp:{i,j,k}) { unsigned long long row=mask[lamp]|(1ULL<<m); for (int bit=m-1;bit>=0;bit--) if (row>>bit&1) { if (basis[bit]) row^=basis[bit]; else { basis[bit]=row; rank++; row=0; break; } } if (row) { valid=false; break; } } if (valid) answer=(answer+power[m-rank])%mod; } cout << answer;''',
        '三次方要枚举有序三元组，重复灯号也需计入。开关可控制多盏灯，灯之间通常不独立。',
        complexity=r'时间 $O(n^3m)$，空间 $O(n+m)$。')
    put(210249,2200,['轮廓DP','前缀最大值'],'三角砖堆选m块，每块需先敲掉其上方两块，最大价值。',
        '按输入的从上到下层编号r，砖(r,j)要求(r−1,j)、(r−1,j+1)都已选。因此每一竖列j选择前h[j]块，并须h[j+1]≥h[j]−1，列长为n−j+1；这两个条件也充分。\n\n按列DP，状态为已用块数及上一列高度。当前列选g块，合法上一高度h≤g+1，贡献为本列前g块价值和。对固定已用块数，预先对上一高度做前缀最大值，就能常数时间得到max(h≤g+1)，总复杂度降为O(n²m)。',
        r'''int n,m; cin >> n >> m; vector<vector<int>> value(n+1,vector<int>(n+1)); for (int r=1;r<=n;r++) for (int j=1;j<=n-r+1;j++) cin >> value[r][j]; const int negative=-1000000000; vector<vector<int>> dp(m+1,vector<int>(n+2,negative)); dp[0][0]=0; for (int j=1;j<=n;j++) { for (int used=0;used<=m;used++) for (int h=1;h<=n+1;h++) dp[used][h]=max(dp[used][h],dp[used][h-1]); vector<vector<int>> next(m+1,vector<int>(n+2,negative)); int prefix=0; for (int g=0;g<=n-j+1 && g<=m;g++) { if (g) prefix+=value[g][j]; for (int used=g;used<=m;used++) if (dp[used-g][g+1]>negative) next[used][g]=dp[used-g][g+1]+prefix; } dp.swap(next); } cout << *max_element(dp[m].begin(),dp[m].end());''',
        '题面前半段的层长度措辞有混淆，按明确输入格式和依赖关系：最上层n块，下一层n−1块。选块数按恰好m处理。',
        complexity=r'时间 $O(n^2m)$，空间 $O(nm)$。')
    put(19978,2100,['最长公共子序列','计数DP','容斥'],'求LCS长度及匹配方案数模一亿。',
        '长度f[i][j]按标准LCS求。计数g[i][j]汇总所有达到该长度的来源：若末字符相同，加入对角子问题的匹配方案；若上方或左方长度也等于当前最优，分别加入它们。上、左共有的对角方案若长度同样最优，要减去一次避免重复。空前缀的空匹配计数为1。\n\n这里计数按两串中选取的位置区分。样例最长长度4，不同字面字符串只有5种，但有7组位置匹配，所以不能用“不同LCS字符串”算法代替。滚动两行保存长度和计数。',
        r'''string a,b; cin >> a >> b; if (!a.empty() && a.back()=='.') a.pop_back(); if (!b.empty() && b.back()=='.') b.pop_back(); int n=a.size(),m=b.size(); const int mod=100000000; vector<int> previousLength(m+1),currentLength(m+1),previousCount(m+1,1),currentCount(m+1,1); for (int i=1;i<=n;i++) { currentLength[0]=0; currentCount[0]=1; for (int j=1;j<=m;j++) { int best=max(previousLength[j],currentLength[j-1]); if (a[i-1]==b[j-1]) best=max(best,previousLength[j-1]+1); long long count=0; if (a[i-1]==b[j-1] && previousLength[j-1]+1==best) count+=previousCount[j-1]; if (previousLength[j]==best) count+=previousCount[j]; if (currentLength[j-1]==best) count+=currentCount[j-1]; if (previousLength[j-1]==best) count-=previousCount[j-1]; currentLength[j]=best; currentCount[j]=(count%mod+mod)%mod; } previousLength.swap(currentLength); previousCount.swap(currentCount); } cout << previousLength[m] << '\n' << previousCount[m];''',
        '字符串末尾点号是终止符，不能参与LCS。减法后取非负模；空LCS有一种空匹配。',
        complexity=r'时间 $O(nm)$，空间 $O(m)$。')
    put(210689,2100,['贡献法','空隙计数','后缀和'],'预处理所有窗口长度的不同数总数，百万次询问。',
        '对每个出现过的数x，长度L窗口一共n−L+1个，其中不含x的窗口必完全位于相邻x之间（含首尾）的空隙。长g空隙能放max(0,g−L+1)个窗口。因此答案=不同数个数*(n−L+1)−Σ(g≥L)countGap[g]*(g−L+1)。\n\n扫描数组记录每个数上次位置，统计前方和中间空隙；最后补尾部空隙。对空隙长度做后缀个数、后缀长度和，可常数时间求上式并预处理全部L。',
        r'''int n; cin >> n; const int limit=1000000; vector<int> previous(limit+1); vector<long long> gap(n+1); int distinct=0; for (int i=1;i<=n;i++) { int x; cin >> x; if (!previous[x]) distinct++; gap[i-previous[x]-1]++; previous[x]=i; } for (int x=1;x<=limit;x++) if (previous[x]) gap[n-previous[x]]++; vector<long long> answer(n+1); long long count=0,length=0; for (int l=n;l>=1;l--) { count+=gap[l]; length+=gap[l]*l; answer[l]=1LL*distinct*(n-l+1)-(length-(l-1)*count); } int q; cin >> q; while (q--) { int l; cin >> l; cout << answer[l] << '\n'; }''',
        '只统计实际出现过的数；每个数首尾空隙都需加入。总价值可超过32位。',
        complexity=r'时间 $O(n+U+q)$，空间 $O(n+U)$。')
    put(210684,1900,['排列DP','前缀和'],'给相邻升降或任意关系，统计合法排列。',
        '构造长度i排列，dp[j]表示最后元素在这i个元素中排名j（从0开始）的方案数。加入下一元素，新排名为j时，旧最后元素原排名k在“上升”情形需k<j，在“下降”情形需k≥j；无约束取全部k。用上一行dp前缀和常数时间求三个转移，每层增加一个排名。',
        r'''string s; cin >> s; const int mod=998244353; vector<int> dp(1,1); for (char relation:s) { int length=dp.size(); vector<int> prefix(length+1); for (int j=0;j<length;j++) { prefix[j+1]=prefix[j]+dp[j]; if (prefix[j+1]>=mod) prefix[j+1]-=mod; } vector<int> next(length+1); for (int j=0;j<=length;j++) { if (relation=='1') next[j]=prefix[j]; else if (relation=='2') next[j]=(prefix[length]-prefix[j]+mod)%mod; else next[j]=prefix[length]; } dp.swap(next); } long long answer=0; for (int x:dp) answer=(answer+x)%mod; cout << answer;''',
        '插入新元素会让原来≥j的值整体加1，因此下降条件在旧排名里是k≥j。',
        complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(19972,2200,['二分答案','动态规划','滑动窗口'],'最多m刀分木棍，最小最长段长度并统计全部最优切法。',
        '先二分最大段长X，贪心从左向右尽量装满一段，所得段数最少；若≤m+1则可行。求得最优X后计数：dp[k][i]为前i根分成恰k个非空段且段长都≤X的方案数，转移Σdp[k−1][j]，其中prefix[i]−prefix[j]≤X、j<i。\n\n长度正数使合法j形成移动窗口，维护上一行DP窗口和，每层O(n)。答案是k=1..m+1的dp[k][n]之和，因为允许最多m刀，最优切法不一定刀数相同。',
        r'''int n,m; cin >> n >> m; vector<long long> prefix(n+1); long long low=0; for (int i=1;i<=n;i++) { int x; cin >> x; prefix[i]=prefix[i-1]+x; low=max(low,(long long)x); } long long high=prefix[n]; auto feasible=[&](long long limit) { int groups=1; long long sum=0; for (int i=1;i<=n;i++) { long long x=prefix[i]-prefix[i-1]; if (sum+x>limit) { groups++; sum=0; } sum+=x; } return groups<=m+1; }; while (low<high) { long long mid=(low+high)/2; if (feasible(mid)) high=mid; else low=mid+1; } const int mod=10007; vector<int> previous(n+1),current(n+1); previous[0]=1; int answer=0; for (int groups=1;groups<=m+1;groups++) { fill(current.begin(),current.end(),0); int left=0,sum=0; for (int i=1;i<=n;i++) { sum=(sum+previous[i-1])%mod; while (prefix[i]-prefix[left]>low) { sum=(sum-previous[left]+mod)%mod; left++; } current[i]=sum; } answer=(answer+current[n])%mod; previous.swap(current); } cout << low << ' ' << answer;''',
        '不能只统计恰好m刀；样例最优长度10既有一刀也有两刀，共2种。',
        complexity=r'时间 $O(n\log(\sum L)+nm)$，空间 $O(n)$。')
    put(20481,2300,['基环树','最大权独立集','拓扑剥叶'],'每个骑士恨一个人，不能同选，求最大总战力。',
        '将每人指向其厌恶者，得到每点出度1的功能图，每个连通块恰有一个有向环。先按入度0剥叶，维护not[u]、yes[u]为以u为根的附属树不选/选u的最大战力，剥去u后向parent累加max(not,yes)和not。剥完剩下的都是环。\n\n每个环上节点已汇总其外接树。枚举第一个环点不选或选，用链式独立集DP逐点更新；首点选中时强制末点不选，保证闭环边合法。各连通块答案相加，百万点也无需递归。',
        r'''int n; cin >> n; vector<int> parent(n),indegree(n); vector<long long> no(n),yes(n); for (int i=0;i<n;i++) { cin >> yes[i] >> parent[i]; parent[i]--; indegree[parent[i]]++; } queue<int> queue; for (int i=0;i<n;i++) if (!indegree[i]) queue.push(i); while (!queue.empty()) { int u=queue.front(); queue.pop(); int p=parent[u]; no[p]+=max(no[u],yes[u]); yes[p]+=no[u]; if (--indegree[p]==0) queue.push(p); } vector<bool> seen(n); long long answer=0; const long long negative=LLONG_MIN/4; for (int start=0;start<n;start++) if (indegree[start] && !seen[start]) { vector<int> cycle; int u=start; do { cycle.push_back(u); seen[u]=true; u=parent[u]; } while (u!=start); auto solve=[&](bool firstSelected) { long long previousNo=firstSelected?negative:no[cycle[0]],previousYes=firstSelected?yes[cycle[0]]:negative; for (int i=1;i<(int)cycle.size();i++) { int v=cycle[i]; long long currentNo=max(previousNo,previousYes)+no[v],currentYes=previousNo+yes[v]; previousNo=currentNo; previousYes=currentYes; } return firstSelected?previousNo:max(previousNo,previousYes); }; answer+=max(solve(false),solve(true)); } cout << answer;''',
        '相互厌恶构成长度2的环，也只要求二者不能同选，环DP照常适用。总战力用64位。',
        complexity=r'时间、空间均 $O(n)$。')
    put(232851,2100,['计数DP','前缀和','对称分布'],'双方每轮各加[-k,k]整数，统计t轮后先手分数更高的游戏数。',
        'L的每次增量取负后仍均匀遍历[-k,k]，所以M减L的总增量可视为2t个独立[-k,k]整数之和。每个数加k变成[0,2k]，若和为s，最终差为a−b+s−2kt，要求s>b−a+2kt。\n\nDP统计2t个[0,2k]整数的和。每层新dp[s]为旧dp[s−2k..s]之和，用滑动窗口O(1)更新每个s。最后把满足严格不等式的和状态相加。',
        r'''int a,b,k,t; cin >> a >> b >> k >> t; const int mod=1000000007; vector<int> dp(1,1); for (int step=0;step<2*t;step++) { int old=dp.size()-1; vector<int> next(old+2*k+1); long long sum=0; for (int s=0;s<(int)next.size();s++) { if (s<=old) sum+=dp[s]; int remove=s-2*k-1; if (remove>=0 && remove<=old) sum-=dp[remove]; sum=(sum%mod+mod)%mod; next[s]=sum; } dp.swap(next); } int threshold=b-a+2*k*t; long long answer=0; for (int s=max(0,threshold+1);s<(int)dp.size();s++) answer=(answer+dp[s])%mod; cout << answer;''',
        '胜利要求严格大于，平分不能计入。每一轮每个人的取值独立，转换后仍需2t个变量。',
        complexity=r'时间 $O(kt^2)$，空间 $O(kt)$。')


if __name__ == '__main__': run()
