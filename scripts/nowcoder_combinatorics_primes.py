"""Reviewed elementary combinations, partial matchings and prime interval tasks."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_number_basics import EXGCD

FACTORIAL = r'''
constexpr long long mod=MODULUS;
long long power(long long a,long long b) { long long result=1; while (b) { if (b&1) result=result*a%mod; a=a*a%mod; b>>=1; } return result; }
struct Combinations {
    vector<long long> factorial,inverse;
    Combinations(int n):factorial(n+1,1),inverse(n+1) {
        for (int i=1;i<=n;i++) factorial[i]=factorial[i-1]*i%mod;
        inverse[n]=power(factorial[n],mod-2);
        for (int i=n;i>=1;i--) inverse[i-1]=inverse[i]*i%mod;
    }
    long long choose(int n,int k) const { if (k<0 || k>n) return 0; return factorial[n]*inverse[k]%mod*inverse[n-k]%mod; }
};
'''
SIEVE = r'''
vector<int> sieve(int n) {
    vector<bool> composite(n+1); vector<int> primes;
    for (int p=2;p<=n;p++) if (!composite[p]) {
        primes.push_back(p);
        if (1LL*p*p<=n) for (int x=p*p;x<=n;x+=p) composite[x]=true;
    }
    return primes;
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(229263,800,['乘法原理','等比数列'],'统计至多n位、每位7或8的数。',
        '恰k位有2^k种，k从1到n相加为2^(n+1)−2。n≤55，64位整数足够。',
        r'''int n; cin >> n; cout << (1ULL<<(n+1))-2;''',
        '不包含空数字，所以减2；移位常数使用64位。',
        complexity=r'时间、空间均 $O(1)$。')
    put(229265,1000,['组合计数'],'巧克力方格中统计同一行或同一列的无序对。',
        '某行有c个巧克力，可选C(c,2)=c(c−1)/2对，列同理。两个不同方格不可能既同一行又同一列，所以行、列贡献可直接相加。',
        r'''int n; cin >> n; vector<int> row(n),column(n); for (int i=0;i<n;i++) for (int j=0;j<n;j++) { char c; cin >> c; if (c=='C') { row[i]++; column[j]++; } } long long answer=0; for (int c:row) answer+=1LL*c*(c-1)/2; for (int c:column) answer+=1LL*c*(c-1)/2; cout << answer;''',
        '只选含巧克力的两格，无序对需要除2。',
        complexity=r'时间 $O(n^2)$，空间 $O(n)$。')
    put(229269,1400,['排序','组合计数'],'正整数数组中乘积最小的三下标组数量。',
        '正数乘积最小的值组合必是排序后前三项。令第三小值x，前三项中严格小于x的元素必须全部选；剩余need个位置从所有等于x的元素中任选，答案C(countX,need)，need只可能1、2、3。无需计算可能溢出的乘积。',
        r'''int n; cin >> n; vector<long long> a(n); for (auto &x:a) cin >> x; sort(a.begin(),a.end()); long long x=a[2],before=lower_bound(a.begin(),a.end(),x)-a.begin(),count=upper_bound(a.begin(),a.end(),x)-lower_bound(a.begin(),a.end(),x),need=3-before,answer=1; for (int i=1;i<=need;i++) answer=answer*(count-i+1)/i; cout << answer;''',
        '不同下标算不同选择，重复数值要用组合数。所有数为正是取前三小值的前提。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(229271,1300,['组合数'],'选t名演员，至少4男、至少1女。',
        '枚举选男生人数b，从4到min(n,t−1)，女生人数t−b。贡献C(n,b)*C(m,t−b)，女生人数不合法时为0。人数不超过30，Pascal表及最终答案可用64位精确计算。',
        r'''int n,m,t; cin >> n >> m >> t; long long choose[31][31]={}; for (int i=0;i<=30;i++) { choose[i][0]=choose[i][i]=1; for (int j=1;j<i;j++) choose[i][j]=choose[i-1][j-1]+choose[i-1][j]; } long long answer=0; for (int boys=4;boys<=n && boys<t;boys++) { int girls=t-boys; if (girls<=m) answer+=choose[n][boys]*choose[m][girls]; } cout << answer;''',
        '至少1名女生，不允许boys=t。演员集合无顺序，不乘排列数。',
        complexity=r'时间 $O(30^2)$，空间 $O(30^2)$。')
    put(229273,1900,['组合数','二分图匹配计数'],'三类岛屿，同色两岛不能距离1或2，统计合法桥集合。',
        '同色岛之间不能直接连边。对任意两种颜色，其跨色边必须是匹配：若同一岛连接两个另一色岛，它们就距离2；反过来，距离2同色冲突也必然来自这种结构。因此三对颜色的匹配互相独立。\n\na、b两类选k条匹配，先各选k个端点，再任意双射，数量C(a,k)C(b,k)k!。定义F(a,b)为k=0..min(a,b)的和，答案F(a,b)*F(a,c)*F(b,c)。',
        r'''int a,b,c; cin >> a >> b >> c; Combinations comb(max({a,b,c})); auto match=[&](int x,int y) { long long sum=0; for (int k=0;k<=min(x,y);k++) sum=(sum+comb.choose(x,k)*comb.choose(y,k)%mod*comb.factorial[k])%mod; return sum; }; cout << match(a,b)*match(a,c)%mod*match(b,c)%mod;''',
        '允许距离3或更长的同色路径，因此不应强行让整个连通块只有一种或两种颜色。',
        declarations=FACTORIAL.replace('MODULUS','998244353'),complexity=r'时间 $O(a+b+c+\log P)$，空间 $O(\max(a,b,c))$。')
    put(229274,1700,['组合数','枚举数位和'],'只含a、b的n位数，其数位和也只含a、b，求数量。',
        '枚举a出现k次，b出现n−k次，数位和S=a*k+b*(n−k)。若S的每个十进制数码都为a或b，则任意选择k个位置放a都合法，贡献C(n,k)。预处理阶乘、逆阶乘，枚举k并检查S。',
        r'''int a,b,n; cin >> a >> b >> n; Combinations comb(n); long long answer=0; for (int k=0;k<=n;k++) { int sum=a*k+b*(n-k); bool good=true; do { int digit=sum%10; if (digit!=a && digit!=b) good=false; sum/=10; } while (sum); if (good) answer=(answer+comb.choose(n,k))%mod; } cout << answer;''',
        'a、b均非零，原数没有前导0问题。判断的是数位和的十进制表示，而非和只等于a或b。',
        declarations=FACTORIAL.replace('MODULUS','1000000007'),complexity=r'时间 $O(n\log(9n)+\log P)$，空间 $O(n)$。')
    put(229275,1900,['组合数','乘法原理'],'严格先增后减数组，恰有一对相等，求数量。',
        'n=2无法严格单峰且重复，答案0。n≥3时选n−1种不同值C(m,n−1)，最大值作为唯一峰值；重复值只能从其余n−2种选择，并在峰左右各放一次。剩下n−3个值各自任选放左或右，之后两侧顺序被严格单调性唯一确定。因此答案C(m,n−1)*(n−2)*2^(n−3)。',
        r'''int n,m; cin >> n >> m; if (n==2) { cout << 0; return 0; } Combinations comb(m); cout << comb.choose(m,n-1)*(n-2)%mod*power(2,n-3)%mod;''',
        '最大值不能重复，否则无法满足峰两侧的严格不等。相等的那一对分居峰两边。',
        declarations=FACTORIAL.replace('MODULUS','998244353'),complexity=r'时间 $O(m+\log P+\log n)$，空间 $O(m)$。')
    put(229276,2000,['多重集排列','枚举频次'],'每种已见数字实际至少一次、至多出现次数，不允许前导0，统计车号。',
        '对每种出现过的数字d，枚举实际次数1..count[d]；未出现数字次数只能0。固定次数c[d]、长度L时，排列数为L!/Πc[d]!。若c[0]>0，减去前导0固定后的(L−1)!/((c[0]−1)!*Π(d>0)c[d]!)。累加全部次数选择。\n\n输入长度至19，阶乘19!仍在64位范围内；可选频次组合数量由总位数限制，远小于10^19。',
        r'''string s; cin >> s; array<int,10> count={},chosen={}; for (char c:s) count[c-'0']++; unsigned long long factorial[20]; factorial[0]=1; for (int i=1;i<20;i++) factorial[i]=factorial[i-1]*i; unsigned long long answer=0; auto dfs=[&](auto &&self,int digit,int length)->void { if (digit==10) { unsigned long long all=factorial[length]; for (int c:chosen) all/=factorial[c]; if (chosen[0]) { unsigned long long bad=factorial[length-1]; for (int d=0;d<10;d++) bad/=factorial[chosen[d]-(d==0)]; all-=bad; } answer+=all; return; } int start=count[digit]?1:0; for (int c=start;c<=count[digit];c++) { chosen[digit]=c; self(self,digit+1,length+c); } }; dfs(dfs,0,0); cout << answer;''',
        '不能完全删掉任何一种已出现数码，包括0。重复数码不可区分，需除以各频次阶乘。',
        complexity=r'设频次组合数S=Π(max(1,count[d]))，时间 $O(10S)$，空间 $O(10+|s|)$。')
    put(228907,1700,['扩展欧几里得','线性同余方程'],'两只青蛙沿圆环同步跳，求首次同时相遇的步数。',
        '相遇条件x+m*t≡y+n*t(mod L)，即(m−n)t≡y−x。把系数和常数规范到0..L−1，令g=gcd(m−n,L)。若g不整除常数则无解；否则扩展欧几里得求系数的Bezout系数u，最小非负解为u*((y−x)/g) mod(L/g)。',
        r'''long long x,y,m,n,length; cin >> x >> y >> m >> n >> length; long long a=((m-n)%length+length)%length,b=((y-x)%length+length)%length,u,v,g=extendedGcd(a,length,u,v); if (b%g) cout << "Impossible"; else { long long period=length/g; cout << ((u*(b/g))%period+period)%period; }''',
        '速度差可以为负，要先规范余数。两青蛙同速而不同位置时判无解；位置在模L意义重合时0步合法。',
        declarations=EXGCD,complexity=r'时间 $O(\log L)$，空间 $O(\log L)$。')
    put(228908,1600,['素数筛','双指针'],'多组统计由连续素数之和组成n的方式。',
        '一次筛出所有不超过最大n的素数。每组对素数序列用双指针维护正数窗口和：向右扩展后，和>n就从左缩小；等于n时计一种。素数均正，每个端点只移动一次。',
        r'''int tests; cin >> tests; vector<int> query(tests); int maximum=0; for (int &n:query) { cin >> n; maximum=max(maximum,n); } auto primes=sieve(maximum); for (int n:query) { int left=0,answer=0; long long sum=0; for (int right=0;right<(int)primes.size() && primes[right]<=n;right++) { sum+=primes[right]; while (sum>n) sum-=primes[left++]; if (sum==n) answer++; } cout << answer << '\n'; }''',
        '连续指素数序列中连续，不是允许任意素数相加。单个素数本身也算一种。',
        declarations=SIEVE,complexity=r'预筛 $O(U\log\log U)$；各组 $O(\pi(n))$，空间 $O(U)$ 位加素数表。')
    put(228910,1800,['分段筛'],'在较大端点、较短区间内找最近和最远相邻素数对。',
        '先筛至sqrt(2^31−1)的素数。每组只开[R−L+1]标记，对每个p，从max(p²,ceil(L/p)*p)开始筛掉区间倍数；p²起步避免误删p自身。显式排除1，按升序扫描剩余素数并比较相邻距离。相等距离保持最先遇到者。',
        r'''auto primes=sieve(46341); int tests; cin >> tests; while (tests--) { long long l,r; cin >> l >> r; vector<bool> composite(r-l+1); for (long long p:primes) { if (p*p>r) break; for (long long x=max(p*p,(l+p-1)/p*p);x<=r;x+=p) composite[x-l]=true; } if (l==1) composite[0]=true; long long previous=-1,c1=-1,c2=-1,d1=-1,d2=-1,closest=LLONG_MAX,distant=-1; for (long long x=l;x<=r;x++) if (!composite[x-l]) { if (previous!=-1) { long long gap=x-previous; if (gap<closest) { closest=gap; c1=previous; c2=x; } if (gap>distant) { distant=gap; d1=previous; d2=x; } } previous=x; } if (c1==-1) cout << "There are no adjacent primes.\n"; else cout << c1 << ',' << c2 << " are closest, " << d1 << ',' << d2 << " are most distant.\n"; }''',
        '两端可能接近有符号32位上限，p²、起始倍数和扫描变量均用64位。',
        declarations=SIEVE,complexity=r'每组 $O((R-L+1)\log\log R+\sqrt R)$，空间 $O(R-L+\sqrt R)$。')
    put(228948,1400,['质因数分解'],'按素因子幂输入n，对n−1分解后降序输出。',
        'n≤30000，先用给定幂还原n，令remaining=n−1。试除全部不超过sqrt(remaining)的整数，每找到因子就除尽并记录指数；最后剩余值>1则是最后一个素因子。记录按升序生成，反向输出。',
        r'''int tests; cin >> tests; while (tests--) { int k; cin >> k; int n=1; while (k--) { int p,e; cin >> p >> e; while (e--) n*=p; } int remaining=n-1; vector<pair<int,int>> factors; for (int p=2;p*p<=remaining;p++) if (remaining%p==0) { int exponent=0; do { remaining/=p; exponent++; } while (remaining%p==0); factors.push_back({p,exponent}); } if (remaining>1) factors.push_back({remaining,1}); for (int i=(int)factors.size()-1;i>=0;i--) cout << factors[i].first << ' ' << factors[i].second << (i? ' ':'\n'); }''',
        '输出不包含因子个数k，直接输出素数、指数对；次序必须降序。',
        complexity=r'每组时间 $O(\sqrt n+\sum e_i)$，空间 $O(\log n)$。')
    put(228951,1700,['质因数分解','多重集排列'],'从1经严格整除链到x，求最多步数与最长链数量。',
        '每一步的倍数至少是一个素数，因此最多步数等于x质因子指数总和M，且每步恰乘一个素因子即可达到。最长链与这些质因子的排列一一对应，数量为M!/Πe[p]!。预处理百万内最小质因子，让每组快速分解。M≤19，阶乘用64位精确计算。',
        r'''const int limit=1000000; vector<int> smallest(limit+1); for (int p=2;p<=limit;p++) if (!smallest[p]) for (int x=p;x<=limit;x+=p) if (!smallest[x]) smallest[x]=p; unsigned long long factorial[21]; factorial[0]=1; for (int i=1;i<=20;i++) factorial[i]=factorial[i-1]*i; int tests; cin >> tests; while (tests--) { int x,total=0; cin >> x; vector<int> exponent; while (x>1) { int p=smallest[x],count=0; do { x/=p; count++; } while (x>1 && x%p==0); exponent.push_back(count); total+=count; } unsigned long long ways=factorial[total]; for (int e:exponent) ways/=factorial[e]; cout << total << ' ' << ways << '\n'; }''',
        '输出m是跳跃步数，链含m+1个数。相同素因子的交换不会产生新链。',
        complexity=r'预处理 $O(U\log\log U)$，每组 $O(\log x)$，空间 $O(U)$。')


if __name__ == '__main__': run()
