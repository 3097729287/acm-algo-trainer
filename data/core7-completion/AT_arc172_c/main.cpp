#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    auto sign = [](int x) { return (x > 0) - (x < 0); };
    int first = s[0] == 'A' ? 1 : -1, difference = 0, ans = 1;
    for (int i = 1; i < n; i++) {
        int v = s[i] == 'A' ? 1 : -1;
        if (sign(difference + first) != sign(difference + v))
            ans++;
        difference += v;
    }
    cout << ans << '\n';

    return 0;
}
