#include <bits/stdc++.h>
using namespace std;
struct Person{string name;int year,month,day,id;};
bool older(const Person&a,const Person&b){if(a.year!=b.year)return a.year<b.year;if(a.month!=b.month)return a.month<b.month;if(a.day!=b.day)return a.day<b.day;return a.id>b.id;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;cin>>n;vector<Person>a(n);for(int i=0;i<n;++i){cin>>a[i].name>>a[i].year>>a[i].month>>a[i].day;a[i].id=i;}
sort(a.begin(),a.end(),older);for(const auto &p:a)cout<<p.name<<'\n';
    return 0;
}
