#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;
while(t--){int n,k;string s;cin>>n>>k>>s;int run=0;bool ok=true;
    for(char c:s){run=c=='1'?run+1:0;if(run>=k)ok=false;}
    if(!ok){cout<<"NO\n";continue;}
    vector<int> p(n);int value=1;
    for(int i=0;i<n;++i)if(s[i]=='1')p[i]=value++;
    for(int i=0;i<n;++i)if(s[i]=='0')p[i]=value++;
    cout<<"YES\n";for(int i=0;i<n;++i)cout<<p[i]<<(i+1==n?'\n':' ');
}
    return 0;
}
