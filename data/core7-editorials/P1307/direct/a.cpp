#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long n; cin >> n;
bool negative = n < 0;
if (negative) n = -n;
long long reversed = 0;
while (n) { reversed = reversed * 10 + n % 10; n /= 10; }
cout << (negative ? -reversed : reversed) << '\n';
    return 0;
}
