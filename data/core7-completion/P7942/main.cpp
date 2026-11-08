#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, k;
    cin >> n >> m >> k;
    const long long P = 998244353;
    vector<vector<long long>> suffix(26, vector<long long>(m + 1)), prefix = suffix;
    vector<vector<vector<int>>> self(26, vector<vector<int>>(m + 1, vector<int>(m + 1)));
    long long inside = 0;
    for (int i = 0; i < n; i++) {
        string s;
        cin >> s;
        for (int l = 0; l < m;) {
            int r = l + 1;
            while (r < m && s[r] == s[l])
                r++;
            inside += max(0, r - l - k + 1);
            l = r;
        }
        int p = 1, t = 1;
        while (p < m && s[p] == s[0])
            p++;
        while (t < m && s[m - 1 - t] == s[m - 1])
            t++;
        prefix[s[0] - 'a'][p]++;
        suffix[s.back() - 'a'][t]++;
        if (s[0] == s.back())
            self[s[0] - 'a'][t][p]++;
    }
    vector<long long> fact(n + 1, 1);
    for (int i = 1; i <= n; i++)
        fact[i] = fact[i - 1] * i % P;
    long long cross = 0;
    for (int c = 0; c < 26; c++)
        for (int s = 1; s <= m; s++)
            for (int p = 1; p <= m; p++) {
                int ways = max(0, min(s, k - 1) - max(1, k - p) + 1);
                long long pairs = (suffix[c][s] * prefix[c][p] - self[c][s][p]) % P;
                cross = (cross + pairs * ways) % P;
            }
    cout << ((inside % P) * fact[n] + cross * fact[n - 1]) % P << '\n';

    return 0;
}
