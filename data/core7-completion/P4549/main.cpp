#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long g = 0;
    while (n--) {
        long long x;
        cin >> x;
        g = gcd(g, llabs(x));
    }
    cout << g << '\n';

    return 0;
}
