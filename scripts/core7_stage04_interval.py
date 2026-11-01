"""Split points, moving endpoints, grammars and time-segment optimizations."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
D=A+['dp']

add('P1435','比较两端字符，递推区间的最少插入数',
    '在字符串任意位置插入字符，使原串成为回文串，求最少插入数，区分大小写。',
    r'''dp[l][r]表示原串闭区间l至r变成回文所需的最少插入数。两端相同便配成一对，答案取内部区间；不同则在另一端补上与某端相同的字符，取去左端与去右端两个子问题的较小值再加一。按区间长度递增，单字符与空区间初始为零。''',
    r'''例如ab的两端不同，可以补成aba或bab，都只插入一个字符。若两端本来都是a，就不必为这两个a再花一次插入，只需处理它们之间的部分。

令 $f(l,r)$ 为保留原来这一段字符、只插入新字符时的最小代价。单个字符与空串本身就是回文，代价零。

最短补全的最外层至少包含一个原端点，否则这一对都是新插入字符，删去它们还能保留原串，反而更短。若两端相同，最外字符因此也与它们相同；可以让原首字符对应最前位置、原尾字符对应最后位置，不破坏中间字符的先后关系。去掉这一对后，恰好是内部区间的补全，因此直接取内部答案。

若两端不同，最终回文的外层不可能直接让这两个原字符互相匹配。可以在右边补左端的镜像，剩下l+1至r；或在左边补右端的镜像，剩下l至r-1。两类至少覆盖一个最优安排，得到

$$f(l,r)=1+\min(f(l+1,r),f(l,r-1)).$$

按长度从短到长处理，所有依赖都已计算。长度二且两端相同时内部为空，显式取零即可；其它内部区间直接查表。长度最多一千，平方个状态足够，不需要枚举所有插入位置。''',
    r'''string s; cin>>s; int n=s.size();
vector<vector<int>> dp(n,vector<int>(n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(s[l]==s[r]) dp[l][r]=length==2?0:dp[l+1][r-1];
        else dp[l][r]=1+min(dp[l+1][r],dp[l][r-1]);
    }
}
cout<<dp[0][n-1]<<'\n';''',
    '只允许插入；字符区分大小写；空区间不访问越界下标；长度递增；原来已回文时答案零。',
    r'时间与空间均为 $O(n^2)$。',tags=['区间 DP'],lessons=D+['strings'])

add('P1775','枚举最后一次合并时的两段分界',
    '一排石子每次只能合并相邻两堆，费用为两堆总质量，求合成一堆的最小总费用。',
    r'''dp[l][r]为把连续石子l至r合成一堆的最小代价。最后一次一定把l至k、k+1至r两堆合并，费用是整个区间质量和，所以枚举k，取dp[l][k]+dp[k+1][r]+区间和的最小值。单堆不需合并，按长度递增。''',
    r'''不能直接用“每次拿两堆最轻的”代替相邻限制；两堆之间还隔着石子时，它们不能直接合并。每个中间堆始终对应原数组中的一个连续区间。

考察区间l至r最后一次合并。这时恰有两堆，它们各自覆盖l至k与k+1至r，某个分界k一定存在。无论内部怎样合并，两堆质量之和总是整个区间的质量，所以最后一步费用固定。

两侧在最后一步之前相互独立，分别采用最小费用即可。因此

$$dp[l][r]=\min_{l\le k<r}\bigl(dp[l][k]+dp[k+1][r]+S(l,r)\bigr).$$

任何真实合并方案都落在某个k中；反过来，分别完成两侧后再合并，也确实是一份合法的相邻合并方案。这样同时证明没有漏解，也没有使用不能执行的组合。

单堆初值零，区间质量用前缀和常数时间求出。长度最多三百，直接枚举区间与分界即可。费用累计使用long long，答案不是最后剩余堆的质量。''',
    r'''int n; cin>>n;
vector<long long> prefix(n+1);
for(int i=0,x;i<n;++i){cin>>x;prefix[i+1]=prefix[i]+x;}
vector<vector<long long>> dp(n,vector<long long>(n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1; dp[l][r]=LLONG_MAX/4;
        long long sum=prefix[r+1]-prefix[l];
        for(int k=l;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k+1][r]+sum);
    }
}
cout<<dp[0][n-1]<<'\n';''',
    '只能合并相邻堆；最后一步加整个区间质量；单堆代价零；求全部操作费用而非最终质量。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['区间 DP'],lessons=D+['prefix'])

add('P2734','剩余区间总分减去对手最优所得',
    '两人轮流从序列任一端取一个数，双方都使自己最终得分最大，输出先手和后手各自的得分。',
    r'''dp[l][r]表示轮到当前玩家面对这段时最多得到的总分。取左后，对手从剩余区间得到dp[l+1][r]，当前玩家最终得到整个区间总和减这个数；取右同理。取两者较大值，最后先手为dp[0][n-1]，后手为总和减先手。''',
    r'''只取眼前较大端点不一定最好，因为会改变留给对手的区间。需要比较对手也采用最优策略后的最终得分。

状态的“当前玩家”随轮次变化，不固定指先手。令区间总分为S。若当前玩家先取左端，此后对手面对l+1至r，并可得到该段的最优分dp[l+1][r]。这段游戏的总分不变，所有分都归两人之一，所以当前玩家最终所得就是S减去这个对手分数，其中已经包含刚取的左端。

取右端时，同理得到S-dp[l][r-1]。因此

$$dp[l][r]=S(l,r)-\min(dp[l+1][r],dp[l][r-1]).$$

不再额外加本次端点，否则会重复计分。只剩一项时当前玩家拿走它，初值就是该数；按长度递增计算。

整段初始轮到先手，所以先手分数为整段状态，后手得到剩余总分。双方“使自己最大”与“使对手最小”等价，是因为两人分数之和固定。''',
    r'''int n; cin>>n;
vector<int> a(n),prefix(n+1);
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i){cin>>a[i];prefix[i+1]=prefix[i]+a[i];dp[i][i]=a[i];}
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        dp[l][r]=prefix[r+1]-prefix[l]-min(dp[l+1][r],dp[l][r-1]);
    }
}
cout<<dp[0][n-1]<<' '<<prefix[n]-dp[0][n-1]<<'\n';''',
    '状态指当前行动者；对手也最优；总和减对手已含本次取数；输出双方分数而非胜负或分差。',
    r'时间与空间均为 $O(n^2)$。',tags=['区间 DP','博弈论'],lessons=D+['prefix','games'])

add('P17015','固定外侧仍在，枚举区间最后删除的元素',
    '逐个删除数组元素，每次得到它当前左右邻居之和，不存在的邻居视作零，求全部删空的最大总分。',
    r'''在数组两端补零。dp[l][r]表示外侧l-1和r+1一直保留时，删空l至r的最大得分。枚举最后删的k：先删它两边的区间，再删k；最后这次邻居恰为a[l-1]和a[r+1]。取两侧最优值与这两个固定外邻居之和的最大值。''',
    r'''删除得分取决于当时邻居，不能直接把原来相邻的两项相加。若先删中间元素，两侧会变成新的邻居，之后分数随之改变。

给原数组左右各补一个永不删除、值为零的边界。状态dp[l][r]约定：删空这一段，但两侧边界l-1和r+1暂时都不删。只有这个约定明确后，区间的收益才与外部删除顺序无关。

假定最后删k。此前l至k-1、k+1至r已经清空，k仍在，所以左子问题的右边界是k，右子问题的左边界也是k，恰与这两个子区间的状态约定一致。最后删k时，眼前邻居就是l-1与r+1，得到固定的两边数值和：

$$dp[l][r]=\max_{l\le k\le r}\bigl(dp[l][k-1]+dp[k+1][r]+a_{l-1}+a_{r+1}\bigr).$$

这里最后一步不加a_k；被删元素自身不计分。两侧先删的操作可以依次执行，或相互交错，都不会跨越尚未删除的k，因此可以分别取最优。

空区间初始零，长度递增计算。整段的两侧是补的零，最终答案正是dp[1][n]。即使原值可到十亿，总收益也只需六十四位整数。''',
    r'''int n; cin>>n;
vector<long long> a(n+2); for(int i=1;i<=n;++i) cin>>a[i];
vector<vector<long long>> dp(n+2,vector<long long>(n+2));
for(int length=1;length<=n;++length){
    for(int l=1;l+length-1<=n;++l){
        int r=l+length-1;
        for(int k=l;k<=r;++k){
            // k最后删，它自己的值不计分。
            dp[l][r]=max(dp[l][r],dp[l][k-1]+dp[k+1][r]+a[l-1]+a[r+1]);
        }
    }
}
cout<<dp[1][n]<<'\n';''',
    '按当前邻居计分；先固定外邻居不删；枚举最后删除点；不加被删元素本身；边界补零；得分六十四位。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['区间 DP'],lessons=D)

add('P1063','复制珠子头标记，枚举每段的最后合并点',
    '环形能量珠的尾标记等于下一珠头标记，合并相邻珠释放头、接缝、尾三个标记的乘积，求最大总能量。',
    r'''把头标记复制一遍并补好最后的尾标记。dp[l][r]表示把这段珠子合成一珠的最大能量。最后分成l至k和k+1至r，额外释放a[l]·a[k+1]·a[r+1]；枚举k取最大。只计算长度不超过n的段，答案是全部n种起点、长度n区间的最大值。''',
    r'''把珠子看成有头尾两个边界。若一段覆盖l至r，它聚合后的头一定是a_l，尾一定是a_{r+1}，与内部先合哪两颗无关。

最后一次把左段l至k与右段k+1至r相接，中间接缝是a_{k+1}，因此新释放的能量为

$$a_l\,a_{k+1}\,a_{r+1}.$$

两侧此前的能量分别取最大，再加最后一次，枚举所有分界即可。单珠不合并，初值零。

环上没有固定断口。将头标记序列复制一遍，每个长度n的连续窗口对应一个断口，包含原来跨过末尾与开头的相邻关系。任意环形合并过程可以在最后剩下珠子的头处断开，得到其中一个窗口的线性合并；反过来，窗口内的合并都对应环上的合法相邻聚合。所以对全部n个窗口取最大。

尾标记比最后一个头多一位，代码建立长度2n+1的头标记数组，最后一项继续取原首项。公式里接缝是k+1而非k，乘法先转long long，再累计能量。''',
    r'''int n; cin>>n;
vector<long long> original(n); for(auto &x:original) cin>>x;
vector<long long> a(2*n+1);
for(int i=0;i<=2*n;++i) a[i]=original[i%n];
vector<vector<long long>> dp(2*n,vector<long long>(2*n));
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=2*n;++l){
        int r=l+length-1;
        for(int k=l;k<r;++k){
            dp[l][r]=max(dp[l][r],dp[l][k]+dp[k+1][r]+a[l]*a[k+1]*a[r+1]);
        }
    }
}
long long answer=0;
for(int start=0;start<n;++start) answer=max(answer,dp[start][start+n-1]);
cout<<answer<<'\n';''',
    '头尾标记不同于珠子价值；接缝取k+1；复制后只计算至多n颗；枚举全部断口；首尾补值；乘积六十四位。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['区间 DP'],lessons=D)

add('P1388','把乘号数量与区间一起作为状态',
    '给定非负数字，顺序不变，恰好插k个乘号，其余间隔加号，括号任意加，求最大结果。',
    r'''dp[l][r][c]表示区间内恰有c个乘号的最大值。枚举表达式最外层运算的分界，把左右子式的乘号数分别枚举；根为加号时数量相加，根为乘号时还要加一。非负数使加法、乘法对两侧都单调，只存各状态最大值就够。''',
    r'''样例一至五、两个乘号，可以写成(1+2+3)乘四乘五，结果一百二十。只把原式按通常乘法优先级分段，会漏掉括号改变后的组合。

任何完整加乘表达式都有最外层的最后一次运算，它把原序列切成左、右两个连续子式。枚举这个分界k，以及左右各自用了多少乘号x、y。

若最后为加法，整段用x+y个乘号，候选是左右结果之和；若最后为乘法，整段用x+y+1个，候选是左右结果之积。必须分别登记到准确的数量状态，不能把“不超过”当成“恰好”。

所有原数字非负，任一子式结果也非负。固定另一侧时，加法与乘法都不会因某侧变大而下降，所以每个子状态只保存最大结果，不需要同时保存最小值。若允许负数，这个理由就不再成立。

单个数字只有零乘号状态可达，其值为该数字；其它状态为负一作为不可达标记。按区间长度递增计算，最终读取整段、恰好k个乘号。n最多十五，直接枚举两侧数量足够，中间计算用long long。''',
    r'''int n,limit; cin>>n>>limit;
vector<long long> a(n); for(auto &x:a) cin>>x;
vector<vector<vector<long long>>> dp(n,vector<vector<long long>>(n,vector<long long>(limit+1,-1)));
for(int i=0;i<n;++i) dp[i][i][0]=a[i];
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        for(int cut=l;cut<r;++cut){
            for(int x=0;x<=min(limit,cut-l);++x){
                for(int y=0;y<=min(limit,r-cut-1);++y){
                    long long left=dp[l][cut][x],right=dp[cut+1][r][y];
                    if(left<0||right<0) continue;
                    if(x+y<=limit) dp[l][r][x+y]=max(dp[l][r][x+y],left+right);
                    if(x+y+1<=limit) dp[l][r][x+y+1]=max(dp[l][r][x+y+1],left*right);
                }
            }
        }
    }
}
cout<<dp[0][n-1][limit]<<'\n';''',
    '括号任意；顺序不能改；乘号数量恰好k；根乘法多计一个乘号；零值合法，不与不可达负一混淆。',
    r'时间 $O(n^3(k+1)^2)$，空间 $O(n^2(k+1))$。',tags=['区间 DP'],lessons=D)

add('P1880','环复制成两倍长，同时求各段最小与最大合并费用',
    '圆环上的石子每次合并相邻两堆，得分为新堆质量，分别求合成一堆的最小与最大总得分。',
    r'''复制数组，把所有环形断口变为长度n的窗口。每段分别保存最小费用low和最大费用high，枚举最后的两段分界，分别取最小、最大，最后一步均加整段质量和。答案在n个长度n窗口中再次取最小与最大，单堆费用零。''',
    r'''原首堆与末堆在环上也相邻，固定只合并原数组区间会漏掉跨断口的方案。将序列接一份自身后，从任意原位置开始的n堆都能成为连续窗口。

对某个窗口，最后一次把它分成左右两段，两段各自先合成一堆，最后加上整个窗口质量。单堆不发生操作，费用零；较长区间枚举所有分界，得到

$$L(l,r)=\min_k(L(l,k)+L(k+1,r)+S(l,r)),$$

$$H(l,r)=\max_k(H(l,k)+H(k+1,r)+S(l,r)).$$

最后两堆的连接处之外还有一个环边界，选那个边界作为窗口断口，就能把任何环上方案放进某个线性窗口；窗口的任意相邻合并也都是环上合法操作。因此遍历全部断口不会漏解。

复制后的区间只计算至多n堆，不能把两份数组一起合成一堆。每次合并都按原质量和收费，最小、最大采用独立状态，不能在一个已取最小的表里再找最大。N为一时两种费用都是零，质量为零也自然适用。''',
    r'''int n; cin>>n;
vector<int> a(2*n); for(int i=0;i<n;++i){cin>>a[i];a[i+n]=a[i];}
vector<long long> prefix(2*n+1);
for(int i=0;i<2*n;++i) prefix[i+1]=prefix[i]+a[i];
vector<vector<long long>> low(2*n,vector<long long>(2*n)),high=low;
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=2*n;++l){
        int r=l+length-1; long long sum=prefix[r+1]-prefix[l];
        low[l][r]=LLONG_MAX/4;
        for(int k=l;k<r;++k){
            low[l][r]=min(low[l][r],low[l][k]+low[k+1][r]+sum);
            high[l][r]=max(high[l][r],high[l][k]+high[k+1][r]+sum);
        }
    }
}
long long minimum=LLONG_MAX,maximum=0;
for(int l=0;l<n;++l){minimum=min(minimum,low[l][l+n-1]);maximum=max(maximum,high[l][l+n-1]);}
cout<<minimum<<'\n'<<maximum<<'\n';''',
    '首尾相邻；枚举所有断口；只合并n堆；最小与最大各自递推；单堆与零质量费用为零；输出两行。',
    r'时间 $O(n^3)$，空间 $O(n^2)$。',tags=['区间 DP'],lessons=D+['prefix'])

add('P3205','记当前已形成区间，以及最后插在左端还是右端',
    '初始身高顺序任意，依次与上一个入队者比较：更矮插左、更高插右；统计生成指定最终队形的初始排列数。',
    r'''dp[l][r][0/1]表示生成目标区间l至r、最后入队者分别在左端或右端的方案数。新增左端必须比此前最后入队者矮，新增右端必须更高；前一个最后者只可能在旧区间两端，分别比较并累加。单人只给一种状态置一，避免把同一开始方式数两遍，最终两端状态相加取模。''',
    r'''插入位置比较的是上一个入队者，不是当前队形最左或最右的人。例如新加入左端后，下一个人要与这个刚入队的人比较，不能仍用另一端的身高。

在最终队形固定后，任意时刻已加入的人必须占据一个连续区间，未来只会从两侧继续扩展。最后入队的人只可能处于这段的左端或右端，因此这两个信息足以决定接下来怎样比较。

令L(l,r)、R(l,r)分别统计最后在左端、右端的数量。要把h_l加到左边，旧区间是l+1至r：若旧最后者在左端，要求h_l小于h_{l+1}；若在右端，要求h_l小于h_r。符合条件的旧方案分别累加。

同理，要把h_r加到右边，旧区间是l至r-1：旧最后在左端时要求h_r大于h_l，在右端时要求h_r大于h_{r-1}。每个初始排列有唯一的最后加入者与此前排列，几类转移不会重复。

单人左右两端其实是同一个人，初始化L(i,i)=1、R(i,i)=0即可；若两项都给一，会把每个排列翻倍。按长度递增后，答案是完整区间两项之和，模数为19650827。

身高严格互异，判断使用严格大小。n至多一千，二维区间、每段常数次比较足够。''',
    r'''int n; cin>>n; vector<int> h(n); for(int &x:h) cin>>x;
const int MOD=19650827;
vector<vector<int>> left(n,vector<int>(n)),right=left;
for(int i=0;i<n;++i) left[i][i]=1; // 单人只登记一份。
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(h[l]<h[l+1]) left[l][r]+=left[l+1][r];
        if(h[l]<h[r]) left[l][r]+=right[l+1][r];
        if(h[r]>h[l]) right[l][r]+=left[l][r-1];
        if(h[r]>h[r-1]) right[l][r]+=right[l][r-1];
        left[l][r]%=MOD; right[l][r]%=MOD;
    }
}
cout<<(left[0][n-1]+right[0][n-1])%MOD<<'\n';''',
    '比较上一个入队者；区间末次位置要分两类；单人只初始化一次；身高互异使用严格比较；模数19650827。',
    r'时间与空间均为 $O(n^2)$。',tags=['区间 DP','组合计数'],lessons=D+['counting','modular'])

add('P4290','逆着替换规则，将左右子串归约为一个可能字母',
    'WING四个字母按给定的一变二规则扩展，给定最终名字，求可能的初始字母，按WING顺序输出。',
    r'''dp[l][r]用四位集合表示这段能由哪些单字母产生。单字符只含自身；枚举分界，把左右可能字母对照规则合成父字母。预先为十六种左集合与十六种右集合算好合成表，使每个分界只需一次查表和按位或。整段集合为空就输出原题无解句子。''',
    r'''若W可以变成II，那么两个I构成的子串可以归约为W；如果另有N也能变成II，同一子串就同时可能来自W或N，不能只留下一个来源。

一次扩展把一个字母变成两个，其后的所有扩展各自作用于这两个子树。最终串必能在某个位置分成左、右两段，分别来自某两个字母；反过来，只要父字母能变成这两个字母，并且两段各自可生成，就能生成整段。

于是以区间保存全部可能父字母，按长度递增，枚举最后分界。四种字母恰可用四位二进制表示，某位为一表示对应来源可行；合并不同分界时做按位或即可。

把规则反存为parent[x][y]，记录哪几个字母能产生左右字母x、y。对左右集合的全部十六种取值预先枚举字母对，得到合成表combine。区间转移就能把一次分界的多对字母检查变成一个常数查表。

长度一允许一次扩展都不做，只登记原字母。最后严格按照W、I、N、G顺序检查，不按字母表顺序；若无任何可行初始字母，按原题输出The name is wrong!。''',
    r'''string alphabet="WING";
vector<int> count(4); for(int &x:count) cin>>x;
int parent[4][4]={};
for(int c=0;c<4;++c){
    for(int i=0;i<count[c];++i){string rule;cin>>rule;int x=alphabet.find(rule[0]),y=alphabet.find(rule[1]);parent[x][y]|=1<<c;}
}
int combine[16][16]={};
for(int a=0;a<16;++a) for(int b=0;b<16;++b){
    for(int x=0;x<4;++x) if(a>>x&1){
        for(int y=0;y<4;++y) if(b>>y&1) combine[a][b]|=parent[x][y];
    }
}
string s; cin>>s; int n=s.size();
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i) dp[i][i]=1<<alphabet.find(s[i]);
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){int r=l+length-1;for(int k=l;k<r;++k) dp[l][r]|=combine[dp[l][k]][dp[k+1][r]];}
}
if(!dp[0][n-1]) cout<<"The name is wrong!";
else for(int c=0;c<4;++c) if(dp[0][n-1]>>c&1) cout<<alphabet[c];
cout<<'\n';''',
    '规则方向是父字母变成左右两字母；保留所有可行来源；单字符无需扩展；输出顺序WING；无解句子的大小写和感叹号。',
    r'四字母集合大小固定，时间 $O(L^3)$，空间 $O(L^2)$。',tags=['区间 DP'],lessons=D+['strings','bitwise','arrays'])

add('P10236','剩余区间之外再记上一次从哪端取走',
    '从双端队列依次取数构成序列，相邻两数得分为前者的后者次幂模998244353；只对单对取模，求总分最大值。',
    r'''先预计算有向得分score[x][y]，零的零次方单独设零。状态保存剩余区间，以及上一项是刚从左外侧还是右外侧取走；上一项因此分别为a[l-1]或a[r+1]。再取左或右时加对应得分，转到更短区间。第一次取数没有前驱，分别枚举从两端开始；总分用六十四位且不再取模。''',
    r'''同一剩余区间可能有不同的上一项，而下一次新增得分取决于这项，不能只保存区间一个最优值。上一项一定是刚从剩余区间旁边取掉的数：或者左边的a[l-1]，或者右边的a[r+1]，无需记更远的全部取数历史。

定义L(l,r)为上一项在左外侧、剩余l至r时，未来还能得到的最大分数；R类似。若上一项为v，再取左端的候选是score(v,a_l)+L(l+1,r)，再取右端是score(v,a_r)+R(l,r-1)。空区间后没有新相邻对，贡献零。

按剩余长度从小到大处理。L仅在l大于零时有意义，R仅在r不是末尾时有意义。每种状态仍枚举两种下一步，取最大值。

游戏第一步没有前驱得分，若先取原左端，就从L(1,n-1)开始；若先取原右端，则从R(0,n-2)开始。取两者最大即可，不额外奖励第一项。

每个有向数对用二进制快速幂预计算；前后交换可能不同，不能把矩阵当成对称。原题特别规定零的零次方为零，而正数的零次方仍是一。单对得分已经取模，总分不能再取模；最多近一千个约十亿的分数，用long long累计。

同一输入可有多组，逐组输出。''',
    r'''int tests; cin>>tests;
while(tests--){
    int n; cin>>n; vector<int>a(n); for(int &x:a) cin>>x;
    vector<vector<long long>> score(n,vector<long long>(n));
    for(int i=0;i<n;++i) for(int j=0;j<n;++j) score[i][j]=power(a[i],a[j]);
    vector<vector<long long>> left(n,vector<long long>(n)),right=left;
    for(int length=1;length<n;++length){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1;
            long long afterLeft=length==1?0:left[l+1][r];
            long long afterRight=length==1?0:right[l][r-1];
            if(l>0) left[l][r]=max(score[l-1][l]+afterLeft,score[l-1][r]+afterRight);
            if(r+1<n) right[l][r]=max(score[r+1][l]+afterLeft,score[r+1][r]+afterRight);
        }
    }
    cout<<max(left[1][n-1],right[0][n-2])<<'\n';
}''',
    '得分有方向；零的零次方为零；第一项无前驱得分；状态带前一次来源；总分不取模；多组输入分别计算。',
    r'模数为M，时间 $O(n^2\log M)$，空间 $O(n^2)$。',tags=['区间 DP','快速幂'],lessons=D+['modular'],
    declarations=r'''long long power(long long base,int exponent){
    const long long MOD=998244353;
    if(base==0&&exponent==0) return 0;
    long long answer=1;
    while(exponent){
        if(exponent&1) answer=answer*base%MOD;
        base=base*base%MOD; exponent>>=1;
    }
    return answer;
}''')

add('P13439','用已空牢房作边界，枚举下一名首先释放的囚犯',
    '一排牢房初始住满，释放一人会通知同一连续住人段的其余所有人并各付一金币，给定待释放编号，求最少总贿赂。',
    r'''在待释放编号两端补0和P+1。dp[l][r]表示两侧边界已经空、其中所有指定囚犯尚待释放的最小费用。先释放中间某个k，会向左右两个空边界之间的其余住客付款，人数为pos[r]-pos[l]-2；此后左右互不通知，递归两段。按边界跨度递推，最后输出Case #编号: 费用。''',
    r'''释放囚犯会把原来的住人段分成两段，以后消息不能穿过空牢房。需要贿赂的不只名单上的人，而是当前连通段内除本次释放者之外的全部住客。

将Q个待释放位置排序，并补边界位置零与P+1。定义dp[l][r]：边界pos[l]、pos[r]已经空，二者之间所有名单位置尚未释放时的最少费用。若没有名单位置，费用零，即使其中还有永不释放的人，也不会再有通知。

若先释放名单位置k，当前这段住人位置数是pos[r]-pos[l]-1，去掉当次释放的人，需要再减一，所以当前贿赂为pos[r]-pos[l]-2。这一费用不取决于k的具体位置。

释放k后，两侧独立，得到

$$dp[l][r]=\min_{l<k<r}(dp[l][k]+dp[k][r]+pos[r]-pos[l]-2).$$

按边界跨度递增，最后读取最外两个边界的状态。P可到一万，但名单最多一百，状态按名单下标开表即可。每个输入案例都要从一开始编号，使用原题Case格式。''',
    r'''int tests; cin>>tests;
for(int test=1;test<=tests;++test){
    int cells,q; cin>>cells>>q; vector<int>pos(q+2); pos[q+1]=cells+1;
    for(int i=1;i<=q;++i) cin>>pos[i];
    vector<vector<int>>dp(q+2,vector<int>(q+2));
    for(int gap=2;gap<=q+1;++gap){
        for(int l=0;l+gap<=q+1;++l){
            int r=l+gap; dp[l][r]=INT_MAX/4;
            for(int k=l+1;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k][r]+pos[r]-pos[l]-2);
        }
    }
    cout<<"Case #"<<test<<": "<<dp[0][q+1]<<'\n';
}''',
    '支付给整段住客，不只名单；两个边界均不住人；当前释放者不收贿赂；费用减二；多组Case编号。',
    r'每组时间 $O(Q^3)$，空间 $O(Q^2)$。',tags=['区间 DP'],lessons=D)

add('UVA1362','分出第一个孩子的完整往返，再处理根的其余孩子',
    '机器人按固定左右次序遍历有根洞穴树，每次进入洞穴都记颜色，给定记录，数有多少种有序树能产生它，模十亿。',
    r'''子树的记录以根颜色开始并结束，长度为奇数。dp[l][r]为产生这段记录的树数，单个字符为一。选第一个孩子访问完、重新回到根的位置k，则孩子记录为l+1至k-1，根与后续孩子的记录为k至r，方案数相乘；枚举所有同根颜色的k求和。读取至文件结束。''',
    r'''[原始PDF](https://onlinejudge.org/external/13/1362.pdf)把左右次序不同的洞穴系统视作不同；机器人进入子洞穴会记它的颜色，返回父洞穴时也会再记父颜色，不能只按首次访问的颜色串计数。

每条树边下去、回来各一次，若子树有v个结点，其记录长度为2v-1，首尾都是根颜色。长度偶数或首尾颜色不同不可能是完整子树；单个字符表示只有一个洞穴，只有一种结构。

对非单点树，考察根的第一个孩子。设它访问完后第一次回到根，记录位置为k。l+1至k-1是这个孩子的完整记录，k至r则是根接着遍历其余孩子的记录，后者也可独立看作一棵以同色根开始的有序树。

因此当首尾颜色相同，可以枚举k=l+2、l+4等到r，且k处颜色须与根相同：

$$dp[l][r]=\sum_k dp[l+1][k-1]\,dp[k][r]\pmod{10^9}.$$

固定k后，两个部分的树结构独立，所以相乘；不同k意味着第一个孩子子树大小不同，不重复。给任意两棵合法的部分树，把第一棵作为第二棵根的第一个孩子接入，就得到唯一的完整有序树，故转移既完整又可实现。

按奇数长度递增。记录长度最多三百，乘积先用long long，每项加入后取模。输入样例包含不止一条记录，程序逐个读到文件结束并各输出一行。''',
    r'''const long long MOD=1000000000;
string s;
while(cin>>s){
    int n=s.size();
    if(n%2==0){cout<<0<<'\n';continue;}
    vector<vector<long long>> dp(n,vector<long long>(n));
    for(int i=0;i<n;++i) dp[i][i]=1;
    for(int length=3;length<=n;length+=2){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1;
            if(s[l]!=s[r]) continue;
            for(int returned=l+2;returned<=r;returned+=2){
                if(s[returned]==s[l]) dp[l][r]=(dp[l][r]+dp[l+1][returned-1]*dp[returned][r])%MOD;
            }
        }
    }
    cout<<dp[0][n-1]<<'\n';
}''',
    '回到父洞也记颜色；树的孩子有左右次序；完整记录为奇数长度且首尾同色；分第一个孩子；模十亿而非十亿加七。',
    r'每条长度L，时间 $O(L^3)$，空间 $O(L^2)$。',tags=['区间 DP','组合计数'],lessons=D+['strings','trees','counting','modular'])

add('UVA10003','以两端切口为边界，枚举当前木段的第一次切割',
    '木棍需在给定位置切开，每刀费用等于当时所在木段的长度，求完成全部切口的最小总费用。',
    r'''在切口列表两端补零与木棍全长。dp[l][r]表示完成两端切口之间所有切割的最小费用。若中间有切口，枚举第一刀k，当前支付pos[r]-pos[l]，之后两段独立，费用加dp[l][k]+dp[k][r]；相邻切口间不需再切，初值零。多组输入以木长零结束。''',
    r'''[原始PDF](https://onlinejudge.org/external/100/10003.pdf)按“这一刀切的是多长木段”收费，而不是按切口到原点的距离。例如长十、切在二四七：先切二需十，再切四需八，再切七需六，共二十四；改为先切四，总费可以降到二十。

将已有切口看作木段边界，并把零与全长加入列表。状态dp[l][r]表示位置pos[l]到pos[r]之间的所有指定切割还没做时，完成它们的最少费用。

如果两边界间没有其它切口，已经无需操作，代价零。否则第一刀必是某个中间位置k，这一刀面对整段，所以费用固定为pos[r]-pos[l]。切开以后，两半不再影响对方收费，分别取最优即可：

$$dp[l][r]=\min_{l<k<r}(dp[l][k]+dp[k][r]+pos[r]-pos[l]).$$

按边界下标跨度递增计算，最后读取最外层。每个真实切割顺序都有唯一第一刀，反过来先切k再按两侧最优顺序切，确实能实现候选代价。

输入不是只有一个案例，木长零只是终止标记，不读取后续切口，也不输出对应结果。答案句子末尾要有句点。''',
    r'''int length;
while(cin>>length&&length){
    int n; cin>>n; vector<int> pos(n+2); pos[n+1]=length;
    for(int i=1;i<=n;++i) cin>>pos[i];
    vector<vector<int>> dp(n+2,vector<int>(n+2));
    for(int gap=2;gap<=n+1;++gap){
        for(int l=0;l+gap<=n+1;++l){
            int r=l+gap; dp[l][r]=INT_MAX/4;
            for(int k=l+1;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k][r]+pos[r]-pos[l]);
        }
    }
    cout<<"The minimum cutting is "<<dp[0][n+1]<<".\n";
}''',
    '收费为当前木段全长；枚举第一刀；无中间切口费用零；切口顺序已递增；木长零只结束输入；输出完整句子。',
    r'每组n个切口，时间 $O(n^3)$，空间 $O(n^2)$。',tags=['区间 DP'],lessons=D)

add('P1070','按顺时针路径分组，用滑动窗口维护机器人起始时刻',
    '环上机器人每秒顺时针走一段，寿命一到p秒，消失后必须立刻另买；费用最后结算，求m秒的最大净金币，可为负。',
    r'''令f[t]为恰好完成前t秒的最大净收益。最后一个机器人从时刻s开始，至t最多p秒。按“道路编号减时间”不变的n条路径分组，各自保存累计金币；一段候选等于这段收集的金币，加此前最优收益，再减购买价。把与s有关的部分放进滑动窗口，用单调双端队列维护最大值，每秒遍历n条路径，总计O(nm)。''',
    r'''不能把收益为负的时间跳过：游戏开始后始终只有一个机器人在工作，消失便须立刻买下一个；初始金币不足也无妨，因为费用最后结算。因此f[t]是恰好覆盖前t秒的收益，不是可以随时停玩的最大值。

最后一个机器人开始于已经完成s秒之后，行走到第t秒，持续t-s秒，范围一到p。起厂x决定它依次经过哪条道路，候选收益为f[s]减购买价，再加这段移动收集的金币。直接枚举t、s、起厂会达到十亿量级，需要合并反复求最大值的部分。

道路和时间都改为从零编号。机器人在时间u走的道路是起厂加已经走的步数，所以道路编号减u对n取模保持不变，记作d。固定d以后，整段轨迹已确定；设P_d(t)为这条轨迹前t秒的金币总和，开始时刻s的起厂恰是(d+s)模n。先把只依赖开始时刻的部分记为

$$G_d(s)=f[s]-P_d(s)-c_{(d+s)\bmod n}.$$

这里c为购买价。先求每条路径在时刻t结束的最好候选，再在路径之间取最大：

$$H_d(t)=P_d(t)+\max_{t-p\le s<t}G_d(s),$$

$$f[t]=\max_d H_d(t).$$

固定d，$G_d(s)$只依赖候选开始时刻s。随着t增加，合法s窗口也向右移动。用双端队列保存候选时刻及其值，值从队首到队尾严格递减：加入新的s时，若旧队尾值不大于新值，就删旧队尾，因为新候选至少一样好且更晚过期；再删去早于t-p的队首。剩下队首就是窗口最大值。

每秒先把s=t-1作为新候选加入，使用的是上一秒f和此前轨迹前缀；再累加这一秒金币，得到P_d(t)，计算当前候选。所有路径都处理完，才把本秒最优赋给f，防止把同秒刚算出的值误当旧状态。

每个候选在自己的队列中至多进出一次，因此总时间为nm。购买价每段只扣一次，机器人结束后可以在任意工厂重新买，状态无需记上一台的终点。收益允许负数，当前最优用负无穷初始化，不能擅自与零取最大。''',
    r'''int n,m,p; cin>>n>>m>>p;
vector<vector<int>> coin(n,vector<int>(m));
for(auto &row:coin) for(int &x:row) cin>>x;
vector<int> cost(n); for(int &x:cost) cin>>x;
vector<long long> prefix(n);
vector<deque<pair<int,long long>>> window(n);
long long best=0;
for(int t=1;t<=m;++t){
    int s=t-1; long long next=LLONG_MIN/4;
    for(int d=0;d<n;++d){
        int road=(d+s)%n;
        long long candidate=best-prefix[d]-cost[road];
        auto &q=window[d];
        while(!q.empty()&&q.back().second<=candidate) q.pop_back();
        q.push_back({s,candidate});
        while(q.front().first<t-p) q.pop_front();
        prefix[d]+=coin[road][s];
        next=max(next,prefix[d]+q.front().second);
    }
    best=next; // 全部路径都只读取同一个上一秒最优值。
}
cout<<best<<'\n';''',
    '必须覆盖全部m秒；收益可负；按道路减时间归类；先插旧时刻再加当秒金币；窗口保留t-p；每段只扣一次购买费。',
    r'时间 $O(nm)$，输入矩阵与候选队列空间 $O(nm+np)=O(nm)$。',tags=['区间 DP','队列'],lessons=D+['queue-stack','modular'])

add('P6006','先数固定两端的三元组，再用区间容斥合并',
    '给定整数数组，多次查询连续区间中三个不同下标、数值和为零的无序三元组数量，重复数值按下标分别计数。',
    r'''固定左端l，右端r从l+1向右扫描，用频次数组维护严格位于两者之间的数，查-a[l]-a[r]得到同时以l、r为两端的三元组数。再用ans[l+1][r]+ans[l][r-1]-ans[l+1][r-1]加这次端点计数，得到整个区间答案。每个左端结束时撤回本轮加入的频次，避免每轮清空两百万格。''',
    r'''三个零位于不同下标时，也是一份合法三元组；若有四个零，就有四种选下标方式。这里不能按数值去重，也不能把同一个下标重复使用。

把一个三元组唯一写成l小于k小于r，先固定它的最左与最右下标。需要中间值等于负的两端数值和。固定l、让r递增，频次表只保存l与r之间的元素；必须先查询再加入a_r，防止把右端自己当成中间项。

记这个两端都使用的数量为C(l,r)，整个区间内三元组数为F(l,r)。F(l+1,r)收集不使用l的组，F(l,r-1)收集不使用r的组，它们共同包含的F(l+1,r-1)被加了两次，扣去一次；还缺同时使用两端的组，补C：

$$\begin{aligned}F(l,r)={}&F(l+1,r)+F(l,r-1)\\&-F(l+1,r-1)+C(l,r).\end{aligned}$$

左端从大到小、右端从小到大处理，这三个旧区间都已计算。每轮固定左端后，将本轮加入的所有元素频次逐个减回，代价与该轮扫描次数相同。若每轮完整清空两百万长度的表，就会多做数十亿次操作。

数组值在正负一百万内，频次下标统一加一百万；查询所需的数可能在范围外，此时端点计数为零。区间表用long long，查询直接查表。n为五千时，完整平方表约两百MB，另加频次表，仍须注意使用连续数组而不是给每个状态附带额外对象。''',
    r'''int n,queries; cin>>n>>queries;
vector<int> a(n+1); for(int i=1;i<=n;++i) cin>>a[i];
const int SHIFT=1000000; vector<int> frequency(2*SHIFT+1);
int stride=n+2; vector<long long> answer(1LL*stride*stride);
auto at=[&](int l,int r)->long long& {return answer[1LL*l*stride+r];};
for(int l=n;l>=1;--l){
    for(int r=l+1;r<=n;++r){
        int needed=-a[l]-a[r];
        long long endpoints=(needed>=-SHIFT&&needed<=SHIFT)?frequency[needed+SHIFT]:0;
        at(l,r)=at(l+1,r)+at(l,r-1)-at(l+1,r-1)+endpoints;
        ++frequency[a[r]+SHIFT]; // 先查询，再让右端成为下一轮的中间项。
    }
    for(int r=l+1;r<=n;++r) --frequency[a[r]+SHIFT];
}
while(queries--){int l,r;cin>>l>>r;cout<<at(l,r)<<'\n';}''',
    '三个不同下标；固定最左与最右后只数中间；先查再加入；频次逐项撤回；容斥扣交集；计数六十四位。',
    r'值域宽度为V，时间 $O(n^2+Q+V)$，空间 $O(n^2+V)$。',tags=['区间 DP','组合计数'],lessons=D+['counting','lambda-local'])

add('P7129','区间递推每关最高分，再做必须正次数解锁的有界背包',
    '每关冰淇淋先吃指定位置，再从已吃区间两边扩展，按吃的次序乘美味度得分；关卡只能逐级解锁，有体力和每关次数限制。',
    r'''每关先求best[l][r]：从指定位置开始，恰吃完这个连续区间的最大分数，扩展一端时乘以新区间长度，得到单次最高分g。外层dp[c]只表示已经把此前所有关都至少玩一次、恰耗体力c的最高分；当前关次数必须一到m。对体力按费用s分余数类，维护前驱下标在q-m至q-1的最大值，用单调队列把有界转移降到每关O(t)。允许在任一关后结束，答案随各前缀更新。''',
    r'''不能把每关当成可任意跳过的独立物品。即使第二关性价比再高，也必须先支付第一关至少一次的体力，才能玩第二关；但游戏允许不开始后面的关。

先看一关。已吃的冰淇淋始终是包含指定位置c的连续区间。令best[l][r]表示恰吃完这段的最高分，单点c的值为它的美味度，乘数一。若下一步吃左边l-1，乘数就是当前长度加一；向右也相同。不同顺序只要形成同一已吃区间，下一步可选的两端与乘数完全相同，所以只留最高分。按长度扩展至整段，得到这一关玩一次的收益g。

重复玩同关时规则相同，每次都能取g。外层用精确体力背包，但要求此前每关都已至少玩一次。初始只有零关、零体力、零分。转入当前关，必须选择x次，范围一到m，且xs不超过当前体力c：

$$new[c]=\max_x(old[c-xs]+xg).$$

若直接枚举所有x，最大范围会很慢。固定体力余数r，把c写成r+qs，前驱写成r+js，则x=q-j，合法j范围为q-m至q-1。转移整理为

$$H(j)=old[r+js]-jg,$$

$$new[r+qs]=qg+\max_{q-m\le j<q}H(j).$$

这又是随q右移的固定宽度窗口。队列中保存可达前驱j及其H(j)值，值递减；加入新的j=q-1前驱，删掉被它支配的队尾，再删早于q-m的队首。队首给出当前最优。注意上界是q-1，不能包含q，否则等于本关玩零次，会绕过解锁条件。

每处理完一关，当前数组只代表连续通关到这里的方案；把它所有状态与总答案比较，即允许此时结束。若仅输出最后一关数组的最大值，会错误要求所有关都玩过。空游戏零分同样合法。

单次得分、重复次数和多关累积都可能很大，用long long，无法达到的精确体力状态不加入队列。''',
    r'''int n,budget; cin>>n>>budget;
const long long NEG=LLONG_MIN/4;
vector<long long> dp(budget+1,NEG); dp[0]=0; long long answer=0;
for(int stage=0;stage<n;++stage){
    int cost,limit,k,center; cin>>cost>>limit>>k>>center; --center;
    vector<long long> y(k); for(auto &x:y) cin>>x;
    vector<vector<long long>> best(k,vector<long long>(k,NEG));
    best[center][center]=y[center];
    for(int length=1;length<k;++length){
        for(int l=0;l+length<=k;++l){
            int r=l+length-1; if(best[l][r]==NEG) continue;
            if(l>0) best[l-1][r]=max(best[l-1][r],best[l][r]+(length+1)*y[l-1]);
            if(r+1<k) best[l][r+1]=max(best[l][r+1],best[l][r]+(length+1)*y[r+1]);
        }
    }
    long long gain=best[0][k-1];
    vector<long long> next(budget+1,NEG);
    for(int residue=0;residue<cost&&residue<=budget;++residue){
        deque<pair<int,long long>> window;
        for(int q=0,c=residue;c<=budget;++q,c+=cost){
            int j=q-1; // 至少玩一次，前驱不能是当前q。
            if(j>=0&&dp[c-cost]!=NEG){
                long long value=dp[c-cost]-j*gain;
                while(!window.empty()&&window.back().second<=value) window.pop_back();
                window.push_back({j,value});
            }
            while(!window.empty()&&window.front().first<q-limit) window.pop_front();
            if(!window.empty()) next[c]=window.front().second+q*gain;
        }
    }
    dp.swap(next);
    for(long long value:dp) answer=max(answer,value);
}
cout<<answer<<'\n';''',
    '首口固定；已吃区间连续；第j口乘j；每个此前关卡都必须玩过；当前次数至少一；允许提前结束；精确体力不可达需区分；六十四位得分。',
    r'时间 $O(\sum_i k_i^2+nt)$，空间 $O(\max_i k_i^2+t)$。',tags=['区间 DP','背包 DP','队列'],lessons=D+['knapsack','queue-stack'])

add('UVA1626','区间配对或分段，按记录恢复最短括号补全',
    '只插入圆括号或方括号，使原序列按顺序成为某个合法括号串的子序列，输出最短的一个，允许空串。',
    r'''dp[l][r]为补全这段的最少插入数。单字符需补一个；两端正好配对时可转内部，否则也要枚举所有分割，取两段补全代价之和。恢复时，单字符输出对应的一对，端点匹配且达到最优就包住内部，否则找一个达到最优的分界并依次输出。按原输入格式读取空行，案例输出间空一行。''',
    r'''[原始PDF](https://onlinejudge.org/external/16/1626.pdf)允许空序列，且原字符只须保持为子序列，不要求连续。比如原串([)]不能靠交换字符修好，只能插入；圆括号必须与圆括号配，方括号也须同类，方向不能反。

令dp[l][r]表示只增加字符、将这段补成合法串的最少插入数。单个字符无论开闭，都补对应另一半，代价一；空段为零。

任意非空合法串要么由一对匹配括号包住内部，要么分成两个非空合法串。若原两端本就可成一对，可以保留它们，只处理内部；对每个原字符分界k，还可分别补全l至k和k+1至r再拼接。取这些候选的最小值即可。若最外一对有新插入字符，对应部分也能由单字符补全与分段表达，不会因此漏解。

求完最少插入数后，还要输出实际字符串。单点输出一对同类括号；若两端匹配且内部状态恰达到当前最优，就输出左括号、内部恢复结果、右括号；否则枚举一个两侧代价之和等于最优值的分界，分别恢复。每步输出都保留原字符先后次序，不必追求字典序。

输入先有案例数及一个分隔空行，每个案例本身占一行，案例之间再隔空行。不能任意跳过全部空行，否则空序列案例会被吞掉。程序按这个格式逐行读取；每两个输出案例之间也打印一个空行。''',
    r'''int tests; cin>>tests; string s,line;
getline(cin,line); getline(cin,line); // 行尾与首个案例前的分隔空行。
for(int test=0;test<tests;++test){
    getline(cin,s); int n=s.size();
    vector<vector<int>> dp(n,vector<int>(n));
    auto match=[](char a,char b){return (a=='('&&b==')')||(a=='['&&b==']');};
    for(int i=0;i<n;++i) dp[i][i]=1;
    for(int length=2;length<=n;++length){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1; dp[l][r]=n+1;
            if(match(s[l],s[r])) dp[l][r]=length==2?0:dp[l+1][r-1];
            for(int k=l;k<r;++k) dp[l][r]=min(dp[l][r],dp[l][k]+dp[k+1][r]);
        }
    }
    function<void(int,int)> emit=[&](int l,int r){
        if(l>r) return;
        if(l==r){cout<<((s[l]=='('||s[l]==')')?"()":"[]");return;}
        int inside=r-l==1?0:dp[l+1][r-1];
        if(match(s[l],s[r])&&dp[l][r]==inside){cout<<s[l];emit(l+1,r-1);cout<<s[r];return;}
        for(int k=l;k<r;++k){
            if(dp[l][r]==dp[l][k]+dp[k+1][r]){emit(l,k);emit(k+1,r);return;}
        }
    };
    if(test) cout<<'\n';
    emit(0,n-1); cout<<'\n';
    if(test+1<tests) getline(cin,line); // 只消费案例间的一个分隔行。
}''',
    '只插不删不交换；括号类型和方向均要配对；分割也要枚举；空序列保留；恢复实际最优串；案例间空行。',
    r'长度L，时间 $O(L^3)$，空间 $O(L^2)$。',tags=['区间 DP'],lessons=D+['strings','recursion','lambda-local'],checker='bracket_supersequence')

add('CF1336C','把目标后面视为任意字符，反推最后一次放在哪一端',
    '顺序取S的前缀字符，每次放到新串首或尾，可以提前停止，数最后串以T为前缀的操作序列，操作不同即使结果相同也分别计数。',
    r'''dp[l][r]为用S的前r-l+1个字符填到目标位置l至r的操作数，位置小于m须匹配T，后面任意。最后使用的字符可放左端或右端，分别在匹配条件满足时从更短区间累加。单字符状态为二，因为第一次放首、放尾仍是两种操作；答案累加所有长度至少m、从位置零开始的状态。''',
    r'''第一次向空串放一个字符，放在头与放在尾得到同一个字符串，但原题把它们算作不同操作。因此单字符不能只计一种。不同停止长度也分别计数，不能只统计用完整个S的结果。

把最终位置从零编号，前m位必须等于T，后面的字符不受限制。dp[l][r]统计：已经按原顺序使用S的前len个字符，恰好填成最终位置l至r这段，所有受约束位置都匹配时，有多少个操作序列；其中len为r-l+1。

第len次使用的字符是S[len-1]。如果它最后放在左端，需要该位置没有约束，或等于T[l]，再接上此前填l+1至r的序列；放在右端则检查r并从l至r-1转移。两个分支代表不同的最后操作，即使字符相同也不能合并去重。

长度一时，只要S[0]能放进这个位置，状态为二，分别对应第一次放首与放尾；否则为零。后续按长度递增，所有依赖已算完。

真正的结果串从位置零开始，并且长度至少m，才能完整拥有前缀T。因此答案为

$$\sum_{len=m}^{n}dp[0][len-1]\pmod{998244353}.$$

不把内部区间的状态也加入答案，也不漏掉可以提前停止的长度。n至多三千，二维表使用int保存模数内结果。''',
    r'''string s,t; cin>>s>>t; int n=s.size(),m=t.size();
const int MOD=998244353;
vector<vector<int>> dp(n,vector<int>(n));
for(int i=0;i<n;++i) if(i>=m||s[0]==t[i]) dp[i][i]=2;
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(l>=m||s[length-1]==t[l]) dp[l][r]+=dp[l+1][r];
        if(r>=m||s[length-1]==t[r]) dp[l][r]+=dp[l][r-1];
        if(dp[l][r]>=MOD) dp[l][r]-=MOD;
    }
}
int answer=0;
for(int length=m;length<=n;++length){answer+=dp[0][length-1];if(answer>=MOD) answer-=MOD;}
cout<<answer<<'\n';''',
    '操作序列计数而非不同结果串；首步有两种；所有停止长度都要计；T以后的位任意；只累加从位置零开始的区间。',
    r'时间与空间均为 $O(n^2)$。',tags=['区间 DP','组合计数'],lessons=D+['strings','counting','modular'])
