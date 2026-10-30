#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n;
    cin >> n;
    vector<long long> a(n), b(n);
    for (auto &x : a)
        cin >> x;
    for (auto &x : b)
        cin >> x;
    sort(a.begin(), a.end());
    sort(b.begin(), b.end());
    int used = 0;
    for (long long x : a)
        if (used < n && b[used] < x)
            ++used;
    cout << n - used << '\n';
}
