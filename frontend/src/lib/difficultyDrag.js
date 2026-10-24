// Relative dragging gives short popover tracks the same precision as wide tracks.
export const DRAG_DEAD_ZONE = 6;
export const MIN_PIXELS_PER_STEP = 32;
export function difficultyDragValue(origin, distance, {min=0,max=4000,step=100,pixelsPerStep=MIN_PIXELS_PER_STEP}={}) {
  const steps=Math.floor(Math.max(0,Math.abs(distance)-DRAG_DEAD_ZONE)/pixelsPerStep);
  if(!steps)return origin;
  const snapped=Math.round(origin/step)*step;
  return Math.max(min,Math.min(max,snapped+Math.sign(distance)*steps*step));
}
