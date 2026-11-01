#include <bits/stdc++.h>
using namespace std;
const long long MOD = 998244353;
struct State { int node, parent, depth, carry; };
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<vector<int>> graph(n);
        for (int i = 1, u, v; i < n; ++i) {
            cin >> u >> v; --u; --v;
            graph[u].push_back(v); graph[v].push_back(u);
        }
        string x, y;
        cin >> x >> y;
        vector<int> bit(n, -1);
        vector<long long> power(n, 1);
        for (int i = 1; i < n; ++i) power[i] = power[i - 1] * 2 % MOD;
        vector<State> stack = {{0, -1, 0, 0}};
        bool possible = true;
        long long answer = 0;
        while (!stack.empty()) {
            State current = stack.back(); stack.pop_back();
            int u = current.node, depth = current.depth;
            int xb = x[u] - '0', yb = y[u] - '0';
            int needed = xb ^ yb ^ current.carry;
            if (bit[depth] == -1) {
                bit[depth] = needed;
                answer = (answer + needed * power[depth]) % MOD;
            } else if (bit[depth] != needed) {
                possible = false; break;
            }
            // 同一深度共用 K 的这一位，但每条根路径的进位可以不同。
            int next_carry = (xb + needed + current.carry) / 2;
            for (int v : graph[u]) if (v != current.parent)
                stack.push_back({v, u, depth + 1, next_carry});
        }
        cout << (possible ? answer : -1) << '\n';
    }
}
