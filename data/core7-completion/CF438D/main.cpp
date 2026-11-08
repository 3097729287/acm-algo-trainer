#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<long long> sum(4 * n);
    vector<int> mx(4 * n);
    auto pull = [&](int p) {
        sum[p] = sum[p * 2] + sum[p * 2 + 1];
        mx[p] = max(mx[p * 2], mx[p * 2 + 1]);
    };
    function<void(int, int, int)> build = [&](int p, int l, int r) {
        if (l == r) {
            cin >> mx[p];
            sum[p] = mx[p];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m);
        build(p * 2 + 1, m + 1, r);
        pull(p);
    };
    build(1, 1, n);
    function<long long(int, int, int, int, int)> query = [&](int p, int l, int r, int a,
                                                             int b) -> long long {
        if (a <= l && r <= b)
            return sum[p];
        int m = (l + r) / 2;
        long long ans = 0;
        if (a <= m)
            ans += query(p * 2, l, m, a, b);
        if (b > m)
            ans += query(p * 2 + 1, m + 1, r, a, b);
        return ans;
    };
    function<void(int, int, int, int, int, int)> mod = [&](int p, int l, int r, int a, int b,
                                                           int x) {
        if (r < a || l > b || mx[p] < x)
            return;
        if (l == r) {
            mx[p] %= x;
            sum[p] = mx[p];
            return;
        }
        int m = (l + r) / 2;
        mod(p * 2, l, m, a, b, x);
        mod(p * 2 + 1, m + 1, r, a, b, x);
        pull(p);
    };
    function<void(int, int, int, int, int)> setvalue = [&](int p, int l, int r, int i, int x) {
        if (l == r) {
            sum[p] = mx[p] = x;
            return;
        }
        int m = (l + r) / 2;
        if (i <= m)
            setvalue(p * 2, l, m, i, x);
        else
            setvalue(p * 2 + 1, m + 1, r, i, x);
        pull(p);
    };
    while (q--) {
        int op, l, r, x;
        cin >> op >> l >> r;
        if (op == 1)
            cout << query(1, 1, n, l, r) << '\n';
        else if (op == 2) {
            cin >> x;
            mod(1, 1, n, l, r, x);
        } else
            setvalue(1, 1, n, l, r);
    }

    return 0;
}
