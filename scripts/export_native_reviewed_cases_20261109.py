"""Freeze the fifteen fixed public local profiles; Python is authoring only.

No personal database, reference program, HTTP service, arbitrary script or OJ
submission is opened. The production Rust consumer only reads the frozen data.
"""
import argparse
import gzip
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'backend-rust/resources/reviewed_cases'
SOURCE_SHA256 = '20fd6a302157ff9b9cefb757a5bda9d287fde6d23aed37a83a07a8e8fb3b7741'
LEGACY_CASE_OUTPUT = 32 * 1024 * 1024
ORIGINAL_SAMPLE_OUTPUT_ALLOWANCE = 1024 * 1024
BLOCK = 65536


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode()


def canonical_output_bound(case, checker):
    if checker == 'Inequality' and case['output'].split()[0] == 'Yes':
        n = int(case['input'].split(None, 1)[0])
        return 4 + n * (len(str(n)) + 1)
    if checker == 'Gcd':
        tests = int(case['input'].split(None, 1)[0])
        return tests * 40  # Two integers <= 10^18 and two separators.
    return len(case['output'].encode())


def export(check=False):
    source = ROOT / 'backend/reviewed_cases.py'
    canonical = source.read_text('utf8').encode()
    if sha(canonical) != SOURCE_SHA256:
        raise ValueError('Public oracle changed; review the new source before exporting')
    policy = json.loads((ROOT / 'backend/resources/native-reviewed-profiles.json').read_text('utf8'))
    if policy['sourceSha256'] != SOURCE_SHA256 or policy['normalization'] != 'utf8-lf':
        raise ValueError('Fixed native profile policy does not match the reviewed oracle')
    sys.path.insert(0, str(ROOT / 'backend'))
    oracle = importlib.import_module('reviewed_cases')
    identities = policy['ids']
    if len(identities) != 15 or len(set(identities)) != 15 or set(identities) != set(oracle.PROFILES):
        raise ValueError('Only the fifteen explicitly reviewed identities may be exported')
    if not check:
        cleanup = json.loads((ROOT / 'docs/verification/native-reviewed-judge-20261109/cleanup.json').read_text('utf8'))
        if not cleanup['checkedBeforeNewContent']:
            raise ValueError('Missing cleanup preflight')
    expected_files = {'manifest.json', 'packs.rs'} | {f'profile-{index:02}.json.gz' for index in range(15)}
    if DESTINATION.exists():
        unknown = {p.name for p in DESTINATION.iterdir()} - expected_files
        if unknown:
            raise ValueError('Review unexpected owned-directory files before changing content: ' + repr(sorted(unknown)))
    outputs = {}
    profiles = []
    arms = []
    for index, identity in enumerate(identities):
        cases, selected = oracle.build(identity)
        checker = ('Exact' if selected is None else 'Inequality' if selected is oracle.inequality_checker
                   else 'Gcd' if selected is oracle.gcd_checker else None)
        if checker is None or not cases or len(cases) > 200:
            raise ValueError('Unexpected public checker/case inventory')
        for case in cases:
            if set(case) != {'name', 'input', 'output'} or not all(isinstance(s, str) for s in case.values()):
                raise ValueError('Unexpected public case shape')
        fixture = {'schema': 1, 'profile_id': identity, 'source_sha256': SOURCE_SHA256,
                   'seed': 20261008, 'checker': checker, 'cases': cases}
        raw = encoded(fixture)
        packed = gzip.compress(raw, compresslevel=9, mtime=0)
        filename = f'profile-{index:02}.json.gz'
        outputs[filename] = packed
        output_bound = sum(canonical_output_bound(case, checker) for case in cases)
        # This is an aggregate budget: preserve the ordinary original-sample
        # allowance, then add the canonical bounds for every extra case.
        budget = ORIGINAL_SAMPLE_OUTPUT_ALLOWANCE + ((output_bound + BLOCK - 1) // BLOCK) * BLOCK
        if budget > LEGACY_CASE_OUTPUT or len(raw) > 64 * 1024 * 1024:
            raise ValueError('Reviewed data exceeds the explicit legacy-derived ceilings')
        record = {'profile_id': identity, 'coverage': oracle.PROFILES[identity], 'checker': checker,
                  'file': filename, 'compressed_bytes': len(packed), 'compressed_sha256': sha(packed),
                  'raw_bytes': len(raw), 'raw_sha256': sha(raw), 'case_count': len(cases),
                  'input_bytes': sum(len(case['input'].encode()) for case in cases),
                  'expected_output_bytes': sum(len(case['output'].encode()) for case in cases),
                  'max_input_bytes': max(len(case['input'].encode()) for case in cases),
                  'max_expected_output_bytes': max(len(case['output'].encode()) for case in cases),
                  'canonical_extra_output_bound_bytes': output_bound, 'max_output_bytes': budget}
        profiles.append(record)
        arms.append('        ' + json.dumps(identity, ensure_ascii=False)
                    + ' => Some(include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/resources/reviewed_cases/'
                    + filename + '"))),')
    manifest = {'schema': 1, 'source': 'backend/reviewed_cases.py', 'source_sha256': SOURCE_SHA256,
                'seed': 20261008, 'oracle_executed_only_during_authoring': True,
                'production_executes_python': False, 'original_samples_included': False,
                'scope': 'local-reviewed-cases; never official AC or reward evidence',
                'legacy_per_case_output_limit_bytes': LEGACY_CASE_OUTPUT,
                'original_sample_output_allowance_bytes': ORIGINAL_SAMPLE_OUTPUT_ALLOWANCE,
                'output_budget_rule': 'aggregate original sample allowance 1 MiB + sum of canonical extra-output bounds rounded up to 64 KiB; capped by the old runner 32 MiB ceiling',
                'profiles': profiles,
                'total_cases': sum(p['case_count'] for p in profiles),
                'total_compressed_bytes': sum(p['compressed_bytes'] for p in profiles),
                'total_raw_bytes': sum(p['raw_bytes'] for p in profiles),
                'max_profile_raw_bytes': max(p['raw_bytes'] for p in profiles),
                'max_case_input_bytes': max(p['max_input_bytes'] for p in profiles),
                'max_case_expected_output_bytes': max(p['max_expected_output_bytes'] for p in profiles)}
    outputs['manifest.json'] = encoded(manifest)
    outputs['packs.rs'] = ('// Generated fixed public identities; never match a title or tags.\n'
                           'fn packed_bytes(identity: &str) -> Option<&\'static [u8]> {\n    match identity {\n'
                           + '\n'.join(arms) + '\n        _ => None,\n    }\n}\n').encode()
    if check:
        for name, raw in outputs.items():
            if not (DESTINATION / name).is_file() or (DESTINATION / name).read_bytes() != raw:
                raise ValueError('Frozen native data differs from the exact reviewed oracle: ' + name)
    else:
        DESTINATION.mkdir(parents=True, exist_ok=True)
        for name, raw in outputs.items():
            path = DESTINATION / name
            if path.exists() and path.read_bytes() != raw:
                raise ValueError('Review and clean the superseded frozen pack before replacing it: ' + name)
            path.write_bytes(raw)
    print(json.dumps({key: value for key, value in manifest.items() if key != 'profiles'}, ensure_ascii=False))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Recompute public old-oracle results and require byte-identical frozen packs')
    export(parser.parse_args().check)
