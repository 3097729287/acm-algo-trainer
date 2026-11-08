#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    string name;
    int x = 0, y = 0, z = 0, best = -1;
    while (n--) {
        string s;
        int a, b, c;
        cin >> s >> a >> b >> c;
        if (a + b + c > best) {
            best = a + b + c;
            name = s;
            x = a;
            y = b;
            z = c;
        }
    }
    cout << name << ' ' << x << ' ' << y << ' ' << z << '\n';

    return 0;
}
