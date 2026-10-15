"""
Turing machines for the arithmetic operations.

Every operation is a plain transition table

    delta(state, read) -> (write, move, next_state)

and a single interpreter, `run`, executes any table on any tape.  The tape is
only ever changed by applying a rule: nothing here computes the answer in
Python and writes it onto the tape.

This module has no project imports, so the same file is copied verbatim into
the web demo (TM-Emulator-Semester-Project/api/tm_machines.py).  Keep the two
copies identical.

Tape conventions (head starts on the first cell of the input):
    unary   1^a <sep> 1^b     result 1^r          (r = 0 is an empty tape)
    binary  a # b             result r in binary  (no leading zeros, 0 is "0")
Binary operands are written MSB first and 0 is written as the empty string.
Subtraction is monus: a - b is clamped to 0 when b > a.
"""

BLANK = '_'
HALT = 'q_accept'
LEFT, RIGHT, STAY = 'L', 'R', 'S'

UNARY_SEP = '0'
BINARY_SEP = '#'


class Machine:
    """A deterministic single-tape Turing machine given by its transition table."""

    def __init__(self, name, start='q0'):
        self.name = name
        self.start = start
        self.rules = {}  # (state, read) -> (write, move, next_state, note)

    def add(self, state, reads, write, move, next_state, note=''):
        """Add one rule for each symbol in `reads`. write=None writes back the symbol read."""
        for sym in reads:
            key = (state, sym)
            if key in self.rules:
                raise ValueError(f'{self.name}: duplicate rule for {key}')
            self.rules[key] = (sym if write is None else write, move, next_state, note)

    def states(self):
        found = {self.start, HALT}
        for (state, _), (_, _, next_state, _) in self.rules.items():
            found.update((state, next_state))
        return sorted(found)

    def alphabet(self):
        found = set()
        for (_, read), (write, _, _, _) in self.rules.items():
            found.update((read, write))
        return sorted(found)

    def table(self):
        """Rules as (state, read, write, move, next_state, note) rows, grouped by state."""
        return [(s, r) + rule for (s, r), rule in self.rules.items()]


def run(machine, tape):
    """
    Execute `machine` on `tape`, one rule per step.

    `tape` needs read(), write(symbol) and move('L' | 'R' | 'S').  Each step is
    applied to the tape first and then yielded as
    (state, read, write, move, next_state, note).  The generator ends when the
    machine enters HALT, or after yielding a step with next_state=None if no
    rule matches (the machine is stuck and rejects).
    """
    state = machine.start
    while state != HALT:
        read = tape.read()
        rule = machine.rules.get((state, read))
        if rule is None:
            yield (state, read, None, None, None, 'no rule for this (state, symbol): stuck')
            return
        write, move, next_state, note = rule
        tape.write(write)
        tape.move(move)
        yield (state, read, write, move, next_state, note)
        state = next_state


# --- Unary machines ---------------------------------------------------------

def unary_add(sep=UNARY_SEP):
    """1^a sep 1^b -> 1^(a+b): turn the separator into a 1, then erase the last 1."""
    m = Machine('unary add')
    m.add('q0', '1', None, RIGHT, 'q0', 'skip a')
    m.add('q0', sep, '1', RIGHT, 'q1', 'replace separator with 1')
    m.add('q1', '1', None, RIGHT, 'q1', 'skip b')
    m.add('q1', BLANK, None, LEFT, 'q2', 'reached right end')
    m.add('q2', '1', BLANK, LEFT, 'q3', 'erase the extra 1')
    m.add('q3', '1', None, LEFT, 'q3', 'return to start')
    m.add('q3', BLANK, None, RIGHT, HALT, 'halt on first cell of result')
    return m


def unary_subtract(sep=UNARY_SEP):
    """1^a sep 1^b -> 1^max(a-b, 0): repeatedly erase the last 1 of b and the first 1 of a."""
    m = Machine('unary subtract')
    m.add('q0', '1' + sep, None, RIGHT, 'q0', 'go to right end')
    m.add('q0', BLANK, None, LEFT, 'q1', 'reached right end')
    m.add('q1', '1', BLANK, LEFT, 'q2', 'erase last 1 of b')
    m.add('q1', sep, BLANK, LEFT, 'q5', 'b used up: erase separator')
    m.add('q2', '1' + sep, None, LEFT, 'q2', 'go to left end')
    m.add('q2', BLANK, None, RIGHT, 'q3', 'reached left end')
    m.add('q3', '1', BLANK, RIGHT, 'q0', 'erase first 1 of a')
    m.add('q3', sep, BLANK, RIGHT, 'q4', 'a used up first: result is 0')
    m.add('q4', '1', BLANK, RIGHT, 'q4', 'erase rest of b')
    m.add('q4', BLANK, None, STAY, HALT, 'halt with empty tape')
    m.add('q5', '1', None, LEFT, 'q5', 'return to start')
    m.add('q5', BLANK, None, RIGHT, HALT, 'halt on first cell of result')
    return m


def unary_multiply(sep=UNARY_SEP):
    """
    1^a sep 1^b -> 1^(a*b).

    A '=' is placed after b and the product is built to its right.  For each 1
    of b (marked Y) the machine copies a one 1 at a time (each copied 1 of a
    is marked X), then restores the X's.  Finally everything up to and
    including '=' is erased.
    """
    m = Machine('unary multiply')
    m.add('q0', '1' + sep, None, RIGHT, 'q0', 'go to right end')
    m.add('q0', BLANK, '=', LEFT, 'q1', 'mark start of product with =')
    m.add('q1', '1' + sep, None, LEFT, 'q1', 'go to left end')
    m.add('q1', BLANK, None, RIGHT, 'q2', 'reached left end')
    m.add('q2', '1', None, RIGHT, 'q2', 'skip a')
    m.add('q2', sep, None, RIGHT, 'q3', 'enter b')
    m.add('q3', 'Y', None, RIGHT, 'q3', 'skip used 1s of b')
    m.add('q3', '1', 'Y', LEFT, 'q4', 'use next 1 of b: copy a once')
    m.add('q3', '=', None, LEFT, 'q9', 'b used up: clean up')
    m.add('q4', 'Y1' + sep, None, LEFT, 'q4', 'go to left end')
    m.add('q4', BLANK, None, RIGHT, 'q5', 'reached left end')
    m.add('q5', 'X', None, RIGHT, 'q5', 'skip copied 1s of a')
    m.add('q5', '1', 'X', RIGHT, 'q6', 'copy this 1 of a')
    m.add('q5', sep, None, LEFT, 'q8', 'all of a copied: restore it')
    m.add('q6', '1Y=' + sep, None, RIGHT, 'q6', 'go to end of product')
    m.add('q6', BLANK, '1', LEFT, 'q7', 'append 1 to product')
    m.add('q7', '1Y=' + sep, None, LEFT, 'q7', 'return to a')
    m.add('q7', 'X', None, RIGHT, 'q5', 'back at copied 1s of a')
    m.add('q8', 'X', '1', LEFT, 'q8', 'restore 1 of a')
    m.add('q8', BLANK, None, RIGHT, 'q2', 'a restored')
    m.add('q9', 'Y1' + sep, None, LEFT, 'q9', 'go to left end')
    m.add('q9', BLANK, None, RIGHT, 'q10', 'reached left end')
    m.add('q10', 'Y1' + sep, BLANK, RIGHT, 'q10', 'erase operands')
    m.add('q10', '=', BLANK, RIGHT, HALT, 'erase =, halt on first cell of result')
    return m


# --- Binary machines --------------------------------------------------------
#
# Add and subtract work bit by bit from the least significant end: take the
# last bit of b (erasing it), carry the bit and the carry/borrow in the
# state, walk left to the lowest unprocessed bit of a, write the result bit
# there as a marked symbol (O = 0, I = 1) and go back for the next bit of b.
# States are named with their carry/borrow and the bit being carried, e.g.
# 'to_a_c1_b0' = "walking to a with carry 1 and b-bit 0".

def _strip_leading_zeros(m, state):
    """From the leftmost result cell: erase leading 0s; an all-zero result becomes '0'."""
    m.add(state, '0', BLANK, RIGHT, state, 'erase leading 0')
    m.add(state, '1', None, STAY, HALT, 'halt on first cell of result')
    m.add(state, BLANK, '0', STAY, HALT, 'result is 0')


def _binary_add_or_subtract(name, subtract):
    m = Machine(name, start='seek_end_c0')
    for c in (0, 1):
        m.add(f'seek_end_c{c}', '01OI#', None, RIGHT, f'seek_end_c{c}', 'go to right end')
        m.add(f'seek_end_c{c}', BLANK, None, LEFT, f'take_b_c{c}', 'reached right end')
        for beta in (0, 1):
            m.add(f'take_b_c{c}', str(beta), BLANK, LEFT, f'to_sep_c{c}_b{beta}',
                  f'take lowest bit of b ({beta})')
            m.add(f'to_sep_c{c}_b{beta}', '01', None, LEFT, f'to_sep_c{c}_b{beta}', 'skip rest of b')
            m.add(f'to_sep_c{c}_b{beta}', '#', None, LEFT, f'to_a_c{c}_b{beta}', 'cross separator')
            m.add(f'to_a_c{c}_b{beta}', 'OI', None, LEFT, f'to_a_c{c}_b{beta}', 'skip finished bits')
            for alpha_sym, alpha in (('0', 0), ('1', 1), (BLANK, 0)):
                if subtract:
                    d = alpha - beta - c
                    out, carry = d % 2, int(d < 0)
                    what = f'{alpha}-{beta}-{c}'
                else:
                    total = alpha + beta + c
                    out, carry = total % 2, total // 2
                    what = f'{alpha}+{beta}+{c}'
                m.add(f'to_a_c{c}_b{beta}', alpha_sym, 'OI'[out], RIGHT, f'seek_end_c{carry}',
                      f'{what}: write {out}, {"borrow" if subtract else "carry"} {carry}')

    # b used up.
    m.add('take_b_c0', '#', BLANK, LEFT, 'unmark', 'b used up: erase separator')
    m.add('take_b_c1', '#', None, LEFT, 'ripple', 'b used up: ' + ('borrow' if subtract else 'carry') + ' into a')
    m.add('ripple', 'OI', None, LEFT, 'ripple', 'skip finished bits')
    if subtract:
        m.add('ripple', '0', 'I', LEFT, 'ripple', '0-1: write 1, borrow on')
        m.add('ripple', '1', 'O', RIGHT, 'back_to_sep', '1-1: write 0, borrow done')
        m.add('ripple', BLANK, None, RIGHT, 'erase_all', 'borrow past top of a: b > a, result is 0')
        m.add('erase_all', '01OI', BLANK, RIGHT, 'erase_all', 'erase')
        m.add('erase_all', '#', '0', STAY, HALT, 'write 0 and halt')
    else:
        m.add('ripple', '1', 'O', LEFT, 'ripple', '1+1: write 0, carry on')
        m.add('ripple', '0' + BLANK, 'I', RIGHT, 'back_to_sep', 'write 1, carry done')
    m.add('back_to_sep', '01OI', None, RIGHT, 'back_to_sep', 'go to separator')
    m.add('back_to_sep', '#', BLANK, LEFT, 'unmark', 'erase separator')

    m.add('unmark', 'O', '0', LEFT, 'unmark', 'unmark 0')
    m.add('unmark', 'I', '1', LEFT, 'unmark', 'unmark 1')
    m.add('unmark', '01', None, LEFT, 'unmark', 'go to left end')
    m.add('unmark', BLANK, None, RIGHT, 'strip', 'reached left end')
    _strip_leading_zeros(m, 'strip')
    return m


def binary_add():
    """a # b -> a+b, ripple-carry from the lowest bit."""
    return _binary_add_or_subtract('binary add', subtract=False)


def binary_subtract():
    """a # b -> max(a-b, 0), ripple-borrow from the lowest bit."""
    return _binary_add_or_subtract('binary subtract', subtract=True)


def binary_multiply():
    """
    a # b -> a*b by shift-and-add.

    The tape is laid out as   P | F = a # b   where P|F is the product so far:
    F holds its low bits that are already final and P the rest.  For each bit
    of b, lowest first (erased as it is taken):
      - if it is 1, add a into P bit by bit (bits of a are marked x/y and
        bits of P marked O/I while the addition runs, then unmarked);
      - then move the lowest bit of P across '|' into F (a blank P bit is 0).
    Adding a into P instead of P|F is what multiplies it by 2^k for the k-th
    bit of b.  When b is used up, a and the markers are erased, P is shifted
    right over '|', and leading zeros are stripped.
    """
    m = Machine('binary multiply', start='init')
    m.add('init', '01#', None, LEFT, 'put_eq', 'start setup')
    m.add('put_eq', BLANK, '=', LEFT, 'put_bar', 'write = left of a')
    m.add('put_bar', BLANK, '|', RIGHT, 'seek_end', 'write | left of =; product starts empty')

    m.add('seek_end', '01#=|', None, RIGHT, 'seek_end', 'go to right end')
    m.add('seek_end', BLANK, None, LEFT, 'take_b', 'reached right end')
    m.add('take_b', '0', BLANK, LEFT, 'freeze_to_sep', 'b bit is 0: no addition')
    m.add('take_b', '1', BLANK, LEFT, 'add_to_sep_c0', 'b bit is 1: add a into P')
    m.add('take_b', '#', BLANK, LEFT, 'erase_a', 'b used up: clean up')

    # P += a, carry c in the state.
    for c in (0, 1):
        m.add(f'add_to_sep_c{c}', '01', None, LEFT, f'add_to_sep_c{c}', 'skip rest of b')
        m.add(f'add_to_sep_c{c}', '#', None, LEFT, f'take_a_c{c}', 'cross separator')
        m.add(f'take_a_c{c}', 'xy', None, LEFT, f'take_a_c{c}', 'skip added bits of a')
        for v in (0, 1):
            m.add(f'take_a_c{c}', str(v), 'xy'[v], LEFT, f'to_eq_c{c}_a{v}', f'take next bit of a ({v})')
            m.add(f'to_eq_c{c}_a{v}', '01xy', None, LEFT, f'to_eq_c{c}_a{v}', 'skip rest of a')
            m.add(f'to_eq_c{c}_a{v}', '=', None, LEFT, f'to_bar_c{c}_a{v}', 'cross =')
            m.add(f'to_bar_c{c}_a{v}', '01', None, LEFT, f'to_bar_c{c}_a{v}', 'skip final bits F')
            m.add(f'to_bar_c{c}_a{v}', '|', None, LEFT, f'to_p_c{c}_a{v}', 'cross |')
            m.add(f'to_p_c{c}_a{v}', 'OI', None, LEFT, f'to_p_c{c}_a{v}', 'skip added bits of P')
            for p_sym, p in (('0', 0), ('1', 1), (BLANK, 0)):
                total = p + v + c
                m.add(f'to_p_c{c}_a{v}', p_sym, 'OI'[total % 2], RIGHT, f'back_to_sep_c{total // 2}',
                      f'{p}+{v}+{c}: write {total % 2}, carry {total // 2}')
        m.add(f'back_to_sep_c{c}', '01OI|=xy', None, RIGHT, f'back_to_sep_c{c}', 'return to b')
        m.add(f'back_to_sep_c{c}', '#', None, LEFT, f'take_a_c{c}', 'at separator')
    m.add('take_a_c0', '=', None, LEFT, 'unmark_go_left', 'a used up: addition done')
    m.add('take_a_c1', '=', None, LEFT, 'carry_to_bar', 'a used up: carry into P')
    m.add('carry_to_bar', '01', None, LEFT, 'carry_to_bar', 'skip final bits F')
    m.add('carry_to_bar', '|', None, LEFT, 'carry', 'cross |')
    m.add('carry', 'OI', None, LEFT, 'carry', 'skip added bits of P')
    m.add('carry', '1', 'O', LEFT, 'carry', '1+1: write 0, carry on')
    m.add('carry', '0' + BLANK, 'I', LEFT, 'unmark_go_left', 'write 1, carry done')

    m.add('unmark_go_left', '01OI|=xy', None, LEFT, 'unmark_go_left', 'go to left end')
    m.add('unmark_go_left', BLANK, None, RIGHT, 'unmark', 'reached left end')
    m.add('unmark', 'Ox', '0', RIGHT, 'unmark', 'unmark 0')
    m.add('unmark', 'Iy', '1', RIGHT, 'unmark', 'unmark 1')
    m.add('unmark', '01|=', None, RIGHT, 'unmark', 'skip')
    m.add('unmark', '#', None, LEFT, 'freeze_to_eq', 'unmarked; now move a bit of P into F')

    # Move the lowest bit of P across '|' into F.
    m.add('freeze_to_sep', '01', None, LEFT, 'freeze_to_sep', 'skip rest of b')
    m.add('freeze_to_sep', '#', None, LEFT, 'freeze_to_eq', 'cross separator')
    m.add('freeze_to_eq', '01', None, LEFT, 'freeze_to_eq', 'skip a')
    m.add('freeze_to_eq', '=', None, LEFT, 'freeze_to_bar', 'cross =')
    m.add('freeze_to_bar', '01', None, LEFT, 'freeze_to_bar', 'skip final bits F')
    m.add('freeze_to_bar', '|', None, LEFT, 'freeze_take', 'at |')
    for p_sym, p in (('0', 0), ('1', 1), (BLANK, 0)):
        m.add('freeze_take', p_sym, '|', RIGHT, f'freeze_put{p}', f'lowest bit of P is {p}: move | left')
    for p in (0, 1):
        m.add(f'freeze_put{p}', '|', str(p), RIGHT, 'seek_end', f'{p} becomes a final bit')

    # Clean up: erase a and '=', shift P right over '|', strip leading zeros.
    m.add('erase_a', '01', BLANK, LEFT, 'erase_a', 'erase a')
    m.add('erase_a', '=', BLANK, LEFT, 'to_bar', 'erase =')
    m.add('to_bar', '01', None, LEFT, 'to_bar', 'skip final bits F')
    m.add('to_bar', '|', None, LEFT, 'to_p_start', 'close the gap at |')
    m.add('to_p_start', '01', None, LEFT, 'to_p_start', 'go to start of P')
    m.add('to_p_start', BLANK, None, RIGHT, 'shift_held_', 'shift P right by one')
    for held in ('_', '0', '1'):
        for p in ('0', '1'):
            m.add(f'shift_held{held}', p, held, RIGHT, f'shift_held{p}', 'shift')
        m.add(f'shift_held{held}', '|', held, LEFT, 'to_start', 'gap closed')
    m.add('to_start', '01', None, LEFT, 'to_start', 'go to start of result')
    m.add('to_start', BLANK, None, RIGHT, 'strip', 'reached start of result')
    _strip_leading_zeros(m, 'strip')
    return m


_BUILDERS = {
    ('unary', 'add'): unary_add,
    ('unary', 'subtract'): unary_subtract,
    ('unary', 'multiply'): unary_multiply,
    ('binary', 'add'): binary_add,
    ('binary', 'subtract'): binary_subtract,
    ('binary', 'multiply'): binary_multiply,
}


def get_machine(op, numeral, sep=None):
    """Machine for op in ('add', 'subtract', 'multiply') and numeral in ('unary', 'binary').
    `sep` overrides the unary separator symbol."""
    try:
        build = _BUILDERS[(numeral, op.lower())]
    except KeyError:
        raise ValueError(f'Unsupported op/numeral combo: {op}/{numeral}')
    if numeral == 'unary' and sep is not None:
        return build(sep)
    return build()


def initial_tape(a, b, numeral, sep=None):
    """Input string for operands a, b (non-negative ints)."""
    if a < 0 or b < 0:
        raise ValueError('Only non-negative integers allowed.')
    if numeral == 'unary':
        return '1' * a + (sep or UNARY_SEP) + '1' * b
    if numeral == 'binary':
        to_bin = lambda n: bin(n)[2:] if n > 0 else ''
        return to_bin(a) + BINARY_SEP + to_bin(b)
    raise ValueError('Unknown numeral system')


def read_result(content, numeral):
    """Integer value of a halted tape's content."""
    digits = content.replace(BLANK, '')
    if numeral == 'unary':
        if set(digits) - {'1'}:
            raise ValueError(f'not a unary result: {content!r}')
        return len(digits)
    if set(digits) - {'0', '1'}:
        raise ValueError(f'not a binary result: {content!r}')
    return int(digits, 2) if digits else 0
