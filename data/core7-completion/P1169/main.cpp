#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, m;
    cin >> n >> m;
    vector<vector<int>> a(n, vector<int>(m));
    for (int i = 0; i < n; i++)
        for (int j = 0; j < m; j++) {
            cin >> a[i][j];
            a[i][j] ^= (i + j) & 1;
        }
    long long square = 0, rectangle = 0;
    for (int color = 0; color < 2; color++) {
        vector<int> h(m + 1);
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < m; j++)
                h[j] = a[i][j] == color ? h[j] + 1 : 0;
            vector<int> st;
            for (int j = 0; j <= m; j++) {
                while (!st.empty() && h[st.back()] > h[j]) {
                    int height = h[st.back()];
                    st.pop_back();
                    int width = j - (st.empty() ? -1 : st.back()) - 1;
                    rectangle = max(rectangle, 1LL * height * width);
                    long long side = min(height, width);
                    square = max(square, side * side);
                }
                st.push_back(j);
            }
        }
    }
    cout << square << '\n' << rectangle << '\n';

    return 0;
}
