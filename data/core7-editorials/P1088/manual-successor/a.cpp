#include <bits/stdc++.h>
using namespace std;
bool successor(vector<int>&a){
    int n=a.size(),i=n-2;while(i>=0&&a[i]>=a[i+1])--i;
    if(i<0){reverse(a.begin(),a.end());return false;}
    int j=n-1;while(a[j]<=a[i])--j;
    swap(a[i],a[j]);reverse(a.begin()+i+1,a.end());return true;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<int>a(n);for(int &x:a)cin>>x;
while(m--)successor(a);
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');
    return 0;
}
