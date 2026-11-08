#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long a[7], sum = 0;
    for (auto &x : a) {
        cin >> x;
        sum += x;
    }
    long double ans = 0;
    if (sum >= 7) {
        ans = 5040.0L * (sum - 6);
        for (int i = 0; i < 7; i++)
            ans = ans * a[i] / (sum - i);
    }
    cout << fixed << setprecision(3) << ans << '\n';

    return 0;
}
