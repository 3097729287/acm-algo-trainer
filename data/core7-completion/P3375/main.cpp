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

    string text, pattern;
    cin >> text >> pattern;
    auto p = prefix(pattern);
    int j = 0;
    for (int i = 0; i < (int)text.size(); i++) {
        while (j && text[i] != pattern[j])
            j = p[j - 1];
        if (text[i] == pattern[j])
            j++;
        if (j == (int)pattern.size()) {
            cout << i - j + 2 << '\n';
            j = p[j - 1];
        }
    }
    for (int x : p)
        cout << x << ' ';
    cout << '\n';

    return 0;
}
