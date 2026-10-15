"""Tests for the /api/tm_core serverless function."""
import json
import os
import sys
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api'))
from tm_core import MAX_STEPS, MachineError, handler, simulate  # noqa: E402
from tm_machines import HALT  # noqa: E402


class TestSimulate(unittest.TestCase):

    def test_results(self):
        cases = {
            '111+11': 5, '+11': 2, '111+': 3, '+': 0,
            '111-11': 1, '11-111': 0, '111-111': 0, '1-': 1, '-': 0,
            '11*111': 6, '1*1': 1, '*11': 0, '11*': 0, '*': 0, '1111*111': 12,
        }
        for expression, expected in cases.items():
            with self.subTest(expression=expression):
                body = simulate(expression)
                self.assertEqual(body['result'], '1' * expected or '0')
                self.assertEqual(body['history'][-1]['state'], HALT)

    def test_history_shape(self):
        body = simulate('11+1')
        history = body['history']
        self.assertEqual(len(history), body['steps_taken'] + 1)
        self.assertEqual([h['step'] for h in history], list(range(len(history))))
        self.assertEqual(history[0]['state'], 'q0')
        self.assertIn('11+1', history[0]['tape_display'])
        widths = {len(h['tape_display']) for h in history}
        self.assertEqual(len(widths), 1, 'every frame should use the same tape window')
        for h in history:
            self.assertTrue(0 <= h['head_index'] < len(h['tape_display']))

    def test_invalid_input(self):
        for expression in ['', '11', '11+-1', '1+1+1', 'abc', '2+2', '1' * 41 + '+']:
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    simulate(expression)

    def test_step_limit(self):
        with self.assertRaises(MachineError):
            simulate('1' * 20 + '*' + '1' * 19)


class TestHandler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        handler.log_message = lambda *args: None
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def request(self, method, body=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_address[1])
        conn.request(method, '/api/tm_core', body=body, headers={'Content-Type': 'application/json'})
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return response, data

    def test_post(self):
        response, data = self.request('POST', json.dumps({'input': '111+11'}))
        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader('Access-Control-Allow-Origin'), '*')
        self.assertEqual(json.loads(data)['result'], '11111')

    def test_post_bad_expression(self):
        response, data = self.request('POST', json.dumps({'input': '1+1+1'}))
        self.assertEqual(response.status, 400)
        self.assertIn('error', json.loads(data))

    def test_post_not_json(self):
        response, data = self.request('POST', 'not json')
        self.assertEqual(response.status, 400)
        self.assertIn('error', json.loads(data))

    def test_options(self):
        response, data = self.request('OPTIONS')
        self.assertEqual(response.status, 204)
        self.assertEqual(data, b'')


if __name__ == '__main__':
    unittest.main()
