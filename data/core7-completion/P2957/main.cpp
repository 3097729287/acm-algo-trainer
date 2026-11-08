#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string a, b;
    cin >> a >> b;
    int ans = 0;
    for (int len = 1; len <= (int)min(a.size(), b.size()); len++)
        if (a.compare(a.size() - len, len, b, 0, len) == 0 ||
            b.compare(b.size() - len, len, a, 0, len) == 0)
            ans = len;
    cout << ans << '\n';

    return 0;
}
