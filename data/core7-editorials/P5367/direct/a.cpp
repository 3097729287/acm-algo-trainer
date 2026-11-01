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
const long long mod=998244353;int n;cin>>n;vector<long long>factorial(n+1,1);for(int i=1;i<=n;++i) factorial[i]=factorial[i-1]*i%mod;
Fenwick bit(n);for(int i=1;i<=n;++i) bit.tree[i]=i&-i;
long long answer=1;for(int i=0,x;i<n;++i){cin>>x;answer=(answer+bit.sum(x-1)*factorial[n-i-1])%mod;bit.add(x,-1);}cout<<answer<<'\n';
    return 0;
}
