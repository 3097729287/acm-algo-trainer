#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
double a, b, c; cin >> a >> b >> c;
double p = (a + b + c) / 2;
cout << fixed << setprecision(1) << sqrt(p * (p-a) * (p-b) * (p-c)) << '\n';
    return 0;
}
