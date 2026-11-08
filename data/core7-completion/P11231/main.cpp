#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> count(100001);
    int ans = 0;
    while (n--) {
        int x;
        cin >> x;
        ans = max(ans, ++count[x]);
    }
    cout << ans << '\n';

    return 0;
}
