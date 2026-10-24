#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    if (n <= 4) {
        cout << -1 << '\n';
        return 0;
    }
    vector<int> a;
    for (int v = 1; v <= n; v += 2) a.push_back(v);
    for (int v = 2; v <= n; v += 2) a.push_back(v);
    for (int i = 0; i < n; ++i) cout << a[i] << " \n"[i == n - 1];
    // 第二行循环左移一位，使同列两数也是环上的相邻数。
    for (int i = 0; i < n; ++i) cout << a[(i + 1) % n] << " \n"[i == n - 1];
}
