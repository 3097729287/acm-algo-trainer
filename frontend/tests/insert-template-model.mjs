import assert from 'node:assert/strict';
import {readFile,mkdtemp,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
import {runInNewContext} from 'node:vm';
import {insertTemplate,normalizeCppTemplate,templateForDisplay} from '../src/lib/insertTemplate.js';
// Read the actual default literal instead of maintaining a convenient substitute.
const workbench=await readFile('src/app/Workbench.jsx','utf8');
const defaultLiteral=workbench.match(/^const TEMPLATE = ('(?:\\.|[^'\\])*');$/m)?.[1];assert(defaultLiteral,'Workbench exposes its current default literal');
const code=normalizeCppTemplate(runInNewContext(defaultLiteral,Object.create(null),{timeout:100}));
assert(code.includes('using ll = long long;')&&code.includes('ios::sync_with_stdio(false);'));
const template='// long long: explanation stays unchanged\n#include <bits/stdc++.h>\n#include <cassert>\nusing namespace std;\nlong long twice(long long x){return x*2;}\n';
const merged=insertTemplate(code,template);
assert.equal((merged.match(/#include <bits\/stdc\+\+\.h>/g)||[]).length,1);
assert.equal((merged.match(/using namespace std;/g)||[]).length,1);
assert.equal((merged.match(/using ll = long long;/g)||[]).length,1);
assert(merged.indexOf('#include <bits/stdc++.h>')<merged.indexOf('ll twice'));
assert(merged.indexOf('ll twice')<merged.indexOf('int main'));
assert(merged.indexOf('using ll = long long;')<merged.indexOf('ll twice'),'existing aliases must precede all inserted uses');
assert(merged.includes('// long long: explanation stays unchanged'));
const originals='// long long documentation\nconst char *s="long long and #include <vector>";\nconst char *r=R"raw(long long\n#include <set>\n)raw";\nunsigned long long u=0;\nlong long x=1;\n';
const normalized=normalizeCppTemplate(originals);
assert(normalized.includes('const char *s="long long and #include <vector>";'));
assert(normalized.includes('R"raw(long long\n#include <set>\n)raw"'));
assert(normalized.includes('unsigned long long u=0;'));assert(normalized.includes('ll x=1;'));
assert(normalizeCppTemplate('unsigned /* keep */ long long u;\nsigned /* keep */ long long s;').includes('unsigned /* keep */ long long u;\nsigned /* keep */ long long s;'));
assert.equal(normalizeCppTemplate(normalized),normalized,'normalization is idempotent');
assert.match(normalizeCppTemplate("long long n=1'000;\nlong long m=2;"),/ll n=1'000;\nll m=2;/);
assert.match(normalizeCppTemplate('#define ll long long\nlong long n;'),/^#define ll long long\nll n;/);
assert.doesNotMatch(insertTemplate('#define ll long long\nint main(){}',template),/using ll/);
assert.match(normalizeCppTemplate('using ll = /* type note */ long long;\nlong long n;'),/using ll = \/\* type note \*\/ long long;\nll n;/);
assert.throws(()=>insertTemplate('using ll = double;\nint main(){}',template),/已有其它类型定义/);
assert.equal(normalizeCppTemplate('using ll = double;\nlong long n;'),'using ll = double;\nlong long n;');
const macros='#include <vector>\n#if defined(DEBUG)\nint debug=1;\n#endif\n#define f(x) \\\n (x)\nusing namespace std;\nint main(){}';
const macroMerged=insertTemplate(macros,template);assert(macroMerged.indexOf('ll twice')>macroMerged.indexOf('#endif'));assert(macroMerged.indexOf('ll twice')>macroMerged.indexOf(' (x)'));
const commented=insertTemplate('// #include <cassert>\nint main(){}',template);assert(commented.includes('\n#include <cassert>'));
const conditional=insertTemplate('#if 0\n#include <cassert>\n#endif\nint main(){}',template);assert.equal((conditional.match(/#include <cassert>/g)||[]).length,2,'conditional existing includes cannot suppress required headers');
assert.equal(templateForDisplay({builtin:true,language:'python3',code:'x=1'}).code,'x=1');
assert.equal(templateForDisplay({builtin:false,language:'cpp17',code:'long long own;'}).code,'long long own;','private user content is preserved');
const templates=JSON.parse(await readFile('../backend/resources/code-templates.json','utf8')).templates;
const folder=await mkdtemp(path.join(tmpdir(),'tb-template-insertion-'));
try{
 let compiled=0;
 const compile=(source,label)=>{const check=spawnSync('g++',['-std=c++17','-fsyntax-only','-x','c++','-'],{input:source,encoding:'utf8',windowsHide:true,timeout:20000});assert.equal(check.status,0,`${label}: ${check.stderr||check.error}`);compiled++;};
 const prefix='#include <bits/stdc++.h>\nusing namespace std;\n',main='\nint main(){return 0;}\n';
 for(const [name,aliases] of [
  ['using','using ll = long long;'],['typedef','typedef long long ll;'],['macro','#define ll long long\n'],
  ['multiline-using','using ll =\n  long long;'],['multiline-typedef','typedef long long\n  ll;'],
  ['other-aliases','using ll=long long;\nusing Vec = vector<ll>;\ntypedef pair<int,int> Pair;'],
  ['aggregate-typedef','typedef struct { int x; } Point;\nusing ll=long long;'],
 ]){
  const result=insertTemplate(prefix+aliases+main,template);compile(result,name);
  assert(result.indexOf(aliases)<result.indexOf('ll twice'),`${name} stays intact above the insertion`);
 }
 compile(insertTemplate(prefix+'int earlier(){return 0;}\nusing ll = long long;'+main,template),'late alias cannot suppress the new visible declaration');
 compile(insertTemplate(prefix+'using ll = long long;'+main,'using ll =\n long long;\nll twice(ll x){return x*2;}'),'complete multiline payload alias removal');
 compile(normalizeCppTemplate(prefix+'using Count = long long;\ntypedef long long Other;\n'+main),'new ll precedes other aliases rewritten to ll');
 compile(normalizeCppTemplate(prefix+'struct Local { using ll=long long; };\nlong long f(){return 0;}\n'+main),'nested ll never suppresses the global alias');
 for(const item of templates.filter(item=>item.language==='cpp17'))for(const variant of ['code','contestCode']){
  const source=templateForDisplay(item)[variant]||templateForDisplay(item).code;
  const result=insertTemplate(code,source);assert(result.indexOf('using ll = long long;')<result.indexOf('int main'));
  compile(result,`${item.id}/${variant} with actual ll default`);
 }
 console.log(JSON.stringify({ok:true,compiledVariants:48,compiledPrograms:compiled,actualDefaultAlreadyHasLl:true,usingTypedefMacroOrder:true,multilineAliases:true,nestedAliasScope:true,literalsCommentsPreserved:true,duplicateIncludesRemoved:true,conditionalHeadersPreserved:true,mainPreserved:true}));
}finally{await rm(folder,{recursive:true,force:true});}
