#include <bits/stdc++.h>
using namespace std;
using ll = long long;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    const int M = 1000000;
    vector<bool> prime(M + 1, true);
    prime[0] = prime[1] = false;
    for (int p = 2; p * p <= M; ++p) {
        if (prime[p]) {
            for (int v = p * p; v <= M; v += p) prime[v] = false;
        }
    }
    int n;
    cin >> n;
    while (n--) {
        ll x;
        cin >> x;
        ll r = static_cast<ll>(sqrtl(static_cast<long double>(x)));
        // 浮点平方根只给候选值，再用整数运算校正。
        while ((r + 1) * (r + 1) <= x) ++r;
        while (r * r > x) --r;
        cout << (r * r == x && prime[r] ? "YES" : "NO") << '\n';
    }
}
