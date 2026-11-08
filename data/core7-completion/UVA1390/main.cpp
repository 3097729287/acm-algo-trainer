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

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    while (cin >> n >> m) {
        DSU d(n);
        while (m--) {
            int a, b;
            cin >> a >> b;
            d.join(a - 1, b - 1);
        }
        vector<int> state;
        for (int i = 0; i < n; i++)
            if (d.find(i) == i)
                state.push_back(d.size[i]);
        sort(state.begin(), state.end());
        map<vector<int>, double> memo;
        function<double(vector<int>)> solve = [&](vector<int> s) -> double {
            if (s.size() == 1)
                return 0;
            auto found = memo.find(s);
            if (found != memo.end())
                return found->second;
            double cross = 0, numerator = 1.0 * n * (n - 1) / 2;
            for (int i = 0; i < (int)s.size(); i++)
                for (int j = i + 1; j < (int)s.size(); j++) {
                    double weight = s[i] * s[j];
                    cross += weight;
                    vector<int> next;
                    for (int k = 0; k < (int)s.size(); k++)
                        if (k != i && k != j)
                            next.push_back(s[k]);
                    next.push_back(s[i] + s[j]);
                    sort(next.begin(), next.end());
                    numerator += weight * solve(next);
                }
            return memo[s] = numerator / cross;
        };
        cout << fixed << setprecision(9) << solve(state) << '\n';
    }

    return 0;
}
