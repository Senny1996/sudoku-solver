"""Puzzles shared by the test modules. Each is 81 characters, 0 = blank."""

# The well-known example puzzle from Wikipedia's article on sudoku. Easy:
# propagation alone solves it.
EASY = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
EASY_SOLUTION = "534678912672195348198342567859761423426853791713924856961537284287419635345286179"

# Arto Inkala's 2012 puzzle, widely billed as the world's hardest sudoku.
# The solver has to guess and backtrack to finish it.
HARD = "800000000003600000070090200050007000000045700000100030001000068008500010090000400"
HARD_SOLUTION = "812753649943682175675491283154237896369845721287169534521974368438526917796318452"

# A sparse puzzle with an empty first row (unique solution).
FEW_CLUES = "000000000000003085001020000000507000004000100090000000500000073002010000000040009"

# EASY with the 6 at row 3, column 8 removed: exactly two solutions.
TWO_SOLUTIONS = "530070000600195000098000000800060003400803001700020006060000280000419005000080079"

# No repeated digit anywhere, yet no solution: row 1 needs a 9 in its last cell,
# but column 9 already has one. Propagation spots this straight away.
UNSOLVABLE_SIMPLE = "123456780000000009" + "0" * 63

# HARD with a 2 at row 1, column 2 (the true digit is 1). It looks fine, since
# no row, column or box repeats a digit, but the puzzle has no solution and the
# solver has to search before it can say so.
UNSOLVABLE_DEEP = "820000000003600000070090200050007000000045700000100030001000068008500010090000400"

# EASY with an extra 5 at row 1, column 3: two 5s in row 1.
DUPLICATE_IN_ROW = "535070000600195000098000060800060003400803001700020006060000280000419005000080079"
