#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        long long g, l;
        cin >> g >> l;
        if (l % g)
            cout << -1 << '\n';
        else
            cout << g << ' ' << l << '\n';
    }

    return 0;
}
