#include <bits/stdc++.h>
using namespace std;

struct Fenwick {
    int n;
    vector<long long> t;
    explicit Fenwick(int n) : n(n), t(n + 1) {}
    void add(int x, long long v) {
        for (; x <= n; x += x & -x)
            t[x] += v;
    }
    long long sum(int x) const {
        long long s = 0;
        for (; x; x -= x & -x)
            s += t[x];
        return s;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<pair<int, int>> a(n);
    for (int i = 0; i < n; i++) {
        cin >> a[i].first;
        a[i].second = i + 1;
    }
    sort(a.begin(), a.end());
    struct Q {
        int l, r, x, id;
    };
    vector<Q> queries(m);
    for (int i = 0; i < m; i++) {
        cin >> queries[i].l >> queries[i].r >> queries[i].x;
        queries[i].id = i;
    }
    sort(queries.begin(), queries.end(), [](Q a, Q b) { return a.x < b.x; });
    Fenwick bit(n);
    vector<long long> ans(m);
    int p = 0;
    for (auto q : queries) {
        while (p < n && a[p].first <= q.x) {
            bit.add(a[p].second, 1);
            p++;
        }
        ans[q.id] = bit.sum(q.r) - bit.sum(q.l - 1);
    }
    for (auto x : ans)
        cout << x << '\n';

    return 0;
}
