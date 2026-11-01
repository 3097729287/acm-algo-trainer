#include <bits/stdc++.h>
using namespace std;
using ll = long long;

ll firstA(ll a, ll b, ll x, ll y, ll n) {
    ll take = min(n, a - x);
    a -= take;
    n -= take;
    b -= min(n, b - y);
    return a * b;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        ll a, b, x, y, n;
        cin >> a >> b >> x >> y >> n;
        // 两个端点：先尽量减 a，或先尽量减 b。
        cout << min(firstA(a, b, x, y, n), firstA(b, a, y, x, n)) << '\n';
    }
}
