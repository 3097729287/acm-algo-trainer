#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, a, b;
    cin >> n >> a >> b;
    __int128 C[51][51]{};
    for (int i = 0; i <= 50; i++) {
        C[i][0] = C[i][i] = 1;
        for (int j = 1; j < i; j++)
            C[i][j] = C[i - 1][j - 1] + C[i - 1][j];
    }
    __int128 ans = C[n + a][n] * C[n + b][n];
    string out;
    do {
        out += char('0' + ans % 10);
        ans /= 10;
    } while (ans);
    reverse(out.begin(), out.end());
    cout << out << '\n';

    return 0;
}
