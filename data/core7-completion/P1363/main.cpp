#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        vector<string> a(n);
        pair<int, int> start;
        for (int i = 0; i < n; i++) {
            cin >> a[i];
            for (int j = 0; j < m; j++)
                if (a[i][j] == 'S')
                    start = {i, j};
        }
        vector<char> seen(n * m);
        vector<pair<int, int>> first(n * m);
        queue<pair<int, int>> q;
        q.push(start);
        seen[start.first * m + start.second] = 1;
        first[start.first * m + start.second] = start;
        bool yes = false;
        int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
        while (!q.empty() && !yes) {
            auto [x, y] = q.front();
            q.pop();
            for (int d = 0; d < 4; d++) {
                int nx = x + dx[d], ny = y + dy[d], r = (nx % n + n) % n, c = (ny % m + m) % m,
                    id = r * m + c;
                if (a[r][c] == '#')
                    continue;
                if (seen[id]) {
                    if (first[id] != pair<int, int>{nx, ny}) {
                        yes = true;
                        break;
                    }
                } else {
                    seen[id] = 1;
                    first[id] = {nx, ny};
                    q.push({nx, ny});
                }
            }
        }
        cout << (yes ? "Yes" : "No") << '\n';
    }

    return 0;
}
