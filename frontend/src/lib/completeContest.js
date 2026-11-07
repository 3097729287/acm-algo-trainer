// A published roster and every original statement are required for a full paper.
export function completeContest(rows){
 if(!rows.length)return false;
 const expected=Math.max(0,...rows.map(row=>Number(row.contestProblemCount)||0));
 if(rows.some(row=>row.catalogContentReady===false))return false;
 if(expected)return rows.length===expected;
 // Compatibility for callers which supply old metadata-free projections.
 return !rows.some(row=>Object.hasOwn(row,'catalogContentReady'))&&rows.length>1;
}

export function replayVisible(row){
 return !row.catalogHidden||row.schoolTraining||row.statementRetirementPolicy==='public-statement-audit-v1'&&!row.statementPriorVisibility?.catalogHidden;
}

export function canReplayContest(rows){
 return rows.some(row=>row.catalogReplayReady===true||row.catalogReplayReady!==false&&(row.catalogContentReady===true||!Object.hasOwn(row,'catalogContentReady')));
}
