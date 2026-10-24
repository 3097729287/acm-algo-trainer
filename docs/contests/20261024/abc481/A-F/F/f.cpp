#include <bits/stdc++.h>
using namespace std;
const long long MOD = 998244353;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    vector<vector<pair<int, int>>> graph(n + 1);
    while (m--) {
        int a, b, c;
        cin >> a >> b >> c;
        graph[a].push_back({b, c});
    }
    vector<bool> seen(n + 1, false);
    vector<long long> answer(n + 1, 0);
    queue<vector<int>> groups;
    groups.push({1});
    seen[1] = true;
    while (!groups.empty()) {
        vector<int> current = move(groups.front());
        groups.pop();
        vector<int> bucket[10];
        for (int u : current)
            for (auto [v, digit] : graph[u])
                if (!seen[v]) bucket[digit].push_back(v);
        for (int digit = 1; digit <= 9; ++digit) {
            vector<int> next;
            for (int v : bucket[digit]) {
                if (seen[v]) continue;
                // 必须在整组按末位排序后确认首次到达，不能按父顶点顺序抢占。
                seen[v] = true;
                answer[v] = (answer[current[0]] * 10 + digit) % MOD;
                next.push_back(v);
            }
            if (!next.empty()) groups.push(move(next));
        }
    }
    for (int v = 2; v <= n; ++v) cout << answer[v] << '\n';
}
