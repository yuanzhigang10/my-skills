"""Offline regression checks; real Cursor verification is separate."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import unittest
import uuid

spec = importlib.util.spec_from_file_location('advisor', Path(__file__).with_name('advisor.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


class AdvisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / 'repo'; self.repo.mkdir()
        (self.repo / 'code.py').write_text('x = 1\n')

    def tearDown(self):
        self.tmp.cleanup()

    def test_local_state_root(self):
        self.assertEqual(a.DEFAULT_STATE, Path.home() / 'Library' / 'Application Support' / 'cursor-advisor')

    def test_explicit_model_change_fails_before_cli_and_preserves_state(self):
        job = self.root / str(uuid.uuid4()); job.mkdir()
        a.save(job / 'session.json', {'model_id': 'gemini-4-argon-medium'})
        before = (job / 'session.json').read_bytes()
        with patch.object(sys, 'argv', ['advisor.py', 'consult', '--follow-up', job.name,
                '--state-root', str(self.root), '--model', a.DEFAULT_MODEL, '--task', 'synthetic']):
            with patch.object(a, 'verify_cli') as verify:
                with self.assertRaisesRegex(ValueError, 'keep the saved model'):
                    a.main()
                verify.assert_not_called()
        self.assertEqual((job / 'session.json').read_bytes(), before)

    def test_context_limits_and_sensitive_paths(self):
        for name in ['../outside.py', '/etc/passwd', '.env', '.codex/auth.json', 'private.key']:
            with self.assertRaises(ValueError):
                a.collect(self.repo, [name], None, 1000)
        with self.assertRaises(ValueError):
            a.collect(self.repo, ['code.py'], None, 1)
        outside = self.root / 'outside.py'; outside.write_text('secret')
        (self.repo / 'link.py').symlink_to(outside)
        with self.assertRaises(ValueError):
            a.collect(self.repo, ['link.py'], None, 1000)

    def test_snapshot_and_stale_source(self):
        package, hashes, files = a.collect(self.repo, ['code.py'], None, 1000)
        self.assertEqual(package['files'][0]['content'], 'x = 1\n')
        self.assertEqual(a.source_changes(self.repo, hashes), [])
        (self.repo / 'code.py').write_text('x = 2\n')
        self.assertEqual(a.source_changes(self.repo, hashes), ['code.py'])

    def test_schema_rejects_unstructured_and_invalid_location(self):
        valid = {'kind': 'review', 'summary': 'ok', 'findings': [], 'questions': [], 'limitations': [], 'next_steps': []}
        self.assertEqual(a.structured(json.dumps(valid), 'review'), valid)
        with self.assertRaises(ValueError): a.structured('prose', 'review')
        with self.assertRaises(ValueError): a.structured(json.dumps(valid), 'debug')
        valid['findings'] = [{'severity': 'high', 'title': 'bug', 'evidence': 'x', 'recommendation': 'fix', 'file': 'code.py', 'line': 0}]
        with self.assertRaises(ValueError): a.structured(json.dumps(valid), 'review')

    def run_fake(self, model='Claude Opus 5.5 300K Medium', tool=False, resume=False, model_id=None):
        job = self.root / str(uuid.uuid4()); (job / 'workspace').mkdir(parents=True)
        (job / 'workspace' / 'guard.json').write_text('{}')
        sid = str(uuid.uuid4())
        meta = {'repo': str(self.repo), 'cursor_session_id': sid if resume else None}
        a.save(job / 'session.json', meta)
        request = str(uuid.uuid4()); rd = job / 'runs' / request; rd.mkdir(parents=True)
        exe = self.root / ('fake-'+uuid.uuid4().hex)
        result = {'kind': 'review', 'summary': 'offline fixture', 'findings': [], 'questions': [], 'limitations': [], 'next_steps': []}
        events = [{'type': 'system', 'subtype': 'init', 'model': model, 'session_id': sid}]
        if tool: events.append({'type': 'tool_call', 'subtype': 'started', 'tool_call': {'writeToolCall': {}}})
        events.append({'type': 'result', 'subtype': 'success', 'is_error': False, 'result': json.dumps(result), 'session_id': sid})
        exe.write_text('#!/usr/bin/env python3\nimport sys,json\nargs=sys.argv[1:]\nassert "--force" not in args and "--yolo" not in args and args[args.index("--mode")+1]=="ask" and args[args.index("--sandbox")+1]=="enabled"\n' +
                       ('assert args[args.index("--resume")+1]=='+repr(sid)+'\n' if resume else '') +
                       'sys.stdin.read()\nfor event in '+repr(events)+': print(json.dumps(event),flush=True)\n')
        exe.chmod(0o700)
        a.save(rd / 'request.json', {'executable': str(exe), 'model': model_id or a.DEFAULT_MODEL, 'cli_version': 'offline',
                                  'timeout': 10, 'kind': 'review', 'source_hashes': {'code.py': a.hashlib.sha256((self.repo/'code.py').read_bytes()).hexdigest()}})
        (rd / 'prompt.txt').write_text('offline test')
        return job, request, sid

    def test_success_and_explicit_resume(self):
        job, request, sid = self.run_fake(resume=True)
        result = a.run(job, request)
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['cursor_session_id'], sid)
        self.assertFalse((job / 'running.lock').exists())

    def test_wrong_model_and_tool_calls_fail_closed(self):
        for params in [{'model': 'Claude Opus 4.8'}, {'tool': True}]:
            job, request, sid = self.run_fake(**params)
            with self.assertRaises(RuntimeError): a.run(job, request)
            saved = a.load(job / 'session.json')
            self.assertEqual(saved['status'], 'failed')
            self.assertEqual(saved['cursor_session_id'], sid)
            self.assertFalse((job / 'running.lock').exists())

    def test_existing_lock_not_stolen(self):
        job, request, _ = self.run_fake()
        (job / 'running.lock').mkdir()
        with self.assertRaises(FileExistsError): a.run(job, request)
        self.assertTrue((job / 'running.lock').exists())


    def test_model_selection_and_pinned_followups(self):
        self.assertEqual(a.select_model(None), a.DEFAULT_MODEL)
        self.assertEqual(a.select_model(None, 'gemini-4-argon-high'), 'gemini-4-argon-high')
        self.assertEqual(a.select_model('gemini-4-argon-medium'), 'gemini-4-argon-medium')
        for value in ['auto', 'gemini-4', 'gemini-4-argon-max']:
            with self.assertRaises(ValueError): a.select_model(value)
        with self.assertRaises(ValueError): a.select_model(a.DEFAULT_MODEL, 'gemini-4-argon-medium')
        with self.assertRaises(ValueError): a.select_model('gemini-4-argon-high', 'gemini-4-argon-medium')

    def test_argon_and_mismatched_init(self):
        job, request, _ = self.run_fake(model='Gemini 4 Argon Medium', model_id='gemini-4-argon-medium', resume=True)
        self.assertEqual(a.run(job, request)['model_id'], 'gemini-4-argon-medium')
        for label in ['Claude Opus 5.5 Medium', 'Gemini 4 Argon High']:
            job, request, _ = self.run_fake(model=label, model_id='gemini-4-argon-medium')
            with self.assertRaises(RuntimeError): a.run(job, request)



if __name__ == '__main__':
    unittest.main()
