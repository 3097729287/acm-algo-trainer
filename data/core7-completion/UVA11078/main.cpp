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
        long long best;
        cin >> best;
        long long answer = LLONG_MIN;
        for (int i = 1; i < n; i++) {
            long long x;
            cin >> x;
            answer = max(answer, best - x);
            best = max(best, x);
        }
        cout << answer << '\n';
    }

    return 0;
}
