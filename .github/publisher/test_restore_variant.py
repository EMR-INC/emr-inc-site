"""Check that a normal publisher run accepts the approved form gateway and nothing else.

The scheduled publisher restores the private function from the serving
deployment. After the login form repair, the serving gateway is the approved
variant named in reviewed-release-lock.json, not the original lock digest.
These tests use synthetic bytes and synthetic locks with the same shape, so
they exercise restore() without network access or real function content.
"""
import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import restore

HERE = Path(__file__).parent
GATEWAY = 'api/_lib/ohpah/gateway.mjs'
SERVING = 'dpl_SyntheticServing1'


def entry(raw):
    return [len(raw), hashlib.sha256(raw).hexdigest()]


def sha1(raw):
    return hashlib.sha1(raw).hexdigest()


class RestoreVariant(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        root = Path(self.scratch.name)
        self.baseline = b'export const gateway = "baseline";\n'
        self.approved = b'export const gateway = "approved form repair";\n'
        self.other = b'export const helper = 1;\n'
        self.extra = b'export const reviewed = 1;\n'
        routes = [{'src': '^/$', 'dest': '/index.html'}, {'handle': 'filesystem'}]
        canonical = json.dumps(routes, sort_keys=True, separators=(',', ':')).encode()
        common = {'public_routes_sha256': hashlib.sha256(canonical).hexdigest(),
                  'insert_before': {'handle': 'filesystem'},
                  'integrated_routes': [{'src': '^/ohpah$', 'dest': '/api/ohpah-gateway'}]}
        original = dict(common, members={GATEWAY: entry(self.baseline), 'api/_lib/ohpah/helper.mjs': entry(self.other)})
        self.reviewed = dict(common, members={GATEWAY: entry(self.baseline), 'api/_lib/ohpah/helper.mjs': entry(self.other),
                                              'api/_lib/ohpah/reviewed.mjs': entry(self.extra)},
                             form_gateway_variant={'baseline': entry(self.baseline), 'approved': entry(self.approved)})
        self.locks = root / 'locks'
        self.locks.mkdir()
        (self.locks / 'release-lock.json').write_text(json.dumps(original))
        self.write_reviewed()
        patcher = mock.patch.object(restore, 'LOCK', self.locks / 'release-lock.json')
        patcher.start()
        self.addCleanup(patcher.stop)
        self.output = root / 'build' / '.vercel' / 'output'
        (self.output / 'static').mkdir(parents=True)
        # vercel build always leaves the public auth functions under functions/api.
        (self.output / 'functions' / 'api').mkdir(parents=True)
        (self.output / 'static' / 'index.html').write_text('public synthetic example')
        (self.output / 'config.json').write_text(json.dumps({'version': 3, 'routes': routes}))
        self.routes = routes

    def write_reviewed(self):
        (self.locks / 'reviewed-release-lock.json').write_text(json.dumps(self.reviewed))

    def serving(self, contents):
        blobs = {sha1(raw): raw for raw in contents.values()}

        def tree(names):
            nodes = {}
            for name in names:
                parts = (restore.PREFIX + name).split('/')
                level = nodes
                for part in parts[:-1]:
                    level = level.setdefault(part, {})
                level[parts[-1]] = sha1(contents[name])

            def emit(level):
                out = []
                for key, value in level.items():
                    if isinstance(value, dict):
                        out.append({'name': key, 'type': 'directory', 'children': emit(value)})
                    else:
                        out.append({'name': key, 'type': 'file', 'uid': value})
                return out
            return emit(nodes)

        def get(path):
            if path == '/v13/deployments/emr-inc.net':
                return {'id': SERVING, 'projectId': restore.PROJECT, 'ownerId': restore.TEAM,
                        'public': False, 'readyState': 'READY', 'target': 'production'}
            if path == '/v6/deployments/' + SERVING + '/files':
                return tree(contents)
            prefix = '/v8/deployments/' + SERVING + '/files/'
            if path.startswith(prefix):
                return {'data': base64.b64encode(blobs[path[len(prefix):]]).decode()}
            raise AssertionError('unexpected provider path ' + path)
        return get

    def contents(self, gateway):
        return {GATEWAY: gateway, 'api/_lib/ohpah/helper.mjs': self.other, 'api/_lib/ohpah/reviewed.mjs': self.extra}

    def restored_gateway(self):
        return (self.output / restore.FUNCTION / GATEWAY).read_bytes()

    def test_approved_form_gateway_is_carried_forward(self):
        result = restore.restore(self.output, 'emr-inc.net', self.serving(self.contents(self.approved)))
        self.assertEqual(result['source_deployment'], SERVING)
        self.assertEqual(result['verified_files'], 3)
        self.assertEqual(result['verified_bytes'], len(self.approved) + len(self.other) + len(self.extra))
        self.assertEqual(self.restored_gateway(), self.approved)
        config = json.loads((self.output / 'config.json').read_text())
        self.assertIn({'src': '^/ohpah$', 'dest': '/api/ohpah-gateway'}, config['routes'])

    def test_baseline_gateway_still_restores_for_rollback(self):
        restore.restore(self.output, 'emr-inc.net', self.serving(self.contents(self.baseline)))
        self.assertEqual(self.restored_gateway(), self.baseline)

    def test_any_other_gateway_is_rejected_and_nothing_is_written(self):
        tampered = b'export const gateway = "unreviewed";\n'
        with self.assertRaises(ValueError):
            restore.restore(self.output, 'emr-inc.net', self.serving(self.contents(tampered)))
        self.assertFalse((self.output / restore.FUNCTION).exists())
        self.assertEqual(json.loads((self.output / 'config.json').read_text())['routes'], self.routes)

    def test_approved_bytes_count_only_for_the_gateway_member(self):
        # Even a member pinned to the baseline digest may not take the approved bytes.
        self.reviewed['members']['api/_lib/ohpah/helper.mjs'] = entry(self.baseline)
        self.write_reviewed()
        contents = self.contents(self.baseline)
        contents['api/_lib/ohpah/helper.mjs'] = self.approved
        with self.assertRaises(ValueError):
            restore.restore(self.output, 'emr-inc.net', self.serving(contents))

    def test_variant_needs_the_matching_baseline(self):
        self.reviewed['form_gateway_variant']['baseline'] = entry(b'some other baseline\n')
        self.write_reviewed()
        with self.assertRaises(ValueError):
            restore.restore(self.output, 'emr-inc.net', self.serving(self.contents(self.approved)))

    def test_original_lock_does_not_accept_the_variant(self):
        contents = self.contents(self.approved)
        del contents['api/_lib/ohpah/reviewed.mjs']
        with self.assertRaises(ValueError):
            restore.restore(self.output, 'emr-inc.net', self.serving(contents))


class CommittedLocks(unittest.TestCase):
    def test_committed_variant_matches_the_reviewed_gateway_and_form_repair(self):
        reviewed = json.loads((HERE / 'reviewed-release-lock.json').read_text())
        variant = reviewed['form_gateway_variant']
        self.assertEqual(variant['baseline'], reviewed['members'][GATEWAY])
        self.assertEqual(variant['approved'], [8627, 'bccdd37b4a07c0ae74e22ce4797cd161c3626361fc7ac1bc677e95da8dd4757c'])
        self.assertEqual(sorted(variant), ['approved', 'baseline'])

    def test_original_lock_has_no_variant(self):
        original = json.loads((HERE / 'release-lock.json').read_text())
        self.assertNotIn('form_gateway_variant', original)


if __name__ == '__main__':
    unittest.main()
