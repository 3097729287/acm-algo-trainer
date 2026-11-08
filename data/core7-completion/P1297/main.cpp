#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long A, B, C, raw;
    cin >> n >> A >> B >> C >> raw;
    long long first = raw % C + 1, previous = first;
    long double ans = 0;
    for (int i = 2; i <= n; i++) {
        raw = (raw * A + B) % 100000001;
        long long current = raw % C + 1;
        ans += 1.0L / max(previous, current);
        previous = current;
    }
    ans += 1.0L / max(previous, first);
    cout << fixed << setprecision(3) << ans << '\n';

    return 0;
}
