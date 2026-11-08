#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> x(n), y(n), c(n), k(n), distance;
    for (int i = 0; i < n; i++)
        cin >> x[i] >> y[i];
    for (auto &v : c)
        cin >> v;
    for (auto &v : k)
        cin >> v;
    distance = c;
    vector<int> from(n, -1), stations;
    vector<pair<int, int>> wires;
    vector<char> used(n);
    long long answer = 0;
    for (int step = 0; step < n; step++) {
        int v = -1;
        for (int i = 0; i < n; i++)
            if (!used[i] && (v < 0 || distance[i] < distance[v]))
                v = i;
        used[v] = 1;
        answer += distance[v];
        if (from[v] < 0)
            stations.push_back(v + 1);
        else
            wires.push_back({from[v] + 1, v + 1});
        for (int u = 0; u < n; u++)
            if (!used[u]) {
                long long cost = (llabs(x[u] - x[v]) + llabs(y[u] - y[v])) * (k[u] + k[v]);
                if (cost < distance[u]) {
                    distance[u] = cost;
                    from[u] = v;
                }
            }
    }
    cout << answer << '\n' << stations.size() << '\n';
    for (int v : stations)
        cout << v << ' ';
    cout << '\n' << wires.size() << '\n';
    for (auto [a, b] : wires)
        cout << a << ' ' << b << '\n';

    return 0;
}
