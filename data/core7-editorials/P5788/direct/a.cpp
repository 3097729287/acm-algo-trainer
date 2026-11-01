#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>values(n),stack,answer(n);for(int &x:values) cin>>x;
for(int i=0;i<n;++i){while(!stack.empty()&&values[stack.back()]<values[i]){answer[stack.back()]=i+1;stack.pop_back();}stack.push_back(i);}
for(int i=0;i<n;++i) cout<<(i?" ":"")<<answer[i];cout<<'\n';
    return 0;
}
