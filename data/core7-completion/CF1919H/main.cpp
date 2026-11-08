#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    if (!(cin >> n))
        return 0;
    const long long HEAVY = 1000000000;
    auto askDistance = [&](int a, int b) {
        cout << "? 2 " << a + 1 << ' ' << b + 1 << endl;
        int result;
        if (!(cin >> result) || result < 0)
            exit(0);
        return result;
    };
    auto askDiameter = [&](const vector<long long> &weight) {
        cout << "? 1";
        for (long long x : weight)
            cout << ' ' << x;
        cout << endl;
        long long result;
        if (!(cin >> result) || result < 0)
            exit(0);
        return result;
    };
    vector<int> level(n - 1, -1);
    for (int edge = 1; edge < n - 1; edge++)
        level[edge] = askDistance(0, edge);
    vector<int> label(n), frontier = {0, 1};
    label[0] = label[1] = 0;
    vector<vector<int>> children(n);
    vector<pair<int, int>> answer = {{0, 1}};
    int created = 2, anchor = -1;
    for (int depth = 0; created < n; depth++) {
        int width = frontier.size(), pivot = -1;
        vector<int> nextFrontier;
        for (int edge = 1; edge < n - 1; edge++)
            if (level[edge] == depth) {
                vector<long long> weight(n - 1, 1);
                for (int i = 0; i < width; i++)
                    weight[label[frontier[i]]] =
                        1LL * n * (anchor < 0 ? min(i + 1, width - 1) : i + 1);
                if (anchor >= 0)
                    weight[anchor] = HEAVY;
                if (pivot >= 0)
                    weight[pivot] = HEAVY;
                weight[edge] = HEAVY;
                long long value = askDiameter(weight) - HEAVY;
                if (anchor >= 0 || pivot >= 0)
                    value -= HEAVY;
                int code = value / n, parentIndex = -1;
                if (anchor >= 0)
                    parentIndex = code - 1;
                else if (depth == 0) {
                    if (pivot < 0) {
                        parentIndex = 0;
                        pivot = edge;
                    } else
                        parentIndex = code == 0 ? 0 : 1;
                } else {
                    code -= width - 1;
                    if (pivot >= 0 && code == -(width - 1))
                        parentIndex = width - 2;
                    else if (code == width - 1) {
                        if (pivot < 0) {
                            parentIndex = width - 2;
                            pivot = edge;
                        } else
                            parentIndex = width - 1;
                    } else
                        parentIndex = code - 1;
                }
                if (parentIndex < 0 || parentIndex >= width)
                    return 0;
                int parent = frontier[parentIndex], v = created++;
                label[v] = edge;
                children[parent].push_back(v);
                nextFrontier.push_back(v);
                answer.push_back({parent, v});
            }
        if (created == n)
            break;
        if (nextFrontier.empty())
            return 0;
        if (anchor < 0) {
            int A = frontier[width - 2], B = frontier[width - 1];
            for (int i = 0; i < width - 2; i++)
                if (children[frontier[i]].empty()) {
                    anchor = label[frontier[i]];
                    break;
                }
            if (anchor < 0 && (children[A].empty() || children[B].empty())) {
                if (label[A] == label[B] || (children[A].empty() && children[B].empty()))
                    anchor = label[A];
                else {
                    int actualParent = askDistance(pivot, label[A]) == 0 ? A : B;
                    anchor = label[actualParent == A ? B : A];
                }
            }
            if (anchor < 0) {
                int a = -1, b = -1;
                for (int parent : frontier)
                    if (children[parent].size() >= 2) {
                        a = children[parent][0];
                        b = children[parent][1];
                        break;
                    }
                if (a < 0) {
                    a = children[A][0];
                    b = children[B][0];
                }
                vector<int> ordered;
                for (int v : nextFrontier)
                    if (v != a && v != b)
                        ordered.push_back(v);
                ordered.push_back(a);
                ordered.push_back(b);
                nextFrontier.swap(ordered);
            }
        }
        frontier.swap(nextFrontier);
    }
    cout << "!" << endl;
    for (auto [a, b] : answer)
        cout << a + 1 << ' ' << b + 1 << '\n';
    cout.flush();

    return 0;
}
