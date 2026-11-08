#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> f(max(n + 1, 3));
    f[0] = f[1] = 1;
    f[2] = 2;
    for (int i = 3; i <= n; i++)
        f[i] = (2 * f[i - 1] + f[i - 3]) % 10000;
    cout << f[n] << '\n';

    return 0;
}
