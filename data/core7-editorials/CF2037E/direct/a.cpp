#include <bits/stdc++.h>
using namespace std;
long long ask(int right){
    cout<<"? 1 "<<right<<endl;
    long long reply;if(!(cin>>reply)||reply<0)exit(0);
    return reply;
}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int tests;if(!(cin>>tests))return 0;
while(tests--){
    int n;cin>>n;long long total=ask(n);
    if(total==0){cout<<"! IMPOSSIBLE"<<endl;continue;}
    string result;long long previous=0,zero_count=0;
    for(int i=2;i<=n;++i){
        long long current=(i==n?total:ask(i));
        if(result.empty()){
            if(current>0){
                // 首次有 01：此前必是若干一、current 个零。
                result=string(i-current-1,'1')+string(current,'0')+'1';
                zero_count=current;
            }
        }else if(current==previous){result+='0';++zero_count;}
        else if(current-previous==zero_count)result+='1';
        else return 0; // 回复不符合协议时结束
        previous=current;
    }
    cout<<"! "<<result<<endl;
}
    return 0;
}
