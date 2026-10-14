"""Collect explicitly attributed public XCPC problems from Luogu, with coverage evidence."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/common')]
from library import LibraryDatabase
from fetch_problem import LG_SECTIONS
import cf_eq

CITIES = dict(zip(
    'Beijing Shanghai Nanjing Hangzhou Shenyang Dalian Changchun Harbin Qingdao Jinan Weihai Yinchuan Xian Xi’an Chengdu Chongqing Kunming Guilin Nanning Wuhan Changsha Xiangtan Zhengzhou Jiaozuo Hefei Xuzhou Xiamen Fuzhou HongKong Macau Macao Shenyang Guangzhou Shenzhen Tianjin Shijiazhuang Baoding Qinhuangdao Mianyang Jiangxi Nanchang Wuhu Kunshan Suzhou Xiangyang'.lower().split(),
    '北京 上海 南京 杭州 沈阳 大连 长春 哈尔滨 青岛 济南 威海 银川 西安 西安 成都 重庆 昆明 桂林 南宁 武汉 长沙 湘潭 郑州 焦作 合肥 徐州 厦门 福州 香港 澳门 澳门 沈阳 广州 深圳 天津 石家庄 保定 秦皇岛 绵阳 江西 南昌 芜湖 昆山 苏州 襄阳'.split()))
PROVINCES = {'SDCPC':'山东','FJCPC':'福建','HNCPC':'湖南','HBCPC':'湖北','ZJCPC':'浙江','JSCPC':'江苏',
             'JXCPC':'江西','GDCPC':'广东','GXCPC':'广西','SCCPC':'四川','SXCPC':'陕西','AHCPC':'安徽',
             'LNCPC':'辽宁','JLCPC':'吉林','HLCPC':'黑龙江','HEBCPC':'河北','HENUCPC':'河南','YNCPC':'云南',
             'GZCPC':'贵州','SXCPC':'陕西','NXPC':'宁夏'}


def group(title):
    match = re.match(r'^\[([^\]]+)\]', title)
    if not match:
        return None
    prefix = match[1]
    year = re.search(r'(?:19|20)\d{2}', prefix)
    if not year:
        return None
    year = int(year[0])
    for code, province in PROVINCES.items():
        if re.match(code + r'\b', prefix, re.I):
            return f'{province}省大学生程序设计竞赛 {year}', year, '省赛', province
    series = re.match(r'(ICPC|CCPC)\s*', prefix, re.I)
    if not series:
        return None
    series = series[1].upper()
    location = re.sub(r'^(ICPC|CCPC)\s*(?:19|20)\d{2}\s*', '', prefix, flags=re.I).strip()
    kind = '邀请赛' if re.search(r'Invitational|邀请|(?:^|\s)I$', location, re.I) else '省赛' if re.search(r'省赛|省.*赛|市赛', location) else '区域赛'
    if re.search(r'WF|World Finals|NAC|Latin|NEERC|SEERC|SWERC|ECNA|NWERC', location, re.I):
        return None
    if re.search(r'Final|EC(?:\s|$)', location, re.I):
        kind = '区域赛'
        place = '亚洲东区决赛' if re.search(r'EC|East', location, re.I) else '总决赛'
    else:
        place = re.sub(r'\s+(R|I|Invitational|Regional|Online|Q)(?:\s+\d+)?$', '', location, flags=re.I)
        place = re.sub(r'(邀请赛|区域赛|重现赛|省赛|市赛|站)$', '', place).strip()
        if not re.search(r'[\u4e00-\u9fff]', place):
            place = CITIES.get(place.replace(' ', '').replace('-', '').lower())
            if not place:
                return None
        if re.search(r'Online|网络|预选', location, re.I):
            return None
    return f'{series} {year} {place}' + ('' if place.endswith('决赛') else kind), year, kind, place


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--database', type=Path, default=ROOT/'data/library.sqlite3')
    args = parser.parse_args(); args.cache.mkdir(parents=True, exist_ok=True)
    def fetch(path):
        cache = args.cache/(hashlib.sha256(path.encode()).hexdigest()+'.json')
        if cache.exists():
            return json.loads(cache.read_text(encoding='utf8'))
        for attempt in range(2):
            try:
                req = Request('https://www.luogu.com.cn'+path, headers={'User-Agent':'Mozilla/5.0 TB public contest archive','x-lentille-request':'content-only'})
                with urlopen(req, timeout=18) as response:
                    payload = json.load(response)
                if payload.get('status') != 200:
                    raise ValueError('Public content unavailable')
                cache.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf8')
                time.sleep(.25)
                return payload
            except Exception:
                if attempt:
                    raise
                time.sleep(1)
    discovered = {}; errors = []
    keywords = ['ICPC', 'CCPC', '邀请赛'] + list(PROVINCES)
    for keyword in keywords:
        try:
            page = 1
            while True:
                data = fetch('/problem/list?'+urlencode({'keyword':keyword,'page':page}))['data']['problems']
                for item in data['result']:
                    grouping = group(item.get('name',''))
                    if grouping:
                        discovered[item['pid']] = (item, grouping)
                if page * data['perPage'] >= data['count']:
                    break
                page += 1
            print(keyword, 'discovered', len(discovered), flush=True)
        except Exception as e:
            errors.append({'source':keyword,'error':type(e).__name__})
    records = []; coverage = {}
    def collect(entry):
        pid, (metadata, (contest, year, kind, place)) = entry
        problem = fetch('/problem/'+pid)['data']['problem']
        if problem.get('pid') != pid:
            raise ValueError('Source identity mismatch')
        content = problem.get('content') or problem.get('contenu') or {}
        body = '\n\n'.join('## '+label+'\n\n'+content[key] for key,label in LG_SECTIONS if content.get(key))
        if len(body) < 30:
            raise ValueError('Incomplete public statement')
        title = re.sub(r'^\[[^\]]+\]\s*', '', metadata['name'])
        identity = 'xcpc-luogu::'+pid; url = 'https://www.luogu.com.cn/problem/'+pid
        difficulty = cf_eq.cf_eq_luogu(problem.get('difficulty'))['cf_eq_rating']
        raw = {'场次':contest,'题号':pid,'题名':title,'知识点':'','难度':str(difficulty) if difficulty is not None else '—','状态':'未做','日期':'','_id':identity,'_url':url,'_platform':'洛谷','_series':'XCPC'}
        encoded = {'id':identity,'contest':contest,'problem':pid,'title':title,'tags':[],'knowledge':'','difficulty':difficulty,'platform':'洛谷','series':'XCPC','contestFamily':'XCPC',
                   'url':url,'source':'xcpc-history','status':'未做','date':'','queue':None,'solutionAvailable':False,'solutionState':'missing',
                   'examYear':year,'examStage':kind,'xcpcYear':year,'xcpcKind':kind,'xcpcPlace':place,'originalTitle':metadata['name'],
                   'collectionSource':url,'collectionNotice':'按原站公开题目收录，原赛总题数与题序未核验；保留原站题号。'}
        samples = [{'name':'样例 '+str(i+1),'input':s[0],'output':s[1]} for i,s in enumerate(problem.get('samples') or []) if len(s)>=2]
        limits = problem.get('limits') or {}; times = limits.get('time') or []; memory = limits.get('memory') or []
        statement = {'id':identity,'title':title,'url':url,'markdown':'# '+metadata['name']+'\n\n来源：[洛谷原题]('+url+')\n\n'+body,
                     'samples':samples,'limits':{'timeMs':int(times[0]) if times else 2000,'memoryMb':max(1,round(memory[0]/1024)) if memory else 256},'statementAvailable':True}
        return raw, encoded, None, statement
    with ThreadPoolExecutor(max_workers=3) as pool:
        jobs = {pool.submit(collect, entry):entry[0] for entry in discovered.items()}
        for i,future in enumerate(as_completed(jobs),1):
            try:
                record = future.result(); records.append(record)
                coverage.setdefault(record[1]['contest'],[]).append(record[1]['problem'])
            except Exception as e:
                errors.append({'source':jobs[future],'error':type(e).__name__})
            if i % 25 == 0:
                print('statements', i, '/', len(jobs), 'saved', len(records), 'missing',len(errors), flush=True)
    database = LibraryDatabase(args.database)
    # The caller uses an isolated copy; preserve any existing source IDs/content.
    existing = {p['url'] for p in database.catalog()}
    owned = {p['id'] for p in database.catalog() if p['encoded'].get('source') == 'xcpc-history'}
    added = [r for r in records if r[1]['url'] not in existing or r[1]['id'] in owned]
    database.import_records(added, {}, {}, {'xcpc_source':'https://www.luogu.com.cn/problem/list'})
    report = {'contests':len(coverage),'problems':len(records),'added':len(added),'coverage':coverage,'missing':errors,
              'notice':'仅收录可核验的公开题目；原赛总题数和原始题序未知时，不宣称完整。'}
    (ROOT/'backend/resources/xcpc-coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','missing')},ensure_ascii=False),flush=True)


if __name__ == '__main__':
    main()
