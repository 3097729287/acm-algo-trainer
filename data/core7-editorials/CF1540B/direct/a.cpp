#include <bits/stdc++.h>
using namespace std;
long long modPower(long long base,long long exponent){
    const long long MOD=1000000007;long long answer=1;
    while(exponent){if(exponent&1) answer=answer*base%MOD;base=base*base%MOD;exponent>>=1;}
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>g(n);
for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;g[u].push_back(v);g[v].push_back(u);}
vector<vector<int>>distance(n,vector<int>(n,-1));
for(int root=0;root<n;++root){
    vector<int>order={root};distance[root][root]=0;
    for(size_t pos=0;pos<order.size();++pos){int u=order[pos];for(int v:g[u]) if(distance[root][v]<0){distance[root][v]=distance[root][u]+1;order.push_back(v);}}
}
const long long MOD=1000000007,HALF=500000004;
vector<vector<long long>>probability(n+1,vector<long long>(n+1));
for(int b=0;b<=n;++b) probability[0][b]=1;
for(int a=1;a<=n;++a) for(int b=1;b<=n;++b) probability[a][b]=(probability[a-1][b]+probability[a][b-1])*HALF%MOD;
long long answer=0;
for(int root=0;root<n;++root){
    for(int u=0;u<n;++u) for(int v=0;v<u;++v){
        int length=distance[u][v];
        int a=(distance[root][u]+length-distance[root][v])/2,b=length-a;
        answer+=probability[a][b];if(answer>=MOD) answer-=MOD;
    }
}
cout<<answer*modPower(n,MOD-2)%MOD<<'\n';
    return 0;
}
