#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        long long k;
        cin >> k;
        vector<int> d;
        for (int base = 2; k; base++) {
            d.push_back(k % base);
            k /= base;
        }
        auto countWays = [&](vector<int> a) {
            int L = a.size();
            sort(a.rbegin(), a.rend());
            __int128 ways = 1;
            vector<int> cnt(22);
            for (int i = 0; i < L; i++) {
                int choices = L - max(1, a[i]) + 1 - i;
                if (choices <= 0)
                    return (long long)0;
                ways *= choices;
                cnt[a[i]]++;
            }
            for (int c : cnt)
                for (int i = 2; i <= c; i++)
                    ways /= i;
            return (long long)ways;
        };
        long long ans = countWays(d);
        auto it = find(d.begin(), d.end(), 0);
        if (it != d.end()) {
            d.erase(it);
            ans -= countWays(d);
        }
        cout << ans - 1 << '\n';
    }

    return 0;
}
