#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin>>n;
vector<long long> a(n); vector<int> b(n),capacity(n+1);
for(auto &x:a) cin>>x;
for(int &x:b) cin>>x;
for(int i=0;i<n;++i){
    capacity[i+1]=max(capacity[i],max(0,capacity[i]-b[i])+1);
}
const long long NEG=LLONG_MIN/4;
vector<long long> dp(n+1,NEG); dp[0]=0;
vector<vector<unsigned char>> take(n,vector<unsigned char>(n+1));
long long best=0; int first=-1,weight=0;
for(int i=n-1;i>=0;--i){
    // 先把i当作最终首格：W=0始终可行，正W受前缀数量约束。
    int upper=max(0,capacity[i]-b[i]);
    for(int w=0;w<=upper;++w){
        if(dp[w]!=NEG&&a[i]+dp[w]>best){best=a[i]+dp[w];first=i;weight=w;}
    }
    // 再把i放入后缀背包；零重量也仅处理一次。
    for(int w=n;w>=b[i];--w){
        if(dp[w-b[i]]!=NEG&&dp[w-b[i]]+a[i]>dp[w]){
            dp[w]=dp[w-b[i]]+a[i]; take[i][w]=1;
        }
    }
}
if(first<0){cout<<"0\n\n0\n";return 0;}
vector<int> suffix,prefix; int remaining=weight;
for(int i=first+1;i<n;++i){
    if(take[i][remaining]){suffix.push_back(i);remaining-=b[i];}
}
// 恢复将来被删的旧格子，这些也必须写进完整选择过程。
int needed=weight?b[first]+weight:0;
for(int i=first-1;i>=0;--i){
    if(needed>capacity[i]){
        prefix.push_back(i);
        needed=needed==1?0:needed-1+b[i];
    }
}
reverse(prefix.begin(),prefix.end());
vector<int> chosen=prefix; chosen.push_back(first);
chosen.insert(chosen.end(),suffix.begin(),suffix.end());
cout<<chosen.size()<<'\n';
for(int i:chosen) cout<<i+1<<' ';
cout<<'\n'<<best<<'\n';
    return 0;
}
