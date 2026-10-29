#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
char c; cin >> c;
for (int i = 0; i < 3; ++i)
    cout << string(2 - i, ' ') << string(2 * i + 1, c) << '\n';
    return 0;
}
