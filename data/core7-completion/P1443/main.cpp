#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m, x, y;
    cin >> n >> m >> x >> y;
    x--;
    y--;
    vector<vector<int>> d(n, vector<int>(m, -1));
    queue<pair<int, int>> q;
    q.push({x, y});
    d[x][y] = 0;
    int dx[] = {1, 1, -1, -1, 2, 2, -2, -2}, dy[] = {2, -2, 2, -2, 1, -1, 1, -1};
    while (!q.empty()) {
        auto [a, b] = q.front();
        q.pop();
        for (int k = 0; k < 8; k++) {
            int u = a + dx[k], v = b + dy[k];
            if (u >= 0 && u < n && v >= 0 && v < m && d[u][v] < 0) {
                d[u][v] = d[a][b] + 1;
                q.push({u, v});
            }
        }
    }
    for (auto &row : d) {
        for (int value : row)
            cout << left << setw(5) << value;
        cout << '\n';
    }

    return 0;
}
