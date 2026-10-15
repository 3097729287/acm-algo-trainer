"""Chinese event names with explicit locations and preserved competition stages."""
import re

PLACES = {
    'Shanghai':'上海', 'Nanjing':'南京', 'Shenyang':'沈阳', 'Jinan':'济南', 'Kunming':'昆明',
    'Macau':'澳门', 'Macao':'澳门', 'Beijing':'北京', 'Tianjin':'天津', 'Hangzhou':'杭州',
    'Qingdao':'青岛', 'Guilin':'桂林', 'Wuhan':'武汉', 'Zhengzhou':'郑州', 'Jiaozuo':'焦作',
    'Harbin':'哈尔滨', 'Dalian':'大连', 'Changchun':'长春', 'Chengdu':'成都', 'Chongqing':'重庆',
    'Xuzhou':'徐州', 'Weihai':'威海', 'Nanning':'南宁', 'Changsha':'长沙', 'Xiangtan':'湘潭',
    'Hefei':'合肥', 'Xiamen':'厦门', 'Fuzhou':'福州', 'Shenzhen':'深圳', 'Guangzhou':'广州',
    'Shijiazhuang':'石家庄', 'Baoding':'保定', 'Qinhuangdao':'秦皇岛', 'Mianyang':'绵阳',
    'Nanchang':'南昌', 'Wuhu':'芜湖', 'Kunshan':'昆山', 'Suzhou':'苏州', 'Xiangyang':'襄阳',
    'Yinchuan':'银川', 'Xian': '西安', "Xi'an": '西安', 'Hong Kong':'香港', 'Taoyuan':'桃园',
    'Taipei-Hsinchu':'台北新竹', 'Taipei':'台北', 'Hsinchu':'新竹', 'Taiwan':'台湾',
    'Yokohama':'横滨', 'Tsukuba':'筑波', 'Daejeon':'大田', 'Seoul':'首尔', 'Jakarta':'雅加达',
    'Dhaka':'达卡', 'Nakhon Pathom':'佛统', 'Manila':'马尼拉', 'Tehran':'德黑兰',
    'Bangkok':'曼谷', 'Amritapuri':'阿姆里塔普里', 'Kanpur':'坎普尔', 'Kharagpur':'克勒格布尔',
    'Gwalior':'瓜廖尔', 'Chennai':'金奈', 'Coimbatore':'哥印拜陀', 'Kabul':'喀布尔',
    'Hanoi':'河内', 'Danang':'岘港', 'Ho Chi Minh':'胡志明市', 'Japan':'日本', 'India':'印度',
    'Heilongjiang':'黑龙江', 'Xinjiang':'新疆', 'Guangxi':'广西', 'Shandong':'山东',
    'Sichuan':'四川', 'Jiangxi':'江西', 'Liaoning':'辽宁', 'Henan':'河南', 'Shaanxi':'陕西',
    'ShaanXi':'陕西', 'Guangdong':'广东', 'Zhejiang':'浙江', 'Jiangsu':'江苏', 'Hubei':'湖北',
    'Hunan':'湖南', 'Fujian':'福建', 'Anhui':'安徽', 'Hebei':'河北', 'Jilin':'吉林',
    'Yunnan':'云南', 'Guizhou':'贵州', 'Shanxi':'山西', 'Hainan':'海南', 'Ningxia':'宁夏',
}


def xcpc_name(original, year=''):
    text = re.sub(r'\s+', ' ', str(original)).strip()
    if not re.search(r'ICPC|CCPC|Collegiate Programming Contest', text, re.I):
        return None
    match = re.search(r'(?:19|20)\d{2}', text)
    year = match[0] if match else str(year or '')
    series = 'CCPC' if re.search(r'CCPC|China Collegiate Programming', text, re.I) else 'ICPC'
    edition = re.search(r'第\s*(\d+)\s*届', text)
    if not year and edition and series=='ICPC' and '区域' in text:year=str(1975+int(edition[1]))
    if not year and edition and series=='CCPC':year=str(2014+int(edition[1]))
    suffix = '（热身赛）' if re.search(r'Warm.?up|热身', text, re.I) else ''
    if re.search(r'Rematch|重赛',text,re.I):suffix+='（重赛）'
    if re.search(r'Partial|部分题', text, re.I):suffix += '（部分题目）'
    # Ordered from the specific subdivision to its broader parent region.
    cases = [
        (r'World Finals|全球总决赛', '全球总决赛'),
        (r'Asia.?Pacific Championship|亚太.*总决赛', '亚太区总决赛'),
        (r'Asia.?East|EC.?Final|亚洲东区', '亚洲东区决赛'),
        (r'Latin America Championship|Latin American Championship', '拉丁美洲总决赛'),
        (r'Gran Premio de Mexico', '墨西哥大奖赛'),
        (r'Masters Mexico', '墨西哥大师赛'),
        (r'Universidad Nacional de Colombia', '哥伦比亚国立大学程序设计竞赛'),
        (r'Columbia University Local', '哥伦比亚大学校内赛'),
        (r'Bolivia Pre.?National', '玻利维亚全国预选赛'),
        (r'Bolivia National', '玻利维亚全国赛'),
        (r'Thailand National', '泰国全国赛'),
        (r'Malaysia National', '马来西亚全国赛'),
        (r'Syrian Private Universities', '叙利亚私立高校程序设计竞赛'),
        (r'Syrian Collegiate', '叙利亚大学生程序设计竞赛'),
        (r'HIAST', '叙利亚高等应用科技学院程序设计竞赛'),
        (r'ICPC.?de.?Tryst', '印度德里理工学院程序设计竞赛'),
        (r'South America.*Brazil First Phase', '巴西第一轮选拔赛'),
        (r'Brazil Subregional', '巴西分区赛'),
        (r'Latin American Regional', '拉丁美洲区域赛'),
        (r'Nordic Collegiate', '北欧大学生程序设计竞赛'),
        (r'German Collegiate', '德国大学生程序设计竞赛'),
        (r'Swiss.?Subregional|Swiss Subregional', '瑞士分区赛'),
        (r'Southeastern Europe|Southeastern European', '东南欧区域赛'),
        (r'Southwestern Europe|Southwestern European', '西南欧区域赛'),
        (r'Northwestern Europe|Northwestern European', '西北欧区域赛'),
        (r'Central Europe Regional', '中欧区域赛'),
        (r'East Central North America', '北美东中部区域赛'),
        (r'East North America', '北美东部区域赛'),
        (r'Pacific Northwest', '北美太平洋西北区域赛'),
        (r'Southeast Regional', '北美东南区域赛'),
        (r'Greece Regional|Greek Collegiate', '希腊大学生程序设计竞赛'),
        (r'Kyrgyzstan', '吉尔吉斯斯坦分区赛'),
        (r'Southern and Volga', '俄罗斯南部及伏尔加地区赛'),
        (r'Southern Subregional', '俄罗斯南部分区赛'),
        (r'North-Western Russia|North.?Western Russia|Северо-Запада России', '俄罗斯西北分区赛'),
        (r'Central Russia|Центрального подрегиона|Central Quarter', '俄罗斯中部分区赛'),
        (r'East Siberian|Восточно-сибирский', '东西伯利亚分区赛'),
        (r'Moscow Subregional|Московского подрегиона', '莫斯科分区赛'),
        (r'Уральского|Уральского региона|Ural', '乌拉尔分区赛'),
        (r'Northern Subregional', '俄罗斯北部分区赛'),
        (r'Northern Eurasia|Northeastern European Regional', '北欧亚区域赛'),
        (r'China Multi-Provincial', '中国多省联合大学生程序设计竞赛'),
        (r'Female Onsite|女生专场', '女生专场'),
    ]
    rest = None
    if re.search(r'Online|网络',text,re.I) and re.search(r'Asia.*(?:EC|East)|亚洲东区|中国区',text,re.I):rest='亚洲东区网络预选赛'
    if '小米' in text:rest='小米网络选拔赛' if re.search(r'Online|网络',text,re.I) else '小米邀请赛决赛'
    # A combined Ural/Northwest qualifier must retain both locations.
    if 'Уральского региона и Северо-Запада' in text:rest = '乌拉尔及俄罗斯西北地区资格赛'
    if rest is None:
        rest = next((name for pattern, name in cases if re.search(pattern, text, re.I)), None)
    if rest is None:
        region = next((chinese for english, chinese in sorted(PLACES.items(), key=lambda item: -len(item[0]))
                       if re.search(re.escape(english), text, re.I)), None)
        region = region or next((place for place in PLACES.values() if place in text), None)
        if region:
            kind = '邀请赛暨省赛' if re.search(r'Provincial', text, re.I) and re.search(r'Invitational', text, re.I) else '省赛' if re.search(r'Provincial|省赛', text, re.I) else '邀请赛' if re.search(r'Invitational|邀请', text, re.I) else '网络赛' if re.search(r'Online|网络', text, re.I) else '区域赛'
            rest = region + kind
        elif re.search(r'National Invitational.*Northeast|Invitational Contest \(Northeast\)', text, re.I):rest = '东北邀请赛'
        elif re.search(r'CCPC.*Final|CCPC.Final|Final.*CCPC', text, re.I):rest = '总决赛'
        elif re.search(r'Online|网络', text, re.I):rest = '网络赛'
    if rest is None:return None
    if re.search(r'Qualif|Квалификац', text, re.I) and '资格' not in rest and '预选' not in rest:rest += '资格赛'
    if re.search(r'Repechaje', text, re.I):rest += '复活赛'
    if re.search(r'Online|网络',text,re.I):
        part=re.search(r'第一场|First.Round|\(I\)|第\s*1\s*场',text,re.I)
        second=re.search(r'第二场|Second.Round|\(II\)|第\s*2\s*场',text,re.I)
        if part:rest+='（第 1 场）'
        elif second:rest+='（第 2 场）'
    round_number = re.search(r'\b([123])(?:ra|da|ta) Fecha\b|Phase\s*(\d+)', text, re.I)
    if round_number:rest += '（第 ' + (round_number[1] or round_number[2]) + ' 轮）'
    division = re.search(r'Div\.\s*(\d)', text, re.I)
    if division:rest += '（第 ' + division[1] + ' 组）'
    return f'{series} {year} {rest}{suffix}'.replace('  ', ' ').strip()
