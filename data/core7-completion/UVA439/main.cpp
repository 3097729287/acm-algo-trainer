#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string a, b;
    while (cin >> a >> b) {
        int d[8][8];
        memset(d, -1, sizeof d);
        queue<pair<int, int>> q;
        int sx = a[0] - 'a', sy = a[1] - '1';
        d[sx][sy] = 0;
        q.push({sx, sy});
        int dx[] = {1, 1, -1, -1, 2, 2, -2, -2}, dy[] = {2, -2, 2, -2, 1, -1, 1, -1};
        while (!q.empty()) {
            auto [x, y] = q.front();
            q.pop();
            for (int k = 0; k < 8; k++) {
                int u = x + dx[k], v = y + dy[k];
                if (u >= 0 && u < 8 && v >= 0 && v < 8 && d[u][v] < 0) {
                    d[u][v] = d[x][y] + 1;
                    q.push({u, v});
                }
            }
        }
        cout << "To get from " << a << " to " << b << " takes " << d[b[0] - 'a'][b[1] - '1']
             << " knight moves.\n";
    }

    return 0;
}
