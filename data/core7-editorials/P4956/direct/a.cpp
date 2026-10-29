#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n;
int total = n / 364;
for (int x = 100; x >= 0; --x) {
    if (total > x && (total-x)%3 == 0) {
        cout << x << '\n' << (total-x)/3 << '\n'; break;
    }
}
    return 0;
}
