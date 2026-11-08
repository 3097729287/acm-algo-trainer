#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long double> x(n), y(n), distance(n, numeric_limits<long double>::infinity());
    for (int i = 0; i < n; i++)
        cin >> x[i] >> y[i];
    vector<char> used(n);
    distance[0] = 0;
    long double ans = 0;
    for (int step = 0; step < n; step++) {
        int v = -1;
        for (int i = 0; i < n; i++)
            if (!used[i] && (v < 0 || distance[i] < distance[v]))
                v = i;
        used[v] = 1;
        ans += sqrt(distance[v]);
        for (int u = 0; u < n; u++)
            if (!used[u])
                distance[u] =
                    min(distance[u], (x[u] - x[v]) * (x[u] - x[v]) + (y[u] - y[v]) * (y[u] - y[v]));
    }
    cout << fixed << setprecision(2) << ans << '\n';

    return 0;
}
