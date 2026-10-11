import base64
from pathlib import Path
import tempfile
import unittest

from educational_images import collect_images, image_targets, MAX_IMAGE_BYTES


class EducationalImageTests(unittest.TestCase):
    def test_nested_and_escaped_alt_brackets_are_imported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
            (root / 'tree.svg').write_bytes(raw)
            markdown = r'''![flow [1] with [nested [labels]]](tree.svg)
![literal \[brackets\]](tree.svg)
![nested [reference]][tree]
![outer ![inner](missing.svg)](tree.svg)
![unresolved outer ![inner](tree.svg)]
[tree]: tree.svg
'''
            images = collect_images(markdown, root / 'lesson.md', root)
            self.assertEqual(set(images), {'tree.svg'})
            self.assertEqual(base64.b64decode(images['tree.svg'].split(',')[1]), raw)

    def test_escaped_image_markers_do_not_require_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # These are ordinary text/links, so missing files must not block import.
            for markdown in (r'\![example](missing.svg)', r'\\\![example](missing.svg)',
                             r'!\[example](missing.svg)'):
                with self.subTest(markdown=markdown):
                    self.assertEqual(collect_images(markdown, root / 'lesson.md', root), {})
            # Two backslashes represent one literal backslash; the image remains active.
            self.assertEqual(image_targets(r'\\![example](tree.svg)'), ['tree.svg'])

    def test_markdown_paths_and_code_are_distinguished(self):
        md = '''![树](<配图/一 棵树.svg> "中文图")
![步骤](fig/step(1).png)
![引用][树]
![短名]
[树]: <配图/二.svg> "title"
[短名]: three.gif
`![代码](not.png)`
```md
![代码块](no.svg)
```
'''
        self.assertEqual(image_targets(md), ['配图/一 棵树.svg', 'fig/step(1).png', '配图/二.svg', 'three.gif'])

    def test_unicode_svg_and_all_browser_formats_survive_source_removal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            folder = root / '配图'; folder.mkdir()
            raw = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>'
            (folder / '一 棵树.svg').write_bytes(raw)
            src = root / 'test.md'
            images = collect_images('![tree](<配图/一 棵树.svg>)\n![same](%E9%85%8D%E5%9B%BE/%E4%B8%80%20%E6%A3%B5%E6%A0%91.svg)', src, root)
            self.assertEqual(len(images), 2)
            (folder / '一 棵树.svg').unlink()
            for value in images.values():
                self.assertTrue(value.startswith('data:image/svg+xml;base64,'))
                self.assertEqual(base64.b64decode(value.split(',')[1]), raw)
            for extension, mime in [('png','png'),('jpg','jpeg'),('jpeg','jpeg'),('gif','gif'),('webp','webp'),('avif','avif'),('bmp','bmp')]:
                (root / ('image.' + extension)).write_bytes(b'image-fixture')
                saved = collect_images(f'![example](image.{extension})', src, root)
                self.assertTrue(saved['image.'+extension].startswith('data:image/'+mime+';base64,'))

    def test_missing_outside_and_oversized_fail_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); src = root / 'test.md'
            for url in ['../private.svg', '%2e%2e/private.svg', 'missing.svg', 'script.html']:
                with self.subTest(url=url), self.assertRaises(ValueError):
                    collect_images(f'![x]({url})', src, root)
            huge = root / 'large.png'
            with huge.open('wb') as out: out.truncate(MAX_IMAGE_BYTES + 1)
            with self.assertRaises(ValueError): collect_images('![x](large.png)', src, root)
            self.assertEqual(collect_images('![remote](https://example.org/x.png)', src, root), {})


if __name__ == '__main__': unittest.main()
