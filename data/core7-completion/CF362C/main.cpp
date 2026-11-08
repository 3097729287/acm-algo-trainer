#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<unsigned short> pref((n + 1) * n);
    for (int i = 0; i < n; i++)
        for (int v = 0; v < n; v++)
            pref[(i + 1) * n + v] = pref[i * n + v] + (a[i] <= v);
    long long inversions = 0, ways = 0;
    int best = -1;
    for (int i = 0; i < n; i++)
        for (int j = i + 1; j < n; j++)
            if (a[i] > a[j]) {
                inversions++;
                int high = a[i] - 1, low = a[j];
                int inside = pref[j * n + high] - pref[(i + 1) * n + high] - pref[j * n + low] +
                             pref[(i + 1) * n + low];
                int reduction = 1 + 2 * inside;
                if (reduction > best) {
                    best = reduction;
                    ways = 1;
                } else if (reduction == best)
                    ways++;
            }
    cout << inversions - best << ' ' << ways << '\n';

    return 0;
}
