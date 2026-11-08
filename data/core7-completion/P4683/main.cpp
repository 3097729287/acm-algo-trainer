#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    struct Node {
        array<int, 26> next{};
        bool terminal = false;
        int height = 0;
    };
    vector<Node> trie(1);
    while (n--) {
        string s;
        cin >> s;
        int v = 0;
        for (char c : s) {
            int x = c - 'a';
            if (!trie[v].next[x]) {
                trie[v].next[x] = trie.size();
                trie.emplace_back();
            }
            v = trie[v].next[x];
        }
        trie[v].terminal = true;
    }
    for (int v = (int)trie.size() - 1; v >= 0; v--)
        for (int u : trie[v].next)
            if (u)
                trie[v].height = max(trie[v].height, trie[u].height + 1);
    string ops;
    function<void(int)> dfs = [&](int v) {
        if (trie[v].terminal)
            ops += 'P';
        int last = -1;
        for (int c = 0; c < 26; c++)
            if (trie[v].next[c] &&
                (last < 0 || trie[trie[v].next[c]].height > trie[trie[v].next[last]].height))
                last = c;
        for (int c = 0; c < 26; c++)
            if (trie[v].next[c] && c != last) {
                ops += char('a' + c);
                dfs(trie[v].next[c]);
                ops += '-';
            }
        if (last >= 0) {
            ops += char('a' + last);
            dfs(trie[v].next[last]);
            ops += '-';
        }
    };
    dfs(0);
    while (!ops.empty() && ops.back() == '-')
        ops.pop_back();
    cout << ops.size() << '\n';
    for (char c : ops)
        cout << c << '\n';

    return 0;
}
