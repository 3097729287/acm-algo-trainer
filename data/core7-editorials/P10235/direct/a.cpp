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
int tests;cin>>tests;while(tests--){int n,k;cin>>n>>k;vector<int>a(n),values;for(int &x:a) cin>>x;values=a;sort(values.begin(),values.end());values.erase(unique(values.begin(),values.end()),values.end());for(int &x:a) x=lower_bound(values.begin(),values.end(),x)-values.begin()+1;
Fenwick total(values.size());long long high=0;for(int i=0;i<n;++i){high+=i-total.sum(a[i]);total.add(a[i],1);}
auto feasible=[&](long long limit){Fenwick bit(values.size());int segments=1,left=0;long long inversions=0;for(int i=0;i<n;++i){long long added=i-left-bit.sum(a[i]);if(inversions+added>limit){if(++segments>k) return false;while(left<i) bit.add(a[left++],-1);inversions=0;added=0;}inversions+=added;bit.add(a[i],1);}return true;};
long long low=0;while(low<high){long long middle=(low+high)/2;if(feasible(middle)) high=middle;else low=middle+1;}cout<<low<<'\n';}
    return 0;
}
