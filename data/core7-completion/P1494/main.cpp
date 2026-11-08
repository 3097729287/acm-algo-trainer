#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, q;
    cin >> n >> q;
    vector<int> a(n + 1), values;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        values.push_back(a[i]);
    }
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    for (int i = 1; i <= n; i++)
        a[i] = lower_bound(values.begin(), values.end(), a[i]) - values.begin();

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
    vector<long long> answer(q), length(q);
    long long current = 0;
    auto change = [&](int p, int delta) {
        int &c = freq[a[p]];
        current -= 1LL * c * (c - 1);
        c += delta;
        current += 1LL * c * (c - 1);
    };
    int l = 1, r = 0;
    for (auto query : queries) {
        while (l > query.l)
            change(--l, 1);
        while (r < query.r)
            change(++r, 1);
        while (l < query.l)
            change(l++, -1);
        while (r > query.r)
            change(r--, -1);
        answer[query.id] = current;
        length[query.id] = query.r - query.l + 1;
    }
    for (int i = 0; i < q; i++) {
        long long a = answer[i], b = length[i] * (length[i] - 1);
        if (a == 0)
            cout << "0/1\n";
        else {
            long long g = gcd(a, b);
            cout << a / g << '/' << b / g << '\n';
        }
    }
    return 0;
}
