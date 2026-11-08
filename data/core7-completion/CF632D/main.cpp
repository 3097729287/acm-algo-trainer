#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<int> a(n), cnt(m + 1), score(m + 1);
    for (int &x : a) {
        cin >> x;
        if (x <= m)
            cnt[x]++;
    }
    for (int v = 1; v <= m; v++)
        if (cnt[v])
            for (int L = v; L <= m; L += v)
                score[L] += cnt[v];
    int best = 1;
    for (int L = 2; L <= m; L++)
        if (score[L] > score[best])
            best = L;
    vector<int> indices;
    long long L = 1;
    for (int i = 0; i < n; i++)
        if (best % a[i] == 0) {
            indices.push_back(i + 1);
            L = L / gcd(L, (long long)a[i]) * a[i];
        }
    cout << L << ' ' << indices.size() << '\n';
    for (int i = 0; i < (int)indices.size(); i++)
        cout << indices[i] << (i + 1 == (int)indices.size() ? '\n' : ' ');
    if (indices.empty())
        cout << '\n';

    return 0;
}
