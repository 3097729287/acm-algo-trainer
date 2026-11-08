#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, na, nb;
    cin >> n >> na >> nb;
    vector<int> a(na), b(nb);
    for (int &x : a)
        cin >> x;
    for (int &x : b)
        cin >> x;
    int win[5][5] = {
        {0, 0, 1, 1, 0}, {1, 0, 0, 1, 0}, {0, 1, 0, 0, 1}, {0, 0, 1, 0, 1}, {1, 1, 0, 0, 0}};
    int first = 0, second = 0;
    for (int i = 0; i < n; i++) {
        int x = a[i % na], y = b[i % nb];
        first += win[x][y];
        second += win[y][x];
    }
    cout << first << ' ' << second << '\n';

    return 0;
}
