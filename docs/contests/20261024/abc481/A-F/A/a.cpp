#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int a, b;
    cin >> a >> b;
    // 和在 2 到 18 之间，只需判断是否达到 10。
    cout << (a + b >= 10 ? 2 : 1) << '\n';
}
