#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long h, r; cin >> h >> r;
long long volume = 314 * r * r * h;
cout << 2000000 / volume + (2000000 % volume != 0) << '\n';
    return 0;
}
