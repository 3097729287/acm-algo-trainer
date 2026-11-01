#include <bits/stdc++.h>
using namespace std;
int levels;
struct Node{unsigned long long id,begin,subtree;};
struct Operation{int type;unsigned long long node;int index;};
Node describe(unsigned long long u){
    int depth=0;for(auto x=u;x;x>>=1)++depth;unsigned long long begin=1;
    for(int level=2;level<=depth;++level)begin+=((u>>(depth-level))&1ULL)?(1ULL<<(levels-level+1)):1ULL;
    return {u,begin,(1ULL<<(levels-depth+1))-1};
}
struct RegionDSU{
    vector<int>parent,size;vector<unsigned long long>mass;
    RegionDSU(const vector<unsigned long long>&weights):parent(weights.size()),size(weights.size(),1),mass(weights){iota(parent.begin(),parent.end(),0);}
    int find(int x){return parent[x]==x?x:parent[x]=find(parent[x]);}
    void merge(int a,int b){a=find(a);b=find(b);if(a==b)return;if(size[a]<size[b])swap(a,b);parent[b]=a;size[a]+=size[b];mass[a]+=mass[b];}
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int operations;cin>>levels>>operations;vector<Operation>op(operations);vector<Node>nodes={describe(1)};
for(auto &o:op){cin>>o.type>>o.node;nodes.push_back(describe(o.node));}
sort(nodes.begin(),nodes.end(),[](const Node&a,const Node&b){return a.begin<b.begin;});
nodes.erase(unique(nodes.begin(),nodes.end(),[](const Node&a,const Node&b){return a.id==b.id;}),nodes.end());
int count=(int)nodes.size();vector<pair<unsigned long long,int>>index;for(int i=0;i<count;++i)index.push_back({nodes[i].id,i});sort(index.begin(),index.end());
auto index_of=[&](unsigned long long u){return lower_bound(index.begin(),index.end(),make_pair(u,-1))->second;};
vector<int>parent(count,-1),stack={0},deleted(count);vector<unsigned long long>mass(count);
for(int i=0;i<count;++i)mass[i]=nodes[i].subtree;
for(int i=1;i<count;++i){
    while(nodes[i].begin>=nodes[stack.back()].begin+nodes[stack.back()].subtree)stack.pop_back();
    parent[i]=stack.back();mass[parent[i]]-=nodes[i].subtree;stack.push_back(i);
}
for(auto &o:op){o.index=index_of(o.node);if(o.type==1&&o.index!=0)++deleted[o.index];}
RegionDSU groups(mass);for(int i=1;i<count;++i)if(deleted[i]==0)groups.merge(i,parent[i]);
unsigned long long answer=0;
for(int i=operations-1;i>=0;--i){int u=op[i].index;
    if(op[i].type==2)answer^=groups.mass[groups.find(u)];
    else if(u!=0&&--deleted[u]==0)groups.merge(u,parent[u]);
}
cout<<answer<<'\n';
    return 0;
}
