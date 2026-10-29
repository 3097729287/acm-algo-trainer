#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string s;cin>>s;stack<long long> values;long long number=0;
for(char c:s){
    if(isdigit((unsigned char)c))number=number*10+c-'0';
    else if(c=='.'){values.push(number);number=0;}
    else if(c=='@')break;
    else {long long right=values.top();values.pop();long long left=values.top();values.pop();
        values.push(c=='+'?left+right:c=='-'?left-right:c=='*'?left*right:left/right);
    }
}
cout<<values.top()<<'\n';
    return 0;
}
