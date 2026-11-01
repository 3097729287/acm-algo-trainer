#include <bits/stdc++.h>
using namespace std;
int n,m;long long answer;
void dfs(int length,int previous,int sum){if(length==n){answer+=sum==m;return;}for(int v=1;v<=previous;v++){int next=sum+previous%v;if(next<=m)dfs(length+1,v,next);}}
int main(){int t;cin>>t;while(t--){cin>>n>>m;answer=0;for(int first=1;first<=m+2;first++)dfs(1,first,0);cout<<answer%998244353<<'\n';}}
