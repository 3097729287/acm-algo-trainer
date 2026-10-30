"""Two original interactive protocols, verified with actual pipe interactors."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions','interactive-io']

add('P7579','两轻球二分定位，分开后分别三分',
    '天平最多使用指定次数，从五到五百个球中找两个同样较轻的球。程序只读球数，再逐次称量、读取比较结果，最终升序输出两个编号。',
    r'''维护包含两个轻球的候选组。把它分成两组，必要时用已知正常球补齐较小一侧，称相同个数：不平衡则两个轻球都在较轻组，平衡则每组各一个。分开后，每组的一个轻球可用三分查找：称前两份等长组，较轻组或未称的第三组包含它。首次球数为奇数而没有正常球时，先留下一个球，异重时把它也保留到较轻组中。最坏十三问；二次幂规模不超过二百五十六时最多十一问，满足该子任务十二问限制。''',
    r'''**相同球数的称量，比较的是两边轻球的数量。** 正常球重 W、轻球重 w<W，两边各放 p 个，总质量分别为 pW−轻球数*(W−w)，所以轻球多的一盘更轻。我们的每次询问都保证球数相等，避免混入球数不同的影响。

先维护“两个轻球都在候选组中”。偶数候选平均分为 A、B：若左轻，两轻都在 A，B 中任意球都是正常球；右轻反之；平衡时，两轻不能全在某侧，只能每组各一个。此时把问题拆成两个“已知恰有一个轻球”的搜索。

候选组为奇数时，小侧可用一个候选组外的已知正常球补齐，这个正常球只参与称量，不加入候选。首次 n 为奇数，还没有正常球可用：两边各放 floor(n/2) 个，剩一个 z 不称。平衡说明每边一个轻球、z 正常；异重说明轻球只能在较轻一边加 z 中，重边全部正常。这样第一次之后就有了正常球，后续奇数候选都能补齐。候选只剩两个时直接提交它们。

例如五球中一、五偏轻。先称 {1,2} 对 {3,4}，左轻，保留 {1,2,5}，三是正常球。再称 {1,3} 对 {2,5}，平衡；真实候选左组 {1}、右组 {2,5} 各有一个轻球。左组已定位，右组称二对五，右轻，得到五。

**一轻球搜索为什么能三分？** 大小 s 的组分成前 q=ceil(s/3) 个、接着 q 个、其余个，称前两组。轻球在前组则左轻，在第二组则右轻，平衡则在未称组。三个子组大小都不超过 ceil(s/3)，故最多 ceil(log_3 s) 问。s=2 时两边各一个，合法数据不可能平衡。

**核对最紧的问数限制。** 若分开前经历 t 次异重，候选数至多 ceil(n/2^t)。接下来平衡的一问将其拆成各至多 ceil(n/2^(t+1)) 个，故总问数不超过

$$t+1+2\left\lceil\log_3\left\lceil\frac{n}{2^{t+1}}\right\rceil\right\rceil.$$

对 n≤500，取可能的 t 逐个核对，上式最大十三；若一直异重直到两球直接结束，只需至多九问。唯一十二问子任务的 n 是不超过二百五十六的二次幂，此时上式最大十一。不要读入 k，它是测试点属性，输入中没有它。

询问格式是 `1 p ... q ...`，最终格式为 `2 x y` 且 x<y。每次用 endl 刷新，再读取字符；提交最终答案后立即结束。官方样例是一次对话，别把样例的三个回复当作适用于任意询问顺序的固定输入。''',
    r'''int n;if(!(cin>>n))return 0;
vector<int>candidate(n);iota(candidate.begin(),candidate.end(),1);int normal=0;
while(candidate.size()>2){
    int half=(int)candidate.size()/2;
    vector<int>left(candidate.begin(),candidate.begin()+half);
    vector<int>right(candidate.begin()+half,candidate.end());
    if(candidate.size()%2&&normal==0){
        // 首次奇数规模：留下一个球，异重时它仍可能是轻球。
        int outside=right.back();right.pop_back();char reply=weigh(left,right);
        if(reply=='='){answer(find_one(left),find_one(right));return 0;}
        if(reply=='<'){normal=right[0];candidate=left;}
        else{normal=left[0];candidate=right;}
        candidate.push_back(outside);
    }else{
        vector<int>pan=left;
        if(pan.size()<right.size())pan.push_back(normal); // 只给称盘补正常球
        char reply=weigh(pan,right);
        if(reply=='='){answer(find_one(left),find_one(right));return 0;}
        if(reply=='<'){normal=right[0];candidate=left;}
        else{normal=left[0];candidate=right;}
    }
}
answer(candidate[0],candidate[1]);''',
    '两盘编号必须互不重复；补入的正常球不属于候选；不读取 k；每问刷新，最终答案升序并立即退出。',
    r'询问次数至多十三，二次幂子任务至多十一；本地计算及发送编号总量均为 $O(n)$，空间 $O(n)$。',
    tags=['交互题','二分查找','分治'],lessons=A+['iterators','binary-answer'],checker='weighing_transcript',interactive='weighing',
    declarations=r'''char weigh(const vector<int>&left,const vector<int>&right){
    cout<<"1 "<<left.size();for(int x:left)cout<<' '<<x;
    cout<<' '<<right.size();for(int x:right)cout<<' '<<x;cout<<endl;
    char reply;if(!(cin>>reply)||(reply!='<'&&reply!='>'&&reply!='='))exit(0);
    return reply;
}
int find_one(vector<int>group){
    while(group.size()>1){
        int q=((int)group.size()+2)/3;
        vector<int>left(group.begin(),group.begin()+q),right(group.begin()+q,group.begin()+2*q);
        char reply=weigh(left,right);
        if(reply=='<')group=left;
        else if(reply=='>')group=right;
        else group=vector<int>(group.begin()+2*q,group.end());
    }
    return group[0];
}
void answer(int x,int y){if(x>y)swap(x,y);cout<<"2 "<<x<<' '<<y<<endl;}''')

add('CF2037E','先确认能否唯一确定，再用前缀增量还原',
    '交互器隐藏二进制串，询问一个区间可得其中零在前、一在后的下标对数量。每组至多询问 n 次，确定完整串，若任何询问策略都不能唯一确定则报告 IMPOSSIBLE。',
    r'''先问整个串的 01 对数，零则所有区间都是零，形如若干一接若干零的多个串无法区分。非零时依次问前缀，首个正值 g 出现在长度 i：该前缀必为 i−g−1 个一、g 个零、末尾一个一。之后前缀计数不变表示新增零，增加量等于此前零数表示新增一。最后一个前缀直接复用整串回答，共至多 n−1 问。''',
    r'''这里统计的是下标对，不要求相邻。例如 01001 的第一个零可与后面两个一配对，另两个零各与末尾一配对，整串共有四对 01。不要把它理解成连续子串的出现次数。

先问 f(1,n)。若为零，串中不存在一个零在某个一前面，只能是若干一接若干零，包括全零、全一。它们的任意区间也都没有 01 对，因此不管换什么区间询问，回复永远是零。n≥2 时存在多个这样的串，确实不能唯一确定，应输出 IMPOSSIBLE。反之整串有 01 时，以下构造会还原所有位置，不能再报告不可能。

依次询问长度 i=2,3,... 的前缀，最后长度 n 直接复用第一问。设首个正值为 g。此前长度 i−1 的前缀没有 01，形状只能是一段一接一段零；新字符必须是一，它与此前全部零产生 g 对，因此此前零数恰为 g。整个前缀就是

$$\underbrace{11\cdots1}_{i-g-1}\underbrace{00\cdots0}_{g}1.$$

从这一步开始，已知前缀至少有一个零。之后若加入零，不产生新的 01 对，计数增量为零；若加入一，就与此前每个零分别配对，增量等于已知零数，大于零。两种回复可以区分，同时新增零时增加 zero_count，新增一时零数不变。

例串 01001：长度二的回复一，确定前缀 01；长度三仍一，加入零；长度四仍一，再加入零；长度五的整串回复四，增量三等于此前三个零，加入一。最终得到完整秘密串。

先询问整串使用一问；中间前缀二到 n−1 至多 n−2 问，总计 n−1，不超过 n。n=2 时只需整串一问，若正则只能是 01。前缀扫描的每轮只更新一个字符与常数个计数，总时间线性。

参考程序按原交互协议读取测试组数、长度和每次询问的回复。题面 Hacks 部分列出的隐藏串供出题端构造测试，不是此交互程序可以直接读到的内容。每问与每组最终回答都刷新；遇 EOF 或负回复立刻结束。''',
    r'''int tests;if(!(cin>>tests))return 0;
while(tests--){
    int n;cin>>n;long long total=ask(n);
    if(total==0){cout<<"! IMPOSSIBLE"<<endl;continue;}
    string result;long long previous=0,zero_count=0;
    for(int i=2;i<=n;++i){
        long long current=(i==n?total:ask(i));
        if(result.empty()){
            if(current>0){
                // 首次有 01：此前必是若干一、current 个零。
                result=string(i-current-1,'1')+string(current,'0')+'1';
                zero_count=current;
            }
        }else if(current==previous){result+='0';++zero_count;}
        else if(current-previous==zero_count)result+='1';
        else return 0; // 回复不符合协议时结束
        previous=current;
    }
    cout<<"! "<<result<<endl;
}''',
    '统计不相邻也算的下标对；只有完全不含 01 的串才无法唯一确定；最后前缀复用第一问，别多问。',
    '每组至多 n−1 问，时间、空间均为 $O(n)$。',tags=['交互题','前缀和','构造'],lessons=A+['strings','string-tools','prefix'],
    checker='kachina_transcript',interactive='kachina',
    declarations=r'''long long ask(int right){
    cout<<"? 1 "<<right<<endl;
    long long reply;if(!(cin>>reply)||reply<0)exit(0);
    return reply;
}''')
