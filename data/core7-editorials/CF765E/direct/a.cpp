#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<vector<int>>edge(n);vector<int>to;for(int i=1,u,v;i<n;++i){cin>>u>>v;--u;--v;int id=to.size();to.push_back(v);to.push_back(u);edge[u].push_back(id);edge[v].push_back(id^1);}
vector<int>parentEdge(n,-1),order{0},message(to.size(),-1);parentEdge[0]=-2;
for(size_t i=0;i<order.size();++i){int u=order[i];for(int e:edge[u])if(e!=parentEdge[u]){int v=to[e];parentEdge[v]=e^1;order.push_back(v);}}
for(int i=n-1;i>0;--i){int u=order[i],length=0;bool ok=true;
    for(int e:edge[u])if(e!=parentEdge[u]){int value=message[e^1];if(value<0||(length&&length!=value))ok=false;length=value;}
    message[parentEdge[u]]=ok?length+1:-1;
}
int answer=INT_MAX;for(int u:order){map<int,int>frequency;int invalid=0;
    for(int e:edge[u]){int value=message[e^1];if(value<0)++invalid;else ++frequency[value];}
    if(!invalid&&frequency.size()<=2){int length=0;for(auto [value,count]:frequency)length+=value;while(length%2==0)length/=2;answer=min(answer,length);}
    for(int e:edge[u])if(e!=parentEdge[u]){int value=message[e^1];if(value<0)--invalid;else if(--frequency[value]==0)frequency.erase(value);
        message[e]=(!invalid&&frequency.size()<=1)?1+(frequency.empty()?0:frequency.begin()->first):-1;
        if(value<0)++invalid;else ++frequency[value];
    }
}cout<<(answer==INT_MAX?-1:answer)<<'\n';
    return 0;
}
