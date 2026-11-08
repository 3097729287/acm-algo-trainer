#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n);
    long long ans = 0;
    for (auto &x : a) {
        cin >> x;
        ans += x * (n - x + 1);
    }
    for (int i = 1; i < n; i++)
        ans -= min(a[i - 1], a[i]) * (n - max(a[i - 1], a[i]) + 1);
    cout << ans << '\n';

    return 0;
}
