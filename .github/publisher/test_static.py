"""Exercise the same static staging step used by manual and scheduled publication."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from verify_public import site_file, static

class StaticSite(unittest.TestCase):
    def setUp(self):
        self.cwd = Path.cwd()
        self.scratch = tempfile.TemporaryDirectory()
        os.chdir(self.scratch.name)
        self.addCleanup(self.scratch.cleanup)
        self.addCleanup(os.chdir, self.cwd)
        self.output = Path('.vercel/output/static')
        self.output.mkdir(parents=True)
        paths = ['index.html','research.html','open-data.html','data/dispatch-views.json',
                 'play/lesson.js','assets/cover.png','internal/research.html','data/build.py',
                 '.github/publisher/helper.py','.agency/cache/notes.txt','scripts/tool.js','templates/notes.html']
        for name in paths:
            p = Path(name)
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('public synthetic example')
            destination = self.output / p
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, destination)
        for args in [['init','-q'],['add','--',*paths],
                     ['-c','user.name=Fixture','-c','user.email=fixture@invalid.test','commit','-qm','fixture']]:
            subprocess.run(['git',*args],check=True)

    def test_served_pages_survive_two_passes(self):
        static(self.output)
        static(self.output)
        self.assertTrue((self.output/'play/lesson.js').is_file())
        self.assertTrue((self.output/'internal/research.html').is_file())
        self.assertTrue(all(site_file(p.relative_to(self.output)) for p in self.output.rglob('*') if p.is_file()))
        self.assertTrue(Path('data/build.py').is_file())

    def test_missing_play_asset_is_rejected(self):
        (self.output/'play/lesson.js').unlink()
        with self.assertRaises(ValueError):
            static(self.output)

    def test_source_and_symlink_rejected(self):
        with self.assertRaises(ValueError):
            static(Path('.'))
        (self.output/'outside').symlink_to(self.cwd)
        with self.assertRaises(ValueError):
            static(self.output)

    def test_tampered_site_payload_stops_before_removal(self):
        (self.output/'assets/cover.png').write_text('different')
        with self.assertRaises(ValueError):
            static(self.output)
        self.assertTrue((self.output/'scripts/tool.js').exists())

if __name__ == '__main__':
    unittest.main()
