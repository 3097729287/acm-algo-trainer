#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<int> a(n);
    int limit = 0;
    for (int &x : a) {
        cin >> x;
        limit = max(limit, x);
    }
    vector<int> frequency(limit + 1), answer(n + 2);
    for (int x : a)
        frequency[x]++;
    for (int d = 1; d <= limit; d++) {
        int c = 0;
        for (int j = d; j <= limit; j += d)
            c += frequency[j];
        if (c)
            answer[c] = max(answer[c], d);
    }
    for (int k = n - 1; k >= 1; k--)
        answer[k] = max(answer[k], answer[k + 1]);
    for (int k = 1; k <= n; k++)
        cout << answer[k] << '\n';

    return 0;
}
