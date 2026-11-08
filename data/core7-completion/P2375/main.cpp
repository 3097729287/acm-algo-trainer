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

    int tests;
    cin >> tests;
    while (tests--) {
        string s;
        cin >> s;
        int n = s.size();
        auto p = prefix(s);
        vector<int> count(n + 1);
        for (int len = 1; len <= n; len++)
            count[len] = count[p[len - 1]] + 1;
        long long ans = 1;
        int j = 0;
        for (int len = 2; len <= n; len++) {
            while (j && s[len - 1] != s[j])
                j = p[j - 1];
            if (s[len - 1] == s[j])
                j++;
            while (2 * j > len)
                j = p[j - 1];
            ans = ans * (count[j] + 1) % 1000000007;
        }
        cout << ans << '\n';
    }

    return 0;
}
