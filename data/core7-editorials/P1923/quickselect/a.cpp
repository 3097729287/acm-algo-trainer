#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,k;cin>>n>>k;vector<int>a(n);for(int &x:a)cin>>x;
mt19937 rng(20261030);int l=0,r=n-1;
while(true){
    int pivot=a[uniform_int_distribution<int>(l,r)(rng)],lt=l,i=l,gt=r;
    while(i<=gt){
        if(a[i]<pivot)swap(a[lt++],a[i++]);
        else if(a[i]>pivot)swap(a[i],a[gt--]);
        else ++i;
    }
    if(k<lt)r=lt-1;else if(k>gt)l=gt+1;else {cout<<pivot<<'\n';break;}
}
    return 0;
}
