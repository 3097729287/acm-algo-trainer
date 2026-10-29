#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;static int count[676][676]={};long long answer=0;
while(n--){string city,state;cin>>city>>state;
    int a=(city[0]-'A')*26+city[1]-'A',b=(state[0]-'A')*26+state[1]-'A';
    if(a==b)continue;
    answer+=count[b][a];++count[a][b];
}
cout<<answer<<'\n';
    return 0;
}
