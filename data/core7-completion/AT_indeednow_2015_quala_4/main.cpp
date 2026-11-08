#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int h, w;
    cin >> h >> w;
    int n = h * w;
    vector<int> a(n);
    int blank = 0, estimate = 0;
    vector<vector<int>> distance(n, vector<int>(n));
    for (int p = 0; p < n; p++)
        for (int value = 1; value < n; value++)
            distance[p][value] = abs(p / w - (value - 1) / w) + abs(p % w - (value - 1) % w);
    for (int i = 0; i < n; i++) {
        cin >> a[i];
        if (a[i])
            estimate += distance[i][a[i]];
        else
            blank = i;
    }
    vector<vector<int>> neighbors(n);
    for (int p = 0; p < n; p++)
        for (auto [dx, dy] : vector<pair<int, int>>{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
            int x = p / w + dx, y = p % w + dy;
            if (x >= 0 && x < h && y >= 0 && y < w)
                neighbors[p].push_back(x * w + y);
        }
    function<bool(int, int, int, int, int)> search = [&](int hole, int previous, int used,
                                                         int lower, int limit) {
        if (used + lower > limit)
            return false;
        if (lower == 0)
            return true;
        vector<pair<int, int>> moves;
        for (int next : neighbors[hole])
            if (next != previous) {
                int value = a[next],
                    newLower = lower - distance[next][value] + distance[hole][value];
                moves.push_back({newLower, next});
            }
        sort(moves.begin(), moves.end());
        for (auto [newLower, next] : moves) {
            swap(a[hole], a[next]);
            bool found = search(next, hole, used + 1, newLower, limit);
            swap(a[hole], a[next]);
            if (found)
                return true;
        }
        return false;
    };
    for (int limit = estimate; limit <= 24; limit += 2)
        if (search(blank, -1, 0, estimate, limit)) {
            cout << limit << '\n';
            return 0;
        }

    return 0;
}
