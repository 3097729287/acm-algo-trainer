#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int a, b, n;
    cin >> a >> b >> n;
    int turn = 0;
    while (n) {
        n -= gcd(turn ? b : a, n);
        turn ^= 1;
    }
    cout << (turn ^ 1) << '\n';

    return 0;
}
