#include <bits/stdc++.h>
using namespace std;
using ull = unsigned long long;
const ull MOD = 998244853;
int main() {
    int t; cin >> t;
    while (t--) {
        int n, x, y, z; cin >> n >> x >> y >> z;
        bool found = false; ull best = 0;
        function<void(int,int,int,int,int,ull)> dfs = [&](int left, int low, int a, int o, int e, ull p) {
            if (!left) { if (a == x && o == y && e == z) { found = true; best = max(best, p); } return; }
            for (int v = low; v <= y; ++v) dfs(left - 1, v, a & v, o | v, e ^ v, p * v);
        };
        dfs(n, 0, 15, 0, 0, 1);
        if (found) cout << best % MOD << '\n'; else cout << -1 << '\n';
    }
}
