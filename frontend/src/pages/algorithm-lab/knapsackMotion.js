import { packingPlan, table01 } from './knapsackModel.js';

export function choiceFrames(items, capacity, focusIndex = null) {
  const table = table01(items, capacity), indices = focusIndex == null ? items.map((_, i) => i + 1) : [focusIndex];
  return indices.flatMap(i => {
    const item = items[i - 1], earlier = items.slice(0, i - 1), remaining = capacity - item.weight;
    const skip = table[i - 1][capacity], source = remaining >= 0 ? table[i - 1][remaining] : null, take = source == null ? null : source + item.value;
    return ['scope', 'skip', 'take', 'compare'].map(phase => ({
      i, phase, item, capacity, remaining, earlier, available: items.slice(0, i), skip, source, take,
      result: table[i][capacity], skipPlan: packingPlan(earlier, capacity),
      takePlan: remaining >= 0 ? [...packingPlan(earlier, remaining), item] : [],
      winner: take != null && take > skip ? 'take' : 'skip', resultPlan: packingPlan(items.slice(0, i), capacity),
    }));
  });
}
