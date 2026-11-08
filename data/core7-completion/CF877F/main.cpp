#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long k;
    cin >> n >> k;
    vector<int> type(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> type[i];
    vector<long long> p(n + 1), values;
    for (int i = 1; i <= n; i++) {
        long long x;
        cin >> x;
        p[i] = p[i - 1] + (type[i] == 1 ? x : -x);
    }
    for (long long x : p) {
        values.push_back(x);
        values.push_back(x - k);
        values.push_back(x + k);
    }
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    vector<int> id(n + 1), minus(n + 1), plus(n + 1);
    for (int i = 0; i <= n; i++) {
        id[i] = lower_bound(values.begin(), values.end(), p[i]) - values.begin();
        minus[i] = lower_bound(values.begin(), values.end(), p[i] - k) - values.begin();
        plus[i] = lower_bound(values.begin(), values.end(), p[i] + k) - values.begin();
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
    int block = max(1, (int)sqrt(n));
    sort(queries.begin(), queries.end(), [&](Query a, Query b) {
        if (a.l / block != b.l / block)
            return a.l < b.l;
        return (a.l / block) & 1 ? a.r > b.r : a.r < b.r;
    });

    vector<int> freq(values.size());
    vector<long long> ans(q);
    long long current = 0;
    int l = 0, r = -1;
    auto add = [&](int i, bool left) {
        current += freq[left ? plus[i] : minus[i]];
        freq[id[i]]++;
    };
    auto remove = [&](int i, bool left) {
        freq[id[i]]--;
        current -= freq[left ? plus[i] : minus[i]];
    };
    for (auto x : queries) {
        x.l--;
        while (l > x.l)
            add(--l, true);
        while (r < x.r)
            add(++r, false);
        while (l < x.l)
            remove(l++, true);
        while (r > x.r)
            remove(r--, false);
        ans[x.id] = current;
    }
    for (long long x : ans)
        cout << x << '\n';

    return 0;
}
