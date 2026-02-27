#Author: Nicholas Marchese

from copy import deepcopy

EMPTY = 0
PAWN, KNIGHT, BISHOP, ROOK, QUEEN, KING = 1, 2, 3, 4, 5, 6
WHITE, BLACK = 1, -1

PIECE_VALUES = {
    PAWN: 100,
    KNIGHT: 320,
    BISHOP: 330,
    ROOK: 500,
    QUEEN: 900,
    KING: 20000
}

# Positional bonus tables (from white's perspective, row 0 = rank 1)
PAWN_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [ 5,  5, 10, 25, 25, 10,  5,  5],
    [ 0,  0,  0, 20, 20,  0,  0,  0],
    [ 5, -5,-10,  0,  0,-10, -5,  5],
    [ 5, 10, 10,-20,-20, 10, 10,  5],
    [ 0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_TABLE = [
    [ 0,  0,  0,  0,  0,  0,  0,  0],
    [ 5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [ 0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [ -5,  0,  5,  5,  5,  5,  0, -5],
    [  0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

KING_MIDDLE_TABLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [ 20, 20,  0,  0,  0,  0, 20, 20],
    [ 20, 30, 10,  0,  0, 10, 30, 20]
]

PIECE_TABLES = {
    PAWN: PAWN_TABLE,
    KNIGHT: KNIGHT_TABLE,
    BISHOP: BISHOP_TABLE,
    ROOK: ROOK_TABLE,
    QUEEN: QUEEN_TABLE,
    KING: KING_MIDDLE_TABLE
}


class ChessBoard:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[EMPTY]*8 for _ in range(8)]
        self.turn = WHITE
        self.castling_rights = {
            WHITE: {'kingside': True, 'queenside': True},
            BLACK: {'kingside': True, 'queenside': True}
        }
        self.en_passant_target = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        self.move_history = []
        self._setup_pieces()

    def _setup_pieces(self):
        back_row = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for col, piece in enumerate(back_row):
            self.board[0][col] = -piece
        for col in range(8):
            self.board[1][col] = -PAWN

        for col, piece in enumerate(back_row):
            self.board[7][col] = piece
        for col in range(8):
            self.board[6][col] = PAWN

    def get_piece(self, row, col):
        return self.board[row][col]

    def piece_color(self, piece):
        if piece > 0: return WHITE
        if piece < 0: return BLACK
        return None

    def piece_type(self, piece):
        return abs(piece)

    def is_valid(self, row, col):
        return 0 <= row < 8 and 0 <= col < 8

    def find_king(self, color):
        king = color * KING
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == king:
                    return (r, c)
        return None

    def is_square_attacked(self, row, col, by_color):
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            r, c = row+dr, col+dc
            if self.is_valid(r,c) and self.board[r][c] == by_color * KNIGHT:
                return True
        pawn_dir = -by_color
        for dc in [-1, 1]:
            r, c = row + pawn_dir, col + dc
            if self.is_valid(r, c) and self.board[r][c] == by_color * PAWN:
                return True
        for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
            r, c = row+dr, col+dc
            while self.is_valid(r,c):
                p = self.board[r][c]
                if p != EMPTY:
                    if p == by_color * ROOK or p == by_color * QUEEN:
                        return True
                    break
                r += dr; c += dc
        for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
            r, c = row+dr, col+dc
            while self.is_valid(r,c):
                p = self.board[r][c]
                if p != EMPTY:
                    if p == by_color * BISHOP or p == by_color * QUEEN:
                        return True
                    break
                r += dr; c += dc
        for dr in [-1,0,1]:
            for dc in [-1,0,1]:
                if dr==0 and dc==0: continue
                r, c = row+dr, col+dc
                if self.is_valid(r,c) and self.board[r][c] == by_color * KING:
                    return True
        return False

    def is_in_check(self, color):
        king_pos = self.find_king(color)
        if king_pos is None:
            return False
        return self.is_square_attacked(king_pos[0], king_pos[1], -color)

    def generate_pseudo_moves(self, color):
        moves = []
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece == EMPTY or self.piece_color(piece) != color:
                    continue
                pt = self.piece_type(piece)
                if pt == PAWN:
                    moves.extend(self._pawn_moves(r, c, color))
                elif pt == KNIGHT:
                    moves.extend(self._knight_moves(r, c, color))
                elif pt == BISHOP:
                    moves.extend(self._sliding_moves(r, c, color, [(1,1),(1,-1),(-1,1),(-1,-1)]))
                elif pt == ROOK:
                    moves.extend(self._sliding_moves(r, c, color, [(0,1),(0,-1),(1,0),(-1,0)]))
                elif pt == QUEEN:
                    moves.extend(self._sliding_moves(r, c, color, [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]))
                elif pt == KING:
                    moves.extend(self._king_moves(r, c, color))
        return moves

    def _pawn_moves(self, row, col, color):
        moves = []
        direction = -color
        start_row = 6 if color == WHITE else 1
        promo_row = 0 if color == WHITE else 7

        nr = row + direction
        if self.is_valid(nr, col) and self.board[nr][col] == EMPTY:
            if nr == promo_row:
                for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
                    moves.append((row, col, nr, col, promo))
            else:
                moves.append((row, col, nr, col, None))
            if row == start_row:
                nr2 = row + 2*direction
                if self.board[nr2][col] == EMPTY:
                    moves.append((row, col, nr2, col, None))

        for dc in [-1, 1]:
            nc = col + dc
            if not self.is_valid(nr, nc): continue
            target = self.board[nr][nc]
            if target != EMPTY and self.piece_color(target) == -color:
                if nr == promo_row:
                    for promo in [QUEEN, ROOK, BISHOP, KNIGHT]:
                        moves.append((row, col, nr, nc, promo))
                else:
                    moves.append((row, col, nr, nc, None))
            # En passant
            if self.en_passant_target == (nr, nc):
                moves.append((row, col, nr, nc, None))

        return moves

    def _knight_moves(self, row, col, color):
        moves = []
        for dr, dc in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
            nr, nc = row+dr, col+dc
            if self.is_valid(nr, nc):
                target = self.board[nr][nc]
                if target == EMPTY or self.piece_color(target) == -color:
                    moves.append((row, col, nr, nc, None))
        return moves

    def _sliding_moves(self, row, col, color, directions):
        moves = []
        for dr, dc in directions:
            nr, nc = row+dr, col+dc
            while self.is_valid(nr, nc):
                target = self.board[nr][nc]
                if target == EMPTY:
                    moves.append((row, col, nr, nc, None))
                elif self.piece_color(target) == -color:
                    moves.append((row, col, nr, nc, None))
                    break
                else:
                    break
                nr += dr; nc += dc
        return moves

    def _king_moves(self, row, col, color):
        moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                nr, nc = row+dr, col+dc
                if self.is_valid(nr, nc):
                    target = self.board[nr][nc]
                    if target == EMPTY or self.piece_color(target) == -color:
                        moves.append((row, col, nr, nc, None))

        # Castling
        back_rank = 7 if color == WHITE else 0
        if row == back_rank and col == 4:
            if self.castling_rights[color]['kingside']:
                if (self.board[back_rank][5] == EMPTY and
                    self.board[back_rank][6] == EMPTY and
                    self.board[back_rank][7] == color * ROOK and
                    not self.is_square_attacked(back_rank, 4, -color) and
                    not self.is_square_attacked(back_rank, 5, -color) and
                    not self.is_square_attacked(back_rank, 6, -color)):
                    moves.append((row, col, back_rank, 6, None))
            if self.castling_rights[color]['queenside']:
                if (self.board[back_rank][3] == EMPTY and
                    self.board[back_rank][2] == EMPTY and
                    self.board[back_rank][1] == EMPTY and
                    self.board[back_rank][0] == color * ROOK and
                    not self.is_square_attacked(back_rank, 4, -color) and
                    not self.is_square_attacked(back_rank, 3, -color) and
                    not self.is_square_attacked(back_rank, 2, -color)):
                    moves.append((row, col, back_rank, 2, None))
        return moves

    def generate_legal_moves(self, color=None):
        if color is None:
            color = self.turn
        pseudo = self.generate_pseudo_moves(color)
        legal = []
        for move in pseudo:
            board_copy = deepcopy(self)
            board_copy.apply_move(move, update_turn=False)
            if not board_copy.is_in_check(color):
                legal.append(move)
        return legal

    def apply_move(self, move, update_turn=True):
        fr, fc, tr, tc, promo = move
        piece = self.board[fr][fc]
        color = self.piece_color(piece)
        pt = self.piece_type(piece)

        # Save state for history
        captured = self.board[tr][tc]
        old_ep = self.en_passant_target
        old_castling = deepcopy(self.castling_rights)

        self.en_passant_target = None

        if pt == PAWN and (tr, tc) == old_ep:
            ep_capture_row = tr + color
            self.board[ep_capture_row][tc] = EMPTY

        if pt == KING:
            back_rank = 7 if color == WHITE else 0
            if fc == 4 and tc == 6:
                self.board[back_rank][5] = self.board[back_rank][7]
                self.board[back_rank][7] = EMPTY
            elif fc == 4 and tc == 2:
                self.board[back_rank][3] = self.board[back_rank][0]
                self.board[back_rank][0] = EMPTY
            self.castling_rights[color]['kingside'] = False
            self.castling_rights[color]['queenside'] = False

        if pt == ROOK:
            back_rank = 7 if color == WHITE else 0
            if fr == back_rank:
                if fc == 7: self.castling_rights[color]['kingside'] = False
                if fc == 0: self.castling_rights[color]['queenside'] = False

        if captured != EMPTY:
            cap_color = self.piece_color(captured)
            cap_back = 7 if cap_color == WHITE else 0
            if tr == cap_back:
                if tc == 7: self.castling_rights[cap_color]['kingside'] = False
                if tc == 0: self.castling_rights[cap_color]['queenside'] = False

        if pt == PAWN and abs(tr - fr) == 2:
            self.en_passant_target = ((fr + tr) // 2, tc)

        self.board[tr][tc] = piece if not promo else color * promo
        self.board[fr][fc] = EMPTY

        if pt == PAWN or captured != EMPTY:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if update_turn:
            if color == BLACK:
                self.fullmove_number += 1
            self.turn = -color

        self.move_history.append(move)

    def is_checkmate(self):
        return self.is_in_check(self.turn) and len(self.generate_legal_moves()) == 0

    def is_stalemate(self):
        return not self.is_in_check(self.turn) and len(self.generate_legal_moves()) == 0

    def is_draw(self):
        return self.is_stalemate() or self.halfmove_clock >= 100

    # For Json serialization
    def to_dict(self):
        return {
            'board': self.board,
            'turn': self.turn,
            'castling_rights': {
                str(WHITE): self.castling_rights[WHITE],
                str(BLACK): self.castling_rights[BLACK]
            },
            'en_passant_target': self.en_passant_target,
            'in_check': self.is_in_check(self.turn),
            'is_checkmate': self.is_checkmate(),
            'is_stalemate': self.is_stalemate(),
            'fullmove_number': self.fullmove_number,
            'halfmove_clock': self.halfmove_clock
        }

    @classmethod
    def from_dict(cls, data):
        board = cls.__new__(cls)
        board.board = data['board']
        board.turn = data['turn']
        board.castling_rights = {
            WHITE: data['castling_rights'][str(WHITE)],
            BLACK: data['castling_rights'][str(BLACK)]
        }
        board.en_passant_target = data['en_passant_target']
        if board.en_passant_target:
            board.en_passant_target = tuple(board.en_passant_target)
        board.halfmove_clock = data.get('halfmove_clock', 0)
        board.fullmove_number = data.get('fullmove_number', 1)
        board.move_history = []
        return board


class ChessAI:
    def __init__(self, depth=4):
        self.depth = depth
        self.nodes_evaluated = 0

    def evaluate(self, board):
        score = 0
        for r in range(8):
            for c in range(8):
                piece = board.board[r][c]
                if piece == EMPTY:
                    continue
                color = board.piece_color(piece)
                pt = board.piece_type(piece)
                value = PIECE_VALUES[pt]
                table = PIECE_TABLES.get(pt)
                if table:
                    if color == WHITE:
                        pos_bonus = table[r][c]
                    else:
                        pos_bonus = table[7-r][c]
                    value += pos_bonus
                score += color * value
        return score

    def order_moves(self, board, moves):
        def move_score(move):
            fr, fc, tr, tc, promo = move
            target = board.board[tr][tc]
            piece = board.board[fr][fc]
            score = 0
            if target != EMPTY:
                # MVV-LVA: Most Valuable Victim - Least Valuable Attacker
                score += 10 * PIECE_VALUES[board.piece_type(target)] - PIECE_VALUES[board.piece_type(piece)]
            if promo:
                score += PIECE_VALUES[promo]
            return -score  # negative because we want highest first
        return sorted(moves, key=move_score)

    def minimax(self, board, depth, alpha, beta, maximizing):
        self.nodes_evaluated += 1

        if depth == 0:
            return self.evaluate(board), None

        legal_moves = board.generate_legal_moves()

        if not legal_moves:
            if board.is_in_check(board.turn):
                # Checkmate
                return (-99999 if maximizing else 99999), None
            else:
                # Stalemate
                return 0, None

        legal_moves = self.order_moves(board, legal_moves)
        best_move = None

        if maximizing:
            max_eval = float('-inf')
            for move in legal_moves:
                board_copy = deepcopy(board)
                board_copy.apply_move(move)
                eval_score, _ = self.minimax(board_copy, depth-1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in legal_moves:
                board_copy = deepcopy(board)
                board_copy.apply_move(move)
                eval_score, _ = self.minimax(board_copy, depth-1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def get_best_move(self, board):
        self.nodes_evaluated = 0
        maximizing = (board.turn == WHITE)
        score, move = self.minimax(board, self.depth, float('-inf'), float('inf'), maximizing)
        return move, score, self.nodes_evaluated
