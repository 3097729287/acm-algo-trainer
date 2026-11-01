#include <bits/stdc++.h>
using namespace std;
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int t;
    cin >> t;
    while (t--) {
        int x, y, z;
        cin >> x >> y >> z;
        char move;
        // 始终克制 Alice 出现最多的手势，赢局数便不会小于输局数。
        if (x >= y && x >= z) move = 'P';
        else if (y >= z) move = 'R';
        else move = 'S';
        cout << string(x + y + z, move) << '\n';
    }
}
