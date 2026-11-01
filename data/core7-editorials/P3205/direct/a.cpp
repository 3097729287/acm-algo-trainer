#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n; vector<int> h(n); for(int &x:h) cin>>x;
const int MOD=19650827;
vector<vector<int>> left(n,vector<int>(n)),right=left;
for(int i=0;i<n;++i) left[i][i]=1; // 单人只登记一份。
for(int length=2;length<=n;++length){
    for(int l=0;l+length<=n;++l){
        int r=l+length-1;
        if(h[l]<h[l+1]) left[l][r]+=left[l+1][r];
        if(h[l]<h[r]) left[l][r]+=right[l+1][r];
        if(h[r]>h[l]) right[l][r]+=left[l][r-1];
        if(h[r]>h[r-1]) right[l][r]+=right[l][r-1];
        left[l][r]%=MOD; right[l][r]%=MOD;
    }
}
cout<<(left[0][n-1]+right[0][n-1])%MOD<<'\n';
    return 0;
}
