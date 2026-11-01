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
int n;string a,b;cin>>n>>a>>b;array<vector<int>,26>positions;array<int,26>next={};
for(int i=0;i<n;++i) positions[b[i]-'A'].push_back(i+1);
Fenwick bit(n);long long answer=0;for(int i=0;i<n;++i){int letter=a[i]-'A',p=positions[letter][next[letter]++];answer+=i-bit.sum(p);bit.add(p,1);}
cout<<answer<<'\n';
    return 0;
}
