#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n, k;
    cin >> n >> k;
    function<long long(int, int, int)> solve = [&](int sum, int count, int minimum) -> long long {
        if (count == 1)
            return sum >= minimum;
        long long ans = 0;
        for (int x = minimum; x <= sum / count; x++)
            ans += solve(sum - x, count - 1, x);
        return ans;
    };
    cout << solve(n, k, 1) << '\n';

    return 0;
}
