#include <bits/stdc++.h>
using namespace std;

struct Hash {
    static uint64_t mix(uint64_t x) {
        x += 0x9e3779b97f4a7c15ULL;
        x = (x ^ (x >> 30)) * 0xbf58476d1ce4e5b9ULL;
        x = (x ^ (x >> 27)) * 0x94d049bb133111ebULL;
        return x ^ (x >> 31);
    }
    size_t operator()(long long x) const {
        static const uint64_t seed = chrono::steady_clock::now().time_since_epoch().count();
        return mix(x + seed);
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        unordered_map<long long, int, Hash> cnt;
        cnt.reserve(2 * n + 1);
        cnt[0] = 1;
        long long sum = 0;
        int ans = 0;
        for (int i = 0; i < n; i++) {
            long long x;
            cin >> x;
            sum += x;
            ans = max(ans, ++cnt[sum] - 1);
        }
        cout << ans << '\n';
    }

    return 0;
}
