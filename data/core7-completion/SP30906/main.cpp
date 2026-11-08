#include <bits/stdc++.h>
using namespace std;

struct Change {
    int position, before, after;
};
struct Query {
    int l, r, time, id;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<int> a(n), working;
    for (int &x : a)
        cin >> x;
    working = a;
    vector<Change> changes;
    vector<Query> queries;
    for (int i = 0; i < q; i++) {
        int op, l, r;
        cin >> op >> l >> r;
        if (op == 1) {
            changes.push_back({l, working[l], r});
            working[l] = r;
        } else
            queries.push_back({l, r, (int)changes.size(), (int)queries.size()});
    }
    int limit = 0;
    for (int x : a)
        limit = max(limit, x);
    for (auto c : changes)
        limit = max(limit, c.after);
    int block = max(1, (int)pow(n, 2.0 / 3));
    sort(queries.begin(), queries.end(), [&](Query a, Query b) {
        if (a.l / block != b.l / block)
            return a.l < b.l;
        if (a.r / block != b.r / block)
            return a.r < b.r;
        return a.time < b.time;
    });
    vector<int> freq(limit + 1), answer(queries.size());
    int current = 0, l = 0, r = -1, time = 0;
    auto adjust = [&](int x, int delta) {
        current -= freq[x] == 1;
        freq[x] += delta;
        current += freq[x] == 1;
    };
    auto apply = [&](Change c, bool forward) {
        if (l <= c.position && c.position <= r)
            adjust(a[c.position], -1);
        a[c.position] = forward ? c.after : c.before;
        if (l <= c.position && c.position <= r)
            adjust(a[c.position], 1);
    };
    for (auto query : queries) {
        while (time < query.time) {
            apply(changes[time], true);
            time++;
        }
        while (time > query.time) {
            time--;
            apply(changes[time], false);
        }
        while (l > query.l)
            adjust(a[--l], 1);
        while (r < query.r)
            adjust(a[++r], 1);
        while (l < query.l)
            adjust(a[l++], -1);
        while (r > query.r)
            adjust(a[r--], -1);
        answer[query.id] = current;
    }
    for (int x : answer)
        cout << x << '\n';

    return 0;
}
