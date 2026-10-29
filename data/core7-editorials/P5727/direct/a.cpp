#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long n; cin >> n; vector<long long> path{n};
while(n!=1){n=n%2?3*n+1:n/2;path.push_back(n);}
for(int i=(int)path.size()-1;i>=0;--i) cout << path[i] << (i==0?'\n':' ');
    return 0;
}
