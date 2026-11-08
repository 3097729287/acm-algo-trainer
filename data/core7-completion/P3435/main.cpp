#include <bits/stdc++.h>
using namespace std;

vector<int> prefix(const string &s) {
    vector<int> p(s.size());
    for (int i = 1; i < (int)s.size(); i++) {
        int j = p[i - 1];
        while (j && s[i] != s[j])
            j = p[j - 1];
        if (s[i] == s[j])
            j++;
        p[i] = j;
    }
    return p;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    string s;
    cin >> n >> s;
    auto p = prefix(s);
    vector<int> shortest(n + 1);
    long long ans = 0;
    for (int len = 1; len <= n; len++) {
        int b = p[len - 1];
        if (b) {
            shortest[len] = shortest[b] ? shortest[b] : b;
            ans += len - shortest[len];
        }
    }
    cout << ans << '\n';

    return 0;
}
