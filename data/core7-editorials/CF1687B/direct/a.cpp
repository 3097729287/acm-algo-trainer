#include <bits/stdc++.h>
using namespace std;
long long ask(const string &selection){
    cout<<"? "<<selection<<endl;long long reply;
    if(!(cin>>reply)||reply<0)exit(0);return reply;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n,m;if(!(cin>>n>>m))return 0;vector<long long>weight(m);string selected(m,'0');
for(int i=0;i<m;++i){selected[i]='1';weight[i]=ask(selected);selected[i]='0';}
vector<int>order(m);iota(order.begin(),order.end(),0);sort(order.begin(),order.end(),[&](int a,int b){return weight[a]<weight[b];});
long long total=0;for(int i:order){selected[i]='1';long long reply=ask(selected);
    // 只有全部正权边都被保留，才说明这次没有形成环。
    if(reply==total+weight[i])total+=weight[i];else selected[i]='0';
}cout<<"! "<<total<<endl;
    return 0;
}
