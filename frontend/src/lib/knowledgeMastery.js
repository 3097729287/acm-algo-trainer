// Parent topics pool unique judged problems, rather than averaging child percentages.
export function combineKnowledgeEvidence(ids, evidence, model = {}) {
  const unique = [...new Set(ids)].map(id => evidence.get(id)).filter(Boolean);
  const rated = unique.filter(item => item.rated).length;
  const minimum = model.minEvidence ?? 5, ratedMinimum = model.minRatedEvidence ?? 3;
  const enough = unique.length >= minimum && rated >= ratedMinimum;
  const weight = unique.reduce((sum, item) => sum + item.weight, 0);
  const value = enough && weight > 0 ? Math.round(unique.reduce((sum, item) => sum + item.score * item.weight, 0) / weight) : null;
  const reason = unique.length < minimum ? `有效作答 ${unique.length} 题，至少需要 ${minimum} 道不同题目才能判断掌握程度`
    : rated < ratedMinimum ? `已有难度的有效作答 ${rated} 题，至少需要 ${ratedMinimum} 道才能判断难度表现`
    : '按已作答题目的解决率、独立完成、提交稳定性和难度加权';
  return { value, reason, participated: unique.length, officialAccepted: unique.filter(item => item.solved).length };
}
