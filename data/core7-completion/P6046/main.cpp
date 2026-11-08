#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    const long long mod = 998244353;
    vector<int> a(n), left(n, -1), right(n, n), st;
    for (int &x : a)
        cin >> x;
    for (int i = 0; i < n; i++) {
        while (!st.empty() && a[st.back()] < a[i])
            st.pop_back();
        if (!st.empty())
            left[i] = st.back();
        st.push_back(i);
    }
    st.clear();
    for (int i = n - 1; i >= 0; i--) {
        while (!st.empty() && a[st.back()] < a[i])
            st.pop_back();
        if (!st.empty())
            right[i] = st.back();
        st.push_back(i);
    }
    vector<long long> inv(2 * n + 2);
    inv[1] = 1;
    for (int i = 2; i < (int)inv.size(); i++)
        inv[i] = (mod - mod / i) * inv[mod % i] % mod;
    for (int i = 0; i < n; i++) {
        long long ans = n - 1;
        if (left[i] >= 0)
            ans = (ans - n * inv[i - left[i] + 1] % mod + mod) % mod;
        if (right[i] < n)
            ans = (ans - n * inv[right[i] - i + 1] % mod + mod) % mod;
        if (left[i] >= 0 && right[i] < n)
            ans = (ans + n * inv[right[i] - left[i] + 1]) % mod;
        cout << ans << (i + 1 == n ? '\n' : ' ');
    }

    return 0;
}
