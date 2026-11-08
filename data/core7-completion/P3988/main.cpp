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
    Fenwick bit(n);
    for (int i = 1; i <= n; i++)
        bit.t[i] = i & -i;
    long long rank = 0;
    int highest = 1;
    while ((highest << 1) <= n)
        highest <<= 1;
    for (int remain = n; remain >= 1; remain--) {
        long long R;
        cin >> R;
        rank = (rank + R) % remain;
        long long need = rank + 1;
        int pos = 0;
        for (int step = highest; step; step >>= 1) {
            int next = pos + step;
            if (next <= n && bit.t[next] < need) {
                need -= bit.t[next];
                pos = next;
            }
        }
        int card = pos + 1;
        cout << card << '\n';
        bit.add(card, -1);
    }

    return 0;
}
