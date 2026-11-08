#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, p;
    cin >> n >> p;
    vector<int> inv(n + 1);
    inv[1] = 1;
    cout << 1 << '\n';
    for (int i = 2; i <= n; i++) {
        inv[i] = 1LL * (p - p / i) * inv[p % i] % p;
        cout << inv[i] << '\n';
    }

    return 0;
}
