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
    vector<long long> p(n + 1), values;
    for (int i = 1; i <= n; i++) {
        int x;
        cin >> x;
        p[i] = p[i - 1] + x - m;
    }
    values = p;
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    Fenwick bit(values.size());
    long long ans = 0;
    for (long long x : p) {
        int rank = lower_bound(values.begin(), values.end(), x) - values.begin() + 1;
        ans += bit.sum(rank - 1);
        bit.add(rank, 1);
    }
    cout << ans % 92084931 << '\n';

    return 0;
}
