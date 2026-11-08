#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> p(n + 1);
    bool sorted = true;
    for (int i = 1; i <= n; i++) {
        cin >> p[i];
        sorted &= p[i] == i;
    }
    vector<tuple<int, int, int>> edges(m);
    int maximum = 0;
    for (auto &[a, b, w] : edges) {
        cin >> a >> b >> w;
        maximum = max(maximum, w);
    }
    if (sorted) {
        cout << -1 << '\n';
        return 0;
    }
    auto ok = [&](int limit) {
        DSU d(n + 1);
        for (auto [a, b, w] : edges)
            if (w >= limit)
                d.join(a, b);
        for (int i = 1; i <= n; i++)
            if (d.find(i) != d.find(p[i]))
                return false;
        return true;
    };
    int l = 0, r = maximum;
    while (l < r) {
        int mid = l + (r - l + 1) / 2;
        if (ok(mid))
            l = mid;
        else
            r = mid - 1;
    }
    cout << l << '\n';

    return 0;
}
