import { AccountError } from './accounts.mjs';

const fields = ['level', 'tier', 'rankTier', 'rankScore', 'titles'];
const titleFields = ['id', 'name', 'category', 'target'];
const displayText = (value, maximum) => typeof value === 'string' && value.trim() === value &&
  [...value].length > 0 && [...value].length <= maximum && !/[\u0000-\u001f\u007f-\u009f]/u.test(value);
const objectWithFields = (value, allowed) => value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).length === allowed.length && Object.keys(value).every(key => allowed.includes(key));

// This small, opt-in summary contains no login ID, code, preferences or cloud
// snapshot. Rankings never deserialize the private account_state payload.
export function validatePublicProgress(value) {
  const reject = () => { throw new AccountError(400, '公开成长资料无效'); };
  if (!objectWithFields(value, fields) || !Number.isSafeInteger(value.level) || value.level < 1 || value.level > 100 ||
      !displayText(value.tier, 24) || !(value.rankTier === null || displayText(value.rankTier, 24)) ||
      !(value.rankScore === null || Number.isSafeInteger(value.rankScore) && value.rankScore >= 0 && value.rankScore <= 1000000) ||
      (value.rankTier === null) !== (value.rankScore === null) ||
      !Array.isArray(value.titles) || value.titles.length > 2) reject();
  const categories = new Set();
  const titles = value.titles.map(item => {
    if (!objectWithFields(item, titleFields) || !/^[a-z][a-z0-9-]{0,47}$/.test(item.id || '') ||
        !displayText(item.name, 24) || !['ac', 'streak'].includes(item.category) || categories.has(item.category) ||
        !Number.isSafeInteger(item.target) || item.target < 1 || item.target > 2000) reject();
    categories.add(item.category);
    return { id: item.id, name: item.name, category: item.category, target: item.target };
  });
  return { level: value.level, tier: value.tier, rankTier: value.rankTier, rankScore: value.rankScore, titles };
}

export function storedPublicProgress(payload) {
  if (typeof payload !== 'string' || payload.length > 4096) return null;
  try { return validatePublicProgress(JSON.parse(payload)); } catch { return null; }
}

export const publicId = userId => 'TB-' + userId.replaceAll('-', '').toUpperCase();
