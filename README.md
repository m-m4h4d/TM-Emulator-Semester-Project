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

**System Architecture**

The system is structured into four main components:
  1. **User Interface**: Where the user inputs an arithmetic expression.
  2. **Turing Machine Core**: Contains the Tape, Head, and Transition logic.
  3. **Arithmetic Logic**: Implements the specific TM rules for **Add, Sub, and Mul** (Multiplication).
  4. **Visualization Layer**: Dynamically displays the results and transitions.

**Execution Flow**

The process involves an iterative loop:
  1. **Start / Input Arithmetic Expression**
  2. **Initialize Tape and Head**
  3. **Apply Transition Rules**
  4. **Write $\rightarrow$ Move $\rightarrow$ Change State**
  5. Check: **If Halt State Reached**, the process stops; otherwise, it **Repeats**.

---
