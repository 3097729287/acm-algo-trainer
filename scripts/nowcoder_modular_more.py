"""Large decimal exponents, generalized CRT and multiplicative divisor sums."""
from nowcoder_editorials import CONTENT, add, read, reviewed_clone
from nowcoder_number_basics import EXGCD
from nowcoder_combinatorics_primes import FACTORIAL


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing: add(n,*args,**kwargs)
    put(229004,1500,['模逆元','线性递推'],'素数模p下求1到n全部逆元。',
        '写p=q*i+r，则r≡−q*i(mod p)，两边乘逆元得到inv[i]≡−q*inv[r]。由于r<i，可以从小到大递推inv[i]=(p−p/i)*inv[p%i] mod p，初值inv[1]=1。n<p且p为素数，所有需要的逆元都存在。',
        r'''int n,p; cin >> n >> p; vector<int> inverse(n+1); inverse[1]=1; for (int i=2;i<=n;i++) inverse[i]=1LL*(p-p/i)*inverse[p%i]%p; for (int i=1;i<=n;i++) cout << inverse[i] << '\n';''',
        '乘法用64位；inv[0]不代表有效逆元，素数条件与i<p保证递推不会真正依赖它。',
        complexity=r'时间、空间均 $O(n)$。')
    put(229014,1900,['等比数列','快速幂'],'周期正负号加权的a与b混合幂求和。',
        '令q=b/a mod P，先求第一周期B=a^n*Σ(i=0..k−1)s[i]q^i。往后每个周期整体乘r=q^k，共有blocks=(n+1)/k个周期。答案B*Σ(j=0..blocks−1)r^j；r=1时为B*blocks，否则为B*(r^blocks−1)/(r−1)。a<P且非零，可以求逆。',
        r'''long long n,a,b,k; string s; cin >> n >> a >> b >> k >> s; long long q=b*power(a,mod-2)%mod,term=power(a,n),block=0; for (int i=0;i<k;i++) { block=(block+(s[i]=='+'?term:mod-term))%mod; term=term*q%mod; } long long ratio=power(q,k),blocks=(n+1)/k,sum; if (ratio==1) sum=blocks%mod; else sum=(power(ratio,blocks)-1+mod)%mod*power((ratio-1+mod)%mod,mod-2)%mod; cout << block*sum%mod;''',
        '等比公比等于1时不能求(r−1)逆元。n+1恰为周期倍数，由题目保证。',
        declarations=FACTORIAL.replace('MODULUS','1000000009'),complexity=r'时间 $O(k+\log n+\log P)$，空间 $O(k)$ 存符号串。')
    put(229006,2100,['扩展中国剩余定理'],'模数可不互素的同余方程组，求最小非负解。',
        '维护已合并解x≡R(mod M)。加入x≡r(mod p)，令x=R+M*t，需M*t≡r−R(mod p)。g=gcd(M,p)，若g不整除差则无解；否则用扩展欧几里得系数u得到t=(r−R)/g*u mod(p/g)。新模数为M*(p/g)，新余数R+M*t再规范化。\n\n最终最小公倍数保证≤10^18，但求t的乘积与合并余数的中间值使用128位，防止先乘溢出。',
        r'''int n; cin >> n; long long remainder=0,period=1; bool possible=true; while (n--) { long long p,r; cin >> p >> r; if (!possible) continue; long long u,v,g=extendedGcd(period,p,u,v),delta=r-remainder; if (delta%g) { possible=false; continue; } long long reduced=p/g; long long step=(long long)(((__int128)(delta/g)*u%reduced+reduced)%reduced); long long nextPeriod=period*reduced; remainder=(long long)(((__int128)remainder+(__int128)period*step)%nextPeriod); period=nextPeriod; } cout << (possible?remainder:-1);''',
        '模数不互素不能套标准CRT直接相乘。输入余数即使等于模数，也可按同余自然处理。',
        declarations=EXGCD,complexity=r'时间 $O(n\log U)$，空间 $O(\log U)$。')
    put(229011,1500,['中国剩余定理'],'周期23、28、33的峰值，求给定日期后下一次共同峰值。',
        '三个周期互素，总周期M=21252。CRT中，M/23乘其模23逆元得到5544，另两个对应14421、1288，所以峰值日x=(5544p+14421e+1288i) mod M。距离为(x−d)规范到模M后，若为0则取M，因为题目排除当天。',
        r'''int tests; cin >> tests; const long long period=21252; while (tests--) { long long p,e,i,d; cin >> p >> e >> i >> d; long long answer=(5544*p+14421*e+1288*i-d)%period; if (answer<=0) answer+=period; cout << answer << '\n'; }''',
        '输出只要天数，没有原始POJ版本的Case前缀。三重峰恰在当天时，应等待一个完整周期。',
        complexity=r'每组时间、空间均 $O(1)$。')
    put(229015,2100,['十进制快速幂','大整数输入'],'b进制所有n位正整数装页，每页c个，求最后一页个数，b和n可有百万位。',
        '总数T=(b−1)*b^(n−1)，只需T mod c；余数为0时最后一页装满，应输出c。无需欧拉降幂，直接按十进制指数快速幂：若已有指数前缀e，再读一位d，则b^(10e+d)=(b^e)^10*b^d mod c。\n\n先将大字符串b逐位求模，将n字符串手工减1，预计算b^0..b^9，再扫描指数。每位仅常数次模乘，对合数c、b与c不互素都成立。',
        r'''string b,n; long long c; cin >> b >> n >> c; if (c==1) { cout << 1; return 0; } long long base=0; for (char d:b) base=(base*10+d-'0')%c; int p=n.size()-1; while (n[p]=='0') { n[p]='9'; p--; } n[p]--; long long small[10]; small[0]=1%c; for (int i=1;i<10;i++) small[i]=small[i-1]*base%c; long long result=1%c; for (char digit:n) { long long square=result*result%c,fourth=square*square%c,eighth=fourth*fourth%c; result=eighth*square%c*small[digit-'0']%c; } result=result*((base-1+c)%c)%c; cout << (result?result:c);''',
        '指数是n−1，不能直接用n。c可能为合数，按位幂避免了不满足互素条件的降幂错误。',
        complexity=r'时间 $O(|b|+|n|)$，空间 $O(|b|+|n|)$。')
    put(229623,2100,['莫比乌斯反演','动态计数'],'动态切换啤酒是否在架，统计互素无序对数。',
        '维护count[d]为架上a的d倍数个数。加入x时新增互素对数=Σ(d|x)mu(d)*count[d]，再把这些count[d]加1；移除时先减1，再减去相同表达式，避免把自身计入。只枚举x的不同质因子子集，得到所有无平方因子约数和mu符号；a≤500000最多6种不同质因子，每次至多64项。',
        r'''int n,q; cin >> n >> q; const int limit=500000; vector<int> smallest(limit+1); for (int p=2;p<=limit;p++) if (!smallest[p]) for (int x=p;x<=limit;x+=p) if (!smallest[x]) smallest[x]=p; vector<int> a(n); for (int &x:a) cin >> x; vector<bool> active(n); vector<int> count(limit+1); long long answer=0; while (q--) { int id; cin >> id; id--; int x=a[id]; vector<int> primes; while (x>1) { int p=smallest[x]; primes.push_back(p); while (x%p==0) x/=p; } vector<pair<int,int>> divisor={{1,1}}; for (int p:primes) { int size=divisor.size(); for (int i=0;i<size;i++) divisor.push_back({divisor[i].first*p,-divisor[i].second}); } if (active[id]) for (auto [d,mu]:divisor) count[d]--; long long change=0; for (auto [d,mu]:divisor) change+=1LL*mu*count[d]; if (active[id]) answer-=change; else { answer+=change; for (auto [d,mu]:divisor) count[d]++; } active[id]=!active[id]; cout << answer << '\n'; }''',
        '切换按啤酒编号而非泡沫值；同值不同啤酒仍是不同元素。x=1只有约数1，可与所有已有元素配对。',
        complexity=r'预处理 $O(U\log\log U)$，每次 $O(\log U+2^{\omega(x)})$，空间 $O(U+n)$。')
    put(229685,1900,['线性筛','约数个数'],'批量求千万内整数的约数个数。',
        'd(n)=Π(e[p]+1)。线性筛维护约数数d以及最小质因子的指数e。若p不整除i，d(i*p)=2d(i)、e=1；若p整除i，则最小质因子仍为p，d(i*p)=d(i)/(e(i)+1)*(e(i)+2)、e加1并停止。用d=0表示尚未筛到的素数，素数设d=2。指数用8位、约数数用16位，降低千万规模内存。',
        r'''int q; cin >> q; vector<int> query(q); int maximum=1; for (int &n:query) { cin >> n; maximum=max(maximum,n); } vector<uint16_t> count(maximum+1); vector<uint8_t> exponent(maximum+1); vector<int> primes; count[1]=1; for (int i=2;i<=maximum;i++) { if (!count[i]) { primes.push_back(i); count[i]=2; exponent[i]=1; } for (int p:primes) { long long next=1LL*i*p; if (next>maximum) break; if (i%p==0) { exponent[next]=exponent[i]+1; count[next]=count[i]/(exponent[i]+1)*(exponent[i]+2); break; } exponent[next]=1; count[next]=count[i]*2; } } for (int n:query) cout << count[n] << '\n';''',
        '1有一个正因数。千万内约数个数远低于65535，但不能把约数数也存8位。',
        complexity=r'时间 $O(U+q)$，空间 $O(U+\pi(U)+q)$，主要数组约3U字节。')
    put(14648,2200,['莫比乌斯反演','下标整除','频数统计'],'两个序列，统计gcd(x,y)=1且a[x]=b[y]的有序下标对。',
        '题面图片要求的是下标x、y互素，与数值互素不同。由[gcd(x,y)=1]=Σ(d|x,d|y)mu(d)，答案=Σ_d mu(d)*Σ_v countA[d][v]*countB[d][v]。\n\n固定d，只扫描d的倍数下标，把a值写入临时频次数组，再扫描b的对应下标累加相等数对。结束后再扫a的倍数下标清零，避免每个d清空整个值域。先线性筛mu，mu=0的d可跳过。',
        r'''int n; cin >> n; vector<int> a(n+1),b(n+1); for (int i=1;i<=n;i++) cin >> a[i]; for (int i=1;i<=n;i++) cin >> b[i]; vector<int> mu(n+1),primes; vector<bool> composite(n+1); mu[1]=1; for (int i=2;i<=n;i++) { if (!composite[i]) { primes.push_back(i); mu[i]=-1; } for (int p:primes) { if (1LL*i*p>n) break; composite[i*p]=true; if (i%p==0) break; mu[i*p]=-mu[i]; } } vector<int> count(n+1); long long answer=0; for (int d=1;d<=n;d++) if (mu[d]) { for (int i=d;i<=n;i+=d) count[a[i]]++; long long pairs=0; for (int i=d;i<=n;i+=d) pairs+=count[b[i]]; answer+=mu[d]*pairs; for (int i=d;i<=n;i+=d) count[a[i]]=0; } cout << answer;''',
        '原题全部文字嵌在图片中，已核对三张图：n≤10^5且a、b值均在1..n。样例n=3全1共7个互素有序对。',
        complexity=r'时间 $O(n\log n)$，空间 $O(n)$。')
    put(229748,1900,['欧拉函数','约数求和'],'求全部n元组的gcd之和，元素范围1..k。',
        '利用恒等式g=Σ(d|g)phi(d)，把每个元组gcd展开成约数和，交换求和顺序。能让全部元素被d整除的元组共有floor(k/d)^n个，故答案Σ(d=1..k)phi(d)*floor(k/d)^n。筛出phi，用快速幂求每项。',
        r'''int n,k; cin >> n >> k; const long long mod=1000000007; vector<int> phi(k+1); iota(phi.begin(),phi.end(),0); for (int p=2;p<=k;p++) if (phi[p]==p) for (int x=p;x<=k;x+=p) phi[x]=phi[x]/p*(p-1); long long answer=0; for (int d=1;d<=k;d++) { long long base=k/d,value=1; int exponent=n; while (exponent) { if (exponent&1) value=value*base%mod; base=base*base%mod; exponent>>=1; } answer=(answer+phi[d]*value)%mod; } cout << answer;''',
        '元组有顺序，允许重复，因此数量是幂，不是组合数。',
        complexity=r'时间 $O(k(\log\log k+\log n))$，空间 $O(k)$。')
    if 'nowcoder-global::230525' not in existing:
        reviewed_clone(230525,17877,'核对相同sin区间加规则、读入顺序和二十万界；新版要求误差1e-2，改为输出十位小数。',replacements={'setprecision(1)':'setprecision(10)'})
    put(17968,1700,['线性基'],'任意多次异或给定数，判断x能否变为y。',
        '重复异或相同元素两次抵消，所以问题等价于x xor y能否表示为给定数的子集异或。构造按最高位排列的二进制线性基；插入数时用已有同最高位向量消去，首次空位保存。查询也同样从高到低消去，最后归0则可表示。',
        r'''int n; cin >> n; array<unsigned,32> basis={}; for (int i=0;i<n;i++) { unsigned x; cin >> x; for (int bit=31;bit>=0 && x;bit--) if (x>>bit&1U) { if (basis[bit]) x^=basis[bit]; else { basis[bit]=x; break; } } } int q; cin >> q; while (q--) { unsigned x,y; cin >> x >> y; x^=y; for (int bit=31;bit>=0 && x;bit--) if (x>>bit&1U) x^=basis[bit]; cout << (!x?"YES\n":"NO\n"); }''',
        '值相同可以不做任何操作。unsigned保存位模式并安全处理第31位。',
        complexity=r'时间 $O(32(n+q))$，空间 $O(32)$。')
    put(230083,2100,['线性基','前缀异或'],'分成最多段，要求各段异或值线性无关。',
        '任意非空段集合异或都非0，等价于段异或向量线性无关。若总异或为0，选全部段就违反，直接−1。否则令前缀异或P[i]，段向量依次为P[t1]、P[t1]xorP[t2]、...，这是可逆三角变换，所以段向量的秩等于所选分界前缀向量的秩。\n\n全部前缀向量的秩r是上界。总前缀P[n]非0，在线性空间中它可以扩展为从所有前缀中选取的一组r个基向量；按下标排序后把n作为最后边界，便得到r个合法段。故答案为全部前缀异或的线性基秩。',
        r'''int n; cin >> n; unsigned prefix=0; array<unsigned,31> basis={}; int rank=0; while (n--) { unsigned x; cin >> x; prefix^=x; x=prefix; for (int b=30;b>=0 && x;b--) if (x>>b&1U) { if (basis[b]) x^=basis[b]; else { basis[b]=x; rank++; break; } } } cout << (!prefix?-1:rank);''',
        '插入的是每个前缀异或，不是原元素。总异或为0时，即使秩非0也无解。',
        complexity=r'时间 $O(31n)$，空间 $O(31)$。')


if __name__ == '__main__': run()
