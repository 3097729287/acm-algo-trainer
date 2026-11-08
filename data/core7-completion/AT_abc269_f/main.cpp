#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long N, M;
    int Q;
    cin >> N >> M >> Q;
    const long long P = 998244353, INV2 = (P + 1) / 2;
    auto range = [&](long long l, long long r, int parity) {
        if (l % 2 != parity)
            l++;
        if (l > r)
            return pair<long long, long long>{0, 0};
        long long count = (r - l) / 2 + 1, last = l + 2 * (count - 1);
        long long sum = (l + last) % P * (count % P) % P * INV2 % P;
        return pair<long long, long long>{count % P, sum};
    };
    while (Q--) {
        long long A, B, C, D;
        cin >> A >> B >> C >> D;
        long long ans = 0;
        for (int parity = 0; parity < 2; parity++) {
            auto [nr, sr] = range(A, B, parity);
            auto [nc, sc] = range(C, D, parity);
            sr = (sr - nr + P) % P;
            ans = (ans + (M % P) * sr % P * nc + sc * nr) % P;
        }
        cout << ans << '\n';
    }

    return 0;
}
