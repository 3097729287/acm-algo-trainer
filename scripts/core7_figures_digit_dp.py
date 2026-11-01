"""Literal decimal digits, binary blocks and finite prefixes for each problem."""
import base64,hashlib,json
from editorial_figures import Figure,BLUE,RED,GREEN,GRAY
from core7_authoring import ROOT,OUT,roster_entries

def lesson_figures(directory):
    f=Figure('不超过二进制 101，禁止相邻两个 1，零不计',400)
    f.row(['000','001','010','011','100','101'],105,x=35,width=115,colors={0:GRAY,1:GREEN,2:GREEN,3:RED,4:GREEN,5:GREEN})
    for i,x in enumerate([0,1,2,3,4,5]):f.text(91+i*115,205,x,size=24,anchor='middle')
    f.text(45,285,'001 与 010 的占位零不属于实际表示',size=23)
    f.text(45,350,'合法正整数：1、2、4、5，共 4 个',GREEN,size=24)
    f.save('digit-dp',directory)

    f=Figure('同一批前缀：整数和与数位和的更新不同',410)
    for y,old,new in [(100,'1','13'),(220,'2','23')]:
        f.box(80,y,140,60,old,BLUE);f.line(225,y+30,440,y+30,GREEN);f.text(330,y+15,'接上 3',GREEN,size=23,anchor='middle');f.box(450,y,180,60,new,GREEN)
    f.text(45,345,'数量 2；整数和 13+23=36；数位和 1+3+2+3=9',size=22)
    f.text(45,390,'前者旧和乘十，后者旧和不乘十',RED,size=22)
    f.save('digit-aggregation',directory)

    f=Figure('用 X²=X+1 约简幂，再乘初值 s₀=0、s₁=1',450)
    for y,power,polynomial,value in [(90,'X⁰','1',0),(155,'X¹','X',1),(220,'X²','1+X',1),(285,'X³','1+2X',2),(350,'X⁴','2+3X',3)]:
        f.box(60,y,130,48,power,BLUE);f.text(290,y+32,polynomial,size=24,anchor='middle');f.line(390,y+24,495,y+24,GREEN);f.box(525,y,150,48,'s = '+str(value),GREEN)
    f.text(45,435,'每次高次替换都对应同一条线性递推等式',size=22)
    f.save('linear-recurrence',directory)

def attach_figures(specs):
    lesson_figures(ROOT/'docs/foundations/assets')
    pictures={};roster=roster_entries()
    previous={r['problem_id']:r.get('images',{}) for r in json.loads((ROOT/'data/library/solutions.json').read_text(encoding='utf-8'))}
    def save(pid,f,caption):
        p=f.save(pid,OUT/'figures');data='data:image/svg+xml;base64,'+base64.b64encode(p.read_bytes()).decode();key='assets/core7/'+pid+'.svg';old=previous.get(roster[pid]['id'],{})
        if key in old and old[key]!=data:key=key[:-4]+'-'+hashlib.sha256(data.encode()).hexdigest()[:10]+'.svg'
        pictures[pid]=(key,data,caption,old)

    f=Figure('相邻差至少二：占位零与实际零分开处理',435)
    for y,word,label,colors in [(90,'135','差 2、2，合法',{0:GREEN,1:GREEN,2:GREEN}),(205,'132','差 2、1，不合法',{2:RED}),(320,'0013','占位零不比较',{0:GRAY,1:GRAY,2:GREEN,3:GREEN})]:
        f.row(list(word),y,x=50,width=85,colors=colors);f.text(430,y+32,label,size=22)
    f.text(45,410,'开始之后的 0 仍要与前一位比较，例如 100 不合法',size=22)
    save('P2657',f,'数字135与132只差末位却合法性不同；0013代表13，占位零没有与真实首位形成相邻对。')

    f=Figure('三至八中，二进制一的数量为奇数的是 4、7、8',585)
    for x,label in [(90,'整数'),(280,'二进制'),(470,'一的个数'),(655,'计入值')]:f.text(x,85,label,size=22,anchor='middle')
    for i,n in enumerate(range(3,9)):
        y=140+i*60;color=GREEN if n.bit_count()%2 else GRAY
        for x,value in [(90,n),(280,bin(n)[2:]),(470,n.bit_count()),(655,n if n.bit_count()%2 else '—')]:f.text(x,y,value,color,size=25,anchor='middle')
    f.text(45,555,'答案是整数和 4+7+8=19，不是个数或数位和',size=23)
    save('P14074',f,'原样例区间逐个核对；三个合格整数分别为4、7、8，其中7虽然有三个一也仍是奇数。')

    f=Figure('页码 1 至 13：个位贡献 51，十位贡献 4',380)
    f.row(range(1,14),100,x=35,width=53,colors={i:GREEN if i>=9 else BLUE for i in range(13)})
    f.text(45,230,'个位：1+…+9，再加 0+1+2+3，得到 51',size=23)
    f.text(45,290,'十位：只有 10、11、12、13，各贡献 1',GREEN,size=23)
    f.text(45,350,'数位和总计 51+4=55',BLUE,size=25)
    save('P1836',f,'完整个位周期后只走到数字三；十至十三的十位另计四，不是把页码数值相加。')

    f=Figure('三人的全部合法队伍序列，122 排第四',430)
    for i,word in enumerate(['111','112','121','122','123']):
        color=GREEN if word=='122' else BLUE;f.box(45+i*140,115,125,60,word,color);f.text(107+i*140,230,'第 '+str(i+1)+' 天',color,size=22,anchor='middle')
    f.text(45,310,'新队伍编号只能是前缀最大编号加一',size=23)
    f.text(45,380,'122 前面的首次不同位置各只计一次，排名再加一',size=22)
    save('P4798',f,'这是原三人样例的全部五种分队记录，固定编号方式排除了对队伍名称任意重命名的重复。')

    f=Figure('区间 24 至 69：两个数位和前缀相减',375)
    f.box(45,115,210,65,'1 … 23',GRAY);f.box(270,115,440,65,'24 … 69',GREEN)
    f.text(150,230,'F(23)=114',GRAY,size=24,anchor='middle');f.text(485,230,'本段数位和 411',GREEN,size=24,anchor='middle')
    f.line(45,80,710,80,BLUE);f.text(380,65,'F(69)=525',BLUE,size=24,anchor='middle')
    f.text(45,325,'525−114=411；低位段包含右端点，所以有 low+1',size=22)
    save('P4999',f,'原样例24至69的两个完整前缀分别为525与114，这些量均为数位和之和。')

    f=Figure('28 至 31 的数位和分别为 10、11、3、4',355)
    f.row([28,29,30,31],100,x=65,width=160)
    f.row([10,11,3,4],220,x=65,width=160,colors={i:GREEN for i in range(4)})
    f.text(45,335,'四个数的数位和相加：10+11+3+4=28',size=24)
    save('SP17247',f,'与原样例一致，跨过整十边界后数位和会下降，不能按整数值连续累加。')

    f=Figure('统计零出现次数时，只算实际写出来的零',380)
    f.text(45,105,'整数 7',size=23);f.row(list('007'),140,x=65,width=95,colors={0:GRAY,1:GRAY,2:BLUE});f.text(410,175,'占位零均不计',GRAY,size=24)
    f.text(45,255,'整数 100',size=23);f.row(list('100'),280,x=65,width=95,colors={0:BLUE,1:GREEN,2:GREEN});f.text(410,315,'实际零有两个',GREEN,size=24)
    save('UVA1640',f,'同样的字符零是否计入由实际表示决定；七的补位零不计，一百的十位零与个位零分别计数。')

    f=Figure('223 的不同重排只有三种，只有 232 被四整除',360)
    for x,word,ok in [(55,'223',False),(290,'232',True),(525,'322',False)]:
        color=GREEN if ok else GRAY;f.box(x,115,180,65,word,color);f.text(x+90,245,'余数 '+str(int(word)%4),color,size=24,anchor='middle')
    f.text(45,325,'两个 2 不编号；交换它们不会产生新的整数',size=23)
    save('CF401D',f,'原样例的三个多重集合排列逐个求余数；每个数码种类只走一次选择，不乘相同副本数量。')

    f=Figure('1020 可删零：全部七个更小结果按长度分类',405)
    for y,label,values in [(100,'删两个零',['12','21']),(210,'删一个零',['102','120','201','210']),(320,'不删零',['1002'])]:
        f.text(35,y+32,label,size=22);f.row(values,y,x=220,width=120,colors={i:GREEN for i in range(len(values))})
    save('P2518',f,'三种长度互不重复，数1020自身不计，首位为零的排列也没有加入。')

    f=Figure('三连可以出现在中途，但同一号码不能兼有四和八',440)
    for y,word,label,color in [(100,'14444101000','有三连；无 8',GREEN),(220,'14444444448','虽有三连，但兼有 4、8',RED),(340,'10010012022','没有三连',GRAY)]:
        f.box(45,y,350,55,word,color);f.text(420,y+35,label,color,size=21)
    save('P4124',f,'三个实际十一位号码分别展示三连成功、四八冲突和从未形成三连；换数字不清除已经成功的标记。')

    f=Figure('10 至 19 中，10、12、18 可被各自数位和整除',395)
    for i,n in enumerate([10,11,12,18]):
        x=40+i*180;color=GREEN if n%sum(map(int,str(n)))==0 else RED
        f.box(x,100,150,55,n,color);f.text(x+75,220,'位和 '+str(sum(map(int,str(n)))),color,size=23,anchor='middle');f.text(x+75,285,'余数 '+str(n%sum(map(int,str(n)))),color,size=23,anchor='middle')
    f.text(45,365,'先固定最终位和 3：前缀 1 与后缀 2 合成 12',size=22)
    save('P4127',f,'原样例合格者为10、12、18；11的位和二不能整除十一，当前前缀位和不能拿来替代最终模数。')

    f=Figure('原样例五个三进制数的价值之和是八',475)
    f.row(['1','2','10','11','12'],100,x=55,width=130)
    f.row([1,1,2,2,2],195,x=55,width=130,colors={i:GREEN for i in range(5)})
    f.text(45,290,'每项最长等差段长度：1+1+2+2+2=8',size=23)
    f.row([1,3,5,2,0],345,x=55,width=130,colors={0:GREEN,1:GREEN,2:GREEN,3:GRAY,4:GRAY})
    f.text(45,450,'另一组数码：1、3、5 的相邻差都为 2，最长段为 3',size=22)
    save('P5128',f,'上半逐个列出n为五、k为三的原样例；下半仅示意连续等差数码段，不把整数字面值当等差数列。')

    f=Figure('2 至 12 的六个圆数，零数均不小于一数',570)
    for x,label in [(100,'十进制'),(300,'二进制'),(500,'零数'),(655,'一数')]:f.text(x,85,label,size=22,anchor='middle')
    for i,n in enumerate([2,4,8,9,10,12]):
        bits=bin(n)[2:];y=150+i*60
        for x,value in [(100,n),(300,bits),(500,bits.count('0')),(655,bits.count('1'))]:f.text(x,y,value,GREEN,size=24,anchor='middle')
    f.text(45,545,'真实首位为 1，它前面的占位零不参与计数',size=22)
    save('P6218',f,'原样例的六个合格正整数全部列出，包括零一相等的1001、1010、1100。')

    f=Figure('l=10，重复两段，上界1010，相邻一数之和至多二',500)
    for y,blocks,label,color in [(95,['10','10'],'1+1=2，且等于上界',GREEN),(205,['00','11'],'0+2=2，且小于上界',GREEN),(315,['01','11'],'1+2=3，超过相邻限制',RED),(425,['11','00'],'2+0=2，但超过上界',RED)]:
        f.row(blocks,y,x=35,width=125,colors={0:color,1:color});f.text(315,y+33,label,color,size=22)
    save('P14084',f,'两个限制分别检查：0011可以含一个有两个一的段，0111违反邻段总数，1100则只违反上界比较。')

    f=Figure('未出现的数字不要求补齐，出现过的按各自奇偶检查',420)
    for y,word,label,color in [(90,'77','奇数码 7 出现两次',GREEN),(180,'211','偶数码 2 一次，奇数码 1 两次',GREEN),(270,'6222','偶数码 6 一次，2 三次',GREEN),(360,'662','偶数码 6 出现两次，不合法',RED)]:
        f.box(35,y,140,45,word,color);f.text(210,y+31,label,color,size=23)
    save('SP10606',f,'三个原例子合格，662中的数码六是正偶次；未出现与正偶次在状态上必须区别。')

    f=Figure('前七个斐波那契表示共二十一个字符，十个一',390)
    words=['1','10','100','101','1000','1001','1010'];x=50
    for number,word in enumerate(words,1):
        start=x;f.row(list(word),145,x=x,width=30,colors={i:GREEN if c=='1' else GRAY for i,c in enumerate(word)})
        x+=30*len(word);f.text((start+x)/2,240,number,size=22,anchor='middle');f.line(x-1,125,x-1,205,BLUE)
    f.text(45,310,'每组首位 1 已计入；组内都没有相邻两个 1',size=23)
    f.text(45,365,'21 个字符：1|10|100|101|1000|1001|1010',size=22)
    save('UVA1652',f,'原样例N为21恰好截在第七个表示末尾；相邻不同表示之间可以出现两个一，不违反各个表示自身的规则。')

    f=Figure('d=6，区间10至99中共有八个满足条件的偶数',375)
    values=[16,26,36,46,56,76,86,96];f.row(values,105,x=40,width=85,colors={i:GREEN for i in range(8)})
    f.text(45,245,'第二位必须是 6；第一位不能是 6，也不能是 0',size=23)
    f.text(45,315,'66 在第一位已违规；这些数都被 m=2 整除',size=23)
    save('CF628D',f,'原第一样例逐个列出八个结果；每个偶数位置都要等于d，不能把“d只出现在偶数位”误读为偶数位可任意。')

    f=Figure('区间10至50，最多一种数码，整数和为110',370)
    f.row([11,22,33,44],110,x=55,width=160,colors={i:GREEN for i in range(4)})
    f.text(45,235,'11+22+33+44=110；重复出现同一数码只算一种',size=22)
    f.text(45,315,'10 含实际数码 1、0 两种；011 只是 11 的补位写法',size=22)
    save('CF1073E',f,'k为一时真正合格的四个整数；数码零在真实开始后必须登记，但前导占位零不能增加种类。')

    for spec in specs:
        if spec.pid not in pictures:continue
        key,data,caption,old=pictures[spec.pid];spec.images.update(old);spec.images[key]=data
        figure='\n\n!['+caption+']('+key+')\n\n';spec.brief=figure+spec.brief;spec.detail=figure+spec.detail
