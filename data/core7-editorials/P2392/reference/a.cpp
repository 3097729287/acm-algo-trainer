#include <bits/stdc++.h>
using namespace std;
int main(){
    ios::sync_with_stdio(false); cin.tie(nullptr);
    array<int,4> counts; for(int &s:counts) if(!(cin>>s)) return 0;
    int answer=0;
    for(int count:counts){
        vector<int> times(count); int S=0;
        for(int &t:times){cin>>t;S+=t;}
        int H=S/2; vector<int> dp(H+1,0);
        for(int t:times)
            for(int c=H;c>=t;--c) dp[c]=max(dp[c],dp[c-t]+t);
        answer+=S-dp[H];
    }
    cout<<answer<<'\n';
}
