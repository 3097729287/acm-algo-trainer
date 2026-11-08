#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long mod = 998244353;
    vector<long long> a(n + 1), p(n + 1), f(n + 1), g(n + 1), allf, allg;
    for (int i = 1; i <= n; i++) {
        cin >> a[i];
        p[i] = 10;
        for (long long x = a[i]; x >= 10; x /= 10)
            p[i] = p[i] * 10 % mod;
        f[i] = a[i] % mod;
        g[i] = p[i];
    }
    vector<int> parent(n + 1);
    for (int i = 2; i <= n; i++)
        cin >> parent[i];
    for (int v = n; v >= 2; v--) {
        int u = parent[v];
        f[u] = (f[u] + f[v] + a[u] * g[v]) % mod;
        g[u] = (g[u] + p[u] * g[v]) % mod;
    }
    allf = f;
    allg = g;
    long long ans = allf[1];
    for (int v = 2; v <= n; v++) {
        int u = parent[v];
        long long outsideF = (allf[u] - f[v] - a[u] * g[v] % mod + 2 * mod) % mod,
                  outsideG = (allg[u] - p[u] * g[v] % mod + mod) % mod;
        allf[v] = (f[v] + outsideF + a[v] * outsideG) % mod;
        allg[v] = (g[v] + p[v] * outsideG) % mod;
        ans = (ans + allf[v]) % mod;
    }
    cout << ans << '\n';

    return 0;
}
