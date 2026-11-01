#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, a, b, c;
    cin >> n >> a >> b >> c;
    vector<int> dp(n + 1, -1000000);
    dp[0] = 0;  // 长度零恰好切成零段，其余长度起初不可达。
    for (int len = 1; len <= n; ++len) {
        for (int cut : {a, b, c}) {
            if (len >= cut && dp[len - cut] >= 0) {
                dp[len] = max(dp[len], dp[len - cut] + 1);
            }
        }
    }
    cout << dp[n] << '\n';
}
