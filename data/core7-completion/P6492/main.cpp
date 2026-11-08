#include <bits/stdc++.h>
using namespace std;

struct Node {
    int len = 1, pre = 1, suf = 1, best = 1, first = 0, last = 0;
};
Node merge(Node a, Node b) {
    Node c;
    c.len = a.len + b.len;
    c.first = a.first;
    c.last = b.last;
    c.pre = a.pre;
    c.suf = b.suf;
    c.best = max(a.best, b.best);
    if (a.last != b.first) {
        c.best = max(c.best, a.suf + b.pre);
        if (a.pre == a.len)
            c.pre = a.len + b.pre;
        if (b.suf == b.len)
            c.suf = b.len + a.suf;
    }
    return c;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<Node> t(4 * n);
    function<void(int, int, int)> build = [&](int p, int l, int r) {
        t[p].len = r - l + 1;
        if (l == r)
            return;
        int m = (l + r) / 2;
        build(p * 2, l, m);
        build(p * 2 + 1, m + 1, r);
        t[p] = merge(t[p * 2], t[p * 2 + 1]);
    };
    build(1, 1, n);
    function<void(int, int, int, int)> change = [&](int p, int l, int r, int x) {
        if (l == r) {
            t[p].first ^= 1;
            t[p].last ^= 1;
            return;
        }
        int m = (l + r) / 2;
        if (x <= m)
            change(p * 2, l, m, x);
        else
            change(p * 2 + 1, m + 1, r, x);
        t[p] = merge(t[p * 2], t[p * 2 + 1]);
    };
    while (q--) {
        int x;
        cin >> x;
        change(1, 1, n, x);
        cout << t[1].best << '\n';
    }

    return 0;
}
