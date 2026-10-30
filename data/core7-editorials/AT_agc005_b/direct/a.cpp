#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n+2),left(n+2),right(n+2),stack;
for(int i=1;i<=n;++i)cin>>a[i];
for(int i=1;i<=n;++i){
    while(!stack.empty()&&a[stack.back()]>a[i])stack.pop_back();
    left[i]=stack.empty()?0:stack.back();stack.push_back(i);
}
stack.clear();
for(int i=n;i>=1;--i){
    while(!stack.empty()&&a[stack.back()]>a[i])stack.pop_back();
    right[i]=stack.empty()?n+1:stack.back();stack.push_back(i);
}
long long answer=0;for(int i=1;i<=n;++i)answer+=1LL*a[i]*(i-left[i])*(right[i]-i);
cout<<answer<<'\n';
    return 0;
}
