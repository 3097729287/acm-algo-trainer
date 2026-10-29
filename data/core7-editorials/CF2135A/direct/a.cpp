#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int t;cin>>t;while(t--){int n;cin>>n;vector<vector<int>> pos(n+1);vector<int> f(n+1);
    for(int i=1;i<=n;++i){int x;cin>>x;pos[x].push_back(i);f[i]=f[i-1];
        int count=pos[x].size();
        if(count>=x){int left=pos[x][count-x];f[i]=max(f[i],f[left-1]+x);}
    }
    cout<<f[n]<<'\n';
}
    return 0;
}
