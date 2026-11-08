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
    string result;
    while (n--) {
        string word;
        cin >> word;
        if (result.empty()) {
            result = word;
            continue;
        }
        string probe = word + '#' + result.substr(result.size() - min(result.size(), word.size()));
        int overlap = prefix(probe).back();
        result += word.substr(overlap);
    }
    cout << result << '\n';

    return 0;
}
