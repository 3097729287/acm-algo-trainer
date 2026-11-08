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

    int n, k;
    cin >> n >> k;
    const long long P = 998244353;
    vector<long long> a(n), values;
    for (auto &x : a)
        cin >> x;
    values = a;
    sort(values.begin(), values.end());
    values.erase(unique(values.begin(), values.end()), values.end());
    Fenwick count(values.size()), sum(values.size());
    vector<long long> inv(k + 1);
    inv[1] = 1;
    for (int i = 2; i <= k; i++)
        inv[i] = (P - P / i) * inv[P % i] % P;
    auto rank = [&](long long x) {
        return int(lower_bound(values.begin(), values.end(), x) - values.begin()) + 1;
    };
    auto change = [&](int i, int delta) {
        int r = rank(a[i]);
        count.add(r, delta);
        sum.add(r, a[i] * delta);
    };
    long long ans = a[0];
    change(0, 1);
    for (int i = 1; i < n; i++) {
        if (i - k - 1 >= 0)
            change(i - k - 1, -1);
        int r = rank(a[i]);
        long long positive = (a[i] * count.sum(r - 1) - sum.sum(r - 1)) % P;
        ans = (ans + positive * inv[min(k, i)]) % P;
        change(i, 1);
    }
    cout << ans << '\n';

    return 0;
}
