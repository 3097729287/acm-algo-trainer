#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n),answer;for(int &x:a)cin>>x;sort(a.begin(),a.end());
for(int i=0;i<n;++i)if(i==0||a[i]!=a[i-1])answer.push_back(a[i]);
cout<<answer.size()<<'\n';for(int i=0;i<(int)answer.size();++i)cout<<answer[i]<<(i+1==(int)answer.size()?'\n':' ');
    return 0;
}
