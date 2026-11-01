#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;int total=1<<n;vector<int>a(total);for(int &x:a)cin>>x;
int left=0,right=total/2;
for(int i=1;i<total/2;++i)if(a[i]>a[left])left=i;
for(int i=total/2+1;i<total;++i)if(a[i]>a[right])right=i;
cout<<(a[left]<a[right]?left:right)+1<<'\n';
    return 0;
}
