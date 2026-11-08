#include <bits/stdc++.h>
using namespace std;

struct Bag {
    long long numerator, denominator, total;
};
struct Compare {
    bool operator()(const Bag &a, const Bag &b) const {
        return (__int128)a.numerator * b.denominator < (__int128)b.numerator * a.denominator;
    }
};

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int tests;
    cin >> tests;
    while (tests--) {
        int n, k;
        cin >> n >> k;
        priority_queue<Bag, vector<Bag>, Compare> q;
        for (int i = 0; i < n; i++) {
            long long t, l;
            cin >> t >> l;
            long long g = gcd(t, l);
            q.push({l / g, t / g, t});
        }
        for (int step = 1; step < k; step++) {
            Bag b = q.top();
            q.pop();
            long long a = b.total - 1, d = b.total, g = gcd(a, b.denominator);
            a /= g;
            b.denominator /= g;
            g = gcd(d, b.numerator);
            d /= g;
            b.numerator /= g;
            b.numerator *= a;
            b.denominator *= d;
            if (!b.numerator)
                b.denominator = 1;
            q.push(b);
        }
        auto b = q.top();
        long long g = gcd(b.numerator, b.denominator);
        cout << b.numerator / g << '/' << b.denominator / g << '\n';
    }

    return 0;
}
