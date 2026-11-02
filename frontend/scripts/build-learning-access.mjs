import fs from 'node:fs';
import crypto from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {trainingListModel} from '../src/lib/trainingListModel.js';
import {curriculumLevel} from '../src/lib/trainingListAccess.js';
const root=new URL('../../',import.meta.url);
const read=name=>fs.readFileSync(new URL(name,root),'utf8');
const lists=JSON.parse(read('data/library/training_lists.json'));
const rows=JSON.parse(read('data/library/problems.json')).map(row=>row.encoded);
const model=trainingListModel(lists,rows,'algorithm');
const units=model.organized.filter(list=>list.id.startsWith('curriculum:')).map(list=>({id:list.id,stage:list.topicPath.find(part=>/^0[1-9] /.test(part)),level:curriculumLevel(list.topicPath.find(part=>/^0[1-9] /.test(part))),problemIds:[...new Set(model.index.own.get(list.id).map(item=>item.row?.id).filter(Boolean))]}));
const sourceHashes=Object.fromEntries(['data/library/training_lists.json','data/library/problems.json'].map(name=>[name,crypto.createHash('sha256').update(read(name)).digest('hex')]));
const value=JSON.stringify({version:1,sourceHashes,units},null,2)+'\n';
const target=fileURLToPath(new URL('backend/resources/learning-access.json',root));
if(process.argv.includes('--check')){if(fs.readFileSync(target,'utf8')!==value)throw Error('Learning access resource is stale');}
else fs.writeFileSync(target,value);
console.log(JSON.stringify({units:units.length,foundationProblems:new Set(units.filter(unit=>unit.level===1).flatMap(unit=>unit.problemIds)).size}));
