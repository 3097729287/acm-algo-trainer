#include <bits/stdc++.h>
using namespace std;
int main() {
    int T; cin >> T;
    while (T--) {
        int n; cin >> n;
        vector<int> p(n), q(n);
        for (auto &v : p) cin >> v;
        for (auto &v : q) cin >> v;
        int count = 0;
        bool infinite = false;
        // k>=n 时不同数值的醒来顺序必定按数值递增。
        for (int k = 0; k <= n; ++k) {
            vector<pair<pair<int, int>, int>> wake;
            for (int i = 0; i < n; ++i) wake.push_back({{i + 1 + k * p[i], i + 1}, p[i]});
            sort(wake.begin(), wake.end());
            bool same = true;
            for (int i = 0; i < n; ++i) if (wake[i].second != q[i]) same = false;
            if (same) {
                if (k == n) infinite = true;
                else ++count;
            }
        }
        if (infinite) cout << "inf\n";
        else cout << count << '\n';
    }
}
