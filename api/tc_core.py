# This file serves as a Vercel Python Serverless Function (API endpoint).
# It contains the complete Turing Machine logic and all transition rules.

from collections import defaultdict
import json

# --- TRANSITION RULE SETS ---

# 1. Unary Addition Rules (1^m + 1^n -> 1^(m+n) - 1)
# Process: Scan to '+', change '+' to '1', scan to end, change last '1' to '_' (halt).
TM_ADD_RULES = {
    ('q0', '1'): ('q0', '1', 'R'),
    ('q0', '+'): ('q1', '1', 'R'), # Change '+' to '1', start scanning second number
    ('q1', '1'): ('q1', '1', 'R'),
    ('q1', '_'): ('q2', '_', 'L'), # Found end, move left
    ('q2', '1'): ('q_halt', '_', 'N'), # Erase the last '1' (which was the separator) and Halt
    ('q_halt', '1'): ('q_halt', '1', 'N'),
    ('q_halt', '_'): ('q_halt', '_', 'N'),
}

# 2. Unary Subtraction Rules (1^m - 1^n -> 1^(m-n))
# Process: Pair-match '1's in m with '1's in n using 'X' markers.
TM_SUB_RULES = {
    # q0: Find 1st '1' of m, mark 'X', look for '-'
    ('q0', '1'): ('q1', 'X', 'R'),
    ('q0', '-'): ('q_cleanup_n', '_', 'R'), # Case m=0 (or m is exhausted first)
    ('q0', '_'): ('q_halt', '_', 'N'),

    # q1: Scan over m and '-'
    ('q1', '1'): ('q1', '1', 'R'),
    ('q1', '-'): ('q2', '-', 'R'),

    # q2: Match '1' in n. Skip marked 'X's.
    ('q2', 'X'): ('q2', 'X', 'R'),
    ('q2', '1'): ('q3', 'X', 'L'), # Found 1st '1' of n, mark 'X', rewind to m
    ('q2', '_'): ('q4_cleanup_m', '_', 'L'), # n is exhausted (m > n). Clean up m.

    # q3: Rewind to m's last matched 'X'
    ('q3', '1'): ('q3', '1', 'L'),
    ('q3', '-'): ('q3', '-', 'L'),
    ('q3', 'X'): ('q0', 'X', 'R'), # Found m's 'X', start next loop (q0)

    # q4_cleanup_m: n is exhausted (m > n). Rewind and convert m's 'X's back to '1's.
    ('q4_cleanup_m', '-'): ('q4_cleanup_m', '_', 'L'), # Erase '-'
    ('q4_cleanup_m', 'X'): ('q4_cleanup_m', '1', 'L'), # Convert 'X' back to '1'
    ('q4_cleanup_m', '1'): ('q4_cleanup_m', '1', 'L'), # Skip remaining m '1's
    ('q4_cleanup_m', '_'): ('q5_cleanup_n', '_', 'R'), # Found left end, move right to clean n

    # q5_cleanup_n: Erase n's 'X's and stop at first result '1'.
    ('q5_cleanup_n', 'X'): ('q5_cleanup_n', '_', 'R'),
    ('q5_cleanup_n', '_'): ('q_halt', '_', 'R'), # End of n's area. Halt.
    ('q5_cleanup_n', '1'): ('q_halt', '1', 'N'), # Found the result 1's. Halt.
    
    # q_cleanup_n: Case m=0, erase n and '-'
    ('q_cleanup_n', '1'): ('q_cleanup_n', '_', 'R'),
    ('q_cleanup_n', '-'): ('q_cleanup_n', '_', 'R'),
    ('q_cleanup_n', '_'): ('q_halt', '_', 'N'),
}

# 3. Unary Multiplication Rules (1^m * 1^n -> 1^(m*n))
# Process: For every '1' in n (marked 'A'), copy all '1's of m (marked 'X' then 'Y') to the result area.
TM_MUL_RULES = {
    # q0: Mark 1st '1' of m with 'X'. Go to q1.
    ('q0', '1'): ('q1', 'X', 'R'),
    ('q0', '*'): ('q_zero_out', '_', 'R'), # m=0 or n=0 handled by zero_out
    ('q0', '_'): ('q_zero_out', '_', 'R'),

    # q1: Find '*' and move to n.
    ('q1', '1'): ('q1', '1', 'R'),
    ('q1', '*'): ('q2', '*', 'R'),

    # q2: Mark 1st unmarked '1' of n with 'A'. Go to q3 (rewind to m's X).
    ('q2', 'A'): ('q2', 'A', 'R'),
    ('q2', '1'): ('q3', 'A', 'L'), # Found 1st '1' of n, mark 'A', rewind
    ('q2', '_'): ('q_cleanup_mul', '_', 'L'), # n exhausted. Cleanup phase.

    # q3: Rewind to m's 'X'.
    ('q3', '1'): ('q3', '1', 'L'),
    ('q3', '*'): ('q3', '*', 'L'),
    ('q3', 'A'): ('q3', 'A', 'L'),
    ('q3', 'X'): ('q4', 'X', 'R'), # Found m's 'X', start copying m's '1's

    # q4: Copy m: Find 1st unmarked '1' of m, mark 'Y'. Go to q_copy.
    ('q4', '1'): ('q_copy_1', 'Y', 'R'), # Found '1', mark 'Y', travel to result area
    ('q4', 'A'): ('q4', 'A', 'R'), # Should not happen, safety
    ('q4', '*'): ('q2', '*', 'R'), # All of m copied for this 'A' cycle. Repeat loop by finding next '1' in n (q2)

    # q_copy_1: Travel to end of tape (past n and current result).
    ('q_copy_1', '1'): ('q_copy_1', '1', 'R'),
    ('q_copy_1', 'A'): ('q_copy_1', 'A', 'R'),
    ('q_copy_1', '*'): ('q_copy_1', '*', 'R'),
    ('q_copy_1', 'Y'): ('q_copy_1', 'Y', 'R'), # Skip previously written '1's in result (marked 'Y' for now)
    ('q_copy_1', '_'): ('q_return_m', '1', 'L'), # Found end, write '1' to result, rewind

    # q_return_m: Rewind all the way back to 'Y' in m.
    ('q_return_m', '1'): ('q_return_m', '1', 'L'),
    ('q_return_m', 'A'): ('q_return_m', 'A', 'L'),
    ('q_return_m', '*'): ('q_return_m', '*', 'L'),
    ('q_return_m', 'Y'): ('q4', '1', 'R'), # Found 'Y', convert back to '1', repeat copying loop (q4)
    
    # q_cleanup_mul: Clean up all markers 'X', 'A', '*' from the tape. Result starts after m's 'X' or at the end.
    ('q_cleanup_mul', 'A'): ('q_cleanup_mul', '_', 'L'), # Erase A markers of n
    ('q_cleanup_mul', '*'): ('q_cleanup_mul_2', '_', 'L'), # Erase '*'
    
    ('q_cleanup_mul_2', '1'): ('q_cleanup_mul_2', '_', 'L'), # Erase m
    ('q_cleanup_mul_2', 'X'): ('q_cleanup_mul_2', '_', 'L'), # Erase X marker of m
    ('q_cleanup_mul_2', '_'): ('q_halt', '_', 'R'), # Found left end, Halt.
    
    # q_zero_out: Erase the entire tape and halt, used for 0 result cases.
    ('q_zero_out', '1'): ('q_zero_out', '_', 'R'),
    ('q_zero_out', '*'): ('q_zero_out', '_', 'R'),
    ('q_zero_out', '_'): ('q_halt', '_', 'N'),

    # --- Halt State (Final) ---
    ('q_halt', '1'): ('q_halt', '1', 'N'),
    ('q_halt', '_'): ('q_halt', '_', 'N'),
}


# --- TURING MACHINE CLASS ---

class TuringMachine:
    def __init__(self, tape_input, transition_rules, initial_state='q0', blank_symbol='_'):
        self.tape = defaultdict(lambda: blank_symbol)
        
        # Initialize tape with input string
        for i, char in enumerate(tape_input):
            self.tape[i] = char
            
        self.head_position = 0
        self.current_state = initial_state
        self.blank_symbol = blank_symbol
        self.rules = transition_rules
        self.is_running = True
        self.max_steps = 2000 # Safety limit
        self.steps_taken = 0
        self.history = []
        self._record_state() # Record initial state

    def _get_symbol(self):
        return self.tape[self.head_position]

    def _record_state(self):
        # Determine the bounds of the active tape content
        min_idx = min(self.tape.keys()) if self.tape else 0
        max_idx = max(self.tape.keys()) if self.tape else 0

        # Display window
        start_display = min(min_idx, self.head_position) - 5
        end_display = max(max_idx, self.head_position) + 5
        
        tape_list = [self.tape.get(i, self.blank_symbol) for i in range(start_display, end_display + 1)]
        relative_head_pos = self.head_position - start_display
        
        self.history.append({
            'state': self.current_state,
            'tape_display': ''.join(tape_list),
            'head_index': relative_head_pos,
            'step': self.steps_taken
        })

    def step(self):
        if not self.is_running or self.steps_taken >= self.max_steps:
            self.is_running = False
            return False

        current_symbol = self._get_symbol()
        
        if (self.current_state, current_symbol) not in self.rules:
            self.is_running = False
            return False 
        
        new_state, new_symbol, move = self.rules[(self.current_state, current_symbol)]
        
        self.tape[self.head_position] = new_symbol
        self.current_state = new_state
        
        if move == 'R':
            self.head_position += 1
        elif move == 'L':
            self.head_position -= 1

        self.steps_taken += 1
        self._record_state()
        return self.is_running

    def run(self):
        while self.is_running:
            if not self.step():
                break
        
        # Extract the final result (contiguous '1's from the leftmost '1')
        used_indices = sorted([i for i, c in self.tape.items() if c == '1'])
        if not used_indices:
            return "0"
            
        start_idx = min(used_indices)
        
        result = ""
        current_idx = start_idx
        while self.tape.get(current_idx, self.blank_symbol) == '1':
            result += '1'
            current_idx += 1
            
        return result if result else "0"

# --- VERCEL API HANDLER ---

def get_rules(operator):
    """Selects the correct transition rules based on the operator."""
    if operator == '+':
        return TM_ADD_RULES
    elif operator == '-':
        return TM_SUB_RULES
    elif operator == '*':
        return TM_MUL_RULES
    return None

def handler(event, context):
    """
    Main entry point for the Vercel Serverless Function.
    The event parameter contains the request data from the frontend.
    """
    try:
        # Check if the request body is present
        if not event.get('body'):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing request body'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        data = json.loads(event['body'])
        input_expression = data.get('input', '')
        
        # Parse the operator and validate input
        if '+' in input_expression:
            operator = '+'
        elif '-' in input_expression:
            operator = '-'
        elif '*' in input_expression:
            operator = '*'
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Input must contain one operator (+, -, or *)'}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        rules = get_rules(operator)
        if not rules:
             return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal Error: Operator rules not found.'}),
                'headers': {'Content-Type': 'application/json'}
            }

        # Initialize and run the TM
        tm = TuringMachine(input_expression, rules)
        final_result = tm.run()
        
        # Prepare the response
        response_data = {
            'history': tm.history,
            'result': final_result,
            'steps_taken': tm.steps_taken
        }

        return {
            'statusCode': 200,
            'body': json.dumps(response_data),
            'headers': {
                'Content-Type': 'application/json',
                # CORS headers for Vercel deployment (optional but safer)
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        }

    except Exception as e:
        # Generic error handling
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'An unexpected error occurred: {str(e)}'}),
            'headers': {'Content-Type': 'application/json'}
        }

# For Vercel, the function name must be 'handler'
def main(request):
    """Wrapper for local testing/deployment compatibility."""
    # Vercel's Python runtime uses a specific 'event/context' structure.
    # We simulate that structure here.
    event = {
        'body': request.get_data(as_text=True),
    }
    return handler(event, None)