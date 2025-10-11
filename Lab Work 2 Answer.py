import math

class State:
    def __init__(self, board=None, player='X'):
        if board is None:
            self.board = [[' ' for _ in range(3)] for _ in range(3)]
        else:
            self.board = [row[:] for row in board]
        self.player = player

    def display(self):
        print("\n".join([" | ".join(row) for row in self.board]))
        print("-" * 5)

def actions(state):
    return [(i, j) for i in range(3) for j in range(3) if state.board[i][j] == ' ']

def result(state, action):
    i, j = action
    new_state = State(state.board, 'O' if state.player == 'X' else 'X')
    new_state.board[i][j] = state.player
    return new_state

def terminal(state):
    b = state.board
    lines = b + [list(col) for col in zip(*b)] + [[b[i][i] for i in range(3)], [b[i][2-i] for i in range(3)]]
    if any(line == ['X'] * 3 or line == ['O'] * 3 for line in lines):
        return True
    if all(cell != ' ' for row in b for cell in row):
        return True
    return False

def utility(state):
    b = state.board
    lines = b + [list(col) for col in zip(*b)] + [[b[i][i] for i in range(3)], [b[i][2-i] for i in range(3)]]
    if ['X'] * 3 in lines:
        return 1
    if ['O'] * 3 in lines:
        return -1
    return 0

def max_value(state):
    if terminal(state):
        return utility(state), None
    value, best_action = -math.inf, None
    for action in actions(state):
        new_state = result(state, action)
        eval_value, _ = min_value(new_state)
        if eval_value > value:
            value, best_action = eval_value, action
    return value, best_action

def min_value(state):
    if terminal(state):
        return utility(state), None
    value, best_action = math.inf, None
    for action in actions(state):
        new_state = result(state, action)
        eval_value, _ = max_value(new_state)
        if eval_value < value:
            value, best_action = eval_value, action
    return value, best_action

def minimax(state):
    if state.player == 'X':   # Maximizer
        return max_value(state)
    else:                     # Minimizer
        return min_value(state)

def play():
    state = State()
    print("Welcome to Tic-Tac-Toe! You are O, AI is X.")
    state.display()

    while not terminal(state):
        if state.player == 'O':
            row, col = map(int, input("Enter row and col (0-2 space separated): ").split())
            if (row, col) not in actions(state):
                print("Invalid move! Try again.")
                continue
            state = result(state, (row, col))
        else:
            _, action = minimax(state)
            print(f"AI plays: {action}")
            state = result(state, action)

        state.display()

    score = utility(state)
    if score == 1:
        print("X wins!")
    elif score == -1:
        print("O wins!")
    else:
        print("It's a draw!")

if __name__ == "__main__":
    play()
