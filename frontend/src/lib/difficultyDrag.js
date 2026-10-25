// Convert physical rail coordinates before snapping both the thumb and value.
export function difficultyPointerValue(clientX, {left,width,min=0,max=4000}) {
  const fraction=Math.max(0,Math.min(1,(clientX-left-6)/Math.max(1,width-12)));
  return min+fraction*(max-min);
}
export function snapDifficulty(value,{min=0,max=4000,step=100}={}) {
  return Math.max(min,Math.min(max,value>=max-step/2?max:min+Math.round((value-min)/step)*step));
}
