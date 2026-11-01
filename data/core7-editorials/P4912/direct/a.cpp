#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,target; cin>>n>>target;
vector<int> a(n),b(n);
for(int i=0;i<n;++i) cin>>a[i]>>b[i];
vector<vector<int>> w(n,vector<int>(n));
for(auto &row:w) for(int &x:row) cin>>x;
int bound=50*n,span=2*bound+1;
const int NEG=-1000000000;
vector<vector<int>> dp(n,vector<int>(span,NEG)); int answer=NEG;
for(int i=0;i<n;++i){
    dp[i][a[i]+bound]=b[i]; // 只用一个魔法，没有前驱影响。
    for(int j=0;j<i;++j){
        for(int index=0;index<span;++index){
            if(dp[j][index]==NEG) continue;
            int to=index+a[i]; // 两边使用同一偏移，直接加本次长度。
            if(to>=0&&to<span){
                dp[i][to]=max(dp[i][to],dp[j][index]+b[i]+w[j][i]);
            }
        }
    }
    if(target>=-bound&&target<=bound) answer=max(answer,dp[i][target+bound]);
}
cout<<(answer==NEG?-1:answer)<<'\n';
    return 0;
}
