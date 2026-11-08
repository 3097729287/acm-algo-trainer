#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int K, V, N;
    cin >> K >> V >> N;
    vector<vector<long long>> dp(V + 1);
    dp[0] = {0};
    for (int i = 0; i < N; i++) {
        int w;
        long long value;
        cin >> w >> value;
        for (int capacity = V; capacity >= w; capacity--) {
            const auto &left = dp[capacity];
            const auto &right = dp[capacity - w];
            vector<long long> next;
            int a = 0, b = 0;
            while ((int)next.size() < K && (a < (int)left.size() || b < (int)right.size())) {
                if (b == (int)right.size() || (a < (int)left.size() && left[a] >= right[b] + value))
                    next.push_back(left[a++]);
                else
                    next.push_back(right[b++] + value);
            }
            dp[capacity].swap(next);
        }
    }
    if ((int)dp[V].size() < K)
        return 0;
    cout << accumulate(dp[V].begin(), dp[V].end(), 0LL) << '\n';

    return 0;
}
