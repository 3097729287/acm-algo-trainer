"""Application catalog backed exclusively by SQLite after one-time migration."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import threading
from errors import APIError
from insights import canonical_url
from library import LibraryDatabase, source_fingerprint
from paths import LIBRARY_SEED, LIBRARY_SOURCE, STATE
from version import VERSION
import toolutil
import knowledge_dict as KD
import status_report as SR

class Store:
    def __init__(self, data_file=None, data_root=None, history_file=None, library_file=None):
        self.lock = threading.RLock()
        self._data_signature = None
        self._data_json = None
        self._data_base_key = None
        self._data_analysis = {}
        self._compact_signature = None
        self._compact_json = None
        self.token = __import__('secrets').token_urlsafe(32)
        self.data_root = str(Path(data_root or os.environ.get('TB_ARCHIVE_ROOT') or STATE / 'imports').resolve())
        self.extensions = None
        self.data_file = Path(data_file or Path(self.data_root) / '题解' / 'TB.md').resolve()
        state = Path(history_file).parent if history_file else self.data_file.parent if data_file else STATE
        target = Path(library_file or os.environ.get('TB_LIBRARY_DB') or state / 'tb-library.sqlite3').resolve()
        if data_file is None and not LIBRARY_SEED.is_file() and LIBRARY_SOURCE.is_dir():
            # The SQLite seed is a build artifact; rebuild it from the text source on first start.
            LibraryDatabase.from_source(LIBRARY_SOURCE, LIBRARY_SEED)
        self.library = LibraryDatabase(target)
        from progression import official_first_xp
        self.previous_first_xp = {canonical_url(row.get('url')) or row['id']:official_first_xp(row.get('difficulty'))
                                  for row in self.library.rows()}
        if data_file is None and LIBRARY_SEED.is_file() and target != LIBRARY_SEED.resolve():
            fingerprint = source_fingerprint(LIBRARY_SOURCE) if LIBRARY_SOURCE.is_dir() else None
            self.library.merge_seed(LIBRARY_SEED, fingerprint=fingerprint)
        if not self.library.rows() and self.data_file.is_file():
            from archive_import import import_archive
            import_archive(self.library, self.data_root, self.data_file)
        if data_file is None and not self.library.rows():
            raise APIError(503, '内置题库缺失或为空，请重新完整安装 TB')
        self.history_file = Path(history_file or STATE / 'history.jsonl')
        from contestmeta import ContestDates
        self.contest_dates = ContestDates(self)
        self._refresh_training_membership()

    def _refresh_training_membership(self):
        entries = [item for training in self.library.training_lists() for item in training.get('problems', [])]
        self._training_problem_ids = {item.get('problemId') for item in entries if item.get('problemId')}
        self._training_problem_urls = {canonical_url(item.get('url')) for item in entries if item.get('url')}

    def raw_rows(self):
        return self.library.rows(raw=True)

    def row(self, identity):
        found = self.library.find(identity)
        if found:
            return found['raw']
        remote = self.extensions.row(identity) if self.extensions else None
        if remote:
            return remote
        raise APIError(404, '没有找到这道题，请刷新列表')

    def contest_metadata(self, row, url=None):
        method = getattr(self.extensions, 'contest_metadata', None)
        return method(row, url) if callable(method) else self.contest_dates.for_row(row, url)

    def _enrich_knowledge(self, row):
        from knowledge import enrich_row
        cache = getattr(self, 'knowledge_analysis', None)
        return cache.apply(row) if cache else enrich_row(row)

    def encode_row(self, row, today=None):
        identity = row.get('_id') or row['场次'] + '::' + row['题号']
        found = self.library.find(identity)
        available, url = self._archive_info(row)
        return self._encode_record(row, found, available, url)

    def _encode_record(self, row, found, available, url):
        identity = row.get('_id') or row['场次'] + '::' + row['题号']
        if found:
            value = dict(found['encoded'])
        elif isinstance(row.get('_encoded'),dict):
            # Preserve captured categories and statement/editorial evidence.
            # Reconstructing from the old text-only 知识点 field erased them.
            from public_platforms import classify_contest
            value = classify_contest(row['_encoded'])
        else:
            value = {'id': identity, 'contest': row['场次'], 'problem': row['题号'], 'title': row['题名'],
                     'knowledge': row['知识点'], 'tags': KD.split_names(row['知识点']), 'difficulty': SR.difficulty_num(str(row['难度'])),
                     'platform': row.get('_platform', '其他'), 'series': row.get('_series', '其他'), 'url': row.get('_url'),
                     'source': 'remote', 'status': '未做', 'date': '', 'queue': None, 'solutionAvailable': False, 'solutionState': 'missing'}
        value.update(solutionAvailable=available, solutionState='available' if available else 'missing')
        if found is not None and 'content_ready' in found:
            value['catalogContentReady'] = bool(found['content_ready'])
        if url:
            value['url'] = url
        if identity in self._training_problem_ids or canonical_url(value.get('url')) in self._training_problem_urls:
            value['trainingListMember'] = True
        metadata = getattr(self.extensions, 'problem_metadata', None)
        if callable(metadata):
            patch = metadata(row, value.get('url'))
            # Generic fallback copy must not erase bundled evidence (e.g. a
            # Gym task explicitly recorded as unrated by Codeforces).
            if 'difficulty' in patch or not value.get('difficultySource'):
                value.update(patch)
            else:
                # Official tags can be published before ratings. Keep reviewed
                # local knowledge while allowing fresh first-party evidence.
                value.update({key: patch[key] for key in ('officialTags', 'officialTagsCheckedAt') if key in patch})
        dated_row = dict(row, _library_metadata=found['encoded']) if found else row
        value.update(self.contest_metadata(dated_row, value.get('url')))
        from contest_names import normalize_row
        from contest_policy import apply_visibility
        from difficulty import normalize_practice_difficulty
        return self._enrich_knowledge(apply_visibility(normalize_row(normalize_practice_difficulty(value))))

    def _archive_info(self, row):
        found = self.library.find(row.get('_id') or row['场次'] + '::' + row['题号'], canonical_url(row.get('_url')))
        return (self.library.has_solution(found['id']), found['url']) if found else (False, row.get('_url'))

    def _content_signature(self):
        extensions = self.extensions
        signature = getattr(extensions, 'catalog_signature', None)
        # An injected provider without an invalidation contract must stay fresh.
        if extensions is not None and not callable(signature):
            return None
        from knowledge import asset_path
        assets = []
        for name in ('problem_knowledge.json', 'public-knowledge.json','knowledge_catalog.json','knowledge_extensions.json','knowledge_topic_review.json'):
            try:
                stat = asset_path(name).stat()
                assets.append((stat.st_mtime_ns, stat.st_size))
            except FileNotFoundError:
                assets.append(None)
        return ('catalog-20261022-v4-unique', VERSION, self.library.content_signature(),
                signature() if signature else None, tuple(assets))

    def problem_catalog(self, identity):
        """Single-task reads do not rebuild the classified full catalogue.

        Preserve complete stored rows for aliases/contest guards; enrich only
        the requested row. Ordinary catalogue/workspace APIs keep data().
        """
        rows = self.library.rows()
        if self.extensions:
            identities = getattr(self.extensions, 'identity_rows', None)
            rows += identities() if callable(identities) else self.extensions.rows()
        try:
            selected = self.encode_row(self.row(identity))
            selected['id'] = identity
            rows = [row for row in rows if row['id'] != identity] + [selected]
        except Exception as error:
            if getattr(error, 'status', None) != 404:
                raise
        return rows

    def _analysis_signature(self):
        analysis = getattr(self, 'knowledge_analysis', None)
        return analysis.catalog_signature() if analysis else {}

    def data(self):
        with self.lock:
            public_signature = self._content_signature()
            analysis = self._analysis_signature()
            signature = (public_signature, tuple(sorted(analysis.items()))) if public_signature is not None else None
            cache_key = hashlib.sha256(repr(signature).encode()).hexdigest() if signature is not None else None
            base_key = hashlib.sha256(repr(public_signature).encode()).hexdigest() if signature is not None else None
            cache_path = self.library.path.with_name('tb-catalog-cache.json')
            if cache_key and self._data_json is None:
                from persistence import load_document
                try:
                    cached = load_document(cache_path, {})
                    if cached.get('baseSignature') == base_key and isinstance(cached.get('catalog'), str):
                        value = json.loads(cached['catalog'])
                        if (isinstance(value.get('rows'), list) and isinstance(value.get('categories'), list)
                                and isinstance(cached.get('analysis'), dict)):
                            self._data_json, self._data_base_key = cached['catalog'].encode('utf-8'), base_key
                            self._data_analysis = cached.get('analysis', {})
                            if cached.get('signature') == cache_key:
                                self._data_signature = signature
                except (OSError, ValueError, TypeError, AttributeError, sqlite3.Error):
                    pass  # An optional cache never prevents reading the library.
            if signature is not None and signature == self._data_signature and self._data_json is not None:
                # JSON decoding is much cheaper than reclassifying thousands of rows.
                # Every caller owns its result; personal/consumer mutations cannot
                # contaminate the shared public snapshot or another account.
                result = json.loads(self._data_json)
                result.update(today=dt.date.today().isoformat(), token=self.token)
                return result
            if base_key and self._data_base_key == base_key and self._data_json is not None:
                # Opening one statement can add knowledge evidence for one task.
                # Refresh only affected rows, rather than reclassifying the library.
                encoded = json.loads(self._data_json)['rows']
                for i, row in enumerate(encoded):
                    identity = row['id']
                    if self._data_analysis.get(identity) != analysis.get(identity):
                        record = self.library.find(identity)
                        raw = record['raw'] if record else self.row(identity)
                        encoded[i] = self._encode_record(raw, record, row['solutionAvailable'], row.get('url'))
            else:
                encoded = self._catalog_rows()
            revision = hashlib.sha256(json.dumps(encoded, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            result = {'rows': encoded, 'statuses': list(SR.STATES), 'categories': self.categories(),
                      'revision': revision, 'today': dt.date.today().isoformat(), 'token': self.token}
            if signature is not None and public_signature == self._content_signature() and analysis == self._analysis_signature():
                self._data_json = json.dumps({key: value for key, value in result.items() if key not in ('token', 'today')}, ensure_ascii=False).encode('utf-8')
                self._data_signature, self._data_base_key, self._data_analysis = signature, base_key, analysis
                from persistence import save_document
                try:
                    save_document(cache_path, {'signature': cache_key, 'baseSignature': base_key,
                                               'analysis': analysis, 'catalog': self._data_json.decode('utf-8')})
                except (OSError, sqlite3.Error):
                    pass
            return result

    def data_response_bytes(self, compact=False):
        """Serve a warm public snapshot without another large object graph.

        Invalidation is identical to data(); a response always appends the
        current session token/date, which are never saved in a public cache.
        """
        with self.lock:
            public = self._content_signature()
            analysis = self._analysis_signature()
            signature = (public, tuple(sorted(analysis.items()))) if public is not None else None
            if signature is None or signature != self._data_signature or self._data_json is None:
                value = self.data()
                # A writer may change the signature while data() is building.
                # The value just read is valid even when no stable cache exists.
                if compact:
                    from catalog_payload import catalogue_payload
                    value = catalogue_payload(value)
                return json.dumps(value, ensure_ascii=False).encode('utf-8')
            raw = self._data_json
            if compact:
                if self._compact_signature != self._data_signature or self._compact_json is None:
                    from catalog_payload import catalogue_payload
                    self._compact_json = json.dumps(catalogue_payload(json.loads(raw)), ensure_ascii=False).encode('utf-8')
                    self._compact_signature = self._data_signature
                raw = self._compact_json
            suffix = json.dumps({'today': dt.date.today().isoformat(), 'token': self.token}, ensure_ascii=False).encode('utf-8')
            return raw[:-1] + b', ' + suffix[1:]

    def _catalog_rows(self):
        self._refresh_training_membership()
        records = self.library.catalog()
        by_id = {record['id']: record for record in records}
        by_url = {}
        for record in records:
            key = canonical_url(record['url'])
            if key:
                by_url.setdefault(key, record)
        encoded = [self._encode_record(record['raw'], record, bool(record['available']), record['url'])
                   for record in records]
        seen_urls = {canonical_url(row.get('url')) for row in encoded if row.get('url')}
        seen_ids = {row['id'] for row in encoded}
        for row in self.extensions.rows() if self.extensions else []:
            key = canonical_url(row.get('url'))
            if row['id'] in seen_ids or key and key in seen_urls:
                continue
            source = by_id.get(row['id']) or by_url.get(key)
            encoded.append(self._encode_record(self.extensions.row(row['id']), by_id.get(row['id']),
                                               bool(source and source['available']), source['url'] if source else row.get('url')))
            seen_ids.add(row['id'])
            if key:
                seen_urls.add(key)
        from catalog_identity import unique_catalog_rows
        return unique_catalog_rows(encoded)

    def solution(self, identity):
        row = self.row(identity)
        found = self.library.find(identity, canonical_url(row.get('_url')))
        value = self.library.solution(found['id']) if found else None
        detailed = self.library.solution(found['id'], 'detailed') if found else None
        if not value and not detailed:
            raise APIError(404, '这道题尚未收录题解')
        value = value or {'markdown': '', 'path': '', 'images': {}, 'digest': ''}
        return {**value, 'title': found['encoded']['title'], 'url': found['url'],
                'detailedSolution': detailed}

    def update(self, body):
        raise APIError(410, '训练进度由提交记录产生，请使用运行或提交')

    def inbox(self, action=None):
        from archive_import import inbox
        return inbox(self, action)

    def categories(self):
        from knowledge import dictionary
        catalog = dictionary()
        groups, standards = catalog['groups'], set(catalog['names'])
        children = {child for parent, kids in groups.items() for child in kids if child != parent}
        def branch(name, ancestry=()):
            if name in ancestry:
                return {'name': name, 'children': [], 'tags': [name] if name in standards else []}
            nodes = [({'name': child, 'children': [], 'tags': [child] if child in standards else []} if child == name
                      else branch(child, ancestry + (name,))) for child in groups.get(name, [])]
            tags = ([name] if name in standards else []) + [tag for node in nodes for tag in node['tags']]
            return {'name': name, 'children': nodes, 'tags': list(dict.fromkeys(tags))}
        roots = [name for name in groups if name not in children]
        represented = set(groups) | children
        roots += [name for name in catalog['names'] if name not in represented]
        return [branch(name) for name in roots]
