"""Normalize three legacy articles discovered by the full teaching-format audit.

Retain all existing proofs and every cpp byte. This migration is idempotent.
"""
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import sys
from refresh_editorial_teaching import ROOT, SOURCE, START, STOP, programs


def rank_article(text):
    if '### 1. 左秩、右秩到底是什么？' not in text:return text
    old=programs(text)
    generic=re.search(re.escape(START)+r'.*?'+re.escape(STOP),text,re.S)
    foundation=generic[0] if generic else ''
    text=re.sub(re.escape(START)+r'.*?'+re.escape(STOP),'',text,flags=re.S)
    headings=list(re.finditer(r'^### ([1-8])\. (.+)\n',text,re.M))
    assert len(headings)==8
    title,preamble=text[:headings[0].start()].split('\n',1)
    title=title.replace(' — 详细题解','')
    sections={}
    for i,head in enumerate(headings):
        end=headings[i+1].start() if i+1<len(headings) else len(text)
        sections[int(head[1])]=(head[2],text[head.end():end].strip())
    statement='选择一个最长子序列，每个原元素对它在子序列中的左秩、右秩各有一个禁止区间，两个秩都必须避开对应区间。'
    idea=preamble.strip()+'\n\n'+'\n\n'.join('#### '+sections[i][0]+'\n\n'+sections[i][1] for i in range(1,7))
    result=title+'\n\n### 题意\n\n'+statement+'\n\n'+foundation+'\n\n### 思路\n\n'+idea
    result+='\n\n### 参考代码\n\n'+sections[8][1]
    result+='\n\n### 复杂度\n\n'+sections[7][1]
    result+='\n\n### 易错点\n\n子序列必须保持原输入顺序。最终长度的可行性不保证单调，不能对长度二分；左右秩都按删除后的队伍重新计算。\n\n'
    sys.path.insert(0,str(Path.home()/'.dsh'/'tools'))
    import unify_latex
    result=unify_latex.process(result,{'frags':0,'lt':0,'failed':[]})
    assert programs(result)==old
    return result


def main():
    backup=ROOT/'.backups'/('editorial-legacy-format-'+dt.datetime.now().strftime('%Y%m%d-%H%M%S-%f'))
    def write(path,text):
        if path.read_text(encoding='utf-8-sig')==text:return
        target=backup/str(path.parent).replace(':','').replace('\\','_')/path.name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        path.write_text(text,encoding='utf-8')
    source=SOURCE/'detailed_solutions.json';rows=json.loads(source.read_text('utf-8'))
    for row in rows:
        if row['problem_id']=='Div.2 1112::C':row['markdown']=rank_article(row['markdown'])
    write(source,json.dumps(rows,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    archive=Path('D:/Data/Code/题解')
    path=archive/'Codeforces/Div.2/1112/1112详细题解.md';text=path.read_text('utf-8')
    match=re.search(r'^## C\..*?(?=^## |\Z)',text,re.M|re.S)
    assert match
    text=text[:match.start()]+rank_article(match[0])+text[match.end():]
    write(path,text)
    for rel in ['牛客/周赛/124/124题解.md','牛客/周赛/142/142题解.md']:
        path=archive/rel;text=path.read_text('utf-8')
        text=re.sub(r'(?<!`)(_work/logs/verify_c\.log|verify_f\.log)(?!`)',r'`\1`',text)
        write(path,text)
    print('Normalized the existing Rank Subsequence layout and quoted legacy log paths; cpp blocks preserved.')


if __name__=='__main__':main()
