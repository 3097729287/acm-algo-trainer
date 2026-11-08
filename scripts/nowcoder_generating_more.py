"""Generating-function cancellation and linear recurrences."""
from nowcoder_editorials import CONTENT, add, read
from nowcoder_combinatorics_primes import FACTORIAL


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(230081,2100,['线性递推','多项式快速幂'],'长度1或m的宝石块恰占n空间，求方案数。',
        '按最后一块长度，f[n]=f[n−1]+f[n−m]，f[0..m−1]=1。对这个m阶递推，特征多项式给出x^m=x^(m−1)+1。计算x^n在此关系下的余式Σc[i]x^i，则f[n]=Σc[i]f[i]=Σc[i]。\n\n用二进制快速幂乘多项式：先普通卷积，再从高次往低次把x^j替换成x^(j−1)+x^(j−m)。每次O(m²)，优于100维稠密矩阵乘法。',
        r'''unsigned long long n; int m; cin >> n >> m; const long long mod=1000000007; auto multiply=[&](const vector<long long> &a,const vector<long long> &b) { vector<long long> c(2*m-1); for (int i=0;i<m;i++) for (int j=0;j<m;j++) c[i+j]=(c[i+j]+a[i]*b[j])%mod; for (int j=2*m-2;j>=m;j--) { c[j-1]=(c[j-1]+c[j])%mod; c[j-m]=(c[j-m]+c[j])%mod; } c.resize(m); return c; }; vector<long long> result(m),base(m); result[0]=1; base[1]=1; while (n) { if (n&1) result=multiply(result,base); n>>=1; if (n) base=multiply(base,base); } long long answer=0; for (auto x:result) answer=(answer+x)%mod; cout << answer;''',
        '普通宝石必须以完整m个块出现。多项式降幂从高到低，才能继续归约新产生的高次项。',
        complexity=r'时间 $O(m^2\log n)$，空间 $O(m)$。')
    put(207746,2000,['生成函数','组合数'],'八类物品不同数量限制，N可至10^18，求方案数。',
        '每类物品用允许数量的生成函数表示：两种最多1个给(1+x)²，最多2和3个给(1+x+x²)(1+x+x²+x³)，偶数鸡翅和奇数鸡汤给x/(1−x²)²，4倍数鸡块与3倍数鸡蛋给1/((1−x⁴)(1−x³))。\n\n用1+x=(1−x²)/(1−x)、1+x+x²=(1−x³)/(1−x)、1+x+x²+x³=(1−x⁴)/(1−x)，所有分子分母抵消后只剩x/(1−x)^4。N次系数为C(N+2,3)=N(N+1)(N+2)/6。模P下乘6的逆元。',
        r'''unsigned long long n; cin >> n; const long long mod=1000000007; long long x=n%mod; cout << x*((x+1)%mod)%mod*((x+2)%mod)%mod*166666668%mod;''',
        '鸡汤必须奇数，所以生成函数多一个x，结果不是C(N+3,3)。N很大，只对因子先取模。',
        complexity=r'时间、空间均 $O(1)$。')
    put(230894,2100,['容斥原理','隔板法'],'n种花各有上限f，恰选s朵的方案数。',
        '无上限时非负解数量为C(s+n−1,n−1)。对违反第i种上限的变量先减f[i]+1，再用容斥枚举违规集合S：贡献(-1)^|S|*C(s−Σ(f[i]+1)+n−1,n−1)，剩余量为负时贡献0。\n\n组合数上项可达10^14，但下项n−1≤19且小于模数，直接连乘上项起的n−1个因子，再乘(n−1)!逆元即可。这是整数多项式恒等式，允许上项大于模数，不必把整个阶乘预处理到上项。',
        r'''int n; long long s; cin >> n >> s; vector<long long> f(n); for (auto &x:f) cin >> x; long long factorial=1; for (int i=1;i<n;i++) factorial=factorial*i%mod; long long inverse=power(factorial,mod-2); int size=1<<n; vector<long long> removed(size); long long answer=0; for (int mask=0;mask<size;mask++) { if (mask) { int bit=__builtin_ctz((unsigned)mask); removed[mask]=removed[mask&(mask-1)]+f[bit]+1; } long long remaining=s-removed[mask]; if (remaining<0) continue; long long ways=inverse; for (int j=1;j<n;j++) ways=ways*((remaining+j)%mod)%mod; if (__builtin_popcount((unsigned)mask)&1) answer=(answer-ways+mod)%mod; else answer=(answer+ways)%mod; } cout << answer;''',
        '上限f允许取等号，违规时应平移f+1。n=1时组合式为空乘积1，容斥自动判是否超上限。',
        declarations=FACTORIAL.replace('MODULUS','1000000007'),complexity=r'时间 $O(n2^n+\log P)$，空间 $O(2^n+n)$。')
    put(230897,1800,['生成函数','奇偶投影'],'四种颜色长n序列，红绿数量均为偶数。',
        '对红、绿的次数分别用(1+(-1)^count)/2筛偶数，展开四项。代入每种颜色的权值，四个总权和分别为4、2、2、0，所以答案(4^n+2*2^n+0^n)/4。n≥1，最后一项为0，快速幂模10007，乘4逆元2502。',
        r'''int tests; cin >> tests; const long long mod=10007; auto power=[&](long long a,int n) { long long result=1; while (n) { if (n&1) result=result*a%mod; a=a*a%mod; n>>=1; } return result; }; while (tests--) { int n; cin >> n; cout << (power(4,n)+2*power(2,n))%mod*2502%mod << '\n'; }''',
        '两种颜色各自为偶数，比它们数量之和为偶数更严格。n=0不在输入范围内。',
        complexity=r'每组时间 $O(\log n)$，空间 $O(1)$。')
    put(205994,1900,['生成函数','线性递推'],'对递推数列的生成函数F，求F+F²+...的n次系数。',
        '原递推给出F(x)=x/(1−ax−bx²)。由于F常数项为0，形式幂级数的几何和为G=F/(1−F)=x/(1−(a+1)x−bx²)。因此所求系数直接满足g[0]=0、g[1]=1、g[n]=(a+1)g[n−1]+b*g[n−2]，线性滚动即可，无需实际卷积。',
        r'''int n; long long a,b; cin >> n >> a >> b; const long long mod=998244353; long long previous=0,current=1; for (int i=2;i<=n;i++) { long long next=((a+1)*current+b*previous)%mod; previous=current; current=next; } cout << current;''',
        '和从F¹开始，不包含常数1；新递推第一系数是a+1。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(232288,2200,['第二类Stirling数','贡献法','容斥原理'],'分成k个非空无序集合，权为每块大小乘块内权和，求全部划分权值和。',
        '固定一个元素i，其权w[i]在每个划分中乘所在块大小。块大小可写成1+Σ(j≠i)[j与i同块]。全部划分的第一项计S(n,k)次；对固定j，把i、j合并为一个元素，同块划分数为S(n−1,k)。故每个w的系数相同，为S(n,k)+(n−1)S(n−1,k)，乘总权值即可。\n\n使用S(N,k)=Σ(i=0..k)(−1)^(k−i)*i^N/(i!*(k−i)!)，两式合并成Σ符号*i^(n−1)*(i+n−1)/(i!*(k−i)!)，预处理逆阶乘，每项一次快速幂。',
        r'''int n,k; cin >> n >> k; long long sum=0; for (int i=0;i<n;i++) { long long x; cin >> x; sum=(sum+x)%mod; } Combinations comb(k); long long coefficient=0; for (int i=0;i<=k;i++) { long long term=power(i,n-1)*(i+n-1)%mod*comb.inverse[i]%mod*comb.inverse[k-i]%mod; if ((k-i)&1) coefficient=(coefficient-term+mod)%mod; else coefficient=(coefficient+term)%mod; } cout << coefficient*sum%mod;''',
        '集合块无编号，因此用第二类Stirling数，不能额外乘k!。n=1时0次幂按1，公式仍成立。',
        declarations=FACTORIAL.replace('MODULUS','1000000007'),complexity=r'时间 $O(n+k\log n+\log P)$，空间 $O(k)$。')
    put(229299,2300,['组合计数','字典序相邻排列'],'把n的全部排列按字典序连接，统计恰为1..m排列的连续窗口。',
        '窗口要么完全在一行n排列内，要么跨相邻两行的边界。行内把m个小数视为一个块，可任意排列m!，连同其余n−m个数共n−m+1个对象，所以行内数为m!*(n−m+1)!。\n\n边界先枚举来自上一行尾部的小数个数k，1≤k<m。理想形态是上一行“前部小数A、中部大数B、尾部小数C”，所有≤m的数刚好占据A和C；每个k有m!*(n−m)!种。若BC严格递减，next_permutation的进位会改动A，使对应边界失败。固定C长度k时，BC的次序已被降序唯一确定，A可从m个小数中选择并排列，坏情况为C(m,k)*(m−k)!=m!/k!。其余形态可按保持不变的A对应到唯一边界窗口。\n\n合计为m!*((n−m+1)!+(m−1)*(n−m)!−Σ(k=1..m−1)1/k!)，阶乘、逆阶乘及逆阶乘前缀和预处理后每问常数时间。\n\n推导核对：[CCPC 2021网络重赛官方题解，Subpermutation](https://codeforces.com/gym/103492/attachments/download/15254/CCPC2021%E7%BD%91%E7%BB%9C%E8%B5%9B%E9%87%8D%E8%B5%9B%20%E9%A2%98%E8%A7%A3.pdf)。',
        r'''const int limit=1000000; Combinations comb(limit); vector<long long> prefix(limit+1); for (int i=1;i<=limit;i++) prefix[i]=(prefix[i-1]+comb.inverse[i])%mod; int tests; cin >> tests; while (tests--) { int n,m; cin >> n >> m; long long inside=comb.factorial[n-m+1],boundary=(m-1)*comb.factorial[n-m]%mod; long long value=(inside+boundary-prefix[m-1]+mod)%mod; cout << comb.factorial[m]*value%mod << '\n'; }''',
        'm=1时没有跨行窗口，逆阶乘前缀和取0。不能把最后排列和第一排列再首尾相接。',
        declarations=FACTORIAL.replace('MODULUS','1000000007'),complexity=r'预处理 $O(U+\log P)$，每问 $O(1)$，空间 $O(U)$。')
    put(230527,1800,['状态枚举','递推消元'],'5×6翻灯，按自身和四邻翻转，求全部按键方案。',
        '枚举第一行6个按钮的64种按法。第一行按法确定后，上一行第j灯若仍亮，唯一还可改变它的未来按钮是下一行第j按钮，必须按下；若已灭就不能按。依次强制推出其余四行，最后检查第五行是否全灭，成功即输出。每个按钮按两次抵消，所以只需0/1选择。',
        r'''int tests; cin >> tests; cout << fixed; for (int tc=1;tc<=tests;tc++) { int original[5][6]; for (auto &row:original) for (int &x:row) cin >> x; int answer[5][6]={}; for (int mask=0;mask<64;mask++) { int light[5][6],press[5][6]={}; copy(&original[0][0],&original[0][0]+30,&light[0][0]); auto push=[&](int i,int j) { press[i][j]=1; const int di[]={0,0,0,-1,1},dj[]={0,-1,1,0,0}; for (int d=0;d<5;d++) { int x=i+di[d],y=j+dj[d]; if (x>=0 && x<5 && y>=0 && y<6) light[x][y]^=1; } }; for (int j=0;j<6;j++) if (mask>>j&1) push(0,j); for (int i=1;i<5;i++) for (int j=0;j<6;j++) if (light[i-1][j]) push(i,j); bool ok=true; for (int j=0;j<6;j++) if (light[4][j]) ok=false; if (ok) { copy(&press[0][0],&press[0][0]+30,&answer[0][0]); break; } } cout << "PUZZLE #" << tc << '\n'; for (auto &row:answer) for (int j=0;j<6;j++) cout << row[j] << (j==5?'\n':' '); }''',
        '输出的是按键矩阵，不是最终灯状态。按题目保证可解的固定规格处理。',
        complexity=r'每组时间 $O(2^6\cdot5\cdot6)$，空间 $O(5\cdot6)$。')


if __name__ == '__main__': run()
