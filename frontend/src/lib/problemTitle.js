// Names retain their original punctuation, mathematical intervals and versions.
export function problemTitle(value) {
 let title=String(value??'').trim();
 while(/^[\[【「『]/.test(title)) {
  const match=title.match(/^(?:\[([^\]\n]+)\]|【([^】\n]+)】|「([^」\n]+)」|『([^』\n]+)』)[ \t\u3000]*/);
  if(!match)break;
  const label=match.slice(1).find(part=>part!==undefined),remaining=title.slice(match[0].length).trim();
  if(!remaining||/^[A-Za-z0-9_+*/^.\s-]+[,，][A-Za-z0-9_+*/^.\s-]+$/.test(label))break;
  title=remaining;
 }
 return title;
}
