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
int n,m;cin>>n>>m;vector<int>a(n),values;for(int &x:a) cin>>x;values=a;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());for(int &x:a) x=lower_bound(values.begin(),values.end(),x)-values.begin()+1;
Fenwick bit(values.size());vector<long long>coefficient(values.size()+1);long long total=0;for(int i=n-1;i>=0;--i){int smaller=bit.sum(a[i]-1);coefficient[a[i]]+=smaller;total+=smaller;bit.add(a[i],1);}for(int i=1;i<(int)coefficient.size();++i) coefficient[i]+=coefficient[i-1];
cout<<total<<'\n';int threshold=0;while(m--){int k;cin>>k;threshold=max(threshold,a[k-1]);cout<<total-coefficient[threshold]<<'\n';}
    return 0;
}
