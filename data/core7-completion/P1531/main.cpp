#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        int size = 1;
        while (size < n)
            size *= 2;
        vector<int> t(2 * size, INT_MIN);
        for (int i = 0; i < n; i++)
            cin >> t[size + i];
        for (int i = size - 1; i; i--)
            t[i] = max(t[i * 2], t[i * 2 + 1]);
        while (m--) {
            char op;
            int x, y;
            cin >> op >> x >> y;
            if (op == 'U') {
                int p = size + x - 1;
                t[p] = y;
                for (p /= 2; p; p /= 2)
                    t[p] = max(t[p * 2], t[p * 2 + 1]);
            } else {
                if (x > y)
                    swap(x, y);
                int ans = INT_MIN;
                for (int l = size + x - 1, r = size + y; l < r; l /= 2, r /= 2) {
                    if (l & 1)
                        ans = max(ans, t[l++]);
                    if (r & 1)
                        ans = max(ans, t[--r]);
                }
                cout << ans << '\n';
            }
        }
    }

    return 0;
}
