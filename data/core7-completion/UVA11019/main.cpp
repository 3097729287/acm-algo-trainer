#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        int N, M;
        cin >> N >> M;
        vector<string> text(N);
        for (auto &s : text)
            cin >> s;
        int X, Y;
        cin >> X >> Y;
        struct Node {
            array<int, 256> next{};
            int fail = 0, id = -1;
        };
        vector<Node> ac(1);
        vector<int> pattern(X);
        int labels = 0;
        for (int i = 0; i < X; i++) {
            string s;
            cin >> s;
            int v = 0;
            for (unsigned char c : s) {
                if (!ac[v].next[c]) {
                    ac[v].next[c] = ac.size();
                    ac.emplace_back();
                }
                v = ac[v].next[c];
            }
            if (ac[v].id < 0)
                ac[v].id = labels++;
            pattern[i] = ac[v].id;
        }
        queue<int> q;
        for (int c = 0; c < 256; c++)
            if (ac[0].next[c])
                q.push(ac[0].next[c]);
        while (!q.empty()) {
            int v = q.front();
            q.pop();
            for (int c = 0; c < 256; c++) {
                int u = ac[v].next[c];
                if (u) {
                    ac[u].fail = ac[ac[v].fail].next[c];
                    q.push(u);
                } else
                    ac[v].next[c] = ac[ac[v].fail].next[c];
            }
        }
        vector<int> pi(X);
        for (int i = 1; i < X; i++) {
            int j = pi[i - 1];
            while (j && pattern[i] != pattern[j])
                j = pi[j - 1];
            if (pattern[i] == pattern[j])
                j++;
            pi[i] = j;
        }
        vector<int> vertical(M);
        long long ans = 0;
        for (auto &s : text) {
            int v = 0;
            for (int j = 0; j < M; j++) {
                v = ac[v].next[(unsigned char)s[j]];
                int id = ac[v].id, k = vertical[j];
                while (k && id != pattern[k])
                    k = pi[k - 1];
                if (id == pattern[k])
                    k++;
                if (k == X) {
                    ans++;
                    k = pi[k - 1];
                }
                vertical[j] = k;
            }
        }
        cout << ans << '\n';
    }

    return 0;
}
