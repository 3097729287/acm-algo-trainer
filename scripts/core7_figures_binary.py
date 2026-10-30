"""Draw the exact cards, deficits, states and interval differences discussed."""
import base64
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import OUT


def attach_figures(specs):
    figures={};history={}
    def save(pid,f,caption,filename=None):
        filename=filename or pid
        if pid in figures:
            old_key,old_data,_=figures[pid];history.setdefault(pid,{})[old_key]=old_data
        path=f.save(filename,OUT/'figures');key='assets/core7/'+filename+'.svg'
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('三种卡各铺两次，再接两个不同的额外类型',355)
    f.row([1,2,3,1,2,3,1,2],75,x=50,width=82,colors={6:GREEN,7:GREEN})
    for i in range(6):
        y=153+i*24;f.line(90+i*82,y,90+(i+2)*82,y,GREEN,width=5)
    f.text(60,330,'六条线各对应一个长度三的排列窗口，分数为六',size=22)
    save('CF1967A',f,'初始数量 [3,2,2]，再买一张二。每条线覆盖的三格恰含一、二、三，不是在数不相邻的选法。')

    f=Figure('阈值五比三：选二、三号，转换得分恰为零',330)
    for y,label,row in [(70,'编号',[1,2,3]),(130,'美味度',[1,2,3]),(190,'耗时',[3,2,1]),(250,'3v−5c',[-12,-4,4])]:
        f.text(45,y+31,label,size=22);f.row(row,y,x=260,width=140,colors={1:GREEN,2:GREEN})
    f.text(55,320,'最大的两项 −4+4=0，等价于总比率至少 5/3',size=21)
    save('P1570',f,'每一列都是同一种调料的美味度、耗时和转换得分；不能拆开重配原本的两种属性。')

    f=Figure('缺口 [8,5,1]：三块长板完整填满，再处理余数',380)
    for row,(need,full) in enumerate([(8,6),(5,3),(1,0)]):
        y=85+row*75;f.text(30,y+31,'缺口 '+str(need),size=21)
        for j in range(need):
            color=BLUE if j<full else RED
            f.box(180+j*60,y,57,48,'1',color,fill='#edf5ff' if j<full else '#fff2f3')
        for cut in range(3,full+1,3):f.line(180+cut*60-2,y-6,180+cut*60-2,y+54,GRAY,dash=True)
    f.text(45,330,'h=3，前三块收益各三；余数分别二、二、一',size=21)
    f.text(45,365,'第四块覆盖一个余数二；其余需三块短板',size=21)
    save('P14115',f,'格子是实际缺口的单位高度；蓝色完整份额与红色余数分开，长板覆盖余数时多出高度会浪费。')

    f=Figure('右端为第五格：三个可选左端，排除首尾同为二',330)
    f.row([1,2,3,1,2],80,x=110,width=120,colors={1:RED,4:RED})
    for i,(label,color) in enumerate([('左端一：长度五，首尾不同，保留',GREEN),('左端二：长度四，首尾相同，排除',RED),('左端三：长度三，首尾不同，保留',GREEN)]):
        f.text(90,190+i*48,label,color,size=22)
    save('P6465',f,'最小长度三，允许左端集合是位置一、二、三；频次扣除的是这个集合里课程为二的左端。')

    f=Figure('两个轻球在一、五：第一次左轻，第二次平衡',420)
    for y,left,right,reply in [(80,'左盘 {1,2}','右盘 {3,4}','<'),(185,'左盘 {1,3}','右盘 {2,5}','=')]:
        f.box(40,y,285,65,left,GREEN);f.box(435,y,285,65,right,BLUE)
        f.text(380,y+43,reply,RED,size=34,anchor='middle')
    f.text(65,170,'五暂不称；较轻组 {1,2} 加五仍包含两轻球',size=21)
    f.text(65,280,'三已知正常，只补左盘，不加入真实候选',size=21)
    f.text(65,335,'平衡后：左候选 {1}，右候选 {2,5}，各有一个',size=21)
    f.text(65,390,'再称二对五，右轻；最终升序提交一、五',size=21)
    save('P7579',f,'盘内数字是球编号。每次两侧个数相等，质量差只来自轻球数，不把补盘的正常球误当候选。')

    f=Figure('两段都含原点：比较选中编号集合的最小差异',400)
    coords=[-10,-5,0,5,10];ids=[2,1,3,4,5]
    for i,(x,pid) in enumerate(zip(coords,ids)):
        px=100+i*140;f.circle(px,120,pid);f.text(px,175,x,GRAY,size=21,anchor='middle')
    f.text(60,75,'圆内为编号，下方为真实坐标；编号三有礼物',size=21)
    f.line(100,220,380,220,BLUE,width=7);f.text(475,227,'{1,2,3}',BLUE,size=23)
    f.line(240,280,520,280,GREEN,width=7);f.text(565,287,'{1,3,4}',GREEN,size=23)
    f.text(65,345,'对称差为 {2,4}，最小编号二属于蓝色方案',size=22)
    f.text(65,385,'蓝色路线按坐标输出 2 1 3；集合比较与访问次序不同',size=21)
    save('P10445',f,'两条线都是宽十的实际坐标区间，往返各需二十；选中集合交集 {1,3} 抵消，只比较两侧剩余编号。')

    f=Figure('允许双人同时回根，阈值一就能会合',370)
    f.circle(380,110,'根');f.text(430,117,'(0,0)',size=22)
    f.circle(160,260,'甲',GREEN);f.text(60,320,'(10,0)',GREEN,size=22)
    f.circle(600,260,'乙',RED);f.text(560,320,'(10,1)',RED,size=22)
    f.line(365,130,180,240,BLUE,width=5);f.line(395,130,580,240,BLUE,width=5)
    f.text(195,180,'通道长 100',BLUE,size=20);f.text(475,180,'通道长 101',BLUE,size=20)
    f.line(185,260,575,260,GRAY,dash=True);f.text(380,290,'起点距离平方 1',GRAY,size=20,anchor='middle')
    f.text(70,355,'两人同一步到根：后续距离零；活动路径总长 201',size=21)
    save('P13824',f,'实线是树上的通道，虚线只表示两人位置间的距离，不能当成额外树边。图形布局表示树结构，坐标数值写在节点旁。')
    f.parts=[part.replace('x="195" y="180"','x="135" y="175"').replace('x="475" y="180"','x="490" y="175"') for part in f.parts]
    save('P13824',f,'实线是树上的通道，虚线只表示两人位置间的距离，不能当成额外树边。图形布局表示树结构，坐标数值写在节点旁。',filename='P13824-readable')

    f=Figure('秘密串 01001：前缀 01 对数增量确定新字符',345)
    f.text(35,110,'位置',size=22);f.row([1,2,3,4,5],80,x=165,width=108)
    f.text(35,180,'字符',size=22);f.row([0,1,0,0,1],150,x=165,width=108)
    f.text(35,250,'前缀对数',size=20);f.row([0,1,1,1,4],220,x=165,width=108,colors={4:GREEN})
    f.text(55,320,'末位增加三对：此前恰有三个零，所以新字符是一',size=22)
    save('CF2037E',f,'每个计数来自该位置结束的完整前缀。首次整串回复四在最后复用，图中长度一的零只作解释，不发非法询问。')

    for spec in specs:
        if spec.pid not in figures:continue
        key,data,caption=figures[spec.pid];spec.images[key]=data;spec.images.update(history.get(spec.pid,{}))
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        head,separator,tail=spec.detail.partition('\n\n');spec.detail=head+block+(separator+tail if separator else '')
        spec.brief+=block
