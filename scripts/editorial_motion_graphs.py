"""Problem-specific parent rewrites, ancestor jumps and expanded graph states."""
from editorial_motion_assets import Clip,BLUE,GREEN,RED,GRAY

def graph_clips():
 clips=[]
 c=Clip('fleet-root-and-head','luogu-training-P1196','整列移动后，代表仍可留在队伍中间','真实队列位置、根身份与有符号偏移必须一起变化。','例如某列顺序',500)
 parent=list(range(5));size=[1]*5;offset=[0]*5;head=[0]*5;groups=[[1],[2],[3],[4]]
 def find(x):
  if parent[x]!=x:
   old=parent[x];parent[x]=find(old);offset[x]+=offset[old]
  return parent[x]
 def fleet_board(f):
  order=[v for group in groups for v in group];f.row(order,110,'实际各列',{i:GREEN if parent[v]==v else BLUE for i,v in enumerate(order)})
  cursor=0
  for group in groups[:-1]:cursor+=len(group);f.line(145+cursor*(840-175)/4-2,95,145+cursor*(840-175)/4-2,172,GRAY,width=4)
  f.row(parent[1:],230,'父亲编号',indices=True)
  f.row(offset[1:],335,'相对偏移',indices=True)
  f.note(450,f'根 2 的 head={head[2]}；竖线分列，绿色编号是代表。' if len(groups)<4 else '每舰各自成列。后续整列移动，列内相对距离不会改变。')
 c.frame('初始四舰分别成列，偏移均为零。',fleet_board,{'parent':parent,'offset':offset,'groups':groups})
 for i,j in [(1,2),(3,1),(2,4)]:
  a,b=find(i),find(j);difference=size[b]+head[a]-head[b]
  ga=next(g for g in groups if i in g);gb=next(g for g in groups if j in g);groups=[g for g in groups if g is not ga and g is not gb]+[gb+ga]
  if size[a]<=size[b]:parent[a]=b;offset[a]=difference;size[b]+=size[a]
  else:parent[b]=a;offset[b]=-difference;head[a]+=size[b];size[a]+=size[b]
  c.frame(f'M {i} {j}：把整列接到另一列尾部。'+('较大列的根 2 保留，4 在它前面，偏移为 −1。' if j==4 else '保持列内原顺序。'),fleet_board,{'parent':parent,'offset':offset,'head':head,'groups':groups,'difference':difference})
 assert groups==[[4,2,1,3]] and offset[4]==-1 and offset[3]==2
 c.frame('查询 4 与 3：|−1−2|−1=2，中间正是 2、1 两舰。',fleet_board,{'answer':2,'parent':parent,'offset':offset,'groups':groups})
 clips.append(c.check('4\nM 1 2\nM 3 1\nM 2 4\nC 4 3\n','2\n'))

 c=Clip('weighted-parent-compression','luogu-training-P2294','压缩父指针时，必须同时累加差值','换父亲后旧边的差值必须改成到新父亲的差。','find 必须先保存旧父亲',500)
 points={0:(640,100),1:(385,230),2:(130,350),3:(640,350)}
 stages=[([(3,0,'0')],[0,1,2,0],[0,0,0,0],'先记录 S₃−S₀=0，另外两个前缀仍可独立平移。'), ([(3,0,'0'),(2,1,'−2')],[0,1,1,0],[0,0,-2,0],'再记录 S₂−S₁=−2，2 指向 1，边差是 −2。'), ([(3,0,'0'),(2,1,'−2'),(1,0,'+4')],[0,0,1,0],[0,4,-2,0],'加入 S₁−S₀=4，把两个分量连起来。2 仍经由 1 到根。'), ([(3,0,'0'),(2,1,'−2'),(1,0,'+4')],[0,0,1,0],[0,4,-2,0],'查询 2 时，先记旧父亲 1：到根的差是 −2+4=2。'), ([(3,0,'0'),(2,0,'+2'),(1,0,'+4')],[0,0,0,0],[0,4,2,0],'现在把 2 直接连向 0，同时把边差改为 +2；关系没有变化。'), ([(3,0,'0'),(2,0,'+2'),(1,0,'+4')],[0,0,0,0],[0,4,2,0],'若又声称 S₂−S₀=3，就与已有差值 2 矛盾，返回 false。')]
 for edges,parent,offset,caption in stages:
  def draw(f):
   f.graph(points,edges,active=[0,2],directed=True)
   f.note(420,'offset[x] = S[x] − S[parent[x]]；改父亲就要改边差。',GREEN)
   f.note(465,'最终选 S₀=0 时，S₁=4、S₂=2、S₃=0；负月收入合法。')
  c.frame(caption,draw,{'parent':parent,'offset':offset,'edges':edges})
 clips.append(c.check('1\n3 4\n1 3 0\n2 2 -2\n1 1 4\n1 2 3\n','false\n'))

 c=Clip('lca-paired-lifting','luogu-training-P3379','先对齐深度，再同步跳到共同父亲下面','两端祖先相同的跳跃不能直接接受，否则会越过 LCA。','查询时，深度差',540)
 points={1:(420,90),2:(235,180),3:(610,180),4:(135,280),5:(330,280),6:(135,375),7:(550,280),8:(720,280)};edges=[(1,2),(1,3),(2,4),(2,5),(4,6),(3,7),(3,8)]
 stages=[(6,8,'补充例子以 1 为根，查询 6、8。深度分别为 3、2。'),(4,8,'深度差一，先把 6 上提到父亲 4；两端现在同深。'),(4,8,'试跳两条边：4 与 8 的祖先都是 1，不能接受这次同步跳。'),(2,3,'试跳一条边：祖先 2、3 不同，可以同时上提。'),(2,3,'两端已经不同点、同父亲；共同父亲 1 才是答案。')]
 for i,(u,v,caption) in enumerate(stages):
  def draw(f):
   f.graph(points,edges,active=[u,v]);f.note(455,f'当前位置 u={u}，v={v}；'+('返回父亲 1。' if i==4 else '始终保留尚未会合的两条父链。'),GREEN)
   f.note(505,'本图固定以 1 为根，与前文根为 4 的例子分开核对。',size=19)
   if i==2:f.line(*points[4],*points[1],RED,dash=True);f.line(*points[8],*points[1],RED,dash=True)
  c.frame(caption,draw,{'u':u,'v':v,'root':1,'answer':1 if i==4 else None})
 clips.append(c.check('8 1 1\n1 2\n1 3\n2 4\n2 5\n4 6\n3 7\n3 8\n6 8\n','1\n'))

 c=Clip('fuel-expanded-state','luogu-training-UVA11367','买油改变费用，开车改变城市与剩油','同一城市不同油量不能合并；行驶不再重复收钱。','任何实际行程都可拆成',500)
 points={0:(125,145),1:(420,285),2:(715,145)};edges=[(0,1,'路长 2'),(1,2,'路长 2'),(0,2,'路长 4')]
 stages=[(0,0,0,'补充小例：容量四，只展示一条最优方案，从城市 0、空油箱开始。'),(0,1,5,'在 0 买一单位油，费用加 5；仍在同城。'),(0,2,10,'再买一单位，剩油 2，累计费用 10。'),(1,0,10,'行驶两单位到城市 1，消耗油但不再付费。'),(1,1,11,'城市 1 油价更低，买一单位只加 1。'),(1,2,12,'再买一单位后有 2 单位油，总费用 12。'),(2,0,12,'开到城市 2，用掉剩油，费用仍为 12；无需在出发时加满。')]
 for city,fuel,cost,caption in stages:
  def draw(f):
   f.graph(points,edges,active=[city]);f.text(125,205,'油价 5',BLUE,size=20,anchor='middle');f.text(420,345,'油价 1',BLUE,size=20,anchor='middle');f.text(715,205,'油价 9',BLUE,size=20,anchor='middle')
   f.row([city,fuel,cost],395,'城/油/费')
   f.note(480,'容量 4；在城市 0 直接买满走直路需要 20，这条方案只需 12。',GREEN,size=18)
  c.frame(caption,draw,{'city':city,'fuel':fuel,'cost':cost})
 clips.append(c.check('3 3\n5 1 9\n0 1 2\n1 2 2\n0 2 4\n1\n4 0 2\n','12\n'))

 c=Clip('forbidden-triple-state','lab:codeforces:59E','同在城市 3，上一站不同就有不同的下一步','需要重访城市；按当前城市去重会丢掉合法路径。','1→3→2→3→4 合法',500)
 points={1:(130,115),2:(130,315),3:(450,215),4:(725,215)};edges=[(1,2),(2,3),(3,4),(1,3)]
 stages=[([1],0,1,False,'起点状态是 (0,1)，虚拟前驱 0 不是实际城市。'),([1,3],1,3,False,'走到 3：上一站为 1，状态 (1,3)。'),([1,3],1,3,True,'此时不能去 4，因为 (1,3,4) 被禁止；不能把所有城市 3 状态都禁掉。'),([1,3,2],3,2,False,'先走到 2，得到状态 (3,2)。'),([1,3,2,3],2,3,False,'再回到 3：现在是不同状态 (2,3)，可以继续。'),([1,3,2,3,4],3,4,False,'(2,3,4) 不在禁表中，抵达 4；实际走了四条边。')]
 for path,previous,current,blocked,caption in stages:
  def draw(f):
   special={(3,4):RED} if blocked else {(a,b):GREEN for a,b in zip(path,path[1:])}
   f.graph(points,edges,active=[current],special=special)
   f.row([previous,current,len(path)-1],365,'前/现/边数')
   f.note(470,'路径：'+' → '.join(map(str,path)),GREEN)
  c.frame(caption,draw,{'path':path,'previous':previous,'current':current,'blocked':blocked})
 clips.append(c.check('4 4 2\n1 2\n2 3\n3 4\n1 3\n1 2 3\n1 3 4\n','4\n1 3 2 3 4\n'))
 return clips
