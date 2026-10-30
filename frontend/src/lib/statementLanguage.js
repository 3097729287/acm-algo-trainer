export function originalIsChinese(problem) {
  // Declarations on a frozen original belong to that snapshot. A recovered
  // current source can be English while retaining the old Chinese declaration.
  const declared=problem?.currentSourceMarkdown?null:problem?.statementLanguage||problem?.sourceLanguage||problem?.translation?.sourceLanguage;
  if(declared)return /^zh(?:-|$)/i.test(declared);
  if(!problem?.currentSourceMarkdown&&problem?.translation?.kind==='original')return true;
  const prose=(problem?.currentSourceMarkdown||problem?.markdown||'').replace(/```[\s\S]*?```|\$\$[\s\S]*?\$\$|\$[^$\n]*\$|https?:\/\/\S+|^#+.*$/gm,'');
  const chinese=(prose.match(/[\u3400-\u9fff]/g)||[]).length,english=(prose.match(/[A-Za-z]{3,}/g)||[]).join('').length;
  return chinese>=8&&chinese*2>english;
}
