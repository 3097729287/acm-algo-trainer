#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> a(n);
        long long sum = 0;
        bool movable = false, inner = false;
        for (int i = 0; i < n; ++i) {
            cin >> a[i]; sum += a[i];
            if (a[i] >= 2) {
                movable = true;
                if (i > 0 && i + 1 < n) inner = true;
            }
        }
        if (!movable) cout << -1 << '\n';
        else if (inner) cout << sum - 1 << '\n';
        else cout << a.front() + a.back() - 1 << '\n';
    }
}
