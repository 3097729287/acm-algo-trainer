#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<string> a(n);
    for (auto &s : a)
        cin >> s;
    int ans = 0;
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (a[i][j] != '0') {
                ans++;
                queue<pair<int, int>> q;
                q.push({i, j});
                a[i][j] = '0';
                while (!q.empty()) {
                    auto [x, y] = q.front();
                    q.pop();
                    for (int d = 0; d < 4; d++) {
                        int nx = x + dx[d], ny = y + dy[d];
                        if (nx >= 0 && nx < n && ny >= 0 && ny < m && a[nx][ny] != '0') {
                            a[nx][ny] = '0';
                            q.push({nx, ny});
                        }
                    }
                }
            }
    cout << ans << '\n';

    return 0;
}
