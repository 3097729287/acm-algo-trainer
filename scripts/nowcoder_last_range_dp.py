"""Heavy-light path moments and offline stack lifetimes for xor-cost knapsack."""
from nowcoder_editorials import CONTENT,add,read
from nowcoder_euler_support import EULER
from nowcoder_tree_queries_more import SQUARE

SUM_QUERY=r'''
    long long querySum(int u,int l,int r,int ql,int qr) {
        if(ql<=l && r<=qr)return sum[u];
        push(u,l,r);int mid=(l+r)/2;long long value=0;
        if(ql<=mid)value+=querySum(u*2,l,mid,ql,qr);
        if(qr>mid)value+=querySum(u*2+1,mid+1,r,ql,qr);
        return value%mod;
    }
'''
MOMENT=SQUARE.replace('23333','1000000007').replace('\n};',SUM_QUERY+'\n};')


def run():
    existing=read(CONTENT/'reviewed.json')
    def put(n,*args,**kwargs):
        if f'nowcoder-global::{n}' not in existing:add(n,*args,**kwargs)
    put(18939,2300,['重链剖分','线段树','平方和'],'子树加、路径加，查询路径所有不同节点对的权值乘积和。',
        '重链剖分使每条重链在DFS序连续，整棵子树也连续。路径被拆成O(log n)个重链区间，子树是一个区间，因此两种加法都交给区间加线段树。\n\n节点维护S=Σa、Q=Σa²；长len区间加v时Q+=2vS+len*v²，随后S+=len*v。路径查询分别累加各段S、Q，所求无序不同节点对乘积和=(S²−Q)/2，模P下乘500000004。若把查询拆段，必须先合并全部S再平方，这样才包含跨段节点对。\n\n父子关系、重儿子、重链编号均由显式栈和逆序计算，避免十万长链递归遍历。',
        r'''int n,m;cin >> n >> m;vector<long long> weight(n+1);for(int i=1;i<=n;i++)cin >> weight[i];EulerTree tree(n);for(int i=1;i<n;i++){int u,v;cin >> u >> v;tree.add(u,v);}tree.root(1);vector<int> size(n+1,1),heavy(n+1),head(n+1);size[0]=0;for(int i=n-1;i>=0;i--){int u=tree.order[i];for(int v:tree.edge[u])if(tree.parent[v]==u){size[u]+=size[v];if(size[v]>size[heavy[u]])heavy[u]=v;}}vector<pair<int,int>> stack={{1,1}};int timer=0;vector<long long> a(n+1);while(!stack.empty()){auto [start,h]=stack.back();stack.pop_back();for(int u=start;u;u=heavy[u]){head[u]=h;tree.in[u]=++timer;a[timer]=weight[u];for(int v:tree.edge[u])if(tree.parent[v]==u && v!=heavy[u])stack.push_back({v,v});}}SquareTree segment(a);const long long mod=1000000007;auto path=[&](int u,int v,auto process){while(head[u]!=head[v]){if(tree.depth[head[u]]<tree.depth[head[v]])swap(u,v);process(tree.in[head[u]],tree.in[u]);u=tree.parent[head[u]];}if(tree.depth[u]>tree.depth[v])swap(u,v);process(tree.in[u],tree.in[v]);};while(m--){int op,u;cin >> op >> u;if(op==1){long long value;cin >> value;segment.change(1,1,n,tree.in[u],tree.in[u]+size[u]-1,value);}else if(op==2){int v;long long value;cin >> v >> value;path(u,v,[&](int l,int r){segment.change(1,1,n,l,r,value);});}else{int v;cin >> v;long long sum=0,square=0;path(u,v,[&](int l,int r){sum=(sum+segment.querySum(1,1,n,l,r))%mod;square=(square+segment.query(1,1,n,l,r))%mod;});cout << (sum*sum%mod-square+mod)%mod*500000004%mod << '\n';}}''',
        '重儿子比较前size[0]应为0；这里空儿子0初始化后需显式清零。单点路径的不同点对数为0。',
        declarations=EULER+MOMENT,complexity=r'子树修改 $O(\log n)$，路径操作 $O(\log² n)$，空间 $O(n)$。')
    put(236249,2300,['离线分治','异或背包','时间线段树'],'堆栈增删石子堆，每天最小代价丢若干堆使Nim和为0。',
        '当前总异或为X，Bob获胜要求保留堆异或0，等价于丢弃子集异或X。令dp[s]为丢弃子集异或s的最小代价。添加(a,b)对应0/1异或背包，按x与x xor a成对更新，可原地同时使用两份旧值。\n\n删除不能直接撤销最小值，所以先读完操作，把每个ADD到对应DEL之前的存在期记为时间区间。将物品加入覆盖其存在期的时间线段树。DFS进入节点时复制父DP，加入本节点物品；叶子查询dp[当日总异或]。兄弟节点各用父表，天然恢复删除前状态。\n\n值小于2^14，DP最多16384项。若dp[a]≤b，新增物品可由已有更便宜的同异或子集替代，整件更新可以安全跳过；每节点按b升序加入，让这一支配剪枝尽早生效。代价为正，即使替代集合与原方案重叠，抵消重复元素只会更便宜。',
        r'''int n;cin >> n;struct Item{int value,cost,left,right;};vector<Item> item;vector<int> stack,totalXor(n);int current=0,maximum=0;for(int day=0;day<n;day++){string op;cin >> op;if(op=="ADD"){int a,b;cin >> a >> b;item.push_back({a,b,day,n-1});stack.push_back(item.size()-1);current^=a;maximum=max(maximum,a);}else{int id=stack.back();stack.pop_back();item[id].right=day-1;current^=item[id].value;}totalXor[day]=current;}int states=1;while(states<=maximum)states<<=1;vector<vector<int>> event(4*n+4);auto insert=[&](auto &&self,int u,int l,int r,int ql,int qr,int id)->void{if(ql<=l && r<=qr){event[u].push_back(id);return;}int mid=(l+r)/2;if(ql<=mid)self(self,u*2,l,mid,ql,qr,id);if(qr>mid)self(self,u*2+1,mid+1,r,ql,qr,id);};for(int id=0;id<(int)item.size();id++)insert(insert,1,0,n-1,item[id].left,item[id].right,id);for(auto &row:event)sort(row.begin(),row.end(),[&](int a,int b){return item[a].cost<item[b].cost;});const int inf=1000000000;vector<int> initial(states,inf),answer(n);initial[0]=0;auto solve=[&](auto &&self,int u,int l,int r,const vector<int> &parent)->void{vector<int> dp=parent;for(int id:event[u]){auto it=item[id];if(dp[it.value]<=it.cost)continue;int pivot=1;while(pivot<=it.value/2)pivot<<=1;for(int block=0;block<states;block+=2*pivot)for(int offset=0;offset<pivot;offset++){int x=block+offset,y=x^it.value,oldX=dp[x],oldY=dp[y];dp[x]=min(oldX,oldY+it.cost);dp[y]=min(oldY,oldX+it.cost);}}if(l==r)answer[l]=dp[totalXor[l]];else{int mid=(l+r)/2;self(self,u*2,l,mid,dp);self(self,u*2+1,mid+1,r,dp);}};solve(solve,1,0,n-1,initial);for(int x:answer)cout << x << '\n';''',
        '当天DEL后该堆已不存在，生存区间右端为删除日−1。两个异或成对状态必须保存旧值后一起更新，避免同件重复使用。',
        complexity=r'令U≤2^14、A为ADD次数，最坏时间 $O((A\log n+n)U)$，空间 $O(A\log n+U\log n+n)$；支配剪枝改善实际耗时，不改变最坏界。')


if __name__=='__main__':run()
