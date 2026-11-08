#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    int L = 1;
    while (2 * L <= n)
        L *= 2;
    vector<pair<int, int>> ops;
    function<void(int, int)> solve = [&](int l, int length) {
        if (length == 1)
            return;
        int half = length / 2;
        solve(l, half);
        solve(l + half, half);
        for (int i = 0; i < half; i++)
            ops.push_back({l + i, l + half + i});
    };
    solve(1, L);
    solve(n - L + 1, L);
    cout << ops.size() << '\n';
    for (auto [a, b] : ops)
        cout << a << ' ' << b << '\n';

    return 0;
}
