#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n),temporary(n);for(int &x:a) cin>>x;
vector<long long>keep(30),flip(30);
function<void(int,int,int)> divide=[&](int l,int r,int bit){
    if(bit<0||r-l<2) return;
    int zeros=0,ones=0;
    for(int i=l;i<r;++i){
        if(a[i]>>bit&1){flip[bit]+=zeros;++ones;}
        else{keep[bit]+=ones;++zeros;}
    }
    int zeroPosition=l,onePosition=l+zeros;
    for(int i=l;i<r;++i){if(a[i]>>bit&1) temporary[onePosition++]=a[i];else temporary[zeroPosition++]=a[i];}
    for(int i=l;i<r;++i) a[i]=temporary[i];
    divide(l,l+zeros,bit-1);divide(l+zeros,r,bit-1);
};
divide(0,n,29);
long long inversions=0;int x=0;
for(int bit=0;bit<30;++bit){
    inversions+=min(keep[bit],flip[bit]);
    if(flip[bit]<keep[bit]) x|=1<<bit;
}
cout<<inversions<<' '<<x<<'\n';
    return 0;
}
