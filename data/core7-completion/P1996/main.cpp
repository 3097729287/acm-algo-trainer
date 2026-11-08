#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    long long m;
    cin >> n >> m;
    vector<int> a(n);
    iota(a.begin(), a.end(), 1);
    long long p = 0;
    while (!a.empty()) {
        p = (p + m - 1) % a.size();
        cout << a[p] << (a.size() == 1 ? '\n' : ' ');
        a.erase(a.begin() + p);
    }

    return 0;
}
