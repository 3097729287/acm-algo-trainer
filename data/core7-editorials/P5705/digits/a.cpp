#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int whole, digit; char dot; cin >> whole >> dot >> digit;
cout << digit << '.' << whole % 10 << whole / 10 % 10 << whole / 100 << '\n';
    return 0;
}
