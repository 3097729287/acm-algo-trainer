#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, B;
    cin >> n >> B;
    vector<bool> composite(n + 1), bad(n + 1);
    for (int p = 2; p <= n; p++)
        if (!composite[p]) {
            if (1LL * p * p <= n)
                for (int j = p * p; j <= n; j += p)
                    composite[j] = 1;
            if (p > B)
                for (int j = p; j <= n; j += p)
                    bad[j] = 1;
        }
    int ans = 0;
    for (int i = 1; i <= n; i++)
        ans += !bad[i];
    cout << ans << '\n';

    return 0;
}
