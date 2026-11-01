#include <bits/stdc++.h>
using namespace std;
int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int T,M; if(!(cin>>T>>M)) return 0;
    vector<int> dp(T+1,0);
    for(int i=0;i<M;++i){
        int t,v; cin>>t>>v;
        for(int c=T;c>=t;--c) dp[c]=max(dp[c],dp[c-t]+v);
    }
    cout<<dp[T]<<'\n';
}
