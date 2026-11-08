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
        map<int, vector<int>> pos;
        for (int i = 1; i <= n; i++) {
            int x;
            cin >> x;
            pos[x].push_back(i);
        }
        int q;
        cin >> q;
        while (q--) {
            int l, r, x;
            cin >> l >> r >> x;
            auto it = pos.find(x);
            if (it == pos.end())
                cout << 0 << '\n';
            else {
                auto &v = it->second;
                cout << upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l)
                     << '\n';
            }
        }
    }

    return 0;
}
