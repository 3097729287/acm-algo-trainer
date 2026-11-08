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

    string s, t;
    cin >> s >> t;
    auto p = prefix(t);
    string out;
    vector<int> state;
    for (char c : s) {
        int j = state.empty() ? 0 : state.back();
        while (j && c != t[j])
            j = p[j - 1];
        if (c == t[j])
            j++;
        out.push_back(c);
        state.push_back(j);
        if (j == (int)t.size()) {
            out.resize(out.size() - t.size());
            state.resize(state.size() - t.size());
        }
    }
    cout << out << '\n';

    return 0;
}
