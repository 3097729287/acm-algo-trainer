#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    vector<long long> a(n + 1), dp(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    for (int i = 1; i <= n; i++) {
        int mask = 0;
        for (int j = i; j >= 1; j--) {
            int bit = 1 << (s[j - 1] - 'a');
            if (mask & bit)
                break;
            mask |= bit;
            dp[i] = max(dp[i], dp[j - 1] + a[i - j + 1]);
        }
    }
    cout << dp[n] << '\n';

    return 0;
}
