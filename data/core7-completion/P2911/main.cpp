#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int a, b, c;
    cin >> a >> b >> c;
    vector<int> cnt(a + b + c + 1);
    for (int x = 1; x <= a; x++)
        for (int y = 1; y <= b; y++)
            for (int z = 1; z <= c; z++)
                cnt[x + y + z]++;
    int ans = 0;
    for (int i = 1; i < (int)cnt.size(); i++)
        if (cnt[i] > cnt[ans])
            ans = i;
    cout << ans << '\n';

    return 0;
}
