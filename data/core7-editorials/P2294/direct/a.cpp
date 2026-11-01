#include <bits/stdc++.h>
using namespace std;
struct WeightedDSU{
    vector<int>parent,size;vector<long long>offset;
    WeightedDSU(int n):parent(n+1),size(n+1,1),offset(n+1){iota(parent.begin(),parent.end(),0);}
    int find(int x){if(parent[x]==x)return x;int old=parent[x];parent[x]=find(old);offset[x]+=offset[old];return parent[x];}
    bool constrain(int x,int y,long long value){
        int a=find(x),b=find(y);long long difference=value+offset[x]-offset[y];
        if(a==b)return difference==0;
        if(size[a]>=size[b]){parent[b]=a;offset[b]=difference;size[a]+=size[b];}
        else{parent[a]=b;offset[a]=-difference;size[b]+=size[a];}
        return true;
    }
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n,m;cin>>n>>m;WeightedDSU groups(n);bool possible=true;
    for(int i=0;i<m;++i){int s,t;long long value;cin>>s>>t>>value;if(!groups.constrain(s-1,t,value))possible=false;}
    cout<<(possible?"true":"false")<<'\n';
}
    return 0;
}
