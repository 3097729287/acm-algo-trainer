#include <bits/stdc++.h>
using namespace std;

long long exgcd(long long a, long long b, long long &x, long long &y) {
    if (!b) {
        x = 1;
        y = 0;
        return a;
    }
    long long u, v;
    long long g = exgcd(b, a % b, u, v);
    x = v;
    y = u - a / b * v;
    return g;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long x, y, m, n, L;
    cin >> x >> y >> m >> n >> L;
    long long a = m - n, b = y - x, u, v, g = exgcd(llabs(a), L, u, v);
    if (b % g) {
        cout << "Impossible\n";
        return 0;
    }
    if (a < 0)
        u = -u;
    long long mod = L / g;
    long long t = (__int128)u * (b / g) % mod;
    if (t < 0)
        t += mod;
    cout << t << '\n';

    return 0;
}
