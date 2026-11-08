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
    int s, t;
    cin >> s >> t;
    struct E {
        int u, v;
        long long w;
    };
    vector<E> e(m);
    long long total = 0;
    for (auto &x : e) {
        cin >> x.u >> x.v >> x.w;
        total += x.w;
    }
    sort(e.begin(), e.end(), [](E a, E b) { return a.w < b.w; });
    DSU d(n + 1);
    long long answer = 0;
    int used = 0;
    if (s == t) {
        cout << 0 << '\n';
        return 0;
    }
    for (auto x : e) {
        d.join(x.u, x.v);
        if (d.find(s) == d.find(t)) {
            cout << x.w << '\n';
            return 0;
        }
    }
    return 0;
}
