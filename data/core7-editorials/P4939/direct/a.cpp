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
int n,m;cin>>n>>m;struct Command{int op,l,r;};vector<Command>commands;vector<int>coordinates;
for(int i=0;i<m;++i){int op,l,r=0;cin>>op>>l;if(op==0){cin>>r;coordinates.push_back(l);coordinates.push_back(r+1);}commands.push_back({op,l,r});}
sort(coordinates.begin(),coordinates.end());coordinates.erase(unique(coordinates.begin(),coordinates.end()),coordinates.end());Fenwick bit(coordinates.size());
for(auto [op,l,r]:commands){if(op==0){int left=lower_bound(coordinates.begin(),coordinates.end(),l)-coordinates.begin()+1,right=lower_bound(coordinates.begin(),coordinates.end(),r+1)-coordinates.begin()+1;bit.add(left,1);bit.add(right,-1);}else cout<<bit.sum(upper_bound(coordinates.begin(),coordinates.end(),l)-coordinates.begin())<<'\n';}
    return 0;
}
