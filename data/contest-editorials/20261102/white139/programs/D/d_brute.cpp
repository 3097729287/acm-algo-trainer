#include <bits/stdc++.h>
using namespace std;
int main() {
    int T; cin >> T;
    while (T--) {
        int n; cin >> n;
        vector<long long> a(n);
        for (auto &v : a) cin >> v;
        vector<bool> legal(n + 1, false);
        // 按图逐层数三角形的三条边，不用闭式公式。
        int cards = 0;
        for (int row = 1; ; ++row) {
            for (int triangle = 0; triangle < row; ++triangle) cards += 3;
            if (cards > n) break;
            legal[cards] = true;
        }
        long long ans = LLONG_MIN;
        for (int l = 0; l < n; ++l) {
            long long sum = 0;
            for (int r = l; r < n; ++r) {
                sum += a[r];
                if (legal[r - l + 1]) ans = max(ans, sum);
            }
        }
        cout << ans << '\n';
    }
}
