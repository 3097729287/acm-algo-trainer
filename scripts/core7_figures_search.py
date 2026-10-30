"""Show actual paths, grid vertices, light-free states and tree cuts."""
import base64
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import OUT


def attach_figures(specs):
    figures={}
    def save(pid,f,caption):
        path=f.save(pid,OUT/'figures');key='assets/core7/'+pid+'.svg'
        figures[pid]=(key,'data:image/svg+xml;base64,'+base64.b64encode(path.read_bytes()).decode(),caption)

    f=Figure('同一格能属于不同路线，标记只限制当前这一条',405)
    paths=[[(0,0),(0,1),(1,1),(1,2)],[(0,0),(1,0),(1,1),(0,1),(0,2),(1,2)]]
    for index,path in enumerate(paths):
        origin=80+index*370
        for r in range(3):
            for c in range(3):
                label='×' if r==2 else ''
                f.box(origin+c*85,90+r*75,81,70,label,GRAY if r==2 else BLUE,fill='#e5e8ed' if r==2 else '#fff')
        color=GREEN if index==0 else RED
        for (r,c),(nr,nc) in zip(path,path[1:]):f.line(origin+c*85+40,125+r*75,origin+nc*85+40,125+nr*75,color,width=5)
        f.circle(origin+40,125,'起',color,radius=18);f.circle(origin+210,200,'终',color,radius=18)
        f.text(origin+125,355,'三步路线' if index==0 else '五步路线',color,size=22,anchor='middle')
    f.text(65,393,'两条路线都用到 (1,2)、(2,2)，都要计数；不是只数最短路',size=21)
    save('P1605',f,'底行三格是障碍；左右两幅是同一张地图上的两条不同路线，每条内部都没有重复格。')

    f=Figure('五步到补给仍存活，六步到补给会先死亡',335)
    f.text(30,108,'五步',size=22);f.row([6,5,4,3,2,'1→6'],75,x=140,width=88,colors={5:GREEN})
    f.text(625,155,'鼠标',GREEN,size=21)
    f.text(30,235,'六步',size=22);f.row([6,5,4,3,2,1,'0 ×'],200,x=140,width=80,colors={6:RED})
    f.text(65,310,'格内是到达后的血量：先扣血，尚大于零才允许补满',size=22)
    save('P2802',f,'每行第一格是六血起点。上行第五步到补给，扣成一后补六；下行第六步先扣成零，不能再拾取。')

    f=Figure('两个三乘三边框重叠，能把四乘三全部染黑',385)
    for origin,center_row,color,label in [(50,1,BLUE,'第一个章'),(290,2,GREEN,'第二个章')]:
        for r in range(4):
            for c in range(3):
                painted=abs(r-center_row)<=1 and (r!=center_row or c!=1)
                f.box(origin+c*60,85+r*55,57,52,'#' if painted else '.',color if painted else GRAY,fill='#edf5ff' if painted else '#fff')
        f.text(origin+85,340,label,color,size=21,anchor='middle')
    for r in range(4):
        for c in range(3):f.box(540+c*60,85+r*55,57,52,'#',RED,fill='#fff3f3')
    f.text(625,340,'并集结果',RED,size=21,anchor='middle')
    f.text(55,376,'某个章的中心，可以由另一个章的边框涂黑',size=22)
    save('CF1059B',f,'三幅图是同一张四行三列棋盘上的两次单独盖章及最终并集，中心不涂不代表目标中心必须为空。')

    f=Figure('aaa 最多用两次：重叠一格比重叠两格更长',355)
    f.text(40,115,'原词',size=22);f.row(['a','a','a'],80,x=200,width=90)
    f.text(40,210,'下一词',size=22);f.row(['a','a','a'],175,x=380,width=90,colors={0:GREEN})
    f.line(425,137,425,170,GREEN,width=4)
    f.text(45,275,'共用第三格的 a，实际结果为 aaaaa，长度五',size=22)
    f.text(45,325,'若共用两格，只得 aaaa；末词与使用次数却完全相同',size=21)
    save('P1019',f,'第二个词的第一格与前词第三格对齐，共用一格；不能用三格重叠吞掉整个词。')

    f=Figure('四个大学排成链：同一配对让各边都达到上界',385)
    x=[100,285,470,655]
    for i in range(3):f.line(x[i],245,x[i+1],245,GRAY,width=5)
    for i,px in enumerate(x):f.circle(px,245,i+1)
    for left,right,y,color in [(0,2,90,BLUE),(1,3,160,GREEN)]:
        f.line(x[left],222,x[left],y,color,width=3);f.line(x[left],y,x[right],y,color,width=3);f.line(x[right],y,x[right],222,color,width=3)
    for i,value in enumerate([1,2,1]):f.text((x[i]+x[i+1])/2,315,str(value)+' 对跨边',size=21,anchor='middle')
    f.text(55,365,'配对 (1,3)、(2,4)，距离各二；边贡献之和 1+2+1=4',size=21)
    save('CF700B',f,'灰线是原树边，蓝绿折线只是标出配对的端点；每条实际路径仍沿原链走，不能把折线长度当距离。')

    f=Figure('中间边切成二加二：四对端点经过它',450)
    xs=[130,290,470,630]
    for i in range(3):f.line(xs[i],130,xs[i+1],130,GRAY,width=5)
    for i,x in enumerate(xs):f.circle(x,130,i+1)
    f.line(380,70,380,205,RED,dash=True)
    f.text(45,220,'跨边点对：(1,3)、(1,4)、(2,3)、(2,4)，共四对',size=21)
    f.text(35,292,'排序后系数',size=20);f.row([3,3,4],260,x=245,width=140)
    f.text(35,362,'所配边权',size=20);f.row([2,3,'5×7=35'],330,x=245,width=140,colors={2:GREEN})
    f.text(55,425,'四个质因子分三组：最大两项合到最大系数，和为 155',size=21)
    save('CF1401D',f,'树上中间边系数是二乘二；下表另按系数排序，不是把原树从左到右的边权误当已排序。')

    f=Figure('在格点上走割线：这一条隔出右上角一格',425)
    origin_x,origin_y,cell=270,85,90
    for r in range(3):
        for c in range(2):f.box(origin_x+c*cell,origin_y+r*cell,cell,cell,'',BLUE,fill='#fff2b8' if (r,c)==(0,1) else '#dff0fc')
    for r in range(4):
        for c in range(3):f.circle(origin_x+c*cell,origin_y+r*cell,'',GRAY,radius=4)
    points=[(360,85),(360,175),(450,175)]
    for (x,y),(nx,ny) in zip(points,points[1:]):f.line(x,y,nx,ny,RED,width=7)
    f.circle(360,85,'起',RED,radius=18);f.circle(450,175,'终',RED,radius=18)
    f.text(40,245,'黄色一格连通',size=21);f.text(40,285,'蓝色五格连通',size=21)
    f.text(475,235,'两部分都接触',size=21);f.text(475,275,'原矩形外边界',size=21)
    f.text(60,405,'红线走的是小格的边，灰点是转弯格点；反过来走仍是同一分法',size=20)
    save('P1790',f,'三行两列的真实方格上，割线从上边界到右边界；这只是样例十五种分法中的一种。')

    f=Figure('一件玩具向右一格：只改变两个相邻格的占用',385)
    for origin,occupied,label in [(80,0,'掩码十进制一'),(450,1,'掩码十进制二')]:
        for r in range(4):
            for c in range(4):
                f.box(origin+c*58,80+r*55,55,52,'●' if 4*r+c==occupied else '',GREEN if 4*r+c==occupied else GRAY,fill='#e5f7ef' if 4*r+c==occupied else '#fff')
        f.text(origin+115,340,label,size=21,anchor='middle')
    f.line(325,175,420,175,RED,width=5);f.text(375,150,'一步',RED,size=21,anchor='middle')
    f.text(50,377,'格编号按行从零开始；最低位对应左上角，不给相同玩具编号',size=20)
    save('P4289',f,'圆点表示玩具，空格表示空位；它从编号零移到编号一，其余十四格与玩具总数都不变。')

    f=Figure('交换两段只改变三处接缝，内部顺序保留',365)
    f.row([0,1,4,5,2,3,6,7],85,x=50,width=82,colors={0:GRAY,7:GRAY,2:RED,3:RED,4:GREEN,5:GREEN})
    for cut in [2,4,6]:f.line(50+cut*82-2,70,50+cut*82-2,153,BLUE,dash=True)
    f.text(60,195,'原断点：1→4、5→2、3→6，恰好三处',size=22)
    f.row([0,1,2,3,4,5,6,7],240,x=50,width=82,colors={0:GRAY,7:GRAY,2:GREEN,3:GREEN,4:RED,5:RED})
    f.text(60,340,'交换 [4,5] 与 [2,3] 后全部有序；灰格是两端哨兵',size=22)
    save('P10488',f,'格中的零与七只用于判断边界，实际书是中间六项；虚线标出本次操作真正改变的三条相邻关系。')

    f=Figure('买油付费，行驶扣油；相同城市不同油量是不同状态',345)
    labels=['(A,0)','(A,1)','(A,2)','(B,0)']
    for i,label in enumerate(labels):f.box(40+i*185,115,145,65,label,BLUE if i<3 else GREEN)
    for i,label in enumerate(['买一：5','买一：5','走长二：0']):
        f.line(185+i*185,147,220+i*185,147,RED,width=4)
        f.line(220+i*185,147,212+i*185,141,RED,width=3);f.line(220+i*185,147,212+i*185,153,RED,width=3)
        f.text(200+i*185,100,label,RED,size=18,anchor='middle')
    f.text(60,245,'容量至少二，A 城每单位油价五；这条路线总费用十',size=21)
    f.text(60,305,'到 A 城但油为零时，还不能执行最后那次行驶',size=22)
    save('UVA11367',f,'每个框写城市与剩油，不是城市与已花费用；箭头上才是本次动作增加的费用，行驶不再付第二次油钱。')

    for spec in specs:
        if spec.pid not in figures:continue
        key,data,caption=figures[spec.pid];spec.images[key]=data
        block='\n\n!['+caption+']('+key+')\n\n'+caption
        head,separator,tail=spec.detail.partition('\n\n');spec.detail=head+block+(separator+tail if separator else '')
        spec.brief+=block
