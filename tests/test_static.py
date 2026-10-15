"""Checks that the favicon files exist and that Vercel serves them instead of index.html."""
import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICONS = {'favicon.ico': b'\x00\x00\x01\x00', 'favicon.png': b'\x89PNG', 'apple-touch-icon.png': b'\x89PNG'}


class TestFavicon(unittest.TestCase):

    def setUp(self):
        with open(os.path.join(ROOT, 'vercel.json')) as f:
            self.config = json.load(f)

    def test_files_exist(self):
        for name, magic in ICONS.items():
            with self.subTest(name=name):
                with open(os.path.join(ROOT, name), 'rb') as f:
                    self.assertTrue(f.read(4).startswith(magic))

    def test_built_and_routed_before_catch_all(self):
        built = {b['src'] for b in self.config['builds']}
        routes = self.config['routes']
        catch_all = next(i for i, r in enumerate(routes) if r['src'] == '/(.*)')
        for name in ICONS:
            with self.subTest(name=name):
                self.assertIn(name, built)
                matching = [i for i, r in enumerate(routes) if re.fullmatch(r['src'], '/' + name)]
                self.assertLess(matching[0], catch_all, f'/{name} would be rewritten to index.html')

    def test_linked_from_page(self):
        with open(os.path.join(ROOT, 'index.html')) as f:
            html = f.read()
        for name in ICONS:
            with self.subTest(name=name):
                self.assertIn(f'href="/{name}"', html)


if __name__ == '__main__':
    unittest.main()
