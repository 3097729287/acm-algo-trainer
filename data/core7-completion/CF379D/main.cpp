#include <bits/stdc++.h>
using namespace std;
struct Descriptor {
    string word;
    char first, last;
    long long count;
};
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int k;
    long long x;
    int n, m;
    cin >> k >> x >> n >> m;
    auto generate = [&](int length) {
        vector<Descriptor> result;
        for (char first : string("ABC")) {
            vector<vector<string>> dp(3, vector<string>(length + 1));
            dp[first - 'A'][0] = string(1, first);
            for (int used = 1; used < length; used++) {
                vector<vector<string>> next(3, vector<string>(length + 1));
                for (int last = 0; last < 3; last++)
                    for (int count = 0; count <= length; count++)
                        if (!dp[last][count].empty())
                            for (int c = 0; c < 3; c++) {
                                int nc = count + (last == 0 && c == 2);
                                if (nc <= length && next[c][nc].empty())
                                    next[c][nc] = dp[last][count] + char('A' + c);
                            }
                dp.swap(next);
            }
            for (int last = 0; last < 3; last++)
                for (int count = 0; count <= length; count++)
                    if (!dp[last][count].empty())
                        result.push_back({dp[last][count], first, char('A' + last), count});
        }
        return result;
    };
    auto left = generate(n), right = generate(m);
    for (auto A : left)
        for (auto B : right) {
            long long a = A.count, b = B.count;
            char fa = A.first, la = A.last, fb = B.first, lb = B.last;
            for (int step = 3; step <= k; step++) {
                long long next = min(x + 1, a + b + (la == 'A' && fb == 'C'));
                char nf = fa, nl = lb;
                a = b;
                b = next;
                fa = fb;
                la = lb;
                fb = nf;
                lb = nl;
            }
            if (b == x) {
                cout << A.word << '\n' << B.word << '\n';
                return 0;
            }
        }
    cout << "Happy new year!\n";

    return 0;
}
