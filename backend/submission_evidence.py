"""Backend-only source-presence evidence; never hydrate historical code."""

def source_present(record):
    if record.get('sourcePresent') is True: return True
    code = record.get('code')
    if not isinstance(code, str) or not code.strip(): return False
    if code.startswith('\x00TB-CODE-V2:'):
        from account_chunks import code_reference
        from training import ServiceError
        try:
            reference = code_reference(code)
            return bool(reference and reference['bytes'] > 0)
        except ServiceError:
            return False
    return True


def annotate_sources(records, connection):
    """Derive the flag from SQLite, discarding any caller-supplied annotation.

    A private, validated code-reference row proves source was saved even when a
    new device has not downloaded its immutable historical archive. Public
    receipts without a source or that private reference remain unqualified.
    """
    rows = [{key: value for key, value in dict(record).items() if key != 'sourcePresent'} for record in records]
    pending = {row.get('id'): row for row in rows if not source_present(row) and row.get('id')}
    if pending and connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='account_sync_code_refs'").fetchone():
        from account_chunks import code_reference
        from training import ServiceError
        for identity, encoded in connection.execute('SELECT submission_id,reference FROM account_sync_code_refs'):
            if identity not in pending: continue
            try:
                reference = code_reference(encoded)
                if reference and reference['bytes'] > 0: pending[identity]['sourcePresent'] = True
            except ServiceError:
                continue
    return rows
