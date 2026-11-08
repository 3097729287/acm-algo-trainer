DINIC=r'''
struct Dinic {
    struct Edge { int to,reverse; long long capacity; };
    vector<vector<Edge>> graph;vector<int> level,current;
    explicit Dinic(int n):graph(n),level(n),current(n){}
    void resize(int n){graph.resize(n);level.resize(n);current.resize(n);}
    int add(int u,int v,long long capacity){int index=graph[u].size(),reverse=graph[v].size();graph[u].push_back({v,reverse,capacity});graph[v].push_back({u,index,0});return index;}
    bool bfs(int source,int sink){fill(level.begin(),level.end(),-1);vector<int> queue={source};level[source]=0;for(size_t i=0;i<queue.size();i++)for(auto e:graph[queue[i]])if(e.capacity>0 && level[e.to]<0){level[e.to]=level[queue[i]]+1;queue.push_back(e.to);}return level[sink]>=0;}
    long long send(int u,int sink,long long amount){if(u==sink)return amount;for(int &i=current[u];i<(int)graph[u].size();i++){auto &e=graph[u][i];if(e.capacity>0 && level[e.to]==level[u]+1){long long value=send(e.to,sink,min(amount,e.capacity));if(value){e.capacity-=value;graph[e.to][e.reverse].capacity+=value;return value;}}}return 0;}
    long long maximum(int source,int sink,long long limit=LLONG_MAX/4){long long total=0;while(total<limit && bfs(source,sink)){fill(current.begin(),current.end(),0);while(total<limit){long long value=send(source,sink,limit-total);if(!value)break;total+=value;}}return total;}
};
'''
MATCHING=r'''
struct Matching {
    int left,right,shortest;vector<vector<int>> edge;vector<int> mateLeft,mateRight,distance;
    Matching(int left,int right):left(left),right(right),edge(left),mateLeft(left,-1),mateRight(right,-1),distance(left){}
    bool bfs(){queue<int> queue;fill(distance.begin(),distance.end(),-1);for(int u=0;u<left;u++)if(mateLeft[u]<0){distance[u]=0;queue.push(u);}shortest=INT_MAX;while(!queue.empty()){int u=queue.front();queue.pop();if(distance[u]+1>shortest)continue;for(int v:edge[u])if(mateRight[v]<0)shortest=min(shortest,distance[u]+1);else if(distance[mateRight[v]]<0){distance[mateRight[v]]=distance[u]+1;queue.push(mateRight[v]);}}return shortest<INT_MAX;}
    bool dfs(int u){for(int v:edge[u])if((mateRight[v]<0 && distance[u]+1==shortest)||(mateRight[v]>=0 && distance[mateRight[v]]==distance[u]+1 && dfs(mateRight[v]))){mateLeft[u]=v;mateRight[v]=u;return true;}distance[u]=-1;return false;}
    int maximum(){int result=0;while(bfs())for(int u=0;u<left;u++)if(mateLeft[u]<0 && dfs(u))result++;return result;}
};
'''
COST_FLOW=r'''
struct CostFlow {
    struct Edge { int to,reverse;long long capacity,cost; };
    vector<vector<Edge>> graph;
    explicit CostFlow(int n):graph(n){}
    void add(int u,int v,long long capacity,long long cost){int a=graph[u].size(),b=graph[v].size();graph[u].push_back({v,b,capacity,cost});graph[v].push_back({u,a,0,-cost});}
    pair<long long,long long> minimum(int source,int sink){
        const long long inf=LLONG_MAX/4;long long flow=0,cost=0;int n=graph.size();
        while(true){vector<long long> distance(n,inf);vector<int> parent(n,-1),index(n);vector<bool> inQueue(n);queue<int> queue;queue.push(source);inQueue[source]=true;distance[source]=0;
            while(!queue.empty()){int u=queue.front();queue.pop();inQueue[u]=false;for(int i=0;i<(int)graph[u].size();i++){auto e=graph[u][i];if(e.capacity>0 && distance[e.to]>distance[u]+e.cost){distance[e.to]=distance[u]+e.cost;parent[e.to]=u;index[e.to]=i;if(!inQueue[e.to]){inQueue[e.to]=true;queue.push(e.to);}}}}
            if(parent[sink]<0)break;long long amount=inf;
            for(int v=sink;v!=source;v=parent[v])amount=min(amount,graph[parent[v]][index[v]].capacity);
            for(int v=sink;v!=source;v=parent[v]){auto &e=graph[parent[v]][index[v]];e.capacity-=amount;graph[v][e.reverse].capacity+=amount;}
            flow+=amount;cost+=amount*distance[sink];
        }
        return {flow,cost};
    }
};
'''
FLOW_EXPLANATION='Dinic先BFS建立剩余容量正边的层次图，再用当前弧DFS只沿层数加1的边增广，更新正反向残量；一轮阻塞流结束后重新分层。最大流等于最小割容量，反向残量允许撤回之前的分配。'
MATCH_EXPLANATION='参考代码使用Hopcroft–Karp：从所有未匹配左点BFS标记最短增广路层数，再DFS沿这些层同时增广。每条增广路将匹配边与非匹配边交替翻转，匹配数增加1；不存在增广路时已达最大匹配。'
