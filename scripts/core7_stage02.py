"""Problem-specific methods for the second curriculum stage."""
from core7_authoring import add

ARRAY=['io-basics','arrays','vector','basic-control']
SORT=ARRAY+['sort','iterators']

add('P1152','标记相邻差值',r'检查相邻元素绝对差是否恰好包含一到 n−1 的全部整数。',
    '一共有 n−1 个相邻差，逐个标记合法范围内的差，最后检查一到 n−1 是否全部出现。',
    r'''[1,4,2,3] 的相邻绝对差是三、二、一，恰好每种需要的差都有。相邻差只有 n−1 个，而需要覆盖的整数也有 n−1 种，所以全部覆盖时自然没有重复或越界。

seen[d] 表示差 d 是否出现。只在 1≤d<n 时访问标记数组，防止输入差太大造成越界；然后检查每个必需值。如果某次出现零、越界或重复，剩下的相邻对已经不足以补齐全部种类，最终检查会发现缺少一项。n=1 时没有相邻差，也没有需要覆盖的整数，条件自然成立。''',
    r'''int n;while(cin>>n){vector<long long>a(n);for(auto &x:a)cin>>x;vector<bool>seen(n);
    for(int i=1;i<n;++i){long long d=abs(a[i]-a[i-1]);if(d>0&&d<n)seen[d]=true;}
    bool ok=true;for(int d=1;d<n;++d)if(!seen[d])ok=false;
    cout<<(ok?"Jolly":"Not jolly")<<'\n';
}''',
    '计算的是相邻绝对差；标记前检查范围，n=1 也成立。',
    '每组时间与空间均为 $O(n)$。',tags=['模拟'],lessons=ARRAY+['basic-arithmetic'])

add('P1059','布尔桶去重并升序扫描','对一到一千范围内的随机数去重，并按升序输出不同数字。',
    '用布尔桶记录某个值是否出现，再从一到一千顺序扫描；出现过的值只输出一次。',
    '输入二十、四十、二十时，第二次看到二十只会把同一个桶再次设为 true，仍只保留一个二十。桶的下标直接等于数字值，按下标升序扫描就自然得到排序结果。先统计 true 桶数量作为第一行，再按同一顺序输出各个值。这里适用桶，是因为值域只有一千；数值到十的九次方时不能照搬同等大的数组。',
    r'''int n;cin>>n;bool present[1001]={};while(n--){int x;cin>>x;present[x]=true;}
int count=0;for(int x=1;x<=1000;++x)count+=present[x];cout<<count<<'\n';
bool first=true;for(int x=1;x<=1000;++x)if(present[x]){if(!first)cout<<' ';cout<<x;first=false;}cout<<'\n';''',
    '只保留是否出现，不保存重复次数；使用题目给定的小值域。',
    '值域为 V，时间 $O(n+V)$、空间 $O(V)$，本题 V=1000。',tags=['排序'],lessons=['io-basics','arrays','basic-control'])

add('P1059','排序后保留每段首项','对给定数字去重，并按升序输出不同数字。',
    '先排序，让相同值相邻；遍历时仅在当前位置为首项或与前一项不同的情况下加入答案。',
    '例如 [20,40,20,15] 排序后为 [15,20,20,40]，相同的二十已经挨在一起，只留下这一段的第一个即可。排序保证同值元素构成连续段，所以检查相邻是否相等足以判断当前项是否是一个新值，不需要再扫描整个已输出答案。先用另一个数组保存各段首项，再输出数组长度和内容。这种做法不依赖数值范围，代价是一次比较排序。',
    r'''int n;cin>>n;vector<int>a(n),answer;for(int &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)if(i==0||a[i]!=a[i-1])answer.push_back(a[i]);
cout<<answer.size()<<'\n';for(int i=0;i<(int)answer.size();++i)cout<<answer[i]<<(i+1==(int)answer.size()?'\n':' ');''',
    'i=0 时没有前一项，必须先单独判断；重复项只保留一份。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序'],lessons=SORT,key='comparison-sort')

add('P1068','排序定位分数线并扩展同分者','按计划人数的一点五倍向下取整确定名次，以该名次分数为线，输出全部达到分数线的人。',
    '按分数降序、报名号升序排列。分数线取下标 m×3/2−1 的分数，再继续统计所有不低于它的选手。',
    r'''计划三人时，定位第四名的分数，不是只取四个人。若第四、五名同为八十八分，两人都必须进入面试，所以实际人数会超过定位名次。

先以具名比较函数实现两级顺序：分数不同，高分在前；相同则报名号小者在前。定位名次 k=3m/2，整数运算直接向下取整，而数组的对应下标是 k−1。取出 cutoff 后，从首项扫描到首次低于它的位置，前面这一整段就是全部符合者。判定包含等号，确保同分者完整输出；它们的报名号顺序已经由比较器保证。''',
    r'''int n,m;cin>>n>>m;vector<Candidate>a(n);for(auto &x:a)cin>>x.id>>x.score;
sort(a.begin(),a.end(),before);int cutoff=a[m*3/2-1].score,count=0;
while(count<n&&a[count].score>=cutoff)++count;
cout<<cutoff<<' '<<count<<'\n';for(int i=0;i<count;++i)cout<<a[i].id<<' '<<a[i].score<<'\n';''',
    '定位名次不等于最终人数；同分者全部进入，排序比较不能使用大于等于。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序'],lessons=SORT+['structures','functions'],
    declarations=r'''struct Candidate{int id,score;};
bool before(const Candidate&a,const Candidate&b){if(a.score!=b.score)return a.score>b.score;return a.id<b.id;}''')

add('P1093','三关键字排序','按总分降序、语文降序、学号升序评选奖学金，输出前五名的学号与总分。',
    '读入时保存输入编号和语文分，并算三科总分。比较器严格按三层条件决定顺序，排序后输出前五项。',
    '总分相同时不能立即按学号排序，还要先比较语文。例如两个学生同为二百七十九分，语文高者应在前，即使学号更大。结构体把总分、语文分和学号作为同一条记录保存；比较器在第一项不同的时候就返回结果，只有相等才看下一项。学号按输入次序从一编号，最后一层规则让不同学生的先后唯一。',
    r'''int n;cin>>n;vector<Scholar>a(n);
for(int i=0;i<n;++i){int math,english;cin>>a[i].chinese>>math>>english;a[i].id=i+1;a[i].total=a[i].chinese+math+english;}
sort(a.begin(),a.end(),before);for(int i=0;i<5;++i)cout<<a[i].id<<' '<<a[i].total<<'\n';''',
    '第二关键字只有语文，不是数学；输出的是学号和总分。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序'],lessons=SORT+['structures','functions'],
    declarations=r'''struct Scholar{int id,chinese,total;};
bool before(const Scholar&a,const Scholar&b){if(a.total!=b.total)return a.total>b.total;if(a.chinese!=b.chinese)return a.chinese>b.chinese;return a.id<b.id;}''')

add('P1104','生日升序并反向处理输入并列','按年龄从大到小输出姓名；出生日期完全相同时，输入较晚者先输出。',
    '出生越早年龄越大，所以年份、月份、日期依次升序；全部相同再按输入编号降序。',
    '先比较年份，一九九一年出生者早于一九九二年，年龄更大；年份相同再比较月份、日期。三个日期字段完全一样时，题目特意要求输入靠后的先输出，普通稳定排序会保留原顺序，恰好不符合要求。因此保存输入编号作为第四关键字，使用降序。比较器对完全相同记录返回 false，保持合法的严格顺序。',
    r'''int n;cin>>n;vector<Person>a(n);for(int i=0;i<n;++i){cin>>a[i].name>>a[i].year>>a[i].month>>a[i].day;a[i].id=i;}
sort(a.begin(),a.end(),older);for(const auto &p:a)cout<<p.name<<'\n';''',
    '日期越小年龄越大；同生日需要输入编号降序。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序'],lessons=SORT+['structures','functions','strings'],
    declarations=r'''struct Person{string name;int year,month,day,id;};
bool older(const Person&a,const Person&b){if(a.year!=b.year)return a.year<b.year;if(a.month!=b.month)return a.month<b.month;if(a.day!=b.day)return a.day<b.day;return a.id>b.id;}''')

add('P1116','统计原排列的逆序对','一次只能交换相邻两节车厢，求使车厢编号升序的最少交换次数。',
    '每对位置 i<j 而编号 a[i]>a[j] 称为逆序对。一次相邻交换最多消除一个逆序对，且不断交换相邻逆序项可以恰好消除全部，所以答案等于原逆序对数。',
    r'''[3,1,2] 有两对逆序：(3,1)、(3,2)。把三依次向右交换两次，得到 [1,2,3]，正好两步。

相邻交换只改变被交换的两个元素之间的相对次序。其它元素要么在它们两者前面，要么在两者后面，因此与这两个元素形成的逆序总数不变；若交换一对相邻逆序，逆序数恰好减少一。最终升序数组逆序数为零，故原有多少逆序，至少需要多少步。

若数组还没升序，就一定存在相邻逆序，否则所有相邻项递增会推出全数组递增。不断选择这样的相邻对交换，每次减少一，最终恰好用原逆序数步完成。因此下界可达。n≤1000，直接枚举全部 i<j 统计即可，不需要真的模拟交换。''',
    r'''int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;long long answer=0;
for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)answer+=a[i]>a[j];
cout<<answer<<'\n';''',
    '只能相邻交换，不能按任意两项交换的置换环公式计数；比较严格大于。',
    '时间 $O(n^2)$、空间 $O(n)$。',tags=['枚举'],lessons=ARRAY+['integer'])

add('P1177','标准库比较排序','把 n 个整数从小到大输出，重复数字全部保留。',
    '存入 vector，调用 sort 处理完整的左闭右开范围，再按数组顺序输出。',
    '样例 [4,2,4,5,1] 排序后为 [1,2,4,4,5]。两个四都来自输入，应全部保留；这题不需要去重。`sort(a.begin(),a.end())` 默认使用整数的小于关系，得到非降序排列；它移动已有元素，不增加、不删除，所以排序前后的多重集合一致。标准库保证比较次数为 n log n 量级，适合十万规模；不应把 sort 固定称为某一种内部快速排序实现。',
    r'''int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');''',
    '题目不要求去重；尾后 end 不属于排序元素。',
    r'时间 $O(n\log n)$；保存输入需 $O(n)$ 空间，库排序另有自身工作空间。',tags=['排序'],lessons=SORT)

add('P1177','自写归并排序','把 n 个整数从小到大输出，重复数字全部保留。',
    '递归排序左右两半，再不断比较两半尚未取出的最小项，写到临时数组，最后复制回当前区间。',
    r'''[4,2,4,5,1] 先分成 [4,2] 和 [4,5,1]，各自排序为 [2,4]、[1,4,5]。合并时比较两边首个未取项，依次取一、二、四、四、五。

函数处理左闭右开区间 [l,r)。长度为零或一时本来有序，直接返回；否则按中点分成两段。左右递归结束后，两段都已排好。i、j 分别指向左右尚未使用的首项，它们就是各自剩余项中的最小值；比较后取较小者，因此写入临时数组的新项也是全部剩余项的最小值。某一边用尽后，只取另一边即可。

每次恰好取走一个原元素，重复数字不会丢失；合并完成后复制临时结果回原数组当前范围，得到这一层的有序结果。每层合并总量 O(n)，区间每次约减半，共 O(log n) 层，因而总时间 O(n log n)。临时数组在主函数一次创建，递归共用，避免每层再分配完整数组。''',
    r'''int n;cin>>n;vector<int>a(n),temp(n);for(int &x:a)cin>>x;merge_sort(a,temp,0,n);
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');''',
    '右端点 r 不包含；只能在两次递归完成后合并，复制回去时不覆盖其它区间。',
    r'时间 $O(n\log n)$，临时数组 $O(n)$、递归栈 $O(\log n)$。',tags=['排序'],lessons=ARRAY+['functions','recursion'],key='merge-sort',
    declarations=r'''void merge_sort(vector<int>&a,vector<int>&temp,int l,int r){
    if(r-l<=1)return;
    int mid=l+(r-l)/2;
    merge_sort(a,temp,l,mid);merge_sort(a,temp,mid,r);
    int i=l,j=mid;
    // 每次取两段剩余元素中最小的一项。
    for(int k=l;k<r;++k){
        if(j==r||(i<mid&&a[i]<=a[j]))temp[k]=a[i++];
        else temp[k]=a[j++];
    }
    for(int k=l;k<r;++k)a[k]=temp[k];
}''')

add('P1271','按候选人编号计数排序','选票编号范围为一到 n，按编号升序输出全部 m 张选票，保留重复票。',
    '统计每个编号出现次数，然后从一到 n 依次输出该编号相应次数。',
    '若编号二有七张票，排序后也必须输出七个二，不能像随机数去重那样只记真假。count[x] 保存编号 x 的票数，读取一张就加一；输出时按编号升序，将该编号输出 count[x] 次。所有票都只属于一个编号，按次数展开恰好输出 m 张，既没有遗漏也没有重复增加。候选人数最多九百九十九，值域远小于两百万张选票，非常适合计数排序。',
    r'''int n,m;cin>>n>>m;vector<int>count(n+1);
for(int i=0;i<m;++i){int x;cin>>x;++count[x];}
bool first=true;for(int x=1;x<=n;++x)for(int k=0;k<count[x];++k){if(!first)cout<<' ';cout<<x;first=false;}cout<<'\n';''',
    '需要次数而非是否出现；循环输出的总量是 m，不是 n。',
    '时间 $O(n+m)$、空间 $O(n)$。',tags=['排序'],lessons=ARRAY)

add('P1781','按位数与字典序比较大整数','每名候选人的票数最多一百位，输出票数最多者的编号与票数，保证无并列。',
    '把票数存成字符串。通常十进制表示下，位数更多的数更大；位数相同时按字典序比较。维护当前最大值即可。',
    '一百万有七位，一律大于六位的九十九万九千九百九十九；不能只按字典序，因为字符九会排在一之后。同位数时，从左边第一个不同数字即可决定大小，这又恰好等价于字符串字典序。先去掉无意义的前导零，让零统一表示为单个零，再比较长度与字典序，就等价于大整数比较。逐个和当前最优比较，不需要把全部候选人排序，票数本身也无需转成有限范围的整数类型。',
    r'''int n;cin>>n;string best;int winner=0;
for(int i=1;i<=n;++i){string votes;cin>>votes;
    size_t p=votes.find_first_not_of('0');votes=p==string::npos?"0":votes.substr(p);
    if(votes.size()>best.size()||(votes.size()==best.size()&&votes>best)){best=votes;winner=i;}
}
cout<<winner<<'\n'<<best<<'\n';''',
    '不能转成 long long 保存一百位票数；先比较位数再比较同位字符串。',
    '最大位数为 L，时间 $O(nL)$、额外空间 $O(L)$。',tags=['高精度'],lessons=['io-basics','strings','string-tools','basic-control'])

add('P1923','随机枢轴三路快速选择','求从零开始编号的第 k 小元素，重复值按出现次数计算。',
    '随机选枢轴，把当前范围原地分成小于、等于、大于三部分。k 在中段就得到答案，否则只保留包含 k 的那一侧继续划分。',
    r'''[4,3,2,1,5] 求 k=1，按枢轴三可分成 [1,2]、[3]、[5,4]。两侧此时不要求内部有序；排序后下标一在左段，只需在一、二中继续选择，不必再排列三、四、五。

维护当前绝对下标范围 [l,r]，第 k 小元素一定在其中。随机选 pivot，使用 lt、i、gt 三个边界：小于段为 [l,lt)，等于段为 [lt,i)，未知段为 [i,gt]，大于段为 (gt,r]。若 a[i] 小于枢轴，与 lt 位置交换并推进 lt、i；相等只推进 i；大于时与 gt 交换并缩小 gt，此时换来的元素还未知，不能同时推进 i。

未知段清空后，中间等于段的绝对下标范围是 [lt,gt]。k 落在这段就返回 pivot；在左边就令 r=lt−1，在右边令 l=gt+1。k 始终按原来的零基名次保留，不要再减一。三路划分能一次处理所有重复枢轴值，避免全相等输入反复缩一格。

随机枢轴使保留范围在期望意义下快速缩小，期望时间线性；随机算法仍有平方的最坏情况，不能把期望保证写成确定性最坏保证。''',
    r'''int n,k;cin>>n>>k;vector<int>a(n);for(int &x:a)cin>>x;
mt19937 rng(20261030);int l=0,r=n-1;
while(true){
    int pivot=a[uniform_int_distribution<int>(l,r)(rng)],lt=l,i=l,gt=r;
    while(i<=gt){
        if(a[i]<pivot)swap(a[lt++],a[i++]);
        else if(a[i]>pivot)swap(a[i],a[gt--]);
        else ++i;
    }
    if(k<lt)r=lt-1;else if(k>gt)l=gt+1;else {cout<<pivot<<'\n';break;}
}''',
    '最小元素是第零小；与右端交换后不能跳过新换来的未知元素。',
    '期望时间 $O(n)$、最坏 $O(n^2)$，数组空间 $O(n)$，划分额外空间 $O(1)$。',tags=['排序'],lessons=ARRAY+['iterators','random-selection'],key='quickselect')

add('P2676','优先选择最高奶牛','选尽量少的奶牛，使身高总和达到书架高度 B，保证存在解。',
    '按身高从高到低排序，依次累加，第一次达到 B 时输出已选数量。',
    '固定只选 k 头时，最高的 k 头能得到不小于其它任何 k 头的总高度：若某个方案用了矮牛而没用更高的牛，替换后数量不变且总高不降低。不断替换，就得到最高 k 头的方案。因此若最高 k 头仍不够，任何 k 头都不够；按降序累加第一次够到的 k 就是最小数量。题目要最少头数，不要求让总高度恰好等于 B 或超出最少。',
    r'''int n;long long b;cin>>n>>b;vector<int>h(n);for(int &x:h)cin>>x;sort(h.begin(),h.end(),greater<int>());
long long sum=0;for(int i=0;i<n;++i){sum+=h[i];if(sum>=b){cout<<i+1<<'\n';break;}}''',
    '高度达到目标也算成功，使用大于等于；不需要求最小超额高度。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['贪心','排序'],lessons=SORT+['greedy'])

add('P5143','按高度排序后连接相邻点','必须经过每个三维点，且经过顺序中的高度严格递增，求总路程，保留三位小数。',
    '高度各不相同，访问顺序已唯一确定为按 z 升序。排序后把相邻点间的三维欧几里得距离累加。',
    r'''样例五个点为 (1,1,1) 到 (5,5,5)，每次坐标都各增加一，相邻距离为 $\sqrt3$，共四段，总长 $4\sqrt3$，输出 6.928。

题目要求每个点都经过且高度严格递增，因此任意两个点之间，较低者一定先访问。这已经确定唯一的完整顺序，不需要搜索路径或求最短路。排序后对每一对相邻点计算 dx、dy、dz，距离为 $\sqrt{dx^2+dy^2+dz^2}$，所有路段相加就是总长。

代码用 long double 保留中间精度，调用三参数 hypot 计算三维长度，避免直接平方可能产生的大中间值。它得到的仍是同一个欧几里得距离。n=1 时没有路段，答案为零。''',
    r'''int n;cin>>n;vector<Point>a(n);for(auto &p:a)cin>>p.x>>p.y>>p.z;sort(a.begin(),a.end(),lower_point);
long double answer=0;for(int i=1;i<n;++i)answer+=hypot(a[i].x-a[i-1].x,a[i].y-a[i-1].y,a[i].z-a[i-1].z);
cout<<fixed<<setprecision(3)<<answer<<'\n';''',
    '排序依据只有高度 z；距离计算使用全部三维差，最后统一格式化。',
    r'时间 $O(n\log n)$、空间 $O(n)$。',tags=['排序','计算几何'],lessons=SORT+['structures','functions','geometry'],exact=True,
    declarations=r'''struct Point{long double x,y,z;};
bool lower_point(const Point&a,const Point&b){return a.z<b.z;}''')
