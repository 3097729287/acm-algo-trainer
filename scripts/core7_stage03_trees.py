"""Tree structure, rooted aggregates, metric walks and constructive embeddings."""
from core7_authoring import add

A=['io-basics','basic-control','vector','integer','functions']
T=A+['graphs','trees']

LIFT=r'''
struct Lift{
    int n,levels;vector<int>depth,order;vector<vector<int>>up;
    Lift(const vector<vector<int>> &g,int root):n(g.size()),levels(1),depth(n,-1){
        while((1LL<<levels)<=n)++levels;up.assign(levels,vector<int>(n,root));
        depth[root]=0;order.push_back(root);
        // 显式遍历次序，链形树也不消耗深递归调用栈。
        for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(depth[v]<0){
            depth[v]=depth[u]+1;up[0][v]=u;order.push_back(v);
        }}
        for(int j=1;j<levels;++j)for(int u=0;u<n;++u)up[j][u]=up[j-1][up[j-1][u]];
    }
    int lca(int u,int v)const{
        if(depth[u]<depth[v])swap(u,v);int gap=depth[u]-depth[v];
        for(int j=0;j<levels;++j)if((gap>>j)&1)u=up[j][u];
        if(u==v)return u;
        for(int j=levels-1;j>=0;--j)if(up[j][u]!=up[j][v]){u=up[j][u];v=up[j][v];}
        return up[0][u];
    }
};
'''

add('P1030','后序末尾定根，中序位置划分左右子树',
    '结点是互不相同的大写字母，给出同一棵二叉树的中序和后序排列，输出先序排列；最多八个结点。',
    r'''后序的最后一个字母就是当前根。在中序找到它，其左侧属于左子树，右侧属于右子树；两侧长度同时划定后序中两棵子树的范围。先输出根，再递归处理左、右子树，空范围不输出。''',
    r'''中序BADC、后序BDCA的最后一个字母A是根。中序在A处被分成B和DC，左子树只有B，右子树的中序是DC、后序是DC，所以右子树的根是C，C的左孩子为D。按根、左、右访问，输出ABCD。

用半开区间表示同一棵子树：中序下标范围为 $[l,r)$，后序为 $[p,q)$。非空时，根是后序下标 $q-1$ 处的字母。设根在中序的位置为 $mid$，左子树有 $mid-l$ 个结点；因此左子树的后序范围为 $[p,p+mid-l)$，右子树为 $[p+mid-l,q-1)$。根不再放入任一子树。

先序要求根先于两棵子树，因此找到根后立即输出，再依次递归左、右。两个排列来自同一棵树且标号不重复，根在中序中的位置唯一，这样的划分也唯一。某一侧可能为空，进入空区间直接返回；不要假定每个非叶结点都有两个孩子。

本题只有八个结点，每次在线性区间寻找根就足够，不必额外建立树后再遍历。''',
    r'''string in,post;cin>>in>>post;
function<void(int,int,int,int)>visit=[&](int l,int r,int p,int q){
    if(l==r)return;char root=post[q-1];int mid=l;while(in[mid]!=root)++mid;
    cout<<root;int left=mid-l;
    visit(l,mid,p,p+left);visit(mid+1,r,p+left,q-1);
};visit(0,in.size(),0,post.size());cout<<'\n';''',
    '后序末字母定根；中序定左右；先序先输出根；空子树直接返回；不能按字母大小判断左右。',
    r'最坏时间 $O(n^2)$，递归空间 $O(n)$；本题 $n\le8$。',tags=['递归','分治'],lessons=T+['strings','recursion','lambda-local'])

add('P4715','决赛双方是左右半区的最强队',
    '二的n次方支球队按相邻两队逐轮淘汰，能力互异、强者必胜，输出亚军的原始编号。',
    r'''前半区只能与前半区比赛，直到各自产生一位决赛选手；后半区同理。分别找两半区的能力最大者，能力较小的那一位在决赛输掉，因此是亚军。输出它的编号，而不是能力值。''',
    r'''八队的能力依次为4、2、3、1、10、5、9、7。左半区最强是第一队的4，右半区最强是第五队的10，决赛是这两队交手，所以亚军为第一队。

比赛每轮都只把相邻两位胜者配对。归纳可知，每个连续的、长度为二的幂的比赛区间，都由区间内最强者出线；决赛之前恰好剩下左半区与右半区各自的最强者。只要找这两个人，不需要存整棵比赛树。

这也说明亚军未必是所有队伍中第二强者：第二强若和冠军处于同一半区，会在决赛前被淘汰。扫描时保存最大者的原编号；原题保证能力互异，不需要平局规则。''',
    r'''int n;cin>>n;int total=1<<n;vector<int>a(total);for(int &x:a)cin>>x;
int left=0,right=total/2;
for(int i=1;i<total/2;++i)if(a[i]>a[left])left=i;
for(int i=total/2+1;i<total;++i)if(a[i]>a[right])right=i;
cout<<(a[left]<a[right]?left:right)+1<<'\n';''',
    '输出编号；亚军不是全局次大；分界是参赛总数的一半；能力可为负，不用零作最大值初值。',
    r'共有 $2^n$ 队，时间与保存输入的空间均为 $O(2^n)$。',tags=['模拟'],lessons=T)

add('P1351','枚举距离二路径的唯一中点',
    '树上每点有正权，距离恰为二的有序点对产生两端权值之积，输出最大积及所有有序积之和模10007。',
    r'''距离二的路径恰有一个中点，其两端是中点的不同邻居。扫描每点的邻居，用最大两个邻居权值更新最大积；累计和可在加入权值w时，增加两倍的新权乘此前邻居权和，正好计入两个方向。每条邻接只扫描一次。''',
    r'''若某点的邻居权值为2、5、10，经过这个中点的无序端点组合是(2,5)、(2,10)、(5,10)。最大积为50，有序总和为两倍的10+20+50，即160。

树上两个距离二的顶点只有一条路径，其中点唯一。反过来，同一个点的任意两个不同邻居之间距离都是二，否则会产生环。因此按中点统计既不漏，也不重复一个有序点对。

正权条件下，邻居中最大的两个数相乘就是本中点能产生的最大积。维护first、second，读到新权值时更新它们；邻居不足两个时贡献为零。

总和也可写成邻居权和的平方减去邻居权平方和。代码采用逐项配对：此前邻居权和为 $S$，新邻居权 $w$ 与此前每个邻居都形成一对，两个方向共增加 $2wS$。先增加贡献、再把 $w$ 加入 $S$，就不会把新邻居和自己配对。只对总和取模，最大积保留原值。

所有顶点的度数和为2(n-1)，即使星形树的中心有很多邻居，也只需线性处理，不枚举邻居对。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<long long>w(n);for(auto &x:w)cin>>x;const int MOD=10007;long long maximum=0,total=0;
for(int u=0;u<n;++u){long long first=0,second=0,sum=0;
    for(int v:g[u]){total=(total+2*w[v]%MOD*sum)%MOD;sum=(sum+w[v])%MOD;
        if(w[v]>=first){second=first;first=w[v];}else second=max(second,w[v]);
    }maximum=max(maximum,first*second);
}cout<<maximum<<' '<<total<<'\n';''',
    '统计有序对要乘二；不选相同邻居；最大积不取模；图是树才能保证中点唯一且邻居两两距离二。',
    r'时间与空间均为 $O(n)$。',tags=['结论与计数'],lessons=T+['modular'])

add('P3379','先补齐深度，再同时向上倍增',
    '给定树根S和多次点对询问，输出两点的最近公共祖先，允许询问同一点；N和M均最多五十万。',
    r'''预处理depth与up[j][u]，后者表示u向上二的j次方步的祖先。先把较深点抬到同一深度；相同则直接返回。否则从大到小尝试同时跳到仍不同的祖先，最后两点的父亲就是LCA。用显式遍历避免长链爆栈。''',
    r'''祖先包括结点自己。若四号是根，二号是四号的孩子，那么LCA(2,4)=4；不用把四号再往上跳一次。

先以指定根遍历树，记录每点深度与父亲。令up[0][u]为父亲，根的父亲设为根；再用

$$up[j][u]=up[j-1][up[j-1][u]]$$

把两个长度为二的j-1次方的跳跃拼成一个更长跳跃。表的层数覆盖最大可能深度即可。

查询时，深度差的二进制哪些位为一，就跳相应长度。两点等深后若已经相同，它就是最近共同点；否则它们都在LCA下方。由大到小检查，如果两个二的j次方祖先仍不相同，就能安全同时跳过去，因为仍没有越过两条祖先链第一次会合的位置。若祖先相同则不能这样跳，否则可能跳过真正答案。

循环结束时两个点不同、父亲相同，返回这个父亲。每个跳长只检查一次，单次查询只需对数时间。预处理也采用队列式次序，不用递归DFS，五十万点的链不会耗尽调用栈。''',
    r'''int n,m,s;cin>>n>>m>>s;--s;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
Lift lift(g,s);while(m--){int u,v;cin>>u>>v;cout<<lift.lca(u-1,v-1)+1<<'\n';}''',
    '采用题目给出的根；同点和祖先关系先返回；只有倍增祖先不同才同时跳；用足够层数；链形树不用深递归。',
    r'预处理时间、空间 $O(n\log n)$，每次查询 $O(\log n)$。',tags=['LCA','倍增'],lessons=T+['binary-lifting','bitwise'],declarations=LIFT)

add('P10113','先求共同祖先链，再在链上选最大编号',
    '零号为老板，其他员工给出直接领导。每次给出一组员工，求能管理所有人的、编号最大的员工；父亲编号不保证小于孩子。',
    r'''所有可主持者恰为参与者LCA到根的整条祖先链，不一定以LCA编号最大。预处理mx[u]为根到u路径上的最大编号；将参与者逐个与当前结果求LCA，最后输出mx[LCA]。不能直接输出LCA。''',
    r'''假设管理链为零号、五号、二号，二号下面又有三号和四号。三、四号最近的共同领导是二号，但五号也能管理他们且编号更大，正确答案应为五号。

对多名员工，先对前两人取LCA，再与下一人继续取LCA。每一步保留此前全部人员最深的共同祖先；处理完全部人后得到l。任何能管理全部人员的人，必为l或l的祖先；这些人也全部合法。

题目要最大编号，而非最深层级。以零号为根建立树后，按父亲先于孩子的遍历次序计算mx[0]=0，mx[u]=max(mx[parent[u]],u)。这样mx[l]正好覆盖所有合法主持人。

输入的父亲编号可能大于孩子编号，不能直接按编号从小到大计算mx。先读完所有关系，再真正遍历树。员工本身也能管理自己，查询中若一人是所有人的祖先，LCA可能就是该参与者；上述链上最大值仍适用。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);for(int u=1,p;u<n;++u){cin>>p;g[p].push_back(u);g[u].push_back(p);}
Lift lift(g,0);vector<int>maximum(n);for(int u:lift.order)maximum[u]=max(u,maximum[lift.up[0][u]]);
int q;cin>>q;while(q--){int m,l,u;cin>>m>>l;for(int i=1;i<m;++i){cin>>u;l=lift.lca(l,u);}cout<<maximum[l]<<'\n';}''',
    '输出祖先链上的最大编号；领导编号可大于下属；员工从零编号；多人的LCA逐次合并；按真实遍历顺序递推。',
    r'预处理时间、空间 $O(n\log n)$；一组m人查询 $O(m\log n)$。',tags=['LCA','倍增'],lessons=T+['binary-lifting'],declarations=LIFT)

add('P1185','先确定满树坐标，删除只让对应枝条留空',
    '按指定字符间距画m层满二叉树，删除若干指定层、序号的结点及整个子树和父边。删除不压缩其它结点的位置，空白使用普通空格。',
    r'''底部兄弟叶子相隔四列，故最后一次父子横纵位移为2；再往上一层位移为3，之后依次6、12……。预先计算各层位移，根放在画布正中。递归到未删除的孩子时才画连接斜线及孩子；遇到删除结点就返回，整片保留为空格。''',
    r'''两层树的两片叶子位于第零、四列，父亲在第二列，连接斜线位于中间一行。三层树的四片叶子位于零、四、六、十列，两位父亲在二、八列，根在五列：上层位移为三，最后一层位移为二。最底层的兄弟间距与不同父亲叶子的间距不同，不能全程套同一个二次幂公式。

设第d层到下一层的横向位移为step[d]，纵向位移也相同，因为边沿四十五度逐字符绘制。最后step[m-2]=2；若还有上一层，step[m-3]=3；再往上每层乘二。根的横坐标为全部step之和，画布高为这个和加一，宽为它的两倍加一。

以零层、零序号为根。左、右孩子在下一层的序号分别为2j、2j+1，坐标分别偏移负、正step，纵坐标增加step。边的中间位置逐格写斜线，终点由孩子递归写字母o。

删除表用原满树中的层与序号标记。父结点在画某条边以前先看孩子是否被删；被删就既不画边，也不进入孩子。祖先被删时根本不会遍历后代，因而同时列出的祖孙删除也不会出错。整幅画布最初全是ASCII 32，原位置从不移动，末尾空格也按完整画布输出。''',
    r'''int m,n;cin>>m>>n;vector<vector<char>>removed(m);for(int d=0;d<m;++d)removed[d].assign(1<<d,false);
for(int z=0,d,j;z<n;++z){cin>>d>>j;removed[d-1][j-1]=true;}
vector<int>step(m-1);step[m-2]=2;if(m>=3)step[m-3]=3;for(int d=m-4;d>=0;--d)step[d]=2*step[d+1];
int span=accumulate(step.begin(),step.end(),0);vector<string>canvas(span+1,string(2*span+1,' '));
function<void(int,int,int,int)>draw=[&](int d,int index,int y,int x){
    if(removed[d][index])return;canvas[y][x]='o';if(d+1==m)return;
    for(int side=0;side<2;++side){int child=2*index+side;if(removed[d+1][child])continue;
        int sign=side?1:-1,len=step[d];for(int t=1;t<len;++t)canvas[y+t][x+sign*t]=side?'\\':'/';
        draw(d+1,child,y+len,x+sign*len);
    }
};draw(0,0,0,span);for(const auto &row:canvas)cout<<row<<'\n';''',
    '最后一层位移二，倒数第二次位移三；删除父边；子树删除不挪位置；普通空格初始化；字符反斜线需转义。',
    r'画布高宽都是 $O(2^m)$，输出及画布空间为 $O(4^m)$，递归深度 $O(m)$。',tags=['模拟','递归'],lessons=T+['strings','recursion','lambda-local'],exact=True)

add('P5536','以树中心为根，保留高度最高的k个结点',
    '在单位边树中选k个连通的核心城市，最小化其它城市到核心集合的最大距离，k小于n，n最多十万。',
    r'''两次遍历求直径，取其中点为根。逆序计算每点的子树高度h，叶子为零。将全部高度降序排序，答案是下标k处的高度加一。高度较大的k个点可选成连通核心；父亲高度严格大于孩子，边界同高不影响连通性。''',
    r'''先看一条五点链。以中点为根，高度依次包含2、1、1、0、0。只保留一个核心，最远距离为二；保留三个最高点，剩下两端距核心都是一。这不是按原编号或根的深度排序。

两次遍历得到直径及其结点序列，取中间一个结点c为根，其偏心距为树的半径r。如果一个连通核心集合不含c，它只能处于c的某个分支；直径的另一侧至少还有r-1条边，距该核心至少r。因此想把答案降到r以下，核心一定包含c；答案等于r时也可选含c的核心。只需考虑含c的连通核心。

设目标距离为 $R$。对非核心点u，若子树高度h[u]至少 $R$，u最深的后代离u至少 $R$，而核心只能在u的祖先方向，距离至少 $R+1$，矛盾。因此所有满足 $h[u]\ge R$ 的点都必须保留。

反过来，把这些点全保留，它们自动连通，因为父亲高度至少比孩子大一。每棵被剪掉的分支，其顶点v的高度最多R-1，从核心经一条边进入v再到最远后代，距离最多R。若保留数量不足k，还能沿边补点，不增加距离。

所以答案是使“高度至少R的点不超过k个”成立的最小整数R。高度降序为b[0..n-1]，第k+1大的高度是b[k]，取R=b[k]+1恰好跨过这个障碍。根的高度是唯一最大值，故结果不会超过半径。''',
    r'''int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n),distance(n),order;
auto farthest=[&](int s){fill(distance.begin(),distance.end(),-1);order={s};distance[s]=0;parent[s]=s;
    for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(distance[v]<0){distance[v]=distance[u]+1;parent[v]=u;order.push_back(v);}}
    return int(max_element(distance.begin(),distance.end())-distance.begin());
};int a=farthest(0),b=farthest(a);vector<int>path;for(int u=b;;u=parent[u]){path.push_back(u);if(u==a)break;}
int center=path[path.size()/2];farthest(center);vector<int>height(n);
for(int i=n-1;i>0;--i){int u=order[i];height[parent[u]]=max(height[parent[u]],height[u]+1);}
sort(height.begin(),height.end(),greater<int>());cout<<height[k]+1<<'\n';''',
    '用直径中心为根；高度是到最深后代而非深度；下标k对应第k+1大；两次遍历求直径，另一次以中心建树。',
    r'时间 $O(n\log n)$，空间 $O(n)$，全部树遍历均为非递归。',tags=['树的直径','贪心'],lessons=T+['sort','lambda-local'])

add('UVA11987','元素名与并查集结点分开，移动时换一个新结点',
    '维护一至n的集合，支持合并两集合、只移动一个元素到另一个集合、查询集合元素个数与元素和；多组输入直到EOF。',
    r'''pos[p]记录元素p目前对应的并查集结点。合并照常维护根上的个数与和；移动时先从旧根扣去p，再新建一个代表p的结点并直接挂到目标根，更新pos[p]。旧结构不拆除，旧结点不再代表实际元素。''',
    r'''普通并查集不能直接把p的父亲改成目标根。若其它元素的父指针经过p，这样会把它们也一起搬走。要分开“元素p”与“树里的存储结点”。

开始pos[p]=p，每个结点各有一个元素。合并集合时，通过pos[p]、pos[q]找到根，把两个树按结构大小合并，元素个数及元素和相加。

移动p时，先找它和q所在的根。若同根无需动作；否则旧根的实际元素数减一、和减p。创建全新结点id，让pos[p]=id，父亲直接设为目标根；目标根实际元素数加一、和加p。旧结点继续留在原树，它或许仍是其它元素的祖先，但已不再由pos[p]指向，不会把p重复计入。

根上的实际元素数可能变为零，仍不应拆除旧树。为保证合并复杂度，另用结构大小rankSize记录并查集结点规模，不把会因移动变小的实际元素数当作按大小合并指标。每次新建结点也增加目标根的结构大小。

一次操作至多新建一个结点，容量n+m就足够。查询元素和可达约五十亿，使用long long。原站PDF明确是多组直到文件结束，不能只读第一组。''',
    r'''int n,m;while(cin>>n>>m){vector<int>parent(n+m+1),rankSize(n+m+1,1),count(n+m+1),pos(n+1);vector<long long>sum(n+m+1);
    iota(parent.begin(),parent.end(),0);for(int i=1;i<=n;++i){pos[i]=i;count[i]=1;sum[i]=i;}int nodes=n;
    auto root=[&](int u){while(parent[u]!=u){parent[u]=parent[parent[u]];u=parent[u];}return u;};
    while(m--){int type,p,q;cin>>type>>p;int a=root(pos[p]);
        if(type==3){cout<<count[a]<<' '<<sum[a]<<'\n';continue;}cin>>q;int b=root(pos[q]);if(a==b)continue;
        if(type==1){if(rankSize[a]<rankSize[b])swap(a,b);parent[b]=a;rankSize[a]+=rankSize[b];count[a]+=count[b];sum[a]+=sum[b];}
        else{--count[a];sum[a]-=p;int id=++nodes;pos[p]=id;parent[id]=b;++rankSize[b];++count[b];sum[b]+=p;}
    }
}''',
    '只移动p；pos与结构结点分离；旧结点不删除；根的统计不是结构大小；同集合操作忽略；多组到EOF；和用六十四位。',
    r'每组初始化空间与时间 $O(n+m)$，操作总摊还 $O((n+m)\alpha(n+m))$。',tags=['并查集'],lessons=A+['dsu','lambda-local'])

add('CF77C','第一次进入子树取得整段收益，剩余入口只补往返',
    '树上各点有一定数量海狸，机器每沿一条边到达某点就吃该点一只，没有海狸则不能进入。从s出发并最终回到s，最多吃多少只；出发时不吃。',
    r'''以s为根。非根u第一次从父亲进入已消耗一只，剩k[u]-1个返回u的额度。每个孩子第一次往返的收益为1+dp[v]个边对，先按此收益降序选择；选完孩子后，若u仍有额度，可用孩子未使用的海狸补一次一个边对。记录dp和本点实际用于孩子的额度used，供父亲算剩余额度。根有k[s]额度，最终乘二。''',
    r'''走到一个孩子再返回，吃掉孩子一只、当前点一只，所以贡献两只海狸。若第一次进入孩子后还可以游走它的子树，则这一次往返会顺便带回更大的收益。只在出发点停留不会吃海狸，根初始也没有消耗。

闭合游走在每条树边上的两个方向次数相同。把一来一回称作一个边对，答案就是边对总数的两倍。以s为根，dp[u]表示已经从父亲进入u一次后，在u子树内最多能再完成多少个边对；used[u]表示达到这个最优值时，最少用了多少次从孩子返回u。非根u可用额度B=k[u]-1，根直接取B=k[s]。

若决定访问孩子v，第一次往返可获得1+dp[v]个边对，而它只使用一次返回u的额度。因此先选这种收益最大的孩子，最多选B个。各子树没有其它交叉，第一次开启不同孩子的收益可以直接相加。

孩子v达到dp[v]时，第一次从u进入占一只，内部返回v占used[v]只，尚有k[v]-1-used[v]只没用。父亲继续与v直接往返，每次恰好再增加一个边对，直到双方额度用完。若孩子没有剩余海狸，想多从父亲进入一次，就必须少做一次内部返回；失去的内部边对至少抵消新边对，不会增加总数。因此额外访问的正收益只有这些空余额度。

所有第一次访问的收益至少为一，不比额外直接往返差。先按1+dp降序开启孩子，再把剩余父额度与已开启孩子的空余总量取最小值，正好得到最优边对数；增加同样数量到used[u]，记录实际消耗。收益相同时优先空余多者便于实现；若有未开启孩子，说明B已全用于首次访问，不会再使用空余。

倒着处理一次显式建树次序，每个孩子的状态就先于父亲得到。海狸总数可达百亿，收益及总额度用long long。''',
    r'''int n;cin>>n;vector<long long>k(n);for(auto &x:k)cin>>x;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}int s;cin>>s;--s;
vector<int>parent(n,-1),order{s};parent[s]=s;for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(parent[v]<0){parent[v]=u;order.push_back(v);}}
vector<long long>dp(n),used(n);for(int i=n-1;i>=0;--i){int u=order[i];vector<pair<long long,long long>>choice;
    for(int v:g[u])if(parent[v]==u&&v!=u)choice.push_back({1+dp[v],k[v]-1-used[v]});
    sort(choice.begin(),choice.end(),greater<pair<long long,long long>>());long long budget=k[u]-(u!=s),spare=0;
    for(const auto &[gain,remaining]:choice){if(used[u]==budget)break;dp[u]+=gain;spare+=remaining;++used[u];}
    long long extra=min(budget-used[u],spare);dp[u]+=extra;used[u]+=extra;
}cout<<2*dp[s]<<'\n';''',
    '根初始不吃；每次进入目的点才吃；必须回根；非根预扣首次进入的一只；额外往返只能用孩子的空余额度；收益用六十四位。',
    r'时间 $O(n\log n)$，空间 $O(n)$；显式次序避免十万点长链递归。',tags=['树形 DP','贪心'],lessons=T+['dp','sort','bindings'])

add('CF455C','只维护每个连通块的直径，合并时连接两树中心',
    '初始图是一片森林，支持查询某块直径及最优连接两块。连接端点可在两块中任选，并非必须连接询问中给出的两座城市。',
    r'''初始每棵树两次遍历求直径D，用并查集维护块。合并两块时新直径为max(D1,D2,ceil(D1/2)+ceil(D2/2)+1)，把该值放到新根。旧块内部直径不变，跨块路径在两边中心相连时最短。同块合并忽略。''',
    r'''长度为四和长度为二的两条链，半径分别为二和一。连接它们的中心，跨块最长路径长二加一条新路加一，为四；原最长路径也是四，所以合并直径仍为四。若直接连接两个端点，则可能变成七，题意允许我们选择更好的端点。

树中一个点到其它点的最大距离称为其偏心距。它至少是直径的一半向上取整；直径中间的结点能达到这个下界。连接第一树的a与第二树的b后，跨块最长路为ecc(a)+1+ecc(b)。两边相互独立，各自选择中心即达到最小值。

旧树内部的所有路径仍然存在，故新直径还必须不小于D1、D2。三者取最大值便得到公式。后续操作只问块身份与直径，不问新路的具体端点，因此不用真的给图添加这条边。

初始森林中，每个块先从任意点走到最远点，再从该点走到最远点，就得到直径。遍历采用父亲标记，每次只处理该块，不为每个孤点重新清空整个n长数组。并查集按结构大小合并，并把新直径写到合并后的根上。''',
    r'''int n,m,q;cin>>n>>m>>q;vector<vector<int>>g(n);DSU dsu(n);
for(int i=0,u,v;i<m;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);dsu.merge(u,v);}
vector<int>diameter(n),parent(n),dist(n);vector<char>seen(n);
auto farthest=[&](int s){vector<int>order{s};parent[s]=s;dist[s]=0;int best=s;
    for(size_t i=0;i<order.size();++i){int u=order[i];seen[u]=true;if(dist[u]>dist[best])best=u;
        for(int v:g[u])if(v!=parent[u]){parent[v]=u;dist[v]=dist[u]+1;order.push_back(v);}}
    return best;
};for(int u=0;u<n;++u)if(!seen[u]){int a=farthest(u),b=farthest(a);diameter[dsu.root(u)]=dist[b];}
while(q--){int type,x,y;cin>>type>>x;--x;int a=dsu.root(x);if(type==1){cout<<diameter[a]<<'\n';continue;}
    cin>>y;int b=dsu.root(y-1);if(a==b)continue;
    int value=max({diameter[a],diameter[b],(diameter[a]+1)/2+(diameter[b]+1)/2+1});
    dsu.merge(a,b);diameter[dsu.root(a)]=value;
}''',
    'x、y只标识块，不指定连接端点；半径向上取整；同块忽略；初始为森林；直径保存到并查集根。',
    r'初始遍历 $O(n+m)$，q次操作摊还 $O(q\alpha(n))$，空间 $O(n+m)$。',tags=['树的直径','并查集'],lessons=T+['dsu','lambda-local'],
    declarations=r'''struct DSU{vector<int>p,size;explicit DSU(int n):p(n),size(n,1){iota(p.begin(),p.end(),0);}int root(int u){while(p[u]!=u){p[u]=p[p[u]];u=p[u];}return u;}bool merge(int a,int b){a=root(a);b=root(b);if(a==b)return false;if(size[a]<size[b])swap(a,b);p[b]=a;size[a]+=size[b];return true;}};''')

add('CF540E','把被交换的位置单独统计，空隙中的整数按长度补回',
    '初始无限递增序列一、二、三……，执行最多十万次两位置交换，位置可达十亿，求最终逆序对数量。',
    r'''只有曾被交换的位置会改变。收集并排序这些位置x，模拟它们的值排名p。触及位置之间的逆序对用树状数组统计；每个位置i与未触及整数形成的逆序数是abs(x[i]-x[p[i]])-abs(i-p[i])。这正是原坐标距离减去触及位置的排名距离，求和即可。''',
    r'''只交换第一、三位，序列成为三、二、一。被触及位置是第一、三位，它们相互贡献一个逆序；中间未触及的二还分别与两端产生一个逆序，总数是三。压缩成两个相邻位置后只数一次，会漏掉这些空隙。

收集所有交换端点，排序去重为x[0..c-1]。这些位置初始保存相同位置编号的值，交换以后仍是这c个值的一个排列；用排名p[i]表示位置x[i]最终存放x[p[i]]。按照输入顺序交换排名即可。

先统计两端都在触及集合中的逆序。按位置从左到右扫描，树状数组保存此前的值排名出现次数；此前总数i减去不大于p[i]的个数，就是以当前点为右端点的逆序数量。

再看一端未触及的逆序。该位置j的值始终是j。若x[p[i]]大于x[i]，恰好位于两者之间的未触及j会构成逆序；向左移动时同理。因此只需数两个原坐标之间的未触及整数。

原坐标之间共有D-1个整数，其中d-1个是其它触及位置，D为两坐标之差的绝对值，d为排名差的绝对值，未触及数为D-d。把每个触及位置的这一项相加不会重复：这类逆序只有一个触及端点。未触及的两个位置仍递增，没有贡献。

下界查找只用于在有序x中找到确定存在的端点，树状数组内部采用一开始的编号。结果可远超int，所有坐标差、贡献和答案用long long。''',
    r'''int n;cin>>n;vector<pair<long long,long long>>swaps(n);vector<long long>x;for(auto &[a,b]:swaps){cin>>a>>b;x.push_back(a);x.push_back(b);}
sort(x.begin(),x.end());x.erase(unique(x.begin(),x.end()),x.end());int c=x.size();vector<int>p(c);iota(p.begin(),p.end(),0);
for(auto [a,b]:swaps){int u=lower_bound(x.begin(),x.end(),a)-x.begin(),v=lower_bound(x.begin(),x.end(),b)-x.begin();swap(p[u],p[v]);}
vector<int>bit(c+1);auto sum=[&](int i){int s=0;for(;i;i-=i&-i)s+=bit[i];return s;};long long answer=0;
for(int i=0;i<c;++i){answer+=i-sum(p[i]+1);for(int j=p[i]+1;j<=c;j+=j&-j)++bit[j];
    answer+=llabs(x[i]-x[p[i]])-abs(i-p[i]);
}cout<<answer<<'\n';''',
    '按原顺序交换值；触及点逆序与空隙贡献分别算；坐标差不能用排名差代替；未触及点之间无逆序；答案六十四位。',
    r'至多2n个触及位置，时间 $O(n\log n)$，空间 $O(n)$。',tags=['离散化','树状数组'],lessons=A+['sort','bounds','fenwick','bindings','lambda-local'])

add('P1099','枚举一条直径上的核端点，用三段距离计算偏心距',
    '带权树中选某条直径上的结点到结点子路径，长度不超过s，可退化为单点，最小化全树到这条子路径的最大距离；n最多三百，允许零权边。',
    r'''计算树上所有点对距离，找到一条直径。枚举这条直径上长度不超过s的端点a、b，对每点v计算到路径的距离(dist[v][a]+dist[v][b]-dist[a][b])/2，取最大为本核偏心距，再对核取最小。只枚举结点端点，s为零也可取a=b。''',
    r'''树上v到路径a至b的第一次接入点为p。v到a和v到b的两条路线都包含v到p，而a至b这一段在两条距离中各占一侧，所以

$$D(v,P_{a,b})=\frac{d(v,a)+d(v,b)-d(a,b)}2.$$

这是树的唯一简单路径关系，分子恰为两倍的枝长，用整数除二即可。即使某些边为零，也不需要浮点数或按距离猜父亲。

n只有三百。每个点作为起点遍历一次树，得到全部距离；从某点到最远点A，再取距A最远点B，得到一条直径。保存以A为起点遍历时的真实父亲，沿B的父链恢复结点序列。之后枚举序列上的两个端点，只保留长度不超过s者，逐点计算偏心距。

为什么固定一条直径就够？把树中其它路径投影到这条直径，投影是一段长度不增的、以树结点为端点的路径，直径两端到它的距离不大于原偏心距。直径外任一分支长度h不大于接入点到直径两端的距离，否则原直径不是最长。若一条候选路径想使偏心距小于h，就必须同时进入这个分支及直径的两个方向，简单路径做不到。因此所有路径的最优偏心距至少为最大分支高度H；而固定直径上某段的偏心距正好是两端剩余长度与H的最大值。投影便能达到不差的结果。

最坏只有约n的平方个端点对，每对再扫描n个点，三次方规模足够。不必引入滑动窗口或复杂数据结构。若所有边为零，求出的直径可能退化为单点，偏心距本来就是零，仍得到正确答案。''',
    r'''int n;long long limit;cin>>n>>limit;vector<vector<pair<int,int>>>g(n);
for(int i=1,u,v,w;i<n;++i){cin>>u>>v>>w;--u;--v;g[u].push_back({v,w});g[v].push_back({u,w});}
vector<vector<long long>>d(n,vector<long long>(n));vector<vector<int>>parent(n,vector<int>(n,-1));
for(int s=0;s<n;++s){vector<int>order{s};parent[s][s]=s;
    for(size_t j=0;j<order.size();++j){int u=order[j];for(auto [v,w]:g[u])if(parent[s][v]<0){parent[s][v]=u;d[s][v]=d[s][u]+w;order.push_back(v);}}
}
int a=max_element(d[0].begin(),d[0].end())-d[0].begin(),b=max_element(d[a].begin(),d[a].end())-d[a].begin();
vector<int>path;for(int u=b;;u=parent[a][u]){path.push_back(u);if(u==a)break;}
long long answer=LLONG_MAX;for(int a:path)for(int b:path)if(d[a][b]<=limit){long long worst=0;
    for(int v=0;v<n;++v)worst=max(worst,(d[v][a]+d[v][b]-d[a][b])/2);answer=min(answer,worst);
}cout<<answer<<'\n';''',
    '端点只能选结点；允许单点核和s为零；零权边靠父链恢复路径；用点到整段路径的距离，不能只取到两端距离的较小值。',
    r'时间 $O(n^3)$，空间 $O(n^2)$，适用于原题 $n\le300$。',tags=['树的直径','枚举'],lessons=T+['geometry','enumeration','bindings'])

add('P9433','关键点的连通子树只建一次，询问只补两条接入路',
    '带权树中固定k个关键点，每次给s、t，求从s走到t并至少经过每个关键点一次的最短路程，允许重复经过边。',
    r'''先找连接全部关键点的最小子树H，总边权W。每个点v记录到H的唯一接入点p[v]和距离h[v]。询问答案为2W+h[s]+h[t]-dist(p[s],p[t])：H内除接入点间路径走一次，其余边走两次；两端接入路各走一次。用LCA计算最后的距离。''',
    r'''两关键点之间的主干长八，从主干某点走出去长一的支路不含关键点。若从这个支路末端出发、最后仍回到那里，必须走一加十六加一，共十八。不能仅求起终点间最短路，因为所有小球都必须收集。

把树以任意点为根，统计每个子树的关键点数cnt。父子边在H中，当且仅当孩子侧有关键点、另一侧也有关键点，即0<cnt[child]<k。给这些边的两端及所有关键点作标记，累计边权得到W。k=1时没有必要边，H就是唯一关键点。

H连通。每个H外的分支只有一个接入H的位置，否则原树会有环。因此从全部H结点一起向外遍历，继承接入点p并累计路长h即可。虽然边有权，这里不需要Dijkstra：每个外部结点只有这一条通向H的路径，没有两条候选短路相互竞争。

从s出发，第一次进入H必在p[s]；最终到t以前最后离开H必在p[t]。这两段至少花h[s]+h[t]。在H中，从p[s]到p[t]的边必须走奇数次，至少一次；其余必要边为了访问另一侧并返回，至少两次。对应最小长度为

$$2W-d(p[s],p[t]).$$

按这条路径前进，遇到旁支做一次完整往返，就同时达到所有边的下界。三项相加得到答案。p[s]=p[t]时距离为零，即使s与t在同一外部分支，仍须先收集H里的球，再按唯一道路返回；公式无需另作减去公共支路的处理。

预处理完整树的LCA，设 $R_u$ 是树根到u的带权距离，则

$$d(a,b)=R_a+R_b-2R_{\operatorname{LCA}(a,b)}.$$

一次询问只需一次LCA。所有总路程用long long。''',
    r'''int n,q,k;cin>>n>>q>>k;vector<vector<int>>g(n);vector<vector<pair<int,int>>>weighted(n);
for(int i=1,u,v,w;i<n;++i){cin>>u>>v>>w;--u;--v;g[u].push_back(v);g[v].push_back(u);weighted[u].push_back({v,w});weighted[v].push_back({u,w});}
vector<int>count(n);vector<char>core(n);for(int i=0,u;i<k;++i){cin>>u;--u;count[u]=1;core[u]=true;}
Lift lift(g,0);vector<long long>rootDist(n);vector<int>edgeWeight(n);
for(int u:lift.order)for(auto [v,w]:weighted[u])if(lift.up[0][v]==u&&v!=u){rootDist[v]=rootDist[u]+w;edgeWeight[v]=w;}
long long total=0;for(int i=n-1;i>0;--i){int u=lift.order[i],p=lift.up[0][u];
    if(count[u]>0&&count[u]<k){total+=edgeWeight[u];core[u]=core[p]=true;}count[p]+=count[u];
}
vector<int>attach(n,-1),order;vector<long long>height(n);for(int u=0;u<n;++u)if(core[u]){attach[u]=u;order.push_back(u);}
for(size_t i=0;i<order.size();++i){int u=order[i];for(auto [v,w]:weighted[u])if(attach[v]<0){attach[v]=attach[u];height[v]=height[u]+w;order.push_back(v);}}
while(q--){int s,t;cin>>s>>t;--s;--t;int a=attach[s],b=attach[t],l=lift.lca(a,b);
    long long distance=rootDist[a]+rootDist[b]-2*rootDist[l];cout<<2*total+height[s]+height[t]-distance<<'\n';
}''',
    'n、q、k按原顺序读；需要全部关键点；k为一时H为单点；外部分支只有一个接入点；s=t仍可能需要往返；总权六十四位。',
    r'预处理时间、空间 $O(n\log n)$，每次询问 $O(\log n)$。',tags=['LCA','倍增'],lessons=T+['binary-lifting','bindings'],declarations=LIFT)

add('CF196C','极点作树根，按极角把点分给各个子树',
    '给一棵n点树和n个平面点，无三点共线，将树无交叉地画在这些点上。原英文要求按平面点输入顺序输出放在该点的树结点编号。',
    r'''预处理有根树各子树大小。对子问题，选平面点集中纵坐标最小、同高时最左的点放根；其余点按绕它的极角排序，按各孩子子树大小分成连续块，递归安排。各块位于互不重叠的扇区，其内部线段和根的连边不会相交。叉积用__int128。''',
    r'''一棵根有两个孩子的树，若一个孩子的子树需要两个点、另一个需要三个点，就从根点向外按方向扫过其它五点，前两个交给第一棵子树，后三个交给第二棵子树。不能只把孩子各取一个点，剩下的子孙也需要预留空间。

先任取树结点一为根，得到父亲、遍历次序与子树大小。对子问题(u,points)，这组点的数量等于u的子树大小。选择纵坐标最小、同高时横坐标最小的点p给u。其它向量都位于朝上的同一半平面，按叉积为正的顺序比较即可；不需要浮点atan2，也不会出现绕回一整圈的排序矛盾。

将有序点列按每个孩子的子树大小切成连续块。不同块各在一个角度扇区内，块中点的凸包也在该扇区内，互不相交。递归画出的子树边都在各自点集的凸包中，因此不同子树之间不会交叉。

u到某孩子根的连线也在该孩子的扇区内。孩子仍选本块最低点，其它点都不比它低；父根p在其下方，所以父子连线除了终点不会进入子树的凸包。没有三点共线，保证边不穿过另一个结点，也不会产生重叠线段。这样逐层得到合法图形。

代码用待处理子问题栈，取出当前子问题后，将对应点块交给孩子，不保留各层整份副本。每组点先选极点，再排序；最坏链形树会依次排序n、n-1……个点，时间为二次方乘对数，适用于n最多一千五百。

特别核对输出方向：原英文要求第i个数是第i个平面点上放的树结点。缓存中文翻译的反向描述不能当作输出规范；代码保存answer[pointId]=treeVertex。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<Point>point(n);for(auto &p:point)cin>>p.x>>p.y;vector<int>parent(n,-1),order{0},size(n,1);parent[0]=0;
for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:g[u])if(parent[v]<0){parent[v]=u;order.push_back(v);}}
for(int i=n-1;i>0;--i)size[parent[order[i]]]+=size[order[i]];
vector<int>all(n),answer(n);iota(all.begin(),all.end(),0);vector<Job>jobs;jobs.push_back({0,all});
while(!jobs.empty()){Job job=jobs.back();jobs.pop_back();int u=job.u;auto &ids=job.ids;
    auto pivot=min_element(ids.begin(),ids.end(),[&](int a,int b){return tie(point[a].y,point[a].x)<tie(point[b].y,point[b].x);});
    iter_swap(ids.begin(),pivot);int p=ids[0];answer[p]=u+1;
    sort(ids.begin()+1,ids.end(),[&](int a,int b){return cross(point[p],point[a],point[b])>0;});
    int next=1;for(int v:g[u])if(parent[v]==u&&v!=u){vector<int>part(ids.begin()+next,ids.begin()+next+size[v]);next+=size[v];jobs.push_back({v,part});}
}for(int i=0;i<n;++i)cout<<answer[i]<<(i+1==n?'\n':' ');''',
    '按点输出树编号；极点保证角度在同一半平面；按子树大小分块；叉积避免浮点角度与溢出；不假定点输入顺序与树相同。',
    r'最坏时间 $O(n^2\log n)$，当前活动点块与图等额外空间 $O(n)$。',tags=['构造','分治','计算几何'],lessons=T+['geometry','sort','lambda-local','vector-ranges'],
    declarations=r'''struct Point{long long x,y;};struct Job{int u;vector<int>ids;};
__int128 cross(Point p,Point a,Point b){return (__int128)(a.x-p.x)*(b.y-p.y)-(__int128)(a.y-p.y)*(b.x-p.x);}''',checker='tree_embedding')

add('CF538E','数出至少需要多少个大叶子或小叶子',
    '有根树的叶子填一到m各一次，两人轮流向孩子移动，先手最大化、后手最小化。可事先重排叶子数字，分别求最终结果的最大及最小可能值。',
    r'''把叶子分成“大于等于阈值”或“小于等于阈值”。强制结果大的最少大叶子数high：最大层取孩子最小值，最小层求和；强制结果小的最少小叶子数low正好相反。叶子两者均为一。最大结果为m-high[root]+1，最小结果为low[root]。''',
    r'''根为最大化一方操作，其一个孩子直接是叶子，另一个孩子由最小化一方选择两片叶子。要让结果尽可能大，只需把最大数字放到那个直接孩子；要让结果尽可能小，却必须同时压住根的两个选项。这里要优化的是数字怎样分配，不是只对某种固定赋值做一次极大极小搜索。

先固定一个阈值x，只关心最终结果能否至少为x。把数字不小于x的叶子称作大叶子，其余是小叶子。令high[u]为无论双方最优操作，能保证u子树结果为大的最少大叶子数。叶子需要一个；最大化一方只要一个孩子为大，因此取孩子high的最小值；最小化一方会选择任一较小孩子，必须让全部孩子为大，因此求和。不同孩子叶集不交，可以独立安排后相加。

全部有m-x+1个大数字。能否保证根结果至少x，等价于这些大数字够不够high[root]个；用足最少要求后，剩余大数字放到其它叶子不会使结果降低。最大阈值便是m-high[root]+1。

对结果至多为x同样计数。令low[u]为强制结果为小的最少小叶子数。最大化层必须所有孩子都小，因此求和；最小化层只需一个小孩子，因此取最小。小数字有x个，所以最小可达值为low[root]。

根深度为零，是最大层；沿边每走一步交换角色，不按结点编号或子树高度判断。逆着显式遍历次序计算两组数。即使树只有根一个叶子，也得到最大与最小都为一。''',
    r'''int n;cin>>n;vector<vector<int>>child(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;child[u-1].push_back(v-1);}
vector<int>depth(n),order{0};for(size_t i=0;i<order.size();++i){int u=order[i];for(int v:child[u]){depth[v]=depth[u]+1;order.push_back(v);}}
vector<int>high(n),low(n);int leaves=0;for(int i=n-1;i>=0;--i){int u=order[i];if(child[u].empty()){high[u]=low[u]=1;++leaves;continue;}
    int sumHigh=0,sumLow=0,minHigh=n,minLow=n;for(int v:child[u]){sumHigh+=high[v];sumLow+=low[v];minHigh=min(minHigh,high[v]);minLow=min(minLow,low[v]);}
    if(depth[u]%2==0){high[u]=minHigh;low[u]=sumLow;}else{high[u]=sumHigh;low[u]=minLow;}
}cout<<leaves-high[0]+1<<' '<<low[0]<<'\n';''',
    '叶子数量不一定是n；按深度奇偶轮流取最大最小；计数是所需的大／小叶子数；先输出最大，再输出最小。',
    r'时间与空间均为 $O(n)$，不枚举数字排列。',tags=['树形 DP','博弈论'],lessons=T+['dp','games'])

add('CF765E','对每个方向求能否折成单臂，再枚举最后的分叉点',
    '一次操作可把同一结点上两条等长、无额外分支的叶端路径合并为一条。问能否折成路径；若可，输出最少边数。',
    r'''有向消息u到v表示去掉uv后，u侧能否折成从v伸出的单臂及长度。u其它方向的消息必须全部合法且等长，消息才为该长度加一；没有其它方向时为一。两趟遍历得到所有方向。某点全部臂合法、不同长度至多两种时可折成路径，长为不同臂长之和，再不断除去二因子；对所有合法点取最小。''',
    r'''同一点伸出长度一、二、二的三条单臂，可先合并两条长度二的臂，剩下一加二的三边路径。长度一、二、三则没有任何一对可合并，三叉不能消去。必须比较整条叶端路径长度，不能只比较孩子深度或子树点数。

先研究一条边uv的u侧。希望这一侧能独立折成从v伸出的一条单臂，此时v当作外部连接点。u的各个孩子方向都必须先成为单臂；若它们长度相同，就能两两合并到只剩一条，再加uv，长度增加一。若有两个不同长度，它们无法在u处合并，便不能对外成为单臂。没有其它方向时，u是叶子，消息长度为一。

消息可能是不合法的负一。任取根先从孩子到父亲递推，再从父亲到孩子递推。对点u汇总所有邻居发来的消息：用有序映射记录合法长度的出现次数，另记不合法数。计算u发给某孩子的消息时，只暂时扣掉该孩子传来的那一项；其余消息无不合法且至多一种长度，才能传出长度加一。

若u作为最后仍有分叉的结点，那么它的每个方向都必须能先独立折成单臂：u尚有至少三个方向时，经过u的路径本身带着额外邻边，不能参与别处的叶端折叠。所有方向合法以后，相同长度的臂合并到只剩一条。不同长度若超过两种，仍有分叉；若为两种a、b，得到长a+b的路径；若只有一种a，可合并到一条长a的路径。

这覆盖所有可能成功的过程：看某个成功过程第一次变成路径前最后一个分叉点，前面的折叠必已使它每个原始方向成为可合并的单臂。原树本来就是路径时也包含在这些候选中。因此枚举全部u，不需要预先猜这个位置。

一条完整路径还能怎样缩短？只有在恰好中点有两条等长叶端臂时可继续折，长度减半；奇数长没有这样的中点结点，不能再折。于是每个候选长度反复除二直到为奇数，再取最小。不合法消息不能拿来参与长度相加。两趟遍历和消息都用显式次序，二十万点长链不会爆栈。''',
    r'''int n;cin>>n;vector<vector<int>>edge(n);vector<int>to;for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;int id=to.size();to.push_back(v);to.push_back(u);edge[u].push_back(id);edge[v].push_back(id^1);}
vector<int>parentEdge(n,-1),order{0},message(to.size(),-1);parentEdge[0]=-2;
for(size_t i=0;i<order.size();++i){int u=order[i];for(int e:edge[u])if(e!=parentEdge[u]){int v=to[e];parentEdge[v]=e^1;order.push_back(v);}}
for(int i=n-1;i>0;--i){int u=order[i],length=0;bool ok=true;
    for(int e:edge[u])if(e!=parentEdge[u]){int value=message[e^1];if(value<0||(length&&length!=value))ok=false;length=value;}
    message[parentEdge[u]]=ok?length+1:-1;
}
int answer=INT_MAX;for(int u:order){map<int,int>frequency;int invalid=0;
    for(int e:edge[u]){int value=message[e^1];if(value<0)++invalid;else ++frequency[value];}
    if(!invalid&&frequency.size()<=2){int length=0;for(auto [value,count]:frequency)length+=value;while(length%2==0)length/=2;answer=min(answer,length);}
    for(int e:edge[u])if(e!=parentEdge[u]){int value=message[e^1];if(value<0)--invalid;else if(--frequency[value]==0)frequency.erase(value);
        message[e]=(!invalid&&frequency.size()<=1)?1+(frequency.empty()?0:frequency.begin()->first):-1;
        if(value<0)++invalid;else ++frequency[value];
    }
}cout<<(answer==INT_MAX?-1:answer)<<'\n';''',
    '消息包含连接当前点的一条边；非根单臂只能有一种孩子长度；最终点允许两种；相同长度可合并多次；完整路径最后去掉二因子。',
    r'两趟遍历的映射操作总计 $O(n\log n)$ 时间，邻接、消息及映射峰值空间 $O(n)$。',tags=['树形 DP','贪心'],lessons=T+['dp','maps','bindings'])

add('CF980E','从最大编号倒着保留，用倍增计算必须补齐的祖先',
    '删除k个树结点，剩余结点需连通，保留编号i贡献二的i次方，要求总贡献最大，按升序输出删除编号；n最多一百万。',
    r'''最高编号的一位胜过全部更小位，所以从大到小贪心。以n为根并先保留n；尝试保留i时，必须把到当前核心的整段祖先链补齐。倍增找到最高未保留祖先，算需要点数；剩余额度够就沿链标记，否则跳过。每点只标一次，输出未标点。''',
    r'''二的i次方大于一到i-1所有二次幂之和。因此比较两个保留集合时，最大的不同编号在哪一边，哪一边就更优。无需真的保存这些大整数，只需优先决定大编号。

保留数量固定为n-k，且总能保留编号n：从n开始沿相邻结点扩展即可得到任意所需大小的连通集合。以n为根，保留集合始终包含根且向祖先封闭。若要加入i，必须加入i到已有集合第一次接触位置之间的整条链。

倍增表up[j][u]表示二的j次方祖先。若这个祖先还没保留，由于核心向祖先封闭，中间结点也都未保留，可以整段向上跳。由大到小找出最高的未保留点v，链上所需新点数就是depth[i]-depth[v]+1。

若点数不超过余额，加入整条链一定能让当前最大尚未决定的编号为一，优先于任何小编号组合。若点数超过余额，任何满足此前决定的连通集合都容不下i，必须跳过。后来核心即使向这条链增长，省掉几个所需点就至少消耗几个余额，不能把一个此前放不下的大编号重新变得可行。

加入以后沿父亲逐点标记，直到遇到已保留点。总共最多标记n次；算链长度才需要倍增，而非对每次尝试都线性爬完整链。过程能补到恰好n-k个：只要还差点数，核心边界的一个未保留相邻点只需一个额度，不会被错误排除。最后按原编号扫描未保留点，自然升序。''',
    r'''int n,k;cin>>n>>k;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
Lift lift(g,n-1);vector<char>kept(n);kept[n-1]=true;int remaining=n-k-1;
for(int i=n-2;i>=0&&remaining;--i){if(kept[i])continue;int v=i;
    for(int j=lift.levels-1;j>=0;--j)if(!kept[lift.up[j][v]])v=lift.up[j][v];
    int need=lift.depth[i]-lift.depth[v]+1;if(need>remaining)continue;remaining-=need;
    for(int u=i;!kept[u];u=lift.up[0][u])kept[u]=true;
}
bool first=true;for(int u=0;u<n;++u)if(!kept[u]){if(!first)cout<<' ';first=false;cout<<u+1;}cout<<'\n';''',
    '保留数量是n-k；最高编号作根；加入点必须补齐祖先链；倍增统计，逐点标记总共线性；输出的是删除点且升序。',
    r'预处理和所有贪心尝试 $O(n\log n)$ 时间，空间 $O(n\log n)$；不计算巨大二次幂。',tags=['贪心','倍增'],lessons=T+['binary-lifting','greedy'],declarations=LIFT)

add('CF1278E','孩子左端点先排一遍，再逆序展开子树',
    '为树的每个结点构造一个区间，全部端点恰用一至2n一次。两区间交叉而互不包含，当且仅当树上两点相邻。',
    r'''根左端点先取一。处理u时，先依次给所有孩子分配左端点，再分配u的右端点，最后按孩子的逆序处理各子树。父子端点形成l[u]<l[v]<r[u]<r[v]；兄弟按左端点先后、右端点反序，形成包含，其他非亲子为包含或分离。用栈实现逆序展开。''',
    r'''根有两个孩子时，先分配根左端点一，再给两个孩子左端点二、三，随后分配根右端点四。后处理左端点二的那棵子树，意味着它的右端点也更晚，于是两个孩子区间相互包含，不会被误判为树边。

具体保持计数器timer。根left先取下一个数；处理u时，先按某个固定顺序为各孩子设置left，接着设置right[u]，再把孩子按同一顺序压栈。栈后进先出，实际就会逆序展开孩子。每个点的left和right各分配一次，最终恰好用完一至2n。

看父子u、v：left[u]先有，left[v]在right[u]之前分配，right[v]在处理v时才分配，因此严格交错

$$left[u]<left[v]<right[u]<right[v].$$

看不同孩子v、w，若left[v]<left[w]，则w的整棵子树先处理完，再处理v。right[w]<right[v]，所以w的区间被v包含；w的后代也全部位于v区间内。v的后代端点则要等w子树全部结束后才开始分配，与w子树的区间分离。

再看祖孙但非父子u、z：z的left只在处理u的孩子时才产生，此时right[u]已经分配完，所以两者区间分离。以上覆盖不同关系，恰好只有父子区间严格交叉。

这是区间端点的相对次序构造，不是把普通DFS的进入、离开时刻直接拿来；普通DFS会让所有祖先区间包含后代，反而连父子边都没有。五十万点使用显式栈，避免递归栈耗尽。''',
    r'''int n;cin>>n;vector<vector<int>>g(n);for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<int>parent(n,-1),left(n),right(n),stack{0};parent[0]=0;int timer=0;left[0]=++timer;
while(!stack.empty()){int u=stack.back();stack.pop_back();
    for(int v:g[u])if(v!=parent[u]){parent[v]=u;left[v]=++timer;}
    right[u]=++timer;
    for(int v:g[u])if(v!=parent[u])stack.push_back(v);
}for(int u=0;u<n;++u)cout<<left[u]<<' '<<right[u]<<'\n';''',
    '全部端点恰好一次；父子严格交错；兄弟相互包含；逆序展开与先分配左端点的次序一致配合；普通DFS区间不能直接套用。',
    r'时间与空间均为 $O(n)$。',tags=['构造','DFS 序'],lessons=T+['construction','queue-stack'],checker='tree_overlap_intervals')
