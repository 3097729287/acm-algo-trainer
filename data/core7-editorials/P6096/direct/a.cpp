#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int N,S;cin>>N>>S;unordered_map<string,int>id;id.reserve(2*S+1);
for(int i=0;i<S;++i){string name;cin>>name;id.emplace(name,i);}
vector<vector<int>>line(N),contains(S);
for(int i=0;i<N;++i){int length;cin>>length;line[i].reserve(length);
    for(int j=0;j<length;++j){string name;cin>>name;int v=id.at(name);line[i].push_back(v);contains[v].push_back(i);}
}
string from,to;cin>>from>>to;int A=id.at(from),B=id.at(to);vector<int>d(S,-1),level(N,-1),order;queue<int>q;d[A]=0;q.push(A);
while(!q.empty()){int u=q.front();q.pop();for(int route:contains[u])if(level[route]==-1){
    level[route]=d[u]+1;order.push_back(route);
    for(int v:line[route])if(d[v]==-1){d[v]=level[route];q.push(v);}
}}
if(d[B]==-1){cout<<"-1\n0\n";return 0;}
const long long NEG=-(1LL<<60);vector<long long>best(S,NEG);best[A]=0;
// BFS 发现顺序按票价层递增；上一层时间此时已经完整。
for(int route:order){int c=level[route];long long minus=NEG,plus=NEG;
    for(int i=0;i<(int)line[route].size();++i){int u=line[route][i];if(d[u]==c-1&&best[u]!=NEG){minus=max(minus,best[u]-i);plus=max(plus,best[u]+i);}}
    if(minus==NEG)continue;
    for(int j=0;j<(int)line[route].size();++j){int v=line[route][j];if(d[v]==c)best[v]=max({best[v],minus+j,plus-j});}
}
cout<<d[B]<<'\n'<<best[B]<<'\n';
    return 0;
}
