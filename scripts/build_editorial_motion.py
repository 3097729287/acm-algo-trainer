"""Generate reviewed, self-contained SVG teaching animations (no library writes)."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
from editorial_motion_assets import ROOT,PREFIX
from editorial_motion_sequences import sequence_clips
from editorial_motion_graphs import graph_clips
from editorial_motion_contests import contest_clips

def all_clips():return sequence_clips()+graph_clips()+contest_clips()

def main():
 clips=all_clips();assert len(clips)==27
 target=ROOT/'docs/editorial-motions/assets';records=[]
 for clip in clips:
  path=clip.export(target);tree=ET.fromstring(path.read_bytes())
  assert len(tree.findall('{http://www.w3.org/2000/svg}g'))==len(clip.steps)
  assert not any(node.tag.rsplit('}',1)[-1] in {'script','foreignObject','image','a'} for node in tree.iter())
  for step in clip.steps:
   import base64
   ET.fromstring(base64.b64decode(step['image'][len(PREFIX):]))
  records.append({'id':clip.key,'problemId':clip.pid,'title':clip.title,'reason':clip.reason,'after':clip.after,'asset':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'steps':len(clip.steps),'input':clip.input,'expected':clip.expected})
 source=ROOT/'data/editorial-motions.json';source.write_text(json.dumps({'version':1,'cases':records},ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf8')
 work=ROOT/'.backups/editorial-motion-20261108';work.mkdir(parents=True,exist_ok=True)
 (work/'models.json').write_text(json.dumps([{'id':c.key,'problemId':c.pid,**c.model()} for c in clips],ensure_ascii=False),encoding='utf8')
 print(json.dumps({'clips':len(clips),'steps':sum(len(c.steps) for c in clips),'bytes':sum((ROOT/r['asset']).stat().st_size for r in records)},ensure_ascii=False))

if __name__=='__main__':main()
