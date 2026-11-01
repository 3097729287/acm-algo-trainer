#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int h,w,total,sx,sy;cin>>h>>w>>total>>sx>>sy;int n,m;cin>>n>>m;int cells=h*w;
vector<vector<char>>danger(total+1,vector<char>(cells));vector<vector<int>>fruit(total+1,vector<int>(cells));int fruitIndex=0;
for(int i=0;i<n;++i){
    int begin,end,small;cin>>begin>>end>>small;int bit=small?1<<fruitIndex++:0;
    for(int t=begin;t<end;++t){int x,y;cin>>x>>y;int p=(y-1)*w+x-1;if(small) fruit[t][p]|=bit;else danger[t][p]=true;}
}
int start=(sy-1)*w+sx-1;
if(danger[1][start]){cout<<-1<<'\n';return 0;}
vector<vector<int>>neighbors(cells);
for(int u=0;u<cells;++u) for(int v=0;v<cells;++v) if(abs(u/w-v/w)+abs(u%w-v%w)<=1) neighbors[u].push_back(v);
int states=1<<m,INF=1000000000;vector<int>dp(cells*states,INF),next(cells*states,INF);dp[start*states+fruit[1][start]]=0;
for(int t=2;t<=total;++t){
    fill(next.begin(),next.end(),INF);
    for(int u=0;u<cells;++u) for(int mask=0;mask<states;++mask) if(dp[u*states+mask]<INF){
        for(int v:neighbors[u]) if(!danger[t][v]){
            int target=v*states+(mask|fruit[t][v]);next[target]=min(next[target],dp[u*states+mask]+(u!=v));
        }
    }
    dp.swap(next);
}
int answer=INF;for(int p=0;p<cells;++p) answer=min(answer,dp[p*states+states-1]);cout<<(answer==INF?-1:answer)<<'\n';
    return 0;
}
