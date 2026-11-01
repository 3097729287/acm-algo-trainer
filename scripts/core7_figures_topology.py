"""Actual dependency, flow, cycle and bridge objects used by this unit."""
import base64
import hashlib
import json
import math
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries


def arrow(f,x,y,px,py,color=BLUE,width=3):
    f.line(x,y,px,py,color,width=width);angle=math.atan2(py-y,px-x)
    for turn in [-0.5,0.5]:f.line(px,py,px-11*math.cos(angle+turn),py-11*math.sin(angle+turn),color,width=width)


def link(f,points,u,v,color=BLUE):
    x,y=points[u];px,py=points[v];angle=math.atan2(py-y,px-x)
    arrow(f,x+27*math.cos(angle),y+27*math.sin(angle),px-27*math.cos(angle),py-27*math.sin(angle),color)


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf-8'))}
    def save(pid,f,caption):
        path=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode();key='assets/core7/'+pid+'.svg'
        old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)

    f=Figure('只有全部前驱退出，三号才能进入可选队列',365)
    p={1:(120,110),2:(120,245),3:(370,175),4:(620,175),5:(620,300)}
    for u,v in [(1,3),(2,3),(3,4)]:link(f,p,u,v)
    for u,(x,y) in p.items():f.circle(x,y,u,GREEN if u in [1,2,5] else BLUE)
    f.text(270,315,'初始可选：1、2、5',GREEN,size=22)
    f.text(55,353,'取出一号后，三号仍在等二号；不能提前入队',size=21)
    save('B3644',f,'箭头表示必须先出现；绿色点无前驱，五号孤立但仍需输出。')

    f=Figure('并行前驱取最晚结束时刻，不把两段时间相加',335)
    f.box(45,95,185,65,'前驱一：5 分钟',GREEN,size=20);f.box(45,195,185,65,'前驱二：8 分钟',BLUE,size=20)
    f.box(410,145,280,65,'本项耗时：3 分钟',RED,size=22)
    arrow(f,230,125,405,167,GREEN);arrow(f,230,225,405,190,BLUE)
    f.text(245,300,'开始 8，结束 11',RED,size=22,anchor='middle')
    save('P1113',f,'两个准备工作同时进行，等最慢的八分钟结束，再完成本项三分钟。')

    for pid in ['P1137','P3183','P4017']:
        f=Figure('两条支路合流：最长路线取大，路径数量相加',375)
        p={1:(90,175),2:(290,95),3:(290,255),4:(520,175),5:(675,290)}
        for u,v in [(1,2),(1,3),(2,4),(3,4)]:link(f,p,u,v)
        for u,(x,y) in p.items():f.circle(x,y,u,GRAY if u==5 else BLUE)
        f.text(55,330,'四号：最长经过 3 个城市，完整路径有 2 条',size=21)
        if pid=='P1137':line='孤立五号仍有一条只游览自己的路线，长度为一'
        elif pid=='P3183':line='孤立五号不计食物链，最终数量为二'
        else:line='本题按两端不可延长定义，五号另计一条，合计三'
        f.text(55,367,line,GREEN,size=20)
        save(pid,f,line+'；箭头所连对象均是实际经过的城市或物种。')

    f=Figure('环留下，仍被环监视的后继也无法砸毁',355)
    p={1:(105,110),2:(355,110),3:(355,240),4:(625,240)}
    link(f,p,2,3,RED);f.line(330,240,280,175,RED);arrow(f,280,175,330,110,RED);link(f,p,3,4,RED)
    for u,(x,y) in p.items():f.circle(x,y,u,GREEN if u==1 else RED)
    f.text(45,315,'一号可砸；二、三互相监视；四号仍被三号监视',size=20)
    f.text(45,348,'最终留下三个摄像头，而非只留下两个环上点',RED,size=21)
    save('P2712',f,'这里四个编号都确有摄像头；一号没有监视关系，二三形成环，三还监视四。')

    f=Figure('先均分，再在汇点用共同单位相加',435)
    p={1:(85,180),2:(300,90),3:(300,285),4:(640,90),5:(640,285)}
    for u,v in [(1,2),(1,3),(1,5),(2,4),(2,5),(3,4),(3,5)]:link(f,p,u,v,GRAY)
    for u,(x,y) in p.items():f.circle(x,y,u,GREEN if u in [4,5] else BLUE)
    f.text(145,95,'每支 1/3',BLUE,size=19);f.text(420,70,'各出管 1/6',RED,size=19)
    f.text(45,370,'四号：1/6 + 1/6 = 1/3',GREEN,size=21)
    f.text(45,412,'五号：1/3 + 1/6 + 1/6 = 2/3',GREEN,size=21)
    save('P7113',f,'与第一组样例的五个结点及七条管道完全一致，四号、五号为最终排水口。')

    f=Figure('端点便宜即可跨过昂贵中间点闭环',370)
    p={1:(130,125),2:(375,125),3:(620,125)}
    link(f,p,1,2);link(f,p,2,3)
    for u,(x,y) in p.items():f.circle(x,y,u);f.text(x,80,'权值 '+str([3,100,4][u-1]),anchor='middle',size=20)
    f.line(620,155,620,250,RED);f.line(620,250,130,250,RED);arrow(f,130,250,130,155,RED)
    f.text(375,290,'新增三到一：代价 4+3=7',RED,size=22,anchor='middle')
    f.text(45,345,'原路径不要求只有一条边；中间点权不参与新增边费用',size=20)
    save('P10166',f,'蓝边为原图路径，红色折线只表示一条新边三到一，并未额外连接中间点。')

    f=Figure('主题一、二先出现，第三篇才能选到主题三',370)
    p={2:(145,125),1:(385,125),3:(625,250)}
    for u,v in [(1,2),(2,3),(3,1)]:f.line(*p[u],*p[v],GRAY)
    for u,(x,y) in p.items():f.circle(x,y,u);f.text(x,y-45,'主题 '+str({1:2,2:1,3:3}[u]),anchor='middle',size=21)
    f.text(50,315,'写作顺序：2 → 1 → 3',GREEN,size=23)
    f.text(50,353,'每次选已写邻居中缺失的最小正整数',size=21)
    save('CF1361A',f,'三个博客互相引用，写作顺序沿二、一、三；看到的较小主题分别为空、只有一、以及一和二。')

    f=Figure('合流后才判断兴奋，负边贡献可能抵消正值',385)
    p={1:(100,110),2:(100,260),3:(390,185),4:(650,185)}
    link(f,p,1,3,GREEN);link(f,p,2,3,RED);link(f,p,3,4,GRAY)
    for u,(x,y) in p.items():f.circle(x,y,u)
    f.text(100,65,'状态 5',GREEN,anchor='middle',size=20);f.text(100,310,'状态 6',RED,anchor='middle',size=20)
    f.text(230,100,'权 +1',GREEN,size=20);f.text(230,285,'权 −1',RED,size=20);f.text(520,150,'权 2',GRAY,size=20)
    f.text(45,352,'三号最终为 −1，不兴奋；四号不会收到先到的正五',size=21)
    save('P1038',f,'本图所有非输入层阈值为零，三号同时接收正五与负六后才确定状态。')

    f=Figure('优先一号的位置，不是先挑当前最小编号',355)
    f.circle(150,110,3);f.circle(400,110,1);arrow(f,177,110,373,110);f.circle(650,110,2,GRAY)
    f.row([2,3,1],190,x=115,width=150,colors={2:RED});f.text(590,222,'一号第 3',RED,size=20)
    f.row([3,1,2],265,x=115,width=150,colors={1:GREEN});f.text(590,297,'一号第 2',GREEN,size=20)
    f.text(45,345,'从末尾优先放编号大的当前汇点，得到下面的顺序',size=20)
    save('P3243',f,'唯一限制为三必须在一前。两个顺序都合法，但下方让一号的位置更早。')

    f=Figure('同一强连通组拿完一次，分叉路线只能选择一支',395)
    f.box(25,140,240,80,'{1,2,4}：38',BLUE,size=23);f.box(350,70,155,60,'{3}：8',GREEN,size=22)
    f.box(350,240,155,60,'{6}：5',GRAY,size=22);f.box(590,140,140,80,'{5}：1',BLUE,size=22)
    arrow(f,265,155,350,108,GREEN);arrow(f,505,108,590,155,GREEN);arrow(f,265,200,350,265,GRAY);arrow(f,505,265,590,200,GRAY)
    f.text(50,348,'选上支：38+8+1=47；选下支：38+5+1=44',size=21)
    f.text(50,385,'组内允许重复走，但每个 ATM 的钱只计算一次',size=20)
    save('P3627',f,'缩图对应原样例：一二四互通，三和六是两条不同后继支路，最终都能到五。')

    f=Figure('一个环至少失败一次，舍弃最小收益十即可',390)
    p={1:(150,125),2:(600,125),3:(600,270),4:(150,270)}
    for u,v in [(1,2),(2,3),(3,4),(4,1)]:link(f,p,u,v,RED if u==1 else BLUE)
    for u,(x,y) in p.items():
        f.circle(x,y,u,RED if u==1 else BLUE)
        f.text(x,y+(-45 if u in [1,2] else 50),'收益 '+str(u*10),anchor='middle',size=21)
    f.text(45,350,'让 2、3、4、1 依次行动，收益为 20+30+40=90',size=21)
    save('P8269',f,'边表示想访问谁；红色一号最后才行动，此时二号已经离开，正好只损失一号的十。')

    f=Figure('两条不同路径可以共同经过同一条桥',405)
    p={1:(120,115),2:(120,295),3:(410,205),4:(665,205)}
    for u,v in [(1,2),(2,3),(3,1)]:f.line(*p[u],*p[v],BLUE,width=4)
    f.line(*p[3],*p[4],RED,width=5)
    for u,(x,y) in p.items():f.circle(x,y,u,GREEN if u in [3,4] else BLUE)
    f.text(50,355,'四到一：4−3−1 和 4−3−2−1，共用桥 4−3',size=21)
    f.text(50,393,'三、四由桥相连必须同色；一、二可与它们异色',GREEN,size=20)
    save('P11022',f,'用绿色边框表示同一黑色组的三、四，蓝色边框表示白色一、二；原图红边是桥。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        first,separator,rest=spec.detail.partition('\n\n');spec.detail=first+block+(separator+rest if separator else '')
        spec.brief+=block
