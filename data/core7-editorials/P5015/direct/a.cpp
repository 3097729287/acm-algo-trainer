#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s; getline(cin,s); int count=0;
for(char c:s) if(c!=' ') ++count;
cout << count << '\n';
    return 0;
}
