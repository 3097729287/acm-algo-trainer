#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, m;
    cin >> n >> m;
    long long squares = 0;
    for (long long k = 1; k <= min(n, m); k++)
        squares += (n - k + 1) * (m - k + 1);
    long long total = n * (n + 1) / 2 * (m * (m + 1) / 2);
    cout << squares << ' ' << total - squares << '\n';

    return 0;
}
