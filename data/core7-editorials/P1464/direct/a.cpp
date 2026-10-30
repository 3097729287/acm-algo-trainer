#include <bits/stdc++.h>
using namespace std;
long long memo[21][21][21];bool seen[21][21][21];
long long w(long long a,long long b,long long c){
    if(a<=0||b<=0||c<=0)return 1;
    if(a>20||b>20||c>20)return w(20,20,20);
    if(seen[a][b][c])return memo[a][b][c];
    long long result;
    if(a<b&&b<c)result=w(a,b,c-1)+w(a,b-1,c-1)-w(a,b-1,c);
    else result=w(a-1,b,c)+w(a-1,b-1,c)+w(a-1,b,c-1)-w(a-1,b-1,c-1);
    seen[a][b][c]=true;return memo[a][b][c]=result;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
long long a,b,c;
while(cin>>a>>b>>c){
    if(a==-1&&b==-1&&c==-1)break;
    cout<<"w("<<a<<", "<<b<<", "<<c<<") = "<<w(a,b,c)<<'\n';
}
    return 0;
}
