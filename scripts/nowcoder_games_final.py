"""Finite search, SG reductions, misere play and rerooted staircase Nim."""
from nowcoder_editorials import CONTENT,add,add_python,read
from nowcoder_euler_support import EULER


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(236125,2000,['极小极大搜索','Alpha-Beta剪枝'],'4×4棋盘交替选择2×2加总分再旋转，最多6步，求最优总分。',
        '只有9个可选2×2区域，深度2k≤6，直接极小极大搜索。Alice层取最大、Bob层取最小；每步先记四格和，再逆时针旋转，递归返回剩余最优分后加本步和。退出分支时恢复四格。\n\n用Alpha-Beta界剪掉不可能影响祖先决策的分支。因递归值是“此后额外得分”，传入子节点的上下界都减去当前gain。Alice优先尝试高gain、Bob优先低gain，只改变搜索顺序，不改变结果。',
        r'''int tests;cin >> tests;while(tests--){int k;cin >> k;array<int,16> board;for(int &x:board)cin >> x;auto search=[&](auto &&self,int remaining,bool maximize,int alpha,int beta)->int{if(!remaining)return 0;vector<pair<int,int>> moves;for(int r=0;r<3;r++)for(int c=0;c<3;c++){int p=r*4+c;int gain=board[p]+board[p+1]+board[p+4]+board[p+5];moves.push_back({gain,p});}sort(moves.begin(),moves.end());if(maximize)reverse(moves.begin(),moves.end());int best=maximize?INT_MIN:INT_MAX;for(auto [gain,p]:moves){array<int,4> old={board[p],board[p+1],board[p+5],board[p+4]};board[p]=old[1];board[p+1]=old[2];board[p+5]=old[3];board[p+4]=old[0];int value=gain+self(self,remaining-1,!maximize,alpha-gain,beta-gain);board[p]=old[0];board[p+1]=old[1];board[p+5]=old[2];board[p+4]=old[3];if(maximize){best=max(best,value);alpha=max(alpha,best);}else{best=min(best,value);beta=min(beta,best);}if(alpha>=beta)break;}return best;};cout << search(search,2*k,true,-1000000000,1000000000) << '\n';}''',
        '双方每步都向同一个总分加分，Bob也不是减去本步得分。旋转是逆时针，恢复棋盘必须与旋转前完全一致。',
        complexity=r'最坏 $O(9^{2k})$，排序9种动作视常数；递归空间 $O(k)$。')
    put(236126,2100,['胜负DP','状态编码'],'数字可减小，遇0可删该位及右侧，判断先手。',
        '最长6位，总共10+100+...+10^6种非空字符串，可全部预处理。按长度升序、同长按数值升序，每次操作都到更短或同长更小的状态，形成拓扑顺序。状态为固定长度下的数值，因此前导0不能丢失；用offset[len]+value编码。\n\n若某位d>0，枚举降到0..d−1；若d=0，删除它和右侧，只留下左前缀。只要存在必败后继则当前必胜。空串为必败，因为上一手删空者已获胜。',
        r'''int tests;cin >> tests;vector<string> query(tests);int maximum=1;for(auto &s:query){cin >> s;maximum=max(maximum,(int)s.size());}int power[7],offset[7];power[0]=1;offset[0]=0;for(int i=1;i<=6;i++){power[i]=power[i-1]*10;offset[i]=offset[i-1]+(i==1?1:power[i-1]);}vector<uint8_t> win(offset[maximum]+power[maximum]);for(int len=1;len<=maximum;len++)for(int value=0;value<power[len];value++){int id=offset[len]+value;for(int position=0;position<len && !win[id];position++){int digit=value/power[position]%10;if(!digit){int prefixLength=len-position-1,prefix=value/power[position+1];if(!win[offset[prefixLength]+prefix])win[id]=1;}else for(int smaller=0;smaller<digit;smaller++)if(!win[id-(digit-smaller)*power[position]]){win[id]=1;break;}}}for(auto &s:query){int value=stoi(s);cout << (win[offset[s.size()]+value]?"Yes\n":"No\n");}''',
        '字符串00与0是不同局面，必须保存长度。删除0包括该0本身，不只是右侧。',
        complexity=r'最多S=1111110种非空状态，时间 $O(S\cdot6\cdot10+T)$，空间 $O(S+6T)$。')
    put(236137,2100,['博弈分类','回文结构'],'翻0付1，非回文且前步非反转时可免费反转，费用少者胜。',
        '统计总0数z和不相等的对称对数d。若d=0，免费反转暂不能用：z=1时先手必须承担最后一次修改而输；z为偶数时后手用镜像回应也赢；z为奇数且>1时先手先改中心，再利用后手打破对称后的免费反转取得优势。z=0时双方费用都是0，平局。\n\n若d>0，先手可先免费反转，把必须付费的责任交给后手。除一种边界外先手胜：恰有一个不对称对、总共两个0、中心也是0时，双方可以各付1，结果平局。此时一个0来自不对称对，另一个来自中心；其他非回文状态先手均可保持免费操作优势。',
        r'''int tests;cin >> tests;while(tests--){int n;string s;cin >> n >> s;int zeros=count(s.begin(),s.end(),'0'),different=0;for(int i=0;i<n/2;i++)different+=s[i]!=s[n-1-i];if(!zeros)cout << "DRAW\n";else if(!different)cout << ((zeros>1 && zeros%2)?"ALICE\n":"BOB\n");else if(different==1 && zeros==2 && n%2 && s[n/2]=='0')cout << "DRAW\n";else cout << "ALICE\n";}''',
        '非回文时也不能连续两步反转，这正是费用策略成立的条件。全1串无需操作，应平局。',
        complexity=r'每组时间 $O(n)$，空间 $O(n)$ 存串。')
    if 'nowcoder-global::236139' not in existing:
        add_python(236139,1700,['日期DP','博弈'],'可跳下一天或下月同日，先到2001年11月4日者赢。',
            '所有合法操作使日期严格增大，因此从目标日期向前倒推。目标日期作为无后继必败态；每个更早日期，若下一天或存在的下月同日是必败态，则它必胜，否则必败。超过目标的操作会立即输，不作为获胜选择。用datetime构造日期，自动检查月份天数与闰年。',
            '''import sys
from datetime import date, timedelta

first = date(1900, 1, 1)
target = date(2001, 11, 4)
win = {target: False}
one_day = timedelta(days=1)
current = target - one_day
while current >= first:
    good = not win[current + one_day]
    year = current.year + (current.month == 12)
    month = current.month % 12 + 1
    try:
        following = date(year, month, current.day)
        if following <= target and not win[following]:
            good = True
    except ValueError:
        pass
    win[current] = good
    current -= one_day
values = list(map(int, sys.stdin.buffer.read().split()))
answers = []
for i in range(values[0]):
    year, month, day = values[1 + 3 * i:4 + 3 * i]
    answers.append('YES' if win[date(year, month, day)] else 'NO')
print('\\n'.join(answers))
''',
            '下月同日不存在时不能选该操作，例如1月31不能跳2月31。初始已在目标日时没有获胜移动，输出NO。',
            complexity=r'日期总数D约四万，预处理 $O(D)$，每问 $O(1)$，空间 $O(D+T)$。')
    put(236141,1000,['巴什博弈'],'每次取1到K，取完赢，多组判断A/B。',
        'N是K+1倍数时必败，否则取余数使对手面对倍数。之后对手取x，就补K+1−x，始终能把倍数交回给对手。',
        r'''int tests;cin >> tests;while(tests--){long long n,k;cin >> n >> k;cout << (n%(k+1)?"A\n":"B\n");}''',
        'K可以大于N，此时先手直接取完。K+1与取模使用64位。',
        complexity=r'每组时间、空间均 $O(1)$。')
    put(15066,2200,['对称局面','排序','博弈'],'从一堆取正数后可把其余部分分给其他非空堆，判断胜负。',
        '将非空堆排序。必败态恰是每种堆大小出现偶数次，也就是排序后两两相等。\n\n这类局面不能一步到另一类必败态：若选中堆从a降到b，任意阈值t∈(b,a]上，达到t的堆数少1。要恢复所有阈值的偶数性，其他堆至少共增加a−b颗；但本步还取走了正数，可分配总数严格小于a−b，矛盾。\n\n反过来，奇数堆时，选最大堆，把其余排序后每一对较小堆补到较大堆，所需总补数小于最大堆，取走余下正数并清空该堆，就到必败态。偶数堆且不两两相等时，仍选最大堆，将它降到最小堆大小，补齐中间相邻配对；能取走的数正好是原排序每对差之和，严格为正。故所有其他局面都能一步到必败态。',
        r'''int n;while(cin >> n && n){vector<int> a;for(int i=0;i<n;i++){int x;cin >> x;if(x)a.push_back(x);}sort(a.begin(),a.end());bool lose=a.size()%2==0;for(int i=0;i+1<(int)a.size();i+=2)if(a[i]!=a[i+1])lose=false;cout << (lose?"Lose\n":"Win\n");}''',
        '不能按普通Nim异或判断，取后转移石子会改变其必败集合。空堆不能接收新石子，因此先忽略已有空堆。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    put(236144,1800,['博弈分类','质因数'],'整数减去非1非自身约数，无法操作者输。',
        '奇数n的合法约数也是奇数，减后为带奇因子>1的偶数；后者总能减去其奇因子，走回奇数。因此所有奇数均必败，所有含奇因子的偶数必胜。\n\n剩下n=2^r。减去2^s，若s≤r−2，结果含奇因子>1，属于必胜态；只有减半能走到另一纯2幂2^(r−1)。n=2无合法约数必败，所以r奇数必败、r偶数必胜。',
        r'''int tests;cin >> tests;while(tests--){unsigned n;cin >> n;bool alice=false;if(n%2==0){if((n&(n-1))!=0)alice=true;else alice=__builtin_ctz(n)%2==0;}cout << (alice?"Alice\n":"Bob\n");}''',
        '1和素数都无合法操作。纯2幂需要看指数奇偶，不能一概判偶数胜。',
        complexity=r'每组时间、空间均 $O(1)$。')
    put(14619,1500,['Nim博弈'],'第一步必须从第k堆取，是否存在必胜取法。',
        '总异或X非0时，获胜首步必须把总异或变0。若改第k堆a，则新值唯一为a xor X；它必须严格小于a，才可通过取走正数实现。只检查这个不等式，不是问整个局面是否先手胜。',
        r'''int tests;cin >> tests;while(tests--){int n,k;cin >> n >> k;int total=0,chosen=0;for(int i=1;i<=n;i++){int a;cin >> a;total^=a;if(i==k)chosen=a;}cout << ((chosen^total)<chosen?"Yes\n":"No\n");}''',
        'X=0时新值等于原值，不允许不取，所以输出No。',
        complexity=r'每组时间 $O(n)$，空间 $O(1)$。')
    put(236145,1900,['Northcott博弈','Nim和'],'每行黑白棋子可移动不可越过，黑方先走。',
        '把每行两棋子之间的空格数g=abs(T−J)−1看作Nim堆。朝对方移动会减小g，恰是取石子。背离对方移动虽会增大g，但对方可沿同方向跟进同样格数，恢复原间隔；这种无效退让只能有限进行，无法破坏Nim必胜策略。因此全部间隔异或非0先手胜。',
        r'''int n,m;while(cin >> n >> m){int total=0;for(int i=0;i<n;i++){int a,b;cin >> a >> b;total^=abs(a-b)-1;}cout << (total?"I WIN!\n":"BAD LUCK!\n");}''',
        '看的是两子之间空格数，距离要减1。题目允许棋子左右顺序任意，取绝对值。',
        complexity=r'每组时间 $O(n)$，空间 $O(1)$。')
    put(236153,1900,['阶梯Nim','Silver Dollar博弈'],'棋子只能向左、不越子，判断胜负。',
        '排序后从右向左两两配对，每对之间的空格数视为一堆Nim；若棋子数奇数，最左棋子与左边界0配成一对。每对右棋子左移可任意减少这一堆。每对左棋子左移会增大配对间隔，对方可让对应右棋子同移，恢复间隔；标准配对策略给出这些间隔异或为0恰为必败态。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;vector<int> a(n);for(int &x:a)cin >> x;sort(a.begin(),a.end());if(n%2)a.insert(a.begin(),0);int total=0;for(int i=1;i<(int)a.size();i+=2)total^=a[i]-a[i-1]-1;cout << (total?"Georgia will win\n":"Bob will win\n");}''',
        '配对从右端确定，奇数个时补0在最左，不能漏掉最左棋子到边界的间隔。',
        complexity=r'每组时间 $O(n\log n)$，空间 $O(n)$。')
    put(236917,1700,['SG函数','DAG博弈'],'DAG上若干棋子独立移动，判断先手。',
        '单棋子在u的SG值为所有后继SG的mex，终点为0。题目保证边指向更大编号，按编号倒序计算即可。多个棋子是独立游戏和，SG异或非0时先手赢。重复棋子也逐个异或，相同状态两枚会抵消。',
        r'''int n;cin >> n;vector<vector<int>> edge(n);for(auto &row:edge){int k;cin >> k;row.resize(k);for(int &v:row)cin >> v;}vector<int> sg(n);for(int u=n-1;u>=0;u--){vector<bool> seen(edge[u].size()+1);for(int v:edge[u])if(sg[v]<(int)seen.size())seen[sg[v]]=true;while(sg[u]<(int)seen.size() && seen[sg[u]])sg[u]++;}int m;while(cin >> m && m){int total=0;while(m--){int u;cin >> u;total^=sg[u];}cout << (total?"WIN\n":"LOSE\n");}''',
        '输出说明一处误写LOST，样例与来源使用LOSE，代码采用LOSE。mex只需标记到出度，因为mex不会超过可达状态数。',
        complexity=r'预处理 $O(n+E)$，每问 $O(m)$，空间 $O(n+E)$。')
    put(236918,1700,['SG函数','减法游戏'],'允许减集合S中数的多堆游戏，输出每问胜负字母。',
        '预处理0..10000的SG：sg[h]=mex{sg[h−s]，s∈S且s≤h}。用时间戳数组标记本轮后继，避免每个h清大数组。询问把各堆SG异或，非0输出W，否则L，所有询问连成一串。',
        r'''int k;cin >> k;vector<int> move(k);for(int &x:move)cin >> x;sort(move.begin(),move.end());const int limit=10000;vector<int> sg(limit+1),seen(k+2,-1);for(int h=1;h<=limit;h++){for(int s:move){if(s>h)break;if(sg[h-s]<(int)seen.size())seen[sg[h-s]]=h;}while(seen[sg[h]]==h)sg[h]++;}int m;cin >> m;string answer;while(m--){int count;cin >> count;int total=0;while(count--){int h;cin >> h;total^=sg[h];}answer.push_back(total?'W':'L');}cout << answer;''',
        '空堆SG为0；不能只预处理单堆胜负，因为多堆组合需要完整SG值。',
        complexity=r'时间 $O(10000k+\sum l)$，空间 $O(10000+k)$。')
    put(236919,2200,['SG函数','阈值递归'],'每箱一次可添1到当前石子平方个，不超容量，多箱组合。',
        '单箱容量s、当前c。若c=0，无论剩余容量多少都不能放，SG=0。若c²≥s−c，一步可到任意更大c，故SG=s−c。\n\n否则令t为满足t(t+1)≥s的最小整数。所有c≥t都属于上一种情形。对c<t，跨入高区的后继SG最小为s−(c+c²)，而s≥t²−t+1，所以它≥(t−1−c)(t+c)+1>t−1−c。这些高SG不会影响只看低区时的mex（低区后继总数不超过t−1−c），因此可把容量缩为t−1，SG不变。反复平方根缩小后进入直接求值情形，最后各箱SG异或。',
        r'''int n;cin >> n;auto grundy=[](long long s,long long c){if(!c)return 0LL;while(c*c<s-c){long long t=sqrtl(s);while(t*(t+1)<s)t++;while(t>0 && (t-1)*t>=s)t--;s=t-1;}return s-c;};long long total=0;while(n--){long long s,c;cin >> s >> c;total^=grundy(s,c);}cout << (total?"Yes":"No");''',
        'c=0时不能添加，必须单独返回0。缩减的是容量s，当前c保持不变。',
        complexity=r'每箱 $O(\log\log s)$ 轮整数阈值计算，空间 $O(1)$。')
    put(237115,2300,['阶梯Nim','换根DP','距离余数'],'每次向k级祖先移动任意多石子，对全部树根判胜负。',
        '固定根时，把深度按长度k分块。仅奇数块（floor(depth/k)为奇数）的石子堆参与Nim异或：每次上移k层恰在奇偶块之间转移，0异或局面任何移动都会改变一个被计入堆；非0时可从某奇块堆减到令异或为0的大小，再把取出的石子移入偶块，因此判定成立。\n\n只需知道距离模2k，令down[u][r]为u子树中距离u模2k等于r的a异或。后序将儿子余数整体+1合并。换根到儿子v时，先从u的全树余数表中异或去v子树贡献，再把其余部分距离+1并入v。每个根取余数k..2k−1的异或。',
        r'''int n,k;cin >> n >> k;EulerTree tree(n);for(int i=1;i<n;i++){int u,v;cin >> u >> v;tree.add(u,v);}int period=2*k;vector<vector<int>> dp(n+1,vector<int>(period));for(int u=1;u<=n;u++)cin >> dp[u][0];tree.root(1);for(int i=n-1;i>0;i--){int u=tree.order[i],p=tree.parent[u];for(int r=0;r<period;r++)dp[p][(r+1)%period]^=dp[u][r];}vector<int> answer(n+1);for(int u:tree.order){int value=0;for(int r=k;r<period;r++)value^=dp[u][r];answer[u]=value!=0;for(int v:tree.edge[u])if(tree.parent[v]==u){auto old=dp[v];for(int r=0;r<period;r++)dp[v][r]=old[r]^dp[u][(r-1+period)%period]^old[(r-2+period)%period];}}for(int u=1;u<=n;u++)cout << answer[u] << (u==n?'\n':' ');''',
        '参与的是距离模2k落在后半段，不是距离模k。换根计算需保存儿子旧子树表，不能边覆盖边读取。',
        declarations=EULER,complexity=r'时间、空间均 $O(nk)$。')
    put(237117,2200,['SG函数','状态压缩','连通分解'],'多个有禁格棋盘放2×2，最后不能放者输。',
        '把每个初始可放的2×2位置视为一种动作，两个动作若共享格子就冲突。状态mask表示仍可选动作，选择i后删除其自身及全部冲突邻居，SG取所有后继SG的mex。R*C<50且可用格≤40，动作数量可用64位保存。\n\n若剩余动作冲突图分成连通分量，不同分量独立，SG是各分量SG异或。每次先按位BFS拆分，再对连通状态记忆化搜索，减少长条棋盘和分裂局面的重复枚举。不同棋盘再作SG异或。',
        r'''int boards;cin >> boards;int total=0;while(boards--){int rows,cols;cin >> rows >> cols;vector<string> grid(rows);for(auto &s:grid)cin >> s;vector<unsigned long long> cells;for(int r=0;r+1<rows;r++)for(int c=0;c+1<cols;c++)if(grid[r][c]=='0' && grid[r+1][c]=='0' && grid[r][c+1]=='0' && grid[r+1][c+1]=='0')cells.push_back((1ULL<<(r*cols+c))|(1ULL<<(r*cols+c+1))|(1ULL<<((r+1)*cols+c))|(1ULL<<((r+1)*cols+c+1)));int moves=cells.size();vector<unsigned long long> conflict(moves);for(int i=0;i<moves;i++)for(int j=0;j<moves;j++)if(cells[i]&cells[j])conflict[i]|=1ULL<<j;unordered_map<unsigned long long,int> memo;memo[0]=0;auto grundy=[&](auto &&self,unsigned long long mask)->int{auto found=memo.find(mask);if(found!=memo.end())return found->second;unsigned long long component=0,frontier=mask&-mask;while(frontier){component|=frontier;unsigned long long next=0;for(auto bits=frontier;bits;bits&=bits-1)next|=conflict[__builtin_ctzll(bits)];frontier=next&mask&~component;}if(component!=mask)return memo[mask]=self(self,component)^self(self,mask^component);unsigned long long seen=0;for(auto bits=mask;bits;bits&=bits-1){int i=__builtin_ctzll(bits);seen|=1ULL<<self(self,mask&~conflict[i]);}int value=__builtin_ctzll(~seen);return memo[mask]=value;};total^=grundy(grundy,moves?(1ULL<<moves)-1:0);}cout << (total?"Yes":"No");''',
        '压缩的是可放动作，状态转移必须删除所有重叠动作。空棋盘SG=0。精确记忆化最坏仍指数。',
        complexity=r'设初始动作数M（本范围小于64）、访问状态数Z，最坏 $O(ZM²)$，空间 $O(Z+M)$；连通分解通常显著减少Z。')
    put(237119,1900,['反常Nim','SG函数'],'每次删某堆连续苹果，可从中间分裂，取最后者输。',
        '长度a的一堆删连续段后剩两段b、c，b+c<a，故b xor c≤b+c<a；而只从一端删可达到0..a−1的任意值。因此普通规则单堆SG=a，新增分裂动作不会引入SG≥a的后继。\n\n反常规则仍按反常Nim判定：若全为1，堆数偶数先手胜；否则总异或非0先手胜。证明必败大堆局面异或0时，分裂一堆将其SG从a改成严格更小的b xor c，不能保持异或0；又不可能一步进入错误的全1终局。其他局面用普通Nim的一端取法就能走到反常Nim必败态。',
        r'''int n;cin >> n;int total=0;bool allOne=true;for(int i=0;i<n;i++){int a;cin >> a;total^=a;allOne=allOne && a==1;}cout << ((allOne?n%2==0:total!=0)?"Yes":"No");''',
        '最后取者输，全1时与普通Nim结论相反。允许中间删不等于能把任意两堆合并。',
        complexity=r'时间 $O(n)$，空间 $O(1)$。')
    put(20055,2100,['SG函数','分裂游戏'],'从瓶i取一豆，在更后j、k各加一豆，统计获胜首步。',
        '把每颗豆视为独立游戏子项，位于瓶i的豆可变成位于j、k的两个子项，因此sg[i]=mex{sg[j] xor sg[k]，i<j≤k}。从最后瓶向前计算。瓶i有p颗相同豆时，偶数份SG抵消，只在p为奇数时异或sg[i]。\n\n枚举每个有豆的i及j、k，操作后的总异或为X xor sg[i] xor sg[j] xor sg[k]；为0就是获胜首步。按i、j、k升序枚举自然得到字典序首解，并统计全部三元组。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;vector<int> count(n),sg(n);for(int &x:count)cin >> x;for(int i=n-1;i>=0;i--){set<int> reachable;for(int j=i+1;j<n;j++)for(int k=j;k<n;k++)reachable.insert(sg[j]^sg[k]);while(reachable.count(sg[i]))sg[i]++;}int total=0;for(int i=0;i<n;i++)if(count[i]%2)total^=sg[i];array<int,3> first={-1,-1,-1};int ways=0;for(int i=0;i<n;i++)if(count[i])for(int j=i+1;j<n;j++)for(int k=j;k<n;k++)if((total^sg[i]^sg[j]^sg[k])==0){if(!ways)first={i,j,k};ways++;}cout << first[0] << ' ' << first[1] << ' ' << first[2] << '\n' << ways << '\n';}''',
        '同瓶豆不可区分，首步按三元组计数，不乘p[i]。j=k合法，会给同一瓶加两豆，SG异或抵消。',
        complexity=r'每组 $O(n³\log n)$，空间 $O(n²)$ 临时mex集合。')
    put(237141,2100,['树上SG','删边博弈'],'剪去一边并丢掉不连根部分，多组判断胜者。',
        '根的各儿子分支互相独立，按Sprague–Grundy定理异或。一个分支是“父边接一棵子树”，绿树删边博弈的加根边规则使其SG为子树SG+1：剪掉父边可到0，其余动作对应子树内部删边，mex归纳得到加1。于是sg[u]=xor(sg[v]+1)，叶子为0，根SG非0则Alice胜。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;EulerTree tree(n);for(int i=1;i<n;i++){int u,v;cin >> u >> v;tree.add(u,v);}tree.root(1);vector<int> sg(n+1);for(int i=n-1;i>0;i--){int u=tree.order[i];sg[tree.parent[u]]^=sg[u]+1;}cout << (sg[1]?"Alice\n":"Bob\n");}''',
        '独立分支先加1再异或，不能先把儿子SG异或后统一加1。没有边的单根树先手输。',
        declarations=EULER,complexity=r'每组时间、空间均 $O(n)$。')


if __name__=='__main__':run()
