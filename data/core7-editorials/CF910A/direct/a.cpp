#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,d;cin>>n>>d;string s;cin>>s;int current=0,jumps=0;
// 同样跳数下保持位置最靠右。
while(current<n-1){
    int next=min(n-1,current+d);while(next>current&&s[next]=='0')--next;
    if(next==current){cout<<-1<<'\n';return 0;}
    current=next;++jumps;
}cout<<jumps<<'\n';
    return 0;
}
