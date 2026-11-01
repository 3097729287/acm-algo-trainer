#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
const int MOD=1000000007;int m,d;string a,b;cin>>m>>d>>a>>b;
auto prefix=[&](const string&bound){
    vector<vector<int>>dp(2,vector<int>(m));dp[1][0]=1;
    for(int pos=0;pos<int(bound.size());++pos){
        vector<vector<int>>next(2,vector<int>(m));
        for(int tight=0;tight<2;++tight) for(int r=0;r<m;++r) if(dp[tight][r]){
            int limit=tight?bound[pos]-'0':9;
            for(int digit=(pos==0?1:0);digit<=limit;++digit){
                if((pos%2==1&&digit!=d)||(pos%2==0&&digit==d)) continue;
                int nt=tight&&digit==limit,nr=(r*10+digit)%m;next[nt][nr]+=dp[tight][r];if(next[nt][nr]>=MOD) next[nt][nr]-=MOD;
            }
        }
        dp.swap(next);
    }
    return (dp[0][0]+dp[1][0])%MOD;
};
int remainder=0;bool valid=true;
for(int i=0;i<int(a.size());++i){int digit=a[i]-'0';remainder=(remainder*10+digit)%m;if((i%2==1&&digit!=d)||(i%2==0&&digit==d)) valid=false;}
int include=valid&&remainder==0;cout<<(prefix(b)-prefix(a)+include+MOD)%MOD<<'\n';
    return 0;
}
