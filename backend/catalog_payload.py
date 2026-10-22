"""Public list projection; full algorithm evidence stays in the problem API.

This does not change Store.data(), personal records or problem identities. The
HTTP caller opts in to a smaller list response after reading the normal view.
"""

# Used by App/model filters, practiceMetadata tooltips/chronology, knowledgeLabels,
# contestShelves and the competition groups. Keep evidence used by difficulty
# tooltips, while omitting the much larger algorithm-analysis derivations.
ROW_FIELDS = frozenset('''
    id aliasIds title name contest problem platform series url source status date queue
    tags knowledge knowledgeCategories difficulty difficultySource difficultyBand
    difficultyConfidence difficultyEvidence difficultyEstimated
    solutionAvailable solutionState detailedSolutionAvailable statementAvailable
    catalogHidden catalogNotice catalogVisibilityPolicy catalogContentReady
    contestDate startedAt endedAt contestDateSource contestDatePrecision
    contestFullName contestId contestFamily contestRoster contestProblemCount
    contestVariant contestDifficulty contestDifficultySource contestPhase
    collectionNotice collectionSource eventYear xcpcYear xcpcKind xcpcPlace
    examYear examStage examGroup region category phase shelf
    active activeAt accepted today lastActivityAt lastSubmittedAt verdict scope locked
'''.split())


def catalogue_payload(data):
    """Project rows without dropping, sorting, renaming or mutating a record."""
    return {**data, 'rows': [{key: value for key, value in row.items() if key in ROW_FIELDS}
                           for row in data.get('rows', [])]}


def hub_payload(data):
    """List UI uses stable ID/URL arrays; omit the duplicate target index."""
    return {**data, 'notifications': [{key: value for key, value in notice.items() if key != 'targets'}
                                    for notice in data.get('notifications', [])]}
