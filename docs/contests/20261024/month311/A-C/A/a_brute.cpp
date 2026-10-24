#include <bits/stdc++.h>
using namespace std;
int main() {
    int n; cin >> n;
    vector<vector<int>> valid;
    vector<int> p(n); iota(p.begin(), p.end(), 1);
    do {
        bool ok = true;
        for (int i = 1; i < n; ++i) ok &= abs(p[i] - p[i - 1]) > 1;
        if (ok) valid.push_back(p);
    } while (next_permutation(p.begin(), p.end()));
    for (auto &a : valid) for (auto &b : valid) {
        bool ok = true;
        for (int i = 0; i < n; ++i) ok &= abs(a[i] - b[i]) > 1;
        if (ok) {
            for (int v : a) cout << v << ' '; cout << '\n';
            for (int v : b) cout << v << ' '; cout << '\n';
            return 0;
        }
    }
    cout << -1 << '\n';
}
