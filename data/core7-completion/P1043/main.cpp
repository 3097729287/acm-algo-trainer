#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> pre(2 * n + 1), a(n);
    for (auto &x : a)
        cin >> x;
    for (int i = 1; i <= 2 * n; i++)
        pre[i] = pre[i - 1] + a[(i - 1) % n];
    long long answerMin = LLONG_MAX, answerMax = 0;
    for (int start = 0; start < n; start++) {
        const long long INF = LLONG_MAX / 4;
        vector<vector<long long>> lo(m + 1, vector<long long>(n + 1, INF)),
            hi(m + 1, vector<long long>(n + 1, -1));
        lo[0][0] = hi[0][0] = 1;
        for (int g = 1; g <= m; g++)
            for (int i = g; i <= n; i++)
                for (int j = g - 1; j < i; j++)
                    if (hi[g - 1][j] >= 0) {
                        long long v = ((pre[start + i] - pre[start + j]) % 10 + 10) % 10;
                        lo[g][i] = min(lo[g][i], lo[g - 1][j] * v);
                        hi[g][i] = max(hi[g][i], hi[g - 1][j] * v);
                    }
        answerMin = min(answerMin, lo[m][n]);
        answerMax = max(answerMax, hi[m][n]);
    }
    cout << answerMin << '\n' << answerMax << '\n';

    return 0;
}
