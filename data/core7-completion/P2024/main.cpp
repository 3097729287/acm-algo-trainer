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

    int n, k;
    cin >> n >> k;
    DSU d(3 * n);
    int ans = 0;
    while (k--) {
        int type, x, y;
        cin >> type >> x >> y;
        x--;
        y--;
        if (x < 0 || x >= n || y < 0 || y >= n) {
            ans++;
            continue;
        }
        if (type == 1) {
            if (d.find(x) == d.find(y + n) || d.find(x) == d.find(y + 2 * n)) {
                ans++;
                continue;
            }
            for (int j = 0; j < 3; j++)
                d.join(x + j * n, y + j * n);
        } else {
            if (d.find(x) == d.find(y) || d.find(x) == d.find(y + 2 * n)) {
                ans++;
                continue;
            }
            d.join(x, y + n);
            d.join(x + n, y + 2 * n);
            d.join(x + 2 * n, y);
        }
    }
    cout << ans << '\n';

    return 0;
}
