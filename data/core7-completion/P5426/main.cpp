#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(2 * n);
    int ones = 0;
    for (int &x : a) {
        cin >> x;
        ones += x;
    }
    auto inversions = [&](int l, int r) {
        long long count = 0, answer = 0;
        for (int i = l; i < r; i++)
            if (a[i])
                count++;
            else
                answer += count;
        return answer;
    };
    long long initial = inversions(0, n) - inversions(n, 2 * n), ans = llabs(initial);
    for (int bit = 0; bit < 2; bit++) {
        vector<int> left, right;
        for (int i = n - 1; i >= 0; i--)
            if (a[i] == bit)
                left.push_back(i);
        for (int i = 0; i < n; i++)
            if (a[n + i] != bit)
                right.push_back(i);
        long long delta = initial, cost = 0;
        int sign = bit ? 1 : -1;
        for (int i = 0; i < (int)min(left.size(), right.size()); i++) {
            long long q = left[i], z = right[i];
            cost += n - q + z;
            delta += sign * (q + z - 2 * n + 1 + ones);
            ans = min(ans, cost + llabs(delta));
        }
    }
    cout << ans << '\n';

    return 0;
}
