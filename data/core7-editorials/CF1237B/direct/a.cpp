#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>entered(n);for(int &x:entered)cin>>x;vector<bool>left(n+1);int next=0,answer=0;
// 当前最早仍在洞内的车，决定出口车有没有超车。
for(int i=0;i<n;++i){int x;cin>>x;while(next<n&&left[entered[next]])++next;
    if(entered[next]!=x)++answer;left[x]=true;
}
cout<<answer<<'\n';
    return 0;
}
