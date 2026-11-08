#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int m, n;
    cin >> m >> n;
    queue<int> q;
    unordered_set<int> memory;
    int ans = 0;
    while (n--) {
        int x;
        cin >> x;
        if (memory.count(x))
            continue;
        ans++;
        if (!m)
            continue;
        if ((int)q.size() == m) {
            memory.erase(q.front());
            q.pop();
        }
        q.push(x);
        memory.insert(x);
    }
    cout << ans << '\n';

    return 0;
}
