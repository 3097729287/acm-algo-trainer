#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>off(m),on(m);
for(int i=0;i<m;++i) for(int j=0,value;j<n;++j){cin>>value;if(value==1) off[i]|=1<<j;else if(value==-1) on[i]|=1<<j;}
int states=1<<n;vector<int>distance(states,-1);queue<int>ready;distance[states-1]=0;ready.push(states-1);
while(!ready.empty()){
    int mask=ready.front();ready.pop();
    for(int i=0;i<m;++i){
        int next=(mask&~off[i])|on[i];
        if(distance[next]<0){distance[next]=distance[mask]+1;ready.push(next);}
    }
}
cout<<distance[0]<<'\n';
    return 0;
}
