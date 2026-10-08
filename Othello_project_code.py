# OTHELLO GAME with Tkinter graphical interface
# Made by: Auréva Tagand-Baud
import tkinter as tk
from tkinter import messagebox

## Step 1: Game logic
# The 8 possible directions on the board (dy, dx)
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

# Constants: cell states
EMPTY = 0
BLACK = 1
WHITE = 2

def create_board():
    """Return an 8x8 board set up for the start of an Othello game."""
    board = [[EMPTY] * 8 for _ in range(8)]
    # Starting position: 4 discs in the center
    board[3][3] = WHITE
    board[3][4] = BLACK
    board[4][3] = BLACK
    board[4][4] = WHITE
    return board

def is_in_board(row, col):
    """Check that a cell is within the board limits."""
    return 0 <= row < 8 and 0 <= col < 8


def opponent(player):
    """Return the opposing player's color."""
    if player == BLACK:
        return WHITE
    else:
        return BLACK


def flipped_discs(board, row, col, player):
    """Return the list of discs flipped if `player` plays at (row, col).
    If the move is invalid, return an empty list."""
    if board[row][col] != EMPTY:  # cell already occupied -> invalid move
        return []
    
    opp = opponent(player)
    to_flip = []
    
    # Look in all 8 directions around the played cell
    for dy, dx in DIRECTIONS:
        flipped_in_dir = []
        r, c = row + dy, col + dx
        # Move along the direction as long as we meet opponent discs
        while is_in_board(r, c) and board[r][c] == opp:
            flipped_in_dir.append((r,c))
            r += dy
            c += dx
        # The line is valid only if it ends on one of the player's own discs
        # and at least one opponent disc was crossed
        if is_in_board(r,c) and board[r][c] == player and flipped_in_dir:
            to_flip.extend(flipped_in_dir)
    return to_flip

def is_valid_move(board, row, col, player):
    """Return True if the move (row, col) is valid for the player."""
    # A valid move must flip at least one disc
    return len(flipped_discs(board,row,col,player)) > 0


def valid_moves(board, player):
    """Return the list of all valid moves (row, col) for the player."""
    moves = []
    for i in range(8):
        for j in range(8):
            if is_valid_move(board,i,j,player):
                moves.append((i,j))
    return moves


def play_move(board,row,col,player):
    """Play the move (row, col) for the player : modifies the board in place
    and returns it."""
    flipped = flipped_discs(board, row, col, player)
    if not flipped:
        return board  # invalid move, do nothing
    board[row][col] = player
    for (r,c) in flipped:
        board[r][c] = player
    return board


def copy_board(board):
    """Return a copy of the board. Needed to simulate moves during the AI
    search without altering the real game state."""
    new_board = [[0 for _ in range(8)] for _ in range(8)]
    for i in range(8):
        for j in range(8):
            new_board[i][j] = board[i][j]
    return new_board


def count_discs(board):
    """Count each player's discs."""
    black_count = 0
    white_count = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == BLACK:
                black_count += 1
            elif board[i][j] == WHITE:
                white_count += 1
    return black_count, white_count

def game_over(board):
    """Return True if the game is over (no valid move for either player)."""
    return not valid_moves(board, BLACK) and not valid_moves(board, WHITE)


def winner(board):
    """Return the winner (BLACK or WHITE), or EMPTY in case of a draw.
    Should only be called when game_over() is True."""
    black_count, white_count = count_discs(board)
    if black_count > white_count:
        return BLACK
    elif white_count > black_count:
        return WHITE
    else:
        return EMPTY


## Step 2: Computer strategy

def heuristic_easy(board, player):
    """Easy level: simply count discs.
    The computer tries to have the most discs (naive strategy)."""
    black_count, white_count = count_discs(board)
    if player == BLACK:
        return black_count - white_count
    else:
        return white_count - black_count


def heuristic_medium(board, player):
    """
    Medium level: score based on strategic positions.
    - 1 point per available valid move (mobility)
    - 3 points per occupied edge cell
    - 10 points per occupied corner
    Then difference between the player's and the opponent's scores.
    """
    opp = opponent(player)
    CORNERS = [(0, 0), (0, 7), (7, 0), (7, 7)]
    EDGES = []
    for i in range(8):
        for j in range(8):
            if i == 0 or i == 7 or j == 0 or j == 7:
                if (i,j) not in CORNERS:
                    EDGES.append((i,j))
    return medium_score(board,player,EDGES,CORNERS) - medium_score(board,opp,EDGES,CORNERS)


def medium_score(board, player, edges, corners):
    """Compute the player's score according to the Medium heuristic criteria."""
    pts = 0
    pts += len(valid_moves(board, player))
    for (r,c) in edges:
        if board[r][c] == player:
            pts += 3
    for (r,c) in corners:
        if board[r][c] == player:
            pts += 10
    return pts


# In the Hard heuristic, each cell has a positional value reflecting its strategic importance.
# Corners: 100, whereas squares adjacent to corners are easily lost (-20/-50),
# and squares next to them can help capture the corner (+10), etc.

def heuristic_hard(board, player):
    """
    Hard level: combines a positional score, mobility and corner control
    (and not only the disc count).
    """
    opp = opponent(player)
    POSITION_WEIGHTS = [[100, -20, 10,  5,  5, 10, -20, 100],
                        [-20, -50, -2, -2, -2, -2, -50, -20],
                        [ 10,  -2,  5,  1,  1,  5,  -2,  10],
                        [  5,  -2,  1,  1,  1,  1,  -2,   5],
                        [  5,  -2,  1,  1,  1,  1,  -2,   5],
                        [ 10,  -2,  5,  1,  1,  5,  -2,  10],
                        [-20, -50, -2, -2, -2, -2, -50, -20],
                        [100, -20, 10,  5,  5, 10, -20, 100]]

    # Positional score: edge and corner control is implied by the cell weights
    position_score = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == player:
                position_score += POSITION_WEIGHTS[i][j]
            elif board[i][j] == opp:
                position_score -= POSITION_WEIGHTS[i][j]

    # Mobility (available moves), computed separately
    mobility_player = len(valid_moves(board, player))
    mobility_opp = len(valid_moves(board, opp))
    mobility_score = mobility_player - mobility_opp

    # Corner control (added after testing: it improves play)
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    corner_score = 0
    for r,c in corners:
        if board[r][c] == player:# the computer controls the corner (+10)
            corner_score += 10
        elif board[r][c] == opp:# the opponent controls the corner (-10)
            corner_score -= 10
    #Weighted sum: the large weights create big gaps between state scores,
    #which proved effective in tests
    return 5 * position_score + 3 * mobility_score + 10 * corner_score



def alphabeta(board, depth, alpha, beta, computer, current_player, heuristic):
    """
    Minimax algorithm with alpha-beta pruning, adapted to Othello.
    Parameters:
      @board          : current game state (2D list)
      @depth          : remaining depth of moves to explore
      @alpha          : lower bound (best score guaranteed for MAX)
      @beta           : upper bound (best score guaranteed for MIN)
      @computer       : the computer's color (it tries to maximize its score)
      @current_player : the player whose turn it is at this node
      @heuristic      : evaluation function applied at the leaves

    Returns the heuristic score of the node, used by the computer to decide.
    """
    opp = opponent(current_player)
    moves = valid_moves(board, current_player)
    # Base case: depth 0 reached or game over
    if depth == 0 or game_over(board):
        return heuristic(board, computer)

    # If the current player cannot move, they pass and the other player continues
    if not moves:
        return alphabeta(board, depth - 1, alpha, beta, computer, opp, heuristic)

    if current_player == computer:#if MAX node
        value = -float('inf')
        for (row, col) in moves:
            new_board = copy_board(board)
            play_move(new_board, row, col, current_player)
            score = alphabeta(new_board, depth - 1, alpha, beta, computer, opp, heuristic)
            value = max(value, score)
            alpha = max(alpha, value)
            if alpha >= beta:  # pruning condition
                break          # alpha cutoff
        return value
    else:
        #if MIN node: the human's move(worst case for the computer)
        value = float('inf')
        for (row, col) in moves:
            new_board = copy_board(board)
            play_move(new_board, row, col, current_player)
            score = alphabeta(new_board, depth - 1, alpha, beta, computer, opp, heuristic)
            value = min(value, score)
            beta = min(value, beta)
            if alpha >= beta:
                break  #beta cutoff
        return value


# Difficulty levels
LEVELS = {
    "Easy":   {"depth": 2, "heuristic": heuristic_easy},
    "Medium": {"depth": 4, "heuristic": heuristic_medium},
    "Hard":   {"depth": 6, "heuristic": heuristic_hard},
    }

def choose_move(board, computer_player, level="Medium"):
    """
    Choose the best move for the computer according to the difficulty level.
    Parameters:
      @board           : current game state
      @computer_player : the computer's color (BLACK or WHITE)
      @level           : "Easy", "Medium" or "Hard"
    Returns (row, col) of the best move, or None if no move is possible.
    """
    moves = valid_moves(board, computer_player)
    if not moves:
        return None

    params = LEVELS[level]
    depth = params["depth"]
    heuristic = params["heuristic"]

    best_move = None
    best_score = float('-inf')#start from the worst possible score

    for (row,col) in moves:
        new_board = copy_board(board)             # simulate on a copy of the board
        play_move(new_board, row,col,computer_player)
        # The opponent plays next -> MIN node
        score = alphabeta(new_board, depth - 1, float('-inf'), float('inf'),
                          computer_player, opponent(computer_player), heuristic)
        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move


## Step 3: Graphical interface

# Interface constants
MARGIN = 30                      #margin around the board
CELL_SIZE = 70
BOARD_SIZE = 8 * CELL_SIZE       #560 pixels
BOARD_COLOR = "#2d6a4f"          #dark green (board)
GRID_COLOR = "#1b4332"           #very dark green (lines)
VALID_MOVE_COLOR = "#74c69d"     #light green (move hints)
BLACK_COLOR = "#1a1a1a"
WHITE_COLOR = "#f0f0f0"
BG_COLOR = "#081c15"             #window background


class OthelloApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Othello")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)

        # Game variables
        self.board = create_board()
        self.human_player = BLACK       # updated according to the player's choice
        self.computer_player = WHITE
        self.current_player = BLACK     # Black always starts
        self.level = tk.StringVar(value="Medium")
        self.game_active = False
        self.computer_thinking = False  # lock to ignore clicks while the computer is thinking

        self._build_interface()
        self._show_welcome_screen()

        # Interface construction

    def _build_interface(self):
        """Build all the tkinter widgets."""
        #Game board
        board_frame = tk.Frame(self.root, bg=BG_COLOR)
        board_frame.grid(row=0, column=0, padx=20, pady=20)
        width = BOARD_SIZE + 2 * MARGIN
        height = BOARD_SIZE + 2 * MARGIN
        self.canvas = tk.Canvas(board_frame,width=width, height=height,bg=BOARD_COLOR, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._human_click)
            
        #Information panel and new game button
        info_frame = tk.Frame(self.root, bg=BG_COLOR)
        info_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="n")

        #Title
        tk.Label(info_frame, text="OTHELLO", font=("Helvetica", 24, "bold"),bg=BG_COLOR, fg="white").pack(pady=(0, 20))

        #Score
        score_frame = tk.Frame(info_frame, bg="#1b4332", bd=0)
        score_frame.pack(fill="x", pady=8)

        tk.Label(score_frame, text="⬛", font=("Helvetica", 20),
                 bg="#1b4332", fg=BLACK_COLOR).grid(row=0, column=0, padx=15, pady=8)
        self.black_label = tk.Label(score_frame, text="2",
                                    font=("Helvetica", 22, "bold"),
                                    bg="#1b4332", fg="white")
        self.black_label.grid(row=0, column=1, padx=5)

        tk.Label(score_frame, text="vs", font=("Helvetica", 14),
                 bg="#1b4332", fg="#adb5bd").grid(row=0, column=2, padx=10)

        self.white_label = tk.Label(score_frame, text="2",
                                    font=("Helvetica", 22, "bold"),
                                    bg="#1b4332", fg="white")
        self.white_label.grid(row=0, column=3, padx=5)
        tk.Label(score_frame, text="⬜", font=("Helvetica", 20),
                 bg="#1b4332", fg=WHITE_COLOR).grid(row=0, column=4, padx=15, pady=8)

        #Current turn
        self.turn_label = tk.Label(
            info_frame, text="",
            font=("Helvetica", 13), bg=BG_COLOR, fg="#74c69d", wraplength=200)
        self.turn_label.pack(pady=10)

        #Difficulty level
        tk.Label(info_frame, text="Difficulty level:",
                 font=("Helvetica", 12), bg=BG_COLOR, fg="#adb5bd").pack(pady=(10, 4))

        for level in ["Easy", "Medium", "Hard"]:
            tk.Radiobutton(
                info_frame, text=level,
                variable=self.level, value=level,
                font=("Helvetica", 12),
                bg=BG_COLOR, fg="white",
                selectcolor=BG_COLOR,
                activebackground=BG_COLOR, activeforeground="#74c69d").pack(anchor="w", padx=20)

        #New game button
        self.new_game_button = tk.Button(
            info_frame, text="New game",
            font=("Helvetica", 13, "bold"),
            bg="#40916c", fg="white",
            activebackground="#52b788", activeforeground="white",
            relief="flat", padx=16, pady=8,
            command=self._show_welcome_screen)
        self.new_game_button.pack(pady=20, fill="x")

        #Status message (computer thinking, no move available, etc.)
        self.status_label = tk.Label(
            info_frame, text="",
            font=("Helvetica", 11, "italic"),
            bg=BG_COLOR, fg="#adb5bd", wraplength=200)
        self.status_label.pack()

        #Rules
        tk.Label(info_frame, text="Rules",
                 font=("Helvetica", 11, "underline"),
                 bg=BG_COLOR, fg="#74c69d",
                 cursor="hand2").pack(pady=(20, 0))
        rules = (
            "Place a disc to surround\n"
            "opponent discs in at least\n"
            "one direction.\n"
            "Surrounded discs are\n"
            "flipped. The player with\n"
            "the most discs at the end\n"
            "wins.")
        tk.Label(info_frame, text=rules,
                 font=("Helvetica", 10),
                 bg=BG_COLOR, fg="#adb5bd",
                 justify="left").pack()

    #Welcome screen (choice of the first player)

    def _show_welcome_screen(self):
        """Show a dialog window to choose who starts."""
        self.game_active = False
        window = tk.Toplevel(self.root)
        window.title("New game")
        window.configure(bg=BG_COLOR)
        window.resizable(False, False)
        window.grab_set()  # blocks the main window

        #Center the window
        window.geometry("500x250")
        self.root.update_idletasks()
        x = self.root.winfo_x() + self.root.winfo_width() // 2 - 160
        y = self.root.winfo_y() + self.root.winfo_height() // 2 - 130
        window.geometry(f"+{x}+{y}")

        tk.Label(window, text="New game",
                 font=("Helvetica", 18, "bold"),
                 bg=BG_COLOR, fg="white").pack(pady=20)

        tk.Label(window, text="Do you want to go first?",
                 font=("Helvetica", 13),
                 bg=BG_COLOR, fg="#adb5bd").pack()

        button_frame = tk.Frame(window, bg=BG_COLOR)
        button_frame.pack(pady=20)

        def choose(human_starts):
            window.destroy()
            self._start_game(human_starts)

        tk.Button(button_frame, text="Yes, I'll start",
                  font=("Helvetica", 12, "bold"),
                  bg="#40916c", fg="white",
                  activebackground="#52b788",
                  relief="flat", padx=14, pady=8,
                  command=lambda: choose(True)).pack(side="left", padx=10)

        tk.Button(button_frame, text="No, the computer starts",
                  font=("Helvetica", 12),
                  bg="#1b4332", fg="white",
                  activebackground="#2d6a4f",
                  relief="flat", padx=14, pady=8,
                  command=lambda: choose(False)).pack(side="left", padx=10)

        tk.Label(window, text="(The player who starts plays ⬛ Black)",
                 font=("Helvetica", 10),
                 bg=BG_COLOR, fg="#6c757d").pack()

    #Game start

    def _start_game(self, human_starts):
        """Initialize and start a new game."""
        self.board = create_board()
        self.human_player = BLACK
        self.computer_player = WHITE
        self.current_player = BLACK   # Black always starts (official Othello rules)

        # If the human does not start, the computer plays first (human is White)
        if not human_starts:
            self.human_player = WHITE
            self.computer_player = BLACK

        self.game_active = True
        self.computer_thinking = False
        self._refresh_display()

        # If the computer plays first
        if self.current_player == self.computer_player:
            self.root.after(400, self._computer_turn)

    #Display

    def _refresh_display(self):
        """Redraw the whole board and update the scores."""
        self._draw_board()
        self._update_score()
        self._update_turn()

    def _draw_board(self):
        """Draw the board, the discs and the valid-move hints."""
        self.canvas.delete("all")

        #Board background
        self.canvas.create_rectangle(
            MARGIN, MARGIN,
            MARGIN + BOARD_SIZE, MARGIN + BOARD_SIZE,
            fill=BOARD_COLOR, outline="")

        #Grid lines
        for i in range(9):
            x = MARGIN + i * CELL_SIZE
            y = MARGIN + i * CELL_SIZE
            self.canvas.create_line(x, MARGIN, x, MARGIN + BOARD_SIZE,
                                    fill=GRID_COLOR, width=1)
            self.canvas.create_line(MARGIN, y, MARGIN + BOARD_SIZE, y,
                                    fill=GRID_COLOR, width=1)

        #Reference dots (like on a real board)
        for pi, pj in [(2, 2), (2, 5), (5, 2), (5, 5)]:
            cx = MARGIN + pj * CELL_SIZE + CELL_SIZE // 2
            cy = MARGIN + pi * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                                    fill=GRID_COLOR, outline="")

        #Valid moves for the human (small green discs)
        if self.game_active and not self.computer_thinking:
            moves = valid_moves(self.board, self.human_player)
            for (row, col) in moves:
                if self.current_player == self.human_player:
                    cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
                    cy = MARGIN + row * CELL_SIZE + CELL_SIZE // 2
                    r = CELL_SIZE // 2 - 18
                    self.canvas.create_oval(
                        cx - r, cy - r, cx + r, cy + r,
                        fill=VALID_MOVE_COLOR, outline="", stipple="gray50")

        #Discs
        for i in range(8):
            for j in range(8):
                if self.board[i][j] != EMPTY:
                    self._draw_disc(i, j, self.board[i][j])

        #Coordinates (letters and numbers)
        for k in range(8):
            letter = chr(ord('A') + k)
            cx = MARGIN + k * CELL_SIZE + CELL_SIZE // 2
            cy = MARGIN + 8 * CELL_SIZE + 14
            self.canvas.create_text(cx, cy, text=letter,
                                    font=("Helvetica", 10), fill="#6c757d")
            cx2 = MARGIN - 14
            cy2 = MARGIN + k * CELL_SIZE + CELL_SIZE // 2
            self.canvas.create_text(cx2, cy2, text=str(k + 1),
                                    font=("Helvetica", 10), fill="#6c757d")

    def _draw_disc(self, row, col, color):
        """Draw a disc at position (row, col)."""
        cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
        cy = MARGIN + row * CELL_SIZE + CELL_SIZE // 2
        r = CELL_SIZE // 2 - 6

        if color == BLACK:
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill=BLACK_COLOR, outline="#444", width=1)
            self.canvas.create_oval(cx - r + 6, cy - r + 6, cx - r + 14, cy - r + 14,
                                    fill="#555", outline="")
        else:
            self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                    fill=WHITE_COLOR, outline="#ccc", width=1)
            self.canvas.create_oval(cx - r + 6, cy - r + 6, cx - r + 14, cy - r + 14,
                                    fill="#fff", outline="")

    def _update_score(self):
        """Update the disc counters."""
        black_count, white_count = count_discs(self.board)
        self.black_label.config(text=str(black_count))
        self.white_label.config(text=str(white_count))

    def _update_turn(self):
        """Update the label showing whose turn it is."""
        if not self.game_active:
            self.turn_label.config(text="")
            return
        if self.current_player == self.human_player:
            color = "Black ⬛" if self.human_player == BLACK else "White ⬜"
            self.turn_label.config(text=f"Your turn ({color})")
        else:
            color = "Black ⬛" if self.computer_player == BLACK else "White ⬜"
            self.turn_label.config(text=f"The computer is thinking ({color})…")

    # Turn management based on user clicks and available moves

    def _human_click(self, event):
        """Called when the human clicks on the canvas."""
        if not self.game_active or self.computer_thinking:
            return
        if self.current_player != self.human_player:
            return

        # Convert pixel coordinates to board cell
        col = (event.x - MARGIN) // CELL_SIZE
        row = (event.y - MARGIN) // CELL_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        # Check that the move is valid
        moves = valid_moves(self.board, self.human_player)
        if (row, col) not in moves:
            self.status_label.config(text="Invalid square!")
            self.root.after(1200, lambda: self.status_label.config(text=""))
            return

        # Play the move
        self.status_label.config(text="")
        play_move(self.board, row, col, self.human_player)
        self._refresh_display()

        # Move on to the next turn
        self._go_to_next_turn(after_computer=False)

    def _go_to_next_turn(self, after_computer):
        """
        After a move has been played, determine who plays next.
        Handles the case where a player has no available move.
        """
        if game_over(self.board):
            self._end_game()
            return

        # Switch player
        self.current_player = opponent(self.current_player)

        moves = valid_moves(self.board, self.current_player)

        if not moves:
            # The next player passes their turn
            if self.current_player == self.human_player:
                name = "You pass"
            else:
                name = "The computer passes"
            self.status_label.config(text=f"{name} the turn (no valid move).")
            # Switch back to the other player
            self.current_player = opponent(self.current_player)
            self._refresh_display()
            # Short delay so the message is readable
            if self.current_player == self.computer_player:
                self.root.after(1500, self._computer_turn)
            return

        self._refresh_display()
        # If it's the computer's turn, start it after a short delay
        if self.current_player == self.computer_player:
            self.root.after(400, self._computer_turn)

    def _computer_turn(self):
        """Compute and play the computer's move.
        Note: the search runs in the main thread, so the interface may freeze
        briefly at the Hard level."""
        if not self.game_active:
            return
        self.computer_thinking = True
        self.status_label.config(text="The computer is calculating…")
        self._draw_board()  # hides the valid-move hints
        move = choose_move(self.board, self.computer_player, self.level.get())
        self._apply_computer_move(move)

    def _apply_computer_move(self, move):
        """Apply the computer's move."""
        self.computer_thinking = False
        self.status_label.config(text="")

        if move is None:
            # The computer has no move -> the pass is handled in _go_to_next_turn
            self._go_to_next_turn(after_computer=True)
            return

        row, col = move
        play_move(self.board, row, col, self.computer_player)
        self._refresh_display()

        # Briefly highlight the disc placed by the computer
        self._highlight_cell(row, col)
        self.root.after(500, lambda: self._go_to_next_turn(after_computer=True))

    def _highlight_cell(self, row, col):
        """Briefly highlight the cell played by the computer."""
        cx = MARGIN + col * CELL_SIZE + CELL_SIZE // 2
        cy = MARGIN + row * CELL_SIZE + CELL_SIZE // 2
        r = CELL_SIZE // 2 - 2
        tag = self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                      outline="#f4d35e", width=3)
        self.root.after(500, lambda: self.canvas.delete(tag))

    # End of game

    def _end_game(self):
        """Handle the end of the game: show the result and offer to replay."""
        self.game_active = False
        black_count, white_count = count_discs(self.board)
        game_winner = winner(self.board)

        if game_winner == EMPTY:
            msg = f"It's a draw! ({black_count} - {white_count})"
        elif game_winner == self.human_player:
            msg = f"You won! ({black_count} - {white_count})"
        else:
            msg = f"The computer wins! ({black_count} - {white_count})"

        self.turn_label.config(text="Game over")
        self.status_label.config(text=msg)

        replay = messagebox.askyesno(
            "Game over",
            f"{msg}\n\nDo you want to play again?")
        if replay:
            self._show_welcome_screen()


# LAUNCH THE GAME (just run the file)

if __name__ == "__main__":
    root = tk.Tk()
    app = OthelloApp(root)
    root.mainloop()


