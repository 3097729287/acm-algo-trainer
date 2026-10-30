#include <bits/stdc++.h>
using namespace std;
char weigh(const vector<int>&left,const vector<int>&right){
    cout<<"1 "<<left.size();for(int x:left)cout<<' '<<x;
    cout<<' '<<right.size();for(int x:right)cout<<' '<<x;cout<<endl;
    char reply;if(!(cin>>reply)||(reply!='<'&&reply!='>'&&reply!='='))exit(0);
    return reply;
}
int find_one(vector<int>group){
    while(group.size()>1){
        int q=((int)group.size()+2)/3;
        vector<int>left(group.begin(),group.begin()+q),right(group.begin()+q,group.begin()+2*q);
        char reply=weigh(left,right);
        if(reply=='<')group=left;
        else if(reply=='>')group=right;
        else group=vector<int>(group.begin()+2*q,group.end());
    }
    return group[0];
}
void answer(int x,int y){if(x>y)swap(x,y);cout<<"2 "<<x<<' '<<y<<endl;}
int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int n;if(!(cin>>n))return 0;
vector<int>candidate(n);iota(candidate.begin(),candidate.end(),1);int normal=0;
while(candidate.size()>2){
    int half=(int)candidate.size()/2;
    vector<int>left(candidate.begin(),candidate.begin()+half);
    vector<int>right(candidate.begin()+half,candidate.end());
    if(candidate.size()%2&&normal==0){
        // 首次奇数规模：留下一个球，异重时它仍可能是轻球。
        int outside=right.back();right.pop_back();char reply=weigh(left,right);
        if(reply=='='){answer(find_one(left),find_one(right));return 0;}
        if(reply=='<'){normal=right[0];candidate=left;}
        else{normal=left[0];candidate=right;}
        candidate.push_back(outside);
    }else{
        vector<int>pan=left;
        if(pan.size()<right.size())pan.push_back(normal); // 只给称盘补正常球
        char reply=weigh(pan,right);
        if(reply=='='){answer(find_one(left),find_one(right));return 0;}
        if(reply=='<'){normal=right[0];candidate=left;}
        else{normal=left[0];candidate=right;}
    }
}
answer(candidate[0],candidate[1]);
    return 0;
}
