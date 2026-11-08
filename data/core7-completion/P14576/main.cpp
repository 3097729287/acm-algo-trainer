#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<long long> position(n);
        long long current = 0, width = 0;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            width = max(width, x);
            current += x + 1;
            position[i] = current - 1;
        }
        int l = 0, ans = 0;
        for (int r = 0; r < n; r++) {
            while (position[r] - position[l] > width)
                l++;
            ans = max(ans, r - l + 1);
        }
        cout << ans << '\n';
    }

    return 0;
}
