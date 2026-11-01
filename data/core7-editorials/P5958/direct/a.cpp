#include <bits/stdc++.h>
using namespace std;
struct Ratio{long long numerator,denominator;};
bool lessRatio(const Ratio &a,const Ratio &b){return a.numerator*b.denominator<b.numerator*a.denominator;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<int>parent(n,-1),children(n),size(n,1);
for(int u=1;u<n;++u){cin>>parent[u];--parent[u];++children[parent[u]];}
for(int u=n-1;u>0;--u) size[parent[u]]+=size[u];
vector<Ratio>limit(n,{0,1});Ratio answer={0,1};
for(int u=n-1;u>=0;--u){
    if(!children[u]) limit[u]={1,1};
    if(size[u]>k&&lessRatio(answer,limit[u])) answer=limit[u];
    if(u){
        Ratio edge={size[u],size[parent[u]]-1};
        Ratio candidate=lessRatio(limit[u],edge)?limit[u]:edge;
        if(lessRatio(limit[parent[u]],candidate)) limit[parent[u]]=candidate;
    }
}
cout<<fixed<<setprecision(10)<<(long double)answer.numerator/answer.denominator<<'\n';
    return 0;
}
