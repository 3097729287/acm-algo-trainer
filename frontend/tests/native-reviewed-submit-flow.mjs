import assert from 'node:assert/strict';
import {resolve} from 'node:path';

async function rpc(page,path,body,query={},requestId){
 return page.evaluate(async({path,body,query,requestId})=>{
  const invoke=window.__TAURI__.core.invoke;
  const read=async path=>{
   const value=await invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query:{}}});
   if(!value.ok)throw new Error(JSON.stringify(value.error));return value.data;
  };
  const auth=body===undefined?{}:{token:(await read('account')).token,owner:(await read('api/capabilities')).owner};
  const value=await invoke('api_request',{request:{version:1,id:requestId||crypto.randomUUID(),method:body===undefined?'GET':'POST',path,query,...(body===undefined?{}:{body,...auth})}});
  if(!value.ok)throw new Error(JSON.stringify(value.error));return value.data;
 },{path,body,query,requestId});
}
async function finished(page,id){
 const deadline=Date.now()+30000;
 for(;;){
  const result=await rpc(page,'submission',undefined,{id:[id]});
  if(result.submission.finishedAt)return result.submission;
  assert(Date.now()<deadline,'The actual native reviewed job must finish');
  await page.waitForTimeout(40);
 }
}

export async function exerciseNativeReviewedSubmissions(page,output){
 const id='入门赛 49::D',problem=await rpc(page,'problem',undefined,{id:[id]});
 assert.equal(problem.judge.scope,'local');assert(problem.samples.length>0);
 const before=(await rpc(page,'data/export')).tables.drafts.filter(row=>row.context===''&&row.problem_id!==id);
 await rpc(page,'training/start',{id});
 const home=page.getByRole('button',{name:'返回主界面',exact:true}).first();
 if(await home.isVisible()){await home.click();await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});}
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('.problem-title:visible').filter({hasText:problem.title}).first().click();
 await page.setViewportSize({width:1500,height:950});
 const editor=page.locator('.tb-workbench .cm-content[contenteditable=true]:visible').first();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 const execute=async(language,code)=>{
  await page.getByRole('combobox',{name:'编程语言',exact:true}).selectOption(language);
  await editor.fill(code);await editor.press('Control+s');
  await page.waitForFunction(async({id,language,marker})=>{
   const value=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'problem',query:{id:[id]}}});
   return value.ok&&value.data.draftLanguage===language&&value.data.draft.includes(marker);
  },{id,language,marker:`reviewed real window ${language==='cpp17'?'C++':'Python'}`});
  const saved=await rpc(page,'problem',undefined,{id:[id]});
  const body={id,code:saved.draft,language,mode:'submit'},requestId=crypto.randomUUID();
  // This exercises the real Tauri IPC API. The existing product Submit button
  // deliberately remains an original-site action until browser migration.
  const queued=await rpc(page,'submissions',body,{},requestId);
  const readStarted=performance.now();await rpc(page,'preferences');
  assert(performance.now()-readStarted<800,'The compiler cannot retain UI/database locks');
  const receipt=await finished(page,queued.submission.id);
  assert.equal(receipt.mode,'submit');assert.equal(receipt.scope,'local');
  assert.equal(receipt.verdict,'SAMPLE_PASS',receipt.message);
  assert.equal(receipt.total,problem.samples.length+60);assert.equal(receipt.passed,receipt.total);
  assert.equal(receipt.code,saved.draft);assert.equal(receipt.reviewRewardXp,0);
  assert(receipt.caseResults.every(row=>row.input===''&&row.expected===null&&row.actual===''));
  assert.equal((await rpc(page,'submissions',body,{},requestId)).submission.id,receipt.id);
  return receipt;
 };
 const cpp=await execute('cpp17','#include <iostream>\n// reviewed real window C++ 😀\nint main(){int n;std::cin>>n;unsigned long long d[61]={1,1,2};for(int i=3;i<=n;i++)d[i]=d[i-1]+d[i-3];std::cout<<d[n]<<"\\n";}\n');
 await page.reload();await page.locator('.tb-workbench:visible').waitFor();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 if(!await page.locator('.wb-result-summary:visible').isVisible())await page.getByRole('button',{name:'运行结果',exact:true}).click();
 await page.locator('.wb-result-summary .wb-verdict-sample_pass').waitFor();
 assert.equal(await page.locator('.wb-result-summary .wb-verdict').innerText(),'本地通过');
 assert(await page.getByText('本地审核测试已通过，暂不计入原站 AC。',{exact:true}).isVisible());
 assert.equal(await page.getByText('自定义输入没有预期答案，仅检查程序是否正常运行。',{exact:true}).count(),0);
 assert.equal(await page.locator('.wb-case-input').count(),0);
 await page.screenshot({path:resolve(output,'native-reviewed-cpp-full.png')});
 const python=await execute('python3','# reviewed real window Python 😀\nn=int(input())\nd=[1,1,2]\nfor i in range(3,n+1): d.append(d[-1]+d[-3])\nprint(d[n])\n');
 await page.reload();await page.locator('.tb-workbench:visible').waitFor();
 await page.setViewportSize({width:800,height:650});
 await page.locator('.tb-workbench.wb-compact').waitFor();
 if(!await editor.isVisible())await page.getByRole('button',{name:'只看代码',exact:true}).click();
 await editor.waitFor();assert((await editor.innerText()).includes('reviewed real window Python'));
 if(!await page.locator('.wb-result-summary:visible').isVisible())await page.getByRole('button',{name:'运行结果',exact:true}).click();
 await page.locator('.wb-result-summary .wb-verdict-sample_pass').waitFor();
 assert.equal(await page.locator('.wb-result-summary .wb-verdict').innerText(),'本地通过');
 assert.equal(await page.getByText('仅通过公开样例，暂不计入已 AC。',{exact:true}).count(),0);
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false);
 await page.screenshot({path:resolve(output,'native-reviewed-python-full-narrow.png')});
 const rows=(await rpc(page,'submissions',undefined,{id:[id]})).submissions;
 assert(rows.some(row=>row.id===cpp.id)&&rows.some(row=>row.id===python.id));
 assert(rows.every(row=>row.scope!=='official'&&row.verdict!=='AC'));
 assert.deepEqual((await rpc(page,'data/export')).tables.drafts.filter(row=>row.context===''&&row.problem_id!==id),before);
 return {realTauriIpc:true,originalPublicProblem:id,submitStartedThroughWindowIpc:true,
  originalSiteSubmitButtonUnchanged:true,originalSamples:problem.samples.length,auditedExtraCases:60,
  actualCpp:cpp.verdict,actualPython:python.verdict,cppPassed:cpp.passed,pythonPassed:python.passed,
  scopedPrivateCaseDetails:true,normalDraftsUnchanged:true,recoveredAfterReload:true,
  officialAcClaims:0,reviewRewardsGranted:0,actualOriginalSiteSubmissions:0};
}
