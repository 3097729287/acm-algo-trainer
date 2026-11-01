#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>a(n),left(n),right(n),stack,answer(n+1);for(int &x:a) cin>>x;
for(int i=0;i<n;++i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();left[i]=stack.empty()?-1:stack.back();stack.push_back(i);}
stack.clear();for(int i=n-1;i>=0;--i){while(!stack.empty()&&a[stack.back()]>=a[i]) stack.pop_back();right[i]=stack.empty()?n:stack.back();stack.push_back(i);}
for(int i=0;i<n;++i){int length=right[i]-left[i]-1;answer[length]=max(answer[length],a[i]);}
for(int length=n-1;length>=1;--length) answer[length]=max(answer[length],answer[length+1]);
for(int length=1;length<=n;++length) cout<<(length==1?"":" ")<<answer[length];cout<<'\n';
    return 0;
}
