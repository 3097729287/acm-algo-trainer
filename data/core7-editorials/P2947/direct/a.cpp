#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<int>height(n),stack,answer(n);for(int &x:height) cin>>x;
for(int i=n-1;i>=0;--i){while(!stack.empty()&&height[stack.back()]<=height[i]) stack.pop_back();if(!stack.empty()) answer[i]=stack.back()+1;stack.push_back(i);}
for(int x:answer) cout<<x<<'\n';
    return 0;
}
