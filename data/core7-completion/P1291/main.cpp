#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    long long numerator = 0, denominator = 1;
    for (long long i = 1; i <= n; i++) {
        long long g = gcd(denominator, i);
        numerator = numerator * (i / g) + n * (denominator / g);
        denominator *= i / g;
        g = gcd(numerator, denominator);
        numerator /= g;
        denominator /= g;
    }
    long long whole = numerator / denominator, rem = numerator % denominator;
    if (!rem)
        cout << whole << '\n';
    else {
        string pad(to_string(whole).size(), ' ');
        cout << pad << rem << '\n'
             << whole << string(to_string(denominator).size(), '-') << '\n'
             << pad << denominator << '\n';
    }

    return 0;
}
