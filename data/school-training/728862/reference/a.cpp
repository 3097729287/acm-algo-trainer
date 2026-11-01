#include <bits/stdc++.h>
using namespace std;

bool distinctDigits(int year) {
    bool seen[10] = {};
    while (year > 0) {
        int digit = year % 10;
        if (seen[digit]) return false;
        seen[digit] = true;
        year /= 10;
    }
    return true;
}

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    int y;
    cin >> y;
    // 从下一年开始，首个合法年份就是最小答案。
    do { ++y; } while (!distinctDigits(y));
    cout << y << '\n';
}
