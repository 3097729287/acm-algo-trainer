#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> p(n);
    int fixed = -1;
    for (int i = 0; i < n; i++) {
        cin >> p[i];
        p[i]--;
        if (p[i] == i)
            fixed = i;
    }
    if (fixed >= 0) {
        cout << "YES\n";
        for (int i = 0; i < n; i++)
            if (i != fixed)
                cout << fixed + 1 << ' ' << i + 1 << '\n';
        return 0;
    }
    vector<char> seen(n);
    vector<vector<int>> cycles;
    int center = -1;
    bool ok = true;
    for (int i = 0; i < n; i++)
        if (!seen[i]) {
            vector<int> c;
            for (int v = i; !seen[v]; v = p[v]) {
                seen[v] = 1;
                c.push_back(v);
            }
            if (c.size() % 2)
                ok = false;
            if (c.size() == 2)
                center = cycles.size();
            cycles.push_back(c);
        }
    if (!ok || center < 0) {
        cout << "NO\n";
        return 0;
    }
    int a = cycles[center][0], b = cycles[center][1];
    cout << "YES\n" << a + 1 << ' ' << b + 1 << '\n';
    for (int j = 0; j < (int)cycles.size(); j++)
        if (j != center)
            for (int i = 0; i < (int)cycles[j].size(); i++)
                cout << cycles[j][i] + 1 << ' ' << (i % 2 ? b : a) + 1 << '\n';

    return 0;
}
