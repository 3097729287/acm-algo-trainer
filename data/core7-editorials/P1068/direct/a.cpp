#include <bits/stdc++.h>
using namespace std;
struct Candidate{int id,score;};
bool before(const Candidate&a,const Candidate&b){if(a.score!=b.score)return a.score>b.score;return a.id<b.id;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;cin>>n>>m;vector<Candidate>a(n);for(auto &x:a)cin>>x.id>>x.score;
sort(a.begin(),a.end(),before);int cutoff=a[m*3/2-1].score,count=0;
while(count<n&&a[count].score>=cutoff)++count;
cout<<cutoff<<' '<<count<<'\n';for(int i=0;i<count;++i)cout<<a[i].id<<' '<<a[i].score<<'\n';
    return 0;
}
