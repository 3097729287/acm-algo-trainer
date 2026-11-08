#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    vector<pair<long long, long long>> st;
    long long ans = 0;
    auto settle = [&]() {
        auto [v, c] = st.back();
        st.pop_back();
        if (v == 0)
            ans += c * (c - 1) / 2;
        else {
            long long a = c / 2, b = c - a;
            ans += a * (a - 1) / 2 + b * (b - 1) / 2;
        }
    };
    for (int i = 0; i < n; i++) {
        long long x;
        cin >> x;
        x = llabs(x);
        while (!st.empty() && st.back().first < x)
            settle();
        if (!st.empty() && st.back().first == x)
            st.back().second++;
        else
            st.push_back({x, 1});
    }
    while (!st.empty())
        settle();
    cout << ans << '\n';

    return 0;
}
