"""Bipartite matching, path covers and explicit allocation witnesses."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_flow_support import MATCHING,MATCH_EXPLANATION,DINIC,FLOW_EXPLANATION,COST_FLOW


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(20472,1800,['二分图匹配'],'交换行列后能否主对角线全黑。',
        '每个黑格连接其行与列。主对角线全黑意味着为每行选一个黑格，且所选列互不相同，恰是完美匹配。反过来匹配给出行列的一一对应，只需重排列就能使所选黑格上主对角线。求最大匹配是否等于n。\n\n'+MATCH_EXPLANATION,
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;Matching match(n,n);for(int i=0;i<n;i++)for(int j=0;j<n;j++){char c;cin >> c;if(c=='1')match.edge[i].push_back(j);}cout << (match.maximum()==n?"Yes\n":"No\n");}''',
        '不能只检查每行每列至少有黑格，它们可能争抢同一列。',
        declarations=MATCHING,complexity=r'每组时间 $O(n^2\sqrt n)$，空间 $O(n^2)$。')
    put(20483,1800,['二分图匹配'],'为不回家学生及来访者分配认识的在校学生床铺。',
        '左边只建需要床的人：非在校者，或在校但不回家者。右边是所有在校者的床，无论其主人回不回家，床都存在。认识床主人就连边；在校者还可睡自己床，即使对角关系输入为0也要补此边。最大匹配覆盖所有左点即可。',
        r'''int tests;cin >> tests;while(tests--){int n;cin >> n;vector<int> student(n),home(n);for(int &x:student)cin >> x;for(int &x:home)cin >> x;Matching match(n,n);int needed=0;for(int i=0;i<n;i++)if(!student[i] || !home[i])needed++;for(int i=0;i<n;i++)for(int j=0;j<n;j++){int known;cin >> known;if((!student[i] || !home[i]) && student[j] && (known || i==j))match.edge[i].push_back(j);}cout << (match.maximum()==needed?"^_^\n":"T_T\n");}''',
        '非在校者的回家标志无意义，不能因此把来访者排除。回家学生的床仍可用。',
        declarations=MATCHING,complexity=r'每组时间 $O(n^2\sqrt n)$，空间 $O(n^2)$。')
    put(51272,1800,['二分图匹配','棋盘染色'],'有禁格棋盘最多放多少1×2骨牌。',
        '按(r+c)奇偶把可用格分为两侧，相邻格总异色，每块骨牌对应一条相邻边。骨牌不重叠恰好是匹配约束，因此最大匹配数就是最大骨牌数。题目输出文字“覆盖格数”有歧义，但8×8样例输出32，显然按骨牌块数，不乘2。',
        r'''int n,m;cin >> n >> m;vector<bool> blocked(n*n);while(m--){int x,y;cin >> x >> y;blocked[(x-1)*n+y-1]=true;}Matching match(n*n,n*n);const int dr[]={-1,1,0,0},dc[]={0,0,-1,1};for(int r=0;r<n;r++)for(int c=0;c<n;c++)if((r+c)%2==0 && !blocked[r*n+c])for(int d=0;d<4;d++){int rr=r+dr[d],cc=c+dc[d];if(rr>=0 && rr<n && cc>=0 && cc<n && !blocked[rr*n+cc])match.edge[r*n+c].push_back(rr*n+cc);}cout << match.maximum();''',
        '只从一种格子颜色向另一种建边，避免把每格既当左点又当右点而重复使用。',
        declarations=MATCHING,complexity=r'令V=n²，时间 $O(V\sqrt V)$，空间 $O(V)$。')
    put(213903,1500,['二分图匹配'],'外籍与英国飞行员配对，求最大飞机数。',
        '把外籍编号1..m作为左侧，英国编号m+1..n作为右侧，给出的可配合关系连边。每人最多参与一次，所以最大匹配即最大可起飞飞机数。输入只要求输出数量，无需输出配对。\n\n'+MATCH_EXPLANATION,
        r'''int n,m;cin >> n >> m;Matching match(m,n-m);int u,v;while(cin >> u >> v && u>0 && v>0)match.edge[u-1].push_back(v-m-1);cout << match.maximum();''',
        '当前题第一行先总人数n、后外籍数m，与某些原题版本顺序不同；按此页样例10 5读取。',
        declarations=MATCHING,complexity=r'时间 $O(E\sqrt n)$，空间 $O(n+E)$。')
    put(213817,2000,['DAG最小路径覆盖','二分图匹配'],'DAG顶点不相交路径覆盖，输出最少路径与方案。',
        '把每个点拆为左出端、右入端，原边u→v对应匹配边u左→v右。匹配限制每点最多一个后继、一个前驱；DAG无环，所以得到若干条不相交路径。每增加一条匹配边，路径条数减少1，最少路径数=n−最大匹配。\n\n从没有匹配前驱的点出发，沿匹配后继输出完整路径。',
        r'''int n,m;cin >> n >> m;Matching match(n,n);while(m--){int u,v;cin >> u >> v;match.edge[u-1].push_back(v-1);}int maximum=match.maximum();for(int start=0;start<n;start++)if(match.mateRight[start]<0){bool space=false;for(int u=start;u>=0;u=match.mateLeft[u]){if(space)cout << ' ';space=true;cout << u+1;}cout << '\n';}cout << n-maximum << '\n';''',
        '这里是顶点不相交覆盖，建原有边，不先做传递闭包。DAG保证匹配后继不会形成环。',
        declarations=MATCHING,checker='minimum-path-cover',complexity=r'时间 $O(m\sqrt n)$，空间 $O(n+m)$。')
    put(213818,2200,['增量匹配','DAG路径覆盖'],'n柱子依次放编号球，相邻和为平方，求最多球与放法。',
        '对1..M建DAG，小球i→j当i<j且i+j为平方。每根柱子是递增路径，所以最少柱数=M−最大匹配。逐个加入新球，只新增指向新右点的边及一个暂时无出边的左点；最大匹配至多增加1，只需从新右点反向尝试一次交替增广。\n\n若新球使最少柱数首次超过n，前一个球数即最优。失败增广不改变既有匹配；从没有前驱的球沿匹配后继输出各柱。邻居可由平方数s²枚举，左点为s²−新球，避免检查所有球对。',
        r'''int columns;cin >> columns;vector<int> successor(1),predecessor(1),seen(1);int stamp=0,matched=0,maximum=0;for(int value=1;;value++){successor.push_back(0);predecessor.push_back(0);seen.push_back(0);stamp++;auto augment=[&](auto &&self,int right)->bool{int first=(int)sqrt(right+1);while(first*first<=right)first++;for(int s=first;s*s<2*right;s++){int left=s*s-right;if(left<=0 || left>=right || seen[left]==stamp)continue;seen[left]=stamp;if(!successor[left] || self(self,successor[left])){successor[left]=right;predecessor[right]=left;return true;}}return false;};if(augment(augment,value))matched++;if(value-matched>columns){maximum=value-1;break;}}cout << maximum << '\n';for(int start=1;start<=maximum;start++)if(!predecessor[start]){bool space=false;for(int u=start;u;u=successor[u]){if(space)cout << ' ';space=true;cout << u;}cout << '\n';}''',
        '先尝试增广再判断柱数，贪心找第一根能放的柱子不能作为一般路径覆盖证明。失败球本身不输出。',
        declarations='',checker='magic-ball-paths',
        cases=[{'input':'1','output':'1'},{'input':'2','output':'3'},{'input':'55','output':'1567'}],
        complexity=r'最终球数B、候选边E=O(B√B)，增量匹配保守时间 $O(BE)$，空间 $O(B)$，邻边按需生成。')
    put(213819,1900,['最大流','分配方案'],'同单位代表不能同桌，按容量分配桌号。',
        '源到单位容量为人数，单位到每桌容量1，桌到汇容量为桌容量。流满总人数即存在方案；单位→桌边满1表示该单位一名代表坐那桌，逐单位输出这些桌号。容量1精确保证同单位在同桌最多一人。\n\n'+FLOW_EXPLANATION,
        r'''int groups,tables;cin >> groups >> tables;int source=groups+tables,sink=source+1;Dinic flow(sink+1);long long required=0;for(int i=0;i<groups;i++){int count;cin >> count;required+=count;flow.add(source,i,count);}for(int j=0;j<tables;j++){int capacity;cin >> capacity;flow.add(groups+j,sink,capacity);}vector<vector<int>> index(groups,vector<int>(tables));for(int i=0;i<groups;i++)for(int j=0;j<tables;j++)index[i][j]=flow.add(i,groups+j,1);if(flow.maximum(source,sink)!=required){cout << 0;return 0;}cout << 1 << '\n';for(int i=0;i<groups;i++){bool space=false;for(int j=0;j<tables;j++)if(flow.graph[i][index[i][j]].capacity==0){if(space)cout << ' ';space=true;cout << j+1;}cout << '\n';}''',
        '第一行输入m是单位数、n是桌数，变量按含义命名避免题面前后字母变化。总容量足够并不保证可行，还受每组每桌至多一人限制。',
        declarations=DINIC,checker='round-table-assignment',complexity=r'一般Dinic最坏 $O(V^2E)$，V=m+n+2、E=O(mn)，空间 $O(E)$。')
    put(25083,2100,['最大流','拆点'],'每牛选一份喜欢的食物与饮料，最大满足牛数。',
        '建源→食物→牛入点→牛出点→饮料→汇。食物、饮料各只能被用一次，源边及汇边容量1；牛拆点边容量1保证最多领一份完整餐；喜好边连通相应食物与饮料。每条单位流都对应一头得到完整餐的牛，最大流即答案。',
        r'''int n,f,d;cin >> n >> f >> d;int cowIn=f,cowOut=f+n,drink=f+2*n,source=drink+d,sink=source+1;Dinic flow(sink+1);for(int i=0;i<f;i++)flow.add(source,i,1);for(int j=0;j<d;j++)flow.add(drink+j,sink,1);for(int i=0;i<n;i++){int a,b;cin >> a >> b;flow.add(cowIn+i,cowOut+i,1);while(a--){int x;cin >> x;flow.add(x-1,cowIn+i,1);}while(b--){int x;cin >> x;flow.add(cowOut+i,drink+x-1,1);}}cout << flow.maximum(source,sink);''',
        '不能把食物、饮料分别独立最大匹配，因为两边可能满足不同的牛。拆点把两种选择绑定。',
        declarations=DINIC,complexity=r'单位容量网络Dinic为 $O(E\sqrt V)$ 级界，空间 $O(V+E)$。')
    put(51316,2000,['最小费用最大流','二分图指派'],'每人各进不同房屋，最小曼哈顿移动总费用。',
        '地图没有障碍，每个人到每间房的最短路为曼哈顿距离。建立源→人容量1、人→房容量1费用距离、房→汇容量1的费用流图。逐次最短增广得到n单位流的最小费用；反向边费用取负，允许撤回之前指派来改进组合。代码用SPFA在残量图找最短路。',
        r'''int rows,cols;while(cin >> rows >> cols && (rows||cols)){vector<pair<int,int>> people,house;for(int r=0;r<rows;r++){string s;cin >> s;for(int c=0;c<cols;c++){if(s[c]=='m')people.push_back({r,c});if(s[c]=='H')house.push_back({r,c});}}int n=people.size(),source=2*n,sink=source+1;CostFlow flow(sink+1);for(int i=0;i<n;i++){flow.add(source,i,1,0);flow.add(n+i,sink,1,0);for(int j=0;j<n;j++)flow.add(i,n+j,1,abs(people[i].first-house[j].first)+abs(people[i].second-house[j].second));}cout << flow.minimum(source,sink).second << '\n';}''',
        '可以穿过其他房屋而不入住，也可多人经过同一格，不添加网格占用冲突。',
        declarations=COST_FLOW,complexity=r'V=2n+2、E=O(n²)，最坏SPFA增广 $O(nVE)$，空间 $O(E)$。')


if __name__=='__main__':run()
