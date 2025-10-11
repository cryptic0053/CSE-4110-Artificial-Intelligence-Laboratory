import time
import copy

# Sample Sudoku puzzle (0 = empty)
puzzle = [
    [8,0,0,0,0,0,0,0,0],
    [0,0,3,6,0,0,0,0,0],
    [0,7,0,0,9,0,2,0,0],
    [0,5,0,0,0,7,0,0,0],
    [0,0,0,0,4,5,7,0,0],
    [0,0,0,1,0,0,0,3,0],
    [0,0,1,0,0,0,0,6,8],
    [0,0,8,5,0,0,0,1,0],
    [0,9,0,0,0,0,4,0,0]
]

# --- Student Task 1: Implement this ---
def is_safe(board, row, col, num):
    """Check if 'num' can be placed at board[row][col]"""
    # TODO: implement row, column, and 3x3 subgrid checks
    return True  # placeholder

# --- Student Task 2: Naive backtracking solver ---
naive_calls = 0
def solve_naive(board):
    global naive_calls
    naive_calls += 1
    # TODO: implement naive backtracking
    return True  # placeholder

# --- Student Task 3: MRV heuristic solver ---
mrv_calls = 0
def solve_mrv(board):
    global mrv_calls
    mrv_calls += 1
    # TODO: implement MRV heuristic
    return True  # placeholder

# --- Student Task 4: MRV + LCV solver ---
mrv_lcv_calls = 0
def count_constraints(board, row, col, num):
    """Count how many choices neighbors lose if 'num' is placed here"""
    # TODO: implement LCV counting
    return 0  # placeholder

def solve_mrv_lcv(board):
    global mrv_lcv_calls
    mrv_lcv_calls += 1
    # TODO: implement MRV + LCV
    return True  # placeholder

# --- Utility: find empty cell ---
def find_empty(board):
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                return i, j
    return None

# --- Runner ---
def run_solver(solver, name):
    board_copy = copy.deepcopy(puzzle)
    start = time.time()
    solver(board_copy)
    end = time.time()
    print(f"{name}: Time = {end-start:.6f}s, Recursive calls = {globals()[name+'_calls']}")
    for row in board_copy:
        print(row)
    print("\n"+"-"*40+"\n")

# --- Execute ---
run_solver(solve_naive, "naive")
run_solver(solve_mrv, "mrv")
run_solver(solve_mrv_lcv, "mrv_lcv")
