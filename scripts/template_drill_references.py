"""Input/output wrappers for independently-oracled template exercises."""
WRAPPERS={
'dsu':[
'''int n,q;cin>>n>>q;DSU d(n);while(q--){int t,u,v;cin>>t;if(t==0){cin>>u>>v;d.merge(u,v);}else if(t==1){cin>>u>>v;cout<<d.same(u,v)<<'\\n';}else if(t==2){cin>>u;cout<<d.size(u)<<'\\n';}else cout<<d.cnt<<'\\n';}''',
'''int n,m;cin>>n>>m;DSU d(n);while(m--){int u,v;cin>>u>>v;bool ok=d.merge(u,v);cout<<ok<<' '<<d.cnt<<' '<<d.size(u)<<'\\n';}'''],
'dijkstra':[
'''int n,m,s;cin>>n>>m>>s;vector<vector<Edge>> g(n);while(m--){int u,v;long long w;cin>>u>>v>>w;g[u].push_back({v,w});}auto r=dijkstra(g,s);for(auto x:r.dis)cout<<(x==INF?-1:x)<<' ';''',
'''int n,m,s;cin>>n>>m>>s;vector<vector<Edge>> g(n);while(m--){int u,v;long long w;cin>>u>>v>>w;g[u].push_back({v,w});}auto r=dijkstra(g,s);int q;cin>>q;while(q--){int t;cin>>t;auto p=r.path(t);cout<<(p.empty()?-1:r.dis[t])<<' '<<p.size();for(int v:p)cout<<' '<<v;cout<<'\\n';}'''],
'kruskal':[
'''int n,m;cin>>n>>m;vector<Edge> es;for(int i=0;i<m;i++){int u,v;long long w;cin>>u>>v>>w;es.push_back({u,v,w,i});}auto r=kruskal(n,es);cout<<r.w<<' '<<r.cnt;''',
'''int n,m;cin>>n>>m;vector<Edge> es;for(int i=0;i<m;i++){int u,v;long long w;cin>>u>>v>>w;es.push_back({u,v,w,i});}auto r=kruskal(n,es);cout<<r.w<<' '<<r.cnt<<' '<<r.ids.size();for(int i:r.ids)cout<<' '<<i;'''],
'bfs':[
'''int n,m,k;cin>>n>>m>>k;vector<int> src(k);for(int& x:src)cin>>x;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);}auto r=bfs(g,src);for(int x:r.dis)cout<<x<<' ';''',
'''int n,m,k;cin>>n>>m>>k;vector<int> src(k);for(int& x:src)cin>>x;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);}auto r=bfs(g,src);int q;cin>>q;while(q--){int t;cin>>t;vector<int> p;if(r.dis[t]!=-1){for(int u=t;u!=-1;u=r.p[u])p.push_back(u);reverse(p.begin(),p.end());}cout<<r.dis[t]<<' '<<p.size();for(int u:p)cout<<' '<<u;cout<<'\\n';}'''],
'zero-one-bfs':[
'''int n,m,s;cin>>n>>m>>s;vector<vector<pair<int,int>>> g(n);while(m--){int u,v,w;cin>>u>>v>>w;g[u].push_back({v,w});}auto d=bfs01(g,s);for(int x:d)cout<<(x==numeric_limits<int>::max()/2?-1:x)<<' ';''',
'''int n,m,s;cin>>n>>m>>s;vector<vector<pair<int,int>>> g(n);while(m--){int u,v,w;cin>>u>>v>>w;g[v].push_back({u,w});}auto d=bfs01(g,s);int q;cin>>q;while(q--){int u;cin>>u;cout<<(d[u]==numeric_limits<int>::max()/2?-1:d[u])<<'\\n';}'''],
'bellman-ford':[
'''int n,m,s;cin>>n>>m>>s;vector<Edge> es(m);for(auto& e:es)cin>>e.u>>e.v>>e.w;auto r=bellman(n,es,s);for(int v=0;v<n;v++){if(r.neg[v])cout<<"-INF ";else cout<<(r.dis[v]==numeric_limits<long long>::max()/4?-1:r.dis[v])<<' ';}''',
'''int n,m,s;cin>>n>>m>>s;vector<Edge> es(m);for(auto& e:es)cin>>e.u>>e.v>>e.w;int q;cin>>q;while(q--){cin>>s;auto r=bellman(n,es,s);int neg=0,no=0;long long sum=0;for(int v=0;v<n;v++){if(r.neg[v])neg++;else if(r.dis[v]==numeric_limits<long long>::max()/4)no++;else sum+=r.dis[v];}cout<<neg<<' '<<no<<' '<<sum<<'\\n';}'''],
'topological':[
'''int n,m;cin>>n>>m;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);}auto r=topo(g);if(!r)cout<<-1;else for(int u:*r)cout<<u<<' ';''',
'''int n,m;cin>>n>>m;vector<pair<int,int>> es(m);for(auto& [u,v]:es)cin>>u>>v;vector<bool> del(m);int q;cin>>q;while(q--){int id;cin>>id;del[id]=true;vector<vector<int>> g(n);for(int i=0;i<m;i++)if(!del[i])g[es[i].first].push_back(es[i].second);cout<<bool(topo(g))<<'\\n';}'''],
'scc':[
'''int n,m;cin>>n>>m;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);}auto r=scc(g);cout<<r.grp.size()<<'\\n';int q;cin>>q;while(q--){int u,v;cin>>u>>v;cout<<(r.bel[u]==r.bel[v])<<'\\n';}''',
'''int n,m;cin>>n>>m;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);}auto r=scc(g);vector<int> deg(r.grp.size());for(auto& es:r.dag)for(int v:es)deg[v]++;cout<<r.grp.size()<<'\\n';for(int u=0;u<n;u++){int c=r.bel[u];cout<<r.grp[c].size()<<' '<<deg[c]<<' '<<r.dag[c].size()<<'\\n';}'''],
'lca':[
'''int n,m,q;cin>>n>>m>>q;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);g[v].push_back(u);}LCA t(g);while(q--){int op,u,v;cin>>op>>u>>v;cout<<(op==0?t.query(u,v):t.dis(u,v))<<'\\n';}''',
'''int n,m,q;cin>>n>>m>>q;vector<vector<int>> g(n);while(m--){int u,v;cin>>u>>v;g[u].push_back(v);g[v].push_back(u);}LCA t(g);while(q--){int op,u,v;cin>>op>>u>>v;cout<<(op==0?t.query(u,v):op==1?t.dis(u,v):t.kth(u,v))<<'\\n';}'''],
'fenwick':[
'''int n,q;cin>>n>>q;BIT b(n);for(int i=0;i<n;i++){long long x;cin>>x;b.add(i,x);}while(q--){int t;cin>>t;if(t==0){int i;long long x;cin>>i>>x;b.add(i,x);}else if(t==1){int l,r;cin>>l>>r;cout<<b.query(l,r)<<'\\n';}else{int r;cin>>r;cout<<b.sum(r)<<'\\n';}}''',
'''int n,q;cin>>n>>q;BIT b(n);for(int i=0;i<n;i++){long long x;cin>>x;b.add(i,x);}while(q--){int t;cin>>t;if(t==0){int i;long long x;cin>>i>>x;b.add(i,x);}else if(t==1){int l,r;cin>>l>>r;cout<<b.query(l,r)<<'\\n';}else{long long k;cin>>k;cout<<b.kth(k)<<'\\n';}}'''],
'segment-tree':[
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;Seg t(a);while(q--){int op,l,r;cin>>op>>l>>r;if(op==0){long long x;cin>>x;t.add(l,r,x);}else cout<<t.ask(l,r)<<'\\n';}''',
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;Seg t(a);while(q--){int op;cin>>op;if(op==2){int i;long long x;cin>>i>>x;t.add(i,i+1,x-t.ask(i,i+1));}else{int l,r;cin>>l>>r;if(op==0){long long x;cin>>x;t.add(l,r,x);}else cout<<t.ask(l,r)<<'\\n';}}'''],
'sparse-table':[
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;ST t(a);while(q--){int l,r;cin>>l>>r;cout<<t.query(l,r)<<'\\n';}''',
'''int n,q;cin>>n>>q;vector<long long>a(n),b(n);for(int i=0;i<n;i++){cin>>a[i];b[i]=-a[i];}ST mn(a),mx(b);while(q--){int l,r;cin>>l>>r;cout<<-mx.query(l,r)-mn.query(l,r)<<'\\n';}'''],
'compression':[
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;Compress<long long> c(a);while(q--){int t;long long x;cin>>t>>x;if(t==0)cout<<c.lower(x);if(t==1)cout<<c.upper(x);if(t==2)cout<<c.idx(x);if(t==3)cout<<c.at(x);cout<<'\\n';}''',
'''int n;cin>>n;vector<long long>a(n);for(auto& x:a)cin>>x;Compress<long long> c(a);cout<<c.size()<<'\\n';for(auto x:a)cout<<c.idx(x)<<' ';cout<<'\\n';for(int i=0;i<c.size();i++)cout<<c.at(i)<<' ';'''],
'prefix-difference':[
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;Prefix p(a);while(q--){int l,r;cin>>l>>r;cout<<p.query(l,r)<<'\\n';}''',
'''int n,m,q;cin>>n>>m>>q;vector<long long>a(n);for(auto& x:a)cin>>x;Diff d(n);while(m--){int l,r;long long x;cin>>l>>r>>x;d.add(l,r,x);}auto inc=d.get();for(int i=0;i<n;i++){a[i]+=inc[i];cout<<a[i]<<' ';}cout<<'\\n';Prefix p(a);while(q--){int l,r;cin>>l>>r;cout<<p.query(l,r)<<'\\n';}'''],
'window-extrema':[
'''int n,k;cin>>n>>k;vector<long long>a(n);for(auto& x:a)cin>>x;for(auto x:window_min(a,k))cout<<x<<' ';''',
'''int n,k;cin>>n>>k;vector<long long>a(n),b(n);for(int i=0;i<n;i++){cin>>a[i];b[i]=-a[i];}for(auto x:window_min(a,k))cout<<x<<' ';cout<<'\\n';for(auto x:window_min(b,k))cout<<-x<<' ';'''],
'binary-search':[
'''int n,q;cin>>n>>q;vector<long long>a(n);for(auto& x:a)cin>>x;while(q--){long long x;cin>>x;cout<<bs(0,n,[&](long long i){return a[i]>=x;})<<'\\n';}''',
'''int q;cin>>q;while(q--){long long t;cin>>t;cout<<bs(0,1000000001LL,[&](long long x){return (__int128)x*x>=t;})<<'\\n';}'''],
'kmp':[
'''string s,t;cin>>s>>t;if(s=="-")s="";if(t=="-")t="";auto p=kmp(s,t);cout<<p.size()<<'\\n';for(int x:p)cout<<x<<' ';''',
'''string s;cin>>s;if(s=="-")s="";auto p=prefix(s);for(int x:p)cout<<x<<' ';cout<<'\\n';int n=s.size(),k=n?n-p.back():0;cout<<(n&&n%k==0?k:n);'''],
'z-function':[
'''string s;cin>>s;if(s=="-")s="";for(int x:zfunc(s))cout<<x<<' ';''',
'''string s;cin>>s;if(s=="-")s="";auto z=zfunc(s);vector<int> ans;int n=s.size();for(int k=1;k<=n;k++)if(z[n-k]>=k)ans.push_back(k);cout<<ans.size()<<'\\n';for(int k:ans)cout<<k<<' ';'''],
'trie':[
'''Trie t;int q;cin>>q;while(q--){int op;string s;cin>>op>>s;if(s=="-")s="";if(op==0)cout<<t.insert(s);if(op==1)cout<<t.erase(s);if(op==2)cout<<t.count(s);if(op==3)cout<<t.prefix(s);cout<<'\\n';}''',
'''Trie t;int n,q;cin>>n>>q;while(n--){string s;cin>>s;if(s=="-")s="";t.insert(s);}while(q--){string s;cin>>s;if(s=="-")s="";int before=t.count(s);t.erase(s);cout<<before<<' '<<t.count(s)<<' '<<t.prefix(s)<<'\\n';}'''],
'mod-combination':[
'''int q;cin>>q;while(q--){int op;long long a;cin>>op>>a;if(op==0){long long e;cin>>e;cout<<qpow(a,e);}else cout<<(a%MOD==0?-1:inv(a));cout<<'\\n';}''',
'''int n,q;cin>>n>>q;Comb c(n);while(q--){int a,b;cin>>a>>b;cout<<c.C(a,b)<<'\\n';}'''],
'linear-sieve':[
'''int n,q;cin>>n>>q;Sieve s(n);while(q--){int t,x;cin>>t>>x;if(t==0)cout<<s.isprime(x);if(t==1)cout<<s.lp[x];if(t==2){auto f=s.factor(x);cout<<f.size();for(auto [p,e]:f)cout<<' '<<p<<' '<<e;}cout<<'\\n';}''',
'''int n,q;cin>>n>>q;Sieve s(n);while(q--){int x;cin>>x;long long phi=x,cnt=1;for(auto [p,e]:s.factor(x)){phi=phi/p*(p-1);cnt*=e+1;}cout<<cnt<<' '<<phi<<'\\n';}'''],
'extended-gcd':[
'''int q;cin>>q;while(q--){long long a,b;cin>>a>>b;auto r=exgcd(a,b);cout<<r.g<<' '<<(long long)r.x<<' '<<(long long)r.y<<'\\n';}''',
'''int q;cin>>q;while(q--){long long a,m;cin>>a>>m;auto r=inv(a,m);cout<<(r?*r:-1)<<'\\n';}'''],
'knapsack':[
'''int n,cap,exact;cin>>n>>cap>>exact;vector<Item> it(n);for(auto& x:it)cin>>x.w>>x.v;auto dp=knapsack(cap,it,false,exact);for(auto x:dp){if(x==NINF)cout<<"X ";else cout<<x<<' ';}''',
'''int n,cap,exact;cin>>n>>cap>>exact;vector<Item> it(n);for(auto& x:it)cin>>x.w>>x.v;auto dp=knapsack(cap,it,true,exact);for(auto x:dp){if(x==NINF)cout<<"X ";else cout<<x<<' ';}'''],
'lis':[
'''int n;cin>>n;vector<long long>a(n);for(auto& x:a)cin>>x;auto p=lis(a);cout<<p.size()<<'\\n';for(int i:p)cout<<i<<' ';''',
'''int n;cin>>n;vector<long long>a(n);for(auto& x:a)cin>>x;cout<<lis(a,true).size()<<' '<<lis(a,false).size();''']}
