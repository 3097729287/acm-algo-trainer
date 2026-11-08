#include <bits/stdc++.h>
using namespace std;

const long long MOD = 1000000007;
long long power(long long a, long long b) {
    long long r = 1;
    for (; b; b >>= 1, a = a * a % MOD)
        if (b & 1)
            r = r * a % MOD;
    return r;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> event(2 * n + 2);
    for (int i = 0; i < n; i++) {
        int l, r;
        cin >> l >> r;
        event[l] = 1;
        event[r] = -1;
    }
    vector<long long> two(n + 1, 1);
    for (int i = 1; i <= n; i++)
        two[i] = two[i - 1] * 2 % MOD;
    int active = 0;
    long long ans = 0;
    for (int x = 1; x <= 2 * n; x++) {
        if (event[x] == 1) {
            ans = (ans + two[n - 1 - active]) % MOD;
            active++;
        } else if (event[x] == -1)
            active--;
    }
    cout << ans << '\n';

    return 0;
}
