import { categoryPath } from './trainingListCatalog.js';

export const algorithmPath = categoryPath;

const urlKey = url => String(url || '').replace(/^https?:\/\/(?:www\.)?/, '').replace(/[?#].*$/, '').replace(/\/$/, '');
export const startsWithPath = (path, prefix) => prefix.every((part, i) => path[i] === part);

export function trainingIndex(lists, rows) {
  const byId = new Map(), byUrl = new Map(), byList = new Map(lists.map(list => [list.id, list]));
  for (const row of rows) {
    for (const id of [row.id, ...(row.aliasIds || [])]) byId.set(id, row);
    byUrl.set(urlKey(row.url), row);
  }
  const resolve = item => ({ ...item, row: byId.get(item.problemId) || byUrl.get(urlKey(item.url)) || null });
  const own = new Map(lists.map(list => {
    const unique = new Map();
    for (const item of list.problems.map(resolve)) {
      const key = item.row?.id || urlKey(item.url) || item.pid;
      if (!unique.has(key)) unique.set(key, item);
    }
    return [list.id, [...unique.values()]];
  }));
  const cache = new Map();
  function all(id) {
    if (cache.has(id)) return cache.get(id);
    const found = new Map(), visited = new Set();
    function visit(key) {
      if (visited.has(key)) return;
      visited.add(key);
      for (const item of own.get(key) || []) {
        const identity = item.row?.id || urlKey(item.url) || item.pid;
        if (!found.has(identity)) found.set(identity, item);
      }
      if (byList.get(key)?.aggregateChildren !== false) {
        for (const child of byList.get(key)?.children || []) visit(child);
      }
    }
    visit(id);
    const result = [...found.values()];
    cache.set(id, result);
    return result;
  }
  const categories = [...new Map(lists.flatMap(list => list.categories || []).map(category => [category.id, category])).values()].sort((a, b) => a.order - b.order);
  function stats(ids) {
    const unique = new Map();
    for (const id of ids) for (const item of all(id)) unique.set(item.row?.id || urlKey(item.url) || item.pid, item);
    return { total: unique.size, accepted: [...unique.values()].filter(item => item.row?.accepted).length };
  }
  return { byList, own, all, categories, stats };
}

export function matchesTrainingProblem(item, query, status = '') {
  const text = [item.pid, item.row?.title, ...(item.row?.tags || []), ...(item.sections || [])].join(' ').toLocaleLowerCase();
  return query.trim().toLocaleLowerCase().split(/\s+/).every(word => text.includes(word))
    && (status !== 'accepted' || item.row?.accepted)
    && (status !== 'pending' || !item.row?.accepted);
}
