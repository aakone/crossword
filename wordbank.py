"""
STEP 1: FROM IDEA TO CONSOLE SOFTWARE
=====================================

THE IDEA (in one sentence):
    "I want to type in English words and get a crossword puzzle."

Real programs grow inbaby steps. Step 1 is the smallest possible
version: NO graphical window, NO puzzle layout yet. Only:

    DATA  -> the words we play with
    LOGIC -> functions that manipulate the data
    CONSOLE input/output -> so we can see it works

WHY START WITHOUT A WINDOW?
    A console program is the easiest thing in the world to test
    and fix. If our idea is broken here, it would be ten times
    harder to debug inside a GUI. Professionals call this
    "prove the idea first, build the interface second".

HOW THIS FILE IS USED LATER:
    This same file stays in our project for every later step.
    It is our first lesson in modules: any .py file can be
    (a) a program you run, and
    (b) a library another file can `import`.
    Both behaviours live in this one file: see __main__ at bottom.

BEGINNER CONCEPTS USED HERE:
    - lists and constants      - for loops and enumerate()
    - f-strings                - functions, parameters, return values
    - exceptions (try/except)  - random.sample()
    - type hints like "list[str]" (documentation, not magic)
"""

import random  # a "standard library" module: ships with Python

# ---------------------------------------------------------------
# 1. DATA
# ---------------------------------------------------------------
# A CONSTANT is a variable we promise not to change, written in
# UPPER_CASE. Constants make rules visible: anyone reading this
# file instantly sees "the puzzle supports 10 to 20 words".
#
# WORD_BANK is our "master list": every vocabulary word we own.
# The puzzle of steps 2-4 will pick 10-20 words FROM this list.
# Keeping data in ONE place (instead of copy-pasting it around)
# is the single most important habit in programming.
WORD_BANK = [
    "apple", "tiger", "house", "water", "green",
    "happy", "chair", "bread", "clock", "smile",
    "river", "cloud", "stone", "ghost", "plant",
    "queen", "zebra", "money", "night", "light",
    "dance", "snake", "train", "beach", "horse",
    "bridge", "yellow", "winter", "garden", "window",
    "castle", "silver", "orange", "pencil", "monkey",
    "rocket", "candle", "dragon", "island", "forest",
    "piano", "ocean", "mountain", "elephant", "triangle",
    # 45 words: big enough that picking 20 still feels fresh,
    # and below most screens' need for the puzzle grid.
]

MIN_WORDS = 10   # smallest allowed puzzle
MAX_WORDS = 20   # biggest allowed puzzle


# ---------------------------------------------------------------
# 2. LOGIC (pure functions — easy to explain, easy to test)
# ---------------------------------------------------------------
def count_vowels(word: str) -> int:
    """Return how many vowels (a, e, i, o, u) the word has.

    The type hints (word: str) -> int are documentation for
    humans. Python ignores them, but your future self and your
    teammates do not: they say what goes in and what comes out.
    """
    # A "generator expression": for every letter, add 1 if it is
    # a vowel. sum() adds those 1s together. One readable line
    # replaces a 4-line loop — but the long loop would also be OK!
    return sum(1 for letter in word.lower() if letter in "aeiou")


def filter_valid_words(words: list[str]) -> list[str]:
    """Keep only words that are safe to draw in a puzzle.

    We demand: letters only (no spaces/hyphens), lowercase, and
    length 3-10. Long words make giant puzzle grids, and this is
    also a good example that functions can VALIDATE data instead
    of trusting it. Trusting input is where bugs are born.
    """
    # A "list comprehension": build a new list in one line.
    # Equivalent to a for-loop with words.append(w). Both fine.
    return [w for w in words
            if w.isalpha() and w.islower() and 3 <= len(w) <= 10]


def pick_words(count: int, rng: random.Random | None = None) -> list[str]:
    """Pick `count` DIFFERENT random words from WORD_BANK.

    The rule of our idea lives here: 10 <= count <= 20.
    Instead of crashing on a bad number, we "clamp" it into the
    allowed range and tell the user what we did.

    The mystery parameter `rng` makes TESTING possible: a test
    can pass its own pre-set random generator to make "random"
    repeatable. Real programs do exactly this; the default value
    None means normal users never need to think about it.
    """
    if count < MIN_WORDS:
        print(f"Too few words: raising {count} to the minimum {MIN_WORDS}.")
        count = MIN_WORDS
    if count > MAX_WORDS:
        print(f"Too many words: cutting {count} to the maximum {MAX_WORDS}.")
        count = MAX_WORDS
    rng = rng or random
    # random.sample() picks `count` items with no repeats —
    # exactly the "no duplicate words in one puzzle" rule.
    return rng.sample(WORD_BANK, count)


# ---------------------------------------------------------------
# 3. CONSOLE OUTPUT (temporary — replaced by the GUI in step 2)
# ---------------------------------------------------------------
def show_words_on_console(words: list[str]) -> None:
    """Print the chosen words neatly.

    The f-string format codes:
        {number:2d}  -> integer, padded to width 2 (" 3" not "3")
        {word:<10}   -> left-aligned in 10 characters
    Format codes turn ugly output into readable tables.
    """
    print()
    print("=== Your crossword words ===")
    for number, word in enumerate(words, start=1):
        # enumerate() numbers our loop 1, 2, 3, ... so we never
        # manage a counter variable by hand.
        vowels = count_vowels(word)
        print(f"{number:2d}. {word:<10} ({len(word)} letters, {vowels} vowels)")
    print()


# ---------------------------------------------------------------
# 4. RUN AS A PROGRAM
# ---------------------------------------------------------------
# Every Python file has a hidden variable __name__.
#   - Run it directly ("python wordbank.py")  -> __name__ is "__main__"
#   - Import it ("import wordbank")          -> __name__ is "wordbank"
# This if-block runs ONLY in the first case. That is how ONE file
# can be both a library and a program — and why imported files do
# NOT suddenly start asking for input.
if __name__ == "__main__":
    print("Welcome to the Crossword Word Bank (console edition)!")
    answer = input(f"How many words do you want ({MIN_WORDS}-{MAX_WORDS})? ")

    # input() ALWAYS gives a string. If the user types "twelve",
    # int() crashes. We catch the error and fall back to a default
    # instead of letting the whole program die. "Never trust user
    # input" is a lesson worth repeating for the rest of step 4.
    try:
        how_many = int(answer)
    except ValueError:
        print("That was not a number — using the default of 12.")
        how_many = 12

    selected = pick_words(how_many)     # <- logic from OUR OWN module
    show_words_on_console(selected)     # could also use built-in help:
                                        # help(pick_words) shows its docstring!
