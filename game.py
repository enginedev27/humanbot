import chess
import chess.engine
import subprocess
import chess.pgn
import os
import sys
import time
import random
player1 = sys.argv[1]
player2 = sys.argv[2]
games = int(sys.argv[3])
board = int(sys.argv[4])
match = f"round{games}"
if os.path.isfile(f"{match}/game{board}.pgn"):
    sys.exit()
engines = {
    "Stockfish": "/opt/homebrew/bin/stockfish",
    "Leela": "/opt/homebrew/bin/lc0"
}
class FastStockfish():
    def __init__(self, engine_path: str):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.id = {
            'name': f"{self.engine.id['name']} FastStockfish"
        }
        self.possible_responses = {}
        self.current_variation = []
    def configure(self, dict: dict):
        self.engine.configure(dict)
    def play(self, board: chess.Board, limit: chess.engine.Limit, info=chess.engine.INFO_ALL):
        if len(list(board.legal_moves)) == 1:
            return chess.engine.PlayResult(move=list(board.legal_moves)[0], info=None, ponder=None)
        if limit.time == None:
            white_clock = limit.white_clock
            black_clock = limit.black_clock
            white_inc = limit.white_inc
            black_inc = limit.black_inc
            remaining_time = white_clock/10 + white_inc/2 if board.turn == chess.WHITE else black_clock/10 + black_inc/2
        else:
            remaining_time = limit.time
        best_move = None
        analysis = None
        if len(board.move_stack) > 0:
            if self.current_variation == [] and board.move_stack[-1].uci() in self.possible_responses:
                self.current_variation = self.possible_responses[board.move_stack[-1].uci()]
            if self.current_variation != []:
                new_board = board.copy()
                for move in new_board.legal_moves:
                    new_board.push(move)
                    if new_board.fen() in self.current_variation:
                        best_move = move
                    new_board.pop()
                    if best_move != None:
                        return chess.engine.PlayResult(move=best_move, info=self.current_variation, ponder=None)
        self.possible_responses.clear()
        self.current_variation.clear()
        unscaled_limit = chess.engine.Limit(time=remaining_time/2)
        engine_info = self.engine.play(board, unscaled_limit, info=info)
        best_move = engine_info.move
        newer_board = board.copy()
        newer_board.push(best_move)
        if newer_board.is_game_over() == False:
            analysis = self.engine.analyse(newer_board, unscaled_limit, info=info, multipv=len(list(board.legal_moves)))
            for info_string in analysis:
                positions = []
                newest_board = newer_board.copy()
                for move in info_string['pv']:
                    newest_board.push(move)
                    positions.append(newest_board.fen())
                self.possible_responses[info_string['pv'][0].uci()] = positions
        return chess.engine.PlayResult(move=best_move, info=analysis, ponder=None)
    def quit(self):
        self.engine.quit()
class HumanBot():
    def __init__(self, engine_path: str):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.id = {
            'name': f"{self.engine.id['name']}+Elite Leela Hybrid 20 MAX CPL BLUNDER=20CPL"
        }
        self.leela = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/lc0", stderr=subprocess.DEVNULL)
        self.leela.configure({"Threads": 1})
        self.leela.configure({"RamLimitMb": 1000})
        self.leela.configure({"WeightsFile": "/Users/me/Desktop/stockfishvariants/leela/Elite-Leela-v2-128x10x8h-1704000.pb.gz"})
        self.leela.configure({"VerboseMoveStats": True})
        self.leela.configure({"PolicyTemperature": 1.0})
    def configure(self, dict: dict):
        self.engine.configure(dict)
    def play(self, board: chess.Board, limit: chess.engine.Limit, info=chess.engine.INFO_ALL):
        if len(list(board.legal_moves)) == 1:
            return chess.engine.PlayResult(move=list(board.legal_moves)[0], info=None, ponder=None)
        if limit.time == None:
            white_clock = limit.white_clock
            black_clock = limit.black_clock
            white_inc = limit.white_inc
            black_inc = limit.black_inc
            remaining_time = white_clock/10 + white_inc/2 if board.turn == chess.WHITE else black_clock/10 + black_inc/2
        else:
            remaining_time = limit.time
        half_time = chess.engine.Limit(time=remaining_time/2)
        leela_moves = {}
        break_flag = False
        master_analysis = self.engine.analyse(board, half_time, info=info, multipv=len(list(board.legal_moves)))
        current_eval = master_analysis[0]['score'].relative.score(mate_score=sys.maxsize)
        fallback_move = master_analysis[0]['pv'][0]
        candidate_moves = 0
        for engine_string in master_analysis:
            if current_eval-20 > engine_string['score'].relative.score(mate_score=sys.maxsize):
                continue
            candidate_moves += 1
        unscaled_limit = chess.engine.Limit(time=remaining_time/(2*candidate_moves))
        if unscaled_limit.time < 0.3 or candidate_moves == 1:
            return chess.engine.PlayResult(move=fallback_move, info={'pv': fallback_move}, ponder=None)
        for engine_info in master_analysis:
            if current_eval-20 > engine_info['score'].relative.score(mate_score=sys.maxsize):
                continue
            move = engine_info['pv'][0]
            board.push(move)
            start_time = time.time()
            leela_analysis = self.leela.analysis(board, chess.engine.Limit(nodes=1), info=info, multipv=len(list(board.legal_moves)))
            time_spent = time.time()-start_time
            if unscaled_limit.time-time_spent > 0:
                modified_limit = chess.engine.Limit(time=unscaled_limit.time-time_spent)
                engine_analysis = self.engine.analyse(board, modified_limit, info=info, multipv=len(list(board.legal_moves)))
                sub_dict = []
                for info_string in leela_analysis:
                    if 'string' in info_string:
                        if 'node' not in info_string['string']:
                            leela_move = info_string['string'].split("(")[0].strip()
                            weight = float(info_string['string'].split("(P:")[1].split(")")[0].strip().replace("%", ""))
                            for engine_move in engine_analysis:
                                if engine_move['pv'][0].uci() == leela_move:
                                    sub_dict.append([leela_move, -engine_move['score'].relative.score(mate_score=sys.maxsize), weight])
                leela_moves[move.uci()] = sub_dict
            else:
                break_flag = True
            board.pop()
            if break_flag:
                return chess.engine.PlayResult(move=fallback_move, info=master_analysis, ponder=None)
        blunder_chances = {}
        for move, variation in leela_moves.items():
            sub_blunder = 0
            for moves in variation:
                if moves[1]-current_eval >= 20:
                    sub_blunder += moves[2]
            blunder_chances[move] = sub_blunder
        max_blunder = 0
        best_moves = []
        for blunder_move, chances in blunder_chances.items():
            if chances < 10:
                continue
            if chances > max_blunder:
                best_moves.clear()
                best_moves.append(blunder_move)
                max_blunder = chances
            elif chances == max_blunder:
                best_moves.append(blunder_move)
        if max_blunder < 10:
            return chess.engine.PlayResult(move=fallback_move, info={'pv': fallback_move}, ponder=None)
        best_move = random.choice(best_moves)
        return chess.engine.PlayResult(move=chess.Move.from_uci(best_move), info=blunder_chances, ponder=None)
    def quit(self):
        self.engine.quit()
        self.leela.quit()
class MaiaBot():
    def __init__(self, engine_path: str):
        self.engine = chess.engine.SimpleEngine.popen_uci(engine_path)
        self.id = {'name': self.engine.id['name']}
        self.stockfish = chess.engine.SimpleEngine.popen_uci("/opt/homebrew/bin/stockfish")
        self.stockfish.configure({"Hash": 1000})
        self.stockfish.configure({"Threads": 1})
    def play(self, board: chess.Board, limit: chess.engine.Limit, info=chess.engine.INFO_ALL):
        actual_maia = self.engine.play(board, chess.engine.Limit(nodes=50), info=info).move
        return chess.engine.PlayResult(move=actual_maia, info=None, ponder=None)
    def configure(self, dict: dict):
        self.engine.configure(dict)
    def quit(self):
        self.engine.quit()
        self.stockfish.quit()
#engine1 = FastStockfish(engines[player1]) if sys.argv[6] == 'white-custom' else chess.engine.SimpleEngine.popen_uci(engines[player1])
#engine2 = FastStockfish(engines[player2]) if sys.argv[6] == 'black-custom' else chess.engine.SimpleEngine.popen_uci(engines[player2])
engine1 = MaiaBot(engines[player1]) if sys.argv[6] == 'white-custom' else HumanBot(engines[player1])
engine2 = MaiaBot(engines[player2]) if sys.argv[6] == 'black-custom' else HumanBot(engines[player2])

threads = 1
memory_size = 1000
engine1_name = engine1.id['name']
engine2_name = engine2.id['name']
try:
    engine1.configure({"Hash": memory_size})
except chess.engine.EngineError:
    engine1_name = "Elite Leela nodes=50"
    engine1.configure({"RamLimitMb": memory_size})
    engine1.configure({"WeightsFile": "/Users/me/Desktop/stockfishvariants/leela/Elite-Leela-v2-128x10x8h-1704000.pb.gz"})
engine1.configure({"Threads": threads})

try:
    engine2.configure({"Hash": memory_size})
except chess.engine.EngineError:
    engine2_name = "Elite Leela nodes=50"
    engine2.configure({"RamLimitMb": memory_size})
    engine2.configure({"WeightsFile": "/Users/me/Desktop/stockfishvariants/leela/Elite-Leela-v2-128x10x8h-1704000.pb.gz"})
engine2.configure({"Threads": threads})

engine = [engine1, engine2]
node = None
chess_board = chess.Board()
game = chess.pgn.Game()
game.headers["Round"] = f"{games}.{board}"
game.headers["White"] = engine1_name
game.headers["Black"] = engine2_name
game.headers["WhiteTitle"] = "BOT"
game.headers["BlackTitle"] = "BOT"
game.headers["Result"] = "*"
print(game, file=open(f"{match}/game{board}.pgn", "w"), end="\n\n")
white_clock = 60*3
black_clock = 60*3
inc = 3
opening_moves = sys.argv[5].split()
while chess_board.is_game_over() == False and chess_board.can_claim_fifty_moves() == False:
    if len(chess_board.move_stack) < len(opening_moves):
        if chess_board.turn == chess.WHITE:
            hour = int(white_clock/3600)
            minute = int(white_clock/60) % 60
            second = white_clock % 60
        elif chess_board.turn == chess.BLACK:
            hour = int(black_clock/3600)
            minute = int(black_clock/60) % 60
            second = black_clock % 60
        move = chess.Move.from_uci(opening_moves[len(chess_board.move_stack)])
    else:
        start = time.time()
        engine_limit = chess.engine.Limit(white_clock=white_clock, black_clock=black_clock, white_inc=inc, black_inc=inc)
        if chess_board.turn == chess.WHITE:
            engine_info = engine[0].play(chess_board, engine_limit, info=chess.engine.INFO_ALL)
            move = engine_info.move
        elif chess_board.turn == chess.BLACK:
            engine_info = engine[1].play(chess_board, engine_limit, info=chess.engine.INFO_ALL)
            move = engine_info.move
        print(engine_info.info)
        if chess_board.turn == chess.WHITE and "nodes=" not in engine1_name:
            white_clock -= time.time()-start
            if white_clock <= 0:
                game.headers["Result"] = "0-1"
                break
            white_clock += inc
            hour = int(white_clock/3600)
            minute = int(white_clock/60) % 60
            second = white_clock % 60
        elif chess_board.turn == chess.BLACK and "nodes=" not in engine2_name:
            black_clock -= time.time()-start
            if black_clock <= 0:
                game.headers["Result"] = "1-0"
                break
            black_clock += inc
            hour = int(black_clock/3600)
            minute = int(black_clock/60) % 60
            second = black_clock % 60
    chess_board.push(move)
    if node == None:
        node = game.add_variation(move)
    else:
        node = node.add_variation(move)
    if "nodes=" not in engine1_name and chess_board.turn == chess.BLACK or "nodes=" not in engine2_name and chess_board.turn == chess.WHITE:
        node.comment = f"[%clk {str(int(hour)).zfill(2)}:{str(int(minute)).zfill(2)}:{str(int(second)).zfill(2)}]"
    if game.headers["Result"] == "*":
        if chess_board.can_claim_fifty_moves():
            game.headers["Result"] = "1/2-1/2"
        else:
            game.headers["Result"] = chess_board.result()
    print(game, file=open(f"{match}/game{board}.pgn", "w"), end="\n\n")
print(game, file=open(f"{match}/game{board}.pgn", "w"), end="\n\n")
engine[0].quit()
engine[1].quit()