#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int maximum = n * (n - 1) / 2;
    vector<vector<char>> dp(n + 1, vector<char>(maximum + 1));
    dp[0][0] = 1;
    for (int i = 0; i < n; i++)
        for (int s = 0; s <= maximum; s++)
            if (dp[i][s])
                for (int k = 1; i + k <= n; k++)
                    dp[i + k][s + i * k] = 1;
    cout << count(dp[n].begin(), dp[n].end(), 1) << '\n';

    return 0;
}
