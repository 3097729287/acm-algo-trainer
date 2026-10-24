#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int q;
    cin >> q;
    map<string, int> id;
    int next_id = 1;
    while (q--) {
        string s;
        cin >> s;
        // 账户从不删除，已用编号始终是从 1 开始的连续一段。
        auto it = id.find(s);
        if (it == id.end()) {
            id[s] = next_id;
            cout << next_id << '\n';
            ++next_id;
        } else {
            cout << it->second << '\n';
        }
    }
}
