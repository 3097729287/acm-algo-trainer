#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<vector<int>> a(n, vector<int>(n));
    for (auto &r : a)
        for (int &x : r)
            cin >> x;
    vector<unordered_map<int, long long>> cnt(n);
    function<void(int, int, int)> go = [&](int x, int y, int v) {
        v ^= a[x][y];
        if (x + y == n - 1) {
            cnt[x][v]++;
            return;
        }
        if (x + 1 < n)
            go(x + 1, y, v);
        if (y + 1 < n)
            go(x, y + 1, v);
    };
    go(0, 0, 0);
    long long ans = 0;
    function<void(int, int, int)> back = [&](int x, int y, int v) {
        v ^= a[x][y];
        if (x + y == n - 1) {
            auto it = cnt[x].find(v ^ a[x][y]);
            if (it != cnt[x].end())
                ans += it->second;
            return;
        }
        if (x)
            back(x - 1, y, v);
        if (y)
            back(x, y - 1, v);
    };
    back(n - 1, n - 1, 0);
    cout << ans << '\n';

    return 0;
}
