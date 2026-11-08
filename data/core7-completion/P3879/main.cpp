#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    unordered_map<string, vector<int>> index;
    for (int article = 1; article <= n; article++) {
        int count;
        cin >> count;
        while (count--) {
            string s;
            cin >> s;
            auto &v = index[s];
            if (v.empty() || v.back() != article)
                v.push_back(article);
        }
    }
    int q;
    cin >> q;
    while (q--) {
        string s;
        cin >> s;
        auto it = index.find(s);
        if (it != index.end())
            for (int article : it->second)
                cout << article << ' ';
        cout << '\n';
    }

    return 0;
}
