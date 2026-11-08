"""Inventory problem-specific state changes; cues nominate review, never attach art."""
import collections,json,re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CUES=['路径压缩','回溯','懒标记','单调队列','单调栈','滚动数组','倒序','交换','滑动窗口','双指针','状态转移','旋转','栈顶','删除','区间合并','进位','环上','倍增','拓扑','增广','残量','失配','读写','优先队列']

def main():
 source=ROOT/'data/library';defaults=json.loads((source/'solutions.json').read_text('utf8'));details={r['problem_id']:r for r in json.loads((source/'detailed_solutions.json').read_text('utf8'))};problems={r['id']:r for r in json.loads((source/'problems.json').read_text('utf8'))}
 counts=collections.Counter();records=[]
 for row in defaults:
  pid=row['problem_id'];body=details.get(pid,row)['markdown'];body=re.sub(r'<!-- reusable-foundations:start -->.*?<!-- reusable-foundations:end -->','',body,flags=re.S)
  body=re.sub(r'^```.*?^```\s*$','',body,flags=re.M|re.S)
  evidence={cue:[line.strip()[:260] for line in body.splitlines() if cue in line][:3] for cue in CUES if cue in body}
  counts.update(evidence.keys())
  record=problems.get(pid,{}).get('encoded',{})
  records.append({'id':pid,'title':record.get('title'), 'cues':evidence,'images':list(row.get('images',{}))})
 out=ROOT/'.backups/editorial-motion-20261108';out.mkdir(parents=True,exist_ok=True)
 (out/'audit.json').write_text(json.dumps({'total':len(records),'counts':dict(counts),'articles':records},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'total':len(records),'candidates':sum(bool(r['cues']) for r in records),'counts':counts},ensure_ascii=False))
 wanted={'P1196','P3372','P1714','P1886','P5788','P1048','P1616','P1434','P3379','P4779','P3375','P5357','P1972','P3374','P3373','P2574','P3376','P3386','P3384','P1439','P2858','P4939','P3531','P2161'}
 for r in records:
  if r['id'].removeprefix('luogu-training-') in wanted:print(json.dumps({'id':r['id'],'title':r['title'],'cues':list(r['cues']),'images':r['images']},ensure_ascii=False))

if __name__=='__main__':main()
