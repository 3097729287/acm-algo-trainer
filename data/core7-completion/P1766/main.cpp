#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long x;
    cin >> n >> x;
    struct Segment {
        long long l, yl, r, yr;
    };
    vector<Segment> a(n);
    for (auto &s : a) {
        cin >> s.l >> s.yl >> s.r >> s.yr;
        if (s.l > s.r) {
            swap(s.l, s.r);
            swap(s.yl, s.yr);
        }
    }
    long long y = 1000000001LL;
    vector<char> used(n);
    for (int step = 0; step <= n; step++) {
        int best = -1;
        long long bestNum = 0, bestDen = 1;
        bool tie = false;
        for (int i = 0; i < n; i++)
            if (!used[i]) {
                auto s = a[i];
                if (s.l == s.r) {
                    if (x == s.l && min(s.yl, s.yr) < y)
                        return 0;
                    continue;
                }
                if (!(s.l < x && x < s.r))
                    continue;
                if (s.yl == s.yr && s.yl <= y)
                    return 0;
                long long den = s.r - s.l, num = s.yl * den + (s.yr - s.yl) * (x - s.l);
                if ((__int128)num > (__int128)y * den)
                    continue;
                if (best < 0 || (__int128)num * bestDen > (__int128)bestNum * den) {
                    best = i;
                    bestNum = num;
                    bestDen = den;
                    tie = false;
                } else if ((__int128)num * bestDen == (__int128)bestNum * den)
                    tie = true;
            }
        if (best < 0) {
            cout << x << '\n';
            return 0;
        }
        if (tie)
            return 0;
        used[best] = 1;
        auto s = a[best];
        if (s.yl < s.yr) {
            x = s.l;
            y = s.yl;
        } else {
            x = s.r;
            y = s.yr;
        }
    }

    return 0;
}
