#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string line;
    while (getline(cin, line)) {
        if (line == "#")
            break;
        if (line.empty())
            continue;
        istringstream header(line);
        int n, m;
        header >> n >> m;
        map<string, int> ids;
        int used = 0;
        auto get = [&](const string &s) {
            auto it = ids.find(s);
            if (it != ids.end())
                return it->second;
            return ids[s] = ++used;
        };
        vector<vector<int>> g(n + 1);
        vector<int> parent(n + 1), size(n + 1);
        vector<long long> cost(n + 1);
        for (int i = 0; i < n; i++) {
            getline(cin, line);
            istringstream in(line);
            string name;
            long long value;
            in >> name >> value;
            int u = get(name);
            cost[u] = value;
            while (in >> name) {
                int v = get(name);
                g[u].push_back(v);
                parent[v] = u;
            }
        }
        for (int i = 1; i <= n; i++)
            if (!parent[i])
                g[0].push_back(i);
        vector<int> order = {0};
        for (int i = 0; i < (int)order.size(); i++)
            for (int u : g[order[i]])
                order.push_back(u);
        const long long INF = 1LL << 60;
        vector<vector<long long>> dp(n + 1);
        for (int i = n; i >= 0; i--) {
            int v = order[i];
            dp[v] = {0};
            for (int u : g[v]) {
                vector<long long> next(size[v] + size[u] + 1, INF);
                for (int a = 0; a <= size[v]; a++)
                    for (int b = 0; b <= size[u]; b++)
                        next[a + b] = min(next[a + b], dp[v][a] + dp[u][b]);
                size[v] += size[u];
                dp[v].swap(next);
            }
            if (v) {
                size[v]++;
                dp[v].resize(size[v] + 1, INF);
                dp[v][size[v]] = min(dp[v][size[v]], cost[v]);
            }
        }
        cout << *min_element(dp[0].begin() + m, dp[0].end()) << '\n';
    }

    return 0;
}
