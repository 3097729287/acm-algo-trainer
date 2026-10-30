import assert from 'node:assert/strict';
import fs from 'node:fs';
import {originalIsChinese} from '../src/lib/statementLanguage.js';
if(!process.argv[2]||!process.argv[3])throw new Error('Supply isolated language corpus JSON and result path');
const rows=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));let recoveredControls=0;
for(const row of rows){
  const declared=row.statementLanguage||row.sourceLanguage||row.translation?.sourceLanguage;
  const prose=(row.currentSourceMarkdown||'').replace(/https?:\/\/\S+|^#+.*$/gm,'');
  if(row.currentSourceMarkdown&&/^zh/i.test(declared||'')&&(prose.match(/[A-Za-z]{3,}/g)||[]).length>(prose.match(/[\u3400-\u9fff]/g)||[]).length){
    assert.equal(originalIsChinese(row),false,row.id);recoveredControls++;
  }
}
assert.equal(recoveredControls,241);
const result={translationSnapshotsChecked:rows.length,recoveredEnglishChineseControls:recoveredControls,changedTranslationText:0};
fs.writeFileSync(process.argv[3],JSON.stringify(result,null,2));console.log(JSON.stringify(result));
