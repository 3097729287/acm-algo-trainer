// Offline content migration. Code is parsed/formatted as text and never run.
import {readFile,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {join} from 'node:path';
import {unified} from 'unified';
import remarkParse from 'remark-parse';
import {cppLanguage} from '@codemirror/lang-cpp';
import {editorialLanguage,normalizeEditorialCode} from '../src/lib/editorialCode.js';

const [input,output,toolRoot]=process.argv.slice(2);
if(!input||!output||!toolRoot)throw Error('Usage: node scripts/standardize-editorial-code.mjs input.json output.json formatter-directory');
const hash=value=>createHash('sha256').update(value).digest('hex');
const run=(command,args,input)=>new Promise((resolve,reject)=>{
 const child=execFile(command,args,{encoding:'utf8',windowsHide:true,timeout:5000,maxBuffer:131072},(error,out,err)=>error?reject(Error(err.slice(0,500)||error.message)):resolve(out));
 child.stdin.on('error',()=>{});child.stdin.end(input);
});
const manifest=JSON.parse(await readFile(new URL('../../backend/resources/code-formatters.json',import.meta.url),'utf8'));
for(const tool of Object.values(manifest.tools)){
 const bytes=await readFile(join(toolRoot,tool.fileName));
 if(bytes.length!==tool.bytes||hash(bytes)!==tool.sha256)throw Error('Unverified formatter: '+tool.name);
}

// Compare lexical tokens, including strings and comments, independently of the
// formatter. Ignore only whitespace outside tokens and block-comment margins.
function cppTokens(source){
 const tokens=[],closers=new Set(),cursor=cppLanguage.parser.parse(source).cursor();let i=0;
 do{if(cursor.name==='>'&&cursor.node.parent?.name==='TemplateArgumentList')closers.add(cursor.from);}while(cursor.next());
 while(i<source.length){
  const rest=source.slice(i);
  if(/^\s/.test(rest)){i++;continue;}
  let token;
  if(rest.startsWith('//'))token=rest.match(/^\/\/[^\r\n]*/)[0].trimEnd();
  else if(rest.startsWith('/*')){
   const end=source.indexOf('*/',i+2);if(end<0)throw Error('Unclosed comment');
   token=source.slice(i,end+2);
  }else{
   const raw=rest.match(/^(?:u8|u|U|L)?R"([^ ()\\\t\r\n]{0,16})\(/);
   const string=rest.match(/^(?:u8|u|U|L)?(["'])/);
   if(raw){
    const delimiter=')'+raw[1]+'"',end=source.indexOf(delimiter,i+raw[0].length);
    if(end<0)throw Error('Unclosed raw string');
    token=source.slice(i,end+delimiter.length);
   }else if(string){
    let end=i+string[0].length;
    for(;end<source.length;end++){if(source[end]==='\\')end++;else if(source[end]===string[1]){end++;break;}}
    token=source.slice(i,end);
   }else if(closers.has(i))token='>';
   else token=rest.match(/^[A-Za-z_$][\w$]*|^(?:\d|\.\d)(?:[eEpP][+-]|[\w.])*|^(?:<=>|>>=|<<=|->\*|\.\.\.|::|\+\+|--|->|<<|>>|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|\/=|%=|&=|\|=|\^=|##)|^./s)[0];
  }
  // Advance by the original comment bytes, including insignificant trailing space.
  const length=rest.startsWith('//')?rest.match(/^\/\/[^\r\n]*/)[0].length:token.length;
  tokens.push(token.startsWith('/*')?token.replace(/\n[ \t]*/g,'\n').replace(/[ \t]+\n/g,'\n'):token);i+=length;
 }
 return tokens;
}

const documents=JSON.parse(await readFile(input,'utf8')),parser=unified().use(remarkParse),jobs=new Map();
function proseTree(node){
 const result={};
 for(const [key,value]of Object.entries(node)){
  if(key==='position')continue;
  result[key]=key==='children'?value.map(proseTree):value;
 }
 if(node.type==='code'){
  const language=editorialLanguage(node.lang?'language-'+node.lang:'',node.value);
  if(language){result.lang=language;result.value='<formatted-code>';}
 }
 return result;
}
const records=[],issues=[];let blocks=0;
for(const document of documents){
 const edits=[];
 function visit(node){
  if(node.type==='code'){
   const language=editorialLanguage(node.lang?'language-'+node.lang:'',node.value);
   if(!language)return;
   const raw=document.markdown.slice(node.position.start.offset,node.position.end.offset);
   const opener=raw.match(/^(`{3,}|~{3,})([^\r\n]*)(\r?\n)/);
   if(!opener)return; // Indented code has no explicit language contract.
   const last=raw.lastIndexOf('\n')+1,closing=raw.slice(last);
   const close=closing.match(/^([ \t>]*)(`{3,}|~{3,})[ \t]*$/);
   if(!close||close[2][0]!==opener[1][0]||close[2].length<opener[1].length){issues.push({document:document.id,line:node.position.start.line,reason:'Unclosed fence'});return;}
   const original=node.value+'\n',normalized=normalizeEditorialCode(original,language);
   const key=hash(language+'\0'+normalized);
   if(!jobs.has(key))jobs.set(key,{language,original:normalized,occurrences:0});
   jobs.get(key).occurrences++;blocks++;
   edits.push({from:node.position.start.offset,to:node.position.end.offset,key,opener:opener[1]+(language==='cpp17'?'cpp':'python')+(node.meta?' '+node.meta:''),prefix:close[1],closing});
  }
  for(const child of node.children||[])visit(child);
 }
 visit(parser.parse(document.markdown));records.push({...document,edits});
}
let complete=0;const pending=[...jobs.values()];
async function worker(){
 while(pending.length){
  const job=pending.shift(),tool=manifest.tools[job.language];
  try{
   if(Buffer.byteLength(job.original)>65536)throw Error('Code exceeds the formatter limit');
   const args=job.language==='cpp17'?['--assume-filename=main.cpp','--fail-on-incomplete-format','--style={BasedOnStyle: LLVM, IndentWidth: 4, ColumnLimit: 100, SortIncludes: Never, ReflowComments: false, FixNamespaceComments: false, BreakStringLiterals: false}']:['format','--isolated','--no-cache','--stdin-filename=main.py','--line-length=100','--target-version=py313','--config',"format.quote-style='preserve'",'-'];
   let formatted=job.original,stable=false;
   // Splitting a one-line branch can change the next pass's comment alignment.
   // Require a fixed point so running this migration again changes nothing.
   for(let pass=0;pass<4;pass++){
    const next=await run(join(toolRoot,tool.fileName),args,formatted);
    if(next===formatted){stable=true;break;}formatted=next;
   }
   if(!stable)throw Error('Formatter did not reach a stable layout');
   if(!formatted.trim())throw Error('Empty formatter output');
   if(job.language==='cpp17'&&JSON.stringify(cppTokens(job.original))!==JSON.stringify(cppTokens(formatted)))throw Error('Lexical token comparison failed');
   if(job.language==='python3'){
    await run('python',['-c','import ast,json,sys,tokenize,io; a,b=json.load(sys.stdin); assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b)); tokens=lambda s:[t.string for t in tokenize.generate_tokens(io.StringIO(s).readline) if t.type in (tokenize.STRING,tokenize.COMMENT)]; assert tokens(a)==tokens(b)'],JSON.stringify([job.original,formatted]));
   }
   job.formatted=formatted;
  }catch(error){job.formatted=job.original;job.error=error.message;}
  complete++;if(complete%500===0)console.log(JSON.stringify({phase:'format',complete,total:jobs.size}));
 }
}
await Promise.all(Array.from({length:4},worker));
const result=[];
for(const record of records){
 let markdown=record.markdown;
 for(const edit of record.edits.toReversed()){
  const body=jobs.get(edit.key).formatted.replace(/\n$/,'').split('\n').map(line=>edit.prefix+line).join('\n')+'\n';
  markdown=markdown.slice(0,edit.from)+edit.opener+'\n'+body+edit.closing+markdown.slice(edit.to);
 }
 if(JSON.stringify(proseTree(parser.parse(record.markdown)))!==JSON.stringify(proseTree(parser.parse(markdown))))throw Error('Prose or Markdown structure changed: '+record.id);
 result.push({id:record.id,markdown});
}
const failures=[...jobs].filter(([,job])=>job.error).map(([id,job])=>({id,reason:job.error,occurrences:job.occurrences,code:job.original}));
const report={documents:documents.length,changedDocuments:result.filter((row,i)=>row.markdown!==documents[i].markdown).length,blocks,uniqueBlocks:jobs.size,changedUniqueBlocks:[...jobs.values()].filter(job=>job.original!==job.formatted).length,proseAndStructurePreserved:true,failures,issues};
await writeFile(output,JSON.stringify({documents:result,report}));
console.log(JSON.stringify({...report,failures:failures.map(({code,...row})=>row)}));
