#include <bits/stdc++.h>
using namespace std;
long long prefix[9][9],memo[16][9][9][9][9];const long long INF=LLONG_MAX/4;
long long square(int x1,int y1,int x2,int y2){long long s=prefix[x2][y2]-prefix[x1][y2]-prefix[x2][y1]+prefix[x1][y1];return s*s;}
long long solve(int k,int x1,int y1,int x2,int y2){
    if((x2-x1)*(y2-y1)<k)return INF;auto &answer=memo[k][x1][y1][x2][y2];if(answer!=-1)return answer;
    if(k==1)return answer=square(x1,y1,x2,y2);answer=INF;
    for(int cut=x1+1;cut<x2;++cut){answer=min(answer,square(x1,y1,cut,y2)+solve(k-1,cut,y1,x2,y2));answer=min(answer,solve(k-1,x1,y1,cut,y2)+square(cut,y1,x2,y2));}
    for(int cut=y1+1;cut<y2;++cut){answer=min(answer,square(x1,y1,x2,cut)+solve(k-1,x1,cut,x2,y2));answer=min(answer,solve(k-1,x1,y1,x2,cut)+square(x1,cut,x2,y2));}
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int pieces;cin>>pieces;for(int i=1;i<=8;++i)for(int j=1;j<=8;++j){long long x;cin>>x;prefix[i][j]=x+prefix[i-1][j]+prefix[i][j-1]-prefix[i-1][j-1];}
memset(memo,-1,sizeof memo);cout<<solve(pieces,0,0,8,8)<<'\n';
    return 0;
}
