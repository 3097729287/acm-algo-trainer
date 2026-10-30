#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int a,b;cin>>a>>b;const int shift=400,size=801;
vector<int>distance(size,-1);queue<int>todo;distance[shift]=0;todo.push(shift);
int change[]={-10,-5,-1,1,5,10};
while(!todo.empty()){
    int u=todo.front();todo.pop();
    if(u==b-a+shift){cout<<distance[u]<<'\n';return 0;}
    for(int delta:change){int v=u+delta;
        // 四十次的现成方案给出搜索边界，不限制只能朝目标走。
        if(0<=v&&v<size&&distance[v]==-1){distance[v]=distance[u]+1;todo.push(v);}
    }
}
    return 0;
}
