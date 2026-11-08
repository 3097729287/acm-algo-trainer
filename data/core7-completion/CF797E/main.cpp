#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n + 1);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    int q;
    cin >> q;
    int B = sqrt(n) + 1;
    vector<vector<pair<int, int>>> small(B + 1);
    vector<int> ans(q), dp(n + 1);
    for (int i = 0; i < q; i++) {
        int p, k;
        cin >> p >> k;
        if (k <= B)
            small[k].push_back({p, i});
        else {
            int count = 0;
            for (; p <= n; p += a[p] + k)
                count++;
            ans[i] = count;
        }
    }
    for (int k = 0; k <= B; k++)
        if (!small[k].empty()) {
            for (int i = n; i >= 1; i--) {
                long long next = 1LL * i + a[i] + k;
                dp[i] = 1 + (next <= n ? dp[next] : 0);
            }
            for (auto [p, id] : small[k])
                ans[id] = dp[p];
        }
    for (int x : ans)
        cout << x << '\n';

    return 0;
}
