import chess
import chess.engine
import os
current_round = 2
def generate_opening_moves(board: chess.Board):
    engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
    threads = 1
    memory_size = 1000
    skill_level = engine.options['Skill Level'].max-1
    engine.configure({"Skill Level": skill_level})
    engine.configure({"Hash": memory_size})
    engine.configure({"Threads": threads})
    opening_moves = []
    ply_count = 10
    for _ in range(ply_count):
        move = engine.play(board, chess.engine.Limit(time=10/ply_count)).move.uci()
        opening_moves.append(move)
        board.push_uci(move)
    engine.quit()
    return opening_moves
white_initial = "b1c3 g8f6 c3d5 f6d5 g1f3 d5f6 f3g1 f6g8"
black_initial = "g1f3 b8c6 b1c3 c6e5 f3e5 g8f6 c3b1 f6d5 e5f3 d5f6 f3g1 f6g8"
for _ in range(1, 10, 2):
    if os.path.isfile(f"round{current_round}/game{_}.pgn"):
        continue
    player1_name = "Leela"
    player2_name = "Stockfish"
    if white_initial == "b1c3 g8f6 c3d5 f6d5 g1f3 d5f6 f3g1 f6g8":
        white_initial = "g1f3 b8c6 f3e5 c6e5 b1c3 e5c6 c3b1 c6b8"
    elif white_initial == "g1f3 b8c6 f3e5 c6e5 b1c3 e5c6 c3b1 c6b8":
        white_initial = "b1c3 g8f6 c3d5 f6d5 g1f3 d5f6 f3g1 f6g8"
    if black_initial == "g1f3 b8c6 b1c3 c6e5 f3e5 g8f6 c3b1 f6d5 e5f3 d5f6 f3g1 f6g8":
        black_initial = "b1c3 g8f6 g1f3 f6d5 c3d5 b8c6 f3g1 c6e5 d5c3 e5c6 c3b1 c6b8"
    elif black_initial == "b1c3 g8f6 g1f3 f6d5 c3d5 b8c6 f3g1 c6e5 d5c3 e5c6 c3b1 c6b8":
        black_initial = "g1f3 b8c6 b1c3 c6e5 f3e5 g8f6 c3b1 f6d5 e5f3 d5f6 f3g1 f6g8"
    white_board = chess.Board()
    for move in white_initial.split():
        white_board.push_uci(move)
    white_opening_moves = white_initial + " " + " ".join(generate_opening_moves(white_board))
    black_board = chess.Board()
    for move in black_initial.split():
        black_board.push_uci(move)
    black_opening_moves = black_initial + " " + " ".join(generate_opening_moves(black_board))
    os.system(f"python3 game.py '{player1_name}' '{player2_name}' '{current_round}' '{_}' '{black_opening_moves}' 'white-custom'")
    os.system(f"python3 game.py '{player2_name}' '{player1_name}' '{current_round}' '{_+1}' '{white_opening_moves}' 'black-custom'")