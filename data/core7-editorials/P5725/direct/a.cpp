#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n; cin >> n; int value = 1;
cout << setfill('0');
for (int i = 0; i < n; ++i) {
    for (int j = 0; j < n; ++j) cout << setw(2) << value++;
    cout << '\n';
}
cout << '\n'; value = 1;
for (int i = 1; i <= n; ++i) {
    cout << string(2*(n-i),' ');
    for (int j = 0; j < i; ++j) cout << setw(2) << value++;
    cout << '\n';
}
    return 0;
}
