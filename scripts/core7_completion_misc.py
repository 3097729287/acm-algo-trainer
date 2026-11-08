from core7_completion import add, FENWICK

add('P12397','枚举原数的数位和',
    '原数 x 不超过 m，它的数位和最多 171。固定数位和 s 后，后续反复求和的贡献完全确定，故 x=m−贡献。枚举 s，检查推得的 x 是否正且数位和确实为 s。',
    '函数 f_k(x) 的首项就是 x，其余项只依赖 x 的数位和 s。虽然 x 范围很大，s 的范围很小：不超过十九位十进制数的数位和上界 171。\n\n对每个候选 s，预处理 H_k(s)=s+s(s)+…，共 k 项。每次取数位和很快变成一位数；之后这个值不再变化，可以直接乘上剩余项数，不必循环到十亿。\n\n每次询问 m 时，固定 s 就只有一个可能原数 x=m−H_k(s)。若 x>0 且真实数位和等于 s，就得到一个解。不同 s 不会重复同一个 x。k=0 时 f_0(x)=x，答案恒为一。',
    '预处理 O(171 log 171)，每次询问 O(171 log m)，空间 O(171)。','一位数后批量计算剩余项；x 必须为正；k=0 单独处理。',r'''
int tests;long long k;cin>>tests>>k;auto digitSum=[](long long x){int s=0;for(;x;x/=10)s+=x%10;return s;};vector<long long>contribution(172);for(int s=1;s<=171;s++){long long value=s,left=k,total=0;while(left&&value>=10){total+=value;value=digitSum(value);left--;}contribution[s]=total+value*left;}while(tests--){long long m;cin>>m;if(!k){cout<<1<<'\n';continue;}int answer=0;for(int s=1;s<=171;s++)if(m>contribution[s]){long long x=m-contribution[s];if(digitSum(x)==s)answer++;}cout<<answer<<'\n';}
''')

add('P10026','把所有减一的影响看作二的幂',
    '若做 d 次翻倍，最终 n=2^d−D，D 是 k−d 个二次幂之和。对 n>0，D 的最少项数为 d−popcount(n−1)，最多为 D；选满足最少项数限制的最大 d，再判断最多项数是否足够。',
    '一次减一之后若还有 j 次翻倍，它对最终值的减少量就是 2^j。因此固定翻倍次数 d 后，剩下 s=k−d 次减一，要把 D=2^d−n 表示成恰好 s 个二次幂。\n\n非负整数 D 的最少二次幂项数为 popcount(D)，最多为 D；把一个大于一的幂拆成两个较小幂，会让项数恰增加一，所以这两个界之间的所有项数都能实现。\n\n对 n>0 且 2^d>=n，D 的 d 位二进制恰为 n−1 的按位补，故 popcount(D)=d−popcount(n−1)。条件变为 d<=k、2d<=k+popcount(n−1)，以及 k−d<=2^d−n。前两者给出 d 上界，最后一式随着 d 增大只会更容易满足，因此取最大允许 d 即可判断。\n\nd>=61 时，2^d 已大于 n+k 的最大可能和，可直接判为满足而不真的移位。n=0 时先从一减到零，之后任意次翻倍仍为零，所以恰好任意正次数都可行。',
    '每组时间 O(1)，空间 O(1)。','次数必须恰好；n=0 另处理；大指数先判断，不能执行超范围移位。',r'''
int tests;cin>>tests;while(tests--){unsigned long long k,n;cin>>k>>n;bool ok;if(n==0)ok=k>=1;else{unsigned long long ones=__builtin_popcountll(n-1),d=min(k,(k+ones)/2);if(d>=61)ok=true;else{unsigned long long value=1ULL<<d;ok=value>=n&&value-n>=k-d;}}cout<<(ok?"Yes":"No")<<'\n';}
''')

add('P3929','一次修改只能修复相邻两条比较',
    '分别尝试两种波动方向，记录不满足的相邻比较。若有错误，唯一修改位置必须是第一条错误边的某个端点；检查所有错误是否都与它相邻即可。',
    '固定“低高低高”或“高低高低”后，每对相邻元素的大小方向确定。修改一个位置 p，只会影响 p−1 与 p、p 与 p+1 这两条比较，其它错误无法修复。\n\n找到第一条错误边 (i,i+1)，候选修改点只有 i 或 i+1。对每个候选，若所有错误边都包含这个点，则其余比较原本正确。候选点在该方向中要么是局部峰，要么是局部谷，因此只需把它改得至少和两邻居一样大，或至多一样小，就能同时修复两侧。\n\n因为允许弱不等号，不存在两侧要求互相冲突的情况。没有错误时不用修改；两种方向任意一种可行就输出 Yes。输入包含多组，读至 EOF。',
    '每组时间 O(n)，空间 O(n)。','两种方向都尝试；允许相等；一次修改只能涉及两条相邻边。',r'''
int n;while(cin>>n){vector<long long>a(n);for(auto &x:a)cin>>x;auto ok=[&](bool firstUp){vector<int>bad;for(int i=0;i+1<n;i++){bool up=((i%2)==0)==firstUp;if(up?a[i]>a[i+1]:a[i]<a[i+1])bad.push_back(i);}if(bad.empty())return true;for(int p:{bad[0],bad[0]+1}){bool valid=true;for(int edge:bad)if(edge!=p-1&&edge!=p)valid=false;if(valid)return true;}return false;};cout<<(ok(true)||ok(false)?"Yes":"No")<<'\n';}
''')

add('P10854','把相邻变化边界移到最近的端点',
    '令 d_i=a_i xor a_(i+1)。合法内部翻转恰好交换相邻的 01 与 10；端点翻转则删除边界。把左半边界依次移到左端、右半边界逆序移到右端，总操作数不超过 floor(n²/4)≤10^6。',
    '全串相同等价于所有相邻差异 d_i 都为零。翻转内部位置 p 会同时翻转 d_(p−1)、d_p，而允许操作的条件 a_(p−1)!=a_(p+1) 正好表示这两个差异位一个零、一个一。于是操作只是在差异数组中交换相邻 01 或 10，让一个边界移动一步。\n\n翻转位置一可以消除最左边界 d_1，翻转位置 n 可以消除最右边界 d_(n−1)。原边界在位置 i 时，移到左端并删除需 i 次，移到右端需 n−i 次。\n\n把 i<=n/2 的边界按 i 递增处理，依次翻转位置 i,i−1,…,1，先前边界已消除，不会挡路；把右半边界按 i 递减处理，依次翻转 i+1,…,n。两侧处理范围不冲突，每一步都满足合法条件。\n\n总次数为 Σ(边界位置i)min(i,n−i)，最大不超过所有位置都出现边界时的 floor(n²/4)。n<=2000，所以不超过一百万，所有合法输入都有方案。',
    '时间和输出量 O(n²)，空间 O(n²)。','保存原始边界位置；左侧从左往右处理，右侧从右往左；输出实际字符位置。',r'''
int n,r;cin>>n>>r;vector<int>a(n);for(int &x:a)cin>>x;vector<int>boundary,operations;for(int i=1;i<n;i++)if(a[i-1]!=a[i])boundary.push_back(i);for(int i:boundary)if(i<=n/2)for(int p=i;p>=1;p--)operations.push_back(p);for(int j=(int)boundary.size()-1;j>=0;j--){int i=boundary[j];if(i>n/2)for(int p=i+1;p<=n;p++)operations.push_back(p);}cout<<operations.size()<<'\n';for(int p:operations)cout<<p<<' ';cout<<'\n';
''',checker='binary-flips')

add('P15267','先缩到四个元素，再穷举最后三次合并',
    '任意四元素集合都能最终合为零。因此先任意合并直到只剩四个，再穷举这四个的所有合并次序。初始不足四个也直接穷举，并按真实元素值输出每次选择。',
    '两个非零元素的 mex 为零，两个零的 mex 为一，一个零与一个非零的 mex 仍为非零。这些规则足以证明四元素总可成功：\n\n零数为零时，先合并两个非零得到零，再与第三个非零合成非零，最后两个非零合成零；零数为一时先合并两个非零，得到“两零一非零”；零数为二时先合并一零一非零，得到“一零两非零”；零数为三或四时先合并两零，也归入这两种三元素可行情形。三元素中，一零两非零或两零一非零都可先合成两个非零，再合成零。\n\n所以当元素数大于四时，任取两元素合并不会破坏最终可解性。剩至多四个时，最多只有六种首选、三种次选，直接枚举所有选择验证最终是否为零，不必硬编码小规模例外。\n\n先记录完整操作，只有找到成功结尾后才输出；无解时只输出 −1。输出的是数值而非下标，遇到相同数也必须确实有两个副本。',
    '时间 O(n)，空间 O(n)。','mex 只需检查 0、1、2；操作输出数值；成功时恰好 n−1 次；无解前不输出半成品。',r'''
int tests;cin>>tests;while(tests--){int n;cin>>n;deque<long long>values;for(int i=0;i<n;i++){long long x;cin>>x;values.push_back(x);}vector<pair<long long,long long>>operations;auto mex=[](long long a,long long b){for(int v=0;;v++)if(v!=a&&v!=b)return (long long)v;};while(values.size()>4){long long a=values.front();values.pop_front();long long b=values.front();values.pop_front();operations.push_back({a,b});values.push_back(mex(a,b));}vector<long long>small(values.begin(),values.end());function<bool(vector<long long>)>solve=[&](vector<long long>a){if(a.size()==1)return a[0]==0;for(int i=0;i<(int)a.size();i++)for(int j=i+1;j<(int)a.size();j++){vector<long long>next;for(int k=0;k<(int)a.size();k++)if(k!=i&&k!=j)next.push_back(a[k]);next.push_back(mex(a[i],a[j]));operations.push_back({a[i],a[j]});if(solve(next))return true;operations.pop_back();}return false;};if(!solve(small))cout<<-1<<'\n';else{for(auto [a,b]:operations)cout<<a<<' '<<b<<'\n';if(n==1)cout<<'\n';}}
''',checker='mex-merges')

add('P7023','分别考虑是否创造全新数值',
    '若不创造新值，只能消除存在其它原值倍数的种类，把这些种类按频数从小到大消除。若创造新值，为减少 r 种至少消除 r+1 个原种类，把全体最便宜的 r+1 种乘到共同倍数即可。比较两类代价。',
    '要让一种原值彻底消失，必须修改它全部出现位置，代价等于频数；只改一部分不会减少这种原值。\n\n第一类方案不出现任何新值。被消除的值必须能乘到某个保留的原值，因此它必有其它原值作为真倍数。反过来，所有这类非极大值都能沿整除关系最终乘到某个极大原值，极大值不被消除，故任取若干非极大种类消除都可行。要减少 r 种，代价为这些频数中最小 r 项之和。\n\n第二类方案出现至少一种新值。若净减少 r 种，就至少让 r+1 个原种类消失，修改次数不小于全部频数中最小 r+1 项之和。这个下界也能达到：把这些种类的每个位置都乘到它们的一个共同倍数，新值只算一种；若共同倍数恰是保留原值，只会更好。\n\n用倍数筛标记非极大值，分别排序两份频数并求前缀和。为每个减少量记录最少代价，再对操作预算做前缀最优，输出 0 到 n 次的答案。多余操作可以乘一，不改变结果。',
    '时间 O(A log A+n log n)，空间 O(A+n)。','一种值消失要修改全部副本；无新值时只消除非极大值；新值方案多消除一种。',r'''
int n;cin>>n;vector<int>a(n);int maximum=0;for(int &x:a){cin>>x;maximum=max(maximum,x);}vector<int>frequency(maximum+1);for(int x:a)frequency[x]++;vector<int>all,removable;for(int x=1;x<=maximum;x++)if(frequency[x]){all.push_back(frequency[x]);bool hasMultiple=false;for(int y=x+x;y<=maximum;y+=x)if(frequency[y]){hasMultiple=true;break;}if(hasMultiple)removable.push_back(frequency[x]);}sort(all.begin(),all.end());sort(removable.begin(),removable.end());vector<int>prefix(all.size()+1),cheap(removable.size()+1);for(int i=0;i<(int)all.size();i++)prefix[i+1]=prefix[i]+all[i];for(int i=0;i<(int)removable.size();i++)cheap[i+1]=cheap[i]+removable[i];int distinct=all.size();vector<int>answer(n+1,distinct);for(int reduction=1;reduction<distinct;reduction++){int cost=prefix[reduction+1];if(reduction<(int)cheap.size())cost=min(cost,cheap[reduction]);answer[cost]=min(answer[cost],distinct-reduction);}for(int k=1;k<=n;k++)answer[k]=min(answer[k],answer[k-1]);for(int k=0;k<=n;k++)cout<<answer[k]<<(k==n?'\n':' ');
''')

add('P11894','差分统计次数，跨二次幂分段跳跃',
    '每个位置最终只取决于被覆盖的次数。先用差分求次数，再利用 floor(log2 x) 在相邻二次幂之间恒定，整段跳过若干次相同增量。',
    '所有操作都独立地把一个数替换为同一个函数 f(x)，所以作用在某个位置上的先后顺序没有区别，只需知道总次数。区间覆盖次数通过差分数组在 O(n+m) 时间求出。\n\n对当前值 x>1，令 b=floor(log2 x)，在到达 2^(b+1) 前，每次都增加 b。距离下个分界还差 gap=2^(b+1)−x，需要 ceil(gap/b) 步才首次到达或越过分界。这些步的起始值仍在当前分段，增量都为 b，可以一次完成。\n\n跳过的步数还要与剩余次数取最小值。越过分界后重新计算 b，直到次数用完。x=1 时增量为零，永远不变。用整数最高位运算代替浮点 log，避免二次幂附近误差。',
    '时间 O(n log A+m)，空间 O(n)，A 为操作后的最大值。','x=1 不动；跳跃次数向上取整；更新后的最高位重新计算。',r'''
int n,m;cin>>n>>m;vector<long long>a(n+1);vector<int>difference(n+2);for(int i=1;i<=n;i++)cin>>a[i];while(m--){int l,r;cin>>l>>r;difference[l]++;difference[r+1]--;}int count=0;for(int i=1;i<=n;i++){count+=difference[i];long long left=count,x=a[i];while(left&&x>1){int b=63-__builtin_clzll(x);long long gap=(1LL<<(b+1))-x,steps=min(left,(gap+b-1)/b);x+=steps*b;left-=steps;}cout<<x<<(i==n?'\n':' ');}
''')

add('P12733','选最小难度，再逆序安排',
    '要做 k 题应选择难度最小的 k 题，并按难度从大到小处理。将难度升序排列后，最小耗时满足 cost[k]=cost[k−1]+前 k 题难度和，预处理后每次二分数量。',
    '处理位置的时间系数为 1、2、…、k。若较大的难度被放到较大的系数上，交换它与更小难度就能减少或保持耗时，因此最优顺序是难度降序。同时所有系数为正，把选中的题替换成更简单的未选题不会变差，所以只选最小的 k 题。\n\n设升序难度为 d1…dn。增加第 k 道题时，新选的 dk 是当前最大，应放在第一位；原来的 k−1 道题系数全部加一，增加耗时为 dk+Σ前k−1难度，即前 k 项和。由此一次扫描预处理全部 cost。\n\ncost 随数量严格递增，每次询问用 upper_bound 找最后一个不超过 t 的代价，返回对应题数。总耗时可达十的十五次方，使用 long long。',
    '时间 O(n log n+q log n)，空间 O(n)。','排序后是从大到小执行；预处理用升序前缀和；t=0 返回 0。',r'''
int n,q;cin>>n>>q;vector<long long>d(n),cost(n+1);for(auto&x:d)cin>>x;sort(d.begin(),d.end());long long sum=0;for(int i=1;i<=n;i++){sum+=d[i-1];cost[i]=cost[i-1]+sum;}while(q--){long long t;cin>>t;cout<<upper_bound(cost.begin(),cost.end(),t)-cost.begin()-1<<'\n';}
''')

add('P13831','按二叉搜索树满层分段求和',
    '二分查找形成近完全二叉搜索树。令 k=floor(log2(n+1))，前 k 层满，剩余点在第 k+1 层，可得 f(n)=(k+1)n−2^(k+1)+k+2。按 k 相同的 n 区间用等差数列求前缀和。',
    '每个目标被比较的次数就是它在二分搜索决策树中的深度。长度 n 的区间每次按中点分成大小相差至多一的两段，因此前 k=floor(log2(n+1)) 层均为满层，第 k+1 层容纳余下节点。\n\n满层贡献 Σ(d=1..k)d·2^(d−1)=(k−1)2^k+1，最后一层有 n−(2^k−1) 个点，每点深度 k+1。整理得 f(n)=(k+1)n−2^(k+1)+k+2。\n\nk 在 n∈[2^k−1,2^(k+1)−2] 内不变，所以 f(n) 是一次函数。求 F(N)=Σ(n=1..N)f(n) 时，枚举至多六十段，对 n 求等差和、常数乘段长，再取模。最终回答 F(R)−F(L−1)。所有分段端点使用六十四位整数，模乘使用先取模后的值。',
    '每组时间 O(log R)，空间 O(1)。','分界是 n+1 的最高位；L=1 时 F(0)=0；模减法规范化。',r'''
int tests;cin>>tests;const long long mod=998244353,inv2=(mod+1)/2;auto solve=[&](long long n){long long ans=0;for(long long power=4,k=1;power/2-1<=n;power*=2,k++){long long l=max(1LL,power/2-1),r=min(n,power-2);if(l<=r){long long count=(r-l+1)%mod,sum=(l%mod+r%mod)%mod*count%mod*inv2%mod;long long constant=(-power%mod+k+2+mod)%mod;ans=(ans+(k+1)*sum+constant*count)%mod;}}return ans;};while(tests--){long long l,r;cin>>l>>r;cout<<(solve(r)-solve(l-1)+mod)%mod<<'\n';}
''')

add('P11231','严格递增链覆盖与最大频数',
    '一条严格递增链可以按从小到大攻击，最终仅留一个怪兽。同攻击力的怪兽不能在同一条链中，因此最少链数等于某个攻击力的最大出现次数，这就是答案。',
    '每个怪兽最多打倒一个更弱者，因此成功攻击构成若干互不相交的链，沿链攻击力严格递增，最终每条链至少留一个怪兽。相同攻击力的怪兽不能出现在同一条严格递增链上，所以若某值出现 c 次，最终至少需要 c 条链。\n\n把所有怪兽按攻击力排序，设最大频数为 C。对每一种攻击力，把它的各个副本分配给不同的 C 条链；同一条链只会拿到同值的一个副本，不同批次值递增，因此链均严格递增。这样确实能用 C 条链覆盖全部怪兽。\n\n每条链从小到大安排攻击：最小者先作一次无效攻击，之后每个更强者打倒前一个，最后只剩最大者。由下界与构造，上述最大频数就是最优答案。实现只需计数，无需输出攻击顺序。',
    '时间 O(n+A)，空间 O(A)。','攻击必须严格更强才能击败；统计频数最大值即可。',r'''
int n;cin>>n;vector<int>count(100001);int ans=0;while(n--){int x;cin>>x;ans=max(ans,++count[x]);}cout<<ans<<'\n';
''')

add('P14081','边数容量下界与独立集上界',
    '能连出 m 条边要求 C(n,2)≥m，给出最小 n。获胜还要求能把最大独立集压到 m−1，最大的可行 n 为 2m−2。若两界交错则 Lose!，否则输出该区间。',
    '炸弹只能放在不相邻的点上，花火能否放 m 个炸弹就是图是否存在大小至少 m 的独立集。首先简单图最多有 n(n−1)/2 条边，故 n 不能小于容量下界 L。\n\n若 m 条边不是两两不相交，就有两条共享一个端点，选这个端点并对其余每边选一个端点，可用至多 m−1 个点覆盖所有边，其余至少 n−m+1 个点构成独立集。若边两两不相交，则至少需要 2m 个顶点，独立集更不可能小于 m。因此 n≥2m−1 时必输。\n\n当 m≥3，三角形加 m−3 条独立边、再加一个孤立点，共 2m−2 点、m 边，最大独立集恰有 m−1 点，可以获胜。对任何 L<=n<=2m−2，删去多余顶点，再补边至 m 条，不会增大独立集；容量条件保证能补足。二分最小 L，右界取 2m−2，比较两者即可。',
    '每组时间 O(log m)，空间 O(1)。','不允许重边与自环；m=1、2 由边界比较自然判输；容量乘积用六十四位。',r'''
int tests;cin>>tests;while(tests--){long long m;cin>>m;long long l=1,r=2*m;while(l<r){long long mid=(l+r)/2;if(mid*(mid-1)/2>=m)r=mid;else l=mid+1;}long long high=2*m-2;if(l>high)cout<<"Lose!\n";else cout<<l<<' '<<high<<'\n';}
''')

add('P14576','光标间距固定的滑动窗口',
    '把所有行连成一条坐标轴，行间跨越也算一步。所有光标同步平移，所以彼此距离不变。目标选最长一行，求有多少个行末坐标能落在长度为最长行长的窗口中。',
    '第一行开头坐标为零，长度 ai 的一行包含 ai+1 个光标位置；从它末尾到下一行开头再移动一步。因此各行末尾坐标由前缀累加 ai+1 得到，相邻末尾距离为后面那行长度加一。\n\n同时按左右键只会给所有尚存光标加上同一个位移。要把一组光标平移进同一行，它们最大与最小坐标之差必须不超过该行长度。最长行容纳能力最强，且任意满足这个跨度的光标组都能整体平移进去，途中也不会使这些最终有效光标越界消失。\n\n行末坐标天然递增，用双指针维护最大坐标减最小坐标不超过 max(ai) 的最长连续段。任意非连续选取都可补上中间光标而不增跨度，所以只看连续段不会漏最优。',
    '每组时间 O(n)，空间 O(n)。','行间换行也占一次移动；窗口比较坐标差，不是位置数；前缀和用 long long。',r'''
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<long long>position(n);long long current=0,width=0;for(int i=0;i<n;i++){long long x;cin>>x;width=max(width,x);current+=x+1;position[i]=current-1;}int l=0,ans=0;for(int r=0;r<n;r++){while(position[r]-position[l]>width)l++;ans=max(ans,r-l+1);}cout<<ans<<'\n';}
''')

add('P2804','减去平均值后统计递增前缀对',
    '把每项减去 M，原子段平均值严格大于 M 等价于新子段和大于 0，也就是右前缀和大于左前缀和。离散化后用树状数组统计此前更小前缀的数量。',
    '子段平均值大于 M，可以同乘正的长度，得到原子段和大于 M×长度。因此逐项减去 M 后，只需统计和严格为正的子段。\n\n定义前缀和 p[0]=0，子段 [l,r] 的新和为 p[r]−p[l−1]。它严格为正，当且仅当 p[l−1]<p[r]。从左到右扫描前缀和，在树状数组中保存此前前缀值出现次数，查询当前排名之前的总数，就得到以当前位置结尾的合法子段数。\n\n先查询再插入，防止把当前前缀与自己配对；查询 rank−1，防止把和为零的子段计入。重复前缀值应按次数保存。答案最后对 92084931 取模。',
    '时间 O(n log n)，空间 O(n)。','严格小于，查询排名减一；插入 p[0]；每项先减 M。',r'''
int n,m;cin>>n>>m;vector<long long>p(n+1),values;for(int i=1;i<=n;i++){int x;cin>>x;p[i]=p[i-1]+x-m;}values=p;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());Fenwick bit(values.size());long long ans=0;for(long long x:p){int rank=lower_bound(values.begin(),values.end(),x)-values.begin()+1;ans+=bit.sum(rank-1);bit.add(rank,1);}cout<<ans%92084931<<'\n';
''',FENWICK)

add('P1883','凸函数上包络的三分搜索',
    '每个二次函数在定义区间上凸，它们的逐点最大值也凸。对最大值函数在 [0,1000] 上三分，收缩到最小值附近，再输出函数值。',
    '题目要求最小化所有函数中的最大值。设 F(x)=max fi(x)，不能分别求各函数的最小值后再取最大，因为它们可能在不同位置达到最小。\n\n每个 fi 是凸函数；对任意两点及其中间点，各 fi 都不超过端点值的同权加权和，再取最大仍保留凸性。因此 F 在区间上是单谷的，可以用三分比较 m1、m2 处的值。若 F(m1)<F(m2)，最优点不会在 m2 右侧，否则对称舍掉左侧。\n\n固定迭代一百次足以使区间误差远小于输出要求。每次评估遍历全部函数，用 double，并最终输出剩余区间中点处的 F。',
    '时间 O(T·n·迭代次数)，空间 O(n)。','评估的是所有二次函数的最大值；搜索区间 [0,1000]；输出四位小数。',r'''
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<array<double,3>>a(n);for(auto &v:a)cin>>v[0]>>v[1]>>v[2];auto value=[&](double x){double answer=-1e100;for(auto v:a)answer=max(answer,(v[0]*x+v[1])*x+v[2]);return answer;};double l=0,r=1000;for(int i=0;i<120;i++){double x=(2*l+r)/3,y=(l+2*r)/3;if(value(x)<value(y))r=y;else l=x;}cout<<fixed<<setprecision(4)<<value((l+r)/2)<<'\n';}
''')

add('P2855','二分最小跳距并贪心移石',
    '给定最小跳距 D，从起点开始尽量保留最靠左的可用石头；与上个保留点距离不足 D 的石头移走。所需移走数不超过 M 时 D 可行，二分最大可行值。',
    '跳距要求越小越容易满足，所以可对答案二分。固定 D 后，若当前石头距离上次保留点不足 D，它不能保留；若已足够，优先保留最靠左的石头会给后续留下最多空间，不会比保留更右的石头更差。\n\n按位置顺序扫描，统计必须删除的石头。终点固定不可删除；若最后一次到终点距离不足 D，可以改为删除最后保留的内部石头。其前一个保留点到最后石头已至少 D，所以删掉后到终点更远，一次删除足够。代码把终点处的这次冲突计为一次删除，数值等价。\n\n可行时提高下界，不可行时降低上界。石头位置先排序，起点零与终点 L 不计入可主动移走的 M 块。',
    '时间 O(n log L+n log n)，空间 O(n)。','终点必须保留；最后一段冲突需要计一次删除；求最大可行值。',r'''
int length,n,m;cin>>length>>n>>m;vector<int>a(n+1);for(int i=0;i<n;i++)cin>>a[i];sort(a.begin(),a.begin()+n);a[n]=length;auto ok=[&](int gap){int removed=0,last=0;for(int x:a)if(x-last<gap)removed++;else last=x;return removed<=m;};int l=0,r=length;while(l<r){int mid=l+(r-l+1)/2;if(ok(mid))l=mid;else r=mid-1;}cout<<l<<'\n';
''')

add('P4058','按月份二分并累加达标树木',
    '给定月份 t，第 i 棵树高为 h_i+a_i·t，只有达到 L 的树才可砍伐。累计可砍高度是否达到 S 是单调条件，二分最早满足的月份。',
    '随时间增加，每棵树只会长高，已达到最低高度要求的树不会重新失去资格，可获得的总木材量因此单调不减。\n\n判定某月时，对每棵树计算当前高度；小于 L 的不计，否则加入总量。达到 S 就可提前返回，避免累加无关大数。高度乘法和总量使用 __int128，以覆盖月份和生长速度的乘积。\n\n先从零月检查，若不够则把右界从一不断翻倍，直到找到可行时间，再在零到右界之间找第一个可行值。这样无需猜测紧的答案上界。',
    '时间 O(n log 答案)，空间 O(n)。','达标后计整棵树高度；零月也可能满足；乘法先转 __int128。',r'''
int n;long long need,limit;cin>>n>>need>>limit;vector<long long>h(n),growth(n);for(auto &x:h)cin>>x;for(auto &x:growth)cin>>x;auto ok=[&](long long day){__int128 sum=0;for(int i=0;i<n;i++){__int128 height=h[i]+(__int128)growth[i]*day;if(height>=limit)sum+=height;if(sum>=need)return true;}return false;};long long l=0,r=1;while(!ok(r))r*=2;while(l<r){long long mid=l+(r-l)/2;if(ok(mid))r=mid;else l=mid+1;}cout<<l<<'\n';
''')

add('P6099','递增堆底与已冲洗下界',
    '把新盘放到堆底编号大于它的最左堆中；若该堆顶较小，就先冲洗掉这些更小盘。记录已经冲洗过的最大编号，一旦新盘小于它，当前前缀便不可能排好。',
    '桌面各堆的底部保持递增。把盘 x 放到堆底大于 x 的最左堆，能够尽量靠左，同时不会让更大的底盘提前挡住它；若不存在，就在最右边开新堆。堆底数组递增，可用二分找位置。\n\n同一堆中，若顶盘小于新来的 x，为了不把较小盘压在 x 下方，必须先把这些顶盘冲洗。它们以及更左堆能够按顺序处理，故记录最大已冲洗编号 washed 即可。之后任何 x<washed 的新盘都应排在已经洗好的大盘下面，却已来不及，说明从这一盘开始失败。\n\n在尚未失败时，上述放置与必要弹栈保持可整理性；遇到失败便输出此前长度。每盘最多进出一个栈一次，二分只依赖堆底，不随弹栈变化。',
    '时间 O(n log n)，空间 O(n)。','washed 只增不减；找最左的较大堆底；失败盘不计入前缀。',r'''
int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;vector<int>bottom;vector<vector<int>>stacks;int washed=0;for(int i=0;i<n;i++){int x=a[i];if(x<washed){cout<<i<<'\n';return 0;}int p=lower_bound(bottom.begin(),bottom.end(),x)-bottom.begin();if(p==(int)bottom.size()){bottom.push_back(x);stacks.push_back({});}while(!stacks[p].empty()&&stacks[p].back()<x){washed=max(washed,stacks[p].back());stacks[p].pop_back();}stacks[p].push_back(x);}cout<<n<<'\n';
''')
