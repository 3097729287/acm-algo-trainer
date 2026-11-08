#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> a(n, vector<int>(n)), b = a;
    for (auto &row : a)
        for (int &x : row)
            cin >> x;
    for (auto &row : b)
        for (int &x : row)
            cin >> x;
    int ans = 0;
    for (int dx = 1 - n; dx < n; dx++)
        for (int dy = 1 - n; dy < n; dy++) {
            vector<vector<int>> dp(n + 1, vector<int>(n + 1));
            for (int i = 0; i < n; i++)
                for (int j = 0; j < n; j++) {
                    int x = i + dx, y = j + dy;
                    if (x >= 0 && x < n && y >= 0 && y < n && a[i][j] == b[x][y]) {
                        dp[i + 1][j + 1] = 1 + min({dp[i][j + 1], dp[i + 1][j], dp[i][j]});
                        ans = max(ans, dp[i + 1][j + 1]);
                    }
                }
        }
    cout << ans << '\n';

    return 0;
}
