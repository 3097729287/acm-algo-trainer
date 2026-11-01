#include <bits/stdc++.h>
using namespace std;
long long power(long long base,int exponent){
    const long long MOD=998244353;
    if(base==0&&exponent==0) return 0;
    long long answer=1;
    while(exponent){
        if(exponent&1) answer=answer*base%MOD;
        base=base*base%MOD; exponent>>=1;
    }
    return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests; cin>>tests;
while(tests--){
    int n; cin>>n; vector<int>a(n); for(int &x:a) cin>>x;
    vector<vector<long long>> score(n,vector<long long>(n));
    for(int i=0;i<n;++i) for(int j=0;j<n;++j) score[i][j]=power(a[i],a[j]);
    vector<vector<long long>> left(n,vector<long long>(n)),right=left;
    for(int length=1;length<n;++length){
        for(int l=0;l+length<=n;++l){
            int r=l+length-1;
            long long afterLeft=length==1?0:left[l+1][r];
            long long afterRight=length==1?0:right[l][r-1];
            if(l>0) left[l][r]=max(score[l-1][l]+afterLeft,score[l-1][r]+afterRight);
            if(r+1<n) right[l][r]=max(score[r+1][l]+afterLeft,score[r+1][r]+afterRight);
        }
    }
    cout<<max(left[1][n-1],right[0][n-2])<<'\n';
}
    return 0;
}
