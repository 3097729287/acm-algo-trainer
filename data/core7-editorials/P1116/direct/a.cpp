#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n);for(int &x:a)cin>>x;long long answer=0;
for(int i=0;i<n;++i)for(int j=i+1;j<n;++j)answer+=a[i]>a[j];
cout<<answer<<'\n';
    return 0;
}
