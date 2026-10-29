#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n),b(n);for(int &x:a)cin>>x;for(int &x:b)cin>>x;sort(a.begin(),a.end());sort(b.begin(),b.end());
int al=0,ar=n-1,bl=0,br=n-1,score=0;
while(al<=ar){
    if(a[ar]>b[br]){++score;--ar;--br;}
    else if(a[al]>b[bl]){++score;++al;++bl;}
    else{score+=(a[al]>b[br])-(a[al]<b[br]);++al;--br;}
}cout<<200*score<<'\n';
    return 0;
}
