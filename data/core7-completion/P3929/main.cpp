#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    while (cin >> n) {
        vector<long long> a(n);
        for (auto &x : a)
            cin >> x;
        auto ok = [&](bool firstUp) {
            vector<int> bad;
            for (int i = 0; i + 1 < n; i++) {
                bool up = ((i % 2) == 0) == firstUp;
                if (up ? a[i] > a[i + 1] : a[i] < a[i + 1])
                    bad.push_back(i);
            }
            if (bad.empty())
                return true;
            for (int p : {bad[0], bad[0] + 1}) {
                bool valid = true;
                for (int edge : bad)
                    if (edge != p - 1 && edge != p)
                        valid = false;
                if (valid)
                    return true;
            }
            return false;
        };
        cout << (ok(true) || ok(false) ? "Yes" : "No") << '\n';
    }

    return 0;
}
