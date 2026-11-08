#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    unsigned long long p, q;
    cin >> p >> q;
    auto a = (p - 1) / 2, b = (q - 1) / 2;
    cout << (p == q ? a * (a + 1) : a * b) << '\n';

    return 0;
}
