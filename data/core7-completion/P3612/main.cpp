#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    string s;
    long long p;
    cin >> s >> p;
    long long length = s.size();
    while (length < p)
        length *= 2;
    while (length > (long long)s.size()) {
        long long half = length / 2;
        if (p > half)
            p = p == half + 1 ? half : p - half - 1;
        length = half;
    }
    cout << s[p - 1] << '\n';

    return 0;
}
