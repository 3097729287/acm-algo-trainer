#include <bits/stdc++.h>
using namespace std;

long long parse_thousandths(string s) {
    size_t dot = s.find('.');
    if (dot == string::npos) return stoll(s) * 1000;
    string fraction = s.substr(dot + 1);
    while (fraction.size() < 3) fraction += '0';
    return stoll(s.substr(0,dot)) * 1000 + stoll(fraction);
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string m, h; cin >> m >> h;
long long M = parse_thousandths(m), H = parse_thousandths(h);
long long numerator = 1000 * M, denominator = H * H;
// 阈值比较完全使用整数，等于阈值时归入右侧区间。
if (2 * numerator < 37 * denominator) cout << "Underweight\n";
else if (numerator < 24 * denominator) cout << "Normal\n";
else cout << 1.0 * numerator / denominator << "\nOverweight\n";
    return 0;
}
