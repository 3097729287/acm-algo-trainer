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
int n;cin>>n;vector<pair<int,int>>a(n),b(n);for(int i=0;i<n;++i){cin>>a[i].first;a[i].second=i;}for(int i=0;i<n;++i){cin>>b[i].first;b[i].second=i;}sort(a.begin(),a.end());sort(b.begin(),b.end());vector<int>target(n);for(int i=0;i<n;++i) target[a[i].second]=b[i].second+1;
Fenwick bit(n);long long answer=0;for(int i=0;i<n;++i){answer+=i-bit.sum(target[i]);bit.add(target[i],1);}cout<<answer%99999997<<'\n';
    return 0;
}
