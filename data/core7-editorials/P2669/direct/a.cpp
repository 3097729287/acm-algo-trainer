#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int remaining; cin >> remaining;
long long answer = 0;
for (int pay = 1; remaining > 0; ++pay) {
    int days = min(remaining,pay);
    answer += 1LL * days * pay;
    remaining -= days;
}
cout << answer << '\n';
    return 0;
}
