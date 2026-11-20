import chess
import chess.engine
import os
current_round = 1
def generate_opening_moves(board: chess.Board):
    engine = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
    threads = 1
    memory_size = 1000
    skill_level = engine.options['Skill Level'].max-1
    engine.configure({"Skill Level": skill_level})
    engine.configure({"Hash": memory_size})
    engine.configure({"Threads": threads})
    opening_moves = []
    ply_count = 20
    for _ in range(ply_count):
        move = engine.play(board, chess.engine.Limit(time=10/ply_count)).move.uci()
        opening_moves.append(move)
        board.push_uci(move)
    engine.quit()
    return opening_moves
for _ in range(1, 10, 2):
    if os.path.isfile(f"round{current_round}/game{_}.pgn"):
        continue
    player1_name = "Stockfish"
    player2_name = "Stockfish"
    opening_moves = " ".join(generate_opening_moves(chess.Board()))
    os.system(f"python3 game.py '{player1_name}' '{player2_name}' '{current_round}' '{_}' '{opening_moves}' 'white-custom'")
    os.system(f"python3 game.py '{player2_name}' '{player1_name}' '{current_round}' '{_+1}' '{opening_moves}' 'black-custom'")