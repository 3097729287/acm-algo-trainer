#include <bits/stdc++.h>
using namespace std;
int main() {
    int T; cin >> T;
    while (T--) {
        int n; cin >> n;
        vector<long long> a(n);
        for (auto &v : a) cin >> v;
        long long ans = 0;
        for (int i = 0; i < n; ++i)
            for (int j = i; j < n; ++j)
                ans += min(a[i], a[j]) + max(0LL, a[j] - a[i]);
        cout << ans << '\n';
    }
}
