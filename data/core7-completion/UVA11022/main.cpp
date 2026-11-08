#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    while (cin >> s && s != "*") {
        int n = s.size();
        vector<vector<int>> lcp(n + 1, vector<int>(n + 1)), dp(n, vector<int>(n));
        for (int i = n - 1; i >= 0; i--)
            for (int j = n - 1; j >= 0; j--)
                if (s[i] == s[j])
                    lcp[i][j] = lcp[i + 1][j + 1] + 1;
        for (int len = 1; len <= n; len++)
            for (int l = 0; l + len <= n; l++) {
                int r = l + len - 1;
                dp[l][r] = len;
                for (int mid = l; mid < r; mid++)
                    dp[l][r] = min(dp[l][r], dp[l][mid] + dp[mid + 1][r]);
                for (int p = 1; p < len; p++)
                    if (len % p == 0 && lcp[l][l + p] >= len - p)
                        dp[l][r] = min(dp[l][r], dp[l][l + p - 1]);
            }
        cout << dp[0][n - 1] << '\n';
    }

    return 0;
}
