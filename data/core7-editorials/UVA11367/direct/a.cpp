#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>price(n);for(int &x:price)cin>>x;vector<vector<pair<int,int>>>graph(n);
for(int i=0;i<m;++i){int u,v,d;cin>>u>>v>>d;graph[u].push_back({v,d});graph[v].push_back({u,d});}
int queries;cin>>queries;const long long inf=LLONG_MAX/4;
while(queries--){int capacity,start,target;cin>>capacity>>start>>target;vector<vector<long long>>distance(n,vector<long long>(capacity+1,inf));
    priority_queue<tuple<long long,int,int>,vector<tuple<long long,int,int>>,greater<tuple<long long,int,int>>>todo;
    distance[start][0]=0;todo.push({0,start,0});long long answer=-1;
    while(!todo.empty()){auto [cost,u,fuel]=todo.top();todo.pop();if(cost!=distance[u][fuel])continue;
        if(u==target){answer=cost;break;}
        // 购油付钱，行驶只扣油；费用不能重复记在道路上。
        if(fuel<capacity&&cost+price[u]<distance[u][fuel+1]){distance[u][fuel+1]=cost+price[u];todo.push({distance[u][fuel+1],u,fuel+1});}
        for(auto [v,length]:graph[u])if(length<=fuel&&cost<distance[v][fuel-length]){distance[v][fuel-length]=cost;todo.push({cost,v,fuel-length});}
    }
    if(answer<0)cout<<"impossible\n";else cout<<answer<<'\n';
}
    return 0;
}
