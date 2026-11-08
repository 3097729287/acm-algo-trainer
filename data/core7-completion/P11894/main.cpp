#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<long long> a(n + 1);
    vector<int> difference(n + 2);
    for (int i = 1; i <= n; i++)
        cin >> a[i];
    while (m--) {
        int l, r;
        cin >> l >> r;
        difference[l]++;
        difference[r + 1]--;
    }
    int count = 0;
    for (int i = 1; i <= n; i++) {
        count += difference[i];
        long long left = count, x = a[i];
        while (left && x > 1) {
            int b = 63 - __builtin_clzll(x);
            long long gap = (1LL << (b + 1)) - x, steps = min(left, (gap + b - 1) / b);
            x += steps * b;
            left -= steps;
        }
        cout << x << (i == n ? '\n' : ' ');
    }

    return 0;
}
