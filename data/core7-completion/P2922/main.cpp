#include <bits/stdc++.h>
using namespace std;

struct Node {
    int child[2] = {0, 0};
    int sub = 0, end = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    cin >> m >> n;
    vector<Node> t(1);
    for (int i = 0; i < m; i++) {
        int len;
        cin >> len;
        int v = 0;
        t[v].sub++;
        while (len--) {
            int b;
            cin >> b;
            if (!t[v].child[b]) {
                t[v].child[b] = t.size();
                t.push_back(Node());
            }
            v = t[v].child[b];
            t[v].sub++;
        }
        t[v].end++;
    }
    while (n--) {
        int len;
        cin >> len;
        int v = 0, ans = 0;
        bool alive = true;
        while (len--) {
            int b;
            cin >> b;
            if (alive) {
                ans += t[v].end;
                int next = t[v].child[b];
                if (!next)
                    alive = false;
                else
                    v = next;
            }
        }
        if (alive)
            ans += t[v].sub;
        cout << ans << '\n';
    }

    return 0;
}
