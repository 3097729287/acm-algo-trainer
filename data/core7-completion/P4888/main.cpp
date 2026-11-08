#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<string> a(n);
    for (auto &s : a)
        cin >> s;
    while (q--) {
        int x, y;
        cin >> x >> y;
        x--;
        y--;
        int horizontal = 0, vertical = 0;
        while (y - horizontal - 1 >= 0 && y + horizontal + 1 < n &&
               a[x][y - horizontal - 1] == a[x][y + horizontal + 1])
            horizontal++;
        while (x - vertical - 1 >= 0 && x + vertical + 1 < n &&
               a[x - vertical - 1][y] == a[x + vertical + 1][y])
            vertical++;
        cout << 2 * max(horizontal, vertical) + 1 << '\n';
    }

    return 0;
}
