#include <bits/stdc++.h>
using namespace std;
using i128=__int128_t;
void print(i128 x){if(x==0){cout<<0;return;}string s;while(x){s.push_back(char('0'+x%10));x/=10;}reverse(s.begin(),s.end());cout<<s;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<i128>power(m+1,1);for(int i=1;i<=m;++i)power[i]=power[i-1]*2;i128 total=0;
for(int row=0;row<n;++row){vector<int>a(m);for(int &v:a)cin>>v;vector<vector<i128>>dp(m,vector<i128>(m));
    for(int length=1;length<=m;++length)for(int l=0;l+length<=m;++l){int r=l+length-1;i128 weight=power[m-length+1];
        i128 left=weight*a[l]+(length==1?0:dp[l+1][r]),right=weight*a[r]+(length==1?0:dp[l][r-1]);dp[l][r]=max(left,right);
    }total+=dp[0][m-1];
}print(total);cout<<'\n';
    return 0;
}
