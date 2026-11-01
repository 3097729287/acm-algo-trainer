#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m,product=0;while(cin>>n>>m&&(n||m)){
    struct Patch{long long cost;unsigned need,absent,remove,added;};vector<Patch>patches;
    for(int i=0;i<m;++i){long long cost;string before,after;cin>>cost>>before>>after;Patch p{cost,0,0,0,0};
        for(int j=0;j<n;++j){unsigned bit=1u<<j;if(before[j]=='+')p.need|=bit;if(before[j]=='-')p.absent|=bit;
            if(after[j]=='-')p.remove|=bit;if(after[j]=='+')p.added|=bit;
        }patches.push_back(p);
    }
    unsigned count=1u<<n,initial=count-1;const long long INF=(1LL<<62);vector<long long>dist(count,INF);
    using State=pair<long long,unsigned>;priority_queue<State,vector<State>,greater<State>>pq;dist[initial]=0;pq.push({0,initial});
    while(!pq.empty()){auto [du,mask]=pq.top();pq.pop();if(du!=dist[mask])continue;if(mask==0)break;
        for(const auto &p:patches)if((mask&p.need)==p.need&&(mask&p.absent)==0){// 先清除，再加入；其它低位保持原样。
            unsigned next=(mask&~p.remove)|p.added;
            if(du+p.cost<dist[next]){dist[next]=du+p.cost;pq.push({dist[next],next});}
        }
    }
    cout<<"Product "<<++product<<'\n';if(dist[0]==INF)cout<<"Bugs cannot be fixed.\n\n";
    else cout<<"Fastest sequence takes "<<dist[0]<<" seconds.\n\n";
}
    return 0;
}
