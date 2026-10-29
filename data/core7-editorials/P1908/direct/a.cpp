#include <bits/stdc++.h>
using namespace std;
vector<int>sequence,temporary;
long long count_inversions(int l,int r){
    if(r-l<=1)return 0;int mid=(l+r)/2;
    long long answer=count_inversions(l,mid)+count_inversions(mid,r);
    int i=l,j=mid,k=l;
    while(i<mid&&j<r){
        if(sequence[i]<=sequence[j])temporary[k++]=sequence[i++];
        else{answer+=mid-i;temporary[k++]=sequence[j++];}
    }
    while(i<mid)temporary[k++]=sequence[i++];while(j<r)temporary[k++]=sequence[j++];
    for(i=l;i<r;++i)sequence[i]=temporary[i];return answer;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;sequence.resize(n);temporary.resize(n);for(int &x:sequence)cin>>x;cout<<count_inversions(0,n)<<'\n';
    return 0;
}
