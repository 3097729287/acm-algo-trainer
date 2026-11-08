#include <bits/stdc++.h>
using namespace std;

pair<vector<int>, vector<int>> manacher(const string &s) {
    int n = s.size();
    vector<int> odd(n), even(n);
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 1 : min(odd[l + r - i], r - i + 1);
        while (i - k >= 0 && i + k < n && s[i - k] == s[i + k])
            k++;
        odd[i] = k;
        if (i + k - 1 > r) {
            l = i - k + 1;
            r = i + k - 1;
        }
    }
    for (int i = 0, l = 0, r = -1; i < n; i++) {
        int k = i > r ? 0 : min(even[l + r - i + 1], r - i + 1);
        while (i - k - 1 >= 0 && i + k < n && s[i - k - 1] == s[i + k])
            k++;
        even[i] = k;
        if (i + k - 1 > r) {
            l = i - k;
            r = i + k - 1;
        }
    }
    return {move(odd), move(even)};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    const long long P = 998244353;
    while (T--) {
        int n;
        long long k;
        string s;
        cin >> n >> k >> s;
        string triple = s + s + s;
        auto [odd, even] = manacher(triple);
        long long length = 1LL * n * k, ans = 0;
        auto contribution = [&](int r, int R, int offset, bool infinite) -> long long {
            if (!infinite) {
                if (k == 1)
                    return min({R, r + offset, n - r});
                return (((k - 2) % P) * R + min(R, r + offset) + min(R, n - r)) % P;
            }
            long long threshold = length - 2LL * r - offset;
            long long left = threshold < 0 ? 0 : min(k, threshold / (2LL * n) + 1);
            long long right = k - left;
            __int128 total = (__int128)left * (r + offset) + (__int128)n * left * (left - 1) / 2 +
                             (__int128)right * (length - r) -
                             (__int128)n * (left + k - 1) * right / 2;
            return total % P;
        };
        for (int r = 0; r < n; r++) {
            ans = (ans + contribution(r, odd[n + r], 1, odd[n + r] >= n + 1)) % P;
            ans = (ans + contribution(r, even[n + r], 0, even[n + r] >= n)) % P;
        }
        cout << ans << '\n';
    }

    return 0;
}
