#include <bits/stdc++.h>
using namespace std;
using i128=__int128;
i128 gcd128(i128 a,i128 b){while(b){i128 r=a%b;a=b;b=r;}return a;}
struct Fraction{
    i128 p=0,q=1;
    void reduce(){i128 g=gcd128(p,q);p/=g;q/=g;}
    void add(const Fraction &other){i128 g=gcd128(q,other.q);p=p*(other.q/g)+other.p*(q/g);q=q*(other.q/g);reduce();}
};
void print128(i128 value){if(value==0){cout<<0;return;}string s;while(value){s.push_back(char('0'+value%10));value/=10;}reverse(s.begin(),s.end());cout<<s;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<vector<int>>graph(n+1);vector<int>indegree(n+1);vector<Fraction>water(n+1);
for(int u=1;u<=n;++u){int d;cin>>d;while(d--){int v;cin>>v;graph[u].push_back(v);++indegree[v];}}
for(int u=1;u<=m;++u)water[u].p=1;
queue<int>ready;for(int u=1;u<=n;++u)if(!indegree[u])ready.push(u);
while(!ready.empty()){int u=ready.front();ready.pop();if(graph[u].empty())continue;
    Fraction part{water[u].p,water[u].q*int(graph[u].size())};part.reduce();
    for(int v:graph[u]){water[v].add(part);if(--indegree[v]==0)ready.push(v);}
}for(int u=1;u<=n;++u)if(graph[u].empty()){print128(water[u].p);cout<<' ';print128(water[u].q);cout<<'\n';}
    return 0;
}
