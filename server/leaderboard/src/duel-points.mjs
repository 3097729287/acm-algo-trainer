// Use pre-match points. The zero floor protects only the losing player.
export function duelPoints(a,b,winner){
 if(![a,b].every(value=>Number.isSafeInteger(value)&&value>=0))throw new TypeError('Invalid duel points');
 if(winner==='draw')return [0,0];
 if(winner!=='A'&&winner!=='B')throw new TypeError('Invalid duel winner');
 const winnerPoints=winner==='A'?a:b,loserPoints=winner==='A'?b:a;
 const gain=Math.max(1,Math.round(40/(1+10**((winnerPoints-loserPoints)/400))));
 const loss=Math.min(loserPoints,gain),deduction=loss===0?0:-loss;
 return winner==='A'?[gain,deduction]:[deduction,gain];
}
