#include <bits/stdc++.h>
using namespace std;

struct Node {
    array<int, 26> child = {};
    bool end = false;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<string> words(n);
    vector<Node> trie(1);
    for (auto &s : words) {
        cin >> s;
        int v = 0;
        for (char c : s) {
            int b = c - 'a';
            if (!trie[v].child[b]) {
                trie[v].child[b] = trie.size();
                trie.push_back(Node());
            }
            v = trie[v].child[b];
        }
        trie[v].end = true;
    }
    vector<string> ans;
    for (auto &s : words) {
        bool edge[26][26] = {};
        bool ok = true;
        int v = 0;
        for (char c : s) {
            if (trie[v].end) {
                ok = false;
                break;
            }
            int x = c - 'a';
            for (int y = 0; y < 26; y++)
                if (y != x && trie[v].child[y])
                    edge[x][y] = true;
            v = trie[v].child[x];
        }
        int in[26] = {};
        for (int x = 0; x < 26; x++)
            for (int y = 0; y < 26; y++)
                in[y] += edge[x][y];
        queue<int> q;
        for (int x = 0; x < 26; x++)
            if (!in[x])
                q.push(x);
        int count = 0;
        while (!q.empty()) {
            int x = q.front();
            q.pop();
            count++;
            for (int y = 0; y < 26; y++)
                if (edge[x][y] && --in[y] == 0)
                    q.push(y);
        }
        if (ok && count == 26)
            ans.push_back(s);
    }
    cout << ans.size() << '\n';
    for (auto &s : ans)
        cout << s << '\n';

    return 0;
}
