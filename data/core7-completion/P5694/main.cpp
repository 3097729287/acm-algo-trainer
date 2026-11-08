#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int A, B, C, D;
    cin >> A >> B >> C >> D;
    const int P = 11380;
    int S = (A + 1) * (B + 1) * (C + 1);
    vector<vector<int>> f(D + 1, vector<int>(S));
    auto id = [&](int a, int b, int c) { return (a * (B + 1) + b) * (C + 1) + c; };
    for (int d = 0; d <= D; d++)
        f[d][0] = 1;
    for (int d = 1; d <= D; d++)
        for (int a = 0; a <= A; a++)
            for (int b = 0; b <= B; b++)
                for (int c = 0; c <= C; c++) {
                    if (!a && !b && !c)
                        continue;
                    long long ans = 0;
                    if (a)
                        for (int x = 0; x < a; x++)
                            for (int y = 0; y <= b; y++)
                                for (int z = 0; z <= c; z++)
                                    ans = (ans + 1LL * f[d - 1][id(x, y, z)] *
                                                     f[d][id(a - 1 - x, b - y, c - z)]) %
                                          P;
                    if (b)
                        for (int y = 0; y < b; y++)
                            for (int z = 0; z <= c; z++)
                                ans = (ans + 1LL * f[d - 1][id(0, y, z)] *
                                                 f[d][id(a, b - 1 - y, c - z)]) %
                                      P;
                    if (c)
                        for (int z = 0; z < c; z++)
                            ans =
                                (ans + 1LL * f[d - 1][id(0, 0, z)] * f[d][id(a, b, c - 1 - z)]) % P;
                    f[d][id(a, b, c)] = ans;
                }
    int ans = f[D][id(A, B, C)];
    if (D)
        ans = (ans - f[D - 1][id(A, B, C)] + P) % P;
    cout << ans << '\n';

    return 0;
}
