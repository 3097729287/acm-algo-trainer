#include <bits/stdc++.h>
using namespace std;
bool leap(int y){return (y%4==0&&y%100!=0)||y%400==0;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int x,y;cin>>x>>y;vector<int> years;
for(int year=x;year<=y;++year)if(leap(year))years.push_back(year);
cout<<years.size()<<'\n';for(int i=0;i<(int)years.size();++i)cout<<years[i]<<(i+1==(int)years.size()?'\n':' ');
if(years.empty())cout<<'\n';
    return 0;
}
