// Rejection sampling gives every matching problem one equally likely ticket.
// Repeats are intentional; neither ordering, rating nor previous draws affect it.
export function uniformIndex(length, cryptoSource = globalThis.crypto) {
  if (!Number.isSafeInteger(length) || length < 1 || length > 0x100000000) throw new RangeError('候选题数量无效');
  if (!cryptoSource?.getRandomValues) throw new Error('随机数源暂不可用，请重试');
  const limit = Math.floor(0x100000000 / length) * length;
  const sample = new Uint32Array(1);
  do { cryptoSource.getRandomValues(sample); } while (sample[0] >= limit);
  return sample[0] % length;
}
