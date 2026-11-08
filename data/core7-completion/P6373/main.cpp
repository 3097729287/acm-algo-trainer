#include <bits/stdc++.h>
using namespace std;

struct Node {
    long long i = 0, o = 0, io = 0, oi = 0, ioi = 0;
};
Node leaf(char c) {
    Node a;
    a.i = c == 'I';
    a.o = c == 'O';
    return a;
}
Node merge(Node a, Node b) {
    return {a.i + b.i, a.o + b.o, a.io + b.io + a.i * b.o, a.oi + b.oi + a.o * b.i,
            a.ioi + b.ioi + a.i * b.oi + a.io * b.i};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    string s;
    cin >> n >> m >> s;
    int size = 1;
    while (size < n)
        size *= 2;
    vector<Node> t(2 * size);
    for (int i = 0; i < n; i++)
        t[size + i] = leaf(s[i]);
    for (int p = size - 1; p; p--)
        t[p] = merge(t[p * 2], t[p * 2 + 1]);
    while (m--) {
        int op, l;
        cin >> op >> l;
        if (op == 1) {
            char c;
            cin >> c;
            int p = size + l - 1;
            t[p] = leaf(c);
            for (p /= 2; p; p /= 2)
                t[p] = merge(t[p * 2], t[p * 2 + 1]);
        } else {
            int r;
            cin >> r;
            Node a, b;
            for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
                if (l & 1)
                    a = merge(a, t[l++]);
                if (r & 1)
                    b = merge(t[--r], b);
            }
            cout << merge(a, b).ioi << '\n';
        }
    }

    return 0;
}
