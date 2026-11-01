#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int H, W, N, Q;
    cin >> H >> W >> N >> Q;
    vector<int> rows(N), columns(N);
    for (int i = 0; i < N; ++i) cin >> rows[i] >> columns[i];
    sort(rows.begin(), rows.end());
    sort(columns.begin(), columns.end());
    while (Q--) {
        int type, l, r;
        cin >> type >> l >> r;
        const vector<int> &v = type == 1 ? rows : columns;
        // 第一个 > r 的位置，减去第一个 >= l 的位置。
        cout << upper_bound(v.begin(), v.end(), r) - lower_bound(v.begin(), v.end(), l) << '\n';
    }
}
