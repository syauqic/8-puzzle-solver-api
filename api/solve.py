import copy
from enum import Enum
import random
# PENTING: Import modul time untuk mengukur waktu eksekusi
import time 
# Tambahan untuk API (PENTING!)
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- INISIALISASI FLASK ---
app = Flask(__name__)
# Mengizinkan frontend (di domain lain) untuk mengakses API
CORS(app) 

# --- CLASS ENUM ---
class MoveEnum(Enum):
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4
    NONE = 5

# =========================================================
# FUNGSI BARU UNTUK KONVERSI STATE (TETAP SAMA)
# =========================================================

def stateToTuple(state_matrix: list[list[int]]) -> tuple:
    """Mengubah matriks list 3x3 menjadi tuple 1D untuk perbandingan yang aman."""
    flat_list = [item for sublist in state_matrix for item in sublist]
    return tuple(flat_list)

def tupleToState(state_tuple: tuple) -> list[list[int]]:
    """Mengubah tuple 1D kembali menjadi matriks list 3x3."""
    if len(state_tuple) != 9:
        raise ValueError("Tuple harus memiliki 9 elemen untuk konversi 3x3.")
        
    return [
        list(state_tuple[0:3]),
        list(state_tuple[3:6]),
        list(state_tuple[6:9])
    ]

# =========================================================
# FUNGSI INTI (BEST-FIRST SEARCH)
# =========================================================

def convertFrontEndToMoves(bfsList) -> dict:
    """Mengkonversi perbedaan state (sebelum & sesudah) menjadi MoveEnum."""
    if not bfsList:
        return []
        
    # State awal di langkah 0, diberi MoveEnum.NONE
    bfsList[0]["moves"] = [MoveEnum.NONE]
    
    # prevMove adalah state tuple dari langkah sebelumnya
    prevMove = bfsList[0]["state"] 

    for step in bfsList[1:]:
        moves = []
        
        # frontEndPath hanya berisi satu state tujuan (karena sudah path terpendek)
        for item in step["frontEndPath"]:
            move = beforeAfterToMove(prevMove, item)
            moves.append(move)
            prevMove = item

        step["moves"] = moves
        
    return bfsList
        
def beforeAfterToMove(before_tuple, after_tuple):
    """Menghitung arah pergerakan (MoveEnum) dari state sebelum ke state sesudah."""
    # DARI TUPLE KE MATRIKS LIST
    before = tupleToState(before_tuple)
    
    # Cari posisi 0 ('blank tile') di state sebelumnya
    foundZero = None
    for i in range(len(before)):
        for j in range(len(before[i])):
            if before[i][j] == 0:
                foundZero = (i, j)
                break
        if foundZero:
            break
    
    if not foundZero:
        return MoveEnum.NONE

    # Definisikan kemungkinan pergerakan (UP, DOWN, LEFT, RIGHT)
    possible_moves = []
    
    # [x - 1] [y] (UP: Menggeser ubin di atas ke bawah, 0 bergerak ke atas)
    if foundZero[0] - 1 >= 0:
        temp = copy.deepcopy(before)
        temp[foundZero[0]][foundZero[1]] = temp[foundZero[0] - 1][foundZero[1]]
        temp[foundZero[0] - 1][foundZero[1]] = 0
        possible_moves.append({"Move": MoveEnum.UP, "State": temp})

    # [x + 1] [y] (DOWN: Menggeser ubin di bawah ke atas, 0 bergerak ke bawah)
    if foundZero[0] + 1 <= 2:
        temp = copy.deepcopy(before)
        temp[foundZero[0]][foundZero[1]] = temp[foundZero[0] + 1][foundZero[1]]
        temp[foundZero[0] + 1][foundZero[1]] = 0
        possible_moves.append({"Move": MoveEnum.DOWN, "State": temp})

    # [x] [y - 1] (LEFT: Menggeser ubin di kiri ke kanan, 0 bergerak ke kiri)
    if foundZero[1] - 1 >= 0:
        temp = copy.deepcopy(before)
        temp[foundZero[0]][foundZero[1]] = temp[foundZero[0]][foundZero[1] - 1]
        temp[foundZero[0]][foundZero[1] - 1] = 0
        possible_moves.append({"Move": MoveEnum.LEFT, "State": temp})

    # [x] [y + 1] (RIGHT: Menggeser ubin di kanan ke kiri, 0 bergerak ke kanan)
    if foundZero[1] + 1 <= 2:
        temp = copy.deepcopy(before)
        temp[foundZero[0]][foundZero[1]] = temp[foundZero[0]][foundZero[1] + 1]
        temp[foundZero[0]][foundZero[1] + 1] = 0
        possible_moves.append({"Move": MoveEnum.RIGHT, "State": temp})
        
    for move in possible_moves:
        # Konversi State di move menjadi tuple untuk perbandingan yang aman
        if stateToTuple(move["State"]) == after_tuple:
            return move["Move"]
            
    return MoveEnum.NONE
    
def convertToFrontEnd(bfsList) -> list:
    """
    MENGGANTIKAN FUNGSI backTrack.
    Mengambil path solusi lengkap dari langkah terakhir yang mencapai goal, 
    memastikan urutan langkah runtut.
    """
    frontEndList = []

    # 1. Cek apakah BFS menemukan solusi
    # steps hanya berisi 1 item (goal state) jika solusi ditemukan
    if not bfsList or bfsList[-1]["heuristic"] != 0:
        return []

    # 2. Langkah terakhir berisi path lengkap ke goal state
    final_step = bfsList[-1]
    
    # Path yang benar: [state awal, step 1, step 2, ..., goal state]
    final_path_tuples = final_step["path"] + [final_step["state"]] 

    # 3. Konversi path menjadi format list step frontend
    for state_tuple in final_path_tuples:
        step_entry = {
            "state": state_tuple,
            # frontEndPath hanya berisi state tujuan langkah ini (untuk animasi 1 langkah)
            "frontEndPath": [state_tuple] 
        }
        frontEndList.append(step_entry)

    return frontEndList

# Fungsi backTrack lama telah dihapus.
    
def BestFirstSearch(initialState, goalState) -> dict:
    """Implementasi Best-First Search (Greedy BFS) dengan Manhattan Distance."""
    
    # --- PENGUKURAN WAKTU DIMULAI ---
    startTime = time.time()
    # ---------------------------------
    
    frontier = []
    explored = set()
    steps = [] 

    # KONVERSI KE TUPLE SAAT AWAL
    initialStateTuple = stateToTuple(initialState)
    goalStateTuple = stateToTuple(goalState)
    
    frontier.append({
        "state": initialStateTuple, 
        "heuristic": countHeuristic(initialState, goalState), 
        "path": []
    })
    
    max_exploration_limit = 10000 
    state_tuple = initialStateTuple # Inisialisasi awal untuk memastikan state_tuple ada

    while len(frontier) > 0:
        currentState = frontier.pop(0)
        state_tuple = currentState["state"]
        
        if state_tuple in explored:
            continue
        explored.add(state_tuple)

        if (len(explored) >= max_exploration_limit): 
            break
        
        if (state_tuple == goalStateTuple):
            # Jika goal tercapai, simpan node terakhir ini dan HENTIKAN
            steps.append(currentState)
            break
        
        currentStateMatrix = tupleToState(state_tuple)
        moves = findMoves({"state": currentStateMatrix})
        
        # Path baru untuk node tetangga: Path lama + state saat ini
        pathList = list(currentState["path"])
        pathList.append(state_tuple) 

        for move_matrix in moves:
            newMoveTuple = stateToTuple(move_matrix)
            
            if newMoveTuple not in explored: 
                frontier.append({
                    "state": newMoveTuple, 
                    "heuristic": countHeuristic(move_matrix, goalState),
                    "path": pathList 
                })

        frontier.sort(key=lambda x: x["heuristic"])
        
    # --- PENGUKURAN WAKTU SELESAI ---
    endTime = time.time()
    executionTime = endTime - startTime
    # ----------------------------------

    winState = (state_tuple == goalStateTuple)

    # Hanya jika winState=True, kita memiliki steps yang akan diolah
    frontEndConverted = convertToFrontEnd(steps)
    convertedMoves = convertFrontEndToMoves(frontEndConverted)
    
    totalSteps = len(convertedMoves) # Hitung total langkah

    # --- RETURN LENGKAP DENGAN WAKTU DAN LANGKAH ---
    return {
        "winState": winState, 
        "content": convertedMoves, 
        "executionTime": executionTime, 
        "totalSteps": totalSteps
    }

def countHeuristic(currentStateMatrix, goalStateMatrix) -> int:
    """Menghitung Heuristik Manhattan Distance."""
    heuristic = 0
    for num in range(1, 9): # Hanya tile 1 sampai 8
        currentFound = None
        goalFound = None
        
        for r in range(3):
            for c in range(3):
                if currentStateMatrix[r][c] == num:
                    currentFound = (r, c)
                if goalStateMatrix[r][c] == num:
                    goalFound = (r, c)
        
        if currentFound and goalFound:
            # Manhattan Distance: |x1 - x2| + |y1 - y2|
            temp = abs(goalFound[0] - currentFound[0]) + abs(goalFound[1] - currentFound[1])
            heuristic += temp
            
    return heuristic
    
def findMoves(currentStateDict) -> list[list[list[int]]]:
    """Menghitung semua state tetangga yang mungkin dari state saat ini."""
    moves = []
    current_state = currentStateDict["state"]

    foundZero = None
    # Cari posisi 0
    for i in range(3):
        for j in range(3):
            if current_state[i][j] == 0:
                foundZero = (i, j)
                break
        if foundZero:
            break
    
    if not foundZero:
        return []

    r0, c0 = foundZero

    # Daftar potensi pergeseran (dr, dc)
    directions = [
        (-1, 0, MoveEnum.UP), 
        ( 1, 0, MoveEnum.DOWN),
        ( 0, -1, MoveEnum.LEFT),
        ( 0, 1, MoveEnum.RIGHT)
    ]
    
    for dr, dc, _ in directions:
        r1, c1 = r0 + dr, c0 + dc
        
        # Cek batas array 3x3
        if 0 <= r1 <= 2 and 0 <= c1 <= 2:
            temp_state = copy.deepcopy(current_state)
            
            # Tukar 0 dengan tile di posisi (r1, c1)
            temp_state[r0][c0] = temp_state[r1][c1]
            temp_state[r1][c1] = 0
            
            moves.append(temp_state)

    return moves

def getInitialState(choice) -> list[list[int]]:
    """Mengambil state awal berdasarkan pilihan angka."""
    
    goalState = [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 0]
    ]

    # Cek apakah state yang diberikan dapat dipecahkan (Solvable)
    def is_solvable(state):
        flat_list = [item for sublist in state for item in sublist if item != 0]
        inversions = 0
        for i in range(len(flat_list)):
            for j in range(i + 1, len(flat_list)):
                if flat_list[i] > flat_list[j]:
                    inversions += 1
        return inversions % 2 == 0

    result = []
    
    # Pilihan state puzzle Anda
    initial_states = {
        1: [[1, 2, 3], [4, 5, 6], [7, 0, 8]], 2: [[1, 2, 3], [4, 5, 6], [0, 7, 8]],
        3: [[1, 2, 3], [4, 0, 6], [7, 5, 8]], 4: [[1, 3, 6], [4, 0, 2], [7, 5, 8]],
        5: [[1, 2, 3], [5, 0, 6], [4, 7, 8]], 6: [[1, 2, 3], [4, 6, 0], [7, 5, 8]],
        7: [[1, 3, 6], [5, 0, 2], [4, 7, 8]], 8: [[1, 3, 6], [5, 2, 0], [4, 7, 8]],
        9: [[1, 2, 0], [4, 5, 3], [7, 8, 6]], 10: [[1, 0, 3], [4, 2, 6], [7, 5, 8]],
        11: [[2, 8, 3], [1, 6, 4], [7, 0, 5]], 12: [[5, 6, 7], [4, 0, 8], [3, 2, 1]],
        13: [[1, 6, 2], [5, 7, 3], [0, 4, 8]], 14: [[2, 3, 6], [1, 5, 0], [4, 7, 8]],
        15: [[8, 6, 7], [2, 5, 4], [3, 0, 1]], 16: [[4, 1, 3], [7, 2, 5], [0, 8, 6]],
        17: [[1, 3, 6], [4, 8, 2], [7, 0, 5]], 18: [[4, 5, 6], [1, 2, 3], [7, 8, 0]],
        19: [[6, 4, 7], [8, 5, 0], [3, 2, 1]], 20: [[1, 8, 2], [0, 4, 3], [7, 6, 5]]
    }
    
    result = initial_states.get(choice, initial_states[20])

    # Logika untuk menghasilkan state acak yang terpecahkan jika 'choice' tidak ada
    if choice not in initial_states or choice == 0: 
        while True:
            numbers = list(range(9))
            random.shuffle(numbers)
            temp_state = [numbers[i:i+3] for i in range(0, 9, 3)]
            if is_solvable(temp_state):
                result = temp_state
                break

    return result

# =========================================================
# ENDPOINT API (FUNGSI UTAMA UNTUK VERCEL)
# =========================================================

@app.route('/api/solve', methods=['POST'])
def handle_puzzle_request():
    """Menangani request SOLVE dan GENERATE dari frontend."""
    try:
        data = request.get_json()
        
        if data is None:
            return jsonify({
                "error": "Permintaan harus berisi JSON yang valid.",
                "details": "Pastikan Content-Type: application/json dan format body JSON sudah benar."
            }), 400
        
        action = data.get('action') 
        
        goalState = [
            [ 1, 2, 3 ],
            [ 4, 5, 6 ],
            [ 7, 8, 0 ]
        ]
        
        # --- 1. AKSI SOLVE ---
        if action == 'solve':
            initial_state = data.get('initialState')
            
            if not initial_state or not isinstance(initial_state, list):
                return jsonify({"error": "Format initialState tidak valid. Harus berupa matriks list 3x3."}), 400

            # Panggil fungsi solver inti
            result = BestFirstSearch(initial_state, goalState)
            
            # Konversi Enum dan Tuple kembali ke string dan List untuk JSON
            final_content = []
            for step in result.get("content", []):
                step_copy = copy.deepcopy(step)
                
                # Konversi MoveEnum ke string
                step_copy["moves"] = [move.name for move in step_copy["moves"]]
                
                # Konversi state tuple ke matriks list
                step_copy["state"] = tupleToState(step_copy["state"]) 
                
                # Konversi path tuple ke matriks list
                if "frontEndPath" in step_copy:
                    step_copy["frontEndPath"] = [tupleToState(t) for t in step_copy["frontEndPath"]]
                
                # Hapus path
                if "path" in step_copy:
                    del step_copy["path"]
                    
                final_content.append(step_copy)

            # --- FINAL RESULT TERMASUK WAKTU DAN LANGKAH ---
            final_result = {
                "winState": result.get("winState", False),
                "content": final_content,
                "executionTime": result.get("executionTime", 0),  # Ditambahkan
                "totalSteps": result.get("totalSteps", 0)        # Ditambahkan
            }
            
            return jsonify(final_result)
            
        # --- 2. AKSI GENERATE ---
        elif action == 'generate':
            choice_num = data.get('choiceNum', 20) 
            
            if not isinstance(choice_num, int):
                return jsonify({"error": "choiceNum harus berupa angka integer."}), 400
            
            new_state = getInitialState(choice_num)
            
            return jsonify({
                "initialState": new_state,
                "goalState": goalState
            })

        return jsonify({"error": "Aksi tidak dikenal. Gunakan 'solve' atau 'generate'."}), 400

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}") 
        return jsonify({
            "error": "Internal Server Error saat memproses permintaan.",
            "details": str(e), 
            "hint": "Cek log Vercel Anda, pastikan format input [list[list[int]]] sudah benar."
        }), 500