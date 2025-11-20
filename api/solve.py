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
# FUNGSI INTI (KODE ASLI ANDA)
# =========================================================

# --- FUNGSI ASLI ANDA DIMULAI DI SINI ---

def convertFrontEndToMoves(bfsList) -> dict:
    prevMove = bfsList[0]["frontEndPath"][0]
    bfsList[0]["moves"] = [MoveEnum.NONE]

    for step in bfsList[1:]:
        moves = []
        
        for item in step["frontEndPath"]:
            move = beforeAfterToMove(prevMove, item)
            moves.append(move)
            prevMove = item

        step["moves"] = moves
    return bfsList
            
def beforeAfterToMove(before, after):
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
        if str(move["State"]) == str(after):
            return move["Move"]
        
    return MoveEnum.NONE
    
def convertToFrontEnd(bfsList) -> dict:
    frontEndList = []
    # 'now' dan looping print yang asli sudah dihapus karena ini API

    for index in range(1, len(bfsList)):
        
        possibleMoves = findMoves(bfsList[index - 1])
        
        # Perlu dikonversi ke format yang sama dengan `findMoves`
        possible_states = [move['state'] for move in possibleMoves] 
        
        if (bfsList[index]["state"] in possible_states): # Perbaikan: Cek state di list of states
            bfsList[index]["frontEndPath"] = [bfsList[index]["state"]]
        else:
            bfsList[index]["frontEndPath"] = backTrack(bfsList[index - 1], bfsList[index])

        frontEndList.append(bfsList[index])

    return frontEndList

def backTrack(start, end):
    listItem = [x for x in start["path"] if x in end["path"]]

    frontEndPath = []

    startPath = list(start["path"])
    endPath = list(end["path"])

    # Pastikan listItem tidak kosong sebelum mencari index
    if not listItem:
        # Jika tidak ada titik temu, mungkin ini langkah pertama atau ada masalah. 
        # Kita kembalikan saja end["state"] untuk menghindari error.
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
    explored = []
    steps = []

    frontier.append({"state": initialState, "heuristic": countHeuristic(initialState, goalState), "path": []})
    
    while len(frontier) > 0:
        currentState = frontier.pop(0)
        state = currentState["state"]
        
        # Cek kalau current state sudah pernah di cek sebelumnya
        if state in explored:
            continue
        explored.append(state)

        # Batasan jumlah langkah
        if (len(explored) >= 1000):
            break

        steps.append(currentState)
        
        # Cek apabila sudah mencapai goal
        if (currentState["state"] == goalState):
            break
        
        # Ambil semua kemungkinan yang bisa dilakukan pada current state
        # findMoves sekarang menerima dictionary (currentState)
        moves = findMoves(currentState) 

        pathList = []
            
        for i in currentState["path"]:
            pathList.append(i)

        pathList.append(currentState["state"])

        # Menambahkan move dan nilai heuristik yang dihitung ke antrian
        for move in moves:
            newMove = copy.deepcopy(move)
            # 'move' dari findMoves adalah state ([[]]), bukan dictionary, 
            # sehingga langsung bisa dipakai sebagai newMove (state)
            
            frontier.append({"state": newMove, "heuristic": countHeuristic(newMove, goalState), "path": pathList})

        # Disortir sehingga nilai berurut dari nilai heuristik terkecil
        frontier.sort(key=lambda x: x["heuristic"])

    winState = False

    if (currentState["state"] == goalState):
        winState = True
    else:
        winState = False

    frontEndConverted = convertToFrontEnd(steps)
    convertedMoves = convertFrontEndToMoves(frontEndConverted)

    return {"winState": winState, "content": convertedMoves}

def countHeuristic(currentState, goalState) -> int:
    heuristic = 0
    for num in range(1,9):
        currentFound = None
        for i in range(len(currentState)):
            for j in range(len(currentState[i])):
                if currentState[i][j] == num:
                    currentFound = (i, j)
                    break
            if currentFound:
                break

        goalFound = None
        for i in range(len(goalState)):
            for j in range(len(goalState[i])):
                if goalState[i][j] == num:
                    goalFound = (i, j)
                    break
            if goalFound:
                break

        # Manhattan Distance
        temp = abs(goalFound[0] - currentFound[0]) + abs(goalFound[1] - currentFound[1])
        heuristic += temp
        
    return heuristic
    
def findMoves(currentState) -> list[list[list[int]]]:
    # Hapus goalState di sini karena tidak digunakan, hanya sisa testing
    moves = []
    temp = copy.deepcopy(currentState["state"])

    foundZero = None
    # Logika mencari 0... (sama seperti kode asli Anda)
    for i in range(len(temp)):
        for j in range(len(temp[i])):
            if temp[i][j] == 0:
                foundZero = (i, j)
                break
        if foundZero:
            break
    
    # [x - 1] [y] (UP)
    item1 = foundZero[0] - 1
    if item1 >= 0:
        temp1 = copy.deepcopy(currentState["state"])
        store = temp1[foundZero[0]][foundZero[1]]
        temp1[foundZero[0]][foundZero[1]] = temp1[item1][foundZero[1]]
        temp1[item1][foundZero[1]] = store
        moves.append(temp1)

    # [x + 1] [y] (DOWN)
    item2 = foundZero[0] + 1
    if item2 <= 2:
        temp2 = copy.deepcopy(currentState["state"])
        store = temp2[foundZero[0]][foundZero[1]]
        temp2[foundZero[0]][foundZero[1]] = temp2[item2][foundZero[1]]
        temp2[item2][foundZero[1]] = store
        moves.append(temp2)

    # [x] [y - 1] (LEFT)
    item3 = foundZero[1] - 1
    if item3 >= 0:
        temp3 = copy.deepcopy(currentState["state"])
        store = temp3[foundZero[0]][foundZero[1]]
        temp3[foundZero[0]][foundZero[1]] = temp3[foundZero[0]][item3]
        temp3[foundZero[0]][item3] = store
        moves.append(temp3)

    # [x] [y + 1] (RIGHT)
    item4 = foundZero[1] + 1
    if item4 <= 2:
        temp4 = copy.deepcopy(currentState["state"])
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
        action = data.get('action') 
        
        goalState = [
            [ 1, 2, 3 ],
            [ 4, 5, 6 ],
            [ 7, 8, 0 ]
        ]
        
        # --- 1. AKSI SOLVE ---
        if action == 'solve':
            initial_state = data.get('initialState')
            
            if not initial_state:
                return jsonify({"error": "Initial state diperlukan untuk solving."}), 400

            # Panggil fungsi solver inti Anda
            result = BestFirstSearch(initial_state, goalState)
            
            # Konversi MoveEnum ke string ("LEFT", "RIGHT", dll.) sebelum dikirim
            for step in result["content"]:
                step["moves"] = [move.name for move in step["moves"]]
            
            return jsonify(result)
            
        # --- 2. AKSI GENERATE ---
        elif action == 'generate':
            choice_num = data.get('choiceNum', 7) 
            
            # Panggil fungsi generator inti Anda
            new_state = getInitialState(choice_num)
            
            return jsonify({
                "initialState": new_state
            })

        return jsonify({"error": "Aksi tidak dikenal. Gunakan 'solve' atau 'generate'."}), 400

    except Exception as e:
        # Menangani error umum
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

# Perhatikan: Blok 'if __name__ == "__main__": main()' yang asli sudah dihapus!
# Vercel akan menjalankan 'app' secara otomatis.