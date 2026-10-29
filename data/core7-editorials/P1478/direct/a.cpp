#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,s,a,b;cin>>n>>s>>a>>b;vector<int>cost;
while(n--){int height,energy;cin>>height>>energy;if(height<=a+b)cost.push_back(energy);}
sort(cost.begin(),cost.end());int answer=0;
for(int energy:cost){if(energy>s)break;s-=energy;++answer;}cout<<answer<<'\n';
    return 0;
}
