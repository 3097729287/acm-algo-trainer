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
    cin >> n;
    map<string, long long> count;
    while (n--) {
        int len;
        string s;
        cin >> len >> s;
        auto p = prefix(s);
        int period = len - p.back();
        if (len % period)
            period = len;
        count[s.substr(0, period)]++;
    }
    long long ans = 0;
    for (auto &[root, c] : count)
        ans += c * c;
    cout << ans << '\n';

    return 0;
}
