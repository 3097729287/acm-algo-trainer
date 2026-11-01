#include <bits/stdc++.h>
using namespace std;
struct SuffixMinimum {
    int n;vector<int>tree;
    explicit SuffixMinimum(int size):n(size),tree(size+1,1000000000){}
    void add(int p,int value){for(;p;p-=p&-p) tree[p]=min(tree[p],value);}
    int query(int p) const {int value=1000000000;for(;p<=n;p+=p&-p) value=min(value,tree[p]);return value;}
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>distance(n+1);for(int i=1;i<=n;++i) cin>>distance[i];for(int i=1,power;i<=n;++i) cin>>power;
SuffixMinimum previous(n+1),right(n);previous.add(1,0);int last=0;
for(int i=1;i<=n;++i){right.add(min(n,i+distance[i]-1),last+1);int left=max(0,i-distance[i]);int current=min(previous.query(left+1)+1,right.query(i));previous.add(i+1,current);last=current;}cout<<last<<'\n';
    return 0;
}
