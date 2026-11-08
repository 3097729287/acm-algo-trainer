#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n;
    cin >> n;
    if (n < 4) {
        cout << 0 << '\n';
        return 0;
    }
    __int128 value = (__int128)n * (n - 1) * (n - 2) * (n - 3) / 24;
    string s;
    do {
        s.push_back('0' + value % 10);
        value /= 10;
    } while (value);
    reverse(s.begin(), s.end());
    cout << s << '\n';

    return 0;
}
