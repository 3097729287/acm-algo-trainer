const valid=value=>/^[A-Z](?:\d)?$/.test(String(value||''));
function letters(index){let text='';for(let n=index+1;n;n=Math.floor((n-1)/26))text=String.fromCharCode(65+(n-1)%26)+text;return text;}
// Original contest letters are authoritative, including split tasks and gaps.
// Collections without an original roster receive explicitly local labels only.
export function withContestLetters(rows){
 const known=new Set(rows.map(row=>row.contestLetter||row.problem).filter(valid).map(String));
 let next=0;
 return rows.map(row=>{
  const original=row.contestLetter||row.problem;
  if(valid(original))return {...row,displayLetter:String(original),localLetter:false};
  while(known.has(letters(next)))next++;
  const displayLetter=letters(next++);known.add(displayLetter);
  return {...row,displayLetter,localLetter:true};
 });
}
export function contestLetterTitle(row){return `${row.localLetter?'本地题序':'原赛题号'} ${row.displayLetter} · ${row.problem} · ${row.title}`;}
