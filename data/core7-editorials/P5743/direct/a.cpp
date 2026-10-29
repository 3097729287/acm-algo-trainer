#include <bits/stdc++.h>
using namespace std;
long long previous(long long remaining){return (remaining+1)*2;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;long long peaches=1;
for(int day=n;day>1;--day)peaches=previous(peaches);
cout<<peaches<<'\n';
    return 0;
}
