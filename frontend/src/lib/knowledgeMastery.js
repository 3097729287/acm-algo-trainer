// Parent topics pool unique judged problems, rather than averaging child percentages.
export function combineKnowledgeEvidence(ids, evidence, model = {}, children = []) {
  const unique = [...new Set(ids)].map(id => evidence.get(id)).filter(Boolean);
  const rated = unique.filter(item => item.rated).length;
  const minimum = model.minEvidence ?? 5, ratedMinimum = model.minRatedEvidence ?? 3;
  const covered = children.filter(child => {
    const entries = [...new Set(child.ids)].map(id => evidence.get(id)).filter(Boolean);
    return entries.length >= minimum && entries.filter(item => item.rated).length >= ratedMinimum;
  });
  const parentMinimum = children.length ? minimum * children.length : minimum;
  const enough = unique.length >= parentMinimum && rated >= ratedMinimum && covered.length === children.length;
  const weight = unique.reduce((sum, item) => sum + item.weight, 0);
  const floor = model.smallSampleFloor ?? .5, reference = model.quantityReference ?? 12;
  const quantity = floor + (1 - floor) * (1 - Math.exp(-unique.length / reference));
  const value = enough && weight > 0 ? Math.round(unique.reduce((sum, item) => sum + item.score * item.weight, 0) / weight * quantity) : null;
  const missing = children.filter(child => !covered.includes(child)).map(child => child.name);
  const reason = missing.length ? `子知识点证据充分 ${covered.length}/${children.length}；每项至少需要 ${minimum} 道有效作答及 ${ratedMinimum} 道已定级题目。尚不足：${missing.join('、')}`
    : unique.length < parentMinimum ? `有效作答 ${unique.length} 题，至少需要 ${parentMinimum} 道不同题目才能判断掌握程度`
    : rated < ratedMinimum ? `已有难度的有效作答 ${rated} 题，至少需要 ${ratedMinimum} 道才能判断难度表现`
    : '按不同题目的作答数量、难度、解决率、独立完成和提交稳定性加权';
  return { value, reason, participated: unique.length, officialAccepted: unique.filter(item => item.solved).length };
}
