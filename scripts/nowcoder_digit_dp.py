"""Digit automata with explicit leading-zero conventions and reusable free states."""
from nowcoder_editorials import CONTENT, add, read

COUNT_DIGIT = r'''
long long countDigit(long long n,int digit) {
    if (n<=0) return 0;
    long long answer=0;
    for (long long place=1;place<=n;) {
        long long high=n/place/10,current=n/place%10,low=n%place;
        if (digit) {
            answer+=high*place;
            if (current>digit) answer+=place;
            else if (current==digit) answer+=low+1;
        } else if (high) {
            answer+=(high-1)*place;
            answer+=current==0?low+1:place;
        }
        if (place>n/10) break;
        place*=10;
    }
    return answer;
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(233097,1700,['按位计数','前导零'],'多组求[m,n]的十进制0总数，包含数字0自身。',
        '先求正整数1..n中0的次数。枚举十进制位place，拆成高位high、当前位current、低位low。高位为0时该位不能出现有效0；否则完整高位周期贡献(high−1)*place，再按当前位补low+1（current=0）或place（current>0）。减掉的一个周期正是非法前导零。\n\n数字0自身有一个0，故F(n)=正数计数+1（n≥0）；最后用F(n)−F(m−1)。',
        r'''long long m,n; auto prefix=[&](long long x) { return x<0?0LL:countDigit(x,0)+1; }; while (cin >> m >> n && m>=0 && n>=0) cout << prefix(n)-prefix(m-1) << '\n';''',
        '不能把0当成没有数位；负输入对是结束标记。高位为0的最高补零不能计数。',
        declarations=COUNT_DIGIT,complexity=r'每组时间 $O(\log n)$，空间 $O(1)$。')
    put(20491,1700,['按位计数'],'求[a,b]内每个十进制数码出现总次数。',
        '对数字d枚举位权place。非零d：完整高位周期贡献high*place；当前位>d再加place，等于d加low+1，小于则不加。d=0时须排除前导零：high>0才有贡献，先加(high−1)*place，再根据当前位补充。分别计算1..b和1..a−1后相减。',
        r'''long long a,b; cin >> a >> b; for (int d=0;d<10;d++) cout << countDigit(b,d)-countDigit(a-1,d) << (d==9?'\n':' ');''',
        '原题区间全为正数，数字0自身不加入。输出次数用64位。',
        declarations=COUNT_DIGIT,complexity=r'时间 $O(10\log b)$，空间 $O(1)$。')
    put(15035,1600,['数位DP','自动机'],'统计区间中包含数字4或相邻子串38的讨厌数。',
        '数位状态保存上一位是否为3、此前是否已经讨厌、是否贴上界。加入d后，若d=4或上一位为3且d=8就永久标记讨厌；结束时只计讨厌状态。前导0既不是3也不是4，不会凭空产生38，因此可以补到相同位数，无需额外开始标记。非贴界状态按剩余位数记忆化，区间由两个前缀计数相减。',
        r'''auto count=[&](long long n) { if (n<0) return 0LL; string s=to_string(n); long long memo[20][2][2]; memset(memo,-1,sizeof(memo)); auto dfs=[&](auto &&self,int p,bool previous3,bool bad,bool tight)->long long { if (p==(int)s.size()) return bad; auto &cached=memo[s.size()-p][previous3][bad]; if (!tight && cached!=-1) return cached; int limit=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=limit;d++) result+=self(self,p+1,d==3,bad||d==4||(previous3&&d==8),tight&&d==limit); if (!tight) cached=result; return result; }; return dfs(dfs,0,false,false,true); }; long long l,r; while (cin >> l >> r && (l||r)) cout << count(r)-count(l-1) << '\n';''',
        '题目输出讨厌数数量，不是避开讨厌数的数量。38必须相邻，不能只出现3和8就判定。',
        complexity=r'每组时间 $O(位数\cdot 2^2\cdot10)$，空间 $O(位数)$。')
    put(20669,2000,['数位DP','连续段约束'],'每个非零数字连续出现次数受上限约束，多组统计模20020219。',
        '同一个数字可能给出多条限制，取最小上限。状态为位置、上一数字、当前连续次数、是否已经开始、贴界。前导0不形成数码段；开始后遇同数字连续长度加1，换数字则重置1，超上限直接跳过。未限制数码把上限设19，0保证无限制。全程未开始代表整数0，应计入。每个测试重建与自身限制对应的缓存。',
        r'''int tests; cin >> tests; const int mod=20020219; while (tests--) { long long l,r; int n; cin >> l >> r >> n; array<int,10> limit; limit.fill(19); while (n--) { int x,len; cin >> x >> len; limit[x]=min(limit[x],len); } auto count=[&](long long bound) { if (bound<0) return 0; string s=to_string(bound); int memo[20][11][20]; memset(memo,-1,sizeof(memo)); auto dfs=[&](auto &&self,int p,int previous,int run,bool tight)->int { if (p==(int)s.size()) return 1; int &cache=memo[s.size()-p][previous][run]; if (!tight && cache!=-1) return cache; int maximum=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=maximum;d++) { if (previous==10 && d==0) result+=self(self,p+1,10,0,tight&&d==maximum); else { int next=previous==d?run+1:1; if (next<=limit[d]) result+=self(self,p+1,d,next,tight&&d==maximum); } } int value=result%mod; if (!tight) cache=value; return value; }; return dfs(dfs,0,10,0,true); }; cout << (count(r)-count(l-1)+mod)%mod << '\n'; }''',
        '限制“不能大于len”允许恰好len次；重复约束取较严者。整数0不是前导0产生的多位串。',
        complexity=r'每组时间 $O(D\cdot11\cdot D\cdot10)$，空间 $O(11D^2)$，D≤19。')
    put(20665,1700,['数位DP','整除状态'],'数和数位和都能被某个全7正整数整除。',
        '全7序列中最小的7整除其余每一项，所以“能被任一项整除”等价于能被7整除；数位和条件同理。只需状态维护当前值模7、数位和模7，添加d后分别更新(10*value+d)%7、(sum+d)%7。结束两者为0就计数。前导0不影响两个状态，内部把0计入两个前缀后会抵消。',
        r'''long long memo[20][7][7]; memset(memo,-1,sizeof(memo)); auto count=[&](long long n) { if (n<0) return 0LL; string s=to_string(n); auto dfs=[&](auto &&self,int p,int value,int sum,bool tight)->long long { if (p==(int)s.size()) return value==0 && sum==0; auto &cache=memo[s.size()-p][value][sum]; if (!tight && cache!=-1) return cache; int limit=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=limit;d++) result+=self(self,p+1,(value*10+d)%7,(sum+d)%7,tight&&d==limit); if (!tight) cache=result; return result; }; return dfs(dfs,0,0,0,true); }; long long l,r; while (cin >> l >> r && (l||r)) cout << count(r)-count(l-1) << '\n';''',
        '两个整除条件必须同时满足，不能只检查数字本身含7。',
        complexity=r'缓存预处理 $O(D\cdot49\cdot10)$，每次边界计数 $O(D\cdot10)$，空间 $O(49D)$。')
    put(17385,2100,['数位DP','枚举数位和'],'统计1到N中能被自身数位和整除的数，多组上界。',
        '直接把数位和作为动态模数不可行，改为枚举最终数位和S。固定S后，数位DP状态为已用和sum、当前数模S的余数remainder；结束要求sum=S且余数0。若sum>S或sum+9*剩余位<S，立刻剪枝。\n\n外层固定S，再依次处理全部测试。非贴界状态只取决于剩余位数、sum、remainder，能跨测试复用同一缓存；换S再清空。这样不用为每个N重复填整张状态表。S≥1自动排除0。',
        r'''int tests; cin >> tests; vector<long long> bound(tests),answer(tests); int digits=1; for (auto &x:bound) { cin >> x; digits=max(digits,(int)to_string(x).size()); } for (int target=1;target<=9*digits;target++) { int sums=target+1; vector<long long> memo((digits+1)*sums*target,-1); for (int tc=0;tc<tests;tc++) { string s=to_string(bound[tc]); auto dfs=[&](auto &&self,int p,int sum,int remainder,bool tight)->long long { int remaining=s.size()-p; if (sum>target || sum+remaining*9<target) return 0; if (!remaining) return sum==target && remainder==0; long long &cache=memo[(remaining*sums+sum)*target+remainder]; if (!tight && cache!=-1) return cache; int maximum=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=maximum;d++) result+=self(self,p+1,sum+d,(remainder*10+d)%target,tight&&d==maximum); if (!tight) cache=result; return result; }; answer[tc]+=dfs(dfs,0,0,0,true); } } for (int tc=0;tc<tests;tc++) cout << "Case " << tc+1 << ": " << answer[tc] << '\n';''',
        '缓存必须包含目标S，代码通过每个S单独开表实现；同一S可跨不同长度上界复用“剩余位数”状态。',
        complexity=r'令最大位数D、Smax=9D，缓存转移上界 $O(10D Smax^3)$，各边界另有 $O(10TD Smax)$；空间 $O(D Smax^2)$。')
    put(232847,2200,['数位DP','最小公倍数'],'统计能被所有非零数码整除的数。',
        '所有非零数码的最小公倍数L一定是2520的约数，共48种。数字只需保存模2520余数，因为最终判定r%L=0即可。加入非零d时L更新为lcm(L,d)，加入0时不变。预先列出2520全部约数及其转移，用(剩余位数,L编号,余数)缓存非贴界状态。前导0不改变L或余数，内部整数0也满足判定，但原区间l≥1，两个前缀相减会抵消它。',
        r'''vector<int> divisor; for (int d=1;d<=2520;d++) if (2520%d==0) divisor.push_back(d); vector<int> index(2521); for (int i=0;i<(int)divisor.size();i++) index[divisor[i]]=i; vector<array<int,10>> next(divisor.size()); for (int i=0;i<(int)divisor.size();i++) for (int d=0;d<=9;d++) next[i][d]=index[d?lcm(divisor[i],d):divisor[i]]; int states=divisor.size(); vector<long long> memo(20*states*2520,-1); auto count=[&](long long bound) { if (bound<0) return 0LL; string s=to_string(bound); auto dfs=[&](auto &&self,int p,int state,int remainder,bool tight)->long long { if (p==(int)s.size()) return remainder%divisor[state]==0; long long &cache=memo[((s.size()-p)*states+state)*2520+remainder]; if (!tight && cache!=-1) return cache; int maximum=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=maximum;d++) result+=self(self,p+1,next[state][d],(remainder*10+d)%2520,tight&&d==maximum); if (!tight) cache=result; return result; }; return dfs(dfs,0,index[1],0,true); }; int tests; cin >> tests; while (tests--) { long long l,r; cin >> l >> r; cout << count(r)-count(l-1) << '\n'; }''',
        '0数码应忽略，不能令L变成0。余数必须模2520，不能随L变化后丢掉必要信息。',
        complexity=r'缓存至多 $O(D\cdot48\cdot2520)$ 个状态，每状态10条转移；单边界另 $O(10D)$，空间同状态数。')
    put(17867,1900,['数位DP','二分答案'],'求严格大于m的第n个7倍数或含7的数字。',
        '用数位DP统计F(x)：值模7、此前是否出现7，结束满足余数0或出现7。整数0也满足倍数判定，但F(x)−F(m)会抵消。答案最小x使F(x)−F(m)≥n。以m+7n为二分上界，因为这段至少含n个7倍数；每次只需前缀计数。',
        r'''long long memo[20][7][2]; memset(memo,-1,sizeof(memo)); auto count=[&](long long bound) { string s=to_string(bound); auto dfs=[&](auto &&self,int p,int remainder,bool has7,bool tight)->long long { if (p==(int)s.size()) return remainder==0 || has7; long long &cache=memo[s.size()-p][remainder][has7]; if (!tight && cache!=-1) return cache; int maximum=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=maximum;d++) result+=self(self,p+1,(remainder*10+d)%7,has7||d==7,tight&&d==maximum); if (!tight) cache=result; return result; }; return dfs(dfs,0,0,false,true); }; long long m,n; cin >> m >> n; long long before=count(m),low=m+1,high=m+7*n; while (low<high) { long long mid=low+(high-low)/2; if (count(mid)-before>=n) high=mid; else low=mid+1; } cout << low;''',
        '“m以后”严格排除m。倍数与含7取并集，不能重复计数。',
        complexity=r'缓存 $O(D\cdot14\cdot10)$；二分 $O(D\log n)$ 次常数规模数位分支，空间 $O(14D)$。')
    put(19327,1900,['数位DP','子序列自动机'],'统计十进制表示中含子序列007的数，多个区间答案异或。',
        '状态0、1、2、3表示已经依次匹配007的长度，3为吸收态。当前数码等于下一个所需字符时匹配长度加1，不相等则保持。还需started区分前导0，未开始的0不能用于匹配。按剩余位数、匹配状态、started缓存自由状态，十万组询问共用；每问两个前缀差，异或进最终结果。',
        r'''long long memo[20][4][2]; memset(memo,-1,sizeof(memo)); auto count=[&](long long bound) { if (bound<0) return 0LL; string s=to_string(bound),pattern="007"; auto dfs=[&](auto &&self,int p,int state,bool started,bool tight)->long long { if (p==(int)s.size()) return state==3; long long &cache=memo[s.size()-p][state][started]; if (!tight && cache!=-1) return cache; int maximum=tight?s[p]-'0':9; long long result=0; for (int d=0;d<=maximum;d++) { bool begun=started||d; int next=state; if (begun && next<3 && d==pattern[next]-'0') next++; result+=self(self,p+1,next,begun,tight&&d==maximum); } if (!tight) cache=result; return result; }; return dfs(dfs,0,0,false,true); }; int tests; cin >> tests; long long answer=0; while (tests--) { long long l,r; cin >> l >> r; answer^=count(r)-count(l-1); } cout << answer;''',
        '007是子序列，可以不连续；前导0不属于名字。匹配成功后不可被后续数码取消。',
        complexity=r'预处理自由状态 $O(D\cdot8\cdot10)$，每次边界 $O(10D)$，总 $O(TD)$，空间 $O(8D)$。')
    put(14732,2200,['集合覆盖','极大不满足集合'],'居民权值和至少m才可打开全部锁，求最少锁数。',
        '没有达到阈值的集合称失败集合。考虑其中“再加任何一个外部居民就成功”的极大失败集合S：它必须至少缺一把钥匙，而所有不在S中的居民都必须持有这把钥匙，否则S再加那个人仍打不开。故这把锁的无钥匙者集合恰好是S。两个不同极大失败集合不能共用此锁，所以至少需要极大失败集合个数把锁。\n\n反过来，为每个极大失败集合各建一锁，只给其外部居民钥匙。所有失败集合都包含于某个极大失败集合而缺该钥匙；任意成功集合不包含于失败集合，故每锁都至少有一名持钥匙者，构造成立。\n\n枚举全部掩码，求权值和；未达m且加上补集中最小权值后达到m，就恰为极大失败集合。补集为空时也算极大失败。',
        r'''int n; long long threshold; cin >> n >> threshold; vector<long long> weight(n); for (auto &x:weight) cin >> x; int size=1<<n; vector<long long> sum(size),minimum(size,LLONG_MAX/4); for (int mask=1;mask<size;mask++) { int bit=__builtin_ctz((unsigned)mask),rest=mask&(mask-1); sum[mask]=sum[rest]+weight[bit]; minimum[mask]=min(minimum[rest],weight[bit]); } int answer=0; for (int mask=0;mask<size;mask++) if (sum[mask]<threshold && (mask==size-1 || sum[mask]+minimum[(size-1)^mask]>=threshold)) answer++; cout << answer;''',
        '权值均正，所以只需检查最小外部权值。所有人总权仍不足m时，完整集合是唯一极大失败集合，一把无人有钥匙的锁即可。',
        complexity=r'时间、空间均 $O(2^n)$。')


if __name__ == '__main__': run()
