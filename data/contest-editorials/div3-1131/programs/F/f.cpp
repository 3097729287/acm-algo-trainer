#include <bits/stdc++.h>
using namespace std;
const int MOD = 998244353;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        cin >> n >> m;
        int maximum = m + 2;
        vector<int> dp(maximum + 1), next_dp(maximum + 1), prefix(maximum + 1);
        dp[maximum] = 1;
        int answer = 0;
        for (int length = 1; length <= n; ++length) {
            // 长度不足 n 时，结束于 2 的前缀以全 1 后缀唯一补齐。
            answer += dp[2];
            if (answer >= MOD) answer -= MOD;
            if (length == n) break;
            prefix[0] = 0;
            for (int v = 1; v <= maximum; ++v) {
                prefix[v] = prefix[v - 1] + dp[v];
                if (prefix[v] >= MOD) prefix[v] -= MOD;
            }
            for (int v = 2; v <= maximum; ++v) {
                // 合法前驱 u 满足 v <= u < 2v。
                int hi = min(maximum, 2 * v - 1);
                next_dp[v] = prefix[hi] - prefix[v - 1];
                if (next_dp[v] < 0) next_dp[v] += MOD;
            }
            dp.swap(next_dp);
        }
        cout << answer << '\n';
    }
}
