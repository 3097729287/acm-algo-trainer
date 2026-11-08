#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, c;
    cin >> n >> c;
    unordered_map<int, pair<int, int>> state;
    state.reserve(2 * n + 1);
    int countC = 0, gain = 0;
    for (int i = 0; i < n; i++) {
        int x;
        cin >> x;
        if (x == c) {
            countC++;
            continue;
        }
        auto &[best, last] = state[x];
        best = max(1, best - (countC - last) + 1);
        last = countC;
        gain = max(gain, best);
    }
    cout << countC + gain << '\n';

    return 0;
}
