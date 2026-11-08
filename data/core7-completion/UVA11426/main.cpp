#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    vector<int> queries;
    int n, maximum = 0;
    while (cin >> n && n) {
        queries.push_back(n);
        maximum = max(maximum, n);
    }
    vector<int> phi(maximum + 1);
    iota(phi.begin(), phi.end(), 0);
    for (int p = 2; p <= maximum; p++)
        if (phi[p] == p)
            for (int j = p; j <= maximum; j += p)
                phi[j] = phi[j] / p * (p - 1);
    vector<long long> sum(maximum + 1);
    for (int d = 1; d <= maximum / 2; d++)
        for (int j = d + d; j <= maximum; j += d)
            sum[j] += 1LL * d * phi[j / d];
    for (int i = 1; i <= maximum; i++)
        sum[i] += sum[i - 1];
    for (int x : queries)
        cout << sum[x] << '\n';

    return 0;
}
