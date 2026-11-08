#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> t(4 * n);
    function<void(int, int, int)> build = [&](int p, int l, int r) {
        if (l == r) {
            cin >> t[p];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m);
        build(p * 2 + 1, m + 1, r);
        t[p] = gcd(t[p * 2], t[p * 2 + 1]);
    };
    build(1, 1, n);
    function<void(int, int, int, int, int)> change = [&](int p, int l, int r, int x, int v) {
        if (l == r) {
            t[p] = v;
            return;
        }
        int m = (l + r) / 2;
        if (x <= m)
            change(p * 2, l, m, x, v);
        else
            change(p * 2 + 1, m + 1, r, x, v);
        t[p] = gcd(t[p * 2], t[p * 2 + 1]);
    };
    function<void(int, int, int, int, int, int, int &)> bad = [&](int p, int l, int r, int a, int b,
                                                                  int x, int &count) {
        if (count >= 2 || r < a || l > b || t[p] % x == 0)
            return;
        if (l == r) {
            count++;
            return;
        }
        int m = (l + r) / 2;
        bad(p * 2, l, m, a, b, x, count);
        bad(p * 2 + 1, m + 1, r, a, b, x, count);
    };
    int q;
    cin >> q;
    while (q--) {
        int op;
        cin >> op;
        if (op == 1) {
            int l, r, x, c = 0;
            cin >> l >> r >> x;
            bad(1, 1, n, l, r, x, c);
            cout << (c <= 1 ? "YES" : "NO") << '\n';
        } else {
            int p, x;
            cin >> p >> x;
            change(1, 1, n, p, x);
        }
    }

    return 0;
}
