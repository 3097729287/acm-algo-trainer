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

    int n;
    cin >> n;
    struct E {
        int u, v, w;
    };
    vector<E> e;
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        e.push_back({0, i, x});
    }
    for (int i = 1; i <= n; i++)
        for (int j = 1; j <= n; j++) {
            int x;
            cin >> x;
            if (i < j)
                e.push_back({i, j, x});
        }
    sort(e.begin(), e.end(), [](E a, E b) { return a.w < b.w; });
    DSU d(n + 1);
    long long ans = 0;
    for (auto x : e)
        if (d.join(x.u, x.v))
            ans += x.w;
    cout << ans << '\n';

    return 0;
}
