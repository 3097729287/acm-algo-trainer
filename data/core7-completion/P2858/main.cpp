#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n), dp(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
        dp[i] = a[i] * n;
    }
    for (int len = 2; len <= n; len++) {
        long long day = n - len + 1;
        for (int l = 0; l + len <= n; l++) {
            int r = l + len - 1;
            dp[l] = max(a[l] * day + dp[l + 1], a[r] * day + dp[l]);
        }
    }
    cout << dp[0] << '\n';

    return 0;
}
