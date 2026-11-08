import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
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

export async function exerciseNativeReviews(page,output,sandbox,python){
 assert(python,'Set TB_NATIVE_TEST_PYTHON to generate an isolated review fixture');
 assert(resolve(sandbox).startsWith(resolve(output)+'\\sandbox-'),'Only this test-owned journal can receive generated receipt fixtures');
 const back=page.getByRole('button',{name:'返回主界面',exact:true}).first();if(await back.isVisible())await back.click();
 const id='luogu-training-P1001';
 const original=await rpc(page,'problem',undefined,{id:[id]});
 const normal='// ordinary code must survive the independent review\nint preserved = 1;\n';
 await rpc(page,'draft',{id,code:normal,language:'cpp17'});await rpc(page,'training/start',{id});
 const stamp=(await rpc(page,'workspace')).now;
 const seed=async(verdict,at)=>{
  // The unported original-site adapter commits receipt plus activation. Seed
  // that complete journal boundary, without sending an external submission.
  const script=`import sqlite3,sys\nfrom pathlib import Path\np=Path(sys.argv[1])\nassert p.name.startswith('sandbox-') and p.is_dir()\nwith sqlite3.connect(p/'personal.sqlite3') as db:\n db.execute("INSERT INTO submissions(id,problem_id,mode,scope,verdict,code,submitted_at,finished_at,message) VALUES(?,?,'submit','official',?,?,?,?,?)",('generated-review-window-'+sys.argv[3],sys.argv[2],sys.argv[3],'// Generated test receipt, never submitted to an OJ',sys.argv[4],sys.argv[4],'Generated offline test fixture'))\n if sys.argv[3]=='AC':db.execute("UPDATE training SET active=1,removed_at=NULL,active_at=MAX(active_at,?) WHERE id=?",(sys.argv[4],sys.argv[2]))\n`;
  await promisify(execFile)(python,['-c',script,sandbox,id,verdict,at],{windowsHide:true});
 };
 await seed('WA',new Date(Date.parse(stamp)-86400000).toISOString());
 const workspace=await rpc(page,'workspace');const task=workspace.reviews.tasks.find(task=>task.problemId===id);
 assert(task,'An actual prior-day WA fixture must create a due rewrite');
 await page.setViewportSize({width:1500,height:950});await page.reload();
 await page.locator('.tb-workbench').first().waitFor({state:'attached'});
 await page.keyboard.press('Escape');
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('.problem-title:visible').filter({hasText:original.title}).first().click();
 const editor=page.locator('.tb-workbench .cm-content[contenteditable=true]:visible').first();
 if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 assert.notEqual((await editor.innerText()).trimEnd(),normal.trimEnd(),'Review must start with its independent draft');
 const rewritten='#include <iostream>\n// independent review draft 😀\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}\n';
 await editor.fill(rewritten);await editor.press('Control+s');
 await page.waitForFunction(()=>document.querySelector('.wb-save-state')?.textContent.includes('已保存') || document.body.innerText.includes('草稿已保存'));
 const review=await rpc(page,'problem',undefined,{id:[id],reviewId:[task.id]});
 assert.equal(review.draft,rewritten);assert.equal((await rpc(page,'problem',undefined,{id:[id]})).draft,normal);
 await page.getByRole('button',{name:'官方样例',exact:true}).click();await page.getByRole('button',{name:'自测运行',exact:true}).click();
 await page.locator('.wb-result-summary .wb-verdict-sample_pass').waitFor();
 const samples=await rpc(page,'submissions',undefined,{id:[id],reviewId:[task.id]});
 assert(samples.submissions.some(row=>row.code===rewritten&&row.scope==='samples'&&row.verdict==='SAMPLE_PASS'));
 assert(samples.submissions.every(row=>row.scope!=='official'));
 await page.screenshot({path:resolve(output,'native-review-independent-draft.png')});
 await page.reload();await page.locator('.tb-workbench').waitFor();if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 assert.equal((await editor.innerText()).trimEnd(),rewritten.trimEnd());
 const cancelled=await rpc(page,'training/remove',{id});assert.equal(cancelled.cancelledReviewId,task.id);
 const restored=await rpc(page,'training/start',{id,restoreReviewId:task.id,deferWorkspace:true});assert.equal(restored.reviewTask.id,task.id);
 await seed('AC',(await rpc(page,'workspace')).now);
 const settled=await rpc(page,'workspace');assert(!settled.reviews.tasks.some(item=>item.id===task.id));
 const receipt=await rpc(page,'submission',undefined,{id:['generated-review-window-AC']});assert.equal(receipt.submission.reviewRewardXp,20);
 assert.equal((await rpc(page,'problem',undefined,{id:[id]})).draft,normal);
 return {realTauriIpc:true,generatedIsolatedJournal:true,externalSubmissionsSent:0,problemId:id,reviewTaskId:task.id,reviewDraftIndependent:true,normalDraftPreserved:true,reviewDraftRestoredAfterReload:true,realCppReviewSampleVerdict:'SAMPLE_PASS',sampleRunCreatesOfficialResult:false,cancelRestorePreserved:true,rewardDerivedFromExistingFixtureReceipt:20};
}
