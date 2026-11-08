"""Arbitrary-modulus counting series and a complete angle-event decision."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_geometry_support import GEOMETRY

NTT=r'''
constexpr int MOD=19260817;
int power(long long a,int e,int mod){long long answer=1;for(;e;e>>=1,a=a*a%mod)if(e&1)answer=answer*a%mod;return answer;}
void transform(vector<int> &a,bool inverse,int mod){
    int n=a.size();for(int i=1,j=0;i<n;i++){int bit=n>>1;for(;j&bit;bit>>=1)j^=bit;j^=bit;if(i<j)swap(a[i],a[j]);}
    for(int len=2;len<=n;len<<=1){int root=power(3,(mod-1)/len,mod);if(inverse)root=power(root,mod-2,mod);for(int i=0;i<n;i+=len){long long w=1;for(int j=0;j<len/2;j++,w=w*root%mod){int u=a[i+j],v=w*a[i+j+len/2]%mod;a[i+j]=u+v;if(a[i+j]>=mod)a[i+j]-=mod;a[i+j+len/2]=u-v;if(a[i+j+len/2]<0)a[i+j+len/2]+=mod;}}}
    if(inverse){int scale=power(n,mod-2,mod);for(int &x:a)x=(long long)x*scale%mod;}
}
vector<int> cyclicProduct(const vector<int> &a,const vector<int> &b,int n){
    const int p1=998244353,p2=1004535809,p3=469762049;
    vector<vector<int>> result;
    for(int mod:{p1,p2,p3}){vector<int> x(n),y(n);copy(a.begin(),a.end(),x.begin());copy(b.begin(),b.end(),y.begin());transform(x,false,mod);transform(y,false,mod);for(int i=0;i<n;i++)x[i]=(long long)x[i]*y[i]%mod;transform(x,true,mod);result.push_back(move(x));}
    static const int inverse12=power(p1,p2-2,p2),inverse123=power((long long)p1*p2%p3,p3-2,p3);
    vector<int> value(n);for(int i=0;i<n;i++){long long a1=result[0][i],a2=(result[1][i]-a1+p2)%p2*inverse12%p2,x=a1+(long long)p1*a2;long long a3=(result[2][i]-x%p3+p3)%p3*inverse123%p3;__int128 full=x+(__int128)p1*p2*a3;value[i]=full%MOD;}return value;
}
'''


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(17528,2300,['生成函数','CDQ分治','任意模数卷积'],'n种商品每种十万件，统计体积1到m的装载方案总数，模19260817。',
        r'm≤50000，每种十万件的上限不会用完，等价于完全背包。设体积d有c_d种不同商品，生成函数$F(x)=\prod_d(1-x^d)^{-c_d}$。对数求导得到$xF^\prime(x)=F(x)H(x)$，其中$H_i=\sum_{d\mid i}d\,c_d$。故$f_0=1,\quad f_i=i^{-1}\sum_{j=0}^{i-1}f_jH_{i-j}$。答案是f1到fm之和。'
        '\n\n用CDQ按下标求递推：先算完左半f，再把“左半f卷积H”的系数累加到右半待定和，最后递归右半。短区间直接转移。模数19260817不支持需要长度的NTT，分别在998244353、1004535809、469762049下卷积，再用三模CRT还原整数系数并对目标模数取模。三模乘积大于每次整数卷积可能的最大系数，128位足够承载CRT。'
        '\n\n实现把递归范围补成2的幂N，卷积只做长度N的循环卷积：左半多项式长度N/2，溢出到N以上的项只回绕到下标小于N/2的左半，不会污染需要的右半系数。这样每次只做N点NTT。超过m的叶子不再计算。',
        r'''int n,m;cin >> n >> m;int size=1;while(size<=m)size<<=1;vector<int> count(m+1),kernel(size),f(size),sum(size),inverse(size);for(int i=0;i<n;i++){int v;cin >> v;if(v<=m)count[v]++;}for(int d=1;d<=m;d++)if(count[d])for(int j=d;j<=m;j+=d)kernel[j]=(kernel[j]+(long long)d*count[d])%MOD;inverse[1]=1;for(int i=2;i<size;i++)inverse[i]=MOD-(long long)(MOD/i)*inverse[MOD%i]%MOD;f[0]=1;function<void(int,int)> solve=[&](int l,int r){if(l>m)return;if(r-l<=32){for(int i=l;i<min(r,m+1);i++){if(i)f[i]=(long long)sum[i]*inverse[i]%MOD;for(int j=i+1;j<min(r,m+1);j++)sum[j]=(sum[j]+(long long)f[i]*kernel[j-i])%MOD;}return;}int mid=(l+r)/2;solve(l,mid);vector<int> a(f.begin()+l,f.begin()+mid),b(kernel.begin(),kernel.begin()+r-l);auto product=cyclicProduct(a,b,r-l);for(int j=mid;j<min(r,m+1);j++){sum[j]+=product[j-l];if(sum[j]>=MOD)sum[j]-=MOD;}solve(mid,r);};solve(0,size);int answer=0;for(int i=1;i<=m;i++){answer+=f[i];if(answer>=MOD)answer-=MOD;}cout << answer;''',
        '同体积的不同商品仍是不同种类，必须用c_d指数计数。最终不含空方案f0。不能直接在19260817下套998244353的NTT根，也不能仅用两个NTT模数还原可能超过它们乘积的系数。',
        declarations=NTT,complexity=r'设N为大于m的最小2次幂，时间 $O(m\log m+N\log^2N)$，空间 $O(N+m)$。',
        cases=[{'name':'one unlimited type','input':'1 3\n1','output':'3'},{'name':'equal volume distinct types','input':'2 3\n1\n1','output':'9'}])
    put(232786,2300,['二分答案','角度事件','双指针'],'两条互相垂直且同宽的无限条带并成十字，求覆盖所有点的最小宽度。',
        '固定十字方向θ，将点投影成(u,v)。若第一条带覆盖按u排序的一段点，其他点必须能放进宽度w的v条带。枚举第一条带左端为某个点的u，用双指针扩展所有u≤左端+w的点；外部点的v最小最大值可由前缀、后缀极值得到，差≤w就可行。这一步O(n log n)。'
        '\n\n还需完整搜索连续方向，不能三分一个可能多峰的函数。固定候选宽度w后，方向变化时，任意点对能否同时放进u条带或v条带，只在投影差的绝对值等于w时改变。点对方向φ、长度d若d≥w，则事件为φ±acos(w/d)；方向对π/2取模自动同时包含v条带的事件，因为交换两条带不改变十字。'
        '\n\n将所有O(n²)个事件角加0和π/2排序，在每个相邻事件间取中点检查。区间内全部点对兼容关系不变，所以可行性不变；检查θ=0也覆盖端点情形。二分w至充分精度；若最优只在孤立角度取得，任意略大于最优的宽度都会产生可行角区间，因此仍可逼近正确答案。',
        r'''int n;cin >> n;vector<Point> p(n);for(auto &q:p)cin >> q.x >> q.y;const long double period=acosl(-1.0L)/2;auto directionWorks=[&](long double angle,long double width){vector<pair<long double,long double>> q;long double c=cosl(angle),s=sinl(angle);for(auto a:p)q.push_back({a.x*c+a.y*s,-a.x*s+a.y*c});sort(q.begin(),q.end());vector<long double> low(n+1,1e100L),high(n+1,-1e100L),suffixLow=low,suffixHigh=high;for(int i=0;i<n;i++){low[i+1]=min(low[i],q[i].second);high[i+1]=max(high[i],q[i].second);}for(int i=n-1;i>=0;i--){suffixLow[i]=min(suffixLow[i+1],q[i].second);suffixHigh[i]=max(suffixHigh[i+1],q[i].second);}int r=0;for(int l=0;l<n;l++){r=max(r,l);while(r<n && q[r].first-q[l].first<=width+1e-12L)r++;long double bottom=min(low[l],suffixLow[r]),top=max(high[l],suffixHigh[r]);if(top-bottom<=width+1e-12L)return true;}return false;};auto feasible=[&](long double width){vector<long double> event={0,period};auto normalized=[&](long double angle){angle=fmodl(angle,period);if(angle<0)angle+=period;return angle;};for(int i=0;i<n;i++)for(int j=0;j<i;j++){Point d=p[i]-p[j];long double length=norm(d);if(length<width)continue;long double base=atan2l(d.y,d.x),delta=acosl(clamp(width/length,-1.0L,1.0L));event.push_back(normalized(base+delta));event.push_back(normalized(base-delta));}sort(event.begin(),event.end());if(directionWorks(0,width))return true;for(int i=1;i<(int)event.size();i++)if(directionWorks((event[i-1]+event[i])/2,width))return true;return false;};long double l=0,r=30000;for(int i=0;i<55;i++){long double mid=(l+r)/2;if(feasible(mid))r=mid;else l=mid;}cout << fixed << setprecision(12) << r;''',
        '条带可以任意平移，不要求十字中心在某个输入点上。固定角度不能只用全体u、v跨度；应允许把点分给两条带。',
        declarations=GEOMETRY,floating_output=True,complexity=r'每次判定 $O(n^3\log n)$，共 $O(n^3\log n\log(C/\varepsilon))$ 时间，空间 $O(n^2)$。')


if __name__=='__main__':run()
