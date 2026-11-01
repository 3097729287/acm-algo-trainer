#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> x(n);
    for (auto &v : x) cin >> v;
    for (int k = 0; k < n; ++k) {
        if (n == 1) { cout << 0 << '\n'; continue; }
        long long answer = LLONG_MAX;
        // 先感染左邻居，两位传播者再分别向两端移动。
        if (k > 0) answer = min(answer, max(x[k] - x[0], x[n - 1] - x[k - 1]) / 2);
        // 对称地考虑先感染右邻居。
        if (k + 1 < n) answer = min(answer, max(x[k + 1] - x[0], x[n - 1] - x[k]) / 2);
        cout << answer << '\n';
    }
}
