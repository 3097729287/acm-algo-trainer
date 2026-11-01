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
int n;cin>>n;vector<int>a(n+1),order(n);for(int i=1;i<=n;++i){cin>>a[i];order[i-1]=i;}sort(order.begin(),order.end(),[&](int x,int y){return a[x]>a[y];});
Fenwick bit(n);int next=0;long long answer=0;for(int i=n;i>=1;--i){while(next<n&&a[order[next]]>=i) bit.add(order[next++],1);int right=min(n,a[i]);if(right>i) answer+=bit.sum(right)-bit.sum(i);}cout<<answer<<'\n';
    return 0;
}
