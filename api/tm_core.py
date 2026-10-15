# Vercel Python Serverless Function: POST /api/tm_core  {"input": "111+11"}
#
# Runs the unary Turing machine for the expression and returns every step for
# the frontend to replay.  The machines themselves live in tm_machines.py, a
# verbatim copy of tm/machines.py from the turing_emulator repo.

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tm_machines import BLANK, HALT, get_machine, run  # noqa: E402

MAX_INPUT_LENGTH = 40
MAX_STEPS = 10_000
WINDOW_PADDING = 3
OPERATIONS = {'+': 'add', '-': 'subtract', '*': 'multiply'}
EXPRESSION = re.compile(r'^(1*)([-+*])(1*)$')


class Tape:
    """Unbounded tape stored sparsely; tracks the furthest cells the head reached."""

    def __init__(self, content):
        self.cells = dict(enumerate(content))
        self.head = 0
        self.low, self.high = 0, max(len(content) - 1, 0)

    def read(self):
        return self.cells.get(self.head, BLANK)

    def write(self, symbol):
        self.cells[self.head] = symbol

    def move(self, direction):
        self.head += {'L': -1, 'R': 1}.get(direction, 0)
        self.low = min(self.low, self.head)
        self.high = max(self.high, self.head)

    def window(self, low, high):
        return ''.join(self.cells.get(i, BLANK) for i in range(low, high + 1))


class MachineError(Exception):
    pass


def simulate(expression):
    """Run the machine for `expression`; return the response body as a dict."""
    match = EXPRESSION.match(expression)
    if not match or len(expression) > MAX_INPUT_LENGTH:
        raise ValueError(f"Input must look like 111+11, 111-11 or 11*11 "
                         f"(one operator, at most {MAX_INPUT_LENGTH} characters).")
    machine = get_machine(OPERATIONS[match.group(2)], 'unary', sep=match.group(2))

    # First pass finds how far the head travels so every frame shares one window.
    tape = Tape(expression)
    steps = 0
    last = None
    for last in run(machine, tape):
        steps += 1
        if steps > MAX_STEPS:
            raise MachineError(f'Stopped after {MAX_STEPS} steps; try smaller numbers.')
    if last is not None and last[4] != HALT:
        raise MachineError(f'Machine got stuck in state {last[0]} reading {last[1]!r}.')
    low, high = tape.low - WINDOW_PADDING, tape.high + WINDOW_PADDING

    tape = Tape(expression)
    history = [{'state': machine.start, 'tape_display': tape.window(low, high),
                'head_index': tape.head - low, 'step': 0}]
    for step, (_, _, _, _, next_state, _) in enumerate(run(machine, tape), start=1):
        history.append({'state': next_state, 'tape_display': tape.window(low, high),
                        'head_index': tape.head - low, 'step': step})

    ones = tape.window(tape.low, tape.high).count('1')
    return {'history': history, 'result': '1' * ones or '0', 'steps_taken': steps}


class handler(BaseHTTPRequestHandler):

    def _send(self, status, body=None):
        payload = b'' if body is None else json.dumps(body).encode()
        self.send_response(status)
        if body is not None:
            self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._send(204)

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length') or 0)
            data = json.loads(self.rfile.read(length) or b'{}')
            expression = str(data.get('input', '')).strip()
        except (ValueError, AttributeError):
            self._send(400, {'error': 'Request body must be JSON like {"input": "111+11"}.'})
            return
        try:
            self._send(200, simulate(expression))
        except (ValueError, MachineError) as e:
            self._send(400, {'error': str(e)})
