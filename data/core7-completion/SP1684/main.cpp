#include <bits/stdc++.h>
using namespace std;

struct Node {
    int len = 0, first = 0, last = 0, pre = 0, suf = 0, best = 0;
};
Node merge(Node a, Node b) {
    if (!a.len)
        return b;
    if (!b.len)
        return a;
    Node c = {a.len + b.len, a.first, b.last, a.pre, b.suf, max(a.best, b.best)};
    if (a.last == b.first) {
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
    while (cin >> n && n) {
        cin >> q;
        int size = 1;
        while (size < n)
            size *= 2;
        vector<Node> t(2 * size);
        for (int i = 0; i < n; i++) {
            int x;
            cin >> x;
            t[size + i] = {1, x, x, 1, 1, 1};
        }
        for (int p = size - 1; p; p--)
            t[p] = merge(t[p * 2], t[p * 2 + 1]);
        while (q--) {
            int l, r;
            cin >> l >> r;
            Node a, b;
            for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
                if (l & 1)
                    a = merge(a, t[l++]);
                if (r & 1)
                    b = merge(t[--r], b);
            }
            cout << merge(a, b).best << '\n';
        }
    }

    return 0;
}
