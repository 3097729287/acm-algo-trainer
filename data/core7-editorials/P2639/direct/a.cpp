#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int h,n; cin>>h>>n;
vector<char> reachable(h+1); reachable[0]=true;
for(int i=0,w;i<n;++i){
    cin>>w;
    // 倒序读取未使用当前捆的旧状态。
    for(int sum=h;sum>=w;--sum){
        if(reachable[sum-w]) reachable[sum]=true;
    }
}
for(int sum=h;sum>=0;--sum){
    if(reachable[sum]){cout<<sum<<'\n';break;}
}
    return 0;
}
