#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long k;
    cin >> n >> k;
    long long value = 1;
    while (n--) {
        long long x;
        cin >> x;
        long long g = gcd(x, k);
        value = value / gcd(value, g) * g;
    }
    cout << (value == k ? "Yes" : "No") << '\n';

    return 0;
}
