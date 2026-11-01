#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<long long> s(n + 1, 0);
        for (int i = 1; i <= n; ++i) {
            long long a;
            cin >> a;
            s[i] = s[i - 1] + a;
        }
        long long ans = numeric_limits<long long>::lowest();
        for (int k = 1; ; ++k) {
            long long len = 3LL * k * (k + 1) / 2;
            if (len > n) break;
            // 固定合法长度，再枚举右端点；非空区间也可能全为负。
            for (int r = static_cast<int>(len); r <= n; ++r) {
                ans = max(ans, s[r] - s[r - len]);
            }
        }
        cout << ans << '\n';
    }
}
