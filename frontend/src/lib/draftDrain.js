// A failed or still-pending read cannot contain editor input before the
// editor becomes writable. Actual edits still require a successful save.
export const emptyUnloadedDraft=record=>Boolean(record&&!record.loaded&&record.version===0&&record.code==='');
