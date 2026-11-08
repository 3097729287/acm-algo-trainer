#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n, k;
        long long a, b;
        cin >> n >> k >> a >> b;
        if (k > n) {
            cout << 0 << '\n';
            for (int i = 0; i < n; i++)
                cout << (i % 2 ? 'b' : 'a');
            cout << '\n';
            continue;
        }
        long long W = n - k + 1, width = k - 1, best = LLONG_MAX, count = 0;
        for (long long c : {0LL, W / width, (W + width - 1) / width}) {
            long long value = c * a + max(0LL, W - c * width) * b;
            if (value < best) {
                best = value;
                count = c;
            }
        }
        string s(n, 'a');
        for (int i = 1; i < n; i++) {
            bool accent = i % width == 0 && i / width <= count;
            s[i] = accent ? s[i - 1] : (s[i - 1] == 'a' ? 'b' : 'a');
        }
        cout << best << '\n' << s << '\n';
    }

    return 0;
}
