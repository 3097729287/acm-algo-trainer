// A full date is required. Two-digit years mean 2000-2099.
export function parseActivityDate(input) {
 const text=String(input||'').trim();
 let parts;
 if(/^\d{8}$/.test(text))parts=[text.slice(0,4),text.slice(4,6),text.slice(6)];
 else if(/^\d{6}$/.test(text))parts=[text.slice(0,2),text.slice(2,4),text.slice(4)];
 else parts=text.replace(/[年月]/g,'-').replace(/日$/,'').split(/[\s/:.\-]+/);
 if(parts.length!==3||!parts.every(part=>/^\d+$/.test(part)))return null;
 if(![2,4].includes(parts[0].length)||parts[1].length>2||parts[2].length>2)return null;
 let [year,month,day]=parts.map(Number);if(parts[0].length===2)year+=2000;
 if(year<1900||year>2199||month<1||month>12||day<1||day>31)return null;
 const date=new Date(Date.UTC(year,month-1,day));
 if(date.getUTCFullYear()!==year||date.getUTCMonth()!==month-1||date.getUTCDate()!==day)return null;
 return `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
}
export function fitActivityGrid(width,height,count=31,gap=7) {
 let best={columns:7,size:1};
 for(let columns=1;columns<=count;columns++){
  const rows=Math.ceil(count/columns),size=Math.min((width-gap*(columns-1))/columns,(height-gap*(rows-1))/rows);
  if(size>best.size)best={columns,size};
 }
 return {columns:best.columns,size:Math.max(1,Math.floor(best.size))};
}
export const activitySegmentSize=maximum=>Math.max(5,Math.ceil((Number(maximum)||0)/25)*5);
