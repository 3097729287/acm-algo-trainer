#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n;
        cin >> n;
        vector<array<double, 3>> a(n);
        for (auto &v : a)
            cin >> v[0] >> v[1] >> v[2];
        auto value = [&](double x) {
            double answer = -1e100;
            for (auto v : a)
                answer = max(answer, (v[0] * x + v[1]) * x + v[2]);
            return answer;
        };
        double l = 0, r = 1000;
        for (int i = 0; i < 120; i++) {
            double x = (2 * l + r) / 3, y = (l + 2 * r) / 3;
            if (value(x) < value(y))
                r = y;
            else
                l = x;
        }
        cout << fixed << setprecision(4) << value((l + r) / 2) << '\n';
    }

    return 0;
}
