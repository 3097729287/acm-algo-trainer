#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string pattern;
    int n;
    cin >> pattern >> n;
    int ans = 0;
    while (n--) {
        string s;
        cin >> s;
        vector<char> dp(s.size() + 1), next(s.size() + 1);
        dp[0] = 1;
        for (char c : pattern) {
            fill(next.begin(), next.end(), 0);
            if (c == '*') {
                next[0] = dp[0];
                for (int j = 1; j <= (int)s.size(); j++)
                    next[j] = dp[j] || next[j - 1];
            } else
                for (int j = 1; j <= (int)s.size(); j++)
                    next[j] = dp[j - 1] && (c == '?' || c == s[j - 1]);
            dp.swap(next);
        }
        ans += !dp.back();
    }
    cout << ans << '\n';

    return 0;
}
