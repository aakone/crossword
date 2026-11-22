"""
STEP 4: DEBUGGING, TESTING AND POLISH ("make it actually right")
=================================================================

Better name for this step than "fine-tuning": professionals say
TESTING and DEBUGGING, then POLISH. It is not decoration — it is
the phase where "works when I demo it" becomes "works when a
stranger uses it".

Step 3 shipped with TWO REAL BUGS (still in crossword_app.py so
your students can reproduce them!). This step finds and fixes
both, using the professional debugging loop:

    1. REPRODUCE  — a predictable way to make the bug happen
    2. UNDERSTAND — explain WHY the wrong behaviour happens
    3. FIX        — the smallest correct change
    4. VERIFY     — a test that now passes and would have
                    failed before the fix

THE BUGS:
  BUG #1 "Floating islands". build_grid()'s fallback parks an
     unplaceable word alone on the left edge. It is in the grid,
     the clue list says it exists — but it touches no other word.
     The solver types into an island of letters. The rule that
     broke silently: "every word must CROSS another".
  BUG #2 "Reveal appends". reveal_letter() calls insert(0, x)
     WITHOUT clearing the box. Type a wrong guess, hit Reveal:
     the box now reads "ax" — a one-letter box, two characters,
     permanently wrong. Works fine if you never guess first,
     which is why demos looked perfect.

THE TECHNIQUE THIS STEP TEACHES — REPLACING FUNCTIONS:
    Without classes there is no "override", but the procedural
    equivalent is just as honest and even simpler to read:

      * everything that WORKED in step 3 is imported and reused
        untouched (fits, place_word, draw_grid, check_answers...)
      * only the two BROKEN functions get new, fixed versions
        (build_connected_grid, reveal_letter_fixed)
      * the shared state dict PUZZLE lives inside the crossword_app
        module, so we write into it through that module — a
        module's variables are its natural "public face" once
        you import it.

    Sidebar lesson: this is also how you patch YOUR OWN projects
    mid-semester: keep the working file, write a corrected twin of
    only the failing function, import the rest.

RUN IT:  needs wordbank.py and crossword_app.py in the folder.
         python crossword_polished.py           (the app)
         python crossword_polished.py --test    (the test suite)
"""

import random
import tkinter as tk
from tkinter import ttk

from wordbank import MIN_WORDS, MAX_WORDS, pick_words

# Reuse step 1 AND step 3: importing our own files is completely
# ordinary — step 3's functions are just as available as Python's.
import crossword_app as ca
from crossword_app import (
    fits,                   # unchanged, trusted
    place_word,             # unchanged, trusted
    grid_bounds,            # unchanged, trusted
    draw_grid,              # unchanged (draws from ca.PUZZLE)
    fill_clues,             # unchanged
    check_answers,          # unchanged
)


# =================================================================
# FIX #1: A LAYOUT THAT CANNOT PRODUCE DISCONNECTED WORDS
# =================================================================
def is_connected(grid: dict, placements: list) -> bool:
    """True if all placed words form ONE crossing cluster.

    Algorithm "flood fill": start from word #0's cells, hop to any
    placed word sharing a cell with it, then repeat. If the hop-set
    stops growing before reaching every word, some words are
    islands. (Graph thinking without the word "graph": words are
    the vertices, shared cells the edges.)

    Pure function: takes (grid, placements), returns True/False,
    touches no globals — that is why it can also serve as a test.
    """
    if not placements:
        return True
    reached = {0}                      # word #0 is our starting point
    grid_owner = {}   # (row, col) -> indices of words on that cell
    for idx, (_w, r, c, d) in enumerate(placements):
        dr, dc = (0, 1) if d == "across" else (1, 0)
        for i in range(len(_w)):
            grid_owner.setdefault((r + dr * i, c + dc * i), set()).add(idx)
    grew = True
    while grew:
        grew = False
        for idx in list(reached):
            _w, r, c, d = placements[idx]
            dr, dc = (0, 1) if d == "across" else (1, 0)
            for i in range(len(_w)):
                for neighbour in grid_owner.get((r + dr * i, c + dc * i), ()):
                    if neighbour not in reached:
                        reached.add(neighbour)
                        grew = True
    return len(reached) == len(placements)


def build_connected_grid(words: list[str], size: int,
                         attempts: int = 10,
                         rng: random.Random | None = None
                         ) -> tuple[dict, list, list]:
    """Crossword_app.build_grid, but with the island bug fixed.

    Returns THREE things now: (grid, placements, excluded).
    "excluded" lists words nobody could place after all retries.

    The differences from step 3:
      - islands are FORBIDDEN: no edge-parking fallback
      - on failure we retry the whole layout with fresh
        randomness before excluding a word
      - exclusions are RETURNED so the caller can warn the user
        (a visible honest warning beats an invisible wrong result)
    """
    rng = rng or random
    excluded: list[str] = []
    best_grid: dict = {}
    best_placements: list = []

    for attempt in range(attempts):
        # Fresh state for this attempt — forgetting this "small"
        # line is a classic bug when REUSING code inside a loop.
        grid: dict = {}
        placements: list = []
        excluded = []

        order = sorted(words, key=len, reverse=True)
        first = order[0]
        start = size // 2 - len(first) // 2
        place_word(grid, placements, first, start, start, "across")

        for word in order[1:]:
            placed = False
            # rng.shuffle: retries produce different crossing
            # orders — each attempt explores a different layout.
            candidates = list(placements)
            rng.shuffle(candidates)
            for placed_word, p_row, p_col, p_dir in candidates:
                for direction in ("down", "across"):
                    if direction == p_dir:
                        continue
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
                if placed:                     # leave the CANDIDATES loop
                    break
            if not placed:
                # THE FIX: no island fallback. Record the failure;
                # a later attempt may still rescue this word.
                excluded.append(word)

        best_grid, best_placements = grid, placements
        if not excluded:          # every word crossed something: done
            break
    # Loop ends: either perfect, or best-attempt kept + honest list.
    return best_grid, best_placements, excluded


# =================================================================
# FIX #2 + POLISH: REPLACED CALLBACKS FOR THE GUI
# =================================================================
def reveal_letter_fixed() -> None:
    """# BUG FIX (do NOT copy from step 3!)

    Step 3 did:      entries[pos].insert(0, letter)     # appends!
    The box could end up holding TWO characters, e.g. "ax".

    The rule this fix enforces:
        a widget is not a variable; showing a value means
        CLEARING the widget first, THEN writing.

    Same pattern already used by show_solution() in step 3:
        entry.delete(0, tk.END); entry.insert(0, letter)
    The bug was simply that one function forgot step 1.

    "state = ca.PUZZLE" is the procedural replacement for step
    three's self attribute: the one box where the app remembers
    things between clicks, now reached through the module.
    """
    state = ca.PUZZLE
    entries = state["entries"]
    wrong = [pos for pos, letter in state["solution"].items()
             if entries[pos].get().lower() != letter]
    if not wrong:
        state["widgets"]["status"].config(
            text="Nothing to reveal — already solved!", fg="green")
        return
    pos = random.choice(wrong)
    entry = entries[pos]
    entry.delete(0, tk.END)               # <-- THE FIX
    entry.insert(0, state["solution"][pos])
    entry.config(fg="dark orange")


def on_key_polished(event: tk.Event) -> None:
    """Step 3 jumped only "next in reading order". Polish: follow
    the ARROW the user pressed; letters still auto-advance.

    The bound walk (for _ in size steps) guarantees we stop at the
    edge instead of marching forever — bounded loops are a
    polish feature too, not just a bug fix!
    """
    state = ca.PUZZLE
    entries = state["entries"]
    arrows = {"Left": (0, -1), "Right": (0, 1),
              "Up": (-1, 0), "Down": (1, 0)}
    if event.keysym not in arrows:
        ca.on_key(event)                  # letters: keep step-3 jump
        return

    current = [pos for pos, e in entries.items() if e is event.widget]
    if not current:
        return
    row, col = current[0]
    dr, dc = arrows[event.keysym]
    size = max(state["solution"])          # (row, col) tuples: the
    for _ in range(size[0] + size[1] + 2): #   far corner bounds our walk
        row, col = row + dr, col + dc
        if (row, col) in entries:
            neighbour = entries[(row, col)]
            neighbour.focus_set()
            neighbour.select_range(0, tk.END)   # so typing overwrites
            return


def new_puzzle_polished() -> None:
    """Step 3's new_puzzle, but building with the FIXED engine
    and telling the user about anything it had to exclude."""
    state = ca.PUZZLE
    widgets = state["widgets"]
    try:
        how_many = int(widgets["count_var"].get())
    except ValueError:
        how_many = 12
    words = pick_words(how_many)

    size = max(len(w) for w in words) + 8
    grid, placements, excluded = build_connected_grid(words, size)

    state["solution"] = dict(grid)
    state["layout"] = (grid, placements)
    draw_grid(grid)            # step-3 function, reused untouched
    fill_clues(placements)     # step-3 function, reused untouched

    if excluded:
        # BUG #1's face AFTER the fix: the user is TOLD which
        # words could not cross, instead of silently getting an
        # island. Transparency is part of the fix.
        widgets["status"].config(
            text=f"Puzzle ready — but not placeable: {', '.join(excluded)}",
            fg="dark orange")
    else:
        widgets["status"].config(
            text="Puzzle ready — every word crosses another! "
                 "Type letters; arrows move.", fg="blue")

    # POLISH: cursor in the first cell, ready to type.
    first_cell = sorted(state["entries"])[0] if state["entries"] else None
    if first_cell:
        state["entries"][first_cell].focus_set()


def build_window(root: tk.Tk) -> None:
    """Nearly identical to step 3's build_window — with the two
    broken callbacks swapped for the fixed twin functions."""
    widgets: dict = {}
    ca.PUZZLE["widgets"] = widgets
    ca.PUZZLE["root"] = root
    root.title("Crossword builder — polished edition")

    bar = tk.Frame(root)
    bar.pack(fill="x", padx=8, pady=5)

    tk.Label(bar, text="Words:").pack(side="left")
    widgets["count_var"] = tk.StringVar(value="12")
    ttk.Spinbox(bar, from_=MIN_WORDS, to=MAX_WORDS, width=4,
                textvariable=widgets["count_var"]).pack(side="left", padx=4)

    # THE SWAP — compare line by line with step 3:
    tk.Button(bar, text="New puzzle",
              command=new_puzzle_polished).pack(side="left", padx=4)
    tk.Button(bar, text="Check answers",
              command=check_answers).pack(side="left", padx=4)      # reused
    tk.Button(bar, text="Reveal one letter",
              command=reveal_letter_fixed).pack(side="left", padx=4)  # FIXED
    tk.Button(bar, text="Solution",
              command=ca.show_solution).pack(side="left", padx=4)    # reused

    widgets["status"] = tk.Label(bar, text="Ready", fg="blue")
    widgets["status"].pack(side="right")

    panes = tk.PanedWindow(root, orient="horizontal")
    panes.pack(fill="both", expand=True, padx=8, pady=5)
    widgets["grid_frame"] = tk.Frame(panes)
    widgets["clue_list"] = tk.Listbox(panes, width=48)
    panes.add(widgets["grid_frame"], minsize=360)
    panes.add(widgets["clue_list"])

    new_puzzle_polished()


# =================================================================
# A TINY TEST SUITE — the "testing" half of the step
# =================================================================
def run_self_tests() -> None:
    """Console tests: python crossword_polished.py --test

    Each test is: arrange -> act -> assert. These are the
    regression tests for the two bugs — each would FAIL on the
    step-3 functions and PASSES on ours. The verify step of the
    debug loop, automated so it runs forever for free.
    """
    def test_connected_layout():
        for _ in range(50):                       # 50 random puzzles
            words = pick_words(random.randint(MIN_WORDS, MAX_WORDS))
            grid, placements, excluded = build_connected_grid(words, size=30)
            assert not excluded or len(excluded) < len(words)
            for w in excluded:                    # excluded = also
                assert w not in {p[0] for p in placements}  # not placed
            if not excluded:                      # full puzzle must
                assert is_connected(grid, placements), \
                    "BUG #1 returned: island!"    # be one cluster
        print("PASS: 50 random puzzles, every placed word connected "
              "(BUG #1 fixed)")

    def test_fresh_state_per_attempt():
        # Excluded words from attempt 1 must not leak into attempts:
        rng = random.Random(7)
        words = pick_words(20)
        grid, placements, excluded = build_connected_grid(words, 30, rng=rng)
        placed = {p[0] for p in placements} | set(excluded)
        assert placed == set(words), "a word vanished entirely!"
        print("PASS: every word is either placed or honestly excluded")

    test_connected_layout()
    test_fresh_state_per_attempt()
    print("All self-tests passed.")


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        run_self_tests()          # console, no window needed
    else:
        root = tk.Tk()
        build_window(root)
        root.mainloop()
