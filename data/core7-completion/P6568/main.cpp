#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    vector<long long> a(n);
    for (auto &x : a)
        cin >> x;
    long long sum = accumulate(a.begin(), a.begin() + k + 1, 0LL), ans = sum;
    for (int r = k + 1; r < n; r++) {
        sum += a[r] - a[r - k - 1];
        ans = max(ans, sum);
    }
    cout << ans << '\n';

    return 0;
}
