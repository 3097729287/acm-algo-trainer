#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<long long> b(n);
        for (int i = 0; i < n; ++i) {
            cin >> b[i];
            if (i % 2 == 1) b[i] = -b[i];
        }
        // 原操作恰好变成 b 的相邻交换，因此 b 可任意重排。
        sort(b.begin(), b.end());
        long long answer = 0;
        for (int i = 0; i < n; ++i) {
            if (i < n / 2) answer -= b[i];
            else answer += b[i];
        }
        cout << answer << '\n';
    }
}
