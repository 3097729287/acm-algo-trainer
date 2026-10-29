#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long a, b, c; cin >> a >> b >> c;
long long p = min({a,b,c}), q = max({a,b,c});
long long g = gcd(p,q);
cout << p/g << '/' << q/g << '\n';
    return 0;
}
