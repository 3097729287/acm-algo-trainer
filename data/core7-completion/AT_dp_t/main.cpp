#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string s;
    if (n > 1)
        cin >> s;
    vector<long long> dp(1, 1);
    for (int len = 1; len < n; len++) {
        vector<long long> prefix(len + 1), next(len + 1);
        for (int j = 0; j < len; j++)
            prefix[j + 1] = (prefix[j] + dp[j]) % MOD;
        for (int j = 0; j <= len; j++)
            next[j] = s[len - 1] == '<' ? prefix[j] : (prefix[len] - prefix[j] + MOD) % MOD;
        dp.swap(next);
    }
    long long ans = 0;
    for (auto x : dp)
        ans = (ans + x) % MOD;
    cout << ans << '\n';

    return 0;
}
