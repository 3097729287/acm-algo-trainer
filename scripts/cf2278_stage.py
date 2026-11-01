"""Stage the six reviewed tasks using the existing public-library pipeline."""
import base64
import hashlib
import json
import re
from cf2278_programs import ROOT, CONTENT, OUT, LETTERS
import three_contests_stage as shared

shared.OUT = OUT

def additions():
    packet = {name:shared.load(CONTENT/(name+'.json')) for name in ['problems','statements','solution_methods','links']}
    for table, variant in [('solutions','default'),('detailed_solutions','detailed')]:
        rows = []
        for p in packet['problems']:
            letter = p['encoded']['problem']
            markdown = (CONTENT/variant/(letter+'.md')).read_text('utf8')
            images = {rel:'data:image/svg+xml;base64,'+base64.b64encode((CONTENT/rel).read_bytes()).decode('ascii')
                      for rel in re.findall(r'!\[[^\]]*\]\((assets/[^)]+)\)',markdown)}
            code = re.findall(r'(?ms)^```cpp\s*\n(.*?)^```',markdown)
            reference = (CONTENT/'programs'/letter/(letter.lower()+'.cpp')).read_text('utf8')
            assert len(code)==1 and code[0].strip()==reference.strip(),letter
            rows.append({'problem_id':p['id'],'markdown':markdown,'images':images,
                         'source_path':f'contest-editorials/div3-1131/{variant}/{letter}.md'})
        packet[table] = rows
    assert len(packet['problems'])==len(LETTERS)==6
    return packet

def seed(packet):
    path = OUT/'packet.sqlite3'
    lib = shared.LibraryDatabase(path)
    wanted = {row['lecture_id'] for row in packet['links']}
    with lib.connection() as db:
        for row in shared.load(ROOT/'data/library/lectures.json'):
            if row['id'] not in wanted:continue
            content=json.dumps(row['content'],ensure_ascii=False)
            db.execute('insert or ignore into lectures values(?,?,?)',(row['id'],content,hashlib.sha256(content.encode()).hexdigest()))
    return shared.insert(path,packet,meta_key='cf2278Content')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    packet=additions();lib=seed(packet)
    assert all(lib.check()[key]==6 for key in ['problems','solutions','detailed_solutions'])
    shared.upgrade_check(packet,lib)
    shared.export_readers(lib,packet)
    shared.text_source(packet)
    shared.dump(OUT/'stage-report.json',{'passed':True,'problems':6,'articles':12,
        'lectureLinks':len(packet['links']),'counts':lib.check(),'textSourceUpdated':True,
        'unrelatedTextRowsPreserved':True,'personalDatabasesModified':False})
    print('Staged 6 problems, 12 articles and',len(packet['links']),'lecture links; local edits/imports preserved.')

if __name__=='__main__':main()
