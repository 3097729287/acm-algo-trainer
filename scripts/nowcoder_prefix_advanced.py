"""Invertible prefix transformations, xor subset sums and polynomial differences."""
from nowcoder_editorials import CONTENT, add, read

MATRIX2 = r'''
constexpr long long mod=1000000007;
using Matrix=array<array<long long,2>,2>;
Matrix product(const Matrix &a,const Matrix &b) {
    Matrix c={{{0,0},{0,0}}};
    for (int i=0;i<2;i++) for (int j=0;j<2;j++) for (int k=0;k<2;k++)
        c[i][j]=(c[i][j]+a[i][k]*b[k][j])%mod;
    return c;
}
Matrix inverse(const Matrix &a) {
    return {{{a[1][1],(mod-a[0][1])%mod},{(mod-a[1][0])%mod,a[0][0]}}};
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(225632,1500,['前缀乘积','模逆元'],'正整数数组多次查询区间乘积模十亿加七。',
        '模数P为素数，且所有a[i]介于1和10^9，小于P，所以前缀乘积pref[i]始终非0。区间乘积=pref[r]*inv(pref[l−1])。只需对pref[n]做一次快速幂求逆，再按invPref[i−1]=invPref[i]*a[i]倒推全部前缀逆元。',
        r'''int n,m; cin >> n >> m; const long long mod=1000000007; vector<long long> a(n+1),prefix(n+1,1),inverse(n+1); for (int i=1;i<=n;i++) { cin >> a[i]; prefix[i]=prefix[i-1]*a[i]%mod; } long long base=prefix[n],exponent=mod-2,value=1; while (exponent) { if (exponent&1) value=value*base%mod; base=base*base%mod; exponent>>=1; } inverse[n]=value; for (int i=n;i>=1;i--) inverse[i-1]=inverse[i]*a[i]%mod; while (m--) { int l,r; cin >> l >> r; cout << prefix[r]*inverse[l-1]%mod << '\n'; }''',
        '模意义下不能直接整数除法。此方法依赖输入没有0，也没有模P的倍数。',
        complexity=r'时间 $O(n+m+\log P)$，空间 $O(n)$。')
    put(225630,1900,['按位计数','子集枚举'],'给集合U，求全部子集的异或价值和及全部超集的异或价值和。',
        '对子集按位统计：若U中该位至少有一个1，所有2^k个子集中恰一半异或为1。因此子集答案是OR(U)*2^(k−1)，空集答案0。\n\n超集等于固定U再任选补集V。设free=|V|、X=XOR(U)、B=OR(V)。B中为1的位有一半超集为1，贡献B*2^(free−1)；B中为0而X为1的位在全部超集中为1，贡献(X & ~B)*2^free。free=0时唯一超集是U，单独输出X。预处理每个掩码的OR，查询读编号后得到mask及X。',
        r'''int n,m; cin >> n >> m; vector<int> a(n); for (int &x:a) cin >> x; int size=1<<n; vector<int> bitOr(size); for (int mask=1;mask<size;mask++) { int bit=__builtin_ctz((unsigned)mask); bitOr[mask]=bitOr[mask&(mask-1)]|a[bit]; } while (m--) { int k,mask=0,xorValue=0; cin >> k; for (int i=0;i<k;i++) { int p; cin >> p; p--; mask|=1<<p; xorValue^=a[p]; } long long subset=k?(long long)bitOr[mask]*(1LL<<(k-1)):0; int free=n-k,b=bitOr[(size-1)^mask]; long long superset=free?(long long)b*(1LL<<(free-1))+(long long)(xorValue&~b)*(1LL<<free):xorValue; cout << subset << ' ' << superset << '\n'; }''',
        '集合含元素自身和空子集，超集含U自身。补集某位有可选1时才有“一半为1”，不能把固定U的异或值直接乘超集数。',
        complexity=r'预处理 $O(2^n)$，每问 $O(k)$，空间 $O(2^n+n)$。')
    put(223137,2000,['前缀矩阵','逆矩阵'],'两塔向上通行，每层一条定向跨塔楼梯，询问区间起终塔的路径数。',
        '用列向量[左方案数,右方案数]。字符/对应左→右，矩阵[[1,0],[1,1]]；反斜线对应右→左，矩阵[[1,1],[0,1]]。第i层转移左乘旧状态。令P[i]=A[i]*...*A[1]，查询从hs到ht的转移为P[ht−1]*inverse(P[hs−1])。\n\n每个基本矩阵行列式都是1，故所有前缀行列式仍为1。2×2逆矩阵直接为[[d,−b],[−c,a]]，不需求逆元。答案取转移矩阵[pt][ps]。',
        r'''int n,m; string s; cin >> n >> m >> s; Matrix identity={{{1,0},{0,1}}}; vector<Matrix> prefix(n); prefix[0]=identity; for (int i=1;i<n;i++) { Matrix step=identity; if (s[i-1]=='/') step[1][0]=1; else step[0][1]=1; prefix[i]=product(step,prefix[i-1]); } while (m--) { int hs,ht,ps,pt; cin >> hs >> ht >> ps >> pt; Matrix segment=product(prefix[ht-1],inverse(prefix[hs-1])); cout << segment[pt][ps] << '\n'; }''',
        '矩阵乘法不可交换，区间前缀逆矩阵要放右边。hs到ht恰好经过hs..ht−1层的楼梯。',
        declarations=MATRIX2,complexity=r'时间 $O(n+m)$，空间 $O(n)$，2×2乘法为常数。')
    put(212925,1800,['前缀置换','逆置换'],'十个杯子按给定区间的交换操作执行，恢复每杯球编号。',
        '保存P[i][j]为从初始状态执行前i次操作后，位置j中的球编号。交换两杯即交换这一行两个位置。若只执行[l,r]，其结果S满足P[r][j]=P[l−1][S[j]]，所以S[j]=inverse(P[l−1])[P[r][j]]。每问先构造十个元素的逆置换，再逐位置查表。',
        r'''int n,m; cin >> n >> m; vector<array<int,10>> prefix(n+1); iota(prefix[0].begin(),prefix[0].end(),0); for (int i=1;i<=n;i++) { int a,b; cin >> a >> b; prefix[i]=prefix[i-1]; swap(prefix[i][a],prefix[i][b]); } while (m--) { int l,r; cin >> l >> r; array<int,10> inverse; for (int j=0;j<10;j++) inverse[prefix[l-1][j]]=j; for (int j=0;j<10;j++) cout << inverse[prefix[r][j]] << (j==9?'\n':' '); }''',
        '操作交换的是杯子位置，不能把a、b当球编号。区间抵消使用逆置换，不能逐项相减。',
        complexity=r'时间 $O(10(n+m))$，空间 $O(10n)$。')
    put(201785,1300,['前缀统计','贡献法'],'所有标记1位置之间的无序距离和。',
        '从左向右遇到位置i为1时，它与之前所有1的距离和为count*i−sumPosition。将此值加入答案后，更新count与位置和。每对恰在右端点处理一次。',
        r'''int n; string s; cin >> n >> s; const long long mod=1000000007; long long count=0,position=0,answer=0; for (int i=0;i<n;i++) if (s[i]=='1') { answer=(answer+count*i-position)%mod; count++; position+=i; } cout << answer;''',
        '无序对只统计一次，不乘2。使用64位保存计数与位置乘积。',
        complexity=r'时间 $O(n)$，空间 $O(n)$ 存输入。')
    put(25090,1800,['多项式差分','前缀和'],'后缀分别加1、连续整数或连续平方，输出最终各点值。',
        '把每次贡献写成位置i的多项式。类型1为1；类型2为i+(1−pos)；类型3为i²+2(1−pos)i+(1−pos)²。每轮只从pos开始生效，所以在pos累加三个系数的差分，扫描i时累积当前系数A、B、C，答案即A*i²+B*i+C，模P计算。',
        r'''int tests; cin >> tests; const long long mod=1000000007; while (tests--) { int n,m; cin >> n >> m; vector<array<long long,3>> event(n+1); while (m--) { int type,pos; cin >> type >> pos; long long shift=1LL-pos; if (type==1) event[pos][0]++; else if (type==2) { event[pos][0]+=shift; event[pos][1]++; } else { event[pos][0]+=shift*shift; event[pos][1]+=2*shift; event[pos][2]++; } } array<long long,3> coefficient={0,0,0}; for (long long i=1;i<=n;i++) { for (int d=0;d<3;d++) coefficient[d]=(coefficient[d]+event[i][d])%mod; long long answer=(coefficient[2]*i%mod*i+coefficient[1]*i+coefficient[0])%mod; if (answer<0) answer+=mod; cout << answer << (i==n?'\n':' '); } }''',
        '每轮从pos处贡献1，不是pos或pos²，必须使用i−pos+1。负系数取模后最终规范到非负。',
        complexity=r'每组时间 $O(n+m)$，空间 $O(n)$。')
    for number,road in [(16534,False),(21466,True)]:
        put(number,1300,['差分','贪心'],'连续区间单位高度调整，求最少操作次数。',
            '从左到右看，每当当前高度h高于左邻prev，至少要从当前位置新开h−prev次操作；否则可以延续左边已有的层。所有上升差之和是下界，也能通过逐层延续区间实现。令最左外侧高度为0，答案Σmax(0,h[i]−h[i−1])。' + ('道路填坑可把方案反向看成从零堆出原深度，最少次数相同。' if road else ''),
            r'''int n; cin >> n; long long previous=0,answer=0; while (n--) { long long h; cin >> h; answer+=max(0LL,h-previous); previous=h; } cout << answer;''',
            '下降时不增加操作，也不从答案扣除。把初始左邻设为0，避免漏掉第一段。',
            complexity=r'时间 $O(n)$，空间 $O(1)$。')


if __name__ == '__main__': run()
