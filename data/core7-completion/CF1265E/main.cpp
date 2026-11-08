#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long P = 998244353;
    auto power = [&](long long a, long long b) {
        long long r = 1;
        for (; b; b >>= 1, a = a * a % P)
            if (b & 1)
                r = r * a % P;
        return r;
    };
    long long E = 0;
    for (int i = 0; i < n; i++) {
        long long p;
        cin >> p;
        E = (E + 1) * 100 % P * power(p, P - 2) % P;
    }
    cout << E << '\n';

    return 0;
}
