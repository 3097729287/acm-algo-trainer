#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;const int MOD=1000003;
while(tests--){
    int n,k;cin>>n>>k;vector<string>s(n);for(string &x:s) cin>>x;
    if(k<0||k>n){cout<<0<<'\n';continue;}
    int states=1<<n,length=s[0].size();vector<int>ways(states,1),size(states),index(states),required(states);
    for(int i=0;i<n;++i) index[1<<i]=i;
    for(int mask=1;mask<states;++mask) size[mask]=size[mask&(mask-1)]+1;
    for(int pos=0;pos<length;++pos){
        required[0]=0;ways[0]=1LL*ways[0]*26%MOD;
        for(int mask=1;mask<states;++mask){
            int bit=mask&-mask,old=required[mask^bit],letter=s[index[bit]][pos]=='?'?0:s[index[bit]][pos]-'a'+1;
            int value=old;
            if(old==-1) value=-1;
            else if(letter){if(old&&old!=letter) value=-1;else value=letter;}
            required[mask]=value;
            if(value<0) ways[mask]=0;else if(value==0) ways[mask]=1LL*ways[mask]*26%MOD;
        }
    }
    vector<vector<int>>choose(n+1,vector<int>(n+1));choose[0][0]=1;
    for(int i=1;i<=n;++i){choose[i][0]=choose[i][i]=1;for(int j=1;j<i;++j) choose[i][j]=(choose[i-1][j-1]+choose[i-1][j])%MOD;}
    long long answer=0;
    for(int mask=0;mask<states;++mask) if(size[mask]>=k){long long value=1LL*choose[size[mask]][k]*ways[mask]%MOD;if((size[mask]-k)%2) answer-=value;else answer+=value;answer%=MOD;}
    cout<<(answer+MOD)%MOD<<'\n';
}
    return 0;
}
