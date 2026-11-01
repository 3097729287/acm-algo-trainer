"""Rehearse cross-updater failures using retained, disposable local fixtures."""
import json
import os
from pathlib import Path
from unittest.mock import patch
import uuid

import core7_deliver as delivery


def main():
    fixture=delivery.OUT/'delivery-guard-checks'/uuid.uuid4().hex
    target=fixture/'app'
    (target/'data').mkdir(parents=True)
    seed=target/'data/library.sqlite3';seed.write_bytes(b'fixture-public-seed')
    build=target/'BUILD-INFO.json';build.write_text('{"version":"fixture"}',encoding='utf-8')
    lease=fixture/'lease.json'
    held={'state':'held','pid':12345,'files':{'seed':{'path':str(seed)},'build':{'path':str(build)}}}
    before={path:path.read_bytes() for path in (seed,build)}
    passed=[]

    def blocked(operation):
        try:operation()
        except RuntimeError:return
        raise AssertionError('Operation ignored the held installation lease')

    with patch.object(delivery,'INSTALLATION_LEASE',lease):
        delivery.assert_installation_available(target)
        passed.append('absent lease allows an otherwise independent installation')
        lease.write_text(json.dumps(held),encoding='utf-8')
        # This must fail before reading a stage report or creating recovery files.
        blocked(lambda:delivery.apply(target))
        assert not (target/'recovery').exists()
        assert all(path.read_bytes()==value for path,value in before.items())
        passed.append('held lease rejects apply before any installation mutation')
        blocked(lambda:delivery.atomic_bytes(build,b'unwanted replacement'))
        assert not build.with_name(build.name+'.core7-staged').exists()
        assert build.read_bytes()==before[build]
        passed.append('held lease rejects metadata writes before staging bytes')
        delivery.assert_installation_available(fixture/'independent-app')
        passed.append('unrelated isolated app remains available for checks')
        lease.write_text('{"state":"released"}',encoding='utf-8')
        delivery.assert_installation_available(target)
        passed.append('explicit owner release is respected')
        if os.name=='nt':
            def hold_during_replace(*_):
                lease.write_text(json.dumps(held),encoding='utf-8')
                raise PermissionError('fixture: another updater acquired the file')
            with patch.object(delivery.os,'replace',side_effect=hold_during_replace),patch.object(delivery.subprocess,'run') as native:
                blocked(lambda:delivery.atomic_bytes(build,b'unwanted replacement'))
                native.assert_not_called()
            assert build.read_bytes()==before[build]
            passed.append('newly held lease cannot be bypassed by native metadata fallback')
        lease.write_text('{broken',encoding='utf-8')
        blocked(lambda:delivery.assert_installation_available(target))
        passed.append('unreadable lease blocks installation without guessing')

    root=fixture/'source';out=fixture/'authoring'
    (root/'data/library').mkdir(parents=True);out.mkdir()
    (root/'data/library/solution_methods.json').write_text('[]',encoding='utf-8')
    (out/'authored.json').write_text('[]',encoding='utf-8')
    with patch.object(delivery,'ROOT',root),patch.object(delivery,'OUT',out):
        first=delivery.delivery_folder(target)
        (first/'recovery').mkdir(parents=True)
        marker=first/'recovery/keep.txt';marker.write_text('retained recovery',encoding='utf-8')
        build.write_text('{"version":"next-fixture"}',encoding='utf-8')
        second=delivery.delivery_folder(target)
        assert first!=second
        seed.write_bytes(b'newer fixture public seed')
        third=delivery.delivery_folder(target)
        assert len({first,second,third})==3 and marker.read_text('utf-8')=='retained recovery'
        passed.append('changed build and seed each isolate the next stage and retain failed recovery')

    report={'passed':True,'checks':passed,'fixturesRetained':str(fixture)}
    delivery.dump(fixture/'report.json',report)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
