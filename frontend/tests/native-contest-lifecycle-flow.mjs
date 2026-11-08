import assert from 'node:assert/strict';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {resolve} from 'node:path';

async function rpc(page,path,query={}) {
 return page.evaluate(async({path,query})=>{
  const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path,query}});
  if(!result.ok)throw new Error(result.error.code+': '+result.error.message);return result.data;
 },{path,query});
}

async function saved(page,id,contestId,code) {
 await page.waitForFunction(async({id,contestId,code})=>{
  const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'problem',query:{id:[id],contestId:[contestId]}}});
  return result.ok&&result.data.draft===code;
 },{id,contestId,code});
}

export async function exerciseNativeContestLifecycle(page,output,sandbox,python) {
 assert(python,'Set TB_NATIVE_TEST_PYTHON for isolated contest lifecycle fixtures');
 assert(resolve(sandbox).startsWith(resolve(output)+'\\sandbox-'),'Only the fresh test journal can receive generated contests');
 const id='luogu-training-P1001',otherId='luogu-training-P1421',contest='generated-running-window-finish';
 const ordinary=await rpc(page,'problem',{id:[id]}),other=await rpc(page,'problem',{id:[otherId]});
 const originalTraining=(await rpc(page,'workspace')).training.map(row=>row.id);
 const back=page.getByRole('button',{name:'返回主界面',exact:true}).first();
 if(await back.isVisible()){
  await back.click();await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
  await page.waitForFunction(async()=>{
   const result=await window.__TAURI__.core.invoke('api_request',{request:{version:1,id:crypto.randomUUID(),method:'GET',path:'preferences',query:{}}});
   return result.ok&&result.data.preferences?.learningPaths?.browserV1?.open===false;
  });
 }
 // This cache only exposes the existing navigation in this generated WebView.
 // It neither changes persisted account experience nor grants room authority.
 const {owner}=await rpc(page,'api/capabilities');assert(owner);
 await page.evaluate(owner=>localStorage.setItem('tb.navigation-level.v1.'+owner,JSON.stringify({owner,level:6})),owner);
 const seed=async(identity,name)=>{
  const at=(await rpc(page,'workspace')).now,start=new Date(Date.parse(at)-5*60000).toISOString(),deadline=new Date(Date.parse(at)+55*60000).toISOString();
  const fixture={identity,name,id,otherId,start,deadline,title:ordinary.title,otherTitle:other.title};
  const script=`import json,sqlite3,sys\nfrom pathlib import Path\nfrom contextlib import closing\np=Path(sys.argv[1]);assert p.name.startswith('sandbox-') and p.is_dir()\nf=json.loads(sys.argv[2])\nroot=Path(sys.argv[3]);assert (root/'data/native-catalog.sqlite3').is_file()\nwith closing(sqlite3.connect((root/'data/native-catalog.sqlite3').as_uri()+'?mode=ro',uri=True)) as source:\n raw=source.execute("SELECT compact FROM catalogue WHERE json_extract(compact,'$.catalogReplayReady')=0 AND COALESCE(json_extract(compact,'$.catalogHidden'),0)=0 ORDER BY id LIMIT 1").fetchone();assert raw\n missing=json.loads(raw[0])\nwith closing(sqlite3.connect(p/'personal.sqlite3')) as db:\n assert db.execute("SELECT COUNT(*) FROM contests WHERE status='running'").fetchone()[0]==0\n slots=[{'letter':'A','id':f['id'],'title':f['title'],'difficulty':800,'tags':['模拟'],'judgeScope':'official','statementAvailable':True,'trainingAdded':False},{'letter':'B','id':missing['id'],'title':missing['title'],'difficulty':1200,'tags':['动态规划'],'judgeScope':'unsupported','statementAvailable':False,'trainingAdded':False},{'letter':'C','id':f['otherId'],'title':f['otherTitle'],'difficulty':800,'tags':['模拟'],'judgeScope':'official','statementAvailable':True,'trainingAdded':False}]\n for slot in slots:\n  prior=db.execute('SELECT active,active_at,removed_at FROM training WHERE id=?',(slot['id'],)).fetchone()\n  slot['trainingBefore']=dict(zip(('active','active_at','removed_at'),prior)) if prior else None\n db.execute("INSERT INTO contests(id,name,status,started_at,deadline,duration,slots,config) VALUES(?,?,'running',?,?,60,?,?)",(f['identity'],f['name'],f['start'],f['deadline'],json.dumps(slots,ensure_ascii=False),json.dumps({'strategy':'replay','contest':'ABC 001','wrongPenalty':20,'compilePenalty':False,'editedTrainingOnly':True})))\n db.commit()\n print(json.dumps({'missingId':missing['id'],'missingTitle':missing['title']}))\n`;
  return JSON.parse((await promisify(execFile)(python,['-c',script,sandbox,JSON.stringify(fixture),resolve(import.meta.dirname,'../..')],{windowsHide:true})).stdout);
 };
 const enter=async()=>{
  await page.setViewportSize({width:1500,height:950});await page.reload();await page.locator('.sidebar').first().waitFor();
  await page.locator('.workspace-area .loading-screen').waitFor({state:'hidden'});
  const home=page.getByRole('button',{name:'返回主界面',exact:true}).first();
  if(await home.isVisible()){await home.click();await home.waitFor({state:'hidden'});}
  await page.keyboard.press('Control+5');
  const resume=page.getByRole('button',{name:'继续比赛',exact:true});
  if(await resume.isVisible())await resume.click();
  const workbench=page.locator(`.tb-workbench[data-problem-id="${id}"]:visible`);await workbench.waitFor();
  const editor=workbench.locator('.cm-content[contenteditable=true]:visible').first();
  if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
  await editor.click();await editor.press('Alt+0');
  await workbench.locator('.mock-problem-trigger').waitFor();
  return {workbench,editor};
 };
 const missing=await seed(contest,'原生比赛结束验证');
 let {workbench,editor}=await enter();
 const before=await rpc(page,'contest',{id:[contest]});assert.equal(before.contest.status,'running');assert.equal(before.contest.total,3);
 assert.equal(before.contest.slots[1].statementAvailable,false);assert.equal(before.contest.slots[1].id,missing.missingId);
 await page.getByRole('button',{name:'选择比赛题目，当前 A',exact:true}).click();
 const menu=page.getByRole('menu',{name:'模拟赛题目',exact:true});
 assert.equal(await menu.getByRole('menuitemradio').count(),3);
 assert(await menu.getByRole('menuitemradio').nth(1).isDisabled());await page.screenshot({path:resolve(output,'native-running-contest-picker.png')});
 await page.keyboard.press('Escape');
 await workbench.getByRole('button',{name:'下一题',exact:true}).click();
 await page.locator(`.tb-workbench[data-problem-id="${otherId}"]:visible`).waitFor();
 await page.getByRole('button',{name:'选择比赛题目，当前 C',exact:true}).click();
 await page.getByRole('menu',{name:'模拟赛题目',exact:true}).getByRole('menuitemradio').nth(0).click();
 await workbench.waitFor();if(!await editor.isVisible())await page.keyboard.press('Alt+2');await editor.waitFor();
 await workbench.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('cpp17');
 const examCode='#include <iostream>\n// independent native exam draft 😀\nint main(){long long a,b;std::cin>>a>>b;std::cout<<a+b<<"\\n";}\n';
 await editor.fill(examCode);await editor.press('Control+s');await saved(page,id,contest,examCode);
 ({workbench,editor}=await enter());
 assert.equal((await editor.innerText()).trimEnd(),examCode.trimEnd());
 await workbench.getByRole('button',{name:'官方样例',exact:true}).click();await workbench.getByRole('button',{name:'自测运行',exact:true}).click();
 await page.locator('.wb-result-summary .wb-verdict-sample_pass').waitFor();
 let view=await rpc(page,'contest',{id:[contest]});assert.equal(view.contest.accepted,0);assert.equal(view.contest.slots[0].attempts,0);
 const attempts=await rpc(page,'submissions',{id:[id],contestId:[contest]});
 const sample=attempts.submissions.find(row=>row.code===examCode);assert(sample&&sample.scope==='samples'&&sample.verdict==='SAMPLE_PASS');
 const running=(await rpc(page,'workspace')).training.find(row=>row.id===id);assert(running&&running.difficulty===null&&running.knowledge===''&&running.tags.length===0);
 await page.getByRole('button',{name:'结束比赛',exact:true}).click();
 await page.getByRole('alertdialog',{name:'结束比赛确认',exact:true}).getByRole('button',{name:'结束并复盘',exact:true}).click();
 const details=page.locator('.record-detail');await details.getByRole('heading',{name:'原生比赛结束验证',exact:true}).waitFor();
 assert((await details.innerText()).includes('0/3 AC'));assert.equal(await details.locator('.record-slot').count(),3);
 assert((await details.innerText()).includes('已结束'));await page.screenshot({path:resolve(output,'native-finished-contest-review.png')});
 view=await rpc(page,'contest',{id:[contest]});assert.equal(view.contest.status,'finished');assert.equal(view.contest.accepted,0);
 assert.equal((await rpc(page,'problem',{id:[id],contestId:[contest]})).draft,examCode);
 assert.equal((await rpc(page,'problem',{id:[id]})).draft,ordinary.draft);
 const afterIds=(await rpc(page,'workspace')).training.map(row=>row.id);
 assert.equal(afterIds.includes(missing.missingId),originalTraining.includes(missing.missingId));
 assert.equal(afterIds.includes(otherId),originalTraining.includes(otherId),'Reading an untouched exam slot must not enroll it in ordinary training');
 await details.getByRole('button',{name:'所有记录',exact:true}).click();
 await page.getByRole('button',{name:'删除模拟赛 原生比赛结束验证',exact:true}).click();
 await page.getByRole('alertdialog',{name:'删除确认',exact:true}).getByRole('button',{name:'删除',exact:true}).click();
 await page.getByRole('button',{name:'删除模拟赛 原生比赛结束验证',exact:true}).waitFor({state:'hidden'});
 assert(!(await rpc(page,'workspace')).contests.some(row=>row.id===contest));
 assert.equal((await rpc(page,'problem',{id:[id],contestId:[contest]})).draft,examCode);
 assert((await rpc(page,'submissions',{id:[id],contestId:[contest]})).submissions.some(row=>row.id===sample.id));
 const cancelled='generated-running-window-cancel';await seed(cancelled,'原生比赛取消验证');
 ({workbench,editor}=await enter());
 await workbench.getByRole('combobox',{name:'编程语言',exact:true}).selectOption('python3');
 const cancelCode='# independent cancelled exam context 😀\nprint(42)\n';await editor.fill(cancelCode);await editor.press('Control+s');await saved(page,id,cancelled,cancelCode);
 await page.getByRole('button',{name:'结束比赛',exact:true}).click();
 await page.getByRole('alertdialog',{name:'结束比赛确认',exact:true}).getByRole('button',{name:'取消比赛',exact:true}).click();
 await page.locator('.tb-workbench:visible').waitFor({state:'hidden'});
 assert.equal((await rpc(page,'contest',{id:[cancelled]})).contest.status,'cancelled');
 assert.equal((await rpc(page,'problem',{id:[id],contestId:[cancelled]})).draft,cancelCode);
 const restored=await rpc(page,'problem',{id:[id]});assert.equal(restored.draft,ordinary.draft);assert.equal(restored.draftLanguage,ordinary.draftLanguage);
 await page.locator('.sidebar').getByRole('button',{name:'我的训练',exact:true}).click();
 await page.locator('.problem-title:visible').filter({hasText:ordinary.title}).first().click();
 const normalEditor=page.locator(`.tb-workbench[data-problem-id="${id}"] .cm-content[contenteditable=true]:visible`).first();
 if(!await normalEditor.isVisible())await page.keyboard.press('Alt+2');await normalEditor.waitFor();
 assert.equal((await normalEditor.innerText()).trimEnd(),ordinary.draft.trimEnd());
 await page.reload();await normalEditor.waitFor();assert.equal((await normalEditor.innerText()).trimEnd(),ordinary.draft.trimEnd());
 await page.screenshot({path:resolve(output,'native-contest-ordinary-draft-restored.png')});
 return {realTauriIpc:true,generatedIsolatedJournal:true,existingRunningContestOpened:true,missingSlotPreservedAndDisabled:true,nextSkipsMissing:true,examDraftReloadPreserved:true,realCppSamples:true,sampleVerdict:sample.verdict,sampleDidNotAwardOfficialAc:true,knowledgeAndDifficultyMasked:true,actualFinishAndReview:true,actualHistoryTombstone:true,physicalDraftAndReceiptPreserved:true,actualCancel:true,ordinaryDraftAndLanguageAndReloadPreserved:true,untouchedSlotsNotAutoEnrolled:true,realAccountLevelChanged:false,externalSubmissionsSent:0};
}
