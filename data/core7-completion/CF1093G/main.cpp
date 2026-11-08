#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    int masks = 1 << k, size = 1;
    while (size < n)
        size *= 2;
    vector<array<int, 32>> tree(2 * size);
    for (auto &v : tree)
        v.fill(INT_MIN / 4);
    auto readPoint = [&](int p) {
        vector<int> a(k);
        for (int &x : a)
            cin >> x;
        for (int mask = 0; mask < masks; mask++) {
            int value = 0;
            for (int j = 0; j < k; j++)
                value += ((mask >> j) & 1) ? a[j] : -a[j];
            tree[p][mask] = value;
        }
    };
    for (int i = 0; i < n; i++)
        readPoint(size + i);
    auto pull = [&](int p) {
        for (int mask = 0; mask < masks; mask++)
            tree[p][mask] = max(tree[p * 2][mask], tree[p * 2 + 1][mask]);
    };
    for (int p = size - 1; p; p--)
        pull(p);
    int q;
    cin >> q;
    while (q--) {
        int op, l;
        cin >> op >> l;
        if (op == 1) {
            int p = size + l - 1;
            readPoint(p);
            for (p /= 2; p; p /= 2)
                pull(p);
        } else {
            int r;
            cin >> r;
            array<int, 32> best;
            best.fill(INT_MIN / 4);
            for (l += size - 1, r += size; l < r; l /= 2, r /= 2) {
                if (l & 1) {
                    for (int mask = 0; mask < masks; mask++)
                        best[mask] = max(best[mask], tree[l][mask]);
                    l++;
                }
                if (r & 1) {
                    r--;
                    for (int mask = 0; mask < masks; mask++)
                        best[mask] = max(best[mask], tree[r][mask]);
                }
            }
            int answer = 0;
            for (int mask = 0; mask < masks; mask++)
                answer = max(answer, best[mask] + best[mask ^ (masks - 1)]);
            cout << answer << '\n';
        }
    }

    return 0;
}
