#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n, m, k;
        cin >> n >> m >> k;
        vector<long long> a(n + 1), b(m + 1);
        vector<int> ones_a(n + 1), ones_b(m + 1);
        for (int i = 1, flag; i <= n; ++i) {
            cin >> a[i] >> flag; a[i] += a[i - 1]; ones_a[i] = ones_a[i - 1] + flag;
        }
        for (int j = 1, flag; j <= m; ++j) {
            cin >> b[j] >> flag; b[j] += b[j - 1]; ones_b[j] = ones_b[j - 1] + flag;
        }
        long long best = LLONG_MIN;
        for (int i = max(0, k - m); i <= min(n, k); ++i) {
            int j = k - i;
            // 仅统计前缀内部的强制换堆；最后一件后无须继续取。
            int cut_a = i ? ones_a[i - 1] : 0;
            int cut_b = j ? ones_b[j - 1] : 0;
            if (cut_a <= j && cut_b <= i) best = max(best, a[i] + b[j]);
        }
        if (best == LLONG_MIN) cout << "IMPOSSIBLE\n";
        else cout << best << '\n';
    }
}
