"""Explicit solutions for the eighteen simulation/enumeration exercises."""
from core7_authoring import add

A=['io-basics','arrays','vector','basic-control']
R=A+['functions','recursion']

add('P2670','枚举八个相邻格','保留地雷格，对其它格子输出周围八个方向的地雷总数。',
    '对每个非地雷格，枚举行偏移和列偏移各为负一、零、一的组合，排除自身并检查边界；每遇到一个地雷就加一。',
    r'''左上角格子只有右、下、右下三个实际邻居，不能仍然访问八个数组位置。以当前坐标 (i,j) 为中心，邻居坐标写成 (i+dr,j+dc)，其中两个偏移都在 −1 到 1 之间，但不能同时为零。

先确认新行列都在棋盘内，再判断原图该处是否为星号。用原图统计不会把后来输出的数字当作地雷；也无需真的翻开或搜索格子，因为全部地雷位置已经给出。地雷格直接输出星号，非雷格计数最多八，所以一个数字字符足够。每输出完一行换行，格子之间不加空格。''',
    r'''int n,m;cin>>n>>m;vector<string>g(n);for(string &s:g)cin>>s;
for(int i=0;i<n;++i){for(int j=0;j<m;++j){
    if(g[i][j]=='*'){cout<<'*';continue;}
    int count=0;
    for(int dr=-1;dr<=1;++dr)for(int dc=-1;dc<=1;++dc){
        if(dr==0&&dc==0)continue;
        int r=i+dr,c=j+dc;
        if(r>=0&&r<n&&c>=0&&c<m&&g[r][c]=='*')++count;
    }
    cout<<count;
}cout<<'\n';}''',
    '先检查边界再访问格子；不把中心自己算入邻居，输出没有分隔空格。',
    '时间 $O(nm)$、保存棋盘空间 $O(nm)$。',tags=['模拟'],lessons=A+['strings'],exact=True)

add('P1036','递增下标枚举组合','从给定的 n 个位置选出 k 个，使所选数之和为质数，统计这样的选法。',
    '递归保存下一个允许选择的下标、已选个数与当前和。每次选一个更靠后的下标，选满 k 个后用试除判断质数。',
    r'''选下标一、二、四与选四、二、一是同一个选法，不能重复计数。限定下标严格递增，每个集合就只剩唯一的访问顺序；即使两个位置上的值相同，它们仍是不同位置，不能先把输入去重。

dfs(start,chosen,sum) 表示前面已经选好 chosen 个，下一次只能选 start 或其后的位置。若还缺 need=k−chosen 个，则本次下标最多为 n−need，保证后面有足够位置补齐。选满时才判断完整的和，中间和是否为质数不能决定最终结果。

质数必须大于一。若 sum 是合数，它必有不超过平方根的因子，所以检查 d 从二到 d²≤sum 即可；找不到因子才计一次。每次递归都增加已选个数，最终最多 k 层。''',
    r'''cin>>n>>k;a.resize(n);for(int &x:a)cin>>x;dfs(0,0,0);cout<<answer<<'\n';''',
    '按位置选组合；一不是质数，不能按选择顺序重复计数。',
    r'设最大可能和为 S，时间上界 $O(k\binom nk+\binom nk\sqrt S)$，数组与递归空间 $O(n+k)$。',
    tags=['DFS','枚举','素数'],lessons=R+['number-theory'],declarations=r'''int n,k,answer=0;vector<int>a;
bool prime(int x){if(x<2)return false;for(int d=2;1LL*d*d<=x;++d)if(x%d==0)return false;return true;}
void dfs(int start,int chosen,int sum){
    if(chosen==k){answer+=prime(sum);return;}
    int need=k-chosen;
    for(int i=start;i<=n-need;++i)dfs(i+1,chosen+1,sum+a[i]);
}''')

add('P1067','拆开符号、系数和幂次输出','按规范输出多项式：省略零项，处理首项符号、系数一以及一次项和常数项。',
    '按次数递减读取。零系数跳过；先按是否已经输出过项决定符号，再按次数与系数绝对值决定数字和 x 的写法。',
    r'''系数序列 [1,−1,0,3] 对应三次到零次，输出 x^3-x^2+3。符号、系数、幂次应分别判断，否则很容易把某个特例遗漏。

维护 first 表示还没输出任何非零项。负系数总输出减号；正系数仅在不是首项时输出加号。随后只看绝对值：常数项必须输出完整数字；其它项在绝对值为一时省略数字。正次数输出 x，大于一次才追加 ^ 和次数。输出完非零项后将 first 设为 false；跳过零项不能改变它。题目保证最高次系数非零，代码也兼容全零输入，最终补一个零。''',
    r'''int n;cin>>n;bool first=true;
for(int power=n;power>=0;--power){int coefficient;cin>>coefficient;if(coefficient==0)continue;
    if(coefficient<0)cout<<'-';else if(!first)cout<<'+';
    int value=abs(coefficient);
    if(power==0||value!=1)cout<<value;
    if(power>0){cout<<'x';if(power>1)cout<<'^'<<power;}
    first=false;
}
if(first)cout<<0;cout<<'\n';''',
    '常数一不能省略；一次项只写 x，首个正项前不写加号。',
    '时间 $O(n)$、额外空间 $O(1)$。',tags=['模拟'],lessons=['io-basics','basic-control','basic-arithmetic'],exact=True)

add('P1088','调用字典序后继','输入排列代表它在全部排列中的名次，求名次增加 m 后的排列；保证结果没有超过最后一种。',
    '名次加一等于取一次字典序下一个排列，直接对完整数组调用 next_permutation 共 m 次。',
    '这不是把手指编号拼成普通十进制整数再做加法。例如三根手指的排列 [1,3,2] 表示第二名，下一个是 [2,1,3]，表示第三名。题目已经把所有排列按字典序编号，所以无需计算可能极大的名次本身，只需 m 次后继操作。m≤100，一次最多扫描 n 项，总共百万量级。标准库会就地修改数组；题目保证不超出范围，因此这 m 次都存在真正的后继，不会触发从最后一种回到第一种的行为。',
    r'''int n,m;cin>>n>>m;vector<int>a(n);for(int &x:a)cin>>x;
while(m--)next_permutation(a.begin(),a.end());
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');''',
    '不要把 m 加到每个编号上；处理的是排列的字典序名次。',
    '时间 $O(mn)$，数组空间 $O(n)$。',tags=['模拟'],lessons=A+['lex-permutation','iterators'])

add('P1088','手写字典序后继','给出一个排列，向后移动 m 个字典序名次，输出结果。',
    '每次找最靠右的可增大位置，换成右侧刚好比它大的数，再反转后缀，使后缀最小。',
    r'''以 [1,3,2] 为例，最后两项已经递减，是这一后缀的最大排列，因此只改最后两项不能变大。要改动前面的 1，换成右边最小的更大数字 2，再把剩余后缀排成 [1,3]，得到 [2,1,3]。

从右往左找 a[i]<a[i+1]，它后面整段必为递减。从末尾往左找到第一个大于 a[i] 的数，它就是后缀中最小的可替代数。交换后，后缀仍递减：原枢轴比换出的数小，但大于它右边所有不满足条件的数。于是反转后缀即可得到升序，不必额外排序。最靠右的改动保证前缀尽可能长地不变，最小增大与最小后缀保证没有夹在中间的其它排列。''',
    r'''int n,m;cin>>n>>m;vector<int>a(n);for(int &x:a)cin>>x;
while(m--)successor(a);
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');''',
    '找的是严格大于枢轴的项，交换后反转的是枢轴右侧，不含枢轴。',
    '时间 $O(mn)$，数组空间 $O(n)$，后继操作额外空间 $O(1)$。',tags=['模拟'],lessons=A+['lex-permutation','functions','iterators'],key='manual-successor',
    declarations=r'''bool successor(vector<int>&a){
    int n=a.size(),i=n-2;while(i>=0&&a[i]>=a[i+1])--i;
    if(i<0){reverse(a.begin(),a.end());return false;}
    int j=n-1;while(a[j]<=a[i])--j;
    swap(a[i],a[j]);reverse(a.begin()+i+1,a.end());return true;
}''')

add('P1149','枚举两个加数并精确计棒','用恰好 n 根火柴拼出 A+B=C，三个数非负且没有多余前导零；交换不同加数视为不同等式。',
    '预先计算每个数字和每个整数需要的火柴数，枚举 A、B，令 C=A+B，检查三者的用棒数加上四是否恰好为 n。',
    r'''数字 0 到 9 的用棒数依次为 6、2、5、5、4、5、6、3、7、6。整数零本身需要六根，不能因为没有进入拆位循环而记为零。加号、等号各两根，先扣除固定的四根，余下才属于数字。

要给枚举一个可靠上界。若某个加数至少五位，非负加法保证和也至少五位；每位至少两根，另一个加数至少两根，总共至少 10+10+2+4=26 根，超过二十四。因此两个加数都在零到九千九百九十九之间，和至多一万九千九百九十八。

还可先过滤候选加数：另外两个数各至少两根，固定符号四根，所以单个加数最多用 n−8 根。n=24 时仅有 2199 个候选。分别枚举有序对，不要求 A≤B，便自然保留 0+1=1 与 1+0=1 两种。验证总和必须等于 n，不能把没用完的火柴闲置。''',
    r'''int n;cin>>n;vector<int>cost(19999);for(int x=0;x<19999;++x)cost[x]=sticks(x);
vector<int>candidate;for(int x=0;x<10000;++x)if(cost[x]<=n-8)candidate.push_back(x);
int answer=0;for(int a:candidate)for(int b:candidate)if(cost[a]+cost[b]+cost[a+b]+4==n)++answer;
cout<<answer<<'\n';''',
    '零需要六根；交换不同加数算另一种，必须恰好用完。',
    r'设候选个数为 q，时间 $O(U\log U+q^2)$、空间 $O(U)$，预处理上界 U=19999，q≤2199。',tags=['枚举'],lessons=A+['functions','enumeration'],
    declarations=r'''int sticks(int x){int use[10]={6,2,5,5,4,5,6,3,7,6},answer=0;do{answer+=use[x%10];x/=10;}while(x);return answer;}''')

add('P1157','递增选择并回溯输出','按字典序输出一到 n 中所有大小为 r 的组合，每个数字占三个字符宽度。',
    '每一层从上次所选数的下一个开始，按升序尝试；收集满 r 个数就按三字符场宽输出一行。',
    r'''n=5、r=3 时，先固定第一项一，再固定第二项二，第三项依次三、四、五，得到 [1,2,3]、[1,2,4]、[1,2,5]。返回上一层后再选第二项三。每层从小到大尝试，所以输出行天然按字典序排列。

组合只关心选了哪些数，限定所选数字严格递增，就不会再输出 [2,1,3] 这样的重复顺序。path 是当前已选前缀，选入一个数后 push_back，递归返回必须 pop_back，撤销这次选择，让下一分支沿用原前缀。还缺 need 项时，当前最多选 n−need+1，以保证足够的位置。r=0 对应唯一的空组合，输出一个空行。setw(3) 只作用于下一次数字输出，因此每个数字前都要调用。''',
    r'''cin>>n>>r;dfs(1);''',
    '每个数都要设置场宽；返回时撤销本层选择，不能把组合当排列。',
    r'含输出的时间 $O((r+1)\binom nr)$，递归与路径空间 $O(r+1)$。',tags=['DFS','枚举'],lessons=R,
    declarations=r'''int n,r;vector<int>path;
void dfs(int start){
    if((int)path.size()==r){for(int x:path)cout<<setw(3)<<x;cout<<'\n';return;}
    int need=r-path.size();
    for(int x=start;x<=n-need+1;++x){path.push_back(x);dfs(x+1);path.pop_back();}
}''',exact=True)

add('P1303','十进制竖式乘法','计算两个至多约两千位非负整数的乘积。',
    '把字符串反过来按位相乘，第 i 位和第 j 位的乘积累加到第 i+j 位，再统一从低到高进位，最后反向输出。',
    r'''普通整数类型不能保存两千位数，因此输入必须用字符串。以 12×13 为例，低位数组分别是 [2,1]、[3,1]。乘积的个位贡献为六，十位贡献为 2×1+1×3=5，百位为一，正好得到 156。

一般地，第 i 位代表数字乘十的 i 次方，第 j 位代表数字乘十的 j 次方，两者的乘积应放在 i+j 位。先用双循环累加全部贡献，再逐位把 c[i]/10 加给下一位、c[i]%10 留在本位；顺序从低到高，保证后来接收的进位也会被处理。这里每个槽最多累积约 2001×81，int 足够保存中间量。

乘积最多占两数位数之和，数组再多留一格供进位。输出前只删除高位的多余零，至少保留一位，因此任一输入为零时正确输出零；输入自身带前导零也不会改变结果。''',
    r'''string a,b;cin>>a>>b;vector<int>c(a.size()+b.size()+1);
for(int i=0;i<(int)a.size();++i)for(int j=0;j<(int)b.size();++j)
    c[i+j]+=(a[a.size()-1-i]-'0')*(b[b.size()-1-j]-'0');
for(int i=0;i+1<(int)c.size();++i){c[i+1]+=c[i]/10;c[i]%=10;}
while(c.size()>1&&c.back()==0)c.pop_back();
for(int i=(int)c.size()-1;i>=0;--i)cout<<c[i];cout<<'\n';''',
    '字符串字符要减去字符零；高位零可删，内部零和零结果的一位不能删。',
    '输入长度为 N、M，时间 $O(NM)$、空间 $O(N+M)$。',tags=['高精度'],lessons=A+['strings','big-integers'],exact=True)

add('P1563','先列表判方向再模 n 移动','小人按逆时针顺序输入，每步依据当前小人的朝向与左右指令移动，输出最终职业。',
    '把逆时针对应下标增加。朝向和左右指令相同时向下标减小方向移动，不同时向增加方向；每步都以当前所在小人为准。',
    r'''输入顺序是逆时针，所以朝内者左手对应顺时针，应该减下标；朝内向右则加下标。朝外的左右关系恰好相反。四种情况分别为：朝内左移减、朝内右移加、朝外左移加、朝外右移减。两种减法正好满足“朝向编码等于左右编码”。

pos 表示当前下标，初始为零。若朝向等于指令，更新为 (pos−s+n)%n；否则为 (pos+s)%n。题目保证 s<n，加一次 n 就能让减法非负，避免 C++ 负余数。走完一条指令后，下一条要读取新位置的朝向，不能始终沿用第一个人的朝向。无需逐个数 s 步，模运算一次得到绕圈后的终点。''',
    r'''int n,m;cin>>n>>m;vector<int>face(n);vector<string>name(n);
for(int i=0;i<n;++i)cin>>face[i]>>name[i];int pos=0;
while(m--){int direction,steps;cin>>direction>>steps;
    if(face[pos]==direction)pos=(pos-steps+n)%n;else pos=(pos+steps)%n;
}cout<<name[pos]<<'\n';''',
    '下标递增是逆时针；每一步使用当前位置朝向，取余前避免负数。',
    '时间 $O(n+m)$、空间 $O(n)$。',tags=['模拟'],lessons=A+['strings','modular'])

add('P1591','逐次乘小整数求阶乘','对每组 n 和数码 a，计算 n! 的十进制表示中 a 出现多少次。',
    '从高精度整数一开始，逐次乘二到 n，每次完成低位乘法与进位；最后统计有效位数组中等于 a 的项。',
    r'''5!=120，低位数组为 [0,2,1]，其中数码二出现一次。这个数组只保存真正存在的位，不给结果补前导零，否则统计数码零时会多算。

乘一个小整数 factor 时，从低位开始计算 value=digit×factor+carry，本位留下 value%10，carry=value/10。原来的每一位处理后，进位可能仍有多位，持续拆分并追加到数组尾部。例如 9×12=108，最后进位十还要拆成零、一两位，不能只追加一个十。

每组独立从一开始，完成二到 n 的全部乘法后再统计。n≤1000，最大阶乘只有 2568 位，朴素高精度足够；不需要把大整数转换回任何机器整数。''',
    r'''int t;cin>>t;while(t--){int n,target;cin>>n>>target;vector<int>digits(1,1);
    for(int factor=2;factor<=n;++factor){int carry=0;
        for(int &digit:digits){int value=digit*factor+carry;digit=value%10;carry=value/10;}
        while(carry){digits.push_back(carry%10);carry/=10;}
    }
    int answer=0;for(int digit:digits)answer+=digit==target;cout<<answer<<'\n';
}''',
    '每组重置结果为一；只统计有效位，进位可能还要追加多位。',
    '设最终位数为 D，每组时间 $O(nD)$、空间 $O(D)$。',tags=['高精度'],lessons=A+['big-integers'])

add('P1618','枚举首数并交叉乘法求比例','把一到九各用一次组成三个三位数，比例等于 A:B:C，按第一个数升序输出全部解。',
    '枚举第一个三位数 x，用 xB/A、xC/A 求另两数；必须整除且都是三位数，再检查九个数码恰好是一到九。',
    r'''比例不要求 A、B、C 已约分，因此不能只枚举 x=A×整数。例如比例 2:4:6 与 1:2:3 是同一要求，首数应允许所有符合整除关系的值。关系 y/x=B/A 改写为 yA=xB；先检查 xB 能否被 A 整除，另一个数同理，整个过程不用浮点数。

A=0 时不可能形成正的首个三位数，直接无解。A>0 时枚举 x 从一百到九百九十九，计算 y、z；任一不在三位数范围内就跳过。将三数的每一位标记，零或已经出现过的数字立即判错。三个三位数共有九位，只要都非零且互不相同，就必然恰好覆盖一到九。x 递增保证输出顺序，也没有同一个三元组被重复枚举。''',
    r'''long long A,B,C;cin>>A>>B>>C;bool found=false;
if(A>0)for(int x=100;x<=999;++x){
    if(x*B%A||x*C%A)continue;long long y=x*B/A,z=x*C/A;
    if(y<100||y>999||z<100||z>999)continue;
    bool used[10]={},ok=true;
    for(int value:{x,(int)y,(int)z})while(value){int d=value%10;value/=10;if(d==0||used[d])ok=false;used[d]=true;}
    if(ok){cout<<x<<' '<<y<<' '<<z<<'\n';found=true;}
}
if(!found)cout<<"No!!!\n";''',
    'A 可以为零；比例不必约分，必须判整除；不能使用零或重复数字。',
    '枚举九百个首数，每个检查九位，时间与空间均为 $O(1)$。',tags=['枚举'],lessons=['io-basics','arrays','basic-control','basic-arithmetic'],exact=True)

add('P1706','按升序选择未使用数字','按字典序输出一到 n 的所有排列，每个数字占五字符宽度。',
    '递归决定下一位置，每层从一到 n 按升序选择尚未用过的数字；长度达到 n 时输出，返回时撤销选择。',
    r'''n=3 时，先放一，后面依次尝试二、三，得到 [1,2,3] 与 [1,3,2]，再把首位换为二。字典序看第一个不同位置，每层递增尝试就保证整行输出的顺序。

used[x] 记录数字 x 是否已经在当前前缀内。选择 x 时标记并加入 path，递归处理下一个位置；回来时先弹出再解除标记，下一分支才能再次使用这个数字。每个完整排列对应唯一的一条选数路径，标记保证每项恰好出现一次，所有可能位置上的选择也都被枚举到了。setw(5) 只影响下一次输出，因此要对行内每个数字分别设置。''',
    r'''cin>>n;dfs();''',
    '每层结束要恢复 used 和路径；每个数字保留五字符宽度。',
    r'含输出时间 $O(n\cdot n!)$，路径、标记与递归空间 $O(n)$。',tags=['DFS','枚举'],lessons=R,
    declarations=r'''int n;bool used[10]={};vector<int>path;
void dfs(){
    if((int)path.size()==n){for(int x:path)cout<<setw(5)<<x;cout<<'\n';return;}
    for(int x=1;x<=n;++x)if(!used[x]){
        used[x]=true;path.push_back(x);dfs();path.pop_back();used[x]=false;
    }
}''',exact=True)

add('P1706','从升序开始枚举字典序后继','按字典序输出一到 n 的所有排列，每个数字占五字符宽度。',
    '初始化为最小排列 [1,2,…,n]，先输出当前排列，再反复取下一个字典序排列，直到不存在。',
    '标准库 next_permutation 在成功时把当前序列改成紧邻的下一个字典序排列。最小的排列是一到 n 升序，先输出它，然后每次输出成功得到的后继，就能不遗漏、不重复地走过全部排列。必须使用 do-while，否则先取后继会漏掉初始升序排列。最后一种之后函数返回 false 并重置为升序，此时终止，不再输出重置后的内容。',
    r'''int n;cin>>n;vector<int>a(n);iota(a.begin(),a.end(),1);
do{for(int x:a)cout<<setw(5)<<x;cout<<'\n';}while(next_permutation(a.begin(),a.end()));''',
    '先输出初始排列；结束时不再次输出被重置的升序排列。',
    r'含输出时间 $O(n\cdot n!)$、数组空间 $O(n)$。',tags=['枚举'],lessons=A+['lex-permutation','iterators'],key='stl-successor',exact=True)

add('P2089','按配料位置回溯','十种配料各放一到三克，总质量恰为 n，输出全部方案的数量及字典序排列。',
    '递归依次决定十个位置，每个位置按一、二、三尝试，选满十项且总和等于 n 时保存。利用剩余项的最小最大贡献剪枝。',
    r'''每个位置对应一种固定配料，所以 [1,2,…] 与 [2,1,…] 是不同方案。递归深度 pos 表示已有多少种配料决定好，sum 是它们的总量。还剩 remain=10−pos 种，每种至少一、至多三，最终总量只能落在 [sum+remain,sum+3remain]；n 不在这个区间就不再往下搜索。

选满十种时，这个区间退化为单个 sum；通过检查的路径就是合法方案。每层按一、二、三递增，保存顺序自然为字典序。题目要求先输出总数，故将完整路径存入答案数组，搜索结束后再统一输出。n<10 或 n>30 从根就被剪掉，只输出零。''',
    r'''cin>>target;dfs(0,0);cout<<answers.size()<<'\n';
for(const auto &row:answers)for(int i=0;i<10;++i)cout<<row[i]<<(i==9?'\n':' ');''',
    '十个位置的意义不同，不能排序后去重；数量要先于所有方案输出。',
    r'最多枚举 $3^{10}$ 个完整选择，含保存与输出时间 $O(10\cdot3^{10})$；有 Q 个答案时空间 $O(10Q+10)$。',tags=['DFS','枚举'],lessons=R,
    declarations=r'''int target;vector<int>path;vector<vector<int>>answers;
void dfs(int pos,int sum){
    int remain=10-pos;if(sum+remain>target||sum+3*remain<target)return;
    if(pos==10){answers.push_back(path);return;}
    for(int x=1;x<=3;++x){path.push_back(x);dfs(pos+1,sum+x);path.pop_back();}
}''',exact=True)

add('P3392','枚举两条分界线并用前缀代价求和','把旗帜改成非空白段、非空蓝段、非空红段三段整行颜色，求最少重涂格数。',
    '预处理每种目标颜色在各行的改色数及其前缀和。枚举白段结束位置 a 和蓝段结束位置 b，取三段代价之和的最小值。',
    r'''一旦确定白段有 a 行、白蓝合计有 b 行，目标图案就唯一确定：前 a 行白、中间 b−a 行蓝、最后 n−b 行红。只需枚举 1≤a<b<n，三段各至少一行，所有合法旗帜都会被某组分界线覆盖。

对某一行，改成白色的代价是该行非 W 格数，改成蓝、红同理。p[i][color] 表示前 i 行全部改成 color 的总成本，p[0] 为零。因此当前分界线的代价为 p[a][W]+(p[b][B]−p[a][B])+(p[n][R]−p[b][R])。每个格子只属于一个颜色段，三段独立且没有重叠，所以可以直接相加。每组分界线用常数时间计算，不必再次扫描棋盘。''',
    r'''int n,m;cin>>n>>m;vector<array<int,3>>p(n+1);string colors="WBR";
for(int i=1;i<=n;++i){string row;cin>>row;p[i]=p[i-1];
    for(char ch:row)for(int c=0;c<3;++c)p[i][c]+=ch!=colors[c];
}
int answer=n*m;for(int a=1;a<n-1;++a)for(int b=a+1;b<n;++b)
    answer=min(answer,p[a][0]+p[b][1]-p[a][1]+p[n][2]-p[b][2]);
cout<<answer<<'\n';''',
    '三种颜色段都必须非空；代价计不等于目标色的格子，不能计已有目标色的数量。',
    '时间 $O(nm+n^2)$、额外空间 $O(n+m)$。',tags=['枚举','前缀和'],lessons=A+['strings','prefix'])

add('P3654','统计连续空地段中的长度 k 窗口','在带障碍棋盘上统计横向或纵向连续 k 个空格的站位，单格站位只算一种。',
    '逐行、逐列扫描连续空地长度，每遇到一个长度至少 k 的后缀，就为以当前位置结尾的站位加一。k=1 时只扫描行，避免重复。',
    r'''一行中长度为五的连续空地，k=3 时能选起点一、二、三，共三种。扫描到本段第三、第四、第五个空格时，分别恰好产生一个以当前位置结尾、长度三的窗口，因此只要当前连续长度至少 k 就累加一次，不需要回头检查每个窗口。

遇障碍把连续长度清零，不让窗口跨过杂物。逐行数完横向站位，再逐列完全同样地数纵向站位。k>1 时，水平的多格集合不可能同时是竖直的多格集合，二者可以直接相加；k=1 时两种扫描会指向同一个单格，故只进行一次方向的扫描。数的是占用哪些格子，不再乘队员的排列数。''',
    r'''int r,c,k;cin>>r>>c>>k;vector<string>g(r);for(string &s:g)cin>>s;int answer=0;
for(int i=0;i<r;++i){int length=0;for(int j=0;j<c;++j){length=g[i][j]=='.'?length+1:0;if(length>=k)++answer;}}
if(k>1)for(int j=0;j<c;++j){int length=0;for(int i=0;i<r;++i){length=g[i][j]=='.'?length+1:0;if(length>=k)++answer;}}
cout<<answer<<'\n';''',
    '障碍处连续长度清零；k=1 时横竖不能各算一次。',
    '时间 $O(rc)$、棋盘空间 $O(rc)$。',tags=['枚举'],lessons=A+['strings'])

add('P1045','低五百位高精度快速幂','输出 2 的 p 次方减一的十进制位数，以及补足五百位的末尾数字，每行五十位。',
    '总位数用十进制对数计算；低五百位用数组竖式乘法和二进制快速幂计算，每次乘完直接舍弃更高位，最后减一并定宽输出。',
    r'''先分开两个任务。总位数不需要保存全数：正整数 X 的十进制位数为 floor(log10 X)+1。2^p 不会恰好是十的整数次方，且 p>1000，所以减一不会从最高位借走一整位，位数仍为 floor(p·log10 2)+1。代码用 long double 计算这个量；这里只用对数确定长度，不拿浮点数生成末尾数字。

末尾五百位等价于模十的五百次方。用五百个十进制位低位在前保存数，乘法累加第 i 与第 j 位对第 i+j 位的贡献，只计算 i+j<500，统一进位并丢弃最高位以外的进位。高位不会反过来影响低位，所以每次截断保持了正确余数。

直接乘二 p 次还嫌慢，改用快速幂。result 初始一，base 初始二；指数最低二进制位为一时把当前 base 乘进 result，每轮 base 自乘、指数除二。第 t 轮的 base 对应 2 的 2^t 次方，因而恰好选中 p 的二进制分解所需因子，总共只需对数量级次乘法。

2^p 的个位只可能是二、四、八、六，减一无需借位，直接减少低位数组首项。最后从下标四百九十九到零输出，连前导零也保留，每五十个字符换行，总共十行。''',
    r'''int p;cin>>p;cout<<(long long)floor(p*log10l(2.0L))+1<<'\n';
Big result{},base{};result[0]=1;base[0]=2;
while(p){if(p&1)result=multiply(result,base);base=multiply(base,base);p>>=1;}
--result[0];for(int i=499;i>=0;--i){cout<<result[i];if(i%50==0)cout<<'\n';}''',
    '末尾数字必须精确计算并补足五百位；每行五十位，不能用普通浮点幂取余。',
    r'保留位数为 K=500，时间 $O(K^2\log p)$、额外空间 $O(K)$。',tags=['高精度','快速幂'],lessons=A+['functions','big-integers','modular','numeric-tools'],
    declarations=r'''using Big=array<int,500>;
Big multiply(const Big&a,const Big&b){
    Big c{};for(int i=0;i<500;++i)for(int j=0;i+j<500;++j)c[i+j]+=a[i]*b[j];
    for(int i=0;i<499;++i){c[i+1]+=c[i]/10;c[i]%=10;}c[499]%=10;return c;
}''',exact=True)

add('P1065','按给定次序插入机器最早空档','依给定顺序安排每个工序，满足工件先后依赖和机器互斥，始终插入最早可用空档，求全部完成时刻。',
    '保存每个工件已完成的工序数与完成时刻，以及每台机器按时间排序的已占区间。新工序从工件可开工时刻起扫描区间，找到第一个容得下它的空档再插入。',
    r'''“先安排”只表示先把一个操作放入时间表，不表示实际开工更早。样例先安排工件一在机器二的 [3,5)，随后工件三的首道工序仍能插进同机器 [0,2)，因此不能只记录一台机器最后的完成时刻。

对工件 j，next[j] 表示下次要安排哪道工序，finish[j] 表示前一道工序完成时刻。新工序耗时 d，最早开始 t=finish[j]。机器占用区间按起点排序，并使用左闭右开 [l,r)：恰好在 r 时刻开始不冲突。

依次检查区间。若 t+d≤l，当前操作能放在该区间之前，而且前面的区间都已排除，这是最早空档，立即停止。否则将 t 更新为 max(t,r)，继续找后面的空档；之前的时间要么早于工件可开工时刻，要么会和这个区间相交，已经不可能容纳当前操作。没有更多区间时放在尾部。把新区间插回当前位置，保持时间表有序，更新工件完成时刻。所有操作都安排完，取完成时刻最大值，不能把所有耗时相加，因为不同机器可以并行工作。''',
    r'''int m,n;cin>>m>>n;int q=m*n;vector<int>order(q);for(int &x:order){cin>>x;--x;}
vector<vector<int>>machine(n,vector<int>(m)),duration=machine;
for(auto &row:machine)for(int &x:row){cin>>x;--x;}
for(auto &row:duration)for(int &x:row)cin>>x;
vector<int>next(n),finish(n);vector<vector<pair<int,int>>>busy(m);int answer=0;
for(int job:order){int op=next[job]++,which=machine[job][op],d=duration[job][op],start=finish[job];
    auto &slots=busy[which];int pos=0;
    while(pos<(int)slots.size()){
        if(start+d<=slots[pos].first)break;
        start=max(start,slots[pos].second);++pos;
    }
    slots.insert(slots.begin()+pos,{start,start+d});finish[job]=start+d;answer=max(answer,finish[job]);
}cout<<answer<<'\n';''',
    '安排顺序不等于开工顺序；要寻找内部空档，区间端点相接不算冲突。',
    '共有 Q=mn 个操作，最坏时间 $O(Q^2)$、空间 $O(Q+n+m)$。',tags=['模拟'],lessons=A+['iterators'])

add('P1518','完整联合状态判环','在十乘十地图上同时模拟农夫和牛，每分钟前进或顺时针转向，求分钟末首次同格的时间，否则输出零。',
    '状态必须同时包含双方位置与方向。每分钟前检查是否相遇与联合状态是否重复，然后各自依据地图移动一次；重复状态说明以后永远循环。',
    r'''只记录两者的位置不够：同一格朝北与朝东，下一步可能完全不同。每个角色有一百个格子、四个方向，共四百种状态；两者合起来最多十六万种。地图固定、规则确定，只要完整状态重复，以后每一分钟都会重演，若此前没有相遇就永远不会相遇。

方向零到三依次为北、东、南、西。前面一格越界或为星号时，本分钟只转向，不能转完立刻前进；否则只前进一步。两个 step 调用虽然在程序中先后执行，但都只依赖各自原位置方向和固定障碍图，不读取对方位置，所以模拟的是同时行动。执行完双方这一步、分钟数加一后，下一次循环开头检查同格。途中擦肩而过或交换格子不算相遇，不能据此提前终止。

用 ((行×10+列)×4+方向) 编码单人状态，再以农夫编码×400+牛编码组合，作为访问数组下标。检测重复前先检查相遇，才能正确返回此刻的分钟数。''',
    r'''g.resize(10);Actor farmer{},cow{};for(int i=0;i<10;++i){cin>>g[i];for(int j=0;j<10;++j){if(g[i][j]=='F')farmer={i,j,0};if(g[i][j]=='C')cow={i,j,0};}}
vector<bool>seen(160000);int minutes=0;
while(true){
    if(farmer.r==cow.r&&farmer.c==cow.c){cout<<minutes<<'\n';break;}
    int state=code(farmer)*400+code(cow);if(seen[state]){cout<<0<<'\n';break;}seen[state]=true;
    step(farmer);step(cow);++minutes;
}''',
    '两者初始都朝北；遇障碍这一分钟仅转弯；相遇只看分钟末同格。',
    '联合状态上界 S=160000，时间与访问标记空间均为 $O(S)$。',tags=['模拟'],lessons=A+['structures','functions'],
    declarations=r'''struct Actor{int r,c,d;};vector<string>g;
int code(const Actor &a){return (a.r*10+a.c)*4+a.d;}
void step(Actor &a){
    int dr[4]={-1,0,1,0},dc[4]={0,1,0,-1};int r=a.r+dr[a.d],c=a.c+dc[a.d];
    if(r<0||r>=10||c<0||c>=10||g[r][c]=='*')a.d=(a.d+1)%4;else{a.r=r;a.c=c;}
}''')

add('P3799','枚举完整边长与拆分长度','从不同身份的木棒中选四根，不折断，拼成一个正三角形，统计选法并对十的九次方加七取模。',
    '四根分配到三条边，只能是一条边由两根拼成，另两边各一根。枚举完整边长 s，再枚举 a≤b 且 a+b=s，分别计算选择完整边和拼接边木棒的组合数。',
    r'''例子长度 [1,1,2,2] 中，两根二各自做一条边，两根一拼成第三条边。因为每条边至少用一根，而只有四根，所以分配一定是 2、1、1；两根单独成边的长度相同，记为 s，拼接两根的长度 a+b=s。正长度保证 a、b 都小于 s，所以它们不会和完整边从同一个长度桶里取棒。

cnt[x] 是长度 x 的木棒数量。从 s 桶选两个完整边，共 cnt[s](cnt[s]−1)/2 种。枚举 a 从一到 s/2，令 b=s−a：若 a<b，拼接边有 cnt[a]×cnt[b] 种；若 a=b，需要在同一桶取两根，有 cnt[a](cnt[a]−1)/2 种。两部分桶互不相交，因此相乘。

限制 a≤b 使交换拼接两根不重复计数；完整边也用无序选二，交换两个边的位置不是新的木棒选法。同一组合法四棒的最大长度就是 s，且恰好有两根这样的棒，所以也不会在另一个 s 或另一个拆分中再次计数。每个组合数先用 long long 精确求出再取模，两个已取模值相乘仍在 64 位范围内。''',
    r'''int n;cin>>n;vector<long long>cnt(5001);int maximum=0;while(n--){int x;cin>>x;++cnt[x];maximum=max(maximum,x);}
const long long mod=1000000007;long long answer=0;
for(int s=2;s<=maximum;++s){long long full=cnt[s]*(cnt[s]-1)/2%mod;if(full==0)continue;
    for(int a=1;a*2<=s;++a){int b=s-a;long long split=a==b?cnt[a]*(cnt[a]-1)/2:cnt[a]*cnt[b];
        answer=(answer+full*(split%mod))%mod;
    }
}cout<<answer<<'\n';''',
    '数的是选哪些木棒，不能把边的交换当新方案；相同长度取两根用组合数。',
    '最大长度为 V≤5000，时间 $O(n+V^2)$、空间 $O(V)$。',tags=['枚举','组合计数','取模与同余'],lessons=A+['counting','modular','integer'])
