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
        vector<int> pos(n + 1), q(n);
        for (int i = 1; i <= n; ++i) {
            int v;
            cin >> v;
            pos[v] = i;
        }
        for (int i = 0; i < n; ++i) cin >> q[i];
        int low = 0, high = n;
        // 有限上界至多为 n-1，故用 n 表示尚无上界。
        for (int i = 0; i + 1 < n; ++i) {
            int u = q[i], v = q[i + 1];
            if (u < v) {
                if (pos[u] > pos[v]) {
                    // 原来较晚入睡的 u 必须严格早醒，平局会让 v 先输出。
                    low = max(low, (pos[u] - pos[v]) / (v - u) + 1);
                }
            } else {
                if (pos[u] > pos[v]) {
                    high = -1;
                } else {
                    // 原来较早入睡的 u 可以和 v 同时醒来。
                    high = min(high, (pos[v] - pos[u]) / (u - v));
                }
            }
        }
        if (low > high) cout << 0 << '\n';
        else if (high == n) cout << "inf\n";
        else cout << high - low + 1 << '\n';
    }
}
