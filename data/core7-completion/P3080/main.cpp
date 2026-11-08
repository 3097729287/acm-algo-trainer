#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> a(n + 1);
    for (int i = 0; i < n; i++)
        cin >> a[i];
    a[n] = 0;
    sort(a.begin(), a.end());
    int N = n + 1, start = lower_bound(a.begin(), a.end(), 0) - a.begin();
    const long long INF = 1LL << 62;
    vector<vector<array<long long, 2>>> dp(N, vector<array<long long, 2>>(N, {INF, INF}));
    dp[start][start] = {0, 0};
    for (int len = 1; len <= N; len++)
        for (int l = 0; l + len <= N; l++) {
            int r = l + len - 1;
            if (l > start || r < start)
                continue;
            long long remaining = N - len;
            for (int side = 0; side < 2; side++)
                if (dp[l][r][side] < INF) {
                    int pos = side ? r : l;
                    if (l)
                        dp[l - 1][r][0] =
                            min(dp[l - 1][r][0], dp[l][r][side] + (a[pos] - a[l - 1]) * remaining);
                    if (r + 1 < N)
                        dp[l][r + 1][1] =
                            min(dp[l][r + 1][1], dp[l][r][side] + (a[r + 1] - a[pos]) * remaining);
                }
        }
    cout << min(dp[0][n][0], dp[0][n][1]) << '\n';

    return 0;
}
