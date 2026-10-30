#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int N, K;
    cin >> N >> K;

    vector<long long> cnt(K, 0);
    cnt[0] = 1;          // 空前缀 S[0] = 0

    long long sum = 0;
    long long ans = 0;

    for (int i = 0; i < N; ++i) {
        long long a;
        cin >> a;
        sum += a;
        int r = (int)(sum % K);
        ans += cnt[r];
        ++cnt[r];
    }

    cout << ans << '\n';
    return 0;
}
