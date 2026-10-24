#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, k;
    cin >> n >> k;
    vector<int> a(n);
    int answer = 0;
    for (int &v : a) {
        cin >> v;
        if (v == k) ++answer;  // 折点单独计数，避免相邻线段重复算它。
    }
    for (int i = 0; i + 1 < n; ++i) {
        // 两端严格分居水平线两侧，才有一个内部交点。
        if (min(a[i], a[i + 1]) < k && k < max(a[i], a[i + 1]))
            ++answer;
    }
    cout << answer << '\n';
}
