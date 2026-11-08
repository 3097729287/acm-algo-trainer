import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {organizeTrainingLists} from '../frontend/src/lib/trainingListCatalog.js';
import {buildTrainingCurriculum,filterTrainingListsScope} from '../frontend/src/lib/trainingCurriculum.js';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const out=path.join(root,'.backups/core7-complete-20261108');
fs.mkdirSync(out,{recursive:true});
const navigation=read(path.join(out,'navigation.json'));
const rows=navigation.rows,byId=new Map(rows.map(row=>[row.id,row]));
const lists=organizeTrainingLists(navigation.lists);
const units=buildTrainingCurriculum(filterTrainingListsScope(lists,rows),rows).filter(l=>/^0[1-7] /.test(l.topicPath[0]));
const defaults=new Map(read(path.join(root,'data/library/solutions.json')).map(r=>[r.problem_id,r]));
const detailed=new Map(read(path.join(root,'data/library/detailed_solutions.json')).map(r=>[r.problem_id,r]));
const old=read(path.join(root,'data/core7-editorials/progress.json'));
const reviewed=new Set(old.problems.filter(p=>p.reviewed).map(p=>p.id));
const scope=units.flatMap(unit=>unit.problems.map(p=>{
 const row=byId.get(p.problemId)||rows.find(row=>row.url===p.url);
 return {id:row.id,pid:row.url.split('/').at(-1),title:row.title,url:row.url,
  difficulty:row.difficulty,knowledge:row.knowledge,stage:unit.topicPath[0],unit:unit.title,
  default:defaults.has(row.id),detailed:detailed.has(row.id),reviewed:reviewed.has(row.id)};
}));
const report={total:scope.length,missing:scope.filter(p=>!p.default||!p.detailed),
 stages:[...new Set(scope.map(p=>p.stage))].map(stage=>({stage,total:scope.filter(p=>p.stage===stage).length,missing:scope.filter(p=>p.stage===stage&&(!p.default||!p.detailed)).length})),problems:scope};
fs.writeFileSync(path.join(out,'inventory.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({total:report.total,missing:report.missing.length,stages:report.stages}));
for(const stage of report.stages){
 console.log(stage.stage);
 for(const p of scope.filter(p=>p.stage===stage.stage&&(!p.default||!p.detailed))) console.log(`${p.pid} ${p.title} [${p.difficulty}] ${p.unit}`);
}
