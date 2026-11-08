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

    int n;
    cin >> n;
    vector<int> a(n + 1);
    int limit = 0;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        limit = max(limit, a[i]);
    }
    int q;
    cin >> q;
    struct Query {
        int l, r, id;
    };
    vector<Query> queries(q);
    for (int i = 0; i < q; i++) {
        cin >> queries[i].l >> queries[i].r;
        queries[i].id = i;
    }
    sort(queries.begin(), queries.end(), [](Query a, Query b) { return a.r < b.r; });
    vector<int> last(limit + 1), ans(q);
    Fenwick bit(n);
    int next = 1;
    for (auto x : queries) {
        while (next <= x.r) {
            int value = a[next];
            if (last[value])
                bit.add(last[value], -1);
            bit.add(next, 1);
            last[value] = next;
            next++;
        }
        ans[x.id] = bit.sum(x.r) - bit.sum(x.l - 1);
    }
    for (int x : ans)
        cout << x << '\n';

    return 0;
}
