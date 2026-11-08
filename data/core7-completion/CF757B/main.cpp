#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int limit = 1;
    for (int &x : a) {
        cin >> x;
        limit = max(limit, x);
    }
    vector<int> freq(limit + 1);
    for (int x : a)
        freq[x]++;
    vector<char> composite(limit + 1);
    int ans = 1;
    for (int p = 2; p <= limit; p++)
        if (!composite[p]) {
            int total = 0;
            for (int j = p; j <= limit; j += p) {
                total += freq[j];
                if (j > p)
                    composite[j] = 1;
            }
            ans = max(ans, total);
        }
    cout << ans << '\n';

    return 0;
}
