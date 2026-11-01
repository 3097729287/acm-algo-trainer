#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> h(n);
    for (int &v : h) cin >> v;
    int sum = 0;
    for (int i = 0; i < k; ++i) sum += h[i];
    int best = sum, answer = 1;
    for (int r = k; r < n; ++r) {
        // 窗口右移：去掉最左木板，加入新右端木板。
        sum += h[r] - h[r - k];
        if (sum < best) {
            best = sum;
            answer = r - k + 2;  // 转为从一开始的左端点。
        }
    }
    cout << answer << '\n';
}
