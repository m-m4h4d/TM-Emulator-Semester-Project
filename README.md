# TM-Emulator-Semester-Project

This proposal is for a **Turing Machine (TM) Emulator for Arithmetic Operations**, developed for the **Theory of Automata and Formal Languages (TAFL)** course by Muhammad Mahad and Abdul Moiz, under the instruction of Dr. Sohail Iqbal.

---

## Project Goal and Motivation

The project is motivated by the fact that the Turing Machine is the **foundation of modern computation**, and arithmetic operations illustrate how complex logic stems from simple transitions.

* **Goal**: To **visualize TM behavior**—including tape reading, head movement, and state transitions—specifically during arithmetic operations.
* **Problem Identified (Gap)**: Current TM simulators are often theoretical and lack an interactive demonstration of arithmetic computation; they usually only show string acceptance.
* **Solution**: To create a **modern emulator** that visually demonstrates TM-based arithmetic (addition, subtraction, multiplication) step-by-step.

---

## Methodology and Architecture

The project follows a standard development methodology: Problem Definition $\rightarrow$ Design $\rightarrow$ Implementation (in Python) $\rightarrow$ Visualization $\rightarrow$ Testing.

### System Architecture

The system is structured into four main components:

  1. **User Interface**: Where the user inputs an arithmetic expression.
  2. **Turing Machine Core**: Contains the Tape, Head, and Transition logic.
  3. **Arithmetic Logic**: Implements the specific TM rules for **Add, Sub, and Mul** (Multiplication).
  4. **Visualization Layer**: Dynamically displays the results and transitions.

### Execution Flow

The process involves an iterative loop:

  1. **Start / Input Arithmetic Expression**
  2. **Initialize Tape and Head**
  3. **Apply Transition Rules**
  4. **Write $\rightarrow$ Move $\rightarrow$ Change State**
  5. Check: **If Halt State Reached**, the process stops; otherwise, it **Repeats**.

---

## Running the Web Demo

Live at <https://tm-emulator-semester-project.vercel.app/>. Enter a unary expression such as `111+11`, `111-11` or `11*111`, press **Run Emulator**, then step backward and forward through the machine's moves.

### Locally

Requires Python 3.10+ and no third-party packages.

```bash
python dev_server.py        # then open http://127.0.0.1:8000/
```

`dev_server.py` serves `index.html` and sends `POST /api/tm_core` to the same handler Vercel runs. The page loads Tailwind and the Inter font from CDNs, so it needs an internet connection to look right. `vercel dev` also works if you have the Vercel CLI.

### API

`POST /api/tm_core` with `{"input": "111+11"}` runs the machine and returns every step:

```json
{
  "result": "11111",
  "steps_taken": 14,
  "history": [{"state": "q0", "tape_display": "____111+11____", "head_index": 4, "step": 0}, "..."]
}
```

The input is `1^a`, one operator (`+`, `-` or `*`), then `1^b`, at most 40 characters. Subtraction is monus (`11-111` gives 0). Invalid input, or a run longer than 10,000 steps, returns status 400 with `{"error": "..."}`.

### Project Structure

```
index.html            frontend: input, tape visualization, step controls
api/tm_core.py        Vercel serverless function (BaseHTTPRequestHandler named `handler`)
api/tm_machines.py    the Turing machines as transition tables, and the interpreter
dev_server.py         local server for development
tests/test_api.py     API tests
vercel.json           Vercel build and routing config
```

`api/tm_machines.py` is a verbatim copy of `tm/machines.py` from the desktop emulator ([m-m4h4d/turing_emulator](https://github.com/m-m4h4d/turing_emulator)), which also has binary arithmetic and a tkinter GUI. CI fails if the two files differ (the `engine-in-sync` job, which also runs daily), so change the engine in the desktop repo first, then copy it here unchanged.

### Running the Tests

```bash
python -m unittest discover -s tests -v
```

The tests and the engine sync check run on every push and pull request, and daily, through GitHub Actions (`.github/workflows/tests.yml`).
