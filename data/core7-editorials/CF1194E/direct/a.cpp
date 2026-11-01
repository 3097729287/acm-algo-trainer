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
int n;cin>>n;struct Horizontal{int y,l,r;};struct Vertical{int x,low,high;};vector<Horizontal>h;vector<Vertical>v;vector<int>xs;
for(int i=0,x1,y1,x2,y2;i<n;++i){cin>>x1>>y1>>x2>>y2;if(y1==y2) h.push_back({y1,min(x1,x2),max(x1,x2)});else{v.push_back({x1,min(y1,y2),max(y1,y2)});xs.push_back(x1);}}sort(h.begin(),h.end(),[](Horizontal a,Horizontal b){return a.y<b.y;});sort(v.begin(),v.end(),[](Vertical a,Vertical b){return a.high<b.high;});sort(xs.begin(),xs.end());xs.erase(unique(xs.begin(),xs.end()),xs.end());
long long answer=0;for(int bottom=0;bottom<(int)h.size();++bottom){Fenwick bit(xs.size());for(auto segment:v) if(segment.low<=h[bottom].y&&h[bottom].y<=segment.high) bit.add(lower_bound(xs.begin(),xs.end(),segment.x)-xs.begin()+1,1);int expired=0;for(int top=bottom+1;top<(int)h.size();++top){while(expired<(int)v.size()&&v[expired].high<h[top].y){auto segment=v[expired++];if(segment.low<=h[bottom].y&&h[bottom].y<=segment.high) bit.add(lower_bound(xs.begin(),xs.end(),segment.x)-xs.begin()+1,-1);}if(h[top].y==h[bottom].y) continue;int l=max(h[bottom].l,h[top].l),r=min(h[bottom].r,h[top].r);if(l>r) continue;int left=lower_bound(xs.begin(),xs.end(),l)-xs.begin(),right=upper_bound(xs.begin(),xs.end(),r)-xs.begin();long long count=bit.sum(right)-bit.sum(left);answer+=count*(count-1)/2;}}
cout<<answer<<'\n';
    return 0;
}
