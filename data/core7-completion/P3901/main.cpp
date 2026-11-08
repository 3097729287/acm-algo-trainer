#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<int> last(n + 1), bad(n + 1);
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        bad[i] = max(bad[i - 1], last[x]);
        last[x] = i;
    }
    while (q--) {
        int l, r;
        cin >> l >> r;
        cout << (bad[r] < l ? "Yes" : "No") << '\n';
    }

    return 0;
}
