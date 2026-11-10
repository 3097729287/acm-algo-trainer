const VERDICTS = new Set(['AC', 'WA', 'CE', 'TLE', 'MLE', 'RE', 'OLE']);
const remoteId = value => /^[1-9]\d{0,19}$/.test(String(value ?? '')) ? String(value) : null;
export function createOfficialAttempt(sent, session) {
  return Object.freeze({...sent,sessionId:session.sessionId,
    ...(session.readOnlyRestore===true?{readOnlyRestore:true,code:null}:{})});
}
const sameContext = (row, attempt) => row.problemId === attempt.problemId
  && (row.contestId || null) === (attempt.contestId || null)
  && (row.reviewId == null || row.reviewId === attempt.reviewId)
  && (row.accountOwner == null || row.accountOwner === attempt.owner)
  && (row.sessionId == null || row.sessionId === attempt.sessionId)
  && (row.language == null || row.language === attempt.language || attempt.readOnlyRestore || attempt.manual);

function receiptId(row) {
  const message = /^原站确认提交 #([1-9]\d{0,19})(?:\s|$)/.exec(row.message || '')?.[1];
  const values = [row.submissionId, row.officialSubmissionId, message].filter(value => value != null);
  return values.length && values.every(value => remoteId(value) === remoteId(values[0])) ? remoteId(values[0]) : null;
}

// History or a submission event is evidence only for the frozen request that
// received this exact official ID. A previous CE for the same code is not enough.
export function officialReceiptMatches(attempt, session, row, owner, boundReceipt = false) {
  if (!attempt || attempt.owner !== owner || attempt.sessionId !== session?.sessionId
      || !remoteId(session.submissionId) || !row || row.scope !== 'official' || row.mode !== 'submit'
      || !VERDICTS.has(row.verdict) || typeof row.finishedAt !== 'string' || !Number.isFinite(Date.parse(row.finishedAt))
      || !sameContext(row, attempt) || receiptId(row) !== remoteId(session.submissionId)) return false;
  // A restored/manual session's original source belongs to the backend, not
  // the current editor. Only its own attached receipt can supply that source.
  return (typeof attempt.code === 'string' && row.code === attempt.code)
    || (boundReceipt && (attempt.readOnlyRestore || attempt.manual) && typeof row.code === 'string');
}

export function reconcileOfficialSession(attempt, previous, incoming, rows, owner) {
  if (!attempt || attempt.owner !== owner || incoming?.sessionId !== attempt.sessionId
      || incoming.accountOwner != null && incoming.accountOwner !== owner
      || incoming.problemId != null && incoming.problemId !== attempt.problemId) return previous;
  const oldId = remoteId(previous?.submissionId), newId = remoteId(incoming.submissionId);
  if (oldId && incoming.submissionId != null && oldId !== newId) return previous;
  if (previous?.status === 'closed' || previous?.status === 'finished' && incoming.status !== 'closed') return previous;
  let next = incoming === previous ? previous : { ...previous, ...incoming, ...(oldId ? { submissionId: oldId } : {}) };
  if (incoming.status === 'finished' && (!remoteId(next.submissionId) || !VERDICTS.has(next.verdict))) return previous;
  if (incoming.submission && !officialReceiptMatches(attempt, next, incoming.submission, owner, true)) return previous;
  const receipt = [next.submission, ...(rows || [])].find(row => officialReceiptMatches(attempt, next, row, owner, row === incoming.submission));
  if (receipt && next.status !== 'closed') next = { ...next, status: 'finished', verdict: receipt.verdict, submission: receipt };
  return next;
}
