#include <bits/stdc++.h>
using namespace std;
int main() {
    int t;
    cin >> t;
    while (t--) {
        int n, m;
        string p, q;
        cin >> n >> m >> p >> q;
        bool ok = true;
        for (char c : q) {
            size_t pos = p.find(c);
            if (pos == string::npos) { ok = false; break; }
            p.erase(pos, 1);
        }
        sort(p.begin(), p.end());
        cout << (ok && p == "isx" ? "YES" : "NO") << '\n';
    }
}
