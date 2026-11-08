#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> parent(n + 1), degree(n + 1), head(n + 1), next(n + 1), previous(n + 1),
        count(n + 1);
    head[0] = 1;
    count[0] = 1;
    auto insert = [&](int v, int d) {
        degree[v] = d;
        previous[v] = 0;
        next[v] = head[d];
        if (head[d])
            previous[head[d]] = v;
        head[d] = v;
        count[d]++;
    };
    auto increase = [&](int v) {
        int d = degree[v], p = previous[v], q = next[v];
        if (p)
            next[p] = q;
        else
            head[d] = q;
        if (q)
            previous[q] = p;
        count[d]--;
        insert(v, d + 1);
    };
    auto adjacent = [&](int a, int b) { return parent[a] == b || parent[b] == a; };
    int top = 1, second = 0, previousUnique = 0, cachedSecond = 0, witness = 0;
    string output;
    output.reserve(8LL * n);
    for (int v = 2; v <= n; v++) {
        int p;
        cin >> p;
        parent[v] = p;
        increase(p);
        insert(v, 1);
        if (p != top) {
            if (degree[p] > degree[top]) {
                second = top;
                top = p;
            } else if (p != second && degree[p] > degree[second])
                second = p;
        }
        if (!second || degree[v] > degree[second])
            second = v;
        int D = degree[top], S = degree[second], answer;
        if (D == S) {
            answer = 2 * D - 1 - (count[D] == 2 && adjacent(top, second));
            previousUnique = 0;
        } else {
            if (previousUnique != top) {
                witness = 0;
                for (int u = head[S]; u; u = next[u])
                    if (!adjacent(top, u)) {
                        witness = u;
                        break;
                    }
            } else if (S != cachedSecond) {
                witness = p != top && degree[p] == S && !adjacent(top, p) ? p : 0;
            } else if (!witness) {
                if (p != top && degree[p] == S && !adjacent(top, p))
                    witness = p;
                if (S == 1 && !adjacent(top, v))
                    witness = v;
            }
            answer = D + S - 1 - (witness == 0);
            previousUnique = top;
            cachedSecond = S;
        }
        output += to_string(answer);
        output += v == n ? '\n' : ' ';
    }
    cout << output;

    return 0;
}
