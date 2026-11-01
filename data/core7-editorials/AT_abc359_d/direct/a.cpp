#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;string s;cin>>n>>k>>s;const int MOD=998244353;
int states=1<<(k-1),keep=states-1;vector<char>palindrome(1<<k,true);
for(int bits=0;bits<(1<<k);++bits) for(int i=0;i<k/2;++i) if(((bits>>i)&1)!=((bits>>(k-1-i))&1)) palindrome[bits]=false;
vector<int>dp(states),next(states);dp[0]=1;
for(int pos=0;pos<n;++pos){
    fill(next.begin(),next.end(),0);
    for(int mask=0;mask<states;++mask) if(dp[mask]) for(int c=0;c<2;++c){
        if(s[pos]!='?'&&s[pos]!=char('A'+c)) continue;
        int bits=(mask<<1)|c;if(pos+1>=k&&palindrome[bits]) continue;
        int target=bits&keep;next[target]+=dp[mask];if(next[target]>=MOD) next[target]-=MOD;
    }
    dp.swap(next);
}
int answer=0;for(int value:dp){answer+=value;if(answer>=MOD) answer-=MOD;}
cout<<answer<<'\n';
    return 0;
}
