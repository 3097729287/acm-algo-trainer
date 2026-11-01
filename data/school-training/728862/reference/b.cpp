#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int x, answer = 0;
    cin >> x;
    while (x > 0) {
        // 除以二前的余数正是当前二进制最低位。
        answer += x % 2;
        x /= 2;
    }
    cout << answer << '\n';
}
