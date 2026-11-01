#include <bits/stdc++.h>
using namespace std;
struct Fleet{
    vector<int>parent,size,offset,head;
    Fleet(int n):parent(n+1),size(n+1,1),offset(n+1),head(n+1){iota(parent.begin(),parent.end(),0);}
    int find(int x){if(parent[x]==x)return x;int old=parent[x];parent[x]=find(old);offset[x]+=offset[old];return parent[x];}
    void append(int i,int j){
        int a=find(i),b=find(j);if(a==b)return;
        int difference=size[b]+head[a]-head[b];
        if(size[a]<=size[b]){parent[a]=b;offset[a]=difference;size[b]+=size[a];}
        else{parent[b]=a;offset[b]=-difference;head[a]+=size[b];size[a]+=size[b];}
    }
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int commands;cin>>commands;Fleet groups(30000);
while(commands--){char type;int i,j;cin>>type>>i>>j;
    if(type=='M')groups.append(i,j);
    else{int a=groups.find(i),b=groups.find(j);if(a!=b)cout<<-1<<'\n';else cout<<abs(groups.offset[i]-groups.offset[j])-1<<'\n';}
}
    return 0;
}
