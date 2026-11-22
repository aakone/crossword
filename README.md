# Crossword Builder — from idea to running software in 4 steps

A teaching project: a program that takes a list of English words and
generates a crossword puzzle in a tkinter window. It is deliberately
built in four stages, each one file, so students can follow the whole
path from a console script to a polished GUI application. Designed for
first-year university students who know functions, lists and dictionaries
but have **not** met classes yet — there is no OOP anywhere.

Each stage imports the previous one, which is the point: your own
`.py` files are modules, exactly like `random` or `tkinter`.

## The stages

| Stage | File | What it shows | Run it |
|-------|------|---------------|--------|
| 1. From idea to console software | `wordbank.py` | data (45-word bank) + pure functions + the 10–20 words rule + `__main__` convention | `python wordbank.py` |
| 2. Wiring tkinter to the console software | `gui_skeleton.py` | importing your own module, first window, widgets, callbacks as plain functions, one module-level state dict | `python gui_skeleton.py` |
| 3. Adding full features | `crossword_app.py` | pure-function layout engine that really crosses words, letter grid, clues, check / hint / solution buttons, keyboard events | `python crossword_app.py` |
| 4. Debugging, testing and polish | `crossword_polished.py` | fixing two real bugs left in stage 3 (disconnected "island" words; reveal button that appends instead of replacing), regression tests, arrow-key navigation | `python crossword_polished.py` |

## Setup

All files belong in the **same folder** (stages 2–4 do
`from wordbank import ...` and stage 4 imports stage 3). Requires
Python 3.10+ with the standard `tkinter` — no third-party packages.

## Self-tests

Stages 3 and 4 carry console test modes that need no window:

```
python crossword_app.py --test       # smoke test: every word placed, every letter consistent
python crossword_polished.py --test  # regression tests for the two stage-3 bugs
```
