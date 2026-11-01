#include <bits/stdc++.h>
using namespace std;

struct Edge {
    int u, v, w;
};

pair<int, int> key(int u, int v) {
    if (u > v) swap(u, v);
    return {u, v};
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int T;
    cin >> T;
    while (T--) {
        int n;
        cin >> n;
        vector<Edge> edges(n - 1);
        vector<int> first(n + 1, -1), second(n + 1, -1);
        set<pair<int, int>> used;
        for (int i = 0; i < n - 1; ++i) {
            Edge &e = edges[i];
            cin >> e.u >> e.v >> e.w;
            used.insert(key(e.u, e.v));
            for (int v : {e.u, e.v}) {
                // 每个顶点保存最轻和次轻的两条边的编号。
                if (first[v] == -1 || e.w < edges[first[v]].w) {
                    second[v] = first[v];
                    first[v] = i;
                } else if (second[v] == -1 || e.w < edges[second[v]].w) {
                    second[v] = i;
                }
            }
        }
        vector<Edge> added;
        bool ok = true;
        for (int i = 0; i < n - 1; ++i) {
            const Edge &e = edges[i];
            int center = e.u, end = e.v;
            int j = (first[center] == i ? second[center] : first[center]);
            if (j == -1 || edges[j].w > e.w) {
                center = e.v;
                end = e.u;
                j = (first[center] == i ? second[center] : first[center]);
            }
            if (j == -1 || edges[j].w > e.w) {
                ok = false;
                break;
            }
            int other = edges[j].u + edges[j].v - center;
            pair<int, int> p = key(end, other);
            // 距离为二的两个端点一定不是原树边；重复方案只留一次。
            if (used.insert(p).second) added.push_back({p.first, p.second, e.w + 1});
        }
        if (!ok) {
            cout << "No\n";
            continue;
        }
        // 补足 n-1 条。已有边对不足 2n，扫描到足额只需 O(n) 次候选。
        for (int u = 1; u <= n && static_cast<int>(added.size()) < n - 1; ++u) {
            for (int v = u + 1; v <= n && static_cast<int>(added.size()) < n - 1; ++v) {
                if (used.insert({u, v}).second) added.push_back({u, v, 2000000000});
            }
        }
        cout << "Yes\n";
        for (const Edge &e : added) cout << e.u << ' ' << e.v << ' ' << e.w << '\n';
    }
}
