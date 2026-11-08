import assert from 'node:assert/strict';
import {resolve} from 'node:path';

async function rpc(page,path,body,query={}){
 return page.evaluate(async({path,body,query})=>{
  const invoke=window.__TAURI__.core.invoke;
  const call=async(path,query={},body,token,owner)=>{
   const request={version:1,id:crypto.randomUUID(),method:body===undefined?'GET':'POST',path,query,...(body===undefined?{}:{body,token,owner})};
   const result=await invoke('api_request',{request});if(!result.ok)throw new Error(result.error.code+': '+result.error.message);return result.data;
  };
  if(body===undefined)return call(path,query);
  const account=await call('account'),capabilities=await call('api/capabilities');
  return call(path,query,body,account.token,capabilities.owner);
 },{path,body,query});
}

export async function exerciseNativeRuns(page,output){
 const id='luogu-training-P1001';
 const original=await rpc(page,'problem',undefined,{id:[id]});
 assert(original.statementAvailable!==false&&original.samples.length>0);
 const cpp='#include <iostream>\n// 真实 Rust 运行 😀\nint main(){ long long a,b; std::cin>>a>>b; std::cout<<a+b<<"\\n"; }\n';
 await rpc(page,'draft',{id,code:cpp,language:'cpp17'});
 await rpc(page,'training/start',{id});
 await page.setViewportSize({width:1500,height:950});
 const back=page.getByRole('button',{name:'返回主界面',exact:true}).first();
 await back.waitFor();await back.click();
 // The real return action refreshes the workspace after the native fixture
 // write. Reopening here tests that rendered table; reload recovery is checked
 // below after the real C++ and Python runs have completed.
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('.problem-title:visible').filter({hasText:original.title}).first().click();
 const editor=page.locator('.tb-workbench .cm-content[contenteditable=true]:visible').first();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');
 await editor.waitFor();assert.equal((await editor.innerText()).trimEnd(),cpp.trimEnd());
 await page.getByRole('button',{name:'官方样例',exact:true}).click();
 await page.getByRole('button',{name:'自测运行',exact:true}).click();
 await page.locator('.wb-result-summary .wb-verdict-sample_pass').waitFor();
 assert.equal(await page.locator('.wb-case').count(),original.samples.length);
 await page.screenshot({path:resolve(output,'native-cpp-samples.png')});
 let history=await rpc(page,'submissions',undefined,{id:[id]});
 const cppResult=history.submissions.find(row=>row.code===cpp);
 assert(cppResult&&cppResult.verdict==='SAMPLE_PASS'&&cppResult.scope==='samples');
 await page.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('python3');
 const python='import time\ntime.sleep(.7)\na,b=map(int,input().split())\nprint(a+b)\n# 中文 😀\n';
 await editor.fill(python);await editor.press('Control+s');
 await page.getByRole('button',{name:'自测输入',exact:true}).click();
 await page.getByRole('textbox',{name:'标准输入',exact:true}).fill('20 22\n');
 await page.getByRole('button',{name:'自测运行',exact:true}).click();
 const before=performance.now();await rpc(page,'preferences');const pendingReadMillis=performance.now()-before;
 assert(pendingReadMillis<600,'The real native IPC remains responsive during user execution');
 await page.locator('.wb-result-summary .wb-verdict-run_ok').waitFor();
 history=await rpc(page,'submissions',undefined,{id:[id]});
 const pythonResult=history.submissions.find(row=>row.code===python);
 assert(pythonResult&&pythonResult.verdict==='RUN_OK'&&pythonResult.scope==='samples'&&pythonResult.language==='python3');
 assert.equal(pythonResult.output.trim(),'42');assert.equal(pythonResult.passed,0);assert.equal(pythonResult.caseResults[0].expected,null);
 assert(history.submissions.every(row=>row.verdict!=='AC'&&row.scope!=='official'));
 await page.setViewportSize({width:800,height:650});
 await page.locator('.tb-workbench.wb-compact').waitFor();
 if(!await editor.isVisible())await page.getByRole('button',{name:'只看代码',exact:true}).click();
 await editor.waitFor();
 await page.locator('.wb-result-summary .wb-verdict-run_ok').waitFor();
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'The narrow code and result pane fits the window');
 await page.screenshot({path:resolve(output,'native-python-custom-narrow.png')});
 await page.reload();await page.locator('.tb-workbench').waitFor();
 if(!await editor.isVisible())await page.getByRole('button',{name:'只看代码',exact:true}).click();
 await editor.waitFor();assert.equal((await editor.innerText()).trimEnd(),python.trimEnd());
 const restored=await rpc(page,'problem',undefined,{id:[id]});assert.equal(restored.draft,python);assert.equal(restored.draftLanguage,'python3');
 assert(restored.submissions.some(row=>row.id===pythonResult.id&&row.verdict==='RUN_OK'));
 return {realTauriIpc:true,realCppCompiler:true,realPythonInterpreter:true,problemId:id,officialSamples:original.samples.length,cppVerdict:cppResult.verdict,pythonVerdict:pythonResult.verdict,customOutput:'42',pendingReadMillis,draftLanguageAndHistoryRestored:true,officialAcClaims:0};
}
