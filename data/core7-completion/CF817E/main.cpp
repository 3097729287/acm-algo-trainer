#include <bits/stdc++.h>
using namespace std;

struct Node {
    int child[2] = {0, 0}, count = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int q;
    cin >> q;
    vector<Node> t(1);
    while (q--) {
        int op, x;
        cin >> op >> x;
        if (op < 3) {
            int v = 0, delta = op == 1 ? 1 : -1;
            t[v].count += delta;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if (!t[v].child[bit]) {
                    t[v].child[bit] = t.size();
                    t.push_back(Node());
                }
                v = t[v].child[bit];
                t[v].count += delta;
            }
        } else {
            int p;
            cin >> p;
            int v = 0, ans = 0;
            for (int b = 30; b >= 0; b--) {
                int bit = (x >> b) & 1;
                if ((p >> b) & 1) {
                    int same = t[v].child[bit];
                    if (same)
                        ans += t[same].count;
                    v = t[v].child[bit ^ 1];
                } else
                    v = t[v].child[bit];
                if (!v)
                    break;
            }
            cout << ans << '\n';
        }
    }

    return 0;
}
