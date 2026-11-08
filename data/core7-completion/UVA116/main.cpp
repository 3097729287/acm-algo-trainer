#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    while (cin >> m >> n) {
        vector<vector<long long>> a(m, vector<long long>(n)), dp = a;
        vector<vector<int>> next(m, vector<int>(n));
        for (auto &r : a)
            for (auto &x : r)
                cin >> x;
        for (int r = 0; r < m; r++)
            dp[r][n - 1] = a[r][n - 1];
        for (int c = n - 2; c >= 0; c--)
            for (int r = 0; r < m; r++) {
                array<int, 3> rows = {(r + m - 1) % m, r, (r + 1) % m};
                sort(rows.begin(), rows.end());
                int best = rows[0];
                for (int u : rows)
                    if (dp[u][c + 1] < dp[best][c + 1])
                        best = u;
                dp[r][c] = a[r][c] + dp[best][c + 1];
                next[r][c] = best;
            }
        int root = 0;
        for (int r = 1; r < m; r++)
            if (dp[r][0] < dp[root][0])
                root = r;
        int r = root;
        for (int c = 0; c < n; c++) {
            cout << r + 1 << (c + 1 == n ? '\n' : ' ');
            if (c + 1 < n)
                r = next[r][c];
        }
        cout << dp[root][0] << '\n';
    }

    return 0;
}
