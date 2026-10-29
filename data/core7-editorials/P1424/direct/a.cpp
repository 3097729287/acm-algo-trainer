#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int x, n; cin >> x >> n;
long long distance = 0;
for (int i = 0; i < n; ++i) {
    if (x <= 5) distance += 250;
    x = x % 7 + 1;
}
cout << distance << '\n';
    return 0;
}
