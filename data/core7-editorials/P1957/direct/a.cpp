#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;char operation='a';
while(n--){string first;cin>>first;int a,b;
    if(first=="a"||first=="b"||first=="c"){operation=first[0];cin>>a>>b;}
    else {a=stoi(first);cin>>b;}
    int answer=operation=='a'?a+b:operation=='b'?a-b:a*b;
    char symbol=operation=='a'?'+':operation=='b'?'-':'*';
    string line=to_string(a)+symbol+to_string(b)+'='+to_string(answer);
    cout<<line<<'\n'<<line.size()<<'\n';
}
    return 0;
}
