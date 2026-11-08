#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<array<long long, 3>> f(n);
    for (auto &v : f)
        cin >> v[0] >> v[1] >> v[2];
    auto value = [&](int i, long long x) { return f[i][0] * x * x + f[i][1] * x + f[i][2]; };
    using Item = tuple<long long, int, int>;
    priority_queue<Item, vector<Item>, greater<Item>> q;
    for (int i = 0; i < n; i++)
        q.push({value(i, 1), i, 1});
    for (int step = 0; step < m; step++) {
        auto [v, i, x] = q.top();
        q.pop();
        cout << v << (step + 1 == m ? '\n' : ' ');
        q.push({value(i, x + 1), i, x + 1});
    }

    return 0;
}
