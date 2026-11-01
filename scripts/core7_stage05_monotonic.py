"""Complete programs for the heap and monotone-structure unit."""
CODE={};DECL={}
CODE['P1628']=r'''
int n;cin>>n;vector<string>words(n);for(auto &s:words) cin>>s;string prefix;cin>>prefix;
vector<string>selected;for(const string &s:words) if(s.size()>=prefix.size()&&s.compare(0,prefix.size(),prefix)==0) selected.push_back(s);
sort(selected.begin(),selected.end());for(const string &s:selected) cout<<s<<'\n';
'''
CODE['UVA11462']=r'''
int n;while(cin>>n&&n){array<int,100>count={};for(int i=0,age;i<n;++i){cin>>age;++count[age];}bool first=true;for(int age=1;age<100;++age) for(int c=0;c<count[age];++c){if(!first) cout<<' ';first=false;cout<<age;}cout<<'\n';}
'''
CODE['B3666']=r'''
int n;cin>>n;vector<pair<unsigned long long,int>>stack;stack.reserve(n);int answer=0;
for(int i=1;i<=n;++i){unsigned long long x;cin>>x;while(!stack.empty()&&stack.back().first<=x){answer^=stack.back().second;stack.pop_back();}stack.push_back({x,i});answer^=i;cout<<answer<<'\n';}
'''
CODE['P1440']=r'''
int n,m;cin>>n>>m;deque<pair<int,int>>queue;
for(int i=1;i<=n;++i){int x;cin>>x;while(!queue.empty()&&queue.front().second<i-m) queue.pop_front();cout<<(queue.empty()?0:queue.front().first)<<'\n';while(!queue.empty()&&queue.back().first>=x) queue.pop_back();queue.push_back({x,i});}
'''
CODE['P1886']=r'''
int n,k;cin>>n>>k;vector<int>a(n);for(int &x:a) cin>>x;
for(int maximum=0;maximum<2;++maximum){deque<int>queue;bool first=true;
    for(int i=0;i<n;++i){while(!queue.empty()&&queue.front()<i-k+1) queue.pop_front();while(!queue.empty()&&(maximum?a[queue.back()]<=a[i]:a[queue.back()]>=a[i])) queue.pop_back();queue.push_back(i);if(i>=k-1){if(!first) cout<<' ';first=false;cout<<a[queue.front()];}}
    cout<<'\n';
}
'''
CODE['P2251']=r'''
int n,m;cin>>n>>m;deque<pair<long long,int>>queue;
for(int i=0;i<n;++i){long long x;cin>>x;while(!queue.empty()&&queue.front().second<i-m+1) queue.pop_front();while(!queue.empty()&&queue.back().first>=x) queue.pop_back();queue.push_back({x,i});if(i>=m-1) cout<<queue.front().first<<'\n';}
'''
CODE['P2947']=r'''
int n;cin>>n;vector<int>height(n),stack,answer(n);for(int &x:height) cin>>x;
for(int i=n-1;i>=0;--i){while(!stack.empty()&&height[stack.back()]<=height[i]) stack.pop_back();if(!stack.empty()) answer[i]=stack.back()+1;stack.push_back(i);}
for(int x:answer) cout<<x<<'\n';
'''
CODE['P5788']=r'''
int n;cin>>n;vector<int>values(n),stack,answer(n);for(int &x:values) cin>>x;
for(int i=0;i<n;++i){while(!stack.empty()&&values[stack.back()]<values[i]){answer[stack.back()]=i+1;stack.pop_back();}stack.push_back(i);}
for(int i=0;i<n;++i) cout<<(i?" ":"")<<answer[i];cout<<'\n';
'''
CODE['P15232']=r'''
int n,m;cin>>n>>m;vector<long long>cost(n),capacity(m);for(auto &x:cost) cin>>x;for(auto &x:capacity) cin>>x;
sort(cost.begin(),cost.end());sort(capacity.begin(),capacity.end(),greater<long long>());
long long answer=0;int first=0,lane=0;
while(first<m){if(lane==n){cout<<-1<<'\n';return 0;}int group=0;while(first+group<m&&group+1<=capacity[first+group]) ++group;answer+=group*cost[lane];first+=group;++lane;}
cout<<answer<<'\n';
'''
CODE['UVA1619']=r'''
int n;bool first=true;
while(cin>>n){vector<long long>a(n),prefix(n+1);for(int i=0;i<n;++i){cin>>a[i];prefix[i+1]=prefix[i]+a[i];}
    vector<int>left(n),right(n),stack;
    for(int i=0;i<n;++i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();left[i]=stack.empty()?0:stack.back()+1;stack.push_back(i);}
    stack.clear();for(int i=n-1;i>=0;--i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();right[i]=stack.empty()?n-1:stack.back()-1;stack.push_back(i);}
    long long best=0;int bestLeft=0,bestRight=0;
    for(int i=0;i<n;++i){int l=left[i],r=right[i];long long value=a[i]*(prefix[r+1]-prefix[l]);if(value>best||(value==best&&make_pair(r-l,l)<make_pair(bestRight-bestLeft,bestLeft))){best=value;bestLeft=l;bestRight=r;}}
    if(!first) cout<<'\n';first=false;cout<<best<<'\n'<<bestLeft+1<<' '<<bestRight+1<<'\n';
}
'''
CODE['P1950']=r'''
int n,m;cin>>n>>m;vector<int>height(m);long long answer=0;
for(int row=0;row<n;++row){string line;cin>>line;vector<pair<int,int>>stack;long long suffixSum=0;
    for(int j=0;j<m;++j){height[j]=line[j]=='.'?height[j]+1:0;int width=1;while(!stack.empty()&&stack.back().first>=height[j]){suffixSum-=1LL*stack.back().first*stack.back().second;width+=stack.back().second;stack.pop_back();}stack.push_back({height[j],width});suffixSum+=1LL*height[j]*width;answer+=suffixSum;}
}
cout<<answer<<'\n';
'''
CODE['P2564']=r'''
int n,k;cin>>n>>k;vector<pair<long long,int>>beads;beads.reserve(n);
for(int color=0;color<k;++color){int count;cin>>count;while(count--){long long position;cin>>position;beads.push_back({position,color});}}
sort(beads.begin(),beads.end());vector<int>count(k);int covered=0,left=0;long long answer=LLONG_MAX;
for(int right=0;right<n;++right){if(count[beads[right].second]++==0) ++covered;while(covered==k){answer=min(answer,beads[right].first-beads[left].first);if(--count[beads[left].second]==0) --covered;++left;}}
cout<<answer<<'\n';
'''
CODE['P6503']=r'''
int n;cin>>n;vector<long long>a(n);for(auto &x:a) cin>>x;long long answer=0;
for(int maximum=0;maximum<2;++maximum){vector<int>stack;long long sum=0;
    for(int i=0;i<=n;++i){while(!stack.empty()&&(i==n||(maximum?a[stack.back()]<=a[i]:a[stack.back()]>=a[i]))){int j=stack.back();stack.pop_back();int left=stack.empty()?-1:stack.back();sum+=a[j]*(j-left)*(i-j);}if(i<n) stack.push_back(i);}
    if(maximum) answer+=sum;else answer-=sum;
}
cout<<answer<<'\n';
'''
DECL['P7410']=r'''
long long allAtLeast(const vector<vector<int>>&g,int threshold){
    int n=g.size();vector<int>height(n);long long answer=0;
    for(int row=0;row<n;++row){vector<pair<int,int>>stack;long long sum=0;
        for(int j=0;j<n;++j){height[j]=g[row][j]>=threshold?height[j]+1:0;int width=1;while(!stack.empty()&&stack.back().first>=height[j]){sum-=1LL*stack.back().first*stack.back().second;width+=stack.back().second;stack.pop_back();}stack.push_back({height[j],width});sum+=1LL*height[j]*width;answer+=sum;}
    }
    return answer;
}
'''
CODE['P7410']=r'''
int n;cin>>n;vector<vector<int>>g(n,vector<int>(n));for(auto &row:g) for(int &x:row) cin>>x;cout<<allAtLeast(g,100)-allAtLeast(g,101)<<'\n';
'''
CODE['P9977']=r'''
int n;long long m,k;cin>>n>>m>>k;vector<pair<long long,long long>>cows(n);for(auto &[w,a]:cows) cin>>w>>a;
sort(cows.begin(),cows.end(),greater<pair<long long,long long>>());deque<pair<long long,long long>>towers;towers.push_back({LLONG_MAX/4,m});long long answer=0;
for(auto [w,count]:cows){long long remaining=count;while(remaining&&!towers.empty()&&towers.front().first>=w+k){long long used=min(remaining,towers.front().second);remaining-=used;towers.front().second-=used;if(towers.front().second==0) towers.pop_front();}long long used=count-remaining;if(used){towers.push_back({w,used});answer+=used;}}
cout<<answer<<'\n';
'''
CODE['P10277']=r'''
int n,k;cin>>n>>k;vector<long long>duration(n),start(n),finish(n),times={0};for(auto &x:duration) cin>>x;
priority_queue<long long,vector<long long>,greater<long long>>ready;
for(int i=0;i<k;++i){finish[i]=duration[i];ready.push(finish[i]);}
for(int i=k;i<n;++i){start[i]=ready.top();ready.pop();finish[i]=start[i]+duration[i];ready.push(finish[i]);}
long long when=ready.top();for(int i=0;i<n;++i){times.push_back(start[i]);times.push_back(finish[i]);}sort(times.begin(),times.end());times.erase(unique(times.begin(),times.end()),times.end());
auto index=[&](long long time){return int(lower_bound(times.begin(),times.end(),time)-times.begin());};
vector<vector<int>>previous(times.size());for(int i=0;i<n;++i) previous[index(finish[i])].push_back(index(start[i]));
vector<char>visited(times.size());vector<int>stack={index(when)};visited[stack.back()]=true;
while(!stack.empty()){int x=stack.back();stack.pop_back();for(int p:previous[x]) if(!visited[p]){visited[p]=true;stack.push_back(p);}}
cout<<when<<'\n';for(int i=0;i<k;++i) cout<<char('0'+visited[index(duration[i])]);cout<<'\n';
'''
CODE['CF547B']=r'''
int n;cin>>n;vector<int>a(n),left(n),right(n),stack,answer(n+1);for(int &x:a) cin>>x;
for(int i=0;i<n;++i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();left[i]=stack.empty()?-1:stack.back();stack.push_back(i);}
stack.clear();for(int i=n-1;i>=0;--i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();right[i]=stack.empty()?n:stack.back();stack.push_back(i);}
for(int i=0;i<n;++i){int length=right[i]-left[i]-1;answer[length]=max(answer[length],a[i]);}
for(int length=n-1;length>=1;--length) answer[length]=max(answer[length],answer[length+1]);
for(int length=1;length<=n;++length) cout<<(length==1?"":" ")<<answer[length];cout<<'\n';
'''
CODE['CF1237D']=r'''
int n;cin>>n;vector<long long>a(3*n);for(int i=0;i<n;++i){cin>>a[i];a[i+n]=a[i+2*n]=a[i];}
long long low=*min_element(a.begin(),a.begin()+n),high=*max_element(a.begin(),a.begin()+n);
if(2*low>=high){for(int i=0;i<n;++i) cout<<(i?" ":"")<<-1;cout<<'\n';return 0;}
deque<int>queue;int right=0;
for(int left=0;left<n;++left){
    while(right<3*n&&(queue.empty()||2*a[right]>=a[queue.front()])){while(!queue.empty()&&a[queue.back()]<=a[right]) queue.pop_back();queue.push_back(right);++right;}
    cout<<(left?" ":"")<<right-left;if(!queue.empty()&&queue.front()==left) queue.pop_front();
}
cout<<'\n';
'''


from core7_authoring import add
A=['io-basics','basic-control','vector','integer','functions']
S=A+['monotone-structures']

def emit(pid,title,meaning,brief,detail,pitfalls,complexity,tags,lessons,exact=False):
    add(pid,title,meaning,brief,detail,CODE[pid],pitfalls,complexity,tags=tags,lessons=lessons,declarations=DECL.get(pid,''),exact=exact)

emit('P1628','筛出真实前缀匹配，再按字典序排序',
    '按字典序输出所有以给定字符串为前缀的单词，相同单词的多次出现仍分别输出。',
    r'''单词长度至少等于前缀长度，并且从首字符开始的相应一段与前缀相同，才是匹配。保存所有匹配单词，再用字符串排序升序输出，不去重。不是查找任意位置的子串。''',
    r'''“以前缀T开头”要求从单词第一个字符开始匹配。例如T为ab，abc可以，cab不可以；单词a太短，也不可以。

读入全部单词后，最后才能得到T。逐个检查单词长度，短于T就跳过；否则用compare从位置零比较T长的一段，返回零表示完全相同。长度先检查也让“整个前缀都存在”的条件清楚可见。

将匹配词放进selected，随后按字符串自带字典序排序。字符全部为小写字母，标准字符串比较与题意字典序一致；一个词是另一个词的前缀时，较短者排在前面。

原样例的ki出现两次，输出也有两个ki。题目没有要求不同单词集合，因此不能用set去重。筛选与排序都保持每次输入的那一份出现。

匹配词之间怎样排序与不匹配词无关，所以先筛选可以少排一些内容。若没有匹配词，循环自然不输出任何词，也不增加“No”之类题目未要求的提示。每个结果占一行。''',
    '必须从首字符匹配；短单词不能匹配长前缀；保留重复出现；字符串按字典序；无匹配时没有额外提示。',
    r'设单词最大长度为L，时间 $O(NL\log N+|T|)$，空间 $O(NL+|T|)$，含输入。',['排序'],A+['strings','string-tools','sort'],True)

emit('UVA11462','年龄值域只有一至九十九，用次数表排序',
    '多组数据，将一至九十九岁的年龄升序输出；每组最多两百万人，人数零终止。',
    r'''年龄只有九十九种，读一个就给对应计数加一，不保存全部年龄。再从一至九十九依次输出每个年龄相应次数。每组清空次数表，人数零只终止。输入输出规模大，关闭流同步并避免每次输出强制刷新。''',
    r'''[原卷](https://onlinejudge.org/external/114/11462.pdf)保证年龄至少一岁、没有人达到一百岁，每组人数最多两百万。比较排序虽然可行，但有限值域直接提供了更简单的计数方法。

建立一百格数组，count[age]表示该年龄出现多少次。每读入一个年龄就增加对应格，不必建立两百万项的年龄列表。

读完后按年龄从一至九十九遍历，某年龄出现多少次便输出多少次。每个输入年龄都会在它对应的位置输出一次，数量不变；按年龄顺序输出又确保全局升序。这就是计数排序在小值域下的应用。

数组必须在每组开始时归零，否则前一组的人口会混入下一组。人数为零的终止组没有年龄，也不产生一行答案。数据之间没有给测试组数，用循环读取直到终止或文件结束。

输出同一组的年龄之间一个空格，每组结束换行。虽然计数数组只需常数空间，读取和打印所有年龄仍至少需要线性时间，不能把整个程序说成常数时间。原卷特意提醒大输入，程序使用普通快速C++流，不对每个数字使用endl。''',
    '年龄一至九十九；零是人数终止符；每组次数重新归零；保留所有重复年龄；每组一行；不保存两百万个年龄也仍要逐个读写。',
    r'每组时间 $O(n+100)$，额外空间 $O(100)$。',['排序'],A+['standard-array','counting'],True)

emit('B3666','严格递减栈保留后缀纪录，下标用异或增删',
    '不断在末尾加入正整数，每次求当前所有严格大于右侧每项的位置的下标异或和；数值可接近无符号六十四位上限。',
    r'''之前不是后缀最大纪录的位置以后也不会恢复；原纪录遇到新值x时，值不大于x的全部失效。栈按值严格递减保留纪录，从栈顶弹这些位置，同时把其下标再异或一次以删除。新末尾必是纪录，加入栈并异或其下标。数值用unsigned long long，下标异或不混入数值。''',
    r'''一个位置必须严格大于它右边所有数，才是题目所称的后缀最大值下标。相同值中靠左的那个不满足严格关系，因此新值到来时，相等旧值也要删除。

先考虑上一次已经不合格的位置。它右边已有一个不小于它的见证，继续在末尾添加元素不会删除这个见证，所以这个位置永远不会重新合格，无需保存。

上次还合格的位置从左到右，数值一定严格递减。新加入x以后，其中数值不大于x的旧纪录全部失效，且它们在这串纪录的末尾连续出现；用栈反复弹出即可。剩下的纪录既大于原右侧全部值，也大于x，仍然合格。

新末尾右边没有元素，条件自然成立，必须加入。归纳可知，栈里恰好是当前所有严格后缀纪录，不多不少。

每次不必重新异或整个栈。维护answer，下标加入时异或一次，弹出时再异或一次。一个数与自己异或为零，因而第二次异或正好删去它的贡献；这是对下标做操作，不是对输入数值。

输入数值可以大于有符号long long上限，必须使用unsigned long long。下标至多一百万，异或答案只涉及这些下标，int足够。每项只进栈、出栈一次，总时间线性，不能每步扫描当前全部后缀纪录。''',
    '严格大于右侧全部值；相等旧值要弹；末尾必合格；失效者不会恢复；异或的是一开始的下标；输入使用无符号六十四位。',
    r'总时间 $O(n)$，空间 $O(n)$。',['单调栈','位运算'],S+['unsigned64','bitwise','bindings'],True)

emit('P1440','先查询之前m项，再把当前项加入单调队列',
    '对第i项，输出它前面至多m项的最小值，不含第i项；第一项前面没有数，输出零。',
    r'''最小值候选按值递增、下标递增保存在双端队列。处理位置i，先移走小于i减m的过期下标，再输出队首；此时尚未加入a_i，所以恰好查之前m项。输出后才从队尾删去不小于a_i的旧候选并加入当前项。第一项队列空，输出零。''',
    r'''这题窗口与通常的“以当前位置结束、长度m”不同：当前位置自身不参与。例如首个数即使很小，第一行也必须输出零；样例中第二项之前只有第一项。

处理一开始编号的位置i，合法下标是最大的一与i减m起，到i减一结束。队列先删除下标小于i减m的元素，恰好保留仍在这个范围内的候选。查询必须在当前项入队之前完成。

队首候选值最小。新项随后入队时，凡队尾旧值不小于它，都可删除：新值更小或相等，并且下标更晚，将来过期也更晚。在旧项仍有效的任一未来窗口里，新项都不劣，旧项没有必要再保留。

重复值保留较新的一个即可，输出的最小值不变。过期从队首删、受支配候选从队尾删，这两个原因不同，不能只保留一个单独的“当前最小值”。

程序可以读取当前x后先输出，只要还没把它加入队列即可。第一项前面无数，队列为空输出零；之后m至少一，前一项总能作为某个有效候选或被更好候选代替。

不需要保存全部两百万项，读入一个便完成本轮查询与更新。每个候选只被加入、删除一次，所有输出也是线性数量。''',
    '查询不含当前项；第一行零；先过期并输出后再加入x；左边界i减m仍有效；重复最小值保留较新者；队首过期与队尾支配分别处理。',
    r'总时间 $O(n)$，额外空间 $O(m)$。',['队列'],S+['queue-stack','bindings'],True)

emit('P1886','同一数组分别维护完整窗口的最小与最大候选',
    '给定长度k的滑动窗口，依次输出每个完整窗口的最小值与最大值，各占一行。',
    r'''数组保存下来，分别做最小值与最大值两遍扫描。队列存下标，先从队首移走窗口左侧的过期项，再从队尾删去被当前值支配的候选，加入当前下标。只有已读满k项才输出队首。最小队列弹不小于当前值者，最大队列弹不大于当前值者；直接比较可覆盖最小int输入。''',
    r'''位置i为当前窗口右端，完整窗口是i减k加一至i。与只查“前面k项”的题不同，本题必须先加入a_i，再得到这一窗口答案。

最小值扫描中，队列下标递增、数值严格递增。下标早于窗口左端的候选从队首移走；队尾若值不小于新值，就被更新更晚且不大的新项永久替代。更新后队首就是窗口最小值。

最大值的证明对称，把队尾比较方向反过来即可。代码用一个maximum标记控制两次扫描，避免把输入取负来转换问题；输入允许最小的有符号int，直接取相反数可能超出int表示范围。

前k减一项还没有组成完整窗口，不产生答案。每行恰有n减k加一个值，按窗口左端递增顺序输出。k为一时两行都与原数组相同；k为n时每行只有一个数。

队列必须存下标，不能只存值，否则重复值无法准确判断何时离开窗口。相同值下保留较新的候选，既不改变极值，也使候选更晚到期。

为了先完整输出最小值一行、再输出最大值一行，保存原数组供两遍使用。不需要保存两份结果数组，扫到完整窗口便输出。''',
    '本题包含当前位置；只输出完整窗口；每行n减k加一项；存下标以处理过期；两次比较方向相反；不把最小int取负；重复值保留较新者。',
    r'时间 $O(n)$，空间 $O(n+k)$，含输入数组。',['队列'],S+['queue-stack'],True)

emit('P2251','按完整产品窗口维护递增的最低分候选',
    '输出每段连续M件产品中的最低质量分，每个完整窗口一个结果。',
    r'''队列保存值递增的有效候选及其位置。当前第i件先移走早于i减M加一的位置，再删去队尾不小于当前分数的候选，最后加入当前件。读满M件后输出队首。新分不高且更晚离窗，所以被它替代的旧候选不会再成为必要最小值。''',
    r'''每个Q对应连续M件产品中的最小分，包含该段最后一件。第一次输出要等到第M件，之后每加入一件、左端前进一件，恰有N减M加一个结果。

保存候选的位置与分数，位置随入队顺序递增。先从队首删除当前窗口左端之前的位置，防止一个很低但已过期的质量分继续影响结果。

当前分数为x时，队尾旧分数若不小于x，新产品在以后仍包含旧产品的窗口中也会存在，而且更晚过期。因此那些队尾可永久移走，不需要等它们自然出窗。

剩下的候选值严格递增，队首最低。若分数相等，保留较新的那件足够，因为题目只输出最低分，不要求是哪一件。

数据流可以边读边处理，当前件加入后、且窗口已满时直接输出，不必保存所有产品分数。M为一时每件自身就是答案，M为N时只输出全体最低分。

每个位置入队一次，最多从首端或尾端移除一次，总时间线性。循环偶尔弹出多个元素不会使总复杂度变成平方。''',
    '当前产品属于窗口；读满M件才输出；过期按位置判断；相等分保留较新者；输出的是分数；恰有N减M加一行。',
    r'时间 $O(N)$，额外空间 $O(M)$。',['队列'],S+['queue-stack','bindings'],True)

emit('P2947','从右向左删去不够高的候选，栈顶就是最近更高者',
    '求每头牛右侧第一头严格比它高的牛的编号，不存在输出零。',
    r'''从右向左扫描，栈保存可能被左侧奶牛仰望的位置。遇到当前高度h，栈顶不高于h的牛不能成为当前答案，也不会比当前牛更适合更左侧的牛，全部弹掉。剩下的栈顶严格更高且最近；记录其一开始的编号，再加入当前牛。相同高度不能仰望。''',
    r'''目标必须同时满足在右边、严格更高、距离最近。只记右侧最高的一头会丢掉更近但稍矮的合法答案，因此要保存一串未被支配的候选。

从最右向最左处理。当前高度为h时，若右侧候选牛的高度不超过h，它不能回答当前询问；对更左侧的牛，它也不如当前位置：当前牛至少同高且更近。于是它可以永久弹出。

弹完后，若栈非空，栈顶高度严格大于h。它是剩下候选中位置最近的；之前被删掉的位置都有一个更近且不矮的替代者，所以没有漏掉真正最近的答案。

记录以后才把当前位置入栈，防止奶牛仰望自己。栈空说明右边没有更高者，保留初始化的零。

相同高度也要弹掉，因为题目要求严格更高，且当前相同高度位置更靠左，对以后处理的更左牛更近。样例里连续两个高度一的牛，都仰望右侧高度二的牛，不会互相仰望。

代码内部用零开始的数组下标，输出编号加一。每头牛只有一次入栈和至多一次出栈，整体线性。''',
    '右侧最近而非最高；必须严格更高；相等高度弹出；先查再把自己入栈；没有答案零；数组下标转成一开始编号。',
    r'时间 $O(N)$，空间 $O(N)$。',['单调栈'],S,True)

emit('P5788','从左向右保留待回答位置，遇到更大值就确定答案',
    '输出每项右侧第一个严格更大元素的下标，没有则为零，长度可达三百万。',
    r'''栈存尚未找到答案的位置。新值a_i严格大于栈顶值时，当前i就是那个旧位置遇到的首个右侧更大者，赋答案后弹出，继续解决新的栈顶。相等不能解决，保留等待。每个位置只入出一次，不用对三百万项分别向右扫描。''',
    r'''从左向右读数组，把尚未找到首个右侧更大者的位置留在栈中。它们的值从栈底到栈顶不递增，可能有相等项。

当前新值a_i若严格大于栈顶a_j，j的答案已经确定为i。因为j之后到i之前的元素都扫描过，却没有把j解决，说明其中没有更大的；i又确实更大，所以它恰为第一个。

弹出j后，当前值可能还大于新的栈顶，继续处理，直到栈空或栈顶不小于当前值。最后把i放入等待栈。

这里用严格小于来弹栈，等于时不能赋答案。与从右向左删除被支配候选的写法相比，栈的含义不同：本写法弹出的每个位置是在“得到答案”，不是仅因它不适合作为候选被丢弃。因此不能照搬另一方向的等号。

数组结束还留在栈中的位置，没有遇到任何更大数，答案为初始零。输出的是位置而不是数值，内部i为零开始下标，答案保存i加一。

三百万项需要线性处理。即使某一次新值弹掉许多旧位置，总共也只有n次弹出，摊还时间线性；输入、答案与栈各是线性空间。''',
    '弹出待回答位置时必须严格更大；相等不能解决；记录下标不是数值；未解决为零；每项只赋一次；不用每个位置独立向右扫。',
    r'时间 $O(n)$，空间 $O(n)$。',['单调栈'],S,True)

emit('P15232','便宜车道先放最大合法组，成员选承受人数最多者',
    '每辆车选择一条收费车道，该车道最终总车数不能超过这辆车的b值，求精确最小总费用，不可分配输出负一。',
    r'''车道费用升序、车辆b值降序。最便宜剩余车道取最大的q，使当前剩余中最大的q个b都至少q，把这q辆一起放入。随后继续处理剩余车道和车辆。更大的组应放在更便宜车道；可通过交换把该组换成b最大的车辆，再把其它组的高b车辆移入最便宜组直到q，不增加费用也不破坏其它组。车道用完仍有车则无解。''',
    r'''限制是“每辆车所处车道最终有多少车”，不是每条车道自带固定容量。一组车辆放同一车道，其合法容量由组内最小b限制，组大小必须不超过这个最小值。

先按车道价格从小到大排序。任何固定的合法分组，都可把较大的组放在较便宜车道：交换两整组的位置不改变组内人数与b约束，而大组付低价不会更贵。

因此存在最优方案，最便宜车道承载某个最大组，设大小h。这个组又可换成剩余车辆里b最大的h辆。若目标车辆原来在另一组，用当前组中较小b的车交换过去也合法，因为另一组人数不超过h，而被换出的车原先已能承受h人。

设剩余b从大到小排列，最大可组成的人数为q，即前q辆的b都至少q。显然q不小于h。继续把排名h加一至q的车辆移入最便宜组，它们都能承受q人；原来的其它组只减少人数，约束更宽松。费用也不会增加，因为这些车转去的车道不比原车道贵。

这就证明存在一个最优方案，第一组恰是b最大的q辆。固定它后，对剩余车和剩余价格做同样选择，归纳得到整体最优。

扫描降序b时，逐渐增大group，只要新组大小不超过新加入车辆的b，就还能加入。第一次不满足后，后面的b只会更小，不能通过跳过它凑出更大的合法组。所有车辆总共被扫描一次，排序以后不需要逐车搜索车道。

如果n条车道已经用尽仍有车辆，上述交换论证说明任何可行方案都能改造成相同首组选取，因此不存在另一种分组能凭更少车道完成，输出负一。每车费用至多十亿，十万辆总费可达十的十四次方，用long long输出精确整数。''',
    'b属于车辆而非车道；检查最终组人数；费用按每辆车支付；b降序、价格升序；先确定整组再前进；没有结果取模；总费用用六十四位。',
    r'时间 $O(n\log n+m\log m)$，空间 $O(n+m)$。',['排序','贪心'],A+['sort','greedy'])

emit('UVA1619','固定正的区间最小值，向两边扩到更小值之前',
    '求区间元素和乘最小值的最大值，平局依次取最短区间、最小左端点；多组数据之间空一行。',
    r'''每项用单调栈找左右最近严格更小值，之间是以它为最小值的最大可扩展区间。原数非负；最小值为正时向外加不小于它的数会严格增加区间和，因此只需评价这个完整跨度，区间和由前缀表取得。初始化答案为零和第一项，涵盖全零时的最短平局。按得分、长度、左端点比较。''',
    r'''[原卷](https://onlinejudge.org/external/16/1619.pdf)允许输出任一最大区间，本地中文题面另要求平局先最短、再最靠左；采用这个更严格规则仍满足原卷。所有a非负，是扩展区间论证的前提。

假设一个最优区间的最小值为正数v，选择其中某个值为v的位置。只要旁边元素仍不小于v，纳入它就不改变最小值，还会严格增加元素和，因此得分严格增加。最优区间必然已经扩到两侧第一个严格小于v的元素之前。

所以对每个位置i，只需找到左、右最近严格更小的位置，评价它们之间的整个跨度。用两个方向的单调栈，遇到不小于当前值的候选都弹掉，使留下的边界确实严格更小。相同最小值可能得到同一跨度，重复评价不影响取最大。

前缀和保存前若干项之和，任意跨度的元素和用右前缀减左前缀取得，乘以a_i得到得分。和可达十的十一次方，乘积可达十的十七次方，两个量都要用long long。

若最大得分为零，则所有元素都为零，否则任一正数单独就有正分。此时最短最靠左的区间就是第一项。把初始答案设为零、端点都为一，比较时只接受更高分或更好的平局，就自然覆盖这个情况。

平局比较区间长度，再比较左端点，不按右端点单独排序。程序内部端点为零开始，输出统一加一。多组输入可以包含空行，整数流读取会跳过；结果之间输出一个空行，每组最后保留换行。''',
    '原数组非负；边界取严格更小；正最小值扩展严格有利；全零选第一项；平局最短再最左；乘积六十四位；组间恰一空行，末尾换行。',
    r'每组时间 $O(n)$，空间 $O(n)$。',['单调栈','前缀和'],S+['prefix','bindings'],True)

emit('P1950','把空白高度的所有后缀最小值相加，数每个右下角',
    '数网格内不含已画格子的全部非空长方形，沿格子边界剪，不是只求最大面积。',
    r'''逐行更新每列向上连续空白高度。固定底行和右列，一个左端点能选的矩形高度数就是对应列段的最小高度。用递增栈按相同最小高度合并左端点数量，并维护这些最小值总和。加入新高度h，弹出不小于h的组，减去旧贡献、累计其数量，再以h统一加回。每格把总和加入答案。''',
    r'''每个合法矩形有唯一底行与右列，按这个右下角分类就不会重复计数。固定底行后，height[j]记录该列向上连续多少格都是空白；画过的格子使高度归零。

选定一段连续列作为矩形宽度，能往上取的最大高度就是这段height的最小值。若它是三，就能取高度一、二、三三个矩形。因此当前右列的矩形数，等于所有以它结束的列区间的最小高度之和。

把这些左端点按得到的最小高度分组，栈里存高度及左端点数量，组高度递增。维护suffixSum为各组高度乘数量之和。

加入新列高度h时，旧后缀的最小值都会与h取小。只有栈尾高度不小于h的组需要改变，把它们的旧高度乘数量从suffixSum减去，数量合并；再加上从当前列自己开始的新左端点一个，以h统一计入。

其它较低的组最小值不会改变。更新后suffixSum恰是当前右下角的合法矩形数，把它加入总答案。h为零时旧高组全部降为零，当前右下角不产生矩形；这是障碍格正确切断范围的效果。

每行重新建栈，但height跨行累计。原网格可以逐行读取，不必全存。一千乘一千全空白时矩形数约为二千五百亿，远大于int；单组贡献、当前后缀和、总答案都在六十四位中计算。

这里是累加所有矩形，不能用只更新“最大宽乘高”的直方图最大面积模板替代。''',
    '高度只累计连续空白；画过格归零；数所有矩形而非最大面积；组数量是左端点数；更新前减旧贡献再合并；底行和右列确定唯一分类；六十四位。',
    r'时间 $O(nm)$，额外空间 $O(m)$。',['单调栈'],S+['monotone-contribution','strings','bindings'])

emit('P2564','将珠子按位置合并，用覆盖全部颜色的双指针窗口',
    '从数轴彩珠中截一段包含全部K种颜色的最短彩带，长度为两端坐标之差，多个珠子可同坐标。',
    r'''把每颗珠子记为坐标与颜色，统一按坐标排序。右端逐颗加入，计数每种颜色以及已覆盖种类数；覆盖全部颜色后不断尝试收缩左端，每次更新坐标差，直到失去一种颜色。两端都只前进。长度不是珠子数量，也不加一；同坐标的不同颜色可以得到长度零。''',
    r'''每种颜色的位置列表分别有序，但不同颜色交错在数轴上。先给每颗珠子附上颜色，把全部珠子按坐标合并成一个有序列表，保留同坐标的不同珠子。

一个最优彩带两端可以移到它最左、最右的珠子坐标而不丢任何颜色，所以只需考虑有序列表中的连续窗口。窗口的代价是两端坐标之差，而不是它包含几颗珠子。

count[color]保存窗口里该颜色数量，covered保存非零颜色数。右端加入一种原本数量为零的颜色时，covered增加一；删除左端使某色数量变为零时，covered减少一。

一旦covered等于K，当前窗口满足要求。先更新长度，再逐颗删除左端，直到某种颜色消失。对固定右端，这样找到了最短的有效左边界；更早且更宽的窗口不会更好。

右端继续前进后，左端不需退回。之前已经删除的左端都在当时有一个不更长的有效替代窗口；以后右端更远，再把它们取回只会更宽。两端总移动次数线性。

K种颜色按题意均实际存在，全体珠子是可行范围。K为一时单颗即可，长度零；多种颜色同坐标时也可能为零。输入位置可接近有符号三十二位上限，用long long保存坐标与差，输出不加一。''',
    '按坐标而非输入颜色分块处理；计数保留同色多颗；失去最后一颗才减少covered；长度是坐标差；同坐标可为零；不加一。',
    r'时间 $O(N\log N)$，空间 $O(N+K)$。',['双指针','排序'],A+['sort','two-pointers','bindings'])

emit('P6503','极差总和等于所有最大值贡献减所有最小值贡献',
    '求每个连续子数组的最大值减最小值，再把所有子数组结果相加。',
    r'''分别统计全部子数组最大值之和与最小值之和。用单调栈固定每项的归属范围，贡献为数值乘可选左端点数乘可选右端点数。重复极值统一交给最右者：最小值左边界严格更小、右边界小于等于；最大值对称。末尾用虚拟边界清栈。两种总和及乘法都用long long。''',
    r'''利用求和的线性性质，可以把每个区间的最大减最小拆成两份总和。关键变成每个元素分别负责多少个区间的最大值或最小值。

以最小值为例，同一最小值可能出现多次，约定区间交给其中最右的位置j。左边最近严格更小的位置记L，右边最近小于等于的位置记R，合法左右端点共有j减L乘R减j种。

允许左侧相等、禁止右侧相等，就保证j恰是最右最小项。若左右等号不区分，会漏算或重复算跨相等元素的区间。

递增栈扫描到新值不大于栈顶时，弹出的j找到了右界R；弹出后的新栈顶是左界L。直接加a_j乘两侧距离。扫描结束再用n这个虚拟右界清空栈，不能访问不存在的a[n]。

最大值完全对称，使用递减栈和相反比较。代码对两类各做一遍，最后最大贡献减最小贡献；同一项可以在两类中分别负责不同区间，不是要判断它只属于哪一边。

[COCI原卷](https://hsin.hr/coci/archive/2010_2011/contest3_tasks.pdf)给出三十万项、数值至多一亿。即使先保存全部最大值之和，上界约为四点五乘十的十八次方，仍在long long范围，但远超int。乘法要从long long的a_j开始，不能先在int中把两个距离相乘。

每个下标两次扫描中各入、出一次，整体线性。原样例七五七五的重复极值也不会因为平局归属重复计数。''',
    '求连续子数组；最大和与最小和分别算；重复极值一侧严格一侧不严格；虚拟右界不读a[n]；距离乘法先用六十四位；两个总和也都要六十四位。',
    r'时间 $O(n)$，空间 $O(n)$。',['单调栈'],S+['monotone-contribution'])

emit('P7410','最小值恰为一百，等于全不小于一百减全不小于一百零一',
    '统计方阵中最小绿度恰好为100的非空子矩形。',
    r'''先数所有格子至少100的矩形，再减所有格子至少101的矩形，剩下的恰好含100且没有更低值。每个阈值把合格格转为空白，用连续高度与单调栈统计全部全合格矩形：每个右下角贡献是各列后缀的最小高度和。两次均为方阵大小的线性扫描，计数用六十四位。''',
    r'''最小值恰好一百，等价于所有格子都至少一百，并且至少有一个格子等于一百。第二个条件不必直接放进矩形状态，可以从第一类里减去“所有格子都至少一百零一”的情况。

这与[官方分析的补集思路](https://usaco.org/current/data/sol_prob3_silver_feb21.html)一致。本文对每个阈值采用单调栈数全合格矩形，使每次扫描达到平方时间。

固定阈值，逐行更新height：当前格合格则在上一行高度上加一，不合格归零。对当前底行，一段连续列能往上组成多少矩形，恰好等于这段高度的最小值。

因此以某列为右边界的矩形数，是所有以该列结束的后缀最小值之和。栈保存不同最小高度及对应左端点数量；新高度h到来，把栈尾不小于h的组旧贡献扣掉，左端点数合并，再以h加回，另包含当前列开始的一种。

把每格这个后缀和累加，就覆盖全部底行、右列、左列与可选上边。每个矩形只对应一个这样的右下角与高度选择，不会重复。

分别计算阈值一百与一百零一，作差输出。全一百方阵的全部矩形都应计入；全一百零一方阵两次相同，答案为零。五百阶方阵矩形数超过三十二位，后缀和、两次总数与最终结果都使用long long。''',
    '最小值恰100不是所有格等100；减去至少101；两次阈值各自重建高度；计所有矩形不是最大面积；计数六十四位；单格也是矩形。',
    r'时间 $O(N^2)$，空间 $O(N^2)$，含输入方阵；每次计数额外空间 $O(N)$。',['单调栈','组合计数'],S+['monotone-contribution','bindings'])

emit('P9977','按体重降序批量占用塔顶，用有序队列压缩塔数',
    '至多M座塔，下方相邻奶牛至少重K，按各体重的大批数量给出，求最多放多少只牛。',
    r'''按体重从大到小处理，塔顶从重到轻排队。当前重w的牛能放到塔顶至少w加K的塔上，优先用最重塔顶；若最重也不行，其它都不行。同体重的塔合成数量，批量扣取可放塔，最后把新塔顶w的已放数量追加队尾。初始用M个无限重的虚拟空塔顶表示未启用塔，不能展开十亿座塔或所有奶牛。''',
    r'''从重到轻决定放置，每次加入的牛都只会成为新的塔顶。一个旧塔顶若足够重，可以接当前牛；还没处理的牛只会更轻，也能放到这个旧塔上。

为什么能贪心放当前牛？若某方案跳过它却以后在某个当前可接的塔上放一只更轻的牛，可以先用当前较重牛替换那只牛。它仍能站在旧塔顶上，且不会让后续更轻的上层更难放。若原方案在别的塔使用当前牛，也可交换对应上层安排。因此只要有可接塔，取当前牛不会减少最优总数。

可接塔里选择最重塔顶即可；若最重者都小于w加K，后面更轻者都不可能。新塔顶w不大于所有已存在顶，追加队尾就保持顺序，无需动态排序。

M及每种牛数量都可达十亿，不能每牛、每塔建立一个对象。队列改存塔顶体重与同类塔数量。一组w取用队首可接塔时，取当前剩余牛数与队首数量的较小者，批量扣去；队首耗尽则弹出。把本组成功放入的总数作为新塔顶组放到队尾。

同组的新塔顶等到整组分配完成再追加，K为正，同重牛本来也不能继续站在同重牛上。未能放下的剩余牛可以跳过，处理未来更轻组，它们可能用得上当前不够重的塔顶。

初始队列放一个虚拟无限重组，数量M，每取一个就相当于启用一座新塔。虚拟值用足够大的long long，不使用浮点无穷；总牛数至多二十万乘十亿，也需六十四位。

[官方分组实现](https://usaco.org/current/data/sol_prob1_silver_dec23.html)同样通过批量队列避免展开数量。每个新组入队一次、每个旧组至多弹出一次，排序后的队列处理是线性的。''',
    '重牛在下且只查直接相邻差；至多M座不是必须M座；虚拟空塔压成一组；同重数量批量处理；当前放不下不代表以后轻牛也放不下；总数量六十四位。',
    r'时间 $O(N\log N)$，空间 $O(N)$。',['贪心','队列'],A+['sort','greedy','queue-stack','bindings'])

emit('P10277','先用最早完成堆定时间，再沿面试时刻的反向图追溯',
    '按固定队列安排N头牛面试，K名农夫同时完成时可任选；求Bessie的确定开始时刻，以及每名农夫能否在某种偏好下为她面试。',
    r'''每次取最早完成时刻，加下一头牛耗时再入堆；相同时取谁都得到相同完成时刻多重集合，所以Bessie开始时间唯一。每次面试建立开始时刻到结束时刻的有向边。由Bessie开始时刻反向找所有可到达时刻，农夫i若其固定第一场结束t_i被找到，就可能接续到Bessie。时刻排序离散化后，用显式栈遍历，不把不同历史时刻简单并查集合并。''',
    r'''先只看完成时间，不看农夫名字。下一头牛必在最小完成时刻开始，耗时由牛编号固定。多个农夫此时完成时，取出的都是同一个时间，插回同一个新结束时间，所以堆内完成时刻的多重集合不随偏好改变。模拟完N头牛，堆顶就是Bessie唯一的开始时刻T。

名字的可能性则要保留时间顺序。对每场已经安排的面试，建立从开始时刻到结束时刻的一条边。所有同刻空闲的农夫都可选择此时开始的某一场；若跟随一名农夫，它的可选后续正好沿这些边前进。

初始第i名农夫固定面试第i头牛，所以他的第一场结束时刻为t_i。该农夫能面试Bessie，当且仅当从t_i能沿面试边到达T。必要性来自真实接续路径；充分性是沿这条路径在每次同时空闲时选择相应下一场，其余空闲农夫承担同刻其余场次即可。这里只分别问每名农夫是否存在一种选择，不要求所有位同时实现。

从T沿反向边遍历一次，就能找出全部可能的初场结束时刻。不应检查共同初始时刻零，因为所有农夫的第一场都从零开始，那会丢掉初始身份的区别。

不能把历史上同时完成的农夫不分先后直接并查集合并。例如初始耗时二、十、十，之后九头牛耗时十一、十、四、一、十、八、五、八、五。第二、三人曾在十同时完成，第一、三人又在十四同时完成；Bessie在二十五开始，只能由第二或第三人面试。无向连通却会把第一人也加进来。

本文采用[官方分析中的时刻图模型](https://usaco.org/current/data/sol_prob1_silver_open24.html)，将所有开始、结束时间排序去重，用二分查找映射到紧凑编号。边反向保存，显式栈标记每个时刻只访问一次；不用递归处理三十万场的长链。

时刻可能达到三十万乘十亿，使用long long。第二行必须是长度K的连续零一字符串，不在位之间插空格。当前实现含时刻排序与二分映射，复杂度按它们计入，不宣称仅有堆操作的界。''',
    '完成时刻多重集合唯一，农夫身份未必唯一；初始i固定对应t_i；从T走反边；检查初场结束而非共同开始零；保留历史方向；时刻六十四位；位串连续输出。',
    r'时间 $O(N\log N+N\log K)$，空间 $O(N+K)$。',['堆','DFS'],A+['heap','graphs','sort','bounds','lambda-local'],True)

emit('CF547B','每个最小项给出最大支配跨度，再由长窗口向短传播',
    '对每种窗口长度k，求所有长k连续窗口最小值中的最大者。',
    r'''用两次单调栈找每项左右最近严格更小者，它们之间的跨度都至少有当前值。令长度len的候选答案更新为当前值；这个跨度还能提供所有不大于len的窗口，所以最后从长到短取后缀最大值传播。不能把每个元素只贡献给一个长度后直接输出空格未填的表。''',
    r'''固定位置i和值a_i，左右扩到第一个严格更小项之前。这段跨度内所有值至少a_i，并且包含a_i，因此整段最小值恰为a_i，长度记len。

对任意k不超过len，都能在这段跨度中选择一个包含i的长k连续窗口，最小值仍是a_i。所以一个位置不只影响跨度len，还能为所有较短长度提供同样强度。

先只把a_i更新到answer[len]，取同长度候选的最大者。之后从n减一向一倒序，使answer[k]至少等于answer[k加一]，就完成所有长跨度向短窗口的传播。

为什么没有遗漏更强答案？任一长k窗口选它的某个最小项i，这个窗口一定包含在i的最大跨度中，所以len至少k，它的最小值会从answer[len]传播过来。反过来，每个传播候选都有实际的长k窗口见证，不会虚增。

左右两边都找严格更小，等高元素可以包含在跨度内。例如所有高度相同，每个最大跨度都是整段；只更新n这一格后，后缀最大值传播恰使全部长度都得到相同高度。

本题高度均为正，答案表初始化为零可表示尚无候选。它不是数所有区间的贡献，因此不需要用左右一严一松来分配重复最小值；这里只取最大，同一跨度多次评价没有问题。''',
    '每个长度求窗口最小值的最大者；边界严格更小；等高可跨；长跨度也能提供短窗口；倒序做后缀最大；不是输出左右跨度本身。',
    r'时间 $O(n)$，空间 $O(n)$。',['单调栈'],S,True)

emit('CF1237D','三份循环数组上双指针延伸，用最大队列判断第一首坏歌',
    '循环播放，从每个起点求停歌前听完的曲目次数；新歌严格小于已听最大值的一半就立刻停止，触发曲目不计入。',
    r'''全局最大不超过最小的两倍时，永远不会触发，全部负一。否则最多经过两圈就会遇到全局最大之后的全局最小，把数组复制三份足够所有起点。右指针保存当前首个坏歌位置，队列维护已听区间最大值；新歌两倍不小于最大才加入。左端前进只会减小历史最大，不会破坏旧有效前缀，右端可继续前移。''',
    r'''比较是严格小于一半，没有四舍五入。使用二乘新值小于历史最大值判断，避免浮点。等于一半仍可继续；历史最大值只来自已经听过的曲目，触发曲目不计入答案。

若全局最大值不大于全局最小值的两倍，任何新歌都不会低到触发，所有起点答案为负一。否则从任一起点出发，一圈内会遇到全局最大，接下来一圈内必遇到足够小的全局最小，最迟在两圈内停止。

把数组复制三份，为全部n个起点提供足够右侧空间。维护当前已听的半开区间左端至right之前，以及该区间最大值的单调队列。

若队列为空，第一首总可听；否则只有二乘a[right]至少队首最大值，才把这首加入。加入时从队尾移走不大于它的旧候选，再把right前进。循环停下时right是第一首坏歌，已听数量就是right减left。

换到下一个起点时，删掉队首可能对应的旧left。旧有效前缀删去最左项后仍有效，因为每首歌之前的最大值只会降低，不会让已经通过的二倍比较变坏。因此right无需后退，可以从旧坏歌继续尝试。

这说明双指针的单调性来自“缩小历史集合只会降低最大值”，不只是数组复制了三份。队列用绝对下标判断离开区间，同一原曲子在不同圈出现是不同次数，不能按原编号去重。

全局极值与二倍计算使用long long。每个复制位置只加入、弹出一次，整体线性；三份数组并不意味着要对每个起点单独扫三n项。''',
    '严格小于一半才停；等于继续；触发歌不计；历史最大只含已经听者；同一歌重复播放逐次计；永不停止先判；左移后右指针不退；绝对下标处理过期。',
    r'时间 $O(n)$，空间 $O(n)$。',['队列','双指针'],S+['two-pointers','queue-stack','iterators'],True)
