#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int w, h;
    cin >> w >> h;
    vector<string> a(h);
    queue<pair<int, int>> q;
    for (int i = 0; i < h; i++) {
        cin >> a[i];
        for (int j = 0; j < w; j++)
            if (a[i][j] == '@') {
                q.push({i, j});
                a[i][j] = '#';
            }
    }
    int ans = 0;
    int dx[4] = {1, -1, 0, 0}, dy[4] = {0, 0, 1, -1};
    while (!q.empty()) {
        auto [x, y] = q.front();
        q.pop();
        ans++;
        for (int d = 0; d < 4; d++) {
            int nx = x + dx[d], ny = y + dy[d];
            if (nx >= 0 && nx < h && ny >= 0 && ny < w && a[nx][ny] == '.') {
                a[nx][ny] = '#';
                q.push({nx, ny});
            }
        }
    }
    cout << ans << '\n';

    return 0;
}
