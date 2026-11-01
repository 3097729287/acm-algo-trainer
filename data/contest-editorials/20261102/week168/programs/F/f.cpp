#include <bits/stdc++.h>
using namespace std;
const long long MOD = 1000000007;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<int> a(n);
        for (int &x : a) cin >> x;
        sort(a.begin(), a.end());
        vector<long long> rook(n + 1);
        rook[0] = 1;
        for (int i = 0; i < n; ++i) {
            // 倒序保证 rook[j-1] 仍属于处理当前朋友之前。
            for (int j = i + 1; j >= 1; --j) {
                long long choices = max(0, a[i] - j + 1);
                rook[j] = (rook[j] + rook[j - 1] * choices) % MOD;
            }
        }
        long long pairs = 1LL * n * (n - 1) / 2 % MOD;
        long long ans = (2 * rook[n - 2] - (n - 1) * rook[n - 1] + pairs * rook[n]) % MOD;
        cout << (ans + MOD) % MOD << '\n';
    }
}
