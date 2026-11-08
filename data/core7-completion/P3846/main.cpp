#include <bits/stdc++.h>
using namespace std;

long long multiply(long long a, long long b, long long mod) { return (__int128)a * b % mod; }
long long modularPower(long long a, long long b, long long mod) {
    long long ans = 1;
    for (; b; b >>= 1, a = multiply(a, a, mod))
        if (b & 1)
            ans = multiply(ans, a, mod);
    return ans;
}
long long logarithm(long long base, long long target, long long mod) {
    long long block = sqrt((long double)mod) + 1;
    unordered_map<long long, int> baby;
    baby.reserve(2 * block);
    long long value = 1;
    for (int j = 0; j < block; j++) {
        baby.emplace(value, j);
        value = multiply(value, base, mod);
    }
    long long inverse = modularPower(value, mod - 2, mod);
    value = target;
    for (long long i = 0; i <= block; i++) {
        auto it = baby.find(value);
        if (it != baby.end())
            return i * block + it->second;
        value = multiply(value, inverse, mod);
    }
    return -1;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long p, b, n;
    cin >> p >> b >> n;
    long long answer = logarithm(b, n, p);
    if (answer < 0)
        cout << "no solution\n";
    else
        cout << answer << '\n';

    return 0;
}
