#include <bits/stdc++.h>
using namespace std;

struct MinTree {
    int n;
    vector<long long> value, tag;
    MinTree(const vector<long long> &a) : n(a.size()), value(4 * n), tag(4 * n) {
        build(1, 0, n - 1, a);
    }
    void build(int p, int l, int r, const vector<long long> &a) {
        if (l == r) {
            value[p] = a[l];
            return;
        }
        int m = (l + r) / 2;
        build(p * 2, l, m, a);
        build(p * 2 + 1, m + 1, r, a);
        value[p] = min(value[p * 2], value[p * 2 + 1]);
    }
    void apply(int p, long long x) {
        value[p] += x;
        tag[p] += x;
    }
    void push(int p) {
        if (tag[p]) {
            apply(p * 2, tag[p]);
            apply(p * 2 + 1, tag[p]);
            tag[p] = 0;
        }
    }
    void add(int p, int l, int r, int a, int b, long long x) {
        if (a <= l && r <= b) {
            apply(p, x);
            return;
        }
        push(p);
        int m = (l + r) / 2;
        if (a <= m)
            add(p * 2, l, m, a, b, x);
        if (b > m)
            add(p * 2 + 1, m + 1, r, a, b, x);
        value[p] = min(value[p * 2], value[p * 2 + 1]);
    }
    long long query(int p, int l, int r, int a, int b) {
        if (a <= l && r <= b)
            return value[p];
        push(p);
        int m = (l + r) / 2;
        long long ans = LLONG_MAX / 4;
        if (a <= m)
            ans = min(ans, query(p * 2, l, m, a, b));
        if (b > m)
            ans = min(ans, query(p * 2 + 1, m + 1, r, a, b));
        return ans;
    }
    void add(int l, int r, long long x) { add(1, 0, n - 1, l, r, x); }
    long long query(int l, int r) { return query(1, 0, n - 1, l, r); }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    vector<pair<int, int>> requests(m);
    for (auto &[r, l] : requests) {
        cin >> l >> r;
        l--;
        r--;
    }
    sort(requests.begin(), requests.end(), [](auto a, auto b) {
        if (a.first != b.first)
            return a.first < b.first;
        return a.second > b.second;
    });
    MinTree tree(a);
    int ans = 0;
    for (auto [r, l] : requests)
        if (tree.query(l, r) > 0) {
            ans++;
            tree.add(l, r, -1);
        }
    cout << ans << '\n';

    return 0;
}
