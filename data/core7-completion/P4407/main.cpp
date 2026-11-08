#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    unordered_set<string> dict;
    while (n--) {
        string s;
        cin >> s;
        dict.insert(s);
    }
    while (m--) {
        string s;
        cin >> s;
        if (dict.count(s)) {
            cout << -1 << '\n';
            continue;
        }
        unordered_set<string> found;
        auto test = [&](const string &v) {
            if (dict.count(v))
                found.insert(v);
        };
        for (int i = 0; i < (int)s.size(); i++) {
            test(s.substr(0, i) + s.substr(i + 1));
            string v = s;
            for (char c = 'a'; c <= 'z'; c++) {
                v[i] = c;
                test(v);
            }
        }
        for (int i = 0; i <= (int)s.size(); i++)
            for (char c = 'a'; c <= 'z'; c++)
                test(s.substr(0, i) + c + s.substr(i));
        cout << found.size() << '\n';
    }

    return 0;
}
