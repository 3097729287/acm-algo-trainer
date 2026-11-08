#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, r, test = 0;
    while (cin >> n >> r && (n || r)) {
        vector<double> p(n), numerator(n);
        for (auto &x : p)
            cin >> x;
        double denominator = 0;
        for (int mask = 0; mask < (1 << n); mask++)
            if (__builtin_popcount((unsigned)mask) == r) {
                double probability = 1;
                for (int i = 0; i < n; i++)
                    probability *= ((mask >> i) & 1) ? p[i] : 1 - p[i];
                denominator += probability;
                for (int i = 0; i < n; i++)
                    if ((mask >> i) & 1)
                        numerator[i] += probability;
            }
        cout << "Case " << ++test << ":\n";
        for (double x : numerator)
            cout << fixed << setprecision(6) << x / denominator << '\n';
    }

    return 0;
}
