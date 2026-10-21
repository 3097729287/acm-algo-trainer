export function defaultTrainingDuration({mode='comprehensive',count=4,max=1400}) {
  const band = max <= 1400 ? 0 : max <= 1700 ? 1 : max <= 2000 ? 2 : 3;
  if (mode === 'single') return [30,45,60,75][band];
  const base = (mode === 'topic' ? [90,120,150,180] : [120,150,180,210])[band];
  return Math.max(30,Math.min(480,Math.ceil(base * Math.max(1,Number(count)||4) / 4 / 15)*15));
}
