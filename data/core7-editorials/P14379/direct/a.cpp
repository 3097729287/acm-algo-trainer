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
int n,q;cin>>n>>q;vector<int>a(n+1);Fenwick ones(n),twos(n);long long noOne=0,twoFree=0;int gap=0,count=0;
auto choose=[](long long x){return x*(x-1)/2;};
for(int i=1;i<=n;++i){cin>>a[i];if(a[i]==1){ones.tree[i]=1;noOne+=choose(gap);gap=0;++count;}else ++gap;if(a[i]==2){twos.tree[i]=1;twoFree+=choose(count);count=0;}}
noOne+=choose(gap);twoFree+=choose(count);for(int i=1;i<=n;++i){int j=i+(i&-i);if(j<=n){ones.tree[j]+=ones.tree[i];twos.tree[j]+=twos.tree[i];}}
int numberOne=ones.sum(n),numberTwo=twos.sum(n);
auto neighbors=[&](const Fenwick &bit,int total,int p,bool present){int before=bit.sum(p-1);int l=before?bit.kth(before):0;int nextRank=before+1+present;int r=nextRank<=total?bit.kth(nextRank):n+1;return pair<int,int>{l,r};};
auto change=[&](int p,int value,int delta){
    if(value==1){auto [l,r]=neighbors(ones,numberOne,p,delta==-1);long long split=choose(p-l-1)+choose(r-p-1)-choose(r-l-1);noOne+=delta*split;auto [left,right]=neighbors(twos,numberTwo,p,false);int c=ones.sum(right-1)-ones.sum(left);twoFree+=delta==1?c:-(c-1);ones.add(p,delta);numberOne+=delta;}
    else if(value==2){auto [l,r]=neighbors(twos,numberTwo,p,delta==-1);int middle=ones.sum(p);long long left=middle-ones.sum(l),right=ones.sum(r-1)-middle;twoFree-=delta*left*right;twos.add(p,delta);numberTwo+=delta;}
};
while(q--){int p,value;cin>>p>>value;int oldCategory=min(a[p],3),newCategory=min(value,3);if(oldCategory!=newCategory){change(p,oldCategory,-1);change(p,newCategory,1);}a[p]=value;cout<<choose(n)-noOne-twoFree<<'\n';}
    return 0;
}
