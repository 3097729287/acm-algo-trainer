#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int n;
        long long M;
        cin >> n >> M;
        vector<long long> a(n - 1), b(n);
        for (auto &x : a)
            cin >> x;
        int k = 0;
        while (a[k] == a[k + 1])
            k++;
        b[k + 1] = gcd(a[k], a[k + 1]);
        for (int i = k; i >= 0; i--)
            b[i] = a[i] / b[i + 1];
        for (int i = k + 1; i < n - 1; i++)
            b[i + 1] = a[i] / b[i];
        bool ok = all_of(b.begin(), b.end(), [&](long long x) { return x <= M; });
        if (!ok)
            cout << -1 << '\n';
        else
            for (int i = 0; i < n; i++)
                cout << b[i] << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
