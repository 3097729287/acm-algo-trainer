#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;cin>>tests;while(tests--){int n;cin>>n;vector<long long>a(n+2),prefix(n+1);
    for(int i=1;i<=n;++i){cin>>a[i];prefix[i]=prefix[i-1]+a[i];}
    string answer;
    for(int m=1;m<n;++m){long long left=prefix[m],right=prefix[n]-left;
        bool win=left>right;
        if(!win&&a[m]>a[m+1]&&left+a[m+1]>right-a[m+1]&&a[m]+a[m+1]>a[m+2])win=true;
        answer.push_back(win?'1':'0');
    }
    cout<<answer<<'\n';
}
    return 0;
}
