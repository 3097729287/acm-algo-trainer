#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    int n;
    cin >> n;
    long long ending = 0, answer = LLONG_MIN;
    while (n--) {
        long long x;
        cin >> x;
        ending = max(x, ending + x);
        answer = max(answer, ending);
    }
    cout << answer << '\n';

    return 0;
}
