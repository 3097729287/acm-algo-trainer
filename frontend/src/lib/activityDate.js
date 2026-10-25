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
export function fitCompactActivityGrid(width,height,count) {
 const previous=fitActivityGrid(width,height,count,3);
 const rows=Math.ceil(count/previous.columns),columns=Math.ceil(count/rows);
 return {columns,rows,size:Math.max(1,Math.floor(previous.size))};
}
export const activitySegmentSize=maximum=>Math.max(5,Math.ceil((Number(maximum)||0)/25)*5);

export function monthDays(month) {
 if(!/^\d{4}-(0[1-9]|1[0-2])$/.test(month))return [];
 const [year,index]=month.split('-').map(Number),count=new Date(Date.UTC(year,index,0)).getUTCDate();
 return Array.from({length:count},(_,i)=>`${month}-${String(i+1).padStart(2,'0')}`);
}
export function activityMonths(endingMonth) {
 if(!monthDays(endingMonth).length)return [];
 const [year,month]=endingMonth.split('-').map(Number);
 return Array.from({length:12},(_,i)=>{
  const date=new Date(Date.UTC(year,month-12+i,1));
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth()+1).padStart(2,'0')}`;
 });
}
export function monthCells(month) {
 const days=monthDays(month);if(!days.length)return [];
 const start=(new Date(`${month}-01T00:00:00Z`).getUTCDay()+6)%7;
 return Array.from({length:42},(_,index)=>days[index-start]||null);
}
export function fitActivityMonths(width,height) {
 const columns=width>=760?4:2,rows=4/columns,gap=16;
 const monthWidth=(width-gap*(columns-1))/columns;
 const monthHeight=(height-gap*(rows-1))/rows;
 return {columns,size:Math.max(1,Math.min(48,Math.floor(Math.min((monthWidth-6*5)/7,(monthHeight-26-5*5)/6))))};
}

export function yearDays(year) {
 if(!/^\d{4}$/.test(String(year))||Number(year)<1900||Number(year)>2199)return [];
 return Array.from({length:12},(_,i)=>monthDays(`${year}-${String(i+1).padStart(2,'0')}`)).flat();
}
// Keep January 1 in the top-left and December 31 in the bottom-right.
// A short final column is bottom-aligned without inserting fictitious dates.
export function activityYearCells(days,rows) {
 const remainder=days.length%rows;
 if(!remainder)return days;
 const start=days.length-remainder;
 return [...days.slice(0,start),...Array(rows-remainder).fill(null),...days.slice(start)];
}
export function activityTone(count,step=5) {
 const amount=Math.max(0,Number(count)||0),size=Math.max(1,Number(step)||5);
 if(!amount)return {band:0,shade:0};
 const band=Math.min(5,Math.ceil(amount/size));
 return {band,shade:Math.min(5,Math.max(1,Math.ceil((amount-(band-1)*size)/size*5)))};
}
