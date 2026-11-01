#include <bits/stdc++.h>
using namespace std;
struct Fenwick {
    int n; vector<int> tree;
    explicit Fenwick(int size):n(size),tree(size+1){}
    void add(int p,int v){for(;p<=n;p+=p&-p) tree[p]+=v;}
    int sum(int p) const {int value=0;for(;p;p-=p&-p) value+=tree[p];return value;}
    int kth(int k) const {int p=0;for(int step=1<<20;step;step>>=1){int q=p+step;if(q<=n&&tree[q]<k){p=q;k-=tree[q];}}return p+1;}
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<pair<int,int>>values(n);for(int i=0;i<n;++i){cin>>values[i].first;values[i].second=i+1;}sort(values.begin(),values.end());vector<pair<int,int>>edges;
auto add=[&](int i,int j){int l=min(values[i].second,values[j].second),r=max(values[i].second,values[j].second);edges.push_back({r,l});};
for(int i=0;i<n;++i){long long left=i?1LL*values[i].first-values[i-1].first:LLONG_MAX,right=i+1<n?1LL*values[i+1].first-values[i].first:LLONG_MAX;if(i&&left<=right) add(i,i-1);if(i+1<n&&right<=left) add(i,i+1);}sort(edges.begin(),edges.end());
struct Query{int l,r,id;};vector<Query>queries(m);for(int i=0;i<m;++i){cin>>queries[i].l>>queries[i].r;queries[i].id=i+1;}sort(queries.begin(),queries.end(),[](Query a,Query b){return a.r<b.r;});Fenwick bit(n);int next=0;long long answer=0;for(auto [l,r,id]:queries){while(next<(int)edges.size()&&edges[next].first<=r){bit.add(edges[next].second,1);++next;}answer+=1LL*(next-bit.sum(l-1))*id;}cout<<answer<<'\n';
    return 0;
}
