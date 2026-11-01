#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>score(n);for(int &x:score)cin>>x;int count[5]={};for(int i=0,v;i<m;++i){cin>>v;++count[v];}
int B=count[2]+1,C=count[3]+1,E=count[4]+1;auto index=[&](int a,int b,int c,int d){return ((a*B+b)*C+c)*E+d;};
vector<int>dp((count[1]+1)*B*C*E);dp[0]=score[0];
for(int a=0;a<=count[1];++a)for(int b=0;b<=count[2];++b)for(int c=0;c<=count[3];++c)for(int d=0;d<=count[4];++d){if(a+b+c+d==0)continue;int best=0;
    if(a)best=max(best,dp[index(a-1,b,c,d)]);if(b)best=max(best,dp[index(a,b-1,c,d)]);if(c)best=max(best,dp[index(a,b,c-1,d)]);if(d)best=max(best,dp[index(a,b,c,d-1)]);
    dp[index(a,b,c,d)]=best+score[a+2*b+3*c+4*d];
}cout<<dp[index(count[1],count[2],count[3],count[4])]<<'\n';
    return 0;
}
