#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
string in,post;cin>>in>>post;
function<void(int,int,int,int)>visit=[&](int l,int r,int p,int q){
    if(l==r)return;char root=post[q-1];int mid=l;while(in[mid]!=root)++mid;
    cout<<root;int left=mid-l;
    visit(l,mid,p,p+left);visit(mid+1,r,p+left,q-1);
};visit(0,in.size(),0,post.size());cout<<'\n';
    return 0;
}
