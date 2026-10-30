#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
int start=0,target=0,start_count=0,target_count=0;char c;for(int i=0;i<16;++i){cin>>c;if(c=='1'){start|=1<<i;++start_count;}}for(int i=0;i<16;++i){cin>>c;if(c=='1'){target|=1<<i;++target_count;}}
if(start_count!=target_count){cout<<-1<<'\n';return 0;}
vector<int>distance(1<<16,-1);queue<int>todo;todo.push(start);distance[start]=0;int dr[]={1,-1,0,0},dc[]={0,0,1,-1};
while(!todo.empty()){int state=todo.front();todo.pop();if(state==target){cout<<distance[state]<<'\n';return 0;}
    for(int p=0;p<16;++p)if(state&(1<<p))for(int d=0;d<4;++d){int r=p/4+dr[d],col=p%4+dc[d];if(r<0||r>=4||col<0||col>=4)continue;int q=r*4+col;
        if(state&(1<<q))continue;
        int next=state^(1<<p)^(1<<q); // 一位搬空，另一空位放入，玩具数不变。
        if(distance[next]==-1){distance[next]=distance[state]+1;todo.push(next);}
    }
}
cout<<-1<<'\n';
    return 0;
}
