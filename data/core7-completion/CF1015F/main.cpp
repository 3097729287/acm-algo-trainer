#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    int m = s.size();
    const int P = 1000000007;
    vector<int> pi(m);
    for (int i = 1; i < m; i++) {
        int j = pi[i - 1];
        while (j && s[i] != s[j])
            j = pi[j - 1];
        if (s[i] == s[j])
            j++;
        pi[i] = j;
    }
    vector<array<int, 2>> next(m + 1);
    for (int state = 0; state < m; state++)
        for (int c = 0; c < 2; c++) {
            char ch = c ? ')' : '(';
            int j = state;
            while (j && s[j] != ch)
                j = pi[j - 1];
            if (s[j] == ch)
                j++;
            next[state][c] = j;
        }
    next[m] = {m, m};
    vector<vector<int>> dp(n + 1, vector<int>(m + 1));
    dp[0][0] = 1;
    for (int used = 0; used < 2 * n; used++) {
        vector<vector<int>> ndp(n + 1, vector<int>(m + 1));
        for (int balance = 0; balance <= n; balance++)
            for (int state = 0; state <= m; state++)
                if (dp[balance][state])
                    for (int c = 0; c < 2; c++) {
                        int b = balance + (c ? -1 : 1);
                        if (b < 0 || b > n || b > 2 * n - used - 1)
                            continue;
                        int &v = ndp[b][next[state][c]];
                        v += dp[balance][state];
                        if (v >= P)
                            v -= P;
                    }
        dp.swap(ndp);
    }
    cout << dp[0][m] << '\n';

    return 0;
}
