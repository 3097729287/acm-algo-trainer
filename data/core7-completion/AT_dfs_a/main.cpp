#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int h, w;
    cin >> h >> w;
    vector<string> a(h);
    int start = -1, goal = -1;
    for (int i = 0; i < h; i++) {
        cin >> a[i];
        for (int j = 0; j < w; j++) {
            if (a[i][j] == 's')
                start = i * w + j;
            if (a[i][j] == 'g')
                goal = i * w + j;
        }
    }
    vector<char> seen(h * w);
    vector<int> st = {start};
    seen[start] = 1;
    int dx[] = {1, -1, 0, 0}, dy[] = {0, 0, 1, -1};
    while (!st.empty()) {
        int v = st.back();
        st.pop_back();
        int x = v / w, y = v % w;
        for (int k = 0; k < 4; k++) {
            int u = x + dx[k], v = y + dy[k];
            if (u >= 0 && u < h && v >= 0 && v < w && a[u][v] != '#' && !seen[u * w + v]) {
                seen[u * w + v] = 1;
                st.push_back(u * w + v);
            }
        }
    }
    cout << (seen[goal] ? "Yes" : "No") << '\n';

    return 0;
}
