#include <bits/stdc++.h>
using namespace std;

struct Bit {
    vector<int> t;
    Bit(int n) : t(n + 1) {}
    void add(int x, int v) {
        for (; x < (int)t.size(); x += x & -x) {
            t[x] += v;
            if (t[x] >= 1000000007)
                t[x] -= 1000000007;
        }
    }
    int sum(int x) const {
        int r = 0;
        for (; x; x -= x & -x) {
            r += t[x];
            if (r >= 1000000007)
                r -= 1000000007;
        }
        return r;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int R, C, K;
    cin >> R >> C >> K;
    vector<vector<int>> a(R, vector<int>(C)), columns(K + 1);
    for (int i = 0; i < R; i++)
        for (int j = 0; j < C; j++) {
            cin >> a[i][j];
            columns[a[i][j]].push_back(j + 1);
        }
    vector<Bit> colored;
    colored.reserve(K + 1);
    for (int c = 0; c <= K; c++) {
        auto &v = columns[c];
        sort(v.begin(), v.end());
        v.erase(unique(v.begin(), v.end()), v.end());
        colored.emplace_back(v.size());
    }
    Bit all(C);
    vector<int> row(C);
    int ans = 0;
    for (int i = 0; i < R; i++) {
        for (int j = 0; j < C; j++) {
            int c = a[i][j],
                r = lower_bound(columns[c].begin(), columns[c].end(), j + 1) - columns[c].begin();
            row[j] = (all.sum(j) - colored[c].sum(r) + 1000000007) % 1000000007;
            if (i == 0 && j == 0)
                row[j] = 1;
        }
        for (int j = 0; j < C; j++) {
            int c = a[i][j], r = lower_bound(columns[c].begin(), columns[c].end(), j + 1) -
                                 columns[c].begin() + 1;
            all.add(j + 1, row[j]);
            colored[c].add(r, row[j]);
        }
        ans = row[C - 1];
    }
    cout << ans << '\n';

    return 0;
}
