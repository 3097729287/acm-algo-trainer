#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    string s;
    cin >> s;
    for (char ch : s) {
        if ('A' <= ch && ch <= 'Z') ch = char(ch - 'A' + 'a');
        bool vowel = ch == 'a' || ch == 'o' || ch == 'y'
                  || ch == 'e' || ch == 'u' || ch == 'i';
        // 只为保留的辅音输出点号，原字符顺序不变。
        if (!vowel) cout << '.' << ch;
    }
    cout << '\n';
}
