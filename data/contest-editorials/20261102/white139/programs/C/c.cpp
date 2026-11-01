#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n, x;
        cin >> n >> x;
        priority_queue<long long, vector<long long>, greater<long long>> heap;
        long long ans = 0;
        int changed = 0;
        for (int i = 1; i <= n; ++i) {
            long long c;
            cin >> c;
            heap.push(c);
            if (i - 2 * changed > x) {
                // 当前前缀必须再改一场，选尚未改判的最小代价。
                ans += heap.top();
                heap.pop();
                ++changed;
            }
        }
        // 改判只会降低小芳的分差，最少次数仍不能赢就无解。
        cout << (n - 2 * changed > 0 ? ans : -1) << '\n';
    }
}
