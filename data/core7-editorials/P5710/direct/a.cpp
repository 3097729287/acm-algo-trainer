#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int x; cin >> x;
bool a = x % 2 == 0, b = x > 4 && x <= 12;
cout << (a&&b) << ' ' << (a||b) << ' ' << (a!=b) << ' ' << (!a&&!b) << '\n';
    return 0;
}
