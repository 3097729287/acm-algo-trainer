#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int x, n; cin >> x >> n;
long long workdays = n / 7 * 5;
for (int i = 0; i < n % 7; ++i)
    if ((x - 1 + i) % 7 + 1 <= 5) ++workdays;
cout << workdays * 250 << '\n';
    return 0;
}
