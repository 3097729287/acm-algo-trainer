#include <bits/stdc++.h>
using namespace std;

struct Tree {
    int n;
    vector<int> sum;
    vector<char> tag;
    Tree(int n) : n(n), sum(4 * n), tag(4 * n) {}
    void apply(int p, int l, int r) {
        sum[p] = r - l + 1 - sum[p];
        tag[p] ^= 1;
    }
    void push(int p, int l, int r) {
        if (tag[p] && l < r) {
            int m = (l + r) / 2;
            apply(p * 2, l, m);
            apply(p * 2 + 1, m + 1, r);
            tag[p] = 0;
        }
    }
    void change(int p, int l, int r, int a, int b) {
        if (a <= l && r <= b) {
            apply(p, l, r);
            return;
        }
        push(p, l, r);
        int m = (l + r) / 2;
        if (a <= m)
            change(p * 2, l, m, a, b);
        if (b > m)
            change(p * 2 + 1, m + 1, r, a, b);
        sum[p] = sum[p * 2] + sum[p * 2 + 1];
    }
    int query(int p, int l, int r, int a, int b) {
        if (a <= l && r <= b)
            return sum[p];
        push(p, l, r);
        int m = (l + r) / 2, ans = 0;
        if (a <= m)
            ans += query(p * 2, l, m, a, b);
        if (b > m)
            ans += query(p * 2 + 1, m + 1, r, a, b);
        return ans;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    Tree t(n);
    while (m--) {
        int op, l, r;
        cin >> op >> l >> r;
        if (op == 0)
            t.change(1, 1, n, l, r);
        else
            cout << t.query(1, 1, n, l, r) << '\n';
    }

    return 0;
}
