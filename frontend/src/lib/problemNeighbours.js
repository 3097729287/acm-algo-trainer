// Queue order remains the source of truth; catalog rows decide whether a
// problem still exists and has a statement. Never turn a missing item into a
// fresh training activation merely to discover that navigation cannot open it.
export function availableProblemNeighbour(ids,current,rows,direction=1){
 const known=new Map(rows.map(row=>[row.id,row])),at=ids.indexOf(current);
 const candidates=direction<0?ids.slice(0,Math.max(0,at)).reverse():ids.slice(at+1);
 return candidates.find(id=>id!==current&&known.has(id)&&known.get(id).statementAvailable!==false)||null;
}
