"""
STEP 2: WIRING BASIC TKINTER FUNCTIONALITY INTO THE CONSOLE SOFTWARE
====================================================================

WHAT CHANGED SINCE STEP 1?
    Step 1 proved our logic works — on the console. Now we give
    the same idea a WINDOW. But here is the trick that makes this
    step easy instead of painful:

        WE CHANGE ZERO LINES OF STEP-1 LOGIC.

    wordbank.py keeps doing all the thinking. This file only
    replaces the CONVERSATION with the user:

        console (step 1)              GUI (this step)
        ----------------------------------------------
        input("how many?")     ->      an Entry box
        print()                ->      Label and Listbox widgets
        script runs once       ->      mainloop() reacts forever

    Keeping logic and interface in separate files is called
    "separation of concerns", and it is why step 3 can bolt an
    even fancier interface on without breaking anything.

KEY TKINTER IDEAS (the wiring being demonstrated):
    - tk.Tk()    : the root window, exactly one per program
    - widgets    : Label (text), Entry (typing), Button (click),
                   Listbox (scrollable list)
    - command=   : "when clicked, call THIS function" — the
                   function is called a CALLBACK because the
                   program calls you back when the user acts
    - .pack()    : cheap automatic layout ("stack from top")
    - mainloop() : the event loop; from here on, tkinter waits
                   for clicks and keys and runs our callbacks

THE ONE PROBLEM tkinter CREATES FOR US — AND THE FIX:
    A window must REMEMBER things between clicks: which words
    were picked, what the widgets are. Scripts have no memory
    between function calls, so we keep ONE carefully-named
    module-level dictionary, UI_STATE, that our callbacks read
    and write. (A hundred loose globals would do the same job
    far worse — one clearly-owned "state" box is the honest,
    readable middle ground until functions can carry it for us.)

BEGINNER CONCEPTS USED HERE:
    - importing YOUR OWN module (most exciting part: it is just
      a file in the same folder!)
    - module-level variables vs. LOCAL variables (very different!)
    - functions as values: passing on_pick_words WITHOUT ( )
    - dictionaries as a "record": UI_STATE["words"] = ...

RUN IT:   put wordbank.py and this file in the same folder,
          then:  python gui_skeleton.py
"""

import tkinter as tk  # GUI library included with Python — nothing to install

# -----------------------------------------------------------------
# IMPORTING OUR OWN MODULE
# -----------------------------------------------------------------
# This line is the heart of this step. We hand-pick names from
# wordbank.py — the file from step 1 — and use them like they
# were part of Python itself. Python finds wordbank.py because
# it sits in the SAME folder as this file.
#
# Why from-import instead of "import wordbank"? Just shorter
# code: pick_words(...) instead of wordbank.pick_words(...).
from wordbank import (
    WORD_BANK,
    MIN_WORDS,
    MAX_WORDS,
    pick_words,
    filter_valid_words,
)


# -----------------------------------------------------------------
# STATE: everything the window must remember between clicks
# -----------------------------------------------------------------
# "widgets" holds the tkinter widgets (addressed by name), and
# "words" holds the current selection. Compare with step 1: there,
# a LOCAL variable inside __main__ was enough, because the script
# ran top-to-bottom once and died. Event-driven programs live on
# and need somewhere to keep their facts.
UI_STATE = {
    "widgets": {},   # e.g. UI_STATE["widgets"]["status"] -> a Label
    "words": [],     # the currently picked words
}


# -----------------------------------------------------------------
# CALLBACKS (tkinter calls these — we never call them ourselves)
# -----------------------------------------------------------------
def on_pick_words() -> None:
    """Read the Entry, run STEP-1 logic, fill the Listbox.

    Notice the shape: read widgets -> CALL LOGIC -> write
    widgets. Callbacks should stay this thin. When a bug
    appears, that shape tells you instantly where to look:
    wrong numbers? logic module. wrong widgets? here.
    """
    widgets = UI_STATE["widgets"]
    try:
        how_many = int(widgets["count_entry"].get())
    except ValueError:
        how_many = 12   # exactly step 1's "not a number" fallback —
                        # same rule, different interface

    # THE ENTIRE "thinking" of this step is this one line.
    # All rules (min 10, max 20, no duplicates) live in
    # wordbank.py and were already tested in step 1.
    UI_STATE["words"] = pick_words(how_many)

    # tkinter lists count from 0. delete(0, tk.END) clears
    # the whole box — without this, every click would make
    # the list LONGER instead of replacing it (a bug you will
    # meet in step 4 in a sneakier costume!).
    word_listbox = UI_STATE["widgets"]["word_listbox"]
    word_listbox.delete(0, tk.END)
    for word in UI_STATE["words"]:
        word_listbox.insert(tk.END, word)

    UI_STATE["widgets"]["status"].config(
        text=f"Picked {len(UI_STATE['words'])} words. "
             "Puzzle grid comes in step 3!"
    )


# -----------------------------------------------------------------
# BUILDING THE WINDOW (runs once, before the user does anything)
# -----------------------------------------------------------------
def build_window(root: tk.Tk) -> None:
    """Create every widget and store them in UI_STATE.

    Why store the widgets? A callback later needs to reach them
    again (read the Entry, rewrite the status Label...). Widgets
    created inside a function are LOCAL and would be lost when
    the function returns — so we save the ones we need later.
    """
    widgets = UI_STATE["widgets"]

    # A Label is just text on the screen.
    widgets["title"] = tk.Label(
        root,
        text=f"Pick {MIN_WORDS}-{MAX_WORDS} words for your puzzle",
        font=("Arial", 14, "bold"),
    )
    widgets["title"].pack(pady=10)

    widgets["count_label"] = tk.Label(root, text="How many words?")
    widgets["count_label"].pack()

    # An Entry is a one-line typing box (the GUI's input()).
    widgets["count_entry"] = tk.Entry(root, justify="center", width=5)
    widgets["count_entry"].insert(0, "12")   # pre-fill a default,
    widgets["count_entry"].pack(pady=5)      #  like step 1's fallback

    # A Button needs two things: text and a CALLBACK.
    # Note we pass the FUNCTION itself (no parentheses!)
    # "call on_pick_words later" not "call it right now".
    widgets["pick_button"] = tk.Button(
        root, text="Pick words", command=on_pick_words
    )
    widgets["pick_button"].pack(pady=5)

    # A Listbox = a scrollable list of lines (the GUI's print()).
    widgets["word_listbox"] = tk.Listbox(root, width=30, height=MAX_WORDS)
    widgets["word_listbox"].pack(padx=10, pady=10)

    # A status Label: the polite way to tell the user things
    # succeeded or failed, instead of print() in a terminal
    # they may not even be looking at.
    widgets["status"] = tk.Label(root, text="Ready.")
    widgets["status"].pack(pady=5)
    widgets["status"].config(
        text=f"Word bank holds {len(filter_valid_words(WORD_BANK))} words."
    )


def main() -> None:
    """The classic three-liner that starts every tkinter program."""
    root = tk.Tk()                    # 1. create the main window
    build_window(root)                # 2. fill it with widgets
    root.mainloop()                    # 3. hand control to the user
                                      # No code after mainloop() runs
                                      # until the window is closed.


if __name__ == "__main__":
    main()
