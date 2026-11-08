#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        long long m;
        cin >> m;
        long long l = 1, r = 2 * m;
        while (l < r) {
            long long mid = (l + r) / 2;
            if (mid * (mid - 1) / 2 >= m)
                r = mid;
            else
                l = mid + 1;
        }
        long long high = 2 * m - 2;
        if (l > high)
            cout << "Lose!\n";
        else
            cout << l << ' ' << high << '\n';
    }

    return 0;
}
