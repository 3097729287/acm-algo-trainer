#include <bits/stdc++.h>
using namespace std;

vector<int> zfunction(const string &s) {
    int n = s.size();
    vector<int> z(n);
    z[0] = n;
    for (int i = 1, l = 0, r = 0; i < n; i++) {
        if (i <= r)
            z[i] = min(r - i + 1, z[i - l]);
        while (i + z[i] < n && s[z[i]] == s[i + z[i]])
            z[i]++;
        if (i + z[i] - 1 > r) {
            l = i;
            r = i + z[i] - 1;
        }
    }
    return z;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    string s;
    cin >> n >> k >> s;
    auto z = zfunction(s);
    z.push_back(0);
    vector<int> diff(n + 2);
    for (int p = 1; 1LL * k * p <= n; p++)
        if (z[p] >= (k - 1) * p) {
            int l = k * p, r = min(n, l + min(p, z[l]));
            diff[l]++;
            diff[r + 1]--;
        }
    int active = 0;
    for (int i = 1; i <= n; i++) {
        active += diff[i];
        cout << (active ? '1' : '0');
    }
    cout << '\n';

    return 0;
}
