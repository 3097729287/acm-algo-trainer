#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; cin >> s;
int sum = 0, weight = 1;
for (int i = 0; i+1 < (int)s.size(); ++i)
    if (s[i] != '-') sum += (s[i]-'0') * weight++;
int r = sum % 11;
char check = r == 10 ? 'X' : char('0'+r);
if (s.back() == check) cout << "Right\n";
else { s.back() = check; cout << s << '\n'; }
    return 0;
}
