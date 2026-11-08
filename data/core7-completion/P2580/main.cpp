#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    set<string> names, called;
    while (n--) {
        string s;
        cin >> s;
        names.insert(s);
    }
    int m;
    cin >> m;
    while (m--) {
        string s;
        cin >> s;
        if (!names.count(s))
            cout << "WRONG\n";
        else
            cout << (called.insert(s).second ? "OK" : "REPEAT") << '\n';
    }

    return 0;
}
