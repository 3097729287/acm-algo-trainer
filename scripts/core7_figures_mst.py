"""Actual cuts, trees, optional vertices and spatial edge thresholds."""
import base64
import hashlib
import json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries
from core7_figures_topology import arrow


def attach_figures(specs):
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text('utf8'))}
    def save(pid,f,caption):
        path=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode();key='assets/core7/'+pid+'.svg'
        old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)
    def nodes(f,points,marked=()):
        for u,(x,y) in points.items():f.circle(x,y,u,RED if u in marked else BLUE)
    def segment(f,p,u,v,label,color=BLUE,dy=-10,dash=False):
        f.line(*p[u],*p[v],color,width=4,dash=dash)
        x=(p[u][0]+p[v][0])/2;y=(p[u][1]+p[v][1])/2+dy
        width=sum(20 if ord(c)>127 else 12 for c in str(label))+12
        f.parts.append(f'<rect x="{x-width/2}" y="{y-22}" width="{width}" height="28" rx="3" fill="#fff"/>')
        f.text(x,y,label,color,size=20,anchor='middle')

    f=Figure('已买二号商品可以同时触发一号、三号优惠',365)
    p={0:(110,190),1:(390,95),2:(390,270),3:(665,270)}
    segment(f,p,0,2,3,GREEN,dy=5);segment(f,p,2,1,2,GREEN,dy=0);segment(f,p,2,3,2,GREEN)
    f.box(55,160,110,55,'商店',BLUE,size=22)
    for u in [1,2,3]:f.circle(*p[u],u)
    f.text(70,115,'原价均为 3',size=21);f.text(65,340,'先买 2，再凭 2 买 1、3：3+2+2=7',GREEN,size=22)
    save('P1194',f,'只画所选的三条购买依据；商品二是两件后续商品的共同父亲，购买过程不是一条链。')

    f=Figure('五朵云组成两组，只接受五减二等于三条边',330)
    p={1:(75,170),2:(220,170),3:(365,170),4:(535,170),5:(680,170)}
    for u,v,w in [(1,2,1),(2,3,2),(4,5,3)]:segment(f,p,u,v,w,GREEN)
    segment(f,p,3,4,20,GRAY,dash=True);nodes(f,p)
    f.text(65,255,'第一组：1、2、3',GREEN,size=21);f.text(490,255,'第二组：4、5',GREEN,size=21)
    f.text(55,305,'已付 1+2+3=6；再接分值 20 的边会只剩一组',size=21)
    save('P1195',f,'孤点也可单独成组；这里达到两组后就停止，不能继续为全图连通多付一条边。')

    f=Figure('每条光纤只铺一次，不能把到根的距离全相加',315)
    p={1:(80,145),2:(275,145),3:(470,145),4:(665,145)}
    for u,v,w in [(1,2,2),(2,3,3),(3,4,4)]:segment(f,p,u,v,w,GREEN)
    nodes(f,p)
    f.text(55,225,'这棵网络只需 2+3+4=9',GREEN,size=22)
    f.text(55,280,'从一号到各点的距离 2、5、9 不是建设费用',size=21)
    save('P1546',f,'示意完整费用矩阵的一棵最优树，其余直接连接可设为一百；网络中同一条光纤只付一次。')

    for pid in ['P1547','P2330']:
        f=Figure('连接三点用两条边，最大边为四十三',355)
        p={1:(105,255),2:(375,90),3:(655,255)}
        segment(f,p,1,2,23,GREEN);segment(f,p,1,3,43,GREEN,dy=30);segment(f,p,2,3,1000,GRAY);nodes(f,p)
        f.text(65,330,'所选边总权 66；瓶颈 43；条数 2',size=22)
        caption='最长已选边为四十三，不输出总权六十六。' if pid=='P1547' else '先把条数压到二，再最小化瓶颈；这张图应输出二与四十三。'
        save(pid,f,caption)

    from core7_cases_mst import euclidean_cost,brute_tree_cost,rank_bound_sum
    assert euclidean_cost([(0,0),(1,0),(0,3)],minimum=4,squared=True)==19
    f=Figure('平方门槛为四，太近的两个点反而不能直连',430)
    p={1:(190,330),2:(270,330),3:(190,90)}
    segment(f,p,1,2,'1<4',RED,dy=36,dash=True);segment(f,p,1,3,9,GREEN,dy=0);segment(f,p,2,3,10,GREEN,dy=0);nodes(f,p)
    f.text(330,155,'一号 (0,0)，二号 (1,0)',size=20);f.text(330,205,'三号 (0,3)，c=4',size=20)
    f.text(330,270,'合法边平方费用：9、10',GREEN,size=20);f.text(330,320,'总费用 19',GREEN,size=23)
    f.text(45,407,'坐标按同一尺度绘制；不能先按普通最近邻连线',size=20)
    save('P2212',f,'红色边被平方费用下限排除，仍可通过远处三号把一号与二号连通；费用相加九与十，不开根号。')

    assert euclidean_cost([(1,1),(3,1),(1,4)],free=[(0,2)])==2
    f=Figure('已建道路费用为零，新增长度只付两单位',420)
    p={1:(200,330),2:(360,330),3:(200,90)}
    segment(f,p,1,3,'已建 0',GRAY,dy=0);segment(f,p,1,2,'新建 2',GREEN,dy=35);segment(f,p,2,3,'未选 √13',GRAY,dy=-15,dash=True);nodes(f,p)
    f.text(405,140,'一号 (1,1)',size=20);f.text(405,190,'二号 (3,1)',size=20);f.text(405,240,'三号 (1,4)',size=20)
    f.text(80,400,'旧路实际长三，但新增费用为零；答案 2.00',size=21)
    save('P2872',f,'空间点按同一尺度绘制；已有一到三号道路不再付费，新建一到二号的两单位即可。')

    assert euclidean_cost([(0,0),(3,4),(3,0)],maximum=4)==7
    f=Figure('长度上限四：三与四可建，五的斜边禁止',405)
    p={1:(110,320),2:(290,80),3:(290,320)}
    segment(f,p,1,3,3,GREEN,dy=32);segment(f,p,3,2,4,GREEN,dy=0);segment(f,p,1,2,5,RED,dy=-12,dash=True);nodes(f,p)
    f.text(400,110,'一号 (0,0)',size=20);f.text(400,160,'二号 (3,4)',size=20);f.text(400,210,'三号 (3,0)',size=20)
    f.text(400,275,'总长 7.00',GREEN,size=23)
    f.text(55,385,'等于上限的边可以用；比较时用整数平方',size=21)
    save('P17016',f,'这是三四五直角三角形，距离五的边超过上限四，但另外两条合法线路仍能连接全部点。')

    assert brute_tree_cost(3,[(0,2,8),(2,1,3),(0,1,2)])==5
    f=Figure('插入新边后，只需替换旧树环上的最重边',365)
    p={1:(105,255),2:(655,255),3:(375,90)}
    segment(f,p,1,3,8,GRAY,dash=True);segment(f,p,3,2,3,GREEN);segment(f,p,1,2,'新边 2',GREEN,dy=30);nodes(f,p)
    f.text(60,330,'旧最优 8+3=11；新最优 2+3=5',size=22)
    save('P1340',f,'灰色八权边只移出当前候选树，原图道路仍然已知；插入更新性质保证保留新最优树足以接续。')

    f=Figure('代价八与七先保留，最后切断代价二的边',335)
    p={0:(80,150),1:(275,150),2:(470,150),3:(665,150)}
    segment(f,p,0,1,8,GREEN);segment(f,p,1,2,2,RED,dash=True);segment(f,p,2,3,7,GREEN);nodes(f,p,marked=[0,3])
    f.text(60,235,'红色城市敌占；两块各含一个敌方点',size=21)
    f.text(60,300,'必须断开它们，选择删除便宜的中间边，代价 2',GREEN,size=21)
    save('P2700',f,'原道路是一条树链，保留两端昂贵边仍合法，切掉中间二权边即可互相隔离。编号从零开始。')

    f=Figure('N为四、K为三：只画必选的星形最小树',435)
    p={1:(100,100),2:(660,100),3:(380,330),4:(380,220)}
    segment(f,p,1,4,'2019201721',RED,dy=0,dash=True);segment(f,p,2,4,'2019201637',RED,dy=0,dash=True)
    segment(f,p,3,4,'2019201553',GREEN,dy=0);nodes(f,p)
    f.text(60,390,'删去两条最大边，得到 {1}、{2}、{3,4}',size=21)
    f.text(60,425,'最小被删边 2019201637，就是最优组间距',GREEN,size=21)
    save('P5425',f,'原图是完全图，此处仅显示以四为中心的必选最小生成树；不能把未绘出的原图边误当作不存在。')

    assert rank_bound_sum(5,5)==12
    f=Figure('n=m=五：先把三点团填满，再接两个新点',385)
    p={1:(90,100),2:(295,100),3:(200,255),4:(460,255),5:(665,255)}
    for u,v,w in [(1,2,1),(2,3,2),(3,4,4),(4,5,5)]:segment(f,p,u,v,w,GREEN)
    segment(f,p,1,3,'3 跳过',RED,dy=0,dash=True);nodes(f,p)
    f.text(45,330,'一、二接受；三闭环；四、五必须留给新点',size=21)
    f.text(45,375,'最小生成树总权 1+2+4+5=12',GREEN,size=22)
    save('P12375',f,'五条边、五个点且无重边自环。若继续把预算用于旧块内部，就不够把第四、第五个点接入。')

    for pid in ['CF1184E1','CF1184E2','P2245']:
        f=Figure('树上两端路径的最大边是四，不是路径和七',365)
        p={1:(100,255),2:(660,255),3:(380,90)}
        segment(f,p,1,3,4,GREEN);segment(f,p,3,2,3,GREEN);segment(f,p,1,2,'原非树边 8',GRAY,dy=30,dash=True);nodes(f,p)
        line='沿树路径最大为 4，优于直接边 8；危险不是 4+3' if pid=='P2245' else '将 8 改到 4，可以换下原树的 4；再大则不行'
        f.text(55,330,line,size=21)
        if pid=='P2245':
            caption='一号到二号走过两条边，最大危险为四；最小生成树路径保留原图的最佳瓶颈。'
        else:caption='在树上用四与三连接两端，路径瓶颈四；修改非树边时等于四仍可能入树，超过四才被排除。'
        save(pid,f,caption)

    f=Figure('最短路相同，再为最后一条边少付一单位',400)
    p={1:(105,275),2:(380,95),3:(655,275)}
    segment(f,p,1,2,1,GREEN);segment(f,p,2,3,1,GREEN);segment(f,p,1,3,2,GRAY,dy=35,dash=True);nodes(f,p)
    f.text(60,345,'源点 3：d[3]=0，d[2]=1，d[1]=2',size=21)
    f.text(60,390,'一号经二号或直达都最短，但父边选权 1 更便宜',GREEN,size=20)
    save('CF545E',f,'两种到一号的路线都长二；选择两条绿色边，总边权二，而直接到一号的树总边权三。')

    f=Figure('一个乡镇接两条新路，城市化费只付一次',410)
    p={1:(100,100),2:(650,100),3:(100,300),4:(650,300),'T':(330,200)}
    segment(f,p,1,'T',1,GREEN);segment(f,p,3,'T',2,GREEN);segment(f,p,3,4,4,BLUE);segment(f,p,4,2,5,BLUE)
    for u in [1,2,3,4]:f.circle(*p[u],u)
    f.circle(*p['T'],'T',GREEN);f.box(390,160,220,55,'乡镇启用费 1',RED,fill='#fff3f4',size=20)
    f.text(50,365,'旧路 4+5，新路 1+2，另付一次启用费 1',size=21)
    f.text(50,405,'总费用 13；只画样例最优方案采用的道路',GREEN,size=21)
    save('P14362',f,'乡镇T通过两条新路服务多个城市，启用费不是每条新路都付；其它乡镇可以完全不选。')

    f=Figure('三角环的最大森林五，小于全部三条边之和六',380)
    p={1:(105,270),2:(380,95),3:(655,270)}
    segment(f,p,1,2,1,GREEN);segment(f,p,2,3,2,GREEN);segment(f,p,1,3,'尝试 3',RED,dy=30,dash=True);nodes(f,p)
    f.text(45,340,'原森林总权 3；加入第三边，模拟器回答 5',size=21)
    f.text(45,375,'5 虽然大于 3，却不等于 3+3，所以应拒绝',RED,size=21)
    save('CF1687B',f,'模拟器对全三角形取最大森林，保留权二、三得到五；不是把五误当成最终最小森林答案。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        first,separator,rest=spec.detail.partition('\n\n');spec.detail=first+block+(separator+rest if separator else '')
        spec.brief+=block
