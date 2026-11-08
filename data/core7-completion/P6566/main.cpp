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
    vector<int> cnt(n * m + 1);
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++)
            if (a[i][j] == '*') {
                vector<int> q = {i * m + j};
                a[i][j] = '.';
                for (int k = 0; k < (int)q.size(); k++) {
                    int x = q[k] / m, y = q[k] % m;
                    for (int dx = -1; dx <= 1; dx++)
                        for (int dy = -1; dy <= 1; dy++) {
                            int nx = x + dx, ny = y + dy;
                            if (nx >= 0 && nx < n && ny >= 0 && ny < m && a[nx][ny] == '*') {
                                a[nx][ny] = '.';
                                q.push_back(nx * m + ny);
                            }
                        }
                }
                cnt[q.size()]++;
            }
    int systems = 0, best = 0;
    for (int s = 1; s <= n * m; s++)
        if (cnt[s]) {
            systems++;
            best = max(best, s * cnt[s]);
        }
    cout << systems << ' ' << best << '\n';

    return 0;
}
