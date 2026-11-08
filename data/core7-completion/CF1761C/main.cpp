#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int t;
    cin >> t;
    while (t--) {
        int n;
        cin >> n;
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        for (int target = 0; target < n; target++) {
            vector<char> seen(n);
            vector<int> st = {target};
            seen[target] = 1;
            while (!st.empty()) {
                int v = st.back();
                st.pop_back();
                for (int u = 0; u < n; u++)
                    if (a[u][v] == '1' && !seen[u]) {
                        seen[u] = 1;
                        st.push_back(u);
                    }
            }
            cout << count(seen.begin(), seen.end(), 1);
            for (int u = 0; u < n; u++)
                if (seen[u])
                    cout << ' ' << u + 1;
            cout << '\n';
        }
    }

    return 0;
}
