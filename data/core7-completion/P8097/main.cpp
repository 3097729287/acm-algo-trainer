#include <bits/stdc++.h>
using namespace std;

struct DSU {
    vector<int> p, size;
    explicit DSU(int n) : p(n), size(n, 1) { iota(p.begin(), p.end(), 0); }
    int find(int x) {
        while (p[x] != x) {
            p[x] = p[p[x]];
            x = p[x];
        }
        return x;
    }
    bool join(int a, int b) {
        a = find(a);
        b = find(b);
        if (a == b)
            return false;
        if (size[a] < size[b])
            swap(a, b);
        p[b] = a;
        size[a] += size[b];
        return true;
    }
};

struct Operation {
    char kind;
    int x, y = 0;
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    cin >> n >> q;
    vector<Operation> operations(q);
    vector<pair<int, int>> edges;
    vector<char> removed, active(n, 1);
    for (auto &op : operations) {
        cin >> op.kind >> op.x;
        op.x--;
        if (op.kind == 'A') {
            cin >> op.y;
            op.y--;
            edges.push_back({op.x, op.y});
            removed.push_back(0);
        } else if (op.kind == 'R')
            removed[op.x] = 1;
        else
            active[op.x] = 0;
    }
    DSU d(n);
    vector<char> relevant(n);
    vector<vector<int>> pending(n);
    vector<int> answer(n, -1);
    for (int i = 0; i < n; i++)
        pending[i] = {i};
    auto mark = [&](int root, int time) {
        root = d.find(root);
        relevant[root] = 1;
        for (int v : pending[root])
            answer[v] = time;
        pending[root].clear();
    };
    auto unite = [&](int a, int b, int time) {
        a = d.find(a);
        b = d.find(b);
        if (a == b)
            return;
        if (d.size[a] < d.size[b])
            swap(a, b);
        d.p[b] = a;
        d.size[a] += d.size[b];
        pending[a].insert(pending[a].end(), pending[b].begin(), pending[b].end());
        pending[b].clear();
        relevant[a] |= relevant[b];
        if (relevant[a])
            mark(a, time);
    };
    for (int i = 0; i < (int)edges.size(); i++)
        if (!removed[i])
            unite(edges[i].first, edges[i].second, q);
    for (int v = 0; v < n; v++)
        if (active[v])
            mark(v, q);
    for (int i = q - 1; i >= 0; i--) {
        auto op = operations[i];
        if (op.kind == 'D')
            mark(op.x, i);
        else if (op.kind == 'R')
            unite(edges[op.x].first, edges[op.x].second, i);
    }
    for (int x : answer)
        cout << x << '\n';

    return 0;
}
