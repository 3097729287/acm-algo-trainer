#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    bool first = true;
    while (n--) {
        long long x;
        cin >> x;
        bool prime = x >= 2;
        for (long long d = 2; prime && d <= x / d; d++)
            if (x % d == 0)
                prime = false;
        if (prime) {
            if (!first)
                cout << ' ';
            first = false;
            cout << x;
        }
    }
    cout << '\n';

    return 0;
}
