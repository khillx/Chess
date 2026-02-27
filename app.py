from flask import Flask, jsonify, request, send_from_directory
from chess_engine import ChessBoard, ChessAI, WHITE, BLACK
import os

app = Flask(__name__, static_folder='static')


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/new_game', methods=['POST'])
def new_game():
    board = ChessBoard()
    return jsonify(board.to_dict())


@app.route('/api/legal_moves', methods=['POST'])
def legal_moves():
    data = request.json
    board = ChessBoard.from_dict(data['board'])
    row, col = data['row'], data['col']
    piece = board.board[row][col]
    
    if piece == 0 or board.piece_color(piece) != board.turn:
        return jsonify({'moves': []})
    
    all_legal = board.generate_legal_moves()
    piece_moves = [(tr, tc, promo) for (fr, fc, tr, tc, promo) in all_legal if fr == row and fc == col]
    
    return jsonify({'moves': piece_moves})


@app.route('/api/make_move', methods=['POST'])
def make_move():
    data = request.json
    board = ChessBoard.from_dict(data['board'])
    move = tuple(data['move'])
    # Convert promo back to int or None
    move = (move[0], move[1], move[2], move[3], move[4] if len(move) > 4 else None)
    
    legal = board.generate_legal_moves()
    move_list = [(fr, fc, tr, tc, promo) for (fr, fc, tr, tc, promo) in legal]
    
    fr, fc, tr, tc, promo = move
    matched = None
    for lm in move_list:
        if lm[0]==fr and lm[1]==fc and lm[2]==tr and lm[3]==tc:
            if promo is None or lm[4] == promo:
                matched = lm
                break
    
    if matched is None:
        return jsonify({'error': 'Illegal move', 'board': board.to_dict()}), 400
    
    board.apply_move(matched)
    return jsonify(board.to_dict())


@app.route('/api/ai_move', methods=['POST'])
def ai_move():
    data = request.json
    board = ChessBoard.from_dict(data['board'])
    depth = data.get('depth', 3)
    
    if board.is_checkmate() or board.is_stalemate():
        return jsonify({'board': board.to_dict(), 'move': None})
    
    ai = ChessAI(depth=depth)
    move, score, nodes = ai.get_best_move(board)
    
    if move is None:
        return jsonify({'board': board.to_dict(), 'move': None, 'nodes': nodes})
    
    board.apply_move(move)
    return jsonify({
        'board': board.to_dict(),
        'move': list(move),
        'score': score,
        'nodes': nodes
    })


@app.route('/api/validate', methods=['POST'])
def validate():
    data = request.json
    board = ChessBoard.from_dict(data['board'])
    return jsonify({
        'legal_moves_count': len(board.generate_legal_moves()),
        'in_check': board.is_in_check(board.turn),
        'is_checkmate': board.is_checkmate(),
        'is_stalemate': board.is_stalemate()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
