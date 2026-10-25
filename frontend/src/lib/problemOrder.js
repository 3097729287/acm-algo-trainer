// Unknown and hidden difficulty always follow rated tasks in either direction.
export function problemDifficulty(row) {
  if(!row||row.difficultyHidden)return null;
  const value=Number(row.difficulty);
  if(Number.isFinite(value)&&value>0)return value;
  const native=Number(row.nativeDifficulty);
  return native>0&&native<=8?[0,800,1100,1400,1700,2000,2300,2700,3200][native]:null;
}
export function compareProblemDifficulty(a,b,descending=false) {
  const left=problemDifficulty(a),right=problemDifficulty(b);
  if(left==null||right==null)return left==null?(right==null?0:1):-1;
  return (left-right)*(descending?-1:1);
}
