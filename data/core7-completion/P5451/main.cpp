#include <bits/stdc++.h>
using namespace std;

long long egcd(long long a, long long b, __int128 &x, __int128 &y) {
    if (!b) {
        x = 1;
        y = 0;
        return a;
    }
    __int128 u, v;
    long long g = egcd(b, a % b, u, v);
    x = v;
    y = u - (__int128)(a / b) * v;
    return g;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long c1, c2, e1, e2, N;
        cin >> c1 >> c2 >> e1 >> e2 >> N;
        __int128 a, b;
        egcd(e1, e2, a, b);
        auto inverse = [&](long long x) {
            __int128 u, v;
            egcd(x, N, u, v);
            u %= N;
            if (u < 0)
                u += N;
            return (long long)u;
        };
        auto power = [&](long long x, __int128 exponent) {
            if (exponent < 0) {
                x = inverse(x);
                exponent = -exponent;
            }
            long long r = 1;
            for (; exponent; exponent >>= 1, x = (__int128)x * x % N)
                if (exponent & 1)
                    r = (__int128)r * x % N;
            return r;
        };
        cout << (long long)((__int128)power(c1, a) * power(c2, b) % N) << '\n';
    }

    return 0;
}
