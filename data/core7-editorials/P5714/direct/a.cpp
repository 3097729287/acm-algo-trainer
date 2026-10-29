#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
double m, h; cin >> m >> h;
double bmi = m / (h*h);
if (bmi < 18.5) cout << "Underweight\n";
else if (bmi < 24) cout << "Normal\n";
else cout << bmi << "\nOverweight\n";
    return 0;
}
