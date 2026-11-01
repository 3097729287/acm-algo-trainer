#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int n, total = 0;
    cin >> n;
    vector<int> a(n);
    for (int &v : a) { cin >> v; total += v; }
    sort(a.begin(), a.end());
    int chosen = 0, answer = 0;
    // 固定枚数时，取最大的这些硬币能得到最大总额。
    for (int i = n - 1; i >= 0 && chosen <= total - chosen; --i) {
        chosen += a[i];
        ++answer;
    }
    cout << answer << '\n';
}
