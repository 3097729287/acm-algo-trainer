#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> next(n + 1), previous(n + 1);
    bool ok = true;
    while (m--) {
        int a, b;
        cin >> a >> b;
        if (a == b || (next[a] && next[a] != b) || (previous[b] && previous[b] != a))
            ok = false;
        else {
            next[a] = b;
            previous[b] = a;
        }
    }
    int chains = 0, visited = 0;
    for (int i = 1; i <= n; i++)
        if (!previous[i]) {
            chains++;
            for (int v = i; v; v = next[v])
                visited++;
        }
    if (!ok || visited != n) {
        cout << 0 << '\n';
        return 0;
    }
    long long ans = 1;
    for (int i = 1; i <= chains; i++)
        ans = ans * i % 1000000007;
    cout << ans << '\n';

    return 0;
}
