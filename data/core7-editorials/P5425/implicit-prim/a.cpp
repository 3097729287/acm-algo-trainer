#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int N,K;cin>>N>>K;const long long P=2019201997,INF=(1LL<<60);
vector<long long>best(N,INF),treeEdges;vector<char>used(N);best[0]=0;
for(int step=0;step<N;++step){int u=-1;for(int v=0;v<N;++v)if(!used[v]&&(u==-1||best[v]<best[u]))u=v;
    used[u]=true;if(step)treeEdges.push_back(best[u]);
    for(int v=0;v<N;++v)if(!used[v]){long long x=min(u,v)+1,y=max(u,v)+1;
        long long w=(2019201913LL*x+2019201949LL*y)%P;best[v]=min(best[v],w);
    }
}sort(treeEdges.begin(),treeEdges.end());cout<<treeEdges[N-K]<<'\n';
    return 0;
}
