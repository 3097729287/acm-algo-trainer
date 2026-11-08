#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    long long n, m, k;
    cin >> n >> m >> k;
    auto choose2 = [](long long x) { return x * (x - 1) / 2; };
    long long answer = 0;
    for (int direction = 0; direction < 2; direction++) {
        for (long long h = 1; h <= n; h++) {
            long long q = k / h, r = k % h;
            if (q > m || (r && q == m))
                continue;
            answer = max(answer, choose2(h) * choose2(q) + q * choose2(r));
        }
        swap(n, m);
    }
    cout << answer << '\n';

    return 0;
}
