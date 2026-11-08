#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    string goal = "111110111100*110000100000";
    while (T--) {
        string a;
        for (int i = 0; i < 5; i++) {
            string row;
            cin >> row;
            a += row;
        }
        int hole = a.find('*'), h = 0;
        for (int i = 0; i < 25; i++)
            if (a[i] != '*' && a[i] != goal[i])
                h++;
        vector<vector<int>> g(25);
        for (int i = 0; i < 25; i++)
            for (auto [dx, dy] : vector<pair<int, int>>{
                     {1, 2}, {1, -2}, {-1, 2}, {-1, -2}, {2, 1}, {2, -1}, {-2, 1}, {-2, -1}}) {
                int x = i / 5 + dx, y = i % 5 + dy;
                if (x >= 0 && x < 5 && y >= 0 && y < 5)
                    g[i].push_back(x * 5 + y);
            }
        function<bool(int, int, int, int, int)> dfs = [&](int p, int prev, int used, int lower,
                                                          int limit) {
            if (used + lower > limit)
                return false;
            if (a == goal)
                return true;
            if (used == limit)
                return false;
            vector<pair<int, int>> moves;
            for (int u : g[p])
                if (u != prev)
                    moves.push_back({lower - (a[u] != goal[u]) + (a[u] != goal[p]), u});
            sort(moves.begin(), moves.end());
            for (auto [nh, u] : moves) {
                swap(a[p], a[u]);
                bool found = dfs(u, p, used + 1, nh, limit);
                swap(a[p], a[u]);
                if (found)
                    return true;
            }
            return false;
        };
        int parity = (hole / 5 + hole % 5) % 2, ans = -1;
        for (int limit = h; limit <= 15; limit++)
            if (limit % 2 == parity && dfs(hole, -1, 0, h, limit)) {
                ans = limit;
                break;
            }
        cout << ans << '\n';
    }

    return 0;
}
