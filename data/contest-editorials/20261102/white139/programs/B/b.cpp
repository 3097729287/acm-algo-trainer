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
        long long ans = 0;
        for (int j = 1; j <= n; ++j) {
            long long a;
            cin >> a;
            // 原式中每一项都等于 a_j，它对应 j 个左端点。
            ans += j * a;
        }
        cout << ans << '\n';
    }
}
