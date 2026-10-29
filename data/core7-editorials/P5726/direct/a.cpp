#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n;
int sum = 0, low = 11, high = -1;
for (int i = 0; i < n; ++i) { int x; cin >> x; sum += x; low = min(low,x); high = max(high,x); }
cout << fixed << setprecision(2) << 1.0*(sum-low-high)/(n-2) << '\n';
    return 0;
}
