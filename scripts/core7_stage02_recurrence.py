"""Explicitly authored recurrence, recursion and divide-and-conquer methods."""
from core7_authoring import add

A=['io-basics','arrays','vector','basic-control','functions']
F=A+['fenwick','integer']
R=A+['recursion']

add('P2345','按听力排序，用两棵树状数组累计距离',
    '每对奶牛的交流音量是两者听力较大值乘坐标距离，求全部无序奶牛对的音量之和。',
    r'''按听力从小到大处理，当前奶牛与此前奶牛配对时，较大听力就是当前 v。用两棵按坐标维护的树状数组分别统计数量和坐标和。当前坐标 x 左边的距离和是 x×左边数量−左边坐标和，右边反过来算；两者相加乘 v，再插入当前奶牛。每一对只在较晚处理的一头处计算一次。''',
    r'''先看一头坐标为五、听力为四的奶牛。若已经处理的坐标为一、三、六，则距离和是 (5−1)+(5−3)+(6−5)=7，它们与当前奶牛的交流贡献为 4×7=28。前提是此前听力都不大于四，这正是先按听力升序排序的作用。

不能为每头奶牛重新遍历此前所有位置。把此前奶牛分为坐标不大于 x 的左组与其余右组。左组有 L 头，坐标和为 S，则距离和为 Lx−S：每头各贡献一个 x，再减去自己的坐标。若总共处理 T 头、总坐标和为 U，右组有 T−L 头、坐标和 U−S，距离和为 (U−S)−(T−L)x。

两棵树状数组的同一个下标表示同一个坐标，一棵每次加一，另一棵加坐标值。查询前缀 x 就得到 L 和 S；总量 T、U 单独保存。必须先查询再插入，避免把当前奶牛当成此前对象。坐标相等时距离本来为零，公式也成立；题目实际上保证不同坐标。

任何一对都有唯一的较晚处理者，在这一轮恰好计入。听力相等时排序先后任意，因为较大听力仍是同一个值。距离和、听力乘积和最终总和都用 long long，不能让乘法先在 int 中溢出。''',
    r'''int n;cin>>n;vector<pair<int,int>>cows(n);
for(auto &cow:cows)cin>>cow.first>>cow.second;
sort(cows.begin(),cows.end());BIT counts(20000),positions(20000);
long long processed=0,total_x=0,answer=0;
for(auto cow:cows){
    long long v=cow.first,x=cow.second;
    long long left_count=counts.sum((int)x),left_sum=positions.sum((int)x);
    long long distance=x*left_count-left_sum+(total_x-left_sum)-x*(processed-left_count);
    answer+=v*distance; // 此时 v 不小于此前任意奶牛的听力
    counts.add((int)x,1);positions.add((int)x,x);++processed;total_x+=x;
}
cout<<answer<<'\n';''',
    '听力决定处理顺序，坐标决定树状数组下标。每对计一次，不额外乘二。',
    r'坐标上限为 M=20000，时间 $O(n\log n+n\log M)$、空间 $O(n+M)$。',
    tags=['排序','树状数组'],lessons=F+['sort','iterators'],
    declarations=r'''struct BIT{
    int n;vector<long long>tree;
    BIT(int size):n(size),tree(size+1){}
    void add(int i,long long value){for(;i<=n;i+=i&-i)tree[i]+=value;}
    long long sum(int i)const{long long result=0;for(;i>0;i-=i&-i)result+=tree[i];return result;}
};''')

add('P1002','在固定禁行点之外逐格累计路径数',
    '卒从 (0,0) 只向两个坐标增大的方向走到 (n,m)，马的位置及其八个攻击点禁止经过，求路径数。',
    r'''先标记马自己及八个日字跳跃终点。令 f[x][y] 表示走到该点的路径数：禁行点为零，其余点的路径来自 (x−1,y) 与 (x,y−1)，所以相加。起点设一，从小坐标向大坐标遍历。''',
    r'''马始终不移动，故先把它所在点以及八个攻击点一次性标出来。这里控制的是九个点，不是一整行或一整列；落在目标矩形以外的攻击点无需保存，也不影响矩形内的走法。

对于可走的 (x,y)，最后一步只能来自左边的 (x−1,y)，或者来自上边的 (x,y−1)。两类路径的最后一步不同，不会重复，而且题目允许的最后一步只有这两类，所以

$$f[x][y]=f[x-1][y]+f[x][y-1].$$

超出边界的来源视为零。起点的一个空走法必须单独设 f[0][0]=1，否则全部状态都会保持零。按 x、y 从小到大计算时，两种来源都已算好。禁行点保持零，不再从其邻点转移，便自动阻断了所有经过它的路径。

例如 (2,2) 的马还控制 (0,1)、(1,0) 等位置，因此从原点甚至无法迈出第一步，答案为零；不能只屏蔽马所在格。题目保证起点不受控制，代码仍明确先判断禁行，边界规则统一。最大无障碍路径数为组合数 C(40,20)，超过 int，用 long long。''',
    r'''int n,m,hx,hy;cin>>n>>m>>hx>>hy;bool blocked[21][21]={};
int dx[9]={0,1,1,-1,-1,2,2,-2,-2};int dy[9]={0,2,-2,2,-2,1,-1,1,-1};
for(int i=0;i<9;++i){int x=hx+dx[i],y=hy+dy[i];if(0<=x&&x<=n&&0<=y&&y<=m)blocked[x][y]=true;}
long long f[21][21]={};
for(int x=0;x<=n;++x)for(int y=0;y<=m;++y){
    if(blocked[x][y])continue;
    if(x==0&&y==0){f[x][y]=1;continue;} // 原点有一个空走法
    if(x>0)f[x][y]+=f[x-1][y];if(y>0)f[x][y]+=f[x][y-1];
}
cout<<f[n][m]<<'\n';''',
    '马自己也禁行；不考虑蹩马腿或马随卒移动。答案用 long long。',
    '时间与状态空间均为 $O((n+1)(m+1))$。',tags=['线性 DP','递推'],lessons=A+['dp','integer'])

add('P1010','二进制分解后递归表示指数',
    '把正整数按二的幂从大到小展开，指数也用同样规则展开，只有零和二作为数字出现。',
    r'''从高位到低位枚举 n 的一位，位号 k 对应 2 的 k 次方。k=0 输出 2(0)，k=1 直接输出 2，其余输出 2(表示(k))。不同幂项之间加加号，指数 k 通过同一个函数递归生成。''',
    r'''以十三为例，二进制是 1101，故十三等于 2³+2²+2⁰。第三次幂的指数三仍需展开成 2+2(0)，第二次幂的指数二表示为 2，于是整体为 `2(2+2(0))+2(2)+2(0)`。

定义 print_number(x) 只负责输出 x 的标准表示。逐位从大到小找一，保证幂项顺序。零次幂与一次幂是两个特殊拼写：前者是 2(0)，后者必须简写为 2，不能输出 2(2(0))。其它位号 k≥2 时，先写 2(，再调用 print_number(k)，最后写右括号。

递归参数从 x 变为不超过 log₂x 的位号，因此会很快降到特殊情况，不会无限递归。每层自己的 first 变量只管理这一层幂项之间的加号，子调用不会破坏外层分隔。输入至多两万，只需检查第十四位到第零位。''',
    r'''int n;cin>>n;print_number(n);cout<<'\n';''',
    '指数一只输出 2；不同层的加号各自管理；结果中不能插入空格。',
    r'本范围每次调用检查固定的十五个位，时间 $O(L)$（L 为输出长度），调用栈为迭代对数级，输出直接写流。',
    tags=['递归','位运算'],lessons=R+['bitwise'],exact=True,
    declarations=r'''void print_number(int x){
    bool first=true;
    for(int k=14;k>=0;--k)if((x>>k)&1){
        if(!first)cout<<'+';first=false;
        if(k==0)cout<<"2(0)";
        else if(k==1)cout<<'2';
        else{cout<<"2(";print_number(k);cout<<')';}
    }
}''')

add('P1044','按元素一被弹出的位置拆分两段',
    '数字一到 n 依次入栈，可以随时弹出栈顶，求不同合法出栈序列的数量。',
    r'''令 f[t] 为 t 个连续递增数字的合法出栈序列数，f[0]=1。若一之前弹出了 k 个数字，它们恰是二到 k+1；一弹出后，剩下 n−1−k 个独立处理。枚举 k，相乘再求和：f[n]=Σf[k]f[n−1−k]。''',
    r'''看 n=3：若一最先弹出，后面的二、三有两种顺序；若一第二个弹出，前面只能是二，后面只能是三，有一种；若一最后弹出，二、三在一上方有两种合法顺序。合计 2+1+2=5。

一般地，设一弹出前已经输出 k 个数字。为了弹出一，栈里位于一上面的数字必须全部弹出，而输入按递增次序推进，因此这些数字恰是 2 到 k+1，不能跳过中间某个数。它们只需在一上方完成一次规模 k 的栈问题，有 f[k] 种。

随后弹出一，剩余尚未入栈的 k+2 到 n 形成规模 n−1−k 的同类问题，有 f[n−1−k] 种。前后选择可以任意配对，故乘起来；不同 k 对应一在输出中的不同位置，互不重复，故再求和。空的一段有一种什么也不做的方式，必须定义 f[0]=1。

从小规模向大规模递推，各项都已存在。元素标签的整体加一不影响出栈模式，因此状态只需记数量。答案也叫卡特兰数，但实现不依赖记忆其闭式公式或模逆元。''',
    r'''int n;cin>>n;vector<long long>f(n+1);f[0]=1;
for(int size=1;size<=n;++size)
    for(int before=0;before<size;++before)
        f[size]+=f[before]*f[size-1-before];
cout<<f[n]<<'\n';''',
    '空段贡献一，不是零；两段长度之和是 n−1，已扣除元素一。',
    '时间 $O(n^2)$、空间 $O(n)$。',tags=['递推','组合计数'],lessons=A+['queue-stack','counting','dp','integer'])

add('P1226','按二进制位选择平方得到的幂',
    '计算 a 的 b 次方对 p 取余，并按题目规定保留原始参数输出整个等式。',
    r'''维护 result=1、base=a mod p。指数当前最低位为一时将 base 乘入 result；每轮把 base 平方取模、指数除二。这样按二进制位选出需要的 a¹、a²、a⁴……，只做对数轮。''',
    r'''例如指数十的二进制是 1010，只需 a⁸ 与 a²。起初 base=a，对应最低位；指数每次除二，base 就平方一次，依次变为 a²、a⁴、a⁸。遇到对应位为一时才乘入答案。

更严格地说，原始目标与 result×base^e 始终同余。若 e 为奇数，先把一个 base 乘入 result，再把其余偶数个 base 两两合成 base²；若 e 为偶数，直接两两合成。令 e 除二，等式保持。最终 e=0，余下因子为一，result 就是所求。

乘法取余可以在每一步做，但乘法本身仍须用足够宽的类型。p<2³¹，两份小于 p 的余数相乘小于 2⁶²，用 long long 安全。b=0 时循环不执行，答案为一；此时题目条件保证 a>0。a、b 不能在运算中被改掉，因为等式左边仍需输出原值，故另用 base、e。''',
    r'''long long a,b,p;cin>>a>>b>>p;long long base=a%p,e=b,result=1;
while(e>0){
    if(e&1)result=result*base%p; // 当前二进制位为一才选择该幂
    base=base*base%p;e>>=1;
}
cout<<a<<'^'<<b<<" mod "<<p<<'='<<result<<'\n';''',
    '不能先用 int 相乘再赋 long long；输出原始 a、b，不输出循环结束后的指数。',
    r'时间 $O(\log(b+1))$、额外空间 $O(1)$。',tags=['快速幂','位运算'],lessons=['io-basics','basic-control','integer','bitwise','modular'],exact=True)

add('P1464','记忆化保存二十一立方个小状态',
    '按题面给定的分段递归函数 w 回答多组查询，保持条件判断顺序及规定输出格式。',
    r'''先判断任一参数不大于零，直接返回一；否则若任一参数大于二十，转为 w(20,20,20)。其余状态只有二十一立方个，用数组缓存，再照原公式递归。各查询共享缓存，但输出仍使用原始参数。''',
    r'''一次 w(15,15,15) 的朴素递归会反复求相同状态。函数值只由三个参数决定，因此第一次求出某个小状态后存起来，以后直接读取，不再展开它的整棵调用树。

先处理边界再访问缓存很关键。输入可达整个 signed long long 范围，不能直接拿输入作下标，也不能先对极小值减一。任一参数≤0 时立即返回一；只有三个都为正，才考虑是否有参数超过二十。比如 w(30,−1,0) 必须返回一，若先处理超二十就会错。

进入缓存部分时，三个参数都在一到二十，才可安全用 memo[a][b][c]。另用 seen 区分“未算过”与“恰好算得零”，不依赖函数值是否为零。若 a<b<c，使用题面的三项式，否则使用四项式；每项都减少参数，递归最终到边界，缓存不会形成循环。

缓存跨查询保留，故全部查询共只展开至多 20³ 个正状态。输入恰为三个负一才结束，单个参数为负一仍是需要输出的普通查询。打印时保留原始的 a、b、c，包括逗号和空格。''',
    r'''long long a,b,c;
while(cin>>a>>b>>c){
    if(a==-1&&b==-1&&c==-1)break;
    cout<<"w("<<a<<", "<<b<<", "<<c<<") = "<<w(a,b,c)<<'\n';
}''',
    '负参数判定先于超二十；只有三个参数同时为负一才是终止符。',
    'T 组询问总时间 $O(20^3+T)$、缓存空间 $O(20^3)$，递归深度有常数上界。',
    tags=['记忆化搜索','递归'],lessons=R+['integer'],exact=True,
    declarations=r'''long long memo[21][21][21];bool seen[21][21][21];
long long w(long long a,long long b,long long c){
    if(a<=0||b<=0||c<=0)return 1;
    if(a>20||b>20||c>20)return w(20,20,20);
    if(seen[a][b][c])return memo[a][b][c];
    long long result;
    if(a<b&&b<c)result=w(a,b,c-1)+w(a,b-1,c-1)-w(a,b-1,c);
    else result=w(a-1,b,c)+w(a-1,b-1,c)+w(a-1,b,c-1)-w(a-1,b-1,c-1);
    seen[a][b][c]=true;return memo[a][b][c]=result;
}''')

add('P2437','按最后一步递推，用十进制字符串相加',
    '蜂房按交错两行编号，只能走向较大编号的相邻蜂房，求从 m 到 n 的路线数。',
    r'''从蜂房 i 可以向较大编号 i+1 或 i+2 移动。把起点平移成零，f[0]=f[1]=1，f[d]=f[d−1]+f[d−2]，答案为 f[n−m]。结果超过机器整数，用字符串逐位相加并进位。''',
    r'''沿原图的六边形边界看相邻关系：一个蜂房向编号较大的一侧只有两个相邻点，分别是加一与加二。相差三的蜂房没有公共边，不能一步过去。右端图片的上方标签按题面备注应为 n−1，不影响这一局部关系。

从 m 到 m 的空路线有一种，到 m+1 只有直接一步这一种。到 m+d 的最后一步，要么从 m+d−1 加一，要么从 m+d−2 加二，两类按最后一步区分，故 f[d]=f[d−1]+f[d−2]。例如距离三的路线是 1+1+1、1+2、2+1，共三种，不是无序地选若干步。

n 可达一千，答案有两百多位，long long 会溢出。用普通从左到右的十进制字符串保存每项，相加时指针从末位往前走。每轮取两个当前数字与 carry，相加后个位追加到结果末尾、十位成为新 carry；最后把逆序的结果反转。`'0'` 与字符相减才能得到数字值。

递推只依赖前两项，用 a、b 滚动保存，先生成 next，再同时前移，避免覆盖还要使用的项。结果字符串和普通机器整数有不同表示，不可直接用字符串的加号当数值加法。''',
    r'''int m,n;cin>>m>>n;string a="1",b="1";
for(int d=2;d<=n-m;++d){string next=plus_decimal(a,b);a=b;b=next;}
cout<<b<<'\n';''',
    '距离是 n−m；字符串加号是拼接，要自己逐位进位相加。',
    '设 d=n−m、答案位数为 L，时间 $O(dL)$、额外空间 $O(L)$。',
    tags=['递推','高精度'],lessons=R+['strings','decimal-addition'],exact=True,
    declarations=r'''string plus_decimal(const string &a,const string &b){
    int i=(int)a.size()-1,j=(int)b.size()-1,carry=0;string result;
    while(i>=0||j>=0||carry){
        int value=carry;if(i>=0)value+=a[i--]-'0';if(j>=0)value+=b[j--]-'0';
        result.push_back(char('0'+value%10));carry=value/10;
    }
    reverse(result.begin(),result.end());return result;
}''')

add('CF873B','把零变为负一，寻找最远的相同前缀和',
    '在只含零、一的字符串中，求零与一个数相同的最长连续子串长度，无非空答案则输出零。',
    r'''把一记为 +1、零记为 −1。子串平衡等价于两端前缀和相同。扫描到前缀位置 i 时，若该和值曾出现，使用最早位置 j 更新 i−j；否则记录当前位置。空前缀和值零的位置是零，也要先登记。''',
    r'''对样例 11010111，前缀和依次是 0,1,2,1,2,1,2,3,4。和值一最早在前缀一出现，之后在前缀五重现，差四；对应原串第二到第五个字符 1010，零和一各两个。

令 S[i] 为前 i 个字符的转换和值。原串第 j+1 到 i 段的和值是 S[i]−S[j]，为零当且仅当 S[i]=S[j]。因此每到 i，只需找此前同和值的位置。固定右端点 i，j 越小区间越长，所以每个和值只保存第一次出现位置；反复改成最近位置反而会丢掉最优解。

S[i] 在 −n 到 n 之间，可以加 n 平移成数组下标，不需要哈希表。用 −1 表示尚未出现；零前缀先设置为位置零，便能找到从第一个字符起的平衡子串。若没有重复和值，答案保持零。''',
    r'''int n;string s;cin>>n>>s;vector<int>first(2*n+1,-1);int sum=0,answer=0;first[n]=0;
for(int i=1;i<=n;++i){
    sum+=s[i-1]=='1'?1:-1;int at=sum+n;
    if(first[at]==-1)first[at]=i;else answer=max(answer,i-first[at]);
}
cout<<answer<<'\n';''',
    '保存最早位置；下标先平移 n；初始空前缀不能遗漏。',
    '时间、空间均为 $O(n)$。',tags=['前缀和'],lessons=A+['prefix'])

add('P1257','横坐标分治，按纵坐标扫描窄条',
    '给定整数坐标的平面点，求任意两点间最短欧几里得距离，四舍五入保留四位小数。',
    r'''先按 x 排序并二分点集，递归求左右最短平方距离 best。跨分界线的更近点对只能在距中线小于 √best 的窄条内；把窄条按 y 排好，每个点只向前检查纵距仍小于 √best 的点。递归返回时同时把本段整理成 y 有序，合并即线性，总时间 O(n log n)。''',
    r'''把按横坐标排好的点分成左右两组。任意最接近点对，要么完全在左组，要么完全在右组，要么一左一右。前两类交给递归，得到距离下界候选 δ；合并时只需寻找距离小于 δ 的跨组点对。

若两点横跨中线且相距小于 δ，则每个点与中线的水平距离都小于 δ。因此只保留中线左右宽 δ 的窄条。按 y 从小到大处理窄条点，当前点只需和此前纵向差小于 δ 的点比较，纵向差已经达到 δ 后，再往前的点更远，可以停止。

为何这不是又一个平方枚举？固定一个点，待比较点位于宽 2δ、高 δ 的矩形内。左右每一侧内部的任意两点距离都至少为 δ，因为左右递归已经求过最小值。把每侧 δ×δ 矩形各分成四个边长 δ/2 的小格，同一侧同一小格内两点距离小于 δ，不可能同时存在。因此这个矩形每侧至多四个点，总共常数个候选。中线重合的点仍按原分组计算，不影响上述界。若发现距离零，已不可能更好，合并完成后直接返回零。

实现维护一个额外约定：一次递归进入时本段仍按 x 有序，返回时本段按 y 有序。先保存中点横坐标，再分别递归；两段返回后用双指针归并 y 坐标，随后线性筛出窄条。若每层另排序 y，会多出一个对数因子。叶段不超过三个点，暴力检查后按 y 排好。

所有比较使用平方距离，坐标差先用 long long，最大平方和 2×10¹⁸ 安全。最后为严格满足四位舍入，用整数处理输出：令 S=best×10⁸，二分求 q=⌊√S⌋；比较 4S 与 (2q+1)²，判断 √S 是否至少 q+1/2，若是则 q 加一。q 的整数与小数部分分别为 q/10000 和 q%10000。S 及比较乘积用 GCC 的 __int128，避免在大坐标下开方舍入丢掉最后一位。该输出辅助只需固定约四十五轮，主体仍是点集分治。''',
    r'''int n;cin>>n;points.resize(n);buffer.resize(n);
for(auto &p:points)cin>>p.x>>p.y;
sort(points.begin(),points.end(),less_x);long long best=closest(0,n);
// 精确地将 sqrt(best) 四舍五入到万分之一
__int128 scaled=(__int128)best*100000000;long long lo=0,hi=20000000000000LL;
while(lo<hi){long long mid=lo+(hi-lo+1)/2;if((__int128)mid*mid<=scaled)lo=mid;else hi=mid-1;}
long long rounded=lo;__int128 odd=(__int128)2*lo+1;
if(4*scaled>=odd*odd)++rounded;
cout<<rounded/10000<<'.'<<setw(4)<<setfill('0')<<rounded%10000<<'\n';''',
    '必须先保存分界横坐标再递归；重复点答案为零；先升为 long long 再平方。',
    r'时间 $O(n\log n)$、辅助数组与窄条空间 $O(n)$，递归栈 $O(\log n)$。',
    tags=['分治','计算几何','排序'],lessons=R+['structures','sort','iterators','geometry','integer','bounds'],exact=True,
    declarations=r'''struct Point{long long x,y;};vector<Point>points,buffer;
bool less_x(const Point&a,const Point&b){return a.x!=b.x?a.x<b.x:a.y<b.y;}
bool less_y(const Point&a,const Point&b){return a.y!=b.y?a.y<b.y:a.x<b.x;}
long long distance2(const Point&a,const Point&b){long long dx=a.x-b.x,dy=a.y-b.y;return dx*dx+dy*dy;}
long long closest(int l,int r){
    if(r-l<=3){
        long long best=LLONG_MAX;
        for(int i=l;i<r;++i)for(int j=i+1;j<r;++j)best=min(best,distance2(points[i],points[j]));
        sort(points.begin()+l,points.begin()+r,less_y);return best;
    }
    int mid=(l+r)/2;long long split_x=points[mid].x; // 子调用将改变排列，先保存中线
    long long best=min(closest(l,mid),closest(mid,r));
    int i=l,j=mid,k=l;
    while(i<mid&&j<r)buffer[k++]=less_y(points[i],points[j])?points[i++]:points[j++];
    while(i<mid)buffer[k++]=points[i++];while(j<r)buffer[k++]=points[j++];
    for(i=l;i<r;++i)points[i]=buffer[i];
    if(best==0)return 0;
    vector<Point>strip;
    for(i=l;i<r;++i){long long dx=points[i].x-split_x;if(dx*dx<best)strip.push_back(points[i]);}
    for(i=0;i<(int)strip.size();++i)for(j=i-1;j>=0;--j){
        long long dy=strip[i].y-strip[j].y;if(dy*dy>=best)break;
        best=min(best,distance2(strip[i],strip[j]));
    }
    return best;
}''')

add('P1228','用一块中心地毯制造四个同类子问题',
    '用四种方向的三格 L 形地毯，恰好覆盖 2^k 阶正方形中除指定公主格之外的所有格子，输出每块地毯的拐角和方向。',
    r'''把棋盘分成四个等大象限。公主所在象限保留真实缺格，其它三个象限各取靠中心的一格，用一块 L 形地毯同时覆盖。于是每个象限都有一个禁止再次覆盖的格，再递归铺满。边长一时无需输出。''',
    r'''单个 2×2 棋盘缺一格时，剩下三格恰是一块 L 形地毯。大棋盘也尽量化成这种问题：先分四个象限，其中只有一个象限含公主，另三个暂时没有缺格。

在棋盘中心的 2×2 区域，避开公主所在的那个象限，覆盖另外三格。这样没有公主的三个象限，各自有一格已被中心毯占用；以后将该格视为不能再盖的“人工缺格”。含公主的象限仍使用真实公主格。四个子棋盘于是都满足“正方形恰有一个缺格”，可以调用同一过程。

中心毯在三个象限各占一格，子问题绝不再盖其缺格，因此各部分不重叠；中心毯加四个子问题覆盖全部非公主格，因此也不遗漏。边长每轮减半，到一格时该格必为缺格，直接返回。

输出坐标不是某个固定左上角，而是 L 的直角拐弯格。按原图，方向一为向上和向左伸臂，二为向上和向右，三为向下和向左，四为向下和向右。若公主在左上象限，中心毯拐角在中心 2×2 的右下格，方向一；右上、左下、右下缺格分别对应方向二、三、四。代码把四个中心格按左上、右上、左下、右下编号零到三，真实缺格象限 q 的对角格编号是 3−q，方向为 q+1。

只需要保存一次递归的边界与缺格坐标，无须维护整个已铺棋盘。输出顺序可以不同于样例，正确性由覆盖情况决定。''',
    r'''int k,x,y;cin>>k>>x>>y;cover(1,1,1<<k,x,y);''',
    '坐标先行后列；输出 L 的拐弯格；已被中心毯盖住的格在子问题中当作缺格。',
    r'边长 N=2^k，输出 (N²−1)/3 块，时间 $O(N^2)$、递归辅助空间 $O(\log N)$。',
    tags=['分治','递归','构造'],lessons=R+['construction'],checker='tromino',
    declarations=r'''void cover(int row,int column,int size,int hole_x,int hole_y){
    if(size==1)return;int half=size/2;
    int q=(hole_x>=row+half)*2+(hole_y>=column+half);
    int x[4]={row+half-1,row+half-1,row+half,row+half};
    int y[4]={column+half-1,column+half,column+half-1,column+half};
    int corner=3-q;cout<<x[corner]<<' '<<y[corner]<<' '<<q+1<<'\n';
    for(int part=0;part<4;++part){
        int hx=part==q?hole_x:x[part],hy=part==q?hole_y:y[part];
        cover(row+(part/2)*half,column+(part%2)*half,half,hx,hy);
    }
}''')

add('P1498','递归摆放顶端与底端的三个小图腾',
    '按样例绘制由斜线、反斜线和下划线组成的 n 级三角图腾，保留行内及行首空格。',
    r'''一级图腾高二宽四。更高一级把上一等级分别放在上方居中、左下、右下，整体高度和宽度各翻倍。先开空格画布，递归只在一级叶图中写字符，最后逐行去掉行末空格输出。''',
    r'''一级的两行是 ` /\` 与 `/__\`，占高二、宽四的区域。二级不是画一个实心大三角，而是把三个一级图腾放成“上一块、下两块”，中间保留三角形空洞。以后每一级重复这个拼接。

让 draw(row,column,height) 表示在左上角为 (row,column)、高 height、宽 2×height 的矩形中绘制图腾。若 height=2，写入基础四个斜边字符和两个下划线。否则 half=height/2，三个子图的左上角分别是 (row,column+half)、(row+half,column)、(row+half,column+height)。三个区域只有边界相接，字符不会互相覆盖。

最终高度为 2^n，宽度为 2^(n+1)。用全空格字符串数组作画布，使空洞、行首缩进自然存在，避免递归过程中直接输出打乱同一行的多个子图。输出只删除每行末尾多余的空格，行首和行内空格都属于图形。C++ 字符字面量中的反斜线必须写成 `'\\'`。

递归画的叶图数量为 3^(n−1)，但清空画布与输出本身已有 O(4^n) 个字符位置，复杂度应计入这部分，而不能只报递归调用数量。''',
    r'''int n;cin>>n;int height=1<<n;canvas.assign(height,string(2*height,' '));draw(0,0,height);
for(auto line:canvas){while(!line.empty()&&line.back()==' ')line.pop_back();cout<<line<<'\n';}''',
    '保留行首与行内空格；反斜线在源码中需要转义；第 n 级高度是 2^n。',
    '初始化与输出时间、画布空间均为 $O(4^n)$，递归深度 $O(n)$。',
    tags=['分治','递归','模拟'],lessons=R+['strings'],exact=True,
    declarations=r'''vector<string>canvas;
void draw(int row,int column,int height){
    if(height==2){
        canvas[row][column+1]='/';canvas[row][column+2]='\\';
        canvas[row+1][column]='/';canvas[row+1][column+1]='_';
        canvas[row+1][column+2]='_';canvas[row+1][column+3]='\\';return;
    }
    int half=height/2;
    draw(row,column+half,half);draw(row+half,column,half);draw(row+half,column+height,half);
}''')

add('P1908','归并时一次统计左半段剩余元素',
    '统计满足 i<j 且 a[i]>a[j] 的下标对，数组允许重复值。',
    r'''递归统计左右内部的逆序对，并把两半排好序。归并时若左值≤右值，取左值；否则取右值，这个右值与左半段尚未取出的全部元素都组成逆序对，一次加 mid−i。''',
    r'''例如左右已经分别排成 [2,4,5] 与 [1,3,6]。右边的一小于左边当前最小值二，因此和二、四、五都构成逆序对，一次加三。随后取二，再遇右边三小于左边四，一次加二，对应四与三、五与三。

一次递归只考虑原下标连续的一段。原来的左半段下标始终小于原右半段下标；即使各自内部排序，跨半段的 i<j 仍天然成立。左右内部交给递归，当前层只统计一左一右的点对，三类按端点位置互斥且覆盖全部逆序对。

归并指针 i、j 指向两半各自最小的未取元素。若 a[i]>a[j]，左半段从 i 到 mid−1 全部不小于 a[i]，因此都严格大于 a[j]，共有 mid−i 个。若 a[i]≤a[j]，取出左值，不计数；特别是相等时不能当逆序对。每个跨段逆序对在其右值被取出的那一步恰好统计一次。

使用一个全局临时数组完成归并，每层线性、共对数层。n=500000 的倒序数组有 124999750000 对，答案必须用 long long；数组值本身用 int 足够。与树状数组法相比，本法无需离散化，但会把输入数组排序。''',
    r'''int n;cin>>n;sequence.resize(n);temporary.resize(n);for(int &x:sequence)cin>>x;cout<<count_inversions(0,n)<<'\n';''',
    '相等时取左、不加答案；使用半开区间 [l,r)，剩余左元素数为 mid−i。',
    r'时间 $O(n\log n)$、辅助数组空间 $O(n)$，递归深度 $O(\log n)$。',
    tags=['分治','排序'],lessons=R+['sort','integer'],
    declarations=r'''vector<int>sequence,temporary;
long long count_inversions(int l,int r){
    if(r-l<=1)return 0;int mid=(l+r)/2;
    long long answer=count_inversions(l,mid)+count_inversions(mid,r);
    int i=l,j=mid,k=l;
    while(i<mid&&j<r){
        if(sequence[i]<=sequence[j])temporary[k++]=sequence[i++];
        else{answer+=mid-i;temporary[k++]=sequence[j++];}
    }
    while(i<mid)temporary[k++]=sequence[i++];while(j<r)temporary[k++]=sequence[j++];
    for(i=l;i<r;++i)sequence[i]=temporary[i];return answer;
}''')

add('P1908','离散化后查询此前严格更大值的数量',
    '统计满足 i<j 且 a[i]>a[j] 的下标对，数组允许重复值。',
    r'''复制所有值，排序去重得到排名。按原顺序从左到右扫描当前排名 r，树状数组查询此前≤当前值的数量，用已处理数减去它得到严格更大值的数量，加到答案，再把 r 的频次加一。''',
    r'''这次不在排序过程中计数，而是保留原下标顺序。处理位置 j 时，所有已经插入树状数组的元素下标都小于 j，只差筛选值大于 a[j]。

值可达十亿，不能按原值开同样大的数组。先复制一份输入，排序去重，使用 lower_bound 找到每个数的零起始排名，再加一作为树状数组下标。排名保持大小关系，相同值映射到同一排名；去重的只是坐标表，原序列中的重复元素仍各自插入一次。

设此前处理了 j 个元素（代码下标从零起），sum(r) 是此前排名≤r 的数量，于是 j−sum(r) 恰好是此前严格更大的数量。这里查询到 r，包含与当前相等的值，才能把它们一起扣掉。若误用 sum(r−1)，相等值就会被算成逆序对。

先查后插，避免把自己计入此前元素。每一对在右端点到来时统计一次。与归并法相比，本法多了坐标压缩和树状数组，但可自然解释为动态频次问题，不改变原输入顺序；两种算法都为 n log n，选择已熟悉的一种即可。''',
    r'''int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;vector<int>values=a;
sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());
vector<int>tree(values.size()+1);long long answer=0;
for(int j=0;j<n;++j){
    int rank=(int)(lower_bound(values.begin(),values.end(),a[j])-values.begin())+1,count=0;
    for(int p=rank;p>0;p-=p&-p)count+=tree[p];
    answer+=j-count;
    for(int p=rank;p<(int)tree.size();p+=p&-p)++tree[p];
}
cout<<answer<<'\n';''',
    '坐标表去重，原输入不去重；查询包含相等值，再从总数扣除。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['离散化','树状数组','排序'],lessons=F+['coordinates','bounds','sort','iterators'],key='fenwick')

add('P1928','递归解析一层括号并返回展开文本',
    '把含嵌套 [重复次数 文本] 的字符串完整展开，重复次数为一到九十九，字母均为大写。',
    r'''用共享下标读取当前层直到右括号或输入结束。普通字母直接追加；遇左括号先读完整十进制次数，再递归得到括号内部的展开串，跳过右括号后重复追加指定次数。''',
    r'''对 `AC[3FUN]`，最外层先收下 A、C，遇左括号读到次数三；内层调用返回 FUN，外层再追加三份，得到 ACFUNFUNFUN。若内部还有括号，内层先完成展开，外层无需知道其结构。

定义 parse() 读取当前下标开始的一段内容，遇到右括号时停在该右括号上并返回，不自行消耗它。调用者已经读过左括号和重复次数，取得内层结果后将下标加一，恰好越过对应的右括号。这一约定使每一对括号由发起它的那一层负责，避免漏读或多跳一位。

重复次数可能有两位，必须在数字连续时使用 times=times×10+digit，不能只读一位。次数结束后的当前位置就是内层文本起点，即使它又是左括号，也直接交给递归。题目保证格式合法，不需要猜测错误输入的恢复方式。

展开长度至多 L=20000，深度 D≤10。每一层生成自己的结果，字符串片段可能在外层再次复制；保守计入这些复制，总时间 O(M+DL)，额外空间 O(M+DL)，M 为压缩串长度。不能因为输入下标只前进一次，就声称所有字符串工作只与压缩长度有关。''',
    r'''cin>>encoded;cout<<parse()<<'\n';''',
    '读完整多位次数；当前层停在右括号，由调用者跳过；输出的是展开结果。',
    '压缩长度 M、输出长度 L、嵌套深度 D 下，时间与空间上界为 $O(M+DL)$。',
    tags=['递归'],lessons=R+['strings','string-tools'],exact=True,
    declarations=r'''string encoded;size_t position=0;
string parse(){
    string result;
    while(position<encoded.size()&&encoded[position]!=']'){
        if(encoded[position]!='['){result.push_back(encoded[position++]);continue;}
        ++position;int times=0;
        while(position<encoded.size()&&'0'<=encoded[position]&&encoded[position]<='9')
            times=times*10+(encoded[position++]-'0');
        string part=parse();++position; // 内层停在 ]，本层消费该括号
        for(int k=0;k<times;++k)result+=part;
    }
    return result;
}''')

add('AT_agc005_b','按每个最小值负责的左右端点计贡献',
    '给定一到 N 的排列，求所有非空连续子数组的最小值之和。',
    r'''对位置 i，求左边第一个更小值位置 L、右边第一个更小值位置 R，不存在则用零和 N+1。恰以 a[i] 为最小值的子数组可选左端点 L+1 到 i，右端点 i 到 R−1，共 (i−L)(R−i) 个，贡献乘 a[i]。两遍单调栈在线性时间内求边界。''',
    r'''样例 [2,1,3] 中，数一在第二个位置，左右都没有更小值。含它的区间有 [1,2]、[1,3]、[2,2]、[2,3]，四个区间各贡献一；数二只负责 [1,1]，数三只负责 [3,3]，合计 4+2+3=9。

固定位置 i，若向左扩展碰到了更小值 a[L]，就不能继续把 a[i] 当最小值，所以左端点只能在 L+1 到 i，共 i−L 种。右端点同理有 R−i 种。左右可以独立选择，任何组合都得到包含 i 且不含更小值的连续区间，因此乘法计数成立。

题目是排列，没有相等值，每个区间有唯一的最小值。按最小值位置分组，区间既不遗漏也不重复。这个前提不能省略：若推广到有重复值的数组，两侧都找严格更小会让相等最小值重复负责，需一侧改为小于等于。

从左向右维护值严格递增的下标栈。新值到来，栈顶更大就弹出；弹出后栈顶是左侧最近更小值。被弹出的点对当前及以后的位置都被新点支配：新点更近且更小，不再可能让旧点成为最近更小者。右边界反向扫描同理。每个下标每遍至多入栈、出栈一次，总时间线性。

边界是“不允许包含”的位置，因此距离因子使用 i−L 与 R−i，不再减一。贡献先转为 long long 再相乘。''',
    r'''int n;cin>>n;vector<int>a(n+2),left(n+2),right(n+2),stack;
for(int i=1;i<=n;++i)cin>>a[i];
for(int i=1;i<=n;++i){
    while(!stack.empty()&&a[stack.back()]>a[i])stack.pop_back();
    left[i]=stack.empty()?0:stack.back();stack.push_back(i);
}
stack.clear();
for(int i=n;i>=1;--i){
    while(!stack.empty()&&a[stack.back()]>a[i])stack.pop_back();
    right[i]=stack.empty()?n+1:stack.back();stack.push_back(i);
}
long long answer=0;for(int i=1;i<=n;++i)answer+=1LL*a[i]*(i-left[i])*(right[i]-i);
cout<<answer<<'\n';''',
    '输入是排列，才能直接两边都找严格更小；每个区间的最小值只贡献一次。',
    '时间、空间均为 $O(n)$。',tags=['单调栈','组合计数'],lessons=A+['monotonic','counting','integer'])

add('AT_joisc2014_h','记录两种数量差同时相同的最早前缀',
    '在只含 J、O、I 的字符串中，找三个字母数量完全相同的最长连续子串，不存在则输出零。',
    r'''前缀状态记为 (J数−O数,J数−I数)。两端状态相同，等价于中间子串的三种计数都相同。用 map 保存每个二元状态最早出现的前缀位置，重复出现时取位置差；先存空前缀 (0,0) 的位置零。''',
    r'''要判断一段中三种数量相等，无须同时存三种绝对数量，只需两个差：J−O 和 J−I。以 JOI 为例，前缀状态从 (0,0) 走到 (1,1)、(0,1)、(0,0)，回到原状态就表示这段三种字母都增加了一次。

设前缀 j 与 i 的两个差都相等。相减后得到区间内 ΔJ−ΔO=0、ΔJ−ΔI=0，故 ΔJ=ΔO=ΔI；反过来若三种增量相同，两种差当然都不变。这证明重复二元状态与合法子串严格等价。只记录 J−O 不够，例如 JO 没有 I，前一个差为零却并不合法。

固定右端点 i，要尽量拉长区间，应使用该状态此前最早的位置。`map<pair<int,int>,int>` 把一对整数作为完整键，不使用容易冲突的随意十进制拼接。先 find：找不到才登记 i，找得到只更新答案，不覆盖最早位置。`operator[]` 会插入默认零，用它直接判断“是否出现”会混淆空前缀位置零。

每次字符只改变相关差：J 使两差各加一，O 使第一差减一，I 使第二差减一。空前缀提前插入，便能识别从首字符开始的合法段。使用有序 map 保证单次 O(log n)，不依赖哈希平均性能。''',
    r'''int n;string s;cin>>n>>s;map<pair<int,int>,int>first;first[{0,0}]=0;
int jo=0,ji=0,answer=0;
for(int i=1;i<=n;++i){
    if(s[i-1]=='J'){++jo;++ji;}else if(s[i-1]=='O')--jo;else --ji;
    pair<int,int>state={jo,ji};auto found=first.find(state);
    if(found==first.end())first[state]=i;else answer=max(answer,i-found->second);
}
cout<<answer<<'\n';''',
    '两种差必须同时相等；保留最早出现位置；空前缀不能用不存在来表示。',
    r'使用有序 map，时间 $O(n\log(n+1))$、空间 $O(n)$。',tags=['前缀和'],lessons=A+['prefix','maps'])

add('P2717','平均值条件转为有序前缀对计数',
    '给定正整数数组，统计平均值不小于 k 的非空连续子数组数量。',
    r'''每个值减去 k，原平均值≥k 等价于新段和≥0。记新前缀和 S，则区间 [l,r] 合法当且仅当 S[l−1]≤S[r]。离散化全部前缀和，用树状数组统计扫描到当前前缀之前有多少个值≤它，查询后再插入当前前缀。''',
    r'''样例 [1,2,3]、k=2，减去二后为 [−1,0,1]，含空前缀的和值为 [0,−1,−1,0]。扫描第二个零时，此前的零及两个负一都不大于它，贡献三段；中间第二个负一与前一个负一又贡献一段，总数四。

平均值的分母是区间长度 r−l+1，为正，故

$$\frac{\sum_{i=l}^r a_i}{r-l+1}\ge k
\iff \sum_{i=l}^r(a_i-k)\ge0
\iff S[l-1]\le S[r].$$

第一个变换是把每一项都减去 k，不是只把总和减一次 k。段内可能有负数，不能用“右端扩大则和不减”的滑窗。我们只需数此前前缀和值中不大于当前者的数量，适合动态前缀频次。

复制 n+1 个前缀和，排序去重后求一开始的排名。按原前缀下标零到 n 依次扫描：先用树状数组查询排名≤当前的频次数，再插入当前。零号空前缀也照此处理，它查询时此前没有对象，贡献零；此后它能作为从第一项开始的区间左边界。

先查后插保证两个前缀下标严格递增，从而排除空区间。查询必须包含等号，因为平均值恰好 k 也符合。重复前缀只在坐标表去重，频次仍按每次出现累加。最多 n(n+1)/2 个区间，答案用 long long。''',
    r'''int n;long long k;cin>>n>>k;vector<long long>prefix(n+1);
for(int i=1;i<=n;++i){long long x;cin>>x;prefix[i]=prefix[i-1]+x-k;}
vector<long long>values=prefix;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());
vector<int>tree(values.size()+1);long long answer=0;
for(long long sum:prefix){
    int rank=(int)(lower_bound(values.begin(),values.end(),sum)-values.begin())+1;
    for(int p=rank;p>0;p-=p&-p)answer+=tree[p]; // 查询包含与当前相等的前缀
    for(int p=rank;p<(int)tree.size();p+=p&-p)++tree[p];
}
cout<<answer<<'\n';''',
    '先查后插以排除空区间；查询包含等号；必须把空前缀纳入。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['前缀和','离散化','树状数组'],lessons=F+['prefix','coordinates','bounds','sort','iterators'])

add('P7167','单调栈连溢流后继，倍增跳过已灌满圆盘',
    '水灌满一个圆盘后流向下方第一个直径严格更大的圆盘，每次独立倒水，求最后停留圆盘，全部流走则输出零。',
    r'''单调栈求每个圆盘下方首个严格更大直径的位置作为 next。倍增保存从 u 开始灌满 2^j 个盘后到达的位置，以及这些盘的容量和。查询从大步长往小试，只有容量和严格小于剩余水量才整段跳过；最终所在盘就是答案。''',
    r'''水从盘一溢出时，不一定进入紧邻的盘二：要跳过所有直径不大于当前盘的圆盘，落到第一个严格更大的盘。因此先独立求出每个盘的唯一溢流后继，水的路线就是不断沿 next 前进的一条链；下标严格增大，不会成环。

从上到下扫描，用栈保存尚未找到更大后继的盘。新直径大于栈顶时，当前盘就是栈顶的首个更大盘，弹出并登记 next；相等不能弹出。每盘至多入栈、出栈一次。剩余未找到者的 next=0，表示水池。

若逐盘扣除容量，一次询问可走十万个盘。定义 up[j][u] 为从 u 开始依次灌满 2^j 个盘后到达的位置，cost[j][u] 为这些盘的总容量，不含到达的那个盘。基础为 up[0][u]=next[u]、cost[0][u]=C[u]。令 v=up[j−1][u]，把前后两个半段拼接：up[j][u]=up[j−1][v]，cost[j][u]=cost[j−1][u]+cost[j−1][v]。虚拟零号盘后继和容量均为零，统一表示进入水池后的终点。

询问从起点 u 和剩余水量 water 开始，降序试跳。只有 cost[j][u]<water 时，水才会溢出整段，可以扣除这些容量并令 u=up[j][u]；若恰好相等，水会停在该段最后一个盘，不能跳到下一盘。最终无法再跳过当前一个盘，即 water≤C[u]，停在 u；若已进入零号水池则输出零。每次询问都用原容量，不改全局盘中水量。

跳表包含超过实际链长的层时，其容量和就是到水池前的总容量。只有水量严格超过这个和才能跳入水池，语义仍然正确。容量和与水量使用 long long。''',
    r'''int n,q;cin>>n>>q;const int LOG=18;
vector<int>diameter(n+1),stack;vector<vector<int>>up(LOG,vector<int>(n+1));
vector<vector<long long>>cost(LOG,vector<long long>(n+1));
for(int i=1;i<=n;++i){
    cin>>diameter[i]>>cost[0][i];
    while(!stack.empty()&&diameter[stack.back()]<diameter[i]){up[0][stack.back()]=i;stack.pop_back();}
    stack.push_back(i);
}
for(int j=1;j<LOG;++j)for(int u=1;u<=n;++u){
    int middle=up[j-1][u];up[j][u]=up[j-1][middle];cost[j][u]=cost[j-1][u]+cost[j-1][middle];
}
while(q--){
    int u;long long water;cin>>u>>water;
    for(int j=LOG-1;j>=0&&u!=0;--j)if(cost[j][u]<water){water-=cost[j][u];u=up[j][u];}
    cout<<u<<'\n';
}''',
    '直径相等不能接水；水量等于容量时不溢出；询问独立，不能累计修改容量。',
    r'预处理 $O(n\log n)$、每次询问 $O(\log n)$，空间 $O(n\log n)$。',
    tags=['单调栈','倍增'],lessons=A+['monotonic','binary-lifting','integer'])

add('SP32079','压缩以当前右端点结束的相同 GCD 段',
    '给定非负整数序列，求所有非空连续子数组最大公约数的总和，包含零值。',
    r'''按右端点从左到右，保存上一轮所有后缀的 (GCD,数量) 分组。加入 x 后，新建单元素组 (x,1)，旧组 (g,c) 变成 (gcd(g,x),c)，相邻结果相同就合并。每组 GCD 乘数量加到总答案。''',
    r'''以 [2,2,3] 为例。右端点在第二个二时，后缀 [2] 与 [2,2] 的 GCD 都是二，压成 (2,2)。加入三后，新单元素 [3] 给出 (3,1)，此前两段都延长后 GCD 变一，给出 (1,2)。这一轮三段的贡献为 3×1+1×2=5。

固定右端点时，从短后缀向长后缀看，GCD 只可能保持或变成前一个值的约数。某个正 GCD 真正变小时，至少缩到一半，因此不同正值只有 O(log(A+1)) 种；若全由零组成的短后缀存在，还多一个零组。相同 GCD 的后缀连续出现，所以用按长度从短到长的分组保存即可。

新值 x 到来，每个旧后缀必须且只需在末尾加 x，GCD 恰好变为 gcd(旧GCD,x)，原组内数量不变。此外新增单元素后缀 [x]。依此顺序遍历旧组得到的新 GCD 仍按整除关系排列，相等者必相邻，只需与新数组末组比较、合并数量，不需要 map 或枚举所有左端点。

每组 (g,c) 表示 c 个不同子数组，贡献是 g×c。所有子数组有唯一右端点，逐轮累加不重不漏。gcd(0,x)=x、gcd(0,0)=0，故零值无需删掉或特殊跳过；全零输入答案为零。代码调用 C++17 `<numeric>` 的 std::gcd，参数为整数。

与“用区间查询结构再枚举全部子数组”相比，节省来自相同 GCD 的合并，而非一次 gcd 运算本身。答案最多 A×n(n+1)/2，本范围 long long 足够。''',
    r'''int n;cin>>n;vector<pair<int,long long>>previous;long long answer=0;
for(int i=0;i<n;++i){
    int x;cin>>x;vector<pair<int,long long>>current;current.push_back({x,1});
    for(auto group:previous){
        int value=gcd(group.first,x);
        if(current.back().first==value)current.back().second+=group.second;
        else current.push_back({value,group.second});
    }
    for(auto group:current)answer+=1LL*group.first*group.second;
    previous.swap(current);
}
cout<<answer<<'\n';''',
    '数量是子数组个数，不能只对不同 GCD 求和；零也构成合法单元素段。',
    r'设 A 为最大值，令 L=max(1,log(A+1))。每轮 O(L) 组，按欧几里得算法的对数上界计，总时间 $O(nL^2)$、额外空间 $O(L)$。',
    tags=['最大公约数','递推'],lessons=A+['number-theory','integer'])
