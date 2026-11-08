from core7_completion import add

PREFIX=r'''
vector<int>prefix(const string&s){vector<int>p(s.size());for(int i=1;i<(int)s.size();i++){int j=p[i-1];while(j&&s[i]!=s[j])j=p[j-1];if(s[i]==s[j])j++;p[i]=j;}return p;}
'''

add('CF808G','KMP 自动机上的最大匹配次数 DP',
    '状态记录已经处理的文本前缀，以及当前匹配的模式前缀长度。问号枚举替换字母，完成一次模式就增加答案并回退到最长 border，以允许重叠。题目保证两串长度乘积不超过一千万。',
    '仅贪心地优先完成眼前一次出现，可能影响后续重叠，因此要保留不同的模式匹配状态。令 dp[j] 为处理当前文本前缀、KMP 状态为 j 时能得到的最多出现次数。\n\n先由模式前缀函数建立自动机：每个状态与每个字母对应一个新状态，以及是否刚完成一次匹配。完成后把状态回退到 pi[m−1]，因为已经匹配的后缀还能作为下一次匹配开头。\n\n固定字符只做对应转移；问号枚举二十六个字母，并对新状态取最大。每一份问号替换方案都沿着一条状态路径，不同路径落在相同状态时，仅保留更大得分，未来不会受损。最后取所有状态中的最大值。\n\n长度乘积限制使 O(26|s||t|) 可行；若模式比文本还长，直接输出零。',
    '时间 O(26|s||t|)，空间 O(26|t|)。','完整匹配后保留 border；问号只改变当前位置；利用长度乘积保证。',r'''
string s,t;cin>>s>>t;int n=s.size(),m=t.size();if(m>n){cout<<0<<'\n';return 0;}auto p=prefix(t);vector<array<int,26>>next(m),gain(m);for(int state=0;state<m;state++)for(int c=0;c<26;c++){int v;if(t[state]-'a'==c)v=state+1;else v=state?next[p[state-1]][c]:0;gain[state][c]=v==m;next[state][c]=v==m?p[m-1]:v;}const int neg=-1000000000;vector<int>dp(m,neg),updated(m);dp[0]=0;for(char ch:s){fill(updated.begin(),updated.end(),neg);int first=ch=='?'?0:ch-'a',last=ch=='?'?25:first;for(int state=0;state<m;state++)if(dp[state]>=0)for(int c=first;c<=last;c++)updated[next[state][c]]=max(updated[next[state][c]],dp[state]+gain[state][c]);dp.swap(updated);}cout<<*max_element(dp.begin(),dp.end())<<'\n';
''',PREFIX)

add('P2375','KMP 维护不重叠 border 数量',
    '先用前缀函数计算每个前缀的 border 链长度，再用第二次 KMP 扫描维护不超过当前长度一半的最长 border。它的整条 border 链都合法，按题意将数量加一后相乘。',
    '长度为 len 的前缀中，前后缀不重叠等价于 border 长度不超过 len/2。最长 border 的其它 border 也都是原前缀的 border，所以只要找到满足长度限制的最长者 j，所有合法 border 就是 j 自身及它的 border 链。\n\n先求 pi，并令 count[len]=count[pi[len−1]]+1，表示从该前缀自身到最短非空 border 的链长。第二次从左向右维护匹配长度 j，先按 KMP 匹配当前字符，再在 2j>len 时沿 pi 回退。合法 border 数就是 count[j]。\n\n不能对每个前缀都从它完整的最长 border 重新一路退到一半，那在全相同字符中会平方级。第二次扫描复用上一前缀的 j，每步增长至多一，所有回退合计线性。答案乘 count[j]+1，并随时取模。',
    '每组时间 O(n)，空间 O(n)。','count[0]=0；先限制不重叠，再乘数量加一；模数为 1000000007。',r'''
int tests;cin>>tests;while(tests--){string s;cin>>s;int n=s.size();auto p=prefix(s);vector<int>count(n+1);for(int len=1;len<=n;len++)count[len]=count[p[len-1]]+1;long long ans=1;int j=0;for(int len=2;len<=n;len++){while(j&&s[len-1]!=s[j])j=p[j-1];if(s[len-1]==s[j])j++;while(2*j>len)j=p[j-1];ans=ans*(count[j]+1)%1000000007;}cout<<ans<<'\n';}
''',PREFIX)

add('P4551','根路径异或与二进制字典树',
    '任选根，记录根到每点的边权异或 d。两点路径异或为 d[u] xor d[v]。把所有 d 插入二进制字典树，逐位优先走相反位，求最大异或值。',
    '两条根路径的公共部分在异或中出现两次，会相互抵消，剩下的正是 u 到 v 的路径。因此树上路径问题变成从全部根路径异或值中选两个数，使异或最大。\n\n从最高二进制位开始比较大小。查询值这一位为 b 时，若字典树存在 1−b 分支，就使结果当前位为一；高位一的收益大于所有低位之和，所以这是安全的贪心选择。不存在反位才走同位。\n\n先用显式遍历计算 d，再插入并查询所有数。允许与自己配对得到零，不会使最大值变错；只有一个顶点时答案也为零。',
    '时间 O(n log W)，空间 O(n log W)。','先求根路径异或而非距离和；高位优先；非递归遍历避免长链栈溢出。',r'''
int n;cin>>n;vector<vector<pair<int,int>>>g(n);for(int i=1;i<n;i++){int a,b,w;cin>>a>>b>>w;a--;b--;g[a].push_back({b,w});g[b].push_back({a,w});}vector<int>d(n),parent(n,-1),order={0};parent[0]=0;for(int i=0;i<(int)order.size();i++){int v=order[i];for(auto [u,w]:g[v])if(u!=parent[v]){parent[u]=v;d[u]=d[v]^w;order.push_back(u);}}vector<array<int,2>>t(1);for(int x:d){int v=0;for(int b=30;b>=0;b--){int bit=(x>>b)&1;if(!t[v][bit]){t[v][bit]=t.size();t.push_back({0,0});}v=t[v][bit];}}int ans=0;for(int x:d){int v=0,value=0;for(int b=30;b>=0;b--){int bit=(x>>b)&1;if(t[v][bit^1]){value|=1<<b;v=t[v][bit^1];}else v=t[v][bit];}ans=max(ans,value);}cout<<ans<<'\n';
''')

add('CF817E','带计数的异或字典树',
    '字典树每个节点记录当前有多少数经过。查询 x xor y<p 时逐位比较：p 当前位为一，可把异或位为零的整支加入答案，再沿异或位为一的分支继续；p 位为零时只能沿同位。',
    '比较二进制整数时，第一次不同的高位决定大小。查询过程中，当前路径对应的异或前缀始终与 p 相同。若 p 当前位为一，把异或位设零就已严格更小，后面任意取值，因此整支数量直接加入答案；继续搜索的另一支则保持当前位相同。若 p 当前位为零，只能令异或位为零。\n\n插入和删除都沿完整数值路径更新经过计数，重复值分别累计。删除只把计数减一，不必物理回收节点，查询遇到计数为零的分支自然无贡献。\n\n扫描完全部位仍相等的数不能计入，因为条件是严格小于 p。p=0 时自然返回零。',
    '每次操作 O(log W)，空间 O(插入次数·log W)。','条件是严格小于；允许重复值；删除更新整条路径计数。',r'''
int q;cin>>q;vector<Node>t(1);while(q--){int op,x;cin>>op>>x;if(op<3){int v=0,delta=op==1?1:-1;t[v].count+=delta;for(int b=30;b>=0;b--){int bit=(x>>b)&1;if(!t[v].child[bit]){t[v].child[bit]=t.size();t.push_back(Node());}v=t[v].child[bit];t[v].count+=delta;}}else{int p;cin>>p;int v=0,ans=0;for(int b=30;b>=0;b--){int bit=(x>>b)&1;if((p>>b)&1){int same=t[v].child[bit];if(same)ans+=t[same].count;v=t[v].child[bit^1];}else v=t[v].child[bit];if(!v)break;}cout<<ans<<'\n';}}
''',r'''
struct Node{int child[2]={0,0},count=0;};
''')

add('P5018','对子树与镜像子树做精确编号',
    '自底向上为 (点权,左子树编号,右子树编号) 分配唯一编号，同时计算交换左右后的镜像编号。两编号相等时，该子树对称；取其中最大节点数。',
    '只比较左右子树大小或点权和不足以保证结构一致。应把一棵有根有序树完整表示为三元组：根点权、左子树结构编号、右子树结构编号。用同一张 map 为相同三元组分配相同编号，就能精确判断整棵结构与点权是否相等。空树编号为零。\n\n原树编号由两个原子树编号构造；镜像编号则由右子树的镜像编号、左子树的镜像编号构造。一个节点原编号等于镜像编号，当且仅当它的完整子树在交换所有左右孩子后保持不变。\n\n先从根遍历得到父先子后的顺序，再倒序处理，确保孩子已计算。与此同时累计子树节点数。这样不受输入编号是否为后序影响，也不会在百万点长链上递归溢出。map 比较完整三元组，不使用存在碰撞的数值哈希。',
    '时间 O(n log n)，空间 O(n)。','孩子 -1 转为空树 0；点权也属于结构；使用真实遍历顺序倒序处理。',r'''
int n;cin>>n;vector<int>w(n+1),l(n+1),r(n+1),id(n+1),mirror(n+1),size(n+1);for(int i=1;i<=n;i++)cin>>w[i];for(int i=1;i<=n;i++){cin>>l[i]>>r[i];l[i]=max(l[i],0);r[i]=max(r[i],0);}vector<int>order={1};for(int i=0;i<(int)order.size();i++){int v=order[i];if(l[v])order.push_back(l[v]);if(r[v])order.push_back(r[v]);}map<tuple<int,int,int>,int>ids;auto intern=[&](int value,int a,int b){auto key=make_tuple(value,a,b);auto it=ids.find(key);if(it!=ids.end())return it->second;int index=ids.size()+1;ids.emplace(key,index);return index;};int ans=0;for(int i=n-1;i>=0;i--){int v=order[i];id[v]=intern(w[v],id[l[v]],id[r[v]]);mirror[v]=intern(w[v],mirror[r[v]],mirror[l[v]]);size[v]=size[l[v]]+size[r[v]]+1;if(id[v]==mirror[v])ans=max(ans,size[v]);}cout<<ans<<'\n';
''')

add('P3065','字典树分歧生成字母先后约束',
    '要让某词排第一，沿它的字典树路径遇到其它分支时，当前字母必须比那些分支字母更小。若有更短单词是它的前缀，立即不行；否则检查字母约束图是否有环。',
    '两个单词的字典序由第一个不同的字母决定。如果候选词经过字符 x 的分支，而同一节点还有字符 y 的其它分支，就必须规定 x 排在 y 前面。把所有这样的要求建成二十六个字母上的有向边。\n\n若沿候选路径已经遇到一个单词终点，说明另一个单词是候选的真前缀。无论如何重排字母，短前缀都在前面，因此候选不可行。到候选终点后的更长扩展则没有影响，因为候选本身更短。\n\n约束图无环时，存在一个拓扑序作为完整字母表，所有字典树分歧都按候选更小排列，候选就排在全部其它词前面；有环时相互矛盾，不可能实现。按输入顺序收集全部可行词。',
    '时间 O(L·26+n·26²)，空间 O(L+n)，L 为总词长。','前缀冲突单独判断；约束是候选字母→其它字母；重边不重复加入入度。',r'''
int n;cin>>n;vector<string>words(n);vector<Node>trie(1);for(auto &s:words){cin>>s;int v=0;for(char c:s){int b=c-'a';if(!trie[v].child[b]){trie[v].child[b]=trie.size();trie.push_back(Node());}v=trie[v].child[b];}trie[v].end=true;}vector<string>ans;for(auto &s:words){bool edge[26][26]={};bool ok=true;int v=0;for(char c:s){if(trie[v].end){ok=false;break;}int x=c-'a';for(int y=0;y<26;y++)if(y!=x&&trie[v].child[y])edge[x][y]=true;v=trie[v].child[x];}int in[26]={};for(int x=0;x<26;x++)for(int y=0;y<26;y++)in[y]+=edge[x][y];queue<int>q;for(int x=0;x<26;x++)if(!in[x])q.push(x);int count=0;while(!q.empty()){int x=q.front();q.pop();count++;for(int y=0;y<26;y++)if(edge[x][y]&&--in[y]==0)q.push(y);}if(ok&&count==26)ans.push_back(s);}cout<<ans.size()<<'\n';for(auto&s:ans)cout<<s<<'\n';
''',r'''
struct Node{array<int,26>child={};bool end=false;};
''')

add('P1381','所需单词筛选与覆盖滑动窗口',
    '先统计文章中实际出现了多少种待背单词，再用双指针求包含这些种类的最短连续片段。字典之外的词仍占文章位置，但不增加覆盖种数。',
    '有些待背单词根本没有出现在文章中，无论截取多长都无法包含它们。所以第一问先求字典与文章出现词的交集种数 need，第二问只要求覆盖这 need 种。\n\n用字典把待背词映射到编号，文章中的其它词标为 −1。右端逐词加入，某词频次从零变一时覆盖种数加一。当覆盖数达到 need 时，记录当前长度并不断右移左端：删除不需要的词，或删除仍有其它副本的词，直到缺少一种为止。\n\n对于固定右端，这样得到最靠右且仍合法的左端，窗口最短；右端遍历全部位置，就覆盖了全局最优。每个位置至多入窗、出窗各一次。need=0 时直接输出两行零。',
    '平均时间 O(总输入字符数+n+m)，空间 O(n+m)。','按种类而非出现次数统计；无关词仍计入片段长度；need=0 特判。',r'''
int n;cin>>n;unordered_map<string,int>dict;while(n--){string s;cin>>s;if(!dict.count(s)){int id=dict.size();dict[s]=id;}}int m;cin>>m;vector<int>a(m,-1),exists(dict.size());for(int i=0;i<m;i++){string s;cin>>s;auto it=dict.find(s);if(it!=dict.end()){a[i]=it->second;exists[it->second]=1;}}int need=accumulate(exists.begin(),exists.end(),0);cout<<need<<'\n';if(!need){cout<<0<<'\n';return 0;}vector<int>freq(dict.size());int have=0,l=0,best=m+1;for(int r=0;r<m;r++){if(a[r]>=0&&freq[a[r]]++==0)have++;while(have==need){best=min(best,r-l+1);if(a[l]>=0&&--freq[a[l]]==0)have--;l++;}}cout<<best<<'\n';
''')

add('P2580','名单查询与已点名标记',
    '用集合保存合法姓名，另一个集合保存已经正确点到的姓名。先判断是否合法，再区分首次点名和重复点名。',
    '同一个名字需要区分三种状态：不在名单、在名单且未点到、在名单且已点到。把名单和已点名记录分开保存，就能让状态转换清楚。\n\n每次收到名字，先查询合法名单。不存在就输出 WRONG，且不修改任何合法同学的记录。存在时向已点名集合插入：插入成功表示此前没有它，输出 OK；插入失败表示早已出现，输出 REPEAT。\n\n重复报错名仍应一直输出 WRONG，不能因为曾经输入过就变成 REPEAT。使用 set 按完整字符串比较，不依赖可能冲突的手写哈希。',
    '时间 O((n+m)·L log(n+m))，空间 O((n+m)L)，L 为姓名长度。','先判断名单合法性；错误名字不能进入正确点名记录。',r'''
int n;cin>>n;set<string>names,called;while(n--){string s;cin>>s;names.insert(s);}int m;cin>>m;while(m--){string s;cin>>s;if(!names.count(s))cout<<"WRONG\n";else cout<<(called.insert(s).second?"OK":"REPEAT")<<'\n';}
''')

add('P2957','枚举两种前后缀重合',
    '重合可以是第一串后缀与第二串前缀，也可以反过来。枚举长度并比较两种方向，取最大的相等长度。',
    '题目中的重合不要求出现在两个串内部的任意位置，而是必须同时是某串的后缀和另一串的前缀。只有两种方向，都要检查。\n\n对长度 len，从 1 到两个长度的较小值，分别比较 a 的最后 len 个字符与 b 的前 len 个字符，以及 b 的最后 len 个字符与 a 的前 len 个字符。任意一组相等，就能更新答案为 len。\n\n字符串至多八十个字符，直接调用 compare 逐字符比较已经足够，避免为很小的输入引入不必要的哈希与碰撞问题。完全没有非空重合时答案保持零。',
    '时间 O(L²)，空间 O(1)。','两个方向都检查；允许整个较短串成为重合部分。',r'''
string a,b;cin>>a>>b;int ans=0;for(int len=1;len<=(int)min(a.size(),b.size());len++)if(a.compare(a.size()-len,len,b,0,len)==0||b.compare(b.size()-len,len,a,0,len)==0)ans=len;cout<<ans<<'\n';
''')

add('P3375','前缀函数驱动的 KMP',
    '先求模式串的前缀函数。扫描文本时，失配沿前缀函数回退，匹配到整个模式就输出起点并继续回退，以保留重叠匹配。最后输出模式串前缀函数。',
    '前缀函数 pi[i] 表示模式前缀 0…i 的最长相等真前后缀长度。计算时令 j=pi[i−1]，若新字符不能接在长度 j 的前缀之后，就退到 pi[j−1]，直到能匹配或 j 为零。\n\n扫描文本时，j 同样表示已匹配的模式前缀长度。匹配成功就 j++，失配则沿同一条前后缀链回退。被跳过的前缀不可能匹配，因为它们不是当前已匹配串的后缀。每个字符至多使 j 前进一步，回退总次数也线性。\n\n当 j 等于模式长度时，一次匹配在当前文本下标结束，转换为从一开始的起点输出。随后令 j=pi[j−1]，这样 aaa 在 aaaaa 中的重叠出现不会遗漏。',
    '时间 O(|文本|+|模式|)，空间 O(|模式|)。','匹配输出使用 1 起始位置；完整匹配后回退而非清零。',r'''
string text,pattern;cin>>text>>pattern;auto p=prefix(pattern);int j=0;for(int i=0;i<(int)text.size();i++){while(j&&text[i]!=pattern[j])j=p[j-1];if(text[i]==pattern[j])j++;if(j==(int)pattern.size()){cout<<i-j+2<<'\n';j=p[j-1];}}for(int x:p)cout<<x<<' ';cout<<'\n';
''',PREFIX)

add('P3435','沿 border 链求最短非空 border',
    '对每个前缀，若它存在真 border，最长合法周期块长度等于前缀长度减去最短非空 border 长度。用前缀函数递推每个前缀的最短 border，再求和。',
    '若长度为 len 的前缀存在长度 b 的真 border，就满足首 b 个字符等于末 b 个字符，相应可选重复结构的块长为 len−b。要让块最长，就应取最短的非空 border。\n\n最长 border 为 pi[len−1]，其它 border 正好沿着这个前缀的 border 链继续回退。令 shortest[len] 为最短非空 border：没有 border 时为零；若最长 border 本身没有更短 border，则取它；否则复用 shortest[最长border]。\n\n按长度递增计算，依赖总是已经算好的更短前缀。对有 border 的前缀把 len−shortest[len] 累加，没有 border 则贡献零。总答案可能二次增长，要用 long long。',
    '时间 O(n)，空间 O(n)。','这里要最短非空 border；不能只使用最长 border；总和用六十四位。',r'''
int n;string s;cin>>n>>s;auto p=prefix(s);vector<int>shortest(n+1);long long ans=0;for(int len=1;len<=n;len++){int b=p[len-1];if(b){shortest[len]=shortest[b]?shortest[b]:b;ans+=len-shortest[len];}}cout<<ans<<'\n';
''',PREFIX)

add('P4391','由最长 border 得到最短周期',
    '求整个字符串的最长真前后缀长度 b，答案为 n−b。电台发送的最后一轮可以不完整，因此不要求周期长度整除 n。',
    '如果一个长度为 n 的字符串可以由长度 p 的循环节生成，那么第 p 个字符之后的部分，应与从开头开始的 n−p 个字符相等，这正是长度为 n−p 的 border。\n\n反过来，若前 n−p 个字符等于后 n−p 个字符，就有 s[i]=s[i−p] 对所有 i>=p 成立，所以首 p 个字符不断重复即可生成整段接收内容。最短周期对应最长 border，故 p=n−pi[n−1]。\n\n接收可能在某个循环节中途停止，所以不能套用“若 n 不能整除 p 就取 n”的整串幂判断。这里即使没有整除关系，p 仍是合法答案。',
    '时间 O(n)，空间 O(n)。','无需检验 n%周期；输入含给定长度。',r'''
int n;string s;cin>>n>>s;auto p=prefix(s);cout<<n-p.back()<<'\n';
''',PREFIX)

add('P4824','字符栈同时保存 KMP 状态',
    '逐字读入原串，把字符与当前模式匹配长度一起压栈。每当匹配完整个待删串，就弹出对应长度；新的匹配状态从栈顶恢复。',
    '删除一个出现后，原来两侧的字符会接到一起，可能产生新的出现，所以不能只在原串上标记所有匹配位置。应实时维护删除后的字符串。\n\n用字符串模拟栈，另一个栈保存加入每个字符后的 KMP 匹配长度。新字符到来时，从当前长度沿前缀函数回退，再尝试扩展，随后把字符和新长度压入。若长度达到模式长度，删除栈尾同样多的字符与状态。\n\n删除后恢复到新的栈顶状态，恰好等于剩余字符串对应的 KMP 状态，因此后续能发现跨删除边界的新匹配。每个字符只入栈一次、出栈至多一次；KMP 回退总量也线性。',
    '时间 O(|原串|+|待删串|)，空间 O(|原串|+|待删串|)。','删除后恢复旧栈顶状态；模式可能重叠；不要每次重新扫描完整结果。',r'''
string s,t;cin>>s>>t;auto p=prefix(t);string out;vector<int>state;for(char c:s){int j=state.empty()?0:state.back();while(j&&c!=t[j])j=p[j-1];if(c==t[j])j++;out.push_back(c);state.push_back(j);if(j==(int)t.size()){out.resize(out.size()-t.size());state.resize(state.size()-t.size());}}cout<<out<<'\n';
''',PREFIX)

add('CF1200E','KMP 找新单词与当前串的最大重合',
    '每次只需比较新单词的前缀与当前结果的后缀。对“新单词#当前结果的末尾部分”求前缀函数，得到最大重合长度，把新单词剩余部分追加。',
    '前面合并出的结果不能改变顺序，只能把新单词接在末尾。可省略的字符必须同时是新词前缀和已有结果后缀，因此找最长这样的重合即可。\n\n重合长度不会超过新词长度，所以从已有结果只截取最后 min(结果长度,新词长度) 个字符。构造 word+# +tail，分隔符不会出现在原字母串中，末位置的前缀函数就只能表示 word 的前缀与 tail 的后缀相等的长度。\n\n把 word 从该长度之后的部分追加。每次处理长度至多新词长度的常数倍，因此总时间与全部输入长度成正比。结果使用 string 原地追加，避免反复复制整个旧结果。',
    '总时间 O(全部单词长度)，空间 O(结果长度+最长单词长度)。','只取当前结果的必要后缀；分隔符必须不在单词中。',r'''
int n;cin>>n;string result;while(n--){string word;cin>>word;if(result.empty()){result=word;continue;}string probe=word+'#'+result.substr(result.size()-min(result.size(),word.size()));int overlap=prefix(probe).back();result+=word.substr(overlap);}cout<<result<<'\n';
''',PREFIX)

add('UVA11475','寻找最长回文后缀',
    '只允许向末尾添加字符，故保留原串最长的回文后缀，把前面剩余部分反转后追加。用反串与原串构造 KMP 前缀函数求该后缀长度。',
    '假设原串分为 A+B，其中 B 是回文，那么追加 reverse(A) 后得到 A+B+reverse(A)，显然是回文。要添加最少，就要让 B 尽可能长。\n\n令 rev=reverse(s)，对 rev+# +s 求前缀函数。末尾的 border 同时是 rev 的前缀和 s 的后缀，意味着这段后缀等于自身反转，因此正好是最长回文后缀。分隔符防止匹配越过反串边界。\n\n答案可以直接输出原串，再输出 rev 从该回文长度之后的部分。输入多行直到 EOF，每个串单独处理，单字符与原本就是回文的串无需添加。',
    '每串时间 O(n)，空间 O(n)。','求最长回文后缀而非前缀；输入到 EOF；保留原串。',r'''
string s;while(cin>>s){string rev=s;reverse(rev.begin(),rev.end());int len=prefix(rev+'#'+s).back();cout<<s<<rev.substr(len)<<'\n';}
''',PREFIX)

add('P3449','回文串拼接等价于共享最小循环节',
    '两个输入串本来都是回文。它们拼接仍回文当且仅当 ab=ba，即二者都是同一个最小循环节的若干次重复。求每串最小循环节，按内容分组，答案为各组大小平方之和。',
    '由于 a、b 各自回文，reverse(ab)=reverse(b)reverse(a)=ba。因此 ab 为回文当且仅当 ab=ba。\n\n两个非空字符串可交换拼接，当且仅当它们都是同一个原始串的幂。这个性质可由消去较短前缀反复证明：若 |a|<=|b|，等式迫使 b 以 a 开头，消去这段后得到 a 与剩余部分仍可交换，过程类似欧几里得算法，最终得到共同的最短循环节。\n\n用前缀函数得到候选周期 p=len−pi[len−1]。若 len 能被 p 整除，首 p 个字符就是最小循环节；否则循环节是整个串。按这个实际字符串分组。组内任意有序二元组都合法，包括自己与自己，所以大小 c 的组贡献 c²。',
    '时间 O(L log n)，空间 O(L)，L 为输入总长度。','输入串已保证回文；只有完整重复时才缩短周期；计有序对与自身配对。',r'''
int n;cin>>n;map<string,long long>count;while(n--){int len;string s;cin>>len>>s;auto p=prefix(s);int period=len-p.back();if(len%period)period=len;count[s.substr(0,period)]++;}long long ans=0;for(auto &[root,c]:count)ans+=c*c;cout<<ans<<'\n';
''',PREFIX)

add('SP4033','排序后只比较相邻号码',
    '将所有电话号码按字典序排序。若一个号码是另一个的前缀，它们之间紧邻它的下一个号码也以它为前缀，因此只需检查相邻两项。',
    '字典序会把拥有同一前缀的字符串放在连续的一段中，而且前缀本身排在它所有更长的扩展之前。因此只要某号码是另一个号码的前缀，排序后它紧邻的后一个号码也必定拥有这个前缀。\n\n依次比较相邻号码，检查后一项开头与前一项是否相同。找到一次就不一致；全部检查通过才一致。相同的两个号码也互为前缀，应判为不一致。\n\n号码须作为字符串读取，不能转整数，否则前导零会丢失，长度与前缀关系会改变。',
    '时间 O(nL log n)，空间 O(nL)。','使用字符串保存前导零；重复号码也不一致；每组读完再判断。',r'''
int t;cin>>t;while(t--){int n;cin>>n;vector<string>a(n);for(auto&s:a)cin>>s;sort(a.begin(),a.end());bool ok=true;for(int i=1;i<n;i++)if(a[i].compare(0,a[i-1].size(),a[i-1])==0)ok=false;cout<<(ok?"YES":"NO")<<'\n';}
''')

add('P2922','字典树中统计祖先终点与子树终点',
    '把拦截到的信息插入二进制字典树。对每条暗号，沿路径累加严格祖先的结束次数，走到末端后再加整棵子树的信息数，即覆盖信息更短和信息不短于暗号的两种情况。',
    '两串匹配要求它们在较短长度内完全相同，因此合法信息要么是暗号的前缀，要么以暗号为前缀。字典树恰好把这两种关系变成祖先和后代。\n\n插入每条信息时，经过的节点的 sub 都加一，最后节点的 end 加一。查询暗号时，在每次向下一位之前，把当前节点的 end 加入答案，这些是已经结束、严格短于暗号的信息。若路径不存在，后面不再有更长匹配，但此前得到的短信息仍有效。\n\n若整个暗号走完，加入当前节点的 sub，它包括与暗号等长以及更长的信息。祖先累加不含当前节点，所以等长信息只计一次。路径丢失后仍须把本条查询剩余输入读完。',
    '时间 O(输入总位数)，空间 O(拦截信息总位数)。','同一信息可能重复，应按次数计；等长匹配不重复；失败后继续读取剩余位。',r'''
int m,n;cin>>m>>n;vector<Node>t(1);for(int i=0;i<m;i++){int len;cin>>len;int v=0;t[v].sub++;while(len--){int b;cin>>b;if(!t[v].child[b]){t[v].child[b]=t.size();t.push_back(Node());}v=t[v].child[b];t[v].sub++;}t[v].end++;}while(n--){int len;cin>>len;int v=0,ans=0;bool alive=true;while(len--){int b;cin>>b;if(alive){ans+=t[v].end;int next=t[v].child[b];if(!next)alive=false;else v=next;}}if(alive)ans+=t[v].sub;cout<<ans<<'\n';}
''',r'''
struct Node{int child[2]={0,0};int sub=0,end=0;};
''')

add('P2536','通配符的滚动动态规划',
    '令 dp[j] 表示模式当前前缀能否匹配 DNA 前 j 个字符。普通字符或 ? 从上一行 j−1 转移，* 则可不匹配字符，或在本行继续吞掉一个字符。',
    '模式中的星号可以匹配任意长度，不能把它当成恰好一个字符。使用逐个模式字符的动态规划可以完整覆盖所有选择。\n\n处理普通字符 c 时，新的 dp[j] 仅能从旧 dp[j−1] 转移，并要求 DNA 第 j 个字符等于 c；问号省略字符相等条件。处理星号时，新的 dp[j] 有两种来源：旧 dp[j] 表示星号匹配空串，新的 dp[j−1] 表示它再匹配一个 DNA 字符。后一项属于本行，必须从左向右计算。\n\n初始空模式只匹配空串。每个 DNA 单独计算，最终 dp[长度] 为假才是非病毒，计入答案。用两行 char 数组滚动，避免为每个片段开完整二维表。',
    '时间 O(N·模式长度·DNA长度)，空间 O(DNA长度)。','* 可匹配零个字符；星号行从左往右；输出不匹配的数量。',r'''
string pattern;int n;cin>>pattern>>n;int ans=0;while(n--){string s;cin>>s;vector<char>dp(s.size()+1),next(s.size()+1);dp[0]=1;for(char c:pattern){fill(next.begin(),next.end(),0);if(c=='*'){next[0]=dp[0];for(int j=1;j<=(int)s.size();j++)next[j]=dp[j]||next[j-1];}else for(int j=1;j<=(int)s.size();j++)next[j]=dp[j-1]&&(c=='?'||c==s[j-1]);dp.swap(next);}ans+=!dp.back();}cout<<ans<<'\n';
''')

add('P4407','枚举一次编辑并用集合去重',
    '若查询词已在字典中，输出 -1。否则枚举删除一个字符、替换一个字符、插入一个字符产生的所有字符串，用字典查找，并把命中的单词去重计数。',
    '编辑距离为一意味着恰好进行一次删除、插入或替换，反过来这三类操作产生的每个不同字典词与查询的距离都为一。因为查询词本身不在字典中，不会混入距离为零的情况。\n\n长度至多二十，删除只有 L 种，替换至多 25L 种，插入至多 26(L+1) 种，数量很小。直接构造每个候选，查询 unordered_set 保存的完整字符串；该容器仍会在哈希冲突时比较实际内容，不会把冲突当相等。\n\n相同候选可能由多个编辑位置产生，例如在重复字母串中删除任意一个相同字母，因此另用集合保存命中字典词，最后取集合大小，不能直接数命中次数。',
    '平均时间 O(M·26L²+NL)，空间 O(NL+26L²)。','先判断完全相等；命中单词要去重；插入位置包含末尾。',r'''
int n,m;cin>>n>>m;unordered_set<string>dict;while(n--){string s;cin>>s;dict.insert(s);}while(m--){string s;cin>>s;if(dict.count(s)){cout<<-1<<'\n';continue;}unordered_set<string>found;auto test=[&](const string &v){if(dict.count(v))found.insert(v);};for(int i=0;i<(int)s.size();i++){test(s.substr(0,i)+s.substr(i+1));string v=s;for(char c='a';c<='z';c++){v[i]=c;test(v);}}for(int i=0;i<=(int)s.size();i++)for(char c='a';c<='z';c++)test(s.substr(0,i)+c+s.substr(i));cout<<found.size()<<'\n';}
''')

add('P4398','枚举相对位移并做公共正方形 DP',
    '固定第二张图相对第一张图的平移后，每对对齐格子的相等关系固定。对重叠区域求全为相等格的最大正方形，枚举所有平移取最大值。',
    '两个公共子矩阵一旦选定左上角，它们对应格子的横纵坐标差就是固定平移。因此枚举所有从 −n+1 到 n−1 的横纵位移，就覆盖了全部公共子矩阵的对齐方式。\n\n固定平移后，把对应值相等的格子视作一，不等或超出另一图范围的视作零。令 dp[i][j] 为以当前格为右下角的最大全一正方形边长。当前格为零时值为零；为一时，必须同时拥有上方、左方、左上方三个可扩展正方形，所以取三者最小值加一。\n\n这个判定逐格比较原整数，完全避免二维哈希的碰撞。n 至多五十，O(n⁴) 的直接计算可以接受。每个平移都清空 DP，不能让上一种对齐的信息混入。',
    '时间 O(n⁴)，空间 O(n²)。','只允许平移，不旋转；越界格当不相等；DP 取三个方向最小值。',r'''
int n;cin>>n;vector<vector<int>>a(n,vector<int>(n)),b=a;for(auto &row:a)for(int &x:row)cin>>x;for(auto &row:b)for(int &x:row)cin>>x;int ans=0;for(int dx=1-n;dx<n;dx++)for(int dy=1-n;dy<n;dy++){vector<vector<int>>dp(n+1,vector<int>(n+1));for(int i=0;i<n;i++)for(int j=0;j<n;j++){int x=i+dx,y=j+dy;if(x>=0&&x<n&&y>=0&&y<n&&a[i][j]==b[x][y]){dp[i+1][j+1]=1+min({dp[i][j+1],dp[i+1][j],dp[i][j]});ans=max(ans,dp[i+1][j+1]);}}}cout<<ans<<'\n';
''')

add('AT_arc172_c','比较相邻插入位置的唯一变化',
    '把第一张选票依次向后移动，与相邻选票交换。两种开票顺序只会在交换中间的那一次公布结果上不同。累计真正改变结果的相邻交换次数，再加一。',
    '第一位投票者之外的顺序固定，所以全部可能顺序只由第一张票插入在什么位置决定。从最前插入开始，逐次把它与下一张票交换，就枚举了所有 n 种顺序。\n\n比较相邻两种顺序：交换前后，在这两张票之前的票数完全相同，在两张都开出后也完全相同。只有开出其中第一张时，公布的领先或平局结果可能不同。用 A=+1、B=−1，设此前差为 d，比较 sign(d+第一票) 与 sign(d+当前票)。不同就产生一个新结果序列。\n\n每次交换改变的是一个此前从未改动过的公布位置，之后也不会再改变它。因此一旦产生新序列，就不可能与更早的序列重复。答案正好是一加上发生变化的交换数，无须保存或哈希全部长度 n 的序列。',
    '时间 O(n)，空间 O(n)。','统计公布结果的不同序列，不是开票顺序；差值需在比较后再加入当前票。',r'''
int n;string s;cin>>n>>s;auto sign=[](int x){return (x>0)-(x<0);};int first=s[0]=='A'?1:-1,difference=0,ans=1;for(int i=1;i<n;i++){int v=s[i]=='A'?1:-1;if(sign(difference+first)!=sign(difference+v))ans++;difference+=v;}cout<<ans<<'\n';
''')
