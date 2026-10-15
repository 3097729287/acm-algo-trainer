// A broad subject remains a subject; it never implies a more specific algorithm.
export function knowledgeLabels(row = {}) {
  if (row.locked) return [];
  if (row.tags?.length) return row.tags;
  return [...new Set(row.knowledgeCategories || [])];
}
