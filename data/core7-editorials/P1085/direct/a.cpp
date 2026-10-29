#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int best = 8, answer = 0;
for (int day = 1; day <= 7; ++day) {
    int a, b; cin >> a >> b;
    if (a + b > best) { best = a + b; answer = day; }
}
cout << answer << '\n';
    return 0;
}
