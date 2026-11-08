#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, q;
    long long m;
    cin >> n >> m >> q;
    long long taken = 0, damage = 0, count = 0;
    bool dead = false;
    for (int i = 0; i < n; i++) {
        long long a;
        cin >> a;
        if (dead)
            continue;
        if (a < 0) {
            taken -= a;
            if (taken >= m)
                dead = true;
        } else {
            damage += a;
            count++;
        }
    }
    while (q--) {
        long long x;
        cin >> x;
        cout << (damage + count * x >= m ? "Yes" : dead ? "No" : "Tie") << '\n';
    }

    return 0;
}
