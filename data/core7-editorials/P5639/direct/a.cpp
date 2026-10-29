#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;int previous=-1,answer=0;
for(int i=0;i<n;++i){int x;cin>>x;if(i==0||x!=previous)++answer;previous=x;}cout<<answer<<'\n';
    return 0;
}
