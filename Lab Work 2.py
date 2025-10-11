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
    """
    Return list of all possible actions (row, col) on empty cells.
    TODO: Implement this function.
    """
    raise NotImplementedError

def result(state, action):
    """
    Return the new state after applying an action.
    TODO: Implement this function.
    """
    raise NotImplementedError

def terminal(state):
    """
    Check if game is over: win or draw.
    TODO: Implement this function.
    """
    raise NotImplementedError

def utility(state):
    """
    Return +1 if X wins, -1 if O wins, 0 otherwise.
    TODO: Implement this function.
    """
    raise NotImplementedError

def max_value(state):
    """
    Maximizer for X.
    TODO: Implement this function using recursion with min_value.
    """
    raise NotImplementedError

def min_value(state):
    """
    Minimizer for O.
    TODO: Implement this function using recursion with max_value.
    """
    raise NotImplementedError

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
