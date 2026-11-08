#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, caseNo = 0;
    while (cin >> n && n) {
        vector<string> a(n);
        for (auto &s : a)
            cin >> s;
        sort(a.begin(), a.end());
        long long same = 0;
        for (int l = 0; l < n;) {
            int r = l + 1;
            while (r < n && a[r] == a[l])
                r++;
            same += 1LL * (r - l) * (r - l - 1) / 2;
            l = r;
        }
        vector<pair<int, int>> st;
        long long ending = 0, totalLcp = 0;
        for (int i = 1; i < n; i++) {
            int h = 0;
            while (h < (int)min(a[i].size(), a[i - 1].size()) && a[i][h] == a[i - 1][h])
                h++;
            int count = 1;
            while (!st.empty() && st.back().first >= h) {
                ending -= 1LL * st.back().first * st.back().second;
                count += st.back().second;
                st.pop_back();
            }
            st.push_back({h, count});
            ending += 1LL * h * count;
            totalLcp += ending;
        }
        cout << "Case " << ++caseNo << ": " << 1LL * n * (n - 1) / 2 + 2 * totalLcp + same << '\n';
    }

    return 0;
}
