#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,target,k; cin>>n>>target>>k;
vector<int> parent(n),size(n,1); iota(parent.begin(),parent.end(),0);
auto find=[&](int x){
    while(parent[x]!=x){parent[x]=parent[parent[x]];x=parent[x];}
    return x;
};
for(int i=0,u,v;i<k;++i){
    cin>>u>>v; u=find(u-1); v=find(v-1);
    if(u==v) continue;
    if(size[u]<size[v]) swap(u,v);
    parent[v]=u; size[u]+=size[v];
}
vector<int> frequency(n+1);
for(int i=0;i<n;++i) if(find(i)==i) ++frequency[size[i]];
vector<char> reachable(n+1); reachable[0]=true;
for(int s=1;s<=n;++s){
    int left=frequency[s];
    // 同大小的连通块拆成若干整批，覆盖零到原数量。
    for(int batch=1;left;batch*=2){
        int count=min(batch,left); left-=count;
        int weight=s*count;
        for(int sum=n;sum>=weight;--sum){
            if(reachable[sum-weight]) reachable[sum]=true;
        }
    }
}
int answer=0;
for(int sum=1;sum<=n;++sum){
    // 只在严格更近时更新，平局留下先遇到的较小人数。
    if(reachable[sum]&&abs(sum-target)<abs(answer-target)) answer=sum;
}
cout<<answer<<'\n';
    return 0;
}
