"""Unregistered, independently checked programs for the Fenwick unit."""
CODE={};DECL={}
BIT=r'''
struct Fenwick {
    int n; vector<int> tree;
    explicit Fenwick(int size):n(size),tree(size+1){}
    void add(int p,int v){for(;p<=n;p+=p&-p) tree[p]+=v;}
    int sum(int p) const {int value=0;for(;p;p-=p&-p) value+=tree[p];return value;}
    int kth(int k) const {int p=0;for(int step=1<<20;step;step>>=1){int q=p+step;if(q<=n&&tree[q]<k){p=q;k-=tree[q];}}return p+1;}
};
'''
CODE['CF44C']=r'''
int n,m;cin>>n>>m;vector<int>difference(n+2);
for(int i=0,l,r;i<m;++i){cin>>l>>r;++difference[l];--difference[r+1];}
int count=0;for(int day=1;day<=n;++day){count+=difference[day];if(count!=1){cout<<day<<' '<<count<<'\n';return 0;}}
cout<<"OK\n";
'''
CODE['P1714']=r'''
int n,m;cin>>n>>m;vector<long long>prefix(n+1);deque<int>queue;queue.push_back(0);long long answer=LLONG_MIN;
for(int i=1;i<=n;++i){int x;cin>>x;prefix[i]=prefix[i-1]+x;while(queue.front()<i-m) queue.pop_front();answer=max(answer,prefix[i]-prefix[queue.front()]);while(!queue.empty()&&prefix[queue.back()]>=prefix[i]) queue.pop_back();queue.push_back(i);}
cout<<answer<<'\n';
'''
DECL['P3531']=BIT
CODE['P3531']=r'''
int n;string a,b;cin>>n>>a>>b;array<vector<int>,26>positions;array<int,26>next={};
for(int i=0;i<n;++i) positions[b[i]-'A'].push_back(i+1);
Fenwick bit(n);long long answer=0;for(int i=0;i<n;++i){int letter=a[i]-'A',p=positions[letter][next[letter]++];answer+=i-bit.sum(p);bit.add(p,1);}
cout<<answer<<'\n';
'''
CODE['P2161']=r'''
int n;cin>>n;set<pair<int,int>>intervals;
while(n--){char op;cin>>op;if(op=='B'){cout<<intervals.size()<<'\n';continue;}int l,r;cin>>l>>r;auto it=intervals.lower_bound({l,INT_MIN});if(it!=intervals.begin()&&prev(it)->second>=l) --it;int removed=0;while(it!=intervals.end()&&it->first<=r){it=intervals.erase(it);++removed;}intervals.insert({l,r});cout<<removed<<'\n';}
'''
DECL['P4939']=BIT
CODE['P4939']=r'''
int n,m;cin>>n>>m;struct Command{int op,l,r;};vector<Command>commands;vector<int>coordinates;
for(int i=0;i<m;++i){int op,l,r=0;cin>>op>>l;if(op==0){cin>>r;coordinates.push_back(l);coordinates.push_back(r+1);}commands.push_back({op,l,r});}
sort(coordinates.begin(),coordinates.end());coordinates.erase(unique(coordinates.begin(),coordinates.end()),coordinates.end());Fenwick bit(coordinates.size());
for(auto [op,l,r]:commands){if(op==0){int left=lower_bound(coordinates.begin(),coordinates.end(),l)-coordinates.begin()+1,right=lower_bound(coordinates.begin(),coordinates.end(),r+1)-coordinates.begin()+1;bit.add(left,1);bit.add(right,-1);}else cout<<bit.sum(upper_bound(coordinates.begin(),coordinates.end(),l)-coordinates.begin())<<'\n';}
'''
DECL['P5367']=BIT
CODE['P5367']=r'''
const long long mod=998244353;int n;cin>>n;vector<long long>factorial(n+1,1);for(int i=1;i<=n;++i) factorial[i]=factorial[i-1]*i%mod;
Fenwick bit(n);for(int i=1;i<=n;++i) bit.tree[i]=i&-i;
long long answer=1;for(int i=0,x;i<n;++i){cin>>x;answer=(answer+bit.sum(x-1)*factorial[n-i-1])%mod;bit.add(x,-1);}cout<<answer<<'\n';
'''
CODE['P7149']=r'''
int n;cin>>n;vector<pair<int,int>>points(n);vector<int>ys;for(auto &[x,y]:points){cin>>x>>y;ys.push_back(y);}sort(points.begin(),points.end());sort(ys.begin(),ys.end());
int side=n+1;vector<int>prefix(side*side),rank(n);for(int i=0;i<n;++i){rank[i]=lower_bound(ys.begin(),ys.end(),points[i].second)-ys.begin()+1;prefix[(i+1)*side+rank[i]]=1;}
for(int x=1;x<=n;++x) for(int y=1;y<=n;++y) prefix[x*side+y]+=prefix[(x-1)*side+y]+prefix[x*side+y-1]-prefix[(x-1)*side+y-1];
auto count=[&](int left,int right,int low,int high){return prefix[right*side+high]-prefix[left*side+high]-prefix[right*side+low]+prefix[left*side+low];};
long long answer=1;for(int left=0;left<n;++left) for(int right=left;right<n;++right){int low=min(rank[left],rank[right]),high=max(rank[left],rank[right]);long long bottom=count(left,right+1,0,low),top=count(left,right+1,high-1,n);answer+=bottom*top;}
cout<<answer<<'\n';
'''
DECL['P10235']=BIT
CODE['P10235']=r'''
int tests;cin>>tests;while(tests--){int n,k;cin>>n>>k;vector<int>a(n),values;for(int &x:a) cin>>x;values=a;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());for(int &x:a) x=lower_bound(values.begin(),values.end(),x)-values.begin()+1;
Fenwick total(values.size());long long high=0;for(int i=0;i<n;++i){high+=i-total.sum(a[i]);total.add(a[i],1);}
auto feasible=[&](long long limit){Fenwick bit(values.size());int segments=1,left=0;long long inversions=0;for(int i=0;i<n;++i){long long added=i-left-bit.sum(a[i]);if(inversions+added>limit){if(++segments>k) return false;while(left<i) bit.add(a[left++],-1);inversions=0;added=0;}inversions+=added;bit.add(a[i],1);}return true;};
long long low=0;while(low<high){long long middle=(low+high)/2;if(feasible(middle)) high=middle;else low=middle+1;}cout<<low<<'\n';}
'''
CODE['P14521']=r'''
int n,q;cin>>n>>q;const long long bound=1000000000000000000LL;vector<int>parent(n+1);vector<long long>l(n+1),r(n+1),delta(n+1),offset(n+1),low(n+1),high(n+1);vector<char>valid(n+1);
for(int i=2;i<=n;++i) cin>>parent[i]>>l[i]>>r[i];for(int i=1;i<=n;++i){char op;long long a;cin>>op>>a;delta[i]=op=='+'?a:-a;}
valid[1]=true;low[1]=-bound;high[1]=bound;offset[1]=delta[1];vector<long long>starts={-bound},ends={bound};
for(int i=2;i<=n;++i){int p=parent[i];if(!valid[p]) continue;low[i]=max(low[p],l[i]-offset[p]);high[i]=min(high[p],r[i]-offset[p]);if(low[i]>high[i]) continue;valid[i]=true;offset[i]=offset[p]+delta[i];starts.push_back(low[i]);ends.push_back(high[i]);}
sort(starts.begin(),starts.end());sort(ends.begin(),ends.end());while(q--){long long x;cin>>x;cout<<(upper_bound(starts.begin(),starts.end(),x)-starts.begin())-(lower_bound(ends.begin(),ends.end(),x)-ends.begin())<<'\n';}
'''
DECL['CF961E']=BIT
CODE['CF961E']=r'''
int n;cin>>n;vector<int>a(n+1),order(n);for(int i=1;i<=n;++i){cin>>a[i];order[i-1]=i;}sort(order.begin(),order.end(),[&](int x,int y){return a[x]>a[y];});
Fenwick bit(n);int next=0;long long answer=0;for(int i=n;i>=1;--i){while(next<n&&a[order[next]]>=i) bit.add(order[next++],1);int right=min(n,a[i]);if(right>i) answer+=bit.sum(right)-bit.sum(i);}cout<<answer<<'\n';
'''
DECL['P1966']=BIT
CODE['P1966']=r'''
int n;cin>>n;vector<pair<int,int>>a(n),b(n);for(int i=0;i<n;++i){cin>>a[i].first;a[i].second=i;}for(int i=0;i<n;++i){cin>>b[i].first;b[i].second=i;}sort(a.begin(),a.end());sort(b.begin(),b.end());vector<int>target(n);for(int i=0;i<n;++i) target[a[i].second]=b[i].second+1;
Fenwick bit(n);long long answer=0;for(int i=0;i<n;++i){answer+=i-bit.sum(target[i]);bit.add(target[i],1);}cout<<answer%99999997<<'\n';
'''
DECL['P3149']=BIT
CODE['P3149']=r'''
int n,m;cin>>n>>m;vector<int>a(n),values;for(int &x:a) cin>>x;values=a;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());for(int &x:a) x=lower_bound(values.begin(),values.end(),x)-values.begin()+1;
Fenwick bit(values.size());vector<long long>coefficient(values.size()+1);long long total=0;for(int i=n-1;i>=0;--i){int smaller=bit.sum(a[i]-1);coefficient[a[i]]+=smaller;total+=smaller;bit.add(a[i],1);}for(int i=1;i<(int)coefficient.size();++i) coefficient[i]+=coefficient[i-1];
cout<<total<<'\n';int threshold=0;while(m--){int k;cin>>k;threshold=max(threshold,a[k-1]);cout<<total-coefficient[threshold]<<'\n';}
'''
CODE['P4064']=r'''
int tests;cin>>tests;while(tests--){int n,m,k;long long increment;cin>>n>>m>>k>>increment;vector<long long>a(n+1);for(int i=1;i<=n;++i) cin>>a[i];vector<pair<int,int>>intervals(m);for(auto &[l,r]:intervals) cin>>l>>r;sort(intervals.begin(),intervals.end());
auto feasible=[&](long long target){vector<int>expiration(n+2);priority_queue<int>ends;int next=0,active=0,used=0;for(int i=1;i<=n;++i){active+=expiration[i];while(next<m&&intervals[next].first<=i) ends.push(intervals[next++].second);long long shortage=target-a[i]-increment*active;if(shortage<=0) continue;long long need=(shortage+increment-1)/increment;if(used+need>k) return false;while(need--){while(!ends.empty()&&ends.top()<i) ends.pop();if(ends.empty()) return false;int r=ends.top();ends.pop();++active;++used;--expiration[r+1];}}return true;};
long long low=*min_element(a.begin()+1,a.end()),high=low+k*increment;while(low<high){long long middle=(low+high+1)/2;if(feasible(middle)) low=middle;else high=middle-1;}cout<<low<<'\n';}
'''
DECL['P5677']=BIT
CODE['P5677']=r'''
int n,m;cin>>n>>m;vector<pair<int,int>>values(n);for(int i=0;i<n;++i){cin>>values[i].first;values[i].second=i+1;}sort(values.begin(),values.end());vector<pair<int,int>>edges;
auto add=[&](int i,int j){int l=min(values[i].second,values[j].second),r=max(values[i].second,values[j].second);edges.push_back({r,l});};
for(int i=0;i<n;++i){long long left=i?1LL*values[i].first-values[i-1].first:LLONG_MAX,right=i+1<n?1LL*values[i+1].first-values[i].first:LLONG_MAX;if(i&&left<=right) add(i,i-1);if(i+1<n&&right<=left) add(i,i+1);}sort(edges.begin(),edges.end());
struct Query{int l,r,id;};vector<Query>queries(m);for(int i=0;i<m;++i){cin>>queries[i].l>>queries[i].r;queries[i].id=i+1;}sort(queries.begin(),queries.end(),[](Query a,Query b){return a.r<b.r;});Fenwick bit(n);int next=0;long long answer=0;for(auto [l,r,id]:queries){while(next<(int)edges.size()&&edges[next].first<=r){bit.add(edges[next].second,1);++next;}answer+=1LL*(next-bit.sum(l-1))*id;}cout<<answer<<'\n';
'''
CODE['P8201']=r'''
int n,m;cin>>n>>m;const int levels=20;vector<int>weight(n+1),values;for(int i=1;i<=n;++i){cin>>weight[i];values.push_back(weight[i]);}sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());vector<int>rank(n+1);for(int i=1;i<=n;++i) rank[i]=lower_bound(values.begin(),values.end(),weight[i])-values.begin();
vector<int>head(n+1,-1),to(2*(n-1)),next(2*(n-1));int edges=0;auto add=[&](int x,int y){to[edges]=y;next[edges]=head[x];head[x]=edges++;};for(int i=1,x,y;i<n;++i){cin>>x>>y;add(x,y);add(y,x);}
vector<array<int,levels>>up(n+1);vector<int>depth(n+1),prefix(n+1),order={1};depth[1]=1;prefix[1]=weight[1];for(int at=0;at<(int)order.size();++at){int u=order[at];for(int e=head[u];e!=-1;e=next[e]){int v=to[e];if(v==up[u][0]) continue;up[v][0]=u;depth[v]=depth[u]+1;prefix[v]=prefix[u]^weight[v];for(int j=1;j<levels;++j) up[v][j]=up[up[v][j-1]][j-1];order.push_back(v);}}
auto lca=[&](int a,int b){if(depth[a]<depth[b]) swap(a,b);int difference=depth[a]-depth[b];for(int j=0;j<levels;++j) if(difference>>j&1) a=up[a][j];if(a==b) return a;for(int j=levels-1;j>=0;--j) if(up[a][j]!=up[b][j]){a=up[a][j];b=up[b][j];}return up[a][0];};
vector<int>queryHead(n+1,-1),queryId,queryNext,target(m),minimumDepth(m);vector<char>answer(m);queryId.reserve(2*m);queryNext.reserve(2*m);auto attach=[&](int u,int id){queryId.push_back(id);queryNext.push_back(queryHead[u]);queryHead[u]=queryId.size()-1;};
for(int i=0,a,b,k;i<m;++i){cin>>a>>b>>k;int c=lca(a,b),need=prefix[a]^prefix[b]^weight[c]^k;auto it=lower_bound(values.begin(),values.end(),need);if(it==values.end()||*it!=need) continue;target[i]=it-values.begin();minimumDepth[i]=depth[c];attach(a,i);attach(b,i);}
vector<int>last(values.size()),saved(n+1),stack={1};while(!stack.empty()){int event=stack.back();stack.pop_back();if(event<0){int u=-event;last[rank[u]]=saved[u];continue;}int u=event;saved[u]=last[rank[u]];last[rank[u]]=u;for(int e=queryHead[u];e!=-1;e=queryNext[e]){int id=queryId[e],v=last[target[id]];if(v&&depth[v]>=minimumDepth[id]) answer[id]=true;}stack.push_back(-u);for(int e=head[u];e!=-1;e=next[e]) if(to[e]!=up[u][0]) stack.push_back(to[e]);}
for(char yes:answer) cout<<(yes?"Yes":"No")<<'\n';
'''
DECL['P11656']=r'''
struct SuffixMinimum {
    int n;vector<int>tree;
    explicit SuffixMinimum(int size):n(size),tree(size+1,1000000000){}
    void add(int p,int value){for(;p;p-=p&-p) tree[p]=min(tree[p],value);}
    int query(int p) const {int value=1000000000;for(;p<=n;p+=p&-p) value=min(value,tree[p]);return value;}
};
'''
CODE['P11656']=r'''
int n;cin>>n;vector<int>distance(n+1);for(int i=1;i<=n;++i) cin>>distance[i];for(int i=1,power;i<=n;++i) cin>>power;
SuffixMinimum previous(n+1),right(n);previous.add(1,0);int last=0;
for(int i=1;i<=n;++i){right.add(min(n,i+distance[i]-1),last+1);int left=max(0,i-distance[i]);int current=min(previous.query(left+1)+1,right.query(i));previous.add(i+1,current);last=current;}cout<<last<<'\n';
'''
DECL['P14379']=BIT
CODE['P14379']=r'''
int n,q;cin>>n>>q;vector<int>a(n+1);Fenwick ones(n),twos(n);long long noOne=0,twoFree=0;int gap=0,count=0;
auto choose=[](long long x){return x*(x-1)/2;};
for(int i=1;i<=n;++i){cin>>a[i];if(a[i]==1){ones.tree[i]=1;noOne+=choose(gap);gap=0;++count;}else ++gap;if(a[i]==2){twos.tree[i]=1;twoFree+=choose(count);count=0;}}
noOne+=choose(gap);twoFree+=choose(count);for(int i=1;i<=n;++i){int j=i+(i&-i);if(j<=n){ones.tree[j]+=ones.tree[i];twos.tree[j]+=twos.tree[i];}}
int numberOne=ones.sum(n),numberTwo=twos.sum(n);
auto neighbors=[&](const Fenwick &bit,int total,int p,bool present){int before=bit.sum(p-1);int l=before?bit.kth(before):0;int nextRank=before+1+present;int r=nextRank<=total?bit.kth(nextRank):n+1;return pair<int,int>{l,r};};
auto change=[&](int p,int value,int delta){
    if(value==1){auto [l,r]=neighbors(ones,numberOne,p,delta==-1);long long split=choose(p-l-1)+choose(r-p-1)-choose(r-l-1);noOne+=delta*split;auto [left,right]=neighbors(twos,numberTwo,p,false);int c=ones.sum(right-1)-ones.sum(left);twoFree+=delta==1?c:-(c-1);ones.add(p,delta);numberOne+=delta;}
    else if(value==2){auto [l,r]=neighbors(twos,numberTwo,p,delta==-1);int middle=ones.sum(p);long long left=middle-ones.sum(l),right=ones.sum(r-1)-middle;twoFree-=delta*left*right;twos.add(p,delta);numberTwo+=delta;}
};
while(q--){int p,value;cin>>p>>value;int oldCategory=min(a[p],3),newCategory=min(value,3);if(oldCategory!=newCategory){change(p,oldCategory,-1);change(p,newCategory,1);}a[p]=value;cout<<choose(n)-noOne-twoFree<<'\n';}
'''
DECL['CF1194E']=BIT
CODE['CF1194E']=r'''
int n;cin>>n;struct Horizontal{int y,l,r;};struct Vertical{int x,low,high;};vector<Horizontal>h;vector<Vertical>v;vector<int>xs;
for(int i=0,x1,y1,x2,y2;i<n;++i){cin>>x1>>y1>>x2>>y2;if(y1==y2) h.push_back({y1,min(x1,x2),max(x1,x2)});else{v.push_back({x1,min(y1,y2),max(y1,y2)});xs.push_back(x1);}}sort(h.begin(),h.end(),[](Horizontal a,Horizontal b){return a.y<b.y;});sort(v.begin(),v.end(),[](Vertical a,Vertical b){return a.high<b.high;});sort(xs.begin(),xs.end());xs.erase(unique(xs.begin(),xs.end()),xs.end());
long long answer=0;for(int bottom=0;bottom<(int)h.size();++bottom){Fenwick bit(xs.size());for(auto segment:v) if(segment.low<=h[bottom].y&&h[bottom].y<=segment.high) bit.add(lower_bound(xs.begin(),xs.end(),segment.x)-xs.begin()+1,1);int expired=0;for(int top=bottom+1;top<(int)h.size();++top){while(expired<(int)v.size()&&v[expired].high<h[top].y){auto segment=v[expired++];if(segment.low<=h[bottom].y&&h[bottom].y<=segment.high) bit.add(lower_bound(xs.begin(),xs.end(),segment.x)-xs.begin()+1,-1);}if(h[top].y==h[bottom].y) continue;int l=max(h[bottom].l,h[top].l),r=min(h[bottom].r,h[top].r);if(l>r) continue;int left=lower_bound(xs.begin(),xs.end(),l)-xs.begin(),right=upper_bound(xs.begin(),xs.end(),r)-xs.begin();long long count=bit.sum(right)-bit.sum(left);answer+=count*(count-1)/2;}}
cout<<answer<<'\n';
'''


from core7_authoring import add
A=['io-basics','basic-control','vector','integer','functions']
F=A+['fenwick']
def emit(pid,title,meaning,brief,detail,pitfalls,complexity,tags,lessons):
    add(pid,title,meaning,brief,detail,CODE[pid],pitfalls,complexity,tags=tags,lessons=lessons,declarations=DECL.get(pid,''),checker='path_value_verdicts' if pid=='P8201' else '')

emit('CF44C','区间差分还原每天人数，顺序找第一次异常',
    '每人负责一个闭区间，要求每天恰好浇水一次；输出最早不符合的天数与当天实际次数，全部正常则输出OK。',
    r'''负责从l到r的一个人，在差分l处加一、r加一处减一。累加差分得到每天总次数，从第一天开始扫描，第一次不是一就输出。次数零和超过一都是错误，不需要分别寻找再比较。''',
    r'''一天的答案等于有多少个值班闭区间包含这一天。要求是恰好一次，既不能遗漏，也不能重复。

把一整段加一记录成两个事件：在左端l开始增加一名值班人，在r的后一天撤销这次增加。于是difference[l]加一，difference[r加一]减一；人数数组多开两格，允许最后一天之后的撤销事件。

从第一天向后维护count，先加当前天差分，再检查count是否为一。这样当前天的左端事件已生效，而当天结束的值班还没撤销，符合闭区间。

发现异常后立即输出天数和count并结束，保证返回最早者。第二个原样例同时存在重复和漏浇，仍应返回第二天的重复，不是优先报告人数为零。

输入虽按值班顺序排列，可能出现相邻区间共用同一天。无需依赖这个顺序或猜测相邻关系，差分直接统计所有贡献。全部天数恰好为一后，才输出大写OK。''',
    '要求恰好一次；两个区间共享端点会重复；r的后一天撤销；先累加再判断；按天数找最早异常；无异常输出大写OK。',
    r'时间 $O(n+m)$，空间 $O(n)$。',['差分','前缀和'],A+['difference','prefix'])

emit('P1714','前缀和减去最近m个合法前缀的最小值',
    '选择至少一块、至多m块连续蛋糕，使幸运值之和最大；幸运值可以全为负数。',
    r'''以i结束的和等于prefix[i]减prefix[j]，其中j从max(0,i减m)到i减一。用单调队列保存这些前缀的最小值：先删除过期下标，查询答案，再把当前前缀加入。当前前缀不能参与本次查询，否则会错误允许空段。答案初始为极小值。''',
    r'''左右端点都枚举会很慢。固定右端i后，选左端l到i的和为prefix[i]减prefix[l减一]。记j为l减一，长度限制给出i减m不大于j，而非空给出j至多i减一。

对当前右端，只需在这些合法j中找最小前缀和。右端每次前进一格，候选范围也向右移动，适合单调队列。

队列下标递增、对应前缀和值严格递增。新前缀更小时，旧的较大或相等前缀不会再优于它：新者既不大，又更晚过期。因此从队尾弹掉这些旧候选。每次查询前还要从队首移走小于i减m的下标。

处理顺序不能交换。先用已存在的前缀更新以i结束的答案，再插入prefix[i]，才能保证选中至少一块。初始化把prefix[0]放入队列，让从第一块开始的段也能计算。

若全部幸运值为负，正确答案是其中最大的单块。把answer初始化为零或先插入当前前缀，都可能得到题目不允许的空段零分。程序使用long long保存前缀与差，并从LLONG_MIN开始更新。

每个前缀只入队一次、从首或尾出队一次，遍历总长度线性。m等于一时比较各单块；m等于n时仍必须选非空段。''',
    '至少一块；j不可等于i；先查再加入当前前缀；i减m仍合法；全负不能初始化零；队列存下标以便过期。',
    r'时间 $O(n)$，空间 $O(n)$。',['前缀和','队列'],A+['prefix','monotone-structures','queue-stack'])

emit('P3531','相同字母按出现次序匹配，再数目标位置的逆序对',
    '两个大写字母串互为重排，每次只交换相邻字符，求把a变成b的最少交换次数。',
    r'''给b中每种字母保存其出现位置。顺序读取a，同字母依次匹配b中最早尚未使用的位置，得到一个目标位置排列。它的逆序对数就是最少相邻交换次数。用树状数组统计已经出现的目标位置，当前贡献为此前项数减不大于当前位置的项数。答案用六十四位。''',
    r'''重复字母彼此没有身份区别，却不能随意分配目标位置。若a中较早的两个相同字母被匹配到b中相反次序的位置，把两个匹配交换即可消除它们的交叉，不改变最终字符串，也不会增加其它字符所需的交叉。因此存在最优方案保持同字母的出现次序。

先扫描b，为二十六种字母分别保存递增的位置列表。再从左到右扫描a，用next[letter]取该字母下一处未使用的位置，并把指针加一。题目保证两串可互相变换，列表不会耗尽后继续取值。

得到的每个目标位置只使用一次。两个字符的目标位置倒序时，它们在相邻交换过程中必须越过彼此至少一次；一次相邻交换最多消除一个逆序。反过来，按目标位置冒泡可以恰好消除全部逆序，所以最少次数等于逆序对总数。

处理第i个字符时，树状数组保存前面i个目标位置的频次。查询sum(p)得到其中不大于当前目标p的数量，i减sum(p)就是此前目标更靠右、必须与当前字符交叉的数量。算完贡献才把p加一。

例如ABC变为BCA，目标位置为三、一、二，第一项分别与后两项交叉，共两次。重复字符的稳定匹配不会把两个相同字符额外当成一次必要交换。

长度可达一百万，逆序对可超过int。树状数组每格只数最多n次出现，int足够，但总答案必须使用long long。''',
    '同字母稳定匹配；目标位置从一编号；先查询后插入；统计此前更大位置；总逆序对六十四位；不能只数字符不在原位置的数量。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',['树状数组'],F+['strings','standard-array'])

emit('P2161','有序维护互不相交的预约，只取消与新闭区间相交者',
    'A操作取消所有与新预约相交的旧预约并报告取消数，然后加入新预约；B操作报告当前预约总数。',
    r'''旧预约始终互不相交，用set按左端排序。新预约[l,r]到来，lower_bound找到左端至少l的第一段；若前一段右端至少l，也从前一段开始删除。继续删除左端不超过r的旧段，最后插入原始[l,r]。删除只是取消预约，不把旧范围合并进新范围。''',
    r'''每次新预约都会先删除所有相交旧段，再插入自己，因此保留下来的区间始终两两不相交。这让“查到哪一段开始删除”只需检查一个前驱。

set保存左端、右端组成的pair，先按左端再按右端排列。使用成员lower_bound({l,INT_MIN})找到第一段左端至少l的区间；INT_MIN保证同左端的任意旧段都不会被跳过。

左端小于l的旧段中，只有紧邻前驱可能与新段相交。若它的右端至少l，就把迭代器退到它；更早的旧段不可能越过这段再与新预约相交，否则旧段之间已重叠。

从这里向后，只要旧段左端不超过r就删除并计数。集合erase(iterator)返回下一项，继续用返回值遍历，不能再递增已经失效的旧迭代器。全部相交项取消后，插入原始的新预约并输出删除数量。

闭区间共享端点也相交，比较使用不小于与不大于。例子先有[1,10]、[20,30]，加入[9,21]会取消两段；以后加入[29,29]不应取消[9,21]。取消不等于区间并集，不能把新右端扩到三十。

一条A可能删除很多段，但每个已插入预约至多被删除一次。所有操作合计的删除次数线性，配合集合查找和插入，整体为n乘对数n。成员lower_bound沿树查找；不要换成对set迭代器调用通用lower_bound，那会有线性迭代开销。''',
    '共享端点也相交；仅前一段需补查；取消不是合并；erase使用返回迭代器；A输出取消数，B输出现存总数。',
    r'全部操作合计时间 $O(n\log n)$，空间 $O(n)$。',['模拟'],A+['sets','iterators','bindings'])

emit('P4939','把区间增量化成两个事件，只离散化实际修改位置',
    '0 a b把闭区间内每个位置加一，1 a询问该位置被增加的次数；位置上限很大，操作数相对较少。',
    r'''闭区间[l,r]加一等价于差分l处加一、r加一处减一。先读全部命令，收集这两个事件坐标并排序去重，再按原顺序执行。修改用lower_bound找事件编号，查询用upper_bound得到所有不大于询问点的事件数，再查树状数组前缀和。没有任何修改时，空事件表的查询自然为零。''',
    r'''单点查询关心的是到这个坐标为止已经开始、尚未结束的区间数。将一次区间增加写成l处开始的一次正事件和r加一处结束的一次负事件，答案就是差分事件的前缀和。

直接按一千万位置开数组也能表示问题，但只有至多两倍修改数的坐标会发生变化。程序预读命令，收集所有修改的l、r加一，排序并去重。询问坐标无需放进压缩表，因为询问只要求一个事件前缀。

重放命令仍必须保持输入顺序。预读不表示把所有修改提前生效，未来的更新不能影响之前的查询。每个修改的两个坐标一定在表里，lower_bound取到其准确位置后加一转为树状数组编号。

查询位置x时，upper_bound给出第一个大于x的事件坐标。它减去begin得到事件数q，恰表示有q个事件坐标不大于x；sum(q)就返回这些事件当前已发生的代数和。这里不再加一，否则会把右侧尚未到达的事件也算进去。

右端事件必须放r加一，查询r时仍应得到本次增加，查询r加一才抵消。即使r等于N，也要保留N加一事件，便于统一更新；它不会进入任一合法位置查询的前缀。

若命令全为查询，坐标表为空，树状数组大小零，每次sum(0)返回零，不进入更新循环。该差分频次允许负事件，所以不能在这棵树上使用要求非负频次的第k项搜索。''',
    '区间闭合；撤销在r加一；离线收集坐标后仍按时序执行；upper_bound返回事件数不加一；无更新时空表合法；差分不是点值频次。',
    r'时间 $O(M\log M)$，空间 $O(M)$，与N的大小无关。',['差分','离散化','树状数组'],F+['difference','sort','bounds','bindings'])

emit('P5367','逐位数更小的剩余值，每个值对应一个阶乘大小的排列块',
    '求给定一至N的全排列在字典序中的名次，第一种名次为一，答案对998244353取模。',
    r'''固定已经相同的前缀，若当前位置改用一个尚未出现且更小的数，后面任意排列都会更早，共有剩余位数阶乘种。树状数组维护未使用数的频次，查询当前数之前还有多少个，乘阶乘加入，再删除当前数。所有更早排列数量最后加一，代码直接把答案初始化为一。''',
    r'''字典序比较只看第一个不同的位置。因此把更早的排列按“首次不同在第几位”分类，类别互不重叠。

处理当前值x时，前面的数已经固定且从剩余集合删除。若当前位选一个剩余且小于x的数，后面每种排法都比原排列早；可选更小数的数量乘后面位置数的阶乘，就是这一位的贡献。

树状数组初始每个数频次为一。sum(x减一)数仍未使用且严格更小的值，乘factorial[后面位置数]并取模，随后add(x,负一)把当前数删除。必须先算再删，虽然当前x本身不在严格前缀里，这个顺序也直接对应“在当前剩余集合中选择”的含义。

所有叶频次都是一，tree[i]负责的块长度正好为lowbit(i)，所以可在线性时间初始化tree[i]为i与负i的按位与。阶乘也从零阶乘一开始递推，每一步取模，避免计算巨大整数。

一、二、三的首排列没有更早者，答案一；三、二、一的末排列名次等于N的阶乘。不能输出从零开始的康托值。本题输入保证是排列，不能把这个方法原样用于带重复数的多重排列名次。

查询次数存int，但频次与取模阶乘相乘应使用long long。代码factorial本身是long long，因此乘法从六十四位进行。''',
    '名次从一开始；后缀为零位时阶乘是一；只数尚未使用的更小值；每位删一次；阶乘逐步取模；不能直接用于重复值。',
    r'时间 $O(N\log N)$，空间 $O(N)$。',['树状数组','组合计数'],F+['counting','modular'])

emit('P7149','固定最左与最右奶牛，分别选择上下边界上的奶牛',
    '横纵坐标分别互异，统计可被一个轴对齐矩形恰好围住的不同奶牛子集，空集也算一种。',
    r'''按x排序并压缩y。固定一组最左、最右奶牛i、j，矩形至少要包含这两头，所以底边上的奶牛需在x条带内且y不高于两者较低者，顶边上的奶牛需在条带内且y不低于较高者。上下候选数量相乘，枚举全部i不大于j并累加，再加空集。二维前缀和使每个候选计数为常数时间。''',
    r'''不能直接枚举任意矩形坐标：很多不同矩形会围住同一个子集。把每个非空子集的矩形收紧到其中最左、最右、最低、最高奶牛，边界就由子集唯一确定。横纵坐标分别互异，使每条边界上的奶牛也唯一。这是[官方分析](https://usaco.org/current/data/sol_prob2_silver_dec20.html)采用的边界计数依据。

按x排序后，固定最左奶牛i和最右奶牛j。所有被选奶牛都在这个连续x条带中；还必须包含i和j，所以底边不能高于它们较低的y，顶边不能低于较高的y。

在条带内，数y不大于较低端点的奶牛数bottom，再数y不小于较高端点的奶牛数top。任选一头底边奶牛、一头顶边奶牛，就确定了一个包含i、j的收紧矩形，贡献bottom乘top。不是任选条带中两头就行，上下限制保证固定的左右极值确实在矩形里。

不同上下选择必然改变收紧边界和子集，同一个子集也有唯一的左右极值，因此不会重数。i等于j时，两侧候选均只有这头在条带里的奶牛，恰好计入单牛子集。

为快速数条带矩形中的点，将y排序后映射为一至N。建立二维前缀表prefix[x][y]，表示前x头且y秩不超过y的奶牛数。矩形计数取右上前缀减左边、减下边、加回左下重叠。代码count使用左侧排除、右侧包含的编号约定，两个维度都对应同一四区域公式。

所有非空子集累计后再加一表示空集。总数用long long；前缀表每格最多N，使用int即可。N至多2500，平方表约二十五MB，避免给每个可能子集建立状态。''',
    '数子集不是任意坐标矩形；x与y分别互异；固定左右端必须被包含；上下候选相乘；i等于j计单牛；最后加空集；总答案六十四位。',
    r'时间 $O(N^2+N\log N)$，空间 $O(N^2)$。',['前缀和','组合计数'],A+['coordinates','sort','rectangle-prefix','counting','lambda-local','bindings'])

emit('P10235','二分每段允许的逆序数，贪心取最长可行前段',
    '把音符序列分成至多k个非空连续段，使各段逆序对数量的最大值最小，输入有多组数据。',
    r'''二分最大允许逆序数limit。依次向当前段加入元素x，新增逆序等于当前段长度减不大于x的项数，用离散化树状数组计算。加入会超限时，在x前切一段并清除旧段频次，再由x开始。总段数至多k即可行。清除时逐个删除旧段元素，每个元素至多删一次，不能每切一段就清空整棵大数组。''',
    r'''一个连续段向右增加元素时，原有逆序对不会消失，因此该段的逆序数单调不减。若最大允许值limit可行，增大限制仍然可行，可以二分最小可行限制。

固定limit，从左到右尽量把当前段延伸到最长。任何可行方案的第一段都不能超过这个终点；用更长的可行第一段替换较短第一段，只会删去后续各段前面的一些元素，不会增加它们的逆序数。因此最长前段不会增加所需段数，逐段贪心可求最少段数。

加入新值x，只新增此前严格大于x的项与它组成的逆序。把值排序去重映射为秩，树状数组sum(rank[x])统计当前段不大于x的项数。当前段长度减去它，就是本次新增量，重复值不会计为逆序。

如果当前逆序数加新增量超过限制，就在x之前切开。先增加段数，若已经超过k立即判失败；否则把旧段所有项从树状数组逐个减一，当前逆序数归零，再插入x。

删除看起来有嵌套循环，但left只会向右移动。一次可行性检查中，每项最多插入一次、删除一次，总树状数组操作数线性。若每切一段就fill一个大小n的数组，全降序且limit为零时会退化成平方时间。

二分下界零，上界用全序列真实逆序数，只分一段总是可行。上界为零时无需检查；k等于n时可分单项，答案也为零。逆序总数可超过三十二位，限制、当前数与新增数均用long long。每组重新压缩并建树，不能串用上一组状态。''',
    '分至多k段；段必须连续；严格大于才成逆序；超限在当前项之前切；清除只删本段元素；多组重建；逆序数六十四位。',
    r'每次检查 $O(n\log n)$，总时间 $O(n\log n\log(n^2+1))$，空间 $O(n)$。',['二分查找','贪心','树状数组'],F+['sort','bounds','binary-answer','greedy','lambda-local'])

emit('P14521','把到达每个结点的条件平移成初始数的闭区间',
    '根结点执行一次加减后，可以选择满足当前值范围的子边继续；每个查询给初始x，数最终可停在哪些结点。',
    r'''到达结点v时的数等于初始x加路径累计增量D[v]。根允许所有合法查询x；子边[l,r]要求x在[l减D[parent],r减D[parent]]，再与父结点已允许区间取交。每个可达结点得到一个初始x闭区间。将所有左端、右端分别排序，查询用不大于x的左端数减严格小于x的右端数。先判区间非空再累计子增量，避免在根本不可达的长链上溢出。''',
    r'''路径上只有加法和减法，执行顺序不会改变累计增量。设D[v]为从根到v全部操作的代数和，初始x到达并执行v的操作后，当前值就是x加D[v]。

边的范围检查发生在进入子结点之前，必须使用父结点已经执行后的增量。若父结点p允许初始x属于I[p]，子边范围为[l,r]，则子结点的允许集合为I[p]与[l减D[p],r减D[p]]的交集。交集仍为一个闭区间，空集表示整个子树不可能从任何合法查询进入。

题目保证父编号小于子编号，因此按编号处理即可，不需要递归走五十万层。根结点总能被选作终点，允许初始范围为题面给定的负十的十八次方至正十的十八次方。

这里不能先不加判断地累计整条路径。每项可达十的十八次方，五十万项的形式和远超六十四位。但对已确认可达的非根结点，进入时的当前值位于边界范围内，绝对值至多十的十八次方；再加减一个同范围操作，执行后的绝对值至多两倍。扣去合法初始x后，D的绝对值至多三倍十的十八次方。根的增量更小。

因此父增量平移边界的中间量绝对值至多四倍十的十八次方，long long足够。实现先检查父结点有效、求交并确认非空，之后才计算D[v]；无效父结点直接跳过，不形成可能溢出的无用路径和。这个界限依赖剪枝顺序，不能在剪枝前先把所有D算完。

每个有效结点对应一个可作终点的初始区间。查询x时，已开始的区间数为upper_bound(starts,x)减begin，已经结束的区间数为lower_bound(ends,x)减begin。后者只排除右端严格小于x的区间，保留右端等于x的闭边界。两者作差就是答案，不是求一条路径能走多长。

本地题面还引用calc2至calc6的附件样例，缓存未给出具体内容。保留这些引用，本次只把能读取的第一组计为原样例，不补造附件数据。''',
    '先执行父操作再检查边；交的是初始x范围；空区间整棵子树跳过；确认非空后才加子增量；闭右端不能提前排除；根一定计入；不累计不可达长链。',
    r'时间 $O(n\log n+q\log n)$，空间 $O(n)$。',['递推','二分查找'],A+['trees','sort','bounds','bindings'])

emit('CF961E','按较小下标倒序激活满足另一侧要求的位置',
    '统计x小于y，且第x季有第y集、第y季有第x集的季编号对。',
    r'''固定较小下标i，另一位置j必须满足i小于j不大于a[i]，同时a[j]至少i。把所有位置按a降序排序，i从n向一枚举，逐步激活a[j]至少i的位置。树状数组存激活位置频次，查询闭区间[i加一,min(n,a[i])]的数量。每对只在较小端i处理一次。''',
    r'''一对季编号i小于j合法，需要同时满足j不大于a[i]和i不大于a[j]。前者限制j的位置范围，后者限制该位置的数值。

将所有位置按a值降序排列，另按i从n到一处理。随着i降低，满足a[j]至少i的位置只会增加。用一个指针依次把这些位置激活，在树状数组对应位置加一，每个位置只插入一次。

激活后，数值这一条件已经满足；剩下只需数位置在i加一到min(n,a[i])之间的激活点，用两个前缀和相减。若右端不大于i，直接贡献零，不要得到负长度区间。

当前i也可能已经激活，减sum(i)时一并排除，不能把一季自己与自己成对。两端的大小关系固定后，每个无序季对只由较小编号枚举到，不再除以二。

a可能大于n，只截断查询位置的右端，不应改变原始数值排序。边界a[j]等于i与a[i]等于j都合法，激活比较使用至少，查询也含右端。

所有a都足够大时答案为n选二，可超过int；频次树中每格至多n，int足够，总答案用long long。''',
    '两个条件都要；a值决定激活，位置决定查询；i小于j严格；等于季集边界合法；右端截到n；每对只计一次；总数六十四位。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',['树状数组','排序'],F+['sort','lambda-local'])

emit('P1966','先按高度秩配对最小化距离，再数两列相对次序的逆序',
    '可以在两列中交换相邻火柴，先使对应高度的平方差和最小，再求达到最小值所需的最少交换次数，对十的八次方减三取模。',
    r'''把两列各自按高度排序，等排名的火柴必须配对，才能使平方差和最小。用这些配对把第一列每个原位置映射到第二列的原位置，所得排列的逆序数就是最少相邻交换数。树状数组统计逆序，最后对99999997取模。无需实际求平方差，也不能改用其它常见模数。''',
    r'''展开每对平方差，所有第一列高度平方之和、第二列高度平方之和都不随重排改变。最小化距离等价于最大化对应高度乘积之和。

若第一列两个高度按小、大排列，第二列却把大、小与它们配对，改成同序配对会使乘积和增加两列高度差的乘积。每列内部高度互异，差的乘积为正，因此最优配对恰为两列相同排序名次对应。

记录每个高度的原位置，分别排序。把第一列原位置处的火柴替换为它必须匹配的第二列原位置，就得到一个目标位置排列。目标位置逆序的一对必须在某一列的相邻交换中交叉一次，因此任意两列共同操作也至少需要这么多次。

这个下界可以达到：固定第二列，按目标位置把第一列用相邻交换排成一致次序即可，恰好消除所有逆序。允许两列都交换不会让总次数低于逆序数，也无需分别把两列完整排序后把交换次数相加。

从左到右把目标位置加入树状数组，当前贡献为此前元素数减sum(当前目标位置)。累加long long，最后对十的八次方减三，即99999997取模。

高度本身可能接近三十二位上限，平方差和可能很大。本方法只比较高度并数位置，不实际做平方运算，也不需要把高度乘积塞进int。''',
    '先最小化平方差再最少交换；同秩配对；映射到另一列原位置；允许两边交换也不减少逆序下界；不分别排序后相加；模数99999997。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',['树状数组','排序'],F+['sort','counting'])

emit('P3149','只记录被排序值域的最高门槛，扣除该范围的初始逆序',
    '每次取当前位置k的值，将所有不大于该值的元素在其占据的位置中升序排列；输出初始及每次操作后的逆序数，元素可重复。',
    r'''若已经排过所有不大于H的值，这些位置内的当前值仍不大于H，其余位置一直保留原值。下一次门槛只可能提高到原始a[k]，因此维护所有查询原始值的最大值即可。初始每个逆序按较大值分类，树状数组从右往左算其右侧严格更小项数，再对值域贡献做前缀和。当前答案为初始逆序减不大于门槛的贡献。''',
    r'''操作排序的是所有小值所占的位置，不是一个连续区间。若此前的最高门槛为H，原值不大于H的位置只互相交换这些小值；原值大于H的位置从未参与，值仍等于原始a[k]。

因此查询当前位置k时有两种情况。原值不大于H，则当前位置也不大于H，重排其子集不会改变已经整体有序的小值次序，门槛不提高。原值大于H，则该位置尚未改变，新的门槛正好是原值。合起来只需更新H为它与原始a[k]的较大值，不必模拟当前数组。

分析逆序的变化。两项都不大于H时，这些小值整体有序，内部逆序全部消失。两项都大于H时，原位置和数值均不变。若一大一小，大值位置固定，小值在所有参与位置中换位，但每个小值都比大值小；该大值右侧有多少参与位置不变，所以这类逆序总数不变。

原逆序中，两项都不大于H等价于其中较大的那个值不大于H。于是从右往左扫描原数组，查询当前值右侧严格更小的项数，把这个贡献归到当前较大值的桶里，同时插入当前值。相等不计逆序，所以查询rank减一。

对贡献桶按值秩做前缀和。查询时维护最大的原始值秩，答案就是total减coefficient[threshold]。这是累计消除的初始逆序，不是在每次操作后重新统计新逆序。

原样例一、五、三、四、二初始有五对。先把不大于三的值排好，消除一对；再把不大于四排好，再消除一对，输出五、四、三。后续即使选到已经移动的小值位置，也不能直接把其原值当成本次当前值；程序只借助上述最大门槛不变量更新累计H。''',
    '选当前位置的值，但累计最高门槛可用原值；不是连续区间排序；重复值不成逆序；按逆序较大值分类；输出初始结果；总逆序六十四位。',
    r'预处理 $O(n\log n)$，每次操作 $O(1)$，总空间 $O(n)$。',['树状数组','排序'],F+['sort','bounds','prefix'])

emit('P4064','二分最低值，缺多少次覆盖就选右端最远的可用区间',
    '给定互异的可选区间，每段最多用一次，必须恰好选k段分别加相同正数，使最终最小元素最大。',
    r'''二分目标最小值。自左向右扫描，堆保存左端已到达的未选区间，按右端最大优先。当前覆盖增量仍不足时，补选所需数量的右端最远区间，并用到期差分维护已选覆盖数。无可覆盖区间或选数超过k则失败。能用至多k段满足目标，就能任取其它未选段补到恰好k，因为增加量为正且k不超过总段数。''',
    r'''若某个目标最低值可达到，更低目标也可达到，二分最大可行目标。下界为原数组最小值；无论怎样选，一项至多被增加k次，所以上界可取原最小值加k乘a。

固定目标，从左到右保证每项达标。将左端不超过当前位置i的区间放入大根堆，堆按右端排列。它们尚未使用，其中右端小于i者已经过期，取用前弹掉。

已选区间对当前位置的覆盖次数为active，用到期差分维护：选右端r的区间时立刻active加一，并在r加一处减一。若A[i]加a乘active仍不足目标，按差额向上取整得到还需多少次覆盖。

每次补选右端最大的可用区间。交换证明要保留此前已经选定的集合：它们已让所有更早位置达标。若一个可行补全用较短区间覆盖当前i，可以把它换为贪心的更长右端区间；以前位置即使失去某次补全覆盖，也仍由已固定集合保证。当前位置及未来，替换者覆盖得不少。因此可以逐个让最优补全包含贪心选择。

每段只能选一次，取用后从堆删除。若堆空，当前项无法补足；若所需新增段使总选择数超过k，也直接失败。一次检查中区间各入堆一次、最多出堆一次，不是对每个位置重新枚举所有区间。

虽然题目必须恰好选k段，可行性检查只要求不超过k段。因为每次增加为正，剩余的未选互异区间可以任意补到k段，只会使元素更大，不会破坏已达到的目标。这一转化依赖k不超过m和正增加量，不能推广到负操作或强制不变的其它约束。

多组分别排序、建堆与差分；二分中重新建状态，不能沿用上次目标的选择。计算差额、乘法及二分端点用long long。''',
    '区间各最多一次；先加入左端已到者；取右端最远者；过期区间不可用；新增选择计入k；正增加才可把至多补到恰好；每次检查重建。',
    r'总时间 $O((n+m\log m)\log(ka+1)+m\log m)$，空间 $O(n+m)$。',['二分查找','贪心','堆'],A+['binary-answer','greedy','heap','difference','sort','lambda-local','bindings'])

emit('P5677','最近值只在排序邻居中找，有向配对转成区间包含查询',
    '每个数与全数组中距离最近的其它数形成有向配对，距离并列可有两对；询问两端都在[l,r]的配对数，输出按询问编号加权的总和。',
    r'''值互异，排序后某项的最近值只可能是相邻前驱或后继，距离相同则两个方向都建。把一条有向配对记为两端位置的最小L、最大R，但保留重复区间，因为反向配对仍是另一对。将查询按右端排序，激活R不超过查询右端的边，在L位置加一；答案是已激活边数减L小于查询左端的数量。''',
    r'''先按数值排序。一个值左边所有更远的数，都不可能比紧邻前驱更近；右边同理只需后继。比较两边距离，取较小者；相等时两者都与当前值形成配对。

配对是有向的。例如只有两个不同值，第一项选第二项，第二项也选第一项，总共有两对。转成位置区间时，这两对的L、R相同，也必须保留两份，不能用set去重。

对每条配对，令L为原位置的较小者、R为较大者。它的两端均落入查询[l,r]，恰好要求L至少l且R至多r。整个配对集合由全数组预先确定，不能在每个查询子数组中重新找最近值。

将边按R升序、查询按r升序处理。先把R不大于当前r的全部边激活，每条在树状数组位置L加一。此时右端条件已经满足，减去sum(l减一)就排除左端过小的边，剩余数量为本次答案。

每个原数最多产生两条有向边，所以边数线性。原序列长度为一时没有其它数可配，边表为空，所有询问为零，不使用无意义的无穷距离来造一条边。

查询排序改变处理顺序，但加权仍用原来的从一开始编号id。每次贡献为本次答案乘id后加到long long总和，不是按排序后的序号加权；也不是只输出各次查询答案。''',
    '全局最近值；并列两边都建；有向反向分别计；同L、R不能去重；先激活R再查L；权重用原询问编号；乘法六十四位。',
    r'时间 $O((n+m)\log(n+m))$，空间 $O(n+m)$。',['树状数组','排序'],F+['sort','counting','bindings'])

emit('P8201','路径异或抵消后，只需查路径上是否出现指定点权',
    '树上两点a、b及给定k，问是否存在任意城市t，使t到a路径点权异或与t到b路径点权异或的结果等于k。',
    r'''把t投影到a至b路径的交点c，两条t出发路径共有部分抵消，得到结果为a至b整条路径异或再异或w[c]。所以只需查a至b路径上是否有点权X异或k。先倍增求LCA和路径异或，离线把查询挂到两个端点；再DFS维护每种权值在当前祖先链中最近出现者，深度至少LCA即在所需半条路径。显式栈进入、退出时恢复状态，避免长链递归。''',
    r'''这里dist是整条路径的点权异或，含两个端点，不是距离和。取t到a、t到b两条路径最后的公共结点c，它位于a到b路径上。

公共的t到c部分在两份异或中出现两次而抵消，c也出现两次。若X是a到b整条路径的点权异或，那么所求结果恰为X再异或w[c]。因此需要某个路径点c满足w[c]等于X异或k。反过来，只要有这个点，直接取t等于c就能实现，城市t不在路径上的选择不会产生新种类的结果。

根到u的点权前缀异或记prefix[u]，包含u。设c为a、b的最近公共祖先，两份前缀把c抵消了，要额外补回w[c]，于是X等于prefix[a]异或prefix[b]异或w[c]。

用倍增预处理祖先并求每次LCA，得到目标权值。压缩的是树上实际出现的权值；若目标不在集合中直接为No，不能因为输入权值上限较小就按X异或k直接访问一个同样上限的数组，异或结果可能越界。

剩下是路径存在性。对每个查询，把目标值和LCA深度挂到a、b两个端点。另做一次DFS，last[value]保存当前根至结点链上该值最近出现的结点。进入u时保存旧last，再把它更新为u；处理u处事件时，若目标的最近祖先深度至少为本查询LCA的深度，目标就在端点至LCA这一半路径上。

两端任一半找到就输出Yes。若最近同值祖先都在LCA上方，则更早同值祖先也更浅，不能误算进路径。退出u时恢复进入前的last，避免另一兄弟子树的同值结点泄漏到当前祖先链。

第一次遍历算父亲、深度和倍增表；第二次用正编号进入、负编号退出的显式栈完成保存与恢复。五十万结点链不会耗尽调用栈。查询挂两端，每个事件只检查一次；答案分别表示每个查询存在一种t，不需要同一个t满足全部询问。''',
    '点权异或含端点；公共结点需补回一次；目标为路径异或再异或k；只查路径上的点；LCA上方同值不算；退出恢复last；用显式栈；Yes与No按询问顺序。',
    r'时间 $O((n+m)\log n)$，空间 $O(n\log n+m)$。',['LCA','DFS'],A+['trees','binary-lifting','bitwise','sort','bounds','lambda-local'])

emit('P11656','把实际喷洒覆盖化成端点分段，用两棵后缀最小树递推',
    '为部分表演者付费并选择喷洒方向，允许同向酒被吸收但禁止喷到任何反向表演者，求覆盖一至n全部位置的最少人数。',
    r'''最优值等价于将整条线划成连续块，每块选左端向右或右端向左的一人，块长不超过此人的距离。实际有效酒段删去被包含者后可形成这种分段；反过来，最少块方案若自然酒程碰到反向端点，就可把中间全部块合成一块而变得更少，矛盾，因此不受强度影响。令f[i]为前i位最少块数，左喷查最近a[i]个旧f的最小值，右喷候选按最远覆盖位置登记，用两棵只更新变小值的后缀最小树状数组维护。''',
    r'''强度会改变某一固定安排的实际酒程，不能直接从模拟中删掉。本题能不把k放进状态，需要先证明最优人数等价于另一种覆盖。

把一至n划成不相交的连续块，每块选左端表演者向右喷，或者右端表演者向左喷，块长不超过这人的a。先证明这种端点分段的最少块数就是原问题答案。

从实际合法安排到分段：每股酒在消失前覆盖的是以表演者为端点的连续区间。两个反向表演者不可能被对方的有效酒段包含，否则已经愤怒。删去被其它有效酒段完整包含的酒段，覆盖不变、数量不增，且这种包含只能发生在同向酒段之间。

删完后，向右酒段的右端随表演者位置严格递增，向左酒段的左端也随位置严格递增。对于相邻保留表演者p、q，中间的空位若能被任何右喷覆盖，最近的p右喷至少覆盖得一样远；左喷同理由q负责。两人都向右就在q前切，都向左就在p后切；向外喷时两人必须相邻；向内喷时两段覆盖相接，可在交叠处选一个切点。首尾也必须覆盖到一、n。于是可划出不多于原人数的端点块，每块长度仍不超过其酒程。

反过来，考虑块数最少的端点分段。若某个左端p向右的自然酒程能到达一个反向、位于其右侧的表演者q，那么从p所在块至q所在块的整个范围正好从p开始、到q结束，全部能由p一人向右覆盖。把这些块合并会使块数严格减少，与最少矛盾。左喷碰到左侧反向者时完全对称。

因此最少块方案的自然酒程都不会碰到反向表演者。每块内部没有别的付费表演者，自己的酒先覆盖完整个块，之后即使被同向者吸收也无妨。它对任意强度k都合法，这才说明最优人数与k无关，而非任意安排与k无关。

现在做分段递推。f[0]为零。若最后一块右端是i并向左喷，前一块终点j可以从max(0,i减a[i])到i减一，取这些已计算f[j]的最小值再加一。

若最后一块从j向右喷，其代价为f[j减一]加一，可以负责右端从j到j加a[j]减一的任意位置。扫描到j时，把这个代价按最远可达右端R登记；处理当前i，只查询所有R至少i的已登记候选。扫描时序已经保证j不大于i，无需额外左端条件。

第一类同样是查询已出现j中下标至少某个值的最小值。用两棵后缀最小树状数组：一棵存旧f，另一棵按R存右喷代价。这里tree[p]保存从p起、长度lowbit(p)的一块，单点更新向p减lowbit移动，后缀查询向p加lowbit移动，与前缀求和的方向相反。

这些树只插入候选、把格内最小值变小，不删除也不把值改大，因此旧的块最小值始终有效。不能把它当作支持任意赋值的区间最小树。f下标包含零，代码统一加一映射；右达范围截到n，避免无用越界。

每步先登记从i向右的新候选，再查询f[i]，最后才插入这个新f，防止左喷使用尚未完成的同一位置形成空块。距离一时每人只能负责自己，答案n；全线可由端点一人喷满时答案一。''',
    '强度无关须经最优分段等价证明；固定安排仍受k影响；块长不超过a；f零下标要映射；后缀最小树只减不增；先算f[i]再登记旧f；右喷起点i本步可用。',
    r'时间 $O(n\log n)$，空间 $O(n)$。',['DP','树状数组'],F+['dp','monotonic'])

emit('P14379','只维护没有一的空隙，以及没有二的块内一的数量',
    '单点修改高度后，统计长度至少二的区间中，能够选一处切开使左右正整数MEX不同的区间数。',
    r'''不贡献的区间恰有两类：整段没有1；或两端都是1且整段没有2。第一类按相邻1之间空隙长度g计g选二，第二类按相邻2之间块里1的数量c计c选二。两类互斥，用全部n选二减去它们。树状数组维护1、2的位置频次，并用非负频次上的第k项搜索找邻居；修改只影响拆分或合并的相邻块及其中1的数量。''',
    r'''题目的MEX从正整数一开始。若一个区间没有一，不管怎样切，左右MEX都是一，贡献零。若有一而某个端点不是一，将这个端点单独切出，或把一侧无一的部分切出，就能得到一与至少二，贡献一。

剩下两端都是一的情况。任一切法的两侧都有一；若整段没有二，两侧MEX始终都是二。若中间有二，在第一个二之前切开，左侧有一无二，MEX为二；右侧含一和二，MEX至少三。因此不贡献恰为“无一”，以及“端点均为一且无二”两类，且两类不重叠。

只统计长度至少二。无一的一个极长空隙长g，区间数为g乘g减一除二。无二的一个极长块里有c个一，任选两个不同的一作端点就是第二类区间，共c选二；中间允许其它大于二的数。

分别维护两类总数noOne、twoFree，答案为n选二减去两者。所有大于二的值在这里等价，修改前后同属第三类时不必动数据结构。

用两棵频次树记录一、二的位置。查一个位置p前有多少次出现，配合第k项搜索即可找到前驱、后继；不存在的邻居使用零、n加一哨兵，哨兵不放进树。

第k项搜索维护一个已确认前缀长度pos和仍需跳过的次数k，按二进制位从大到小尝试向右一块。若该块总频次严格小于k，就整块跳过并扣除它的频次；否则在更小位继续找。最后pos加一是首个累计次数至少k的位置。频次始终为零或一，因此前缀单调；k只取一至当前总次数，不能对空集合硬查。代码最高步长为二的二十次方，覆盖本题至多一百万位置。

插入一个一，会把无一空隙分成左右两段，用两段的组合数替换整段。同时，所在无二块原来有c个一，新增一形成c个新的双一端点区间。删除一个一则把两个空隙合并，并从所在块减去c减一个配对。注意先查旧数量，再更新一的频次。

插入一个二，把原无二块分成左右，若两侧分别有L、R个一，跨过新二的L乘R个端点对不再属于twoFree。删除一个二则恢复这些跨界配对。左右一的数量用一频次树的前缀差计算。

一次修改先删除旧类别，再插入新类别，特别是从一改二时，拆块计数必须使用已经删除旧一的状态。总答案可达约五千亿，组合数与乘法均使用long long。

题面引用building2至building7附件，但缓存只含第一组具体样例；原引用保留，不将未取得附件计为已跑样例。''',
    '正整数MEX；只计长度至少二；无一与双一无二两类互斥；其它高度同类；先删旧再加新；第k项要求非负频次与合法k；哨兵不入树；组合数六十四位。',
    r'初始化 $O(n)$，每次修改 $O(\log n)$，空间 $O(n)$。',['树状数组','组合计数'],F+['counting','prefix','monotonic','bindings','lambda-local'])

emit('CF1194E','枚举上下两条横线，统计同时贯穿它们的竖线',
    '给定水平或垂直线段，同方向线段互不相交，数选四段能围成轴对齐矩形的方案，端点相接也算相交。',
    r'''横线按高度排序，枚举底边后用树状数组登记所有经过该高度的竖线，按x计数。上边高度逐渐增加时，删除上端已经低于该高度的竖线。查询上下横线横向重叠闭区间内还剩多少条竖线c，任选两条组成矩形，贡献c选二。竖线上端等于当前上边时仍有效。''',
    r'''矩形唯一对应两条不同高度的横线，以及两条不同横坐标的竖线，四次横竖相交都必须存在。固定上下横线后，只需数同时跨过这两个高度、且x落在两横线共同覆盖范围里的竖线。

先排序横线高度。固定底边时，把纵向区间包含底边高度的竖线加入树状数组，位置是压缩后的x。随后按上边高度递增枚举，同时从按上端排序的竖线列表中删去上端严格小于当前上边的候选。

初始化未包含底边的竖线不应在删除时减一，否则会把频次变成负数。代码仍检查这条线是否曾满足底边条件，仅对真正加入的线删除。每条线在一个固定底边的扫描中最多加、删一次。

两横线的共同横向范围为较大左端到较小右端。若左端大于右端，贡献零；否则用lower_bound得到严格在左界前的竖线坐标数，upper_bound得到不超过右界的坐标数，两个前缀和相减，含两个端点。

剩下c条可用竖线，任选两条贡献c乘c减一除二。同x的两条竖线由于同方向不得相交，不可能同时跨过上下两个不同高度，因此这些候选实际具有不同x，不会造出零宽矩形。同高度横线不形成矩形，明确跳过。

每个矩形按唯一上下横线、唯一两条竖线只计一次，不再乘排列数。端点恰在角上也应计入，删线条件是上端严格小于上边高度；不能在相等时删除。

线段输入端点不保证从左到右或从下到上，先分别取最小、最大值。线段数至多五千，双层枚举配合对数更新可行，答案乘法使用long long。''',
    '同向互不相交是关键保证；上端等于高度仍有效；横向范围闭合；仅删除本底边曾加入的竖线；同高度横线跳过；每矩形只计一次；计数六十四位。',
    r'时间 $O(n^2\log n)$，空间 $O(n)$。',['树状数组','扫描线'],F+['coordinates','sort','bounds','counting','bindings','lambda-local'])
