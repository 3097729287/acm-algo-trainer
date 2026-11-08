#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, r;
    cin >> n >> r;
    vector<int> a(n);
    for (int &x : a)
        cin >> x;
    vector<int> boundary, operations;
    for (int i = 1; i < n; i++)
        if (a[i - 1] != a[i])
            boundary.push_back(i);
    for (int i : boundary)
        if (i <= n / 2)
            for (int p = i; p >= 1; p--)
                operations.push_back(p);
    for (int j = (int)boundary.size() - 1; j >= 0; j--) {
        int i = boundary[j];
        if (i > n / 2)
            for (int p = i + 1; p <= n; p++)
                operations.push_back(p);
    }
    cout << operations.size() << '\n';
    for (int p : operations)
        cout << p << ' ';
    cout << '\n';

    return 0;
}
