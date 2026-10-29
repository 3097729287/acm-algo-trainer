#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int year, month; cin >> year >> month;
int days[13] = {0,31,28,31,30,31,30,31,31,30,31,30,31};
bool leap = (year%4 == 0 && year%100 != 0) || year%400 == 0;
cout << days[month] + (month == 2 && leap) << '\n';
    return 0;
}
