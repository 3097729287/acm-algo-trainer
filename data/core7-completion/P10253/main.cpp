#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int T;
    cin >> T;
    while (T--) {
        string y;
        cin >> y;
        vector<int> d;
        int carry = 0;
        for (int i = (int)y.size() - 1; i >= 0; i--) {
            int z = (y[i] - '0') * 9 + carry;
            d.push_back(z % 10);
            carry = z / 10;
        }
        if (carry)
            d.push_back(carry);
        int rem = d[0];
        d.erase(d.begin());
        if (d.empty())
            d.push_back(0);
        int sum = accumulate(d.begin(), d.end(), 0);
        auto increment = [&]() {
            int i = 0;
            while (i < (int)d.size() && d[i] == 9) {
                d[i] = 0;
                sum -= 9;
                i++;
            }
            if (i == (int)d.size())
                d.push_back(0);
            d[i]++;
            sum++;
        };
        int delta = 0;
        if (rem) {
            increment();
            delta = 10 - rem;
        }
        bool found = false;
        int bound = 9 * y.size();
        for (; delta <= bound; delta += 10) {
            if (sum == delta) {
                found = true;
                break;
            }
            increment();
        }
        if (!found) {
            cout << -1 << '\n';
            continue;
        }
        while (d.size() > 1 && !d.back())
            d.pop_back();
        for (int i = (int)d.size() - 1; i >= 0; i--)
            cout << d[i];
        cout << '\n';
    }

    return 0;
}
