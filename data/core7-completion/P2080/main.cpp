#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, v;
    cin >> n >> v;
    vector<pair<int, int>> events(n);
    int bound = 0;
    for (auto &[a, b] : events) {
        cin >> a >> b;
        bound += abs(a - b);
    }
    const int neg = INT_MIN / 4;
    vector<int> dp(2 * bound + 1, neg);
    dp[bound] = 0;
    for (auto [a, b] : events) {
        auto next = dp;
        int difference = a - b;
        for (int i = 0; i < (int)dp.size(); i++)
            if (dp[i] != neg && i + difference >= 0 && i + difference < (int)dp.size())
                next[i + difference] = max(next[i + difference], dp[i] + a + b);
        dp.swap(next);
    }
    int ans = INT_MAX;
    for (int i = 0; i < (int)dp.size(); i++)
        if (dp[i] >= v)
            ans = min(ans, abs(i - bound));
    cout << (ans == INT_MAX ? -1 : ans) << '\n';

    return 0;
}
