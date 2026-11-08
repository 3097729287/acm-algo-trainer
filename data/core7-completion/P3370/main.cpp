#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_set<string> words;
    words.reserve(2 * n);
    while (n--) {
        string s;
        cin >> s;
        words.insert(s);
    }
    cout << words.size() << '\n';

    return 0;
}
