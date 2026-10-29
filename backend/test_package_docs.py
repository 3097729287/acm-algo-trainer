"""Shipped manuals resolve locally or point to the exact release source tag."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_docs',ROOT/'scripts/build_release.py')
release=importlib.util.module_from_spec(spec);spec.loader.exec_module(release)


class PackageDocumentTests(unittest.TestCase):
    def test_relative_manual_and_version_pinned_source_links(self):
        with tempfile.TemporaryDirectory(prefix='tb-package-docs-') as temporary:
            root=Path(temporary);docs=root/'docs';docs.mkdir();target=root/'package';target.mkdir()
            (docs/'accounts.md').write_text('# Account','utf8')
            (docs/'算法.md').write_text('# Public algorithm','utf8')
            source=docs/'usage.md';source.write_text('[Account](accounts.md#offline) [Math](%E7%AE%97%E6%B3%95.md) [External](https://example.org/a) [Here](#here)','utf8')
            release.package_document(source,target/'使用说明.md',version='1.4.29',source_root=root)
            text=(target/'使用说明.md').read_text('utf8')
            self.assertIn('[Account](accounts.md#offline)',text)
            self.assertIn('/blob/v1.4.29/docs/%E7%AE%97%E6%B3%95.md',text)
            self.assertIn('[External](https://example.org/a)',text)
            self.assertIn('[Here](#here)',text)
            source.write_text('[Missing](missing.md)','utf8')
            with self.assertRaises(RuntimeError): release.package_document(source,target/'使用说明.md',version='1.4.29',source_root=root)

    def test_actual_current_manuals_have_no_dangling_package_links(self):
        with tempfile.TemporaryDirectory(prefix='tb-current-manuals-') as temporary:
            package=Path(temporary)
            for source,target in release.PACKAGE_DOCUMENTS.items():
                release.package_document(ROOT/'docs'/source,package/target,version='1.4.29')
            release.check_package_documents(package)
            guide=(package/'使用说明.md').read_text('utf8')
            self.assertNotIn('正在准备',guide)
            self.assertNotIn('1.4.1-win64',guide)
            self.assertNotIn('releases/1.4.28.md)',guide)


if __name__=='__main__': unittest.main()
