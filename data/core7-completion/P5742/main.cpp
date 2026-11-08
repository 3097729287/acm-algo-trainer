#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    while (n--) {
        int id, a, b;
        cin >> id >> a >> b;
        cout << ((a + b > 140 && 7 * a + 3 * b >= 800) ? "Excellent" : "Not excellent") << '\n';
    }

    return 0;
}
