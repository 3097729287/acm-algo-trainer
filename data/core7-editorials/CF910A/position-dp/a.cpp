#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,d;cin>>n>>d;string s;cin>>s;const int INF=1000000000;
vector<int>best(n,INF);best[0]=0;
// 枚举最后一跳的来源，只允许落在荷叶。
for(int i=1;i<n;++i)if(s[i]=='1'){
    for(int j=max(0,i-d);j<i;++j)if(best[j]!=INF)best[i]=min(best[i],best[j]+1);
}cout<<(best[n-1]==INF?-1:best[n-1])<<'\n';
    return 0;
}
