"""Actual graph edges, queue positions and large-tree region partitions."""
import base64
import math
import json
import hashlib
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries

def arrow(f,x1,y1,x2,y2,color=GRAY):
    f.line(x1,y1,x2,y2,color)
    angle=math.atan2(y2-y1,x2-x1);length=11
    points=[(x2,y2)]+[(x2-length*math.cos(angle+turn),y2-length*math.sin(angle+turn)) for turn in [-.48,.48]]
    f.parts.append('<polygon points="'+' '.join(f'{x:.2f},{y:.2f}' for x,y in points)+'" fill="'+color+'"/>')

def attach_figures(specs):
    pictures={}
    old={r['problem_id']:r.get('content',r).get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    roster=roster_entries()
    def save(pid,figure,caption):
        path=figure.save(pid,OUT/'figures');key='assets/core7/'+pid+'.svg'
        data='data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode()
        previous=old.get(roster[pid]['id'],{})
        if key in previous and previous[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,previous)

    f=Figure('三角形里能绕行，连向四号的边却无替代通路',360)
    points={1:(120,170),2:(290,95),3:(290,245),4:(610,245)}
    for u,v in [(1,2),(2,3),(3,1),(3,4)]:f.line(*points[u],*points[v],RED if (u,v)==(3,4) else BLUE,width=4)
    for u,(x,y) in points.items():f.circle(x,y,u)
    f.text(447,220,'唯一桥：3−4',RED,size=22,anchor='middle')
    f.text(45,330,'删三角形任一边仍连通；删红边后四号独立成块',size=22)
    save('P1656',f,'原图的四条边均画出。只有红色三号至四号铁路是桥，不是把 DFS 树上的每条边都当成桥。')

    f=Figure('环内的钥匙互相锁住，砸入树上的点不一定有用',355)
    for x,label in [(130,1),(360,2),(610,3)]:f.circle(x,145,label,radius=28)
    arrow(f,158,145,332,145,BLUE);arrow(f,388,130,582,130,RED);arrow(f,582,160,388,160,RED)
    f.text(50,225,'依赖 i → x：i 号的钥匙放在 x 号罐里',size=22)
    f.text(50,280,'砸一号：环仍锁住     砸二号：可取出一号、三号钥匙',size=20)
    f.text(50,330,'全部同属一块，最少砸一只，但不能在块中随便选',GREEN,size=21)
    save('P3420',f,'依赖为一到二、二到三、三到二。二与三构成环，一号只是在依赖链外端。')

    f=Figure('两色可整体交换；孤立学生可以独立选择学校',370)
    points={1:(100,120),2:(285,200),3:(100,235),4:(470,120),5:(650,235)}
    for leaf in [1,3,4]:f.line(*points[2],*points[leaf],GRAY,width=4)
    for u,(x,y) in points.items():f.circle(x,y,u,GREEN if u in [1,3,4,5] else RED)
    f.text(70,300,'交流块：三人对一人',size=21);f.text(525,300,'孤立点：一对零',size=20)
    f.text(55,350,'B 校最少 1+0=1 人，最多 3+1=4 人',GREEN,size=22)
    save('P10378',f,'已知交流只有二号分别与一、三、四号相连；五号未交流，不代表它必须属于某一校。')

    f=Figure('只添这一堵墙，就能把坏人隔在左下角',365)
    grid=['G...','#...','B#..'];x0,y0,cell=215,75,76
    for r,row in enumerate(grid):
        for c,value in enumerate(row):
            color=RED if (r,c)==(2,1) or value=='B' else GREEN if value=='G' else GRAY
            label='出口' if (r,c)==(2,3) else value
            f.box(x0+c*cell,y0+r*cell,cell-3,cell-3,label,color,fill='#fff0f0' if (r,c)==(2,1) else '#fff')
    f.text(45,135,'原墙',GRAY,size=20);f.line(110,145,210,185,GRAY)
    f.text(42,300,'新墙',RED,size=20);f.line(110,290,180,318,RED);f.line(180,318,329,318,RED);f.line(329,318,329,301,RED)
    f.text(55,347,'好人可经顶行到右侧出口；坏人的向上、向右都已封住',size=21)
    save('CF1365D',f,'三行四列地图中，只有左下角右侧的红色井号是新增墙；左边中格本来就是墙。')

    f=Figure('代表可以在队伍中间，距离仍由相对偏移相减',370)
    for y,label,values in [(80,'位置',[0,1,2,3]),(155,'舰船',[4,2,1,3]),(230,'根差',[-1,0,1,2])]:
        f.text(65,y+31,label,size=22);f.row(values,y,x=205,width=120,colors={1:GREEN})
    f.text(65,325,'根是二号；四号与三号之间是二、一，共两艘',size=22)
    f.text(65,360,'相对偏移：|−1−2|−1=2，不要求根就是队首',GREEN,size=21)
    save('P1196',f,'实际舰船顺序是四、二、一、三。绿色列是代表二号，根差一行表示各舰位置减代表位置。')

    f=Figure('一次往返每条边两遍，谈话费用也可分配到边',375)
    xs=[85,230,375,520,665];cost=[2,5,3,4,1];length=[1,2,1,0]
    for i in range(4):
        f.line(xs[i],150,xs[i+1],150,GRAY,width=4)
        f.text((xs[i]+xs[i+1])/2,115,'L='+str(length[i]),size=20,anchor='middle')
    for i,x in enumerate(xs):
        f.circle(x,150,i+1);f.text(x,215,'C='+str(cost[i]),GREEN,size=21,anchor='middle')
    f.text(45,285,'新边权依次为 9、12、9、5，总和三十五',size=22)
    f.text(45,340,'起点选五号，另加一次谈话费用一，总费用三十六',GREEN,size=21)
    save('P2916',f,'五个牧场的所有道路都已在链上，度数谈话项与两倍路程一起放到边权，只有最初一次起点谈话留在边外。')

    f=Figure('两条新路可以共用中间区域，不必连通全体田地',390)
    xs=[75,195,315,435,555,675]
    for a,b in [(0,1),(4,5)]:f.line(xs[a],150,xs[b],150,BLUE,width=5)
    f.line(xs[1],150,xs[2],150,GREEN,width=5)
    f.line(xs[2],172,xs[2],265,GREEN,width=4);f.line(xs[2],265,xs[4],265,GREEN,width=4);f.line(xs[4],265,xs[4],172,GREEN,width=4)
    for i,x in enumerate(xs):f.circle(x,150,i+1,GRAY if i==3 else BLUE)
    f.text(255,110,'费用 1',GREEN,size=21,anchor='middle');f.text(435,310,'费用 4',GREEN,size=21,anchor='middle')
    f.text(45,365,'选择 2−3、3−5，总费用五；四号不必接入牛棚路线',size=21)
    save('P7991',f,'蓝边是已有路，绿边是两条新路；折线只是标记三至五的一条边，并未在四号处建立连接。')

    f=Figure('共同零位才有边，全一掩码的重复景点仍各自孤立',435)
    xs=[90,265,440,650]
    f.line(xs[0],135,xs[1],135,BLUE,width=4);f.line(xs[1],135,xs[2],135,BLUE,width=4)
    for x,label,missing in zip(xs,['3','1','5','6'],['缺位 2','缺位 1、2','缺位 1','缺位 0']):
        f.circle(x,135,label);f.text(x,195,missing,size=19,anchor='middle')
    for x,label in [(225,'7a'),(530,'7b')]:f.circle(x,300,label,GRAY,radius=29);f.text(x,355,'没有零位',GRAY,size=20,anchor='middle')
    f.text(45,410,'三个相连景点一组，另有六号与两个七号，共四组',GREEN,size=21)
    save('P16495',f,'仅看低三位，按顺序插入三、一、五、六、七、七。两个七号为不同次得到的景点，不能共享一条合法相邻边。')

    f=Figure('边权和更小，不代表按位或更小',355)
    p={1:(160,105),2:(590,105),3:(375,260)}
    f.line(*p[1],*p[2],RED,width=4);f.line(*p[1],*p[3],GREEN,width=5);f.line(*p[2],*p[3],GREEN,width=5)
    for u,(x,y) in p.items():f.circle(x,y,u)
    f.text(375,85,'3',RED,size=22,anchor='middle');f.text(240,210,'4',GREEN,size=22);f.text(495,210,'4',GREEN,size=22)
    f.text(70,330,'选绿边：4 OR 4 = 4；选三和四则得到七',size=22)
    save('CF1624G',f,'三角形两条绿色边已是一棵生成树。高位判定针对能否避开某些位，不能替换为普通最小生成树权值和。')

    f=Figure('父指针压缩后，仍保留相同的坐标差',455)
    before={0:(175,100),1:(175,225),2:(175,350),3:(55,225)}
    after={0:(555,100),1:(435,300),2:(555,350),3:(680,300)}
    for positions in [before,after]:
        for u,parent in ([(1,0),(2,1),(3,0)] if positions is before else [(1,0),(2,0),(3,0)]):
            x,y=positions[u];px,py=positions[parent];angle=math.atan2(py-y,px-x)
            arrow(f,x+24*math.cos(angle),y+24*math.sin(angle),px-24*math.cos(angle),py-24*math.sin(angle),BLUE)
        for u,(x,y) in positions.items():f.circle(x,y,u)
    f.text(205,170,'+4',GREEN,size=22);f.text(205,295,'−2',RED,size=22);f.text(70,145,'0',size=20)
    f.text(590,230,'+2',GREEN,size=22);f.text(447,185,'+4',GREEN,size=22);f.text(678,180,'0',size=20)
    f.text(85,410,'压缩前：−2+4=2',size=21);f.text(440,410,'压缩后：直接到根，偏移二',size=20)
    f.save('weighted-dsu',ROOT/'docs/foundations/assets')

    f=Figure('四层原树逐点分区，旁支节点仍计入区域质量',525)
    points={1:(380,90),2:(210,175),3:(550,175),4:(125,260),5:(295,260),6:(465,260),7:(635,260)}
    for i,x in enumerate([75,170,245,340,415,510,585,680],8):points[i]=(x,350)
    for u in range(2,16):f.line(*points[u//2],*points[u],GRAY,width=2)
    orange='#9a6000'
    for u,(x,y) in points.items():f.circle(x,y,u,RED if u==8 else orange if u==10 else GREEN if u in [5,11] else BLUE,radius=20)
    for i,(label,color) in enumerate([('根区域：11',BLUE),('八号：1',RED),('五号：2',GREEN),('十号：1',orange)]):f.box(35+i*180,415,170,48,label,color,size=20)
    f.text(45,505,'四块共十五点；五号的完整子树三点，扣掉十号后为二',size=21)
    f.save('subtree-regions',ROOT/'docs/foundations/assets')
    save('P13308',f,'收集点仅为一、五、八、十，颜色表示收缩区域。未单独收集的二号、四号和右侧全部旁支仍属于蓝色根区域。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,previous=pictures[spec.pid];spec.images.update(previous);spec.images[key]=data
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        first,separator,rest=spec.detail.partition('\n\n');spec.detail=first+block+(separator+rest if separator else '')
        spec.brief+=block
