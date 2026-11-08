#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    if (!(cin >> n >> m))
        return 0;
    vector<int> parent(n + 1);
    vector<char> seen(n + 1);
    int current = 1;
    seen[1] = 1;
    for (;;) {
        string token;
        if (!(cin >> token))
            return 0;
        if (token == "OK" || token == "-1")
            return 0;
        int k = stoi(token), next = 0;
        for (int i = 0; i < k; i++) {
            int v;
            cin >> v;
            if (!seen[v])
                next = v;
        }
        if (next) {
            parent[next] = current;
            seen[next] = 1;
        } else
            next = parent[current];
        if (!next)
            return 0;
        cout << next << endl;
        current = next;
    }

    return 0;
}
