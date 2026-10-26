import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import {createServer} from 'vite';
const vite=await createServer({server:{middlewareMode:true}});
try{
 const {filterRows,progressRows}=await vite.ssrLoadModule('/src/models/workspaceModel.js');
 const records=JSON.parse(await readFile('../data/library/problems.json','utf8'));
 const rows=progressRows(records.map(item=>item.encoded),{training:[],contests:[]});
 const favorites=rows.filter((_,i)=>i%3===0).map(row=>row.id);
 const cases=[['catalogue',{}],['search-abc',{query:'ABC'}],['search-title',{query:rows[Math.floor(rows.length/2)].title}],['search-range',{query:'1200-1800'}],['favorites',{favoritesOnly:true,favorites}],['id-subset',{ids:favorites}],['knowledge',{category:{name:'数学与计数',tags:['数学','数论','组合计数','取模与同余']}}]];
 const results=[];
 for(const [name,filters] of cases){
  const times=[];let result;
  for(let i=0;i<7;i++){const start=performance.now();result=filterRows(rows,filters);times.push(performance.now()-start);}
  results.push({name,rows:result.length,medianMs:Number([...times].sort((a,b)=>a-b)[3].toFixed(3)),minMs:Number(Math.min(...times).toFixed(3)),idsSha256:createHash('sha256').update(JSON.stringify(result.map(row=>row.id))).digest('hex')});
 }
 const report={dataset:'bundled public library',rows:rows.length,node:process.version,results};
 const out='../.backups/local-1416/performance';await mkdir(out,{recursive:true});
 await writeFile(`${out}/${process.argv[2]||'latest'}-frontend.json`,JSON.stringify(report,null,2));console.log(JSON.stringify(report));
}finally{await vite.close();}
