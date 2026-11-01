#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n, m, k;
        cin >> n >> m >> k;
        vector<long long> a(n + 1), b(m + 1);
        vector<int> c(n + 1), d(m + 1);
        for (int i = 1; i <= n; ++i) { cin >> a[i] >> c[i]; a[i] += a[i - 1]; }
        for (int j = 1; j <= m; ++j) { cin >> b[j] >> d[j]; b[j] += b[j - 1]; }
        vector<vector<array<char, 2>>> can(n + 1, vector<array<char, 2>>(m + 1, {0, 0}));
        for (int i = 0; i <= n && i <= k; ++i) {
            for (int j = 0; j <= m && i + j <= k; ++j) {
                bool empty = i + j == 0;
                if (i < n && (empty || can[i][j][1] || (can[i][j][0] && c[i] == 0)))
                    can[i + 1][j][0] = 1;
                if (j < m && (empty || can[i][j][0] || (can[i][j][1] && d[j] == 0)))
                    can[i][j + 1][1] = 1;
            }
        }
        long long best = LLONG_MIN;
        for (int i = max(0, k - m); i <= min(n, k); ++i) {
            int j = k - i;
            // 相同前缀的总价值固定；DP 只需记录能否到达。
            if (k == 0 || can[i][j][0] || can[i][j][1]) best = max(best, a[i] + b[j]);
        }
        if (best == LLONG_MIN) cout << "IMPOSSIBLE\n";
        else cout << best << '\n';
    }
}
