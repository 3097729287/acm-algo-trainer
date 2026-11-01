"""Public list projection; full algorithm evidence stays in the problem API.

This does not change Store.data(), personal records or problem identities. The
HTTP caller opts in to a smaller list response after reading the normal view.
"""

# Used by App/model filters, practiceMetadata tooltips/chronology, knowledgeLabels,
# contestShelves and the competition groups. Keep evidence used by difficulty
# tooltips, while omitting the much larger algorithm-analysis derivations.
ROW_FIELDS = frozenset('''
    id aliasIds title name contest problem platform series url source status date queue addedAt firstAdded catalogAddedAt
    tags knowledge knowledgeCategories knowledgeReviewRequired difficulty difficultySource difficultyBand
    difficultyConfidence difficultyEvidence difficultyEstimated nativeDifficulty nativeDifficultyLabel problemKind schoolTraining labTopic
    solutionAvailable solutionState detailedSolutionAvailable statementAvailable
    catalogHidden catalogNotice catalogVisibilityPolicy catalogContentReady
    catalogStatementReady catalogReplayReady problemType localJudgeSupported rosterVerified contestLetterVerified
    contestDate startedAt endedAt contestDateSource contestDatePrecision
    contestFullName contestId contestLetter contestFamily contestRoster contestProblemCount
    contestVariant contestDifficulty contestDifficultySource contestPhase
    collectionNotice collectionSource eventYear xcpcYear xcpcKind xcpcPlace
    examYear examStage examGroup region category phase shelf
    active activeAt accepted today lastActivityAt lastSubmittedAt verdict scope locked
'''.split())


# Legacy explicit additions predate persisted addedAt. These UTC timestamps
# come from their first source inclusion (679e2c7d and be24193f), not from
# contest names/dates or users' practice activity. New imports retain addedAt.
_LEGACY_ADDED={
    'https://codeforces.com/gym/726517/':'2026-10-25T09:44:56Z',
    'https://ac.nowcoder.com/acm/contest/142622/':'2026-10-25T09:44:56Z',
    'https://codeforces.com/gym/728862/':'2026-11-01T07:38:58Z',
}


def _project(row):
    result={key:value for key,value in row.items() if key in ROW_FIELDS}
    if row.get('schoolTraining') and not any(row.get(key) for key in ('addedAt','firstAdded','catalogAddedAt')):
        url=str(row.get('url') or '')
        for prefix,stamp in _LEGACY_ADDED.items():
            if url.startswith(prefix):
                result['catalogAddedAt']=stamp
                break
    return result


def catalogue_payload(data):
    """Project rows without dropping, sorting, renaming or mutating a record."""
    return {**data, 'rows': [_project(row) for row in data.get('rows', [])]}


def hub_payload(data):
    """List UI uses stable ID/URL arrays; omit the duplicate target index."""
    return {**data, 'notifications': [{key: value for key, value in notice.items() if key != 'targets'}
                                    for notice in data.get('notifications', [])]}
