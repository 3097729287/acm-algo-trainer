#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; getline(cin,s);
string presses="12312312312312312341231234";
int answer=0;
for(char c:s) answer += c==' '?1:presses[c-'a']-'0';
cout << answer << '\n';
    return 0;
}
