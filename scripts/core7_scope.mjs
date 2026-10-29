import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {organizeTrainingLists} from '../frontend/src/lib/trainingListCatalog.js';
import {buildTrainingCurriculum,filterTrainingListsScope} from '../frontend/src/lib/trainingCurriculum.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.join(root,'.backups/core7-editorials-20261030');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const initial=read(path.join(out,'scope.json'));
const initialPath=path.join(out,'initial-raw-scope.json');
if(!fs.existsSync(initialPath))fs.writeFileSync(initialPath,JSON.stringify(initial,null,2)+'\n');
const rows=read(path.join(out,'runtime-rows.json'));
const byId=new Map(rows.map(r=>[r.id,r]));
const lists=read(path.join(root,'data/library/training_lists.json'));
const units=buildTrainingCurriculum(filterTrainingListsScope(organizeTrainingLists(lists),rows),rows).filter(l=>/^0[1-7] /.test(l.topicPath[0]));
const defaults=new Set(read(path.join(root,'data/library/solutions.json')).map(r=>r.problem_id));
const detailed=new Set(read(path.join(root,'data/library/detailed_solutions.json')).map(r=>r.problem_id));
const authored=read(path.join(out,'authored.json')),done=new Set(authored.map(r=>r.problemId));
const notesPath=path.join(root,'data/core7-editorials/notes.json');
const notes=fs.existsSync(notesPath)?read(notesPath):{};
let scope=units.flatMap(l=>l.problems.map(p=>{
  const row=byId.get(p.problemId)||rows.find(r=>r.url===p.url);
  return {stage:l.topicPath[0],unit:l.title,id:row.id,title:row.title,url:row.url,difficulty:row.difficulty,knowledge:row.knowledge,
          default:defaults.has(row.id),detailed:detailed.has(row.id),reviewed:done.has(row.id)};
}));
const pinned=path.join(root,'data/core7-editorials/requested-roster.json');
if(fs.existsSync(pinned)){
  const sourceRows=new Map(read(path.join(root,'data/library/problems.json')).map(r=>[r.id,r.encoded]));
  scope=read(pinned).map(p=>{
    const row=byId.get(p.id)||rows.find(r=>r.url===p.url)||sourceRows.get(p.id);if(!row)throw Error('Missing roster identity '+p.id);
    return {...p,title:row.title,difficulty:row.difficulty,knowledge:row.knowledge,default:defaults.has(p.id),detailed:detailed.has(p.id),reviewed:done.has(p.id)};
  });
}
scope=scope.map(entry=>notes[entry.id]?{...entry,reviewNote:notes[entry.id]}:entry);
fs.writeFileSync(path.join(out,'scope.json'),JSON.stringify(scope,null,2)+'\n');
const report={scopeVersion:fs.existsSync(pinned)?'2026-10-30-screenshot-verified-610':'2026-10-30-runtime-curriculum',requestedStages:7,totalProblems:scope.length,
  authoredProblems:done.size,authoredMethods:authored.length,authoredArticles:authored.length*2,
  hasBothVariants:scope.filter(p=>p.default&&p.detailed).length,missingVariants:scope.filter(p=>!p.default||!p.detailed).length,
  pendingStandardReview:scope.filter(p=>!p.reviewed).length,complete:false,
  stages:[...new Set(scope.map(p=>p.stage))].map(stage=>({stage,total:scope.filter(p=>p.stage===stage).length,reviewed:scope.filter(p=>p.stage===stage&&p.reviewed).length})),
  problems:scope};
fs.writeFileSync(path.join(root,'data/core7-editorials/progress.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(Object.fromEntries(Object.entries(report).filter(([key])=>!['problems','stages'].includes(key)))));
