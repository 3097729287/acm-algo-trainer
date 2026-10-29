#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n; int bit=0, used=0, count;
while(cin >> count) {
    while(count--) { cout << bit; if(++used%n==0) cout << '\n'; }
    bit=1-bit;
}
    return 0;
}
