#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<long long> d(n), cost(n + 1);
    for (auto &x : d)
        cin >> x;
    sort(d.begin(), d.end());
    long long sum = 0;
    for (int i = 1; i <= n; i++) {
        sum += d[i - 1];
        cost[i] = cost[i - 1] + sum;
    }
    while (q--) {
        long long t;
        cin >> t;
        cout << upper_bound(cost.begin(), cost.end(), t) - cost.begin() - 1 << '\n';
    }

    return 0;
}
