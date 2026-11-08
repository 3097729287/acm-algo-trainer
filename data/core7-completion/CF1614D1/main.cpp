#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int maximum = 0;
    for (int &x : a) {
        cin >> x;
        maximum = max(maximum, x);
    }
    vector<int> frequency(maximum + 1), count(maximum + 1);
    for (int x : a)
        frequency[x]++;
    for (int d = 1; d <= maximum; d++)
        for (int j = d; j <= maximum; j += d)
            count[d] += frequency[j];
    vector<long long> dp(maximum + 1);
    for (int d = maximum; d >= 1; d--) {
        dp[d] = 1LL * d * count[d];
        for (int j = d + d; j <= maximum; j += d)
            dp[d] = max(dp[d], dp[j] + 1LL * d * (count[d] - count[j]));
    }
    cout << dp[1] << '\n';

    return 0;
}
