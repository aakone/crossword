"""
STEP 3: ADDING FULL FEATURES — TURN THE SKELETON INTO A REAL CROSSWORD
=======================================================================

WHAT CHANGED SINCE STEP 2?
    Step 2 could pick words into a list. A real crossword still
    needs: a GRID where words CROSS each other, typing, clues,
    checking answers, hints. That is this step.

    It stays honest to the plan: all NEW thinking (how words
    cross) is written as PURE FUNCTIONS in PART A, with no
    tkinter anywhere near them. Pure functions take everything
    they need as PARAMETERS and tell the world everything via
    RETURN VALUES (no globals touched inside!). Two payoffs:

      1. you can test each one from a console exactly like
         step 1 — no window needed,
      2. the GUI in PART B just calls them and displays the
         result. Logic never asks the interface anything.

    (Spoiler for step 4: this step even contains two REAL bugs we
    planted by writing code the natural, quick way: words can end
    up disconnected from each other, and the "reveal letter"
    button appends instead of replacing. Step 4 fixes both —
    which is the most realistic software lesson of all: code that
    DEMOS beautifully can still be wrong.)

BEGINNER CONCEPTS USED HERE:
    - dictionaries as sparse grids: {(row, col): "A"}
    - "pure" functions: parameters in, return value out
    - tuples (row, col) as dictionary keys
    - nested loops & the early-break pattern
    - module-level state dict for the GUI (grown from step 2)
    - binding keyboard events to plain functions

RUN IT:  needs wordbank.py in the same folder.
         python crossword_app.py
"""

import random
import tkinter as tk
from tkinter import ttk

# Our step-1 module, still doing its job three steps later:
# the words, the 10-20 rule, the duplicate-free picking.
from wordbank import MIN_WORDS, MAX_WORDS, pick_words


# =================================================================
# PART A: THE PUZZLE LAYOUT ENGINE (pure logic — nothing tkinter)
# =================================================================
# SOFTWARE DESIGN PATTERN being taught here — "pass the data":
#     The grid is represented by ONE dictionary,
#         grid = {(row, col): letter}
#     and every function RECEIVES it and RETURNS it, or returns a
#     True/False answer ABOUT it. Nothing in Part A reads or
#     writes a global. Pure functions like these are the easiest
#     code in the world to test and debug, because you can call
#     them with values you invented yourself:
#         >>> make_clues([("GARDEN", 1, 2, "across")])[0]
#
# THE ALGORITHM (a classic beginner crossword builder):
#     1. sort words longest-first (long words are hardest to
#        place, so place them while the grid is empty)
#     2. place word #1 horizontally in the middle
#     3. for every next word: find a letter it SHARES with an
#        already-placed word and try to cross there (a down
#        word through an across word, or vice versa)
#     4. fallback: park it alone on the left edge
#        <- this fallback is exactly what step 4 improves:
#           alone means "not connected to the puzzle"!

def letter_at(grid: dict, row: int, col: int) -> str | None:
    """Return the letter at (row, col), or None if the cell is empty."""
    return grid.get((row, col))


def fits(grid: dict, size: int, word: str,
         row: int, col: int, direction: str) -> bool:
    """Would `word` be LEGAL at this spot? (a True/False question)

    Crossword legality rules:
      a) stay inside the size x size grid
      b) a cell may only be reused if it holds the SAME letter
         (that is what makes two words cross!)
      c) the cell right before the first letter, and right
         after the last one, must be EMPTY — otherwise our
         word would fuse into a neighbour and create nonsense
         like "BREADRIDGE" reading across two words.
    """
    dr, dc = (0, 1) if direction == "across" else (1, 0)
    if not (0 <= row < size and 0 <= col < size):
        return False
    end_row = row + dr * (len(word) - 1)
    end_col = col + dc * (len(word) - 1)
    if not (0 <= end_row < size and 0 <= end_col < size):
        return False
    for i, letter in enumerate(word):
        existing = letter_at(grid, row + dr * i, col + dc * i)
        if existing is not None and existing != letter:
            return False  # would overwrite a different letter
    before = letter_at(grid, row - dr, col - dc)
    after = letter_at(grid, row + dr * len(word), col + dc * len(word))
    if before is not None or after is not None:
        return False
    return True


def place_word(grid: dict, placements: list,
               word: str, row: int, col: int, direction: str) -> None:
    """Write all letters of `word` into the grid and log the placement.

    The one function allowed to MUTATE the grid — because callers
    checked fits() first. placements grows one entry:
        (word, row, col, direction)
    Direction is stored as the STEP of the walk: across moves
    (0, +1) per letter, down moves (+1, 0).
    """
    dr, dc = (0, 1) if direction == "across" else (1, 0)
    for i, letter in enumerate(word):
        grid[(row + dr * i, col + dc * i)] = letter
    placements.append((word, row, col, direction))


def build_grid(words: list[str], size: int) -> tuple[dict, list]:
    """Make a crossword: return (grid, placements).

    Returns TWO values — perfectly normal in Python:
        grid, placements = build_grid(my_words, 30)
    """
    grid: dict = {}
    placements: list = []
    words = sorted(words, key=len, reverse=True)

    first = words[0]
    start = size // 2 - len(first) // 2
    place_word(grid, placements, first, start, start, "across")

    for word in words[1:]:
        placed = False
        # random.sample shuffles the attempt order so two runs
        # with the same words can look different.
        for placed_word, p_row, p_col, p_dir in random.sample(
            placements, len(placements)
        ):
            # A new word crosses an across-word going DOWN,
            # and a down-word going ACROSS. same-direction
            # overlap would just sit on top of the other word.
            for direction in ("down", "across"):
                if direction == p_dir:
                    continue
                # Find every position i in `word` whose letter
                # also exists in placed_word, and try to put
                # that letter exactly onto the placed letter.
                for i, letter in enumerate(word):
                    if letter not in placed_word:
                        continue
                    j = placed_word.index(letter)
                    if p_dir == "across":
                        row, col = p_row - i, p_col + j
                    else:
                        row, col = p_row + j, p_col - i
                    if fits(grid, size, word, row, col, direction):
                        place_word(grid, placements,
                                   word, row, col, direction)
                        placed = True
                        break              # leave the LETTER loop
                if placed:                 # leave the DIRECTION loop
                    break
            if placed:                     # leave the PLACEMENTS loop
                break
        if not placed:
            # Fallback: park the word on the left edge.
            # STEP-4 BUG WARNING: such a word is in the grid
            # but NOT connected to the rest of the puzzle —
            # solvers see a floating island of letters.
            for row in range(size):
                if fits(grid, size, word, row, 0, "across"):
                    place_word(grid, placements, word, row, 0, "across")
                    break
    return grid, placements


def grid_bounds(grid: dict) -> tuple[int, int, int, int]:
    """(min_row, min_col, max_row, max_col) actually used."""
    rows = [r for r, _ in grid]
    cols = [c for _, c in grid]
    return min(rows), min(cols), max(rows), max(cols)


def make_clues(placements: list,
               fun_facts: dict | None = None) -> list[str]:
    """One clue line per word, numbered like a real puzzle.

    Real crossword numbering is fancier (by grid position),
    but for teaching, "1. Across ..." per placement is fine.
    The fun_facts dict lets you supply real definitions later:
        make_clues(placements, {"GARDEN": "plants grow here"})
    """
    lines = []
    for n, (word, row, col, direction) in enumerate(placements, 1):
        kind = "Across" if direction == "across" else "Down"
        hint = (fun_facts or {}).get(
            word, f"a {len(word)}-letter word meaning... {word}!")
        lines.append(f"{n}. {kind} ({len(word)} letters): {hint}")
    return lines


# Self-test hook (run:  python crossword_app.py --test) — running
# a module's OWN smoke test before the GUI is a habit worth having.
def _smoke_test() -> None:
    words = pick_words(12)
    grid, placements = build_grid(words, size=30)
    assert len({p[0] for p in placements}) == len(words)   # all placed
    for word, row, col, d in placements:                   # all letters written
        dr, dc = (0, 1) if d == "across" else (1, 0)
        for i, ch in enumerate(word):
            assert grid[(row + dr * i, col + dc * i)] == ch
    print("Smoke test OK:", len(words), "words placed:",
          [p[0] for p in placements])


# =================================================================
# PART B: THE FULL GUI (functions + ONE module-level state dict)
# =================================================================
# Same idea as step 2's UI_STATE, one level up: three facts must
# survive between callbacks.
#   entries   (row, col) -> the Entry widget in that cell
#   solution  (row, col) -> the correct hidden letter
#   layout    the last (grid, placements) pair, for redraws
# Keeping "parallel" dictionaries lets checking answers be one
# small loop, instead of re-deriving geometry each time.
PUZZLE = {"entries": {}, "solution": {}, "layout": None, "root": None}


def new_puzzle() -> None:
    """Callback of the "New puzzle" button: build everything fresh."""
    widgets = PUZZLE["widgets"]
    try:
        how_many = int(widgets["count_var"].get())
    except ValueError:
        how_many = 12
    words = pick_words(how_many)              # step-1 logic, reused!

    size = max(len(w) for w in words) + 8
    grid, placements = build_grid(words, size)          # Part A does the work

    PUZZLE["solution"] = dict(grid)          # remember the answer...
    PUZZLE["layout"] = (grid, placements)
    draw_grid(grid)                           # ...but show blanks
    fill_clues(placements)
    widgets["status"].config(text="New puzzle ready — start typing!", fg="blue")


def draw_grid(grid: dict) -> None:
    """Create one small Entry per filled cell.

    Subtlety: layout coordinates can be anywhere in the size x
    size area (even far from 0,0 after crossings). grid_bounds()
    gives the really-used rectangle, and (row - min_r) slides the
    whole puzzle snugly to the top-left corner of the window.
    """
    entries = PUZZLE["entries"]
    for entry in entries.values():
        entry.destroy()          # forget the OLD puzzle before
    entries.clear()               # drawing the new one, or both
                                  # would overlap in the frame
    grid_frame = PUZZLE["widgets"]["grid_frame"]
    min_r, min_c, max_r, max_c = grid_bounds(grid)
    grid_frame.pack_propagate(False)

    for (row, col), letter in sorted(grid.items()):
        r, c = row - min_r, col - min_c
        e = tk.Entry(
            grid_frame, width=1, justify="center",
            font=("Arial", 14, "bold"),
            relief="solid", bd=1,
            exportselection=False,  # let tkinter keep focus
        )                           # per-box — otherwise typing
        e.grid(row=r, column=c, ipadx=2, ipady=2)
        e.bind("<KeyRelease>", on_key)
        entries[(row, col)] = e


def fill_clues(placements: list) -> None:
    clue_list = PUZZLE["widgets"]["clue_list"]
    clue_list.delete(0, tk.END)     # same "clear first!" rule
    for line in make_clues(placements):
        clue_list.insert(tk.END, line)


# ---- event handlers ("full features") -----------------------------
def on_key(event: tk.Event) -> None:
    """After typing a letter, jump to the next cell.

    Simple version: walk cells in reading order (top row,
    then second row...). Not how the NYT does it (they follow
    the WORD you are solving across/down), but it shows event
    binding with almost no code.
    """
    if not event.char.isalpha():
        return
    # find which grid position the event happened in, then hop
    # to the next entry in (row, col) order — sorted() gives us
    # reading order for free because tuples compare nicely.
    entries = PUZZLE["entries"]
    order = sorted(entries)
    current = [k for k in entries if entries[k] is event.widget]
    if current:
        idx = order.index(current[0])
        if idx + 1 < len(order):
            entries[order[idx + 1]].focus_set()


def check_answers() -> None:
    """Count cells whose typed letter equals the solution."""
    entries = PUZZLE["entries"]
    correct = sum(
        1 for pos, letter in PUZZLE["solution"].items()
        if entries[pos].get().lower() == letter
    )
    total = len(PUZZLE["solution"])
    status = PUZZLE["widgets"]["status"]
    if correct == total:
        status.config(text="All letters correct — well done!", fg="green")
    else:
        status.config(text=f"{correct}/{total} letters correct", fg="blue")


def reveal_letter() -> None:
    """Help button: fill in one still-wrong cell.

    STEP-4 BUG WARNING: insert(0, ...) PUTS the letter in
    front of whatever is already there. If the user typed a
    wrong guess "x", the box ends up holding "?x" — two
    characters in a one-letter box, and the check button
    then grades a wrong answer! Step 4 fixes it; here it is
    a live demonstration that "works in my demo" != "correct".
    """
    entries = PUZZLE["entries"]
    wrong = [pos for pos, letter in PUZZLE["solution"].items()
             if entries[pos].get().lower() != letter]
    if wrong:
        pos = random.choice(wrong)
        entries[pos].insert(0, PUZZLE["solution"][pos])
        entries[pos].config(fg="dark orange")


def show_solution() -> None:
    """Fill every cell with its letter (this one clears first)."""
    for pos, letter in PUZZLE["solution"].items():
        entry = PUZZLE["entries"][pos]
        entry.delete(0, tk.END)      # <- the clear-first pattern
        entry.insert(0, letter)     #    reveal_letter forgets!
        entry.config(fg="red")
    PUZZLE["widgets"]["status"].config(
        text="Solution revealed — try a new puzzle!", fg="red")


# ---- building the window -------------------------------------------
def build_window(root: tk.Tk) -> None:
    """Create every widget; store the ones callbacks need later."""
    widgets: dict = {}
    PUZZLE["widgets"] = widgets
    PUZZLE["root"] = root
    root.title("Crossword builder — full edition")

    # --- toolbar row -----------------------------------------------
    bar = tk.Frame(root)
    bar.pack(fill="x", padx=8, pady=5)

    tk.Label(bar, text="Words:").pack(side="left")
    widgets["count_var"] = tk.StringVar(value="12")
    # ttk.Spinbox: an Entry WITH up/down arrows AND built-in
    # bounds — tkinter enforcing our 10-20 rule for us.
    spin = ttk.Spinbox(bar, from_=MIN_WORDS, to=MAX_WORDS, width=4,
                       textvariable=widgets["count_var"])
    spin.pack(side="left", padx=4)

    tk.Button(bar, text="New puzzle", command=new_puzzle).pack(side="left", padx=4)
    tk.Button(bar, text="Check answers", command=check_answers).pack(side="left", padx=4)
    tk.Button(bar, text="Reveal one letter", command=reveal_letter).pack(side="left", padx=4)
    tk.Button(bar, text="Solution", command=show_solution).pack(side="left", padx=4)

    widgets["status"] = tk.Label(bar, text="Ready", fg="blue")
    widgets["status"].pack(side="right")

    # --- puzzle area + clue list with a draggable divider -----------
    # PanedWindow = a divider the USER can drag: polite interfaces
    # let people widen the clues themselves for bigger fonts.
    panes = tk.PanedWindow(root, orient="horizontal")
    panes.pack(fill="both", expand=True, padx=8, pady=5)
    widgets["grid_frame"] = tk.Frame(panes)
    widgets["clue_list"] = tk.Listbox(panes, width=48)
    panes.add(widgets["grid_frame"], minsize=360)
    panes.add(widgets["clue_list"])

    # And fill it immediately, like build_window did in step 2.
    new_puzzle()


def main() -> None:
    root = tk.Tk()               # 1. create the main window
    build_window(root)           # 2. fill it
    root.mainloop()               # 3. hand control to the user


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        _smoke_test()             # console: python crossword_app.py --test
    else:
        main()
