#include <bits/stdc++.h>
using namespace std;
void merge_sort(vector<int>&a,vector<int>&temp,int l,int r){
    if(r-l<=1)return;
    int mid=l+(r-l)/2;
    merge_sort(a,temp,l,mid);merge_sort(a,temp,mid,r);
    int i=l,j=mid;
    // 每次取两段剩余元素中最小的一项。
    for(int k=l;k<r;++k){
        if(j==r||(i<mid&&a[i]<=a[j]))temp[k]=a[i++];
        else temp[k]=a[j++];
    }
    for(int k=l;k<r;++k)a[k]=temp[k];
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n),temp(n);for(int &x:a)cin>>x;merge_sort(a,temp,0,n);
for(int i=0;i<n;++i)cout<<a[i]<<(i+1==n?'\n':' ');
    return 0;
}
