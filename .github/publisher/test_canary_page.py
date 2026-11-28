"""The Canary link page is a reviewed public page; other new pages still need release review."""
from pathlib import Path
import os
import subprocess
import unittest

from verify_public import reviewed_input, site_file, verify

ROOT = Path(__file__).resolve().parents[2]

class CanaryPage(unittest.TestCase):
    def test_canary_page_is_a_reviewed_input_and_served(self):
        self.assertTrue(reviewed_input('canary.html'))
        self.assertTrue(site_file(Path('canary.html')))

    def test_other_new_pages_still_need_review(self):
        for name in ('unreviewed.html', 'canary/index.html', 'canary.js', 'data/canary.json',
                     'assets/page.html', 'scripts/tool.js'):
            self.assertFalse(reviewed_input(name), name)

    def test_assets_and_publisher_files_unchanged(self):
        self.assertTrue(reviewed_input('assets/brand/logo.png'))
        self.assertTrue(reviewed_input('.github/publisher/verify_public.py'))
        self.assertTrue(reviewed_input('.github/publisher/test_restore_variant.py'))
        self.assertTrue(reviewed_input('.github/publisher/test_canary_page.py'))
        self.assertFalse(reviewed_input('.github/publisher/other_helper.py'))
        self.assertFalse(site_file(Path('.github/publisher/verify_public.py')))

    def test_current_main_passes_the_release_input_check(self):
        cwd = Path.cwd()
        self.addCleanup(os.chdir, cwd)
        os.chdir(ROOT)
        if subprocess.run(['git', 'cat-file', '-e', 'HEAD:canary.html']).returncode:
            self.skipTest('canary.html not in this revision')
        verify()

if __name__ == '__main__':
    unittest.main()
