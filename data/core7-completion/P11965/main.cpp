#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    unordered_map<int, long long> cnt;
    cnt.reserve(2 * n + 1);
    cnt[0] = 1;
    int mask = 0;
    long long ans = 0;
    for (char c : s) {
        mask ^= 1 << (c - 'a');
        ans += cnt[mask];
        cnt[mask]++;
    }
    cout << ans << '\n';

    return 0;
}
