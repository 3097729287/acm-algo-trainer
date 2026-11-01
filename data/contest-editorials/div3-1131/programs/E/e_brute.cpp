#include <bits/stdc++.h>
using namespace std;
int main(){int t;cin>>t;while(t--){int n;cin>>n;vector<int>a(n);for(int &v:a)cin>>v;set<vector<int>>seen;queue<vector<int>>q;seen.insert(a);q.push(a);long long best=LLONG_MIN;
while(!q.empty()){auto v=q.front();q.pop();long long sum=0;for(int x:v)sum+=x;best=max(best,sum);for(int i=0;i+1<n;i++){auto w=v;w[i]=-v[i+1];w[i+1]=-v[i];if(seen.insert(w).second)q.push(w);}}cout<<best<<'\n';}}
