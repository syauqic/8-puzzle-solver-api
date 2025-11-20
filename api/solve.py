# =========================================================
# FILE: api/solve.py 
# SIAP UNTUK DEPLOY KE VERCEL SEBAGAI SERVERLESS FUNCTION
# =========================================================

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
    flat_list = [item for sublist in state_matrix for item in sublist]
    return tuple(flat_list)

def tupleToState(state_tuple: tuple) -> list[list[int]]:
    """Mengubah tuple 1D kembali menjadi matriks list 3x3."""
    return [
        list(state_tuple[0:3]),
        list(state_tuple[3:6]),
        list(state_tuple[6:9])
    ]

# =========================================================
# FUNGSI INTI (KODE ASLI ANDA)
# =========================================================

def convertFrontEndToMoves(bfsList) -> dict:
    prevMove = bfsList[0]["frontEndPath"][0]
    bfsList[0]["moves"] = [MoveEnum.NONE]

    for step in bfsList[1:]:
        moves = []
        
        for item in step["frontEndPath"]:
            # item di sini adalah tuple (state)
            move = beforeAfterToMove(prevMove, item)
            moves.append(move)
            prevMove = item

        step["moves"] = moves
    return bfsList
        
def beforeAfterToMove(before_tuple, after_tuple):
    # DARI TUPLE KE MATRIKS
    before = tupleToState(before_tuple)
    after = tupleToState(after_tuple)
    
    moves = []

    temp = copy.deepcopy(before)

    foundZero = None
    
    for i in range(len(temp)):
        for j in range(len(temp[i])):
            if temp[i][j] == 0:
                foundZero = (i, j)
                break
        
        if foundZero:
            break
    
    # [x - 1] [y]
    # Semua akses ke 'before' dan 'temp' sudah aman karena mereka adalah list/matriks
    item1 = foundZero[0] - 1
    if item1 >= 0:
        temp1 = copy.deepcopy(before)
        
        store = temp1[foundZero[0]][foundZero[1]]
        temp1[foundZero[0]][foundZero[1]] = temp1[item1][foundZero[1]]
        temp1[item1][foundZero[1]] = store

        moves.append({"Move": MoveEnum.UP, "State": temp1})

    # [x + 1] [y] 
    item2 = foundZero[0] + 1
    if item2 <= 2:
        temp2 = copy.deepcopy(before)
        
        store = temp2[foundZero[0]][foundZero[1]]
        temp2[foundZero[0]][foundZero[1]] = temp2[item2][foundZero[1]]
        temp2[item2][foundZero[1]] = store

        moves.append({"Move": MoveEnum.DOWN, "State": temp2})

    # [x] [y - 1]
    item3 = foundZero[1] - 1
    if item3 >= 0:
        temp3 = copy.deepcopy(before)
        
        store = temp3[foundZero[0]][foundZero[1]]
        temp3[foundZero[0]][foundZero[1]] = temp3[foundZero[0]][item3]
        temp3[foundZero[0]][item3] = store

        moves.append({"Move": MoveEnum.LEFT, "State": temp3})

    # [x] [y + 1]
    item4 = foundZero[1] + 1
    if item4 <= 2:
        temp4 = copy.deepcopy(before)
        
        store = temp4[foundZero[0]][foundZero[1]]
        temp4[foundZero[0]][foundZero[1]] = temp4[foundZero[0]][item4]
        temp4[foundZero[0]][item4] = store

        moves.append({"Move": MoveEnum.RIGHT, "State": temp4})
        

    for move in moves:
        # PENTING: Konversi State di move menjadi tuple untuk perbandingan yang aman
        if stateToTuple(move["State"]) == stateToTuple(after):
            return move["Move"]
        
    return MoveEnum.NONE
    
def convertToFrontEnd(bfsList) -> dict:
    frontEndList = []

    for index in range(1, len(bfsList)):
        
        # PENTING: Ubah state ke matriks list sebelum dikirim ke findMoves
        currentStateMatrix = tupleToState(bfsList[index - 1]["state"])
        possibleMoves = findMoves({"state": currentStateMatrix}) # findMoves menerima dict {"state": matrix}
        
        # Ambil state dari possibleMoves (masih dalam bentuk matriks list)
        possible_states_matrix = [move for move in possibleMoves] 
        
        # Konversi semua possible state matrix menjadi tuple untuk perbandingan
        possible_states_tuple = [stateToTuple(s) for s in possible_states_matrix]
        
        current_state_tuple = bfsList[index]["state"]

        if (current_state_tuple in possible_states_tuple): # Cek state tuple di list of state tuple
            bfsList[index]["frontEndPath"] = [current_state_tuple]
        else:
            bfsList[index]["frontEndPath"] = backTrack(bfsList[index - 1], bfsList[index])

        frontEndList.append(bfsList[index])

    return frontEndList

def backTrack(start, end):
    # start["path"] dan end["path"] berisi list of TUPLE state
    listItem = [x for x in start["path"] if x in end["path"]] # Perbandingan aman dengan tuple

    frontEndPath = []

    startPath = list(start["path"])
    endPath = list(end["path"])

    # Pastikan listItem tidak kosong sebelum mencari index
    if not listItem:
        return [end["state"]] 

    startIndex = startPath.index(listItem[len(listItem) - 1])
    endIndex = endPath.index(listItem[len(listItem) - 1])

    for i in range(len(startPath) - 1, startIndex - 1, -1):
        frontEndPath.append(startPath[i])
        
    for i in range(endIndex + 1, len(endPath), 1):
        frontEndPath.append(endPath[i])
        
    frontEndPath.append(end["state"])
    
    return frontEndPath
        
def BestFirstSearch(initialState, goalState) -> dict:
    frontier = []
    explored = [] # Sekarang akan menyimpan tuple
    steps = []

    # KONVERSI KE TUPLE SAAT AWAL
    initialStateTuple = stateToTuple(initialState)
    goalStateTuple = stateToTuple(goalState)
    
    # State yang disimpan di frontier, explored, steps, dan path adalah TUPLE
    frontier.append({"state": initialStateTuple, 
                     "heuristic": countHeuristic(initialState, goalState), 
                     "path": []})
    
    while len(frontier) > 0:
        currentState = frontier.pop(0)
        state_tuple = currentState["state"]
        
        # Cek kalau current state sudah pernah di cek sebelumnya (AMAN: perbandingan tuple)
        if state_tuple in explored:
            continue
        explored.append(state_tuple)

        # Batasan jumlah langkah
        if (len(explored) >= 10000): # Batas eksplorasi dinaikkan
             break

        steps.append(currentState)
        
        # Cek apabila sudah mencapai goal (AMAN: perbandingan tuple)
        if (state_tuple == goalStateTuple):
            break
        
        # Ambil state tuple, ubah ke matriks list, lalu kirim ke findMoves
        currentStateMatrix = tupleToState(state_tuple)
        moves = findMoves({"state": currentStateMatrix}) # findMoves sekarang bekerja dengan matriks list
        
        pathList = []
        for i in currentState["path"]:
            pathList.append(i)

        pathList.append(state_tuple) # state_tuple ditambahkan ke path
        
        # Menambahkan move dan nilai heuristik yang dihitung ke antrian
        for move_matrix in moves:
            # move_matrix adalah matriks list 3x3
            newMoveTuple = stateToTuple(move_matrix) # KONVERSI KE TUPLE
            
            # State yang masuk ke frontier adalah TUPLE
            frontier.append({"state": newMoveTuple, 
                             "heuristic": countHeuristic(move_matrix, goalState), # Hitung heuristik dari matriks
                             "path": pathList})

        # Disortir sehingga nilai berurut dari nilai heuristik terkecil
        frontier.sort(key=lambda x: x["heuristic"])

    winState = False

    if (currentState["state"] == goalStateTuple):
        winState = True
    else:
        winState = False

    frontEndConverted = convertToFrontEnd(steps)
    convertedMoves = convertFrontEndToMoves(frontEndConverted)

    # Output content sekarang berisi TUPLE, tapi Flask akan mengkonversinya ke list saat jsonify
    return {"winState": winState, "content": convertedMoves}

def countHeuristic(currentStateMatrix, goalStateMatrix) -> int:
    # Fungsi ini sekarang menerima MATRIKS LIST (tidak perlu konversi di awal)
    
    heuristic = 0
    for num in range(1,9):
        currentFound = None
        for i in range(len(currentStateMatrix)):
            for j in range(len(currentStateMatrix[i])):
                if currentStateMatrix[i][j] == num:
                    currentFound = (i, j)
                    break
            if currentFound:
                break

        goalFound = None
        for i in range(len(goalStateMatrix)):
            for j in range(len(goalStateMatrix[i])):
                if goalStateMatrix[i][j] == num:
                    goalFound = (i, j)
                    break
            if goalFound:
                break

        # Manhattan Distance (Akses tuple aman: [0] dan [1] adalah integer)
        temp = abs(goalFound[0] - currentFound[0]) + abs(goalFound[1] - currentFound[1])
        heuristic += temp
        
    return heuristic
    
def findMoves(currentStateDict) -> list[list[list[int]]]:
    # Menerima dictionary {"state": matrix}
    moves = []
    temp = copy.deepcopy(currentStateDict["state"]) # Ambil state matrix

    foundZero = None
    # Logika mencari 0...
    for i in range(len(temp)):
        for j in range(len(temp[i])):
            if temp[i][j] == 0:
                foundZero = (i, j)
                break
        if foundZero:
            break
    
    # [x - 1] [y] (UP)
    # Semua akses ke 'foundZero' menggunakan [0] dan [1] (integer) sudah benar
    item1 = foundZero[0] - 1
    if item1 >= 0:
        temp1 = copy.deepcopy(currentStateDict["state"])
        store = temp1[foundZero[0]][foundZero[1]]
        temp1[foundZero[0]][foundZero[1]] = temp1[item1][foundZero[1]]
        temp1[item1][foundZero[1]] = store
        moves.append(temp1)

    # [x + 1] [y] (DOWN)
    item2 = foundZero[0] + 1
    if item2 <= 2:
        temp2 = copy.deepcopy(currentStateDict["state"])
        store = temp2[foundZero[0]][foundZero[1]]
        temp2[foundZero[0]][foundZero[1]] = temp2[item2][foundZero[1]]
        temp2[item2][foundZero[1]] = store
        moves.append(temp2)

    # [x] [y - 1] (LEFT)
    item3 = foundZero[1] - 1
    if item3 >= 0:
        temp3 = copy.deepcopy(currentStateDict["state"])
        store = temp3[foundZero[0]][foundZero[1]]
        temp3[foundZero[0]][foundZero[1]] = temp3[foundZero[0]][item3]
        temp3[foundZero[0]][item3] = store
        moves.append(temp3)

    # [x] [y + 1] (RIGHT)
    item4 = foundZero[1] + 1
    if item4 <= 2:
        temp4 = copy.deepcopy(currentStateDict["state"])
        store = temp4[foundZero[0]][foundZero[1]]
        temp4[foundZero[0]][foundZero[1]] = temp4[foundZero[0]][item4]
        temp4[foundZero[0]][item4] = store
        moves.append(temp4)

    return moves

def getInitialState(choice) -> list[list[int]]:
    result = []
    
    # Pilihan state puzzle Anda
    match choice:
        case 1:
            result = [[1, 2, 3], [4, 5, 6], [7, 0, 8]]
        case 2:
            result = [[1, 2, 3], [4, 5, 6], [0, 7, 8]]
        case 3:
            result = [[1, 2, 3], [4, 0, 6], [7, 5, 8]]
        case 4:
            result = [[1, 3, 6], [4, 0, 2], [7, 5, 8]]
        case 5:
            result = [[1, 2, 3], [5, 0, 6], [4, 7, 8]]
        case 6:
            result = [[1, 2, 3], [4, 6, 0], [7, 5, 8]]
        case 7:
            result = [[1, 3, 6], [5, 0, 2], [4, 7, 8]]
        case 8:
            result = [[1, 3, 6], [5, 2, 0], [4, 7, 8]]
        case 9:
            result = [[1, 2, 0], [4, 5, 3], [7, 8, 6]]
        case 10:
            result = [[1, 0, 3], [4, 2, 6], [7, 5, 8]]
        # ... (Kasus 11-19 dan default tetap sama)
        case 11:
            result = [[2, 8, 3], [1, 6, 4], [7, 0, 5]]
        case 12:
            result = [[5, 6, 7], [4, 0, 8], [3, 2, 1]]
        case 13:
            result = [[1, 6, 2], [5, 7, 3], [0, 4, 8]]
        case 14:
            result = [[2, 3, 6], [1, 5, 0], [4, 7, 8]]
        case 15:
            result = [[8, 6, 7], [2, 5, 4], [3, 0, 1]]
        case 16:
            result = [[4, 1, 3], [7, 2, 5], [0, 8, 6]]
        case 17:
            result = [[1, 3, 6], [4, 8, 2], [7, 0, 5]]
        case 18:
            result = [[4, 5, 6], [1, 2, 3], [7, 8, 0]]
        case 19:
            result = [[6, 4, 7], [8, 5, 0], [3, 2, 1]]
        case _:
            result = [[1, 8, 2], [0, 4, 3], [7, 6, 5]]

    return result

# --- FUNGSI ASLI ANDA BERAKHIR DI SINI ---

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
                "details": "Pastikan Content-Type: application/json dan format body JSON sudah benar (semua key dikelilingi double quotes)."
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
                return jsonify({"error": "Format initialState tidak valid."}), 400

            # Panggil fungsi solver inti Anda
            result = BestFirstSearch(initial_state, goalState)
            
            # Konversi MoveEnum ke string ("LEFT", "RIGHT", dll.) sebelum dikirim
            for step in result["content"]:
                step["moves"] = [move.name for move in step["moves"]]
                
                # PENTING: Ubah kembali state tuple di output ke matriks list
                step["state"] = tupleToState(step["state"]) 
                
                # Ubah path tuple ke matriks list
                if "frontEndPath" in step:
                    step["frontEndPath"] = [tupleToState(t) for t in step["frontEndPath"]]


            # PENTING: Ubah kembali state tuple di output steps ke matriks list
            for step in result["content"]:
                step["state"] = tupleToState(step["state"])
            
            return jsonify(result)
            
        # --- 2. AKSI GENERATE ---
        elif action == 'generate':
            choice_num = data.get('choiceNum', 7) 
            
            if not isinstance(choice_num, int):
                return jsonify({"error": "choiceNum harus berupa angka integer."}), 400
            
            new_state = getInitialState(choice_num)
            
            return jsonify({
                "initialState": new_state
            })

        return jsonify({"error": "Aksi tidak dikenal. Gunakan 'solve' atau 'generate'."}), 400

    except Exception as e:
        print(f"FATAL ERROR: {str(e)}") # Mencetak error ke log Vercel untuk debugging
        return jsonify({
            "error": "Internal Server Error saat memproses permintaan.",
            "details": str(e), 
            "hint": "Cek log Vercel Anda, error ini sering disebabkan oleh list/tuple yang diakses dengan indeks string."
        }), 500

# Perhatikan: Blok 'if __name__ == "__main__": main()' yang asli sudah dihapus!
# Vercel akan menjalankan 'app' secara otomatis.