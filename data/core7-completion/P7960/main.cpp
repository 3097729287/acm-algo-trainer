#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    vector<int> queries(T);
    int maximum = 0;
    for (int &x : queries) {
        cin >> x;
        maximum = max(maximum, x);
    }
    int limit = max(128, maximum + 128);
    vector<bool> bad;
    vector<int> next;
    for (;;) {
        bad.assign(limit + 1, false);
        for (int i = 1; i <= limit; i++)
            if (!bad[i]) {
                int x = i;
                bool seven = false;
                while (x) {
                    if (x % 10 == 7)
                        seven = true;
                    x /= 10;
                }
                if (seven)
                    for (int j = i; j <= limit; j += i)
                        bad[j] = true;
            }
        int last = 0;
        next.assign(limit + 1, 0);
        for (int i = limit; i >= 1; i--) {
            next[i] = last;
            if (!bad[i])
                last = i;
        }
        if (next[maximum])
            break;
        limit *= 2;
    }
    for (int x : queries)
        cout << (bad[x] ? -1 : next[x]) << '\n';

    return 0;
}
