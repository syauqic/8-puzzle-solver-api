import copy
from enum import Enum
import random
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
# FUNGSI BARU UNTUK KONVERSI STATE
# =========================================================

def stateToTuple(state_matrix: list[list[int]]) -> tuple:
    """Mengubah matriks list 3x3 menjadi tuple 1D untuk perbandingan yang aman."""
    # List comprehension untuk membuat list datar, lalu konversi ke tuple
    flat_list = [item for sublist in state_matrix for item in sublist]
    return tuple(flat_list)

def tupleToState(state_tuple: tuple) -> list[list[int]]:
    """Mengubah tuple 1D kembali menjadi matriks list 3x3."""
    # Memastikan tuple berukuran 9 elemen
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
        
        # frontEndPath berisi state tuple yang dilalui
        # item terakhir di frontEndPath adalah state tujuan langkah ini
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
    after = tupleToState(after_tuple)
    
    moves = []

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
        # PENTING: Konversi State di move menjadi tuple untuk perbandingan yang aman
        if stateToTuple(move["State"]) == after_tuple:
            return move["Move"]
            
    return MoveEnum.NONE
    
def convertToFrontEnd(bfsList) -> list:
    """Mengisi 'frontEndPath' (langkah-langkah perantara) untuk animasi frontend."""
    frontEndList = []

    for index in range(1, len(bfsList)):
        # Ambil state matriks dari langkah sebelumnya
        currentStateMatrix = tupleToState(bfsList[index - 1]["state"])
        
        # Hasilkan semua state yang mungkin dari state sebelumnya
        possibleMovesMatrix = findMoves({"state": currentStateMatrix})
        
        # Konversi semua possible state matrix menjadi tuple untuk perbandingan
        possible_states_tuple = [stateToTuple(s) for s in possibleMovesMatrix]
        
        current_state_tuple = bfsList[index]["state"]

        # Jika langkah saat ini ADALAH salah satu langkah langsung, simpan saja langkah tersebut
        if (current_state_tuple in possible_states_tuple): 
            bfsList[index]["frontEndPath"] = [current_state_tuple]
        # Jika bukan, lakukan backtrack untuk mendapatkan semua langkah perantara
        else:
            bfsList[index]["frontEndPath"] = backTrack(bfsList[index - 1], bfsList[index])

        frontEndList.append(bfsList[index])

    return frontEndList

def backTrack(start, end):
    """Menghitung path terpendek dari start ke end state berdasarkan path yang tersimpan di BFS."""
    # start["path"] dan end["path"] berisi list of TUPLE state
    # Cari irisan path
    common_path_items = [x for x in start["path"] if x in end["path"]] # Perbandingan aman dengan tuple

    frontEndPath = []

    startPath = list(start["path"])
    endPath = list(end["path"])

    if not common_path_items:
        # Seharusnya tidak terjadi jika BFS sukses, tapi sebagai fallback
        return [end["state"]] 

    # Ambil titik temu terakhir (common_path_items[len(common_path_items) - 1])
    common_item = common_path_items[-1]
    
    # Cari indeks titik temu di kedua path
    startIndex = startPath.index(common_item)
    endIndex = endPath.index(common_item)

    # Langkah dari START menuju titik temu (dibalik)
    for i in range(len(startPath) - 1, startIndex - 1, -1):
        frontEndPath.append(startPath[i])
        
    # Langkah dari titik temu menuju END
    for i in range(endIndex + 1, len(endPath), 1):
        frontEndPath.append(endPath[i])
        
    frontEndPath.append(end["state"])
    
    return frontEndPath
        
def BestFirstSearch(initialState, goalState) -> dict:
    """Implementasi Best-First Search (Greedy BFS) dengan Manhattan Distance."""
    frontier = []
    explored = set() # Menggunakan set untuk cek eksplorasi O(1)
    steps = []

    # KONVERSI KE TUPLE SAAT AWAL
    initialStateTuple = stateToTuple(initialState)
    goalStateTuple = stateToTuple(goalState)
    
    # State yang disimpan di frontier adalah TUPLE
    frontier.append({
        "state": initialStateTuple, 
        "heuristic": countHeuristic(initialState, goalState), 
        "path": []
    })
    
    max_exploration_limit = 10000 
    
    while len(frontier) > 0:
        currentState = frontier.pop(0)
        state_tuple = currentState["state"]
        
        # Cek kalau current state sudah pernah di cek sebelumnya (AMAN: perbandingan tuple)
        if state_tuple in explored:
            continue
        explored.add(state_tuple)

        # Batasan jumlah langkah
        if (len(explored) >= max_exploration_limit): 
             break

        steps.append(currentState)
        
        # Cek apabila sudah mencapai goal (AMAN: perbandingan tuple)
        if (state_tuple == goalStateTuple):
            break
        
        # Ambil state tuple, ubah ke matriks list, lalu kirim ke findMoves
        currentStateMatrix = tupleToState(state_tuple)
        moves = findMoves({"state": currentStateMatrix}) # findMoves sekarang bekerja dengan matriks list
        
        pathList = list(currentState["path"])
        pathList.append(state_tuple) # state_tuple ditambahkan ke path
        
        # Menambahkan move dan nilai heuristik yang dihitung ke antrian
        for move_matrix in moves:
            # move_matrix adalah matriks list 3x3
            newMoveTuple = stateToTuple(move_matrix) # KONVERSI KE TUPLE
            
            # State yang masuk ke frontier adalah TUPLE
            if newMoveTuple not in explored: # Cek jika belum dieksplorasi
                frontier.append({
                    "state": newMoveTuple, 
                    "heuristic": countHeuristic(move_matrix, goalState), # Hitung heuristik dari matriks
                    "path": pathList
                })

        # Disortir sehingga nilai berurut dari nilai heuristik terkecil
        frontier.sort(key=lambda x: x["heuristic"])

    winState = (state_tuple == goalStateTuple)

    # Jika pencarian sukses, konversi path ke format yang mudah diproses frontend
    frontEndConverted = convertToFrontEnd(steps)
    convertedMoves = convertFrontEndToMoves(frontEndConverted)

    # Output content berisi TUPLE, tapi akan dikonversi ke list saat jsonify di endpoint
    return {"winState": winState, "content": convertedMoves}

def countHeuristic(currentStateMatrix, goalStateMatrix) -> int:
    """Menghitung Heuristik Manhattan Distance."""
    # Fungsi ini menerima MATRIKS LIST
    heuristic = 0
    for num in range(1, 9): # Hanya tile 1 sampai 8
        currentFound = None
        goalFound = None
        
        # Cari posisi num di state saat ini
        for r in range(3):
            for c in range(3):
                if currentStateMatrix[r][c] == num:
                    currentFound = (r, c)
                if goalStateMatrix[r][c] == num:
                    goalFound = (r, c)
        
        if currentFound and goalFound:
            # Manhattan Distance
            temp = abs(goalFound[0] - currentFound[0]) + abs(goalFound[1] - currentFound[1])
            heuristic += temp
            
    return heuristic
    
def findMoves(currentStateDict) -> list[list[list[int]]]:
    """Menghitung semua state tetangga yang mungkin dari state saat ini."""
    # Menerima dictionary {"state": matrix}
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
    # (dr, dc) = (row change, col change)
    directions = [
        (-1, 0, MoveEnum.UP),    # Pindah ke atas (0: r-1, c0) -> Geser tile (r-1, c0) ke bawah
        ( 1, 0, MoveEnum.DOWN),  # Pindah ke bawah (0: r+1, c0) -> Geser tile (r+1, c0) ke atas
        ( 0, -1, MoveEnum.LEFT), # Pindah ke kiri (0: r0, c-1) -> Geser tile (r0, c-1) ke kanan
        ( 0, 1, MoveEnum.RIGHT)  # Pindah ke kanan (0: r0, c+1) -> Geser tile (r0, c+1) ke kiri
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
    # Dapatkan state awal dari logic Anda
    
    # State goal standard
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
    
    # Pilihan state puzzle Anda (sudah dimodifikasi agar lebih rapi)
    initial_states = {
        1: [[1, 2, 3], [4, 5, 6], [7, 0, 8]],
        2: [[1, 2, 3], [4, 5, 6], [0, 7, 8]],
        3: [[1, 2, 3], [4, 0, 6], [7, 5, 8]],
        4: [[1, 3, 6], [4, 0, 2], [7, 5, 8]],
        5: [[1, 2, 3], [5, 0, 6], [4, 7, 8]],
        6: [[1, 2, 3], [4, 6, 0], [7, 5, 8]],
        7: [[1, 3, 6], [5, 0, 2], [4, 7, 8]],
        8: [[1, 3, 6], [5, 2, 0], [4, 7, 8]],
        9: [[1, 2, 0], [4, 5, 3], [7, 8, 6]],
        10: [[1, 0, 3], [4, 2, 6], [7, 5, 8]],
        11: [[2, 8, 3], [1, 6, 4], [7, 0, 5]],
        12: [[5, 6, 7], [4, 0, 8], [3, 2, 1]],
        13: [[1, 6, 2], [5, 7, 3], [0, 4, 8]],
        14: [[2, 3, 6], [1, 5, 0], [4, 7, 8]],
        15: [[8, 6, 7], [2, 5, 4], [3, 0, 1]],
        16: [[4, 1, 3], [7, 2, 5], [0, 8, 6]],
        17: [[1, 3, 6], [4, 8, 2], [7, 0, 5]],
        18: [[4, 5, 6], [1, 2, 3], [7, 8, 0]],
        19: [[6, 4, 7], [8, 5, 0], [3, 2, 1]],
        20: [[1, 8, 2], [0, 4, 3], [7, 6, 5]] # Default case added to the map
    }
    
    # Ambil state berdasarkan pilihan, default ke 20 jika tidak ditemukan
    result = initial_states.get(choice, initial_states[20])

    # Logika untuk menghasilkan state acak yang terpecahkan jika 'choice' tidak ada
    if choice not in initial_states or choice == 0: # Gunakan 'choice == 0' untuk meminta random state
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
    """
    Menangani request SOLVE dan GENERATE dari frontend.
    """
    try:
        data = request.get_json()
        
        # --- Pengecekan Kualitas JSON (PENTING!) ---
        if data is None:
            return jsonify({
                "error": "Permintaan harus berisi JSON yang valid.",
                "details": "Pastikan Content-Type: application/json dan format body JSON sudah benar."
            }), 400
        
        # --- Melanjutkan logika ---
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
                    # frontEndPath berisi state tuple, ubah ke matriks list
                    step_copy["frontEndPath"] = [tupleToState(t) for t in step_copy["frontEndPath"]]
                
                # Hapus path (list panjang berisi state) agar payload tidak terlalu besar
                if "path" in step_copy:
                    del step_copy["path"]
                    
                final_content.append(step_copy)

            final_result = {
                "winState": result.get("winState", False),
                "content": final_content
            }
            
            return jsonify(final_result)
            
        # --- 2. AKSI GENERATE ---
        elif action == 'generate':
            choice_num = data.get('choiceNum', 20) # Default ke 20
            
            if not isinstance(choice_num, int):
                return jsonify({"error": "choiceNum harus berupa angka integer."}), 400
            
            new_state = getInitialState(choice_num)
            
            return jsonify({
                "initialState": new_state,
                "goalState": goalState # Opsional: kirim goal state juga
            })

        return jsonify({"error": "Aksi tidak dikenal. Gunakan 'solve' atau 'generate'."}), 400

    except Exception as e:
        # Mencetak error ke log Vercel untuk debugging
        print(f"FATAL ERROR: {str(e)}") 
        return jsonify({
            "error": "Internal Server Error saat memproses permintaan.",
            "details": str(e), 
            "hint": "Cek log Vercel Anda, pastikan format input [list[list[int]]] sudah benar."
        }), 500