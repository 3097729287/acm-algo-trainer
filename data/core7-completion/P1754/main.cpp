#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long ans = 1;
    for (int i = 1; i <= n; i++)
        ans = ans * (4 * i - 2) / (i + 1);
    cout << ans << '\n';

    return 0;
}
