#include <bits/stdc++.h>
using namespace std;
long long memo[15][9][9][9][9];
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long pre[9][9]{};
    for (int i = 1; i <= 8; i++)
        for (int j = 1; j <= 8; j++) {
            long long x;
            cin >> x;
            pre[i][j] = x + pre[i - 1][j] + pre[i][j - 1] - pre[i - 1][j - 1];
        }
    memset(memo, -1, sizeof memo);
    auto sum = [&](int a, int b, int c, int d) {
        return pre[c][d] - pre[a - 1][d] - pre[c][b - 1] + pre[a - 1][b - 1];
    };
    const long long INF = 1LL << 60;
    function<long long(int, int, int, int, int)> solve = [&](int k, int a, int b, int c,
                                                             int d) -> long long {
        if ((c - a + 1) * (d - b + 1) < k)
            return INF;
        long long &ans = memo[k][a][b][c][d];
        if (ans >= 0)
            return ans;
        if (k == 1) {
            long long s = sum(a, b, c, d);
            return ans = s * s;
        }
        ans = INF;
        for (int x = a; x < c; x++) {
            long long s = sum(a, b, x, d), t = sum(x + 1, b, c, d);
            ans =
                min({ans, s * s + solve(k - 1, x + 1, b, c, d), t * t + solve(k - 1, a, b, x, d)});
        }
        for (int y = b; y < d; y++) {
            long long s = sum(a, b, c, y), t = sum(a, y + 1, c, d);
            ans =
                min({ans, s * s + solve(k - 1, a, y + 1, c, d), t * t + solve(k - 1, a, b, c, y)});
        }
        return ans;
    };
    long double mean = (long double)pre[8][8] / n;
    long double variance = (long double)solve(n, 1, 1, 8, 8) / n - mean * mean;
    cout << fixed << setprecision(3) << sqrtl(max(0.0L, variance)) << '\n';

    return 0;
}
