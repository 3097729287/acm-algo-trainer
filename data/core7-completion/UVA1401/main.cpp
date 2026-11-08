#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    int caseNo = 0;
    while (cin >> s) {
        int count;
        cin >> count;
        struct Node {
            array<int, 26> next{};
            bool terminal = false;
        };
        vector<Node> trie(1);
        int maxLength = 0;
        while (count--) {
            string word;
            cin >> word;
            maxLength = max(maxLength, (int)word.size());
            int v = 0;
            for (char c : word) {
                int x = c - 'a';
                if (!trie[v].next[x]) {
                    trie[v].next[x] = trie.size();
                    trie.emplace_back();
                }
                v = trie[v].next[x];
            }
            trie[v].terminal = true;
        }
        const int P = 20071027;
        int n = s.size();
        vector<int> dp(n + 1);
        dp[n] = 1;
        for (int i = n - 1; i >= 0; i--) {
            int v = 0;
            for (int j = i; j < n && j < i + maxLength; j++) {
                v = trie[v].next[s[j] - 'a'];
                if (!v)
                    break;
                if (trie[v].terminal) {
                    dp[i] += dp[j + 1];
                    if (dp[i] >= P)
                        dp[i] -= P;
                }
            }
        }
        cout << "Case " << ++caseNo << ": " << dp[0] << '\n';
    }

    return 0;
}
