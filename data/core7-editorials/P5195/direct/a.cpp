#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int W,H;cin>>W>>H;int cells=W*H,start=-1,knight=-1;vector<char>land(cells);
for(int i=0;i<cells;++i){cin>>land[i];if(land[i]=='2')start=i;if(land[i]=='3')knight=i;}
auto bfs=[&](int source,bool blockKnight){vector<int>dist(cells,-1);queue<int>q;dist[source]=0;q.push(source);
    const int dr[4]={-1,1,0,0},dc[4]={0,0,-1,1};
    while(!q.empty()){int u=q.front();q.pop();int r=u/W,c=u%W;
        for(int k=0;k<4;++k){int nr=r+dr[k],nc=c+dc[k];if(nr<0||nr>=H||nc<0||nc>=W)continue;int v=nr*W+nc;
            if(land[v]=='1'||(blockKnight&&land[v]=='3')||dist[v]!=-1)continue;
            dist[v]=dist[u]+1;q.push(v);
        }
    }return dist;
};
// 找到灌木之前，骑士格不可通过。
auto first=bfs(start,true),second=bfs(knight,false);int answer=INT_MAX;
for(int i=0;i<cells;++i)if(land[i]=='4'&&first[i]!=-1&&second[i]!=-1)answer=min(answer,first[i]+second[i]);
cout<<(answer==INT_MAX?-1:answer)<<'\n';
    return 0;
}
