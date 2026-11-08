#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<long long> s(n), b(n);
    for (int i = 0; i < n; i++)
        cin >> s[i] >> b[i];
    long long ans = LLONG_MAX;
    for (int mask = 1; mask < (1 << n); mask++) {
        long long sour = 1, bitter = 0;
        for (int i = 0; i < n; i++)
            if ((mask >> i) & 1) {
                sour *= s[i];
                bitter += b[i];
            }
        ans = min(ans, llabs(sour - bitter));
    }
    cout << ans << '\n';

    return 0;
}
