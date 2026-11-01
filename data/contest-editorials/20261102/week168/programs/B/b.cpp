#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m, ans = 0;
    cin >> n >> m;
    for (int i = 0; i < n; ++i) {
        string s;
        cin >> s;
        for (int j = 0; j < m; ++j) {
            // 用一个条件取边界的并集，角和单行、单列均只计一次。
            if (s[j] == '#' && (i == 0 || i == n - 1 || j == 0 || j == m - 1)) ++ans;
        }
    }
    cout << ans << '\n';
}
