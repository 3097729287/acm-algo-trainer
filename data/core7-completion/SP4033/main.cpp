#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        sort(a.begin(), a.end());
        bool ok = true;
        for (int i = 1; i < n; i++)
            if (a[i].compare(0, a[i - 1].size(), a[i - 1]) == 0)
                ok = false;
        cout << (ok ? "YES" : "NO") << '\n';
    }

    return 0;
}
