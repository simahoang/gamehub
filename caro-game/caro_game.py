import socket
import json
import os
from flask import request
from flask_socketio import emit, join_room, leave_room

# socketio instance được inject từ hub qua register()
socketio = None

# --- TRẠNG THÁI GAME ---
BOARD_SIZE = 20 # BẠN CÓ THỂ ĐỔI THÀNH SỐ BẤT KỲ (15, 20, 25...)
VERSION = "v2.3.1"
COUNTDOWN_SECONDS = 8

# --- CONFIG ---
# Bật (True) để cho phép cùng 1 IP cầm cả X và O (dùng khi self-test).
# Tắt (False) để chặn trùng IP như bình thường.
ALLOW_SAME_IP = False

def create_empty_board():
    return [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Mở sẵn 3 phòng cố định (Thêm trường win_cells để lưu chuỗi ô chiến thắng)
rooms = {
    'Phòng 1': {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_over': False, 'countdown_seconds': 0, 'chat_history': []},
    'Phòng 2': {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_over': False, 'countdown_seconds': 0, 'chat_history': []},
    'Phòng 3': {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_over': False, 'countdown_seconds': 0, 'chat_history': []},
}       
user_rooms = {}

# --- TỰ ĐỘNG NHẬN DIỆN TÊN NGƯỜI CHƠI QUA IP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAYERS_FILE = os.path.join(BASE_DIR, 'players.json')

def load_player_names():
    if not os.path.exists(PLAYERS_FILE):
        return {}
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def resolve_player_name(ip):
    names = load_player_names()
    entry = names.get(ip)
    if isinstance(entry, dict):
        return entry.get('name', f"Guest_{ip}")
    if isinstance(entry, str):
        return entry
    return f"Guest_{ip}"

# --- HTML & GIAO DIỆN WEB ---
HTML_PAGE = f"""
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cờ Caro LAN - Đa Phòng</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; background: #f0f0f0; margin: 0; padding: 20px; }}
        h1 {{ color: #333; margin-bottom: 5px; }}
        #info {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; color: #555; }}
        #role {{ font-size: 16px; color: #888; margin-bottom: 20px; }}
        
        /* Giao diện sảnh chờ */
        #lobby-wrapper {{ display: flex; justify-content: center; margin-top: 50px; }}
        .lobby-box {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 300px; }}
        .lobby-box h3 {{ margin-top: 0; color: #444; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
        
        #game {{ display: none; }} /* Ẩn game lúc mới vào */

        /* Bàn cờ */
        #board {{
            display: grid;
            grid-template-columns: repeat({BOARD_SIZE}, 30px);
            gap: 0;
            background: transparent;
            width: fit-content;
            margin: 0 auto;
            border: 2px solid #000;
        }}
        .cell {{
            width: 30px; height: 30px;
            background: #EEDD82;
            border: 1px solid #000;
            box-sizing: border-box;
            display: flex; justify-content: center; align-items: center;
            font-size: 24px; font-weight: bold;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}
        .cell:hover {{ background: #dfc85a; }}
        .X {{ color: red; }}
        .O {{ color: blue; }}
        
        /* HIỆU ỨNG TÔ ĐẬM Ô VỪA ĐÁNH (XANH LÁ) */
        .last-move {{
            background: #7bed9f !important; /* Xanh lá */
            box-shadow: inset 0 0 8px rgba(0,0,0,0.4);
        }}

        /* HIỆU ỨNG TÔ ĐẬM ĐƯỜNG CHIẾN THẮNG (VÀNG ĐẬM) */
        .win-cell {{
            background: #f1c40f !important; /* Vàng */
            box-shadow: inset 0 0 12px rgba(0,0,0,0.6);
            color: #fff; 
        }}

        /* HIỆU ỨNG IN ĐẬM ĐƯỜNG NGUY HIỂM */
        .threat-cell {{ font-weight: 900 !important; }}
        
        /* Nút bấm */
        button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; border-radius: 5px; border: none; background: #007bff; color: white; transition: 0.2s; }}
        button:hover {{ background: #0056b3; }}
        
        .btn-room {{ background: #28a745; margin-top: 10px; font-weight: bold; width: 100%; }}
        .btn-room:hover {{ background: #218838; }}
        
        .btn-gray {{ background: #6c757d; }}
        .btn-gray:hover {{ background: #5a6268; }}
        
        .game-controls {{ display: flex; justify-content: center; gap: 10px; max-width: 400px; margin: 20px auto 0 auto; }}
        
        #version {{ position: fixed; bottom: 10px; right: 15px; font-size: 12px; color: #999; z-index: 100; }}
        
        #player-list {{
            position: fixed;
            top: 100px;
            right: 20px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            min-width: 180px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: left;
            z-index: 99;
        }}
        #player-list h4 {{ margin-top: 0; color: #444; border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        .player-item {{ padding: 4px 0; font-size: 14px; }}
        .player-item .piece-x {{ color: red; font-weight: bold; }}
        .player-item .piece-o {{ color: blue; font-weight: bold; }}
        .player-item .piece-spec {{ color: #999; }}
    #chat-box {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 250px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            z-index: 100;
            display: none;
        }}
        #chat-messages {{
            height: 200px;
            overflow-y: auto;
            padding: 10px;
            font-size: 13px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        #chat-messages .chat-msg {{
            margin-bottom: 5px;
            word-break: break-word;
        }}
        #chat-messages .chat-name {{
            font-weight: bold;
            color: #007bff;
        }}
        #chat-input-area {{
            display: flex;
            padding: 5px;
        }}
        #chat-input {{
            flex: 1;
            padding: 6px;
            font-size: 13px;
            border: 1px solid #ddd;
            border-radius: 4px;
            outline: none;
        }}
        #chat-input-area button {{
            padding: 6px 10px;
            font-size: 12px;
            margin-left: 5px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <h1>Cờ Caro Mạng LAN</h1>

    <!-- MÀN HÌNH CHỌN PHÒNG -->
    <div id="lobby-wrapper">
        <div class="lobby-box">
            <h3>🏠 Danh sách phòng</h3>
            <p style="font-size: 14px; color: #666;">Bấm vào để vào chơi ngay</p>
            <button class="btn-room" onclick="joinSpecificRoom('Phòng 1')">🚪 Phòng 1</button>
            <button class="btn-room" onclick="joinSpecificRoom('Phòng 2')">🚪 Phòng 2</button>
            <button class="btn-room" onclick="joinSpecificRoom('Phòng 3')">🚪 Phòng 3</button>
        </div>
    </div>

    <!-- MÀN HÌNH CHƠI GAME -->
    <div id="game">
        <h2 id="roomTitle" style="color: #d9534f; margin-top: 0;"></h2>
        <div id="info">Đang kết nối...</div>
        <div id="role"></div>
        <div id="board-wrapper" style="overflow: auto; max-width: 100%;">
            <div id="board"></div>
        </div>
        <div class="game-controls">
            <button id="surrender-btn" onclick="surrender()" style="display: none;">🏳️ Đầu Hàng</button>
            <button class="btn-gray" onclick="leaveRoom()">🚪 Rời Phòng</button>
            <button id="threat-toggle" onclick="toggleThreat()">⚠️ Cảnh báo: BẬT</button>
        </div>
    </div>

    <div id="chat-box">
        <div id="chat-messages"></div>
        <div id="chat-input-area">
            <input type="text" id="chat-input" placeholder="Nhập tin nhắn..." maxlength="200" onkeydown="if(event.key==='Enter') sendChat()">
            <button onclick="sendChat()">Gửi</button>
        </div>
    </div>

    <div id="player-list" style="display: none;">
        <h4>👥 Người chơi</h4>
        <div id="player-list-content"></div>
    </div>

    <script>
        const socket = io();
        let myPiece = '';
        let myName = '';
        let isMyTurn = false;
        let currentRoom = '';
        let threatEnabled = true;
        let lastBoardState = null;
        
        const size = {BOARD_SIZE}; 

        // Khởi tạo lưới bàn cờ
        const boardDiv = document.getElementById('board');
        for (let r = 0; r < size; r++) {{
            for (let c = 0; c < size; c++) {{
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.id = `cell-${{r}}-${{c}}`;
                cell.onclick = () => makeMove(r, c);
                boardDiv.appendChild(cell);
            }}
        }}

        function joinSpecificRoom(roomName) {{
            currentRoom = roomName;
            socket.emit('join', {{ room: roomName }});
            
            document.getElementById('lobby-wrapper').style.display = 'none';
            document.getElementById('game').style.display = 'block';
            document.getElementById('player-list').style.display = 'block';
            document.getElementById('roomTitle').innerText = "Đang chơi tại: " + roomName;
            document.getElementById('chat-box').style.display = 'block';
        }}

        function leaveRoom() {{
            location.reload(); 
        }}

        socket.on('init', (data) => {{
            myPiece = data.piece;
            myName = data.player_name || 'Unknown';
            const surBtn = document.getElementById('surrender-btn');
            if (myPiece === 'X' || myPiece === 'O') {{
                surBtn.style.display = 'inline-block';
            }} else {{
                surBtn.style.display = 'none';
            }}
            if (myPiece === 'X' || myPiece === 'O') {{
                document.getElementById('role').innerText = `Xin chào ${{myName}}! Bạn cầm quân: ${{myPiece}}`;
            }} else {{
                document.getElementById('role').innerText = `Xin chào ${{myName}}! Phòng đã đầy! Bạn đang xem dưới tư cách Khán Giả.`;
            }}
            const chatContainer = document.getElementById('chat-messages');
            chatContainer.innerHTML = '';
            if (data.chat_history) {{
                data.chat_history.forEach(m => {{
                    const div = document.createElement('div');
                    div.className = 'chat-msg';
                    div.innerHTML = '<span class="chat-name">' + m.name + ':</span> ' + m.message;
                    chatContainer.appendChild(div);
                }});
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }}
            updateBoard(data.board, data.last_move, data.win_cells, data.threat_cells);
            if (data.game_over && data.countdown_seconds > 0) {{
                document.getElementById('info').innerText = 'Ván mới sau ' + data.countdown_seconds + 's...';
                document.getElementById('info').style.color = '#e67e22';
                isMyTurn = false;
            }} else {{
                updateTurn(data.turn);
            }}
        }});

        socket.on('update', (data) => {{
            updateBoard(data.board, data.last_move, null, data.threat_cells);
            updateTurn(data.turn);
        }});

        socket.on('game_over', (data) => {{
            updateBoard(data.board, data.last_move, data.win_cells, data.threat_cells);
            let msg;
            if (data.surrender) {{
                msg = data.winner_name + ' đã đầu hàng — ' + data.winner + ' THẮNG!';
            }} else {{
                msg = data.winner + ' ĐÃ CHIẾN THẮNG!';
            }}
            document.getElementById('info').innerText = msg;
            document.getElementById('info').style.color = "green";
            isMyTurn = false;
        }});

        socket.on('countdown', (data) => {{
            const info = document.getElementById('info');
            if (data.seconds > 0) {{
                info.innerText = 'Ván mới sau ' + data.seconds + 's...';
                info.style.color = '#e67e22';
            }}
        }});

        socket.on('player_list', (data) => {{
            const container = document.getElementById('player-list-content');
            container.innerHTML = '';
            data.players.forEach(p => {{
                const div = document.createElement('div');
                div.className = 'player-item';
                let pieceLabel = '';
                if (p.piece === 'X') pieceLabel = ' <span class="piece-x">[X]</span>';
                else if (p.piece === 'O') pieceLabel = ' <span class="piece-o">[O]</span>';
                else pieceLabel = ' <span class="piece-spec">[Khán giả]</span>';
                div.innerHTML = p.name + pieceLabel;
                container.appendChild(div);
            }});
        }});

        function makeMove(r, c) {{
            if (!isMyTurn || myPiece === '') return;
            const cell = document.getElementById(`cell-${{r}}-${{c}}`);
            if (cell.innerText === '') {{
                socket.emit('move', {{ room: currentRoom, row: r, col: c }});
            }}
        }}

        // Hàm này giờ nhận thêm mảng tọa độ winCells và threatCells
        function updateBoard(boardData, lastMove, winCells, threatCells) {{
            lastBoardState = {{ board: boardData, lastMove: lastMove, winCells: winCells, threatCells: threatCells }};
            for (let r = 0; r < size; r++) {{
                for (let c = 0; c < size; c++) {{
                    const cell = document.getElementById(`cell-${{r}}-${{c}}`);
                    cell.innerText = boardData[r][c];
                    
                    let className = 'cell ' + boardData[r][c];
                    
                    // Kiểm tra ô vừa đánh
                    if (lastMove && lastMove.r === r && lastMove.c === c) {{
                        className += ' last-move';
                    }}
                    
                    // Kiểm tra nếu ô này nằm trong chuỗi quân thắng
                    if (winCells && winCells.some(pt => pt[0] === r && pt[1] === c)) {{
                        className += ' win-cell';
                    }}

                    // Kiểm tra nếu ô này nằm trong threat cells
                    if (threatEnabled && threatCells && threatCells.some(pt => pt[0] === r && pt[1] === c)) {{
                        className += ' threat-cell';
                    }}
                    
                    cell.className = className;
                }}
            }}
        }}

        function updateTurn(turn) {{
            document.getElementById('info').style.color = "#555";
            if (myPiece === '' || (myPiece !== 'X' && myPiece !== 'O')) {{
                document.getElementById('info').innerText = `Đang xem: Lượt của ${{turn}}`;
                isMyTurn = false;
            }} else if (turn === myPiece) {{
                document.getElementById('info').innerText = "Đến lượt của bạn!";
                isMyTurn = true;
            }} else {{
                document.getElementById('info').innerText = "Chờ đối thủ đánh...";
                isMyTurn = false;
            }}
        }}

        function toggleThreat() {{
            threatEnabled = !threatEnabled;
            const btn = document.getElementById('threat-toggle');
            btn.innerText = threatEnabled ? '⚠️ Cảnh báo: BẬT' : '⚠️ Cảnh báo: TẮT';
            btn.className = threatEnabled ? '' : 'btn-gray';
            if (lastBoardState) {{
                updateBoard(lastBoardState.board, lastBoardState.lastMove, lastBoardState.winCells, lastBoardState.threatCells);
            }}
        }}

function sendChat() {{
            const input = document.getElementById('chat-input');
            const msg = input.value.trim();
            if (!msg) return;
            socket.emit('chat', {{ room: currentRoom, message: msg }});
            input.value = '';
        }}

        function surrender() {{
            if (confirm("Bạn chắc chắn muốn đầu hàng?")) {{
                socket.emit('surrender', {{ room: currentRoom }});
            }}
        }}

        socket.on('chat', (data) => {{
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'chat-msg';
            div.innerHTML = '<span class="chat-name">' + data.name + ':</span> ' + data.message;
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            while (container.children.length > 50) {{
                container.removeChild(container.firstChild);
            }}
        }});

        </script>

    <div id="version">{VERSION}</div>
</body>
</html>
"""

def check_win(board, row, col, piece):
    opponent = 'O' if piece == 'X' else 'X'
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        # Lưu các ô chiến thắng vào mảng
        winning_cells = [(row, col)]
        
        # Đi theo một chiều
        r, c = row + dr, col + dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
            winning_cells.append((r, c))
            r += dr; c += dc
        forward_r, forward_c = r, c
            
        # Đi theo chiều ngược lại
        r, c = row - dr, col - dc
        while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
            winning_cells.append((r, c))
            r -= dr; c -= dc
        backward_r, backward_c = r, c
            
        if len(winning_cells) == 5:
            opponent_blocks = 0
            if 0 <= forward_r < BOARD_SIZE and 0 <= forward_c < BOARD_SIZE and board[forward_r][forward_c] == opponent:
                opponent_blocks += 1
            if 0 <= backward_r < BOARD_SIZE and 0 <= backward_c < BOARD_SIZE and board[backward_r][backward_c] == opponent:
                opponent_blocks += 1
            if opponent_blocks < 2:
                return winning_cells # Trả về mảng tọa độ thay vì True
            
    return None

def check_threat_pattern(board, row, col, dr, dc, piece):
    opponent = 'O' if piece == 'X' else 'X'
    cells = [(row, col)]

    # Scan forward từ vị trí bắt đầu
    r, c = row + dr, col + dc
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
        cells.append((r, c))
        r += dr; c += dc
    forward_end_r, forward_end_c = r, c
    forward_open = (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == '')
    forward_open2 = (0 <= r + dr < BOARD_SIZE and 0 <= c + dc < BOARD_SIZE
                     and board[r + dr][c + dc] == '') if forward_open else False

    # Scan backward từ vị trí bắt đầu
    r, c = row - dr, col - dc
    while 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == piece:
        cells.append((r, c))
        r -= dr; c -= dc
    backward_end_r, backward_end_c = r, c
    backward_open = (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == '')
    backward_open2 = (0 <= r - dr < BOARD_SIZE and 0 <= c - dc < BOARD_SIZE
                      and board[r - dr][c - dc] == '') if backward_open else False

    count = len(cells)
    result = []

    # Pattern 1: Simple Four – 4 quân liên tiếp, đúng 1 đầu hở
    if count == 4 and (forward_open != backward_open):
        # Kiểm tra gap+piece: nếu đầu hở có quân cùng màu cách 2 ô → lấp gap → 6+ quân → overline
        skip = False
        if backward_open:
            pr, pc = backward_end_r - dr, backward_end_c - dc
            if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == piece:
                skip = True
        if forward_open and not skip:
            pr, pc = forward_end_r + dr, forward_end_c + dc
            if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == piece:
                skip = True
        # Kiểm tra đối thủ chặn 2 đầu: nếu đầu bị chặn là quân đối thủ
        # và ô beyond (cách 2 vị trí theo hướng hở) cũng là quân đối thủ
        # → lấp đầu hở tạo chuỗi 5 bị chặn 2 đầu → không thắng → skip
        if not skip:
            if backward_open and not forward_open:
                if (0 <= forward_end_r < BOARD_SIZE and 0 <= forward_end_c < BOARD_SIZE
                        and board[forward_end_r][forward_end_c] == opponent):
                    br, bc = backward_end_r - dr, backward_end_c - dc
                    if 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE and board[br][bc] == opponent:
                        skip = True
            elif forward_open and not backward_open:
                if (0 <= backward_end_r < BOARD_SIZE and 0 <= backward_end_c < BOARD_SIZE
                        and board[backward_end_r][backward_end_c] == opponent):
                    br, bc = forward_end_r + dr, forward_end_c + dc
                    if 0 <= br < BOARD_SIZE and 0 <= bc < BOARD_SIZE and board[br][bc] == opponent:
                        skip = True
        if not skip:
            result.extend(cells)

    # Pattern 2: Open Four – 4 quân liên tiếp, cả 2 đầu hở
    if count == 4 and forward_open and backward_open:
        # Kiểm tra gap+piece: nếu CẢ 2 đầu đều có gap+piece → overline → bỏ qua
        # Nếu chỉ 1 đầu có → đầu kia vẫn sạch → vẫn là threat
        back_over = False
        forward_over = False
        pr, pc = backward_end_r - dr, backward_end_c - dc
        if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == piece:
            back_over = True
        pr, pc = forward_end_r + dr, forward_end_c + dc
        if 0 <= pr < BOARD_SIZE and 0 <= pc < BOARD_SIZE and board[pr][pc] == piece:
            forward_over = True
        if not (back_over and forward_over):
            result.extend(cells)

    # Pattern 4: Open Three – 3 quân liên tiếp, cả 2 đầu hở, ít nhất 1 phía có ≥2 ô trống
    if count == 3 and forward_open and backward_open and (backward_open2 and forward_open2):
        result.extend(cells)

    # Pattern 3 & 5: Gap detection phía forward
    if forward_open:
        gap_r, gap_c = forward_end_r + dr, forward_end_c + dc
        if 0 <= gap_r < BOARD_SIZE and 0 <= gap_c < BOARD_SIZE and board[gap_r][gap_c] == piece:
            gap_cells = []
            gr, gc = gap_r, gap_c
            while 0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == piece:
                gap_cells.append((gr, gc))
                gr += dr; gc += dc
            total = count + len(gap_cells)
            gap_end_open = (0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == '')

            all_cells = cells + gap_cells

            # Pattern 3: Broken Four – total >= 4, 1 gap, ít nhất 1 đầu hở
            if total == 4 and (backward_open or gap_end_open):
                result.extend(all_cells)

            # Pattern 5: Broken Three – total == 3, 1 gap, cả 2 đầu hở, ít nhất 1 phía có ≥2 ô trống
            gap_end_open2 = (0 <= gr + dr < BOARD_SIZE and 0 <= gc + dc < BOARD_SIZE
                             and board[gr + dr][gc + dc] == '') if gap_end_open else False
            if total == 3 and backward_open and gap_end_open and (backward_open2 and gap_end_open2):
                result.extend(all_cells)

    # Pattern 3 & 5: Gap detection phía backward
    if backward_open:
        gap_r, gap_c = backward_end_r - dr, backward_end_c - dc
        if 0 <= gap_r < BOARD_SIZE and 0 <= gap_c < BOARD_SIZE and board[gap_r][gap_c] == piece:
            gap_cells = []
            gr, gc = gap_r, gap_c
            while 0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == piece:
                gap_cells.append((gr, gc))
                gr -= dr; gc -= dc
            total = count + len(gap_cells)
            gap_end_open = (0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == '')

            all_cells = cells + gap_cells

            # Pattern 3: Broken Four – total >= 4, 1 gap, ít nhất 1 đầu hở
            if total == 4 and (forward_open or gap_end_open):
                result.extend(all_cells)

            # Pattern 5: Broken Three – total == 3, 1 gap, cả 2 đầu hở, ít nhất 1 phía có ≥2 ô trống
            gap_end_open2 = (0 <= gr - dr < BOARD_SIZE and 0 <= gc - dc < BOARD_SIZE
                             and board[gr - dr][gc - dc] == '') if gap_end_open else False
            if total == 3 and forward_open and gap_end_open and (forward_open2 and gap_end_open2):
                result.extend(all_cells)

    return result

def detect_threats(board):
    threat_cells = set()
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]

    for piece in ('X', 'O'):
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] != piece:
                    continue
                for dr, dc in directions:
                    cells = check_threat_pattern(board, r, c, dr, dc, piece)
                    if cells:
                        threat_cells.update(cells)

    return threat_cells

def countdown_worker(room_id):
    global socketio
    if socketio is None or room_id not in rooms:
        return
    r_data = rooms[room_id]
    for sec in range(5, -1, -1):
        r_data['countdown_seconds'] = sec
        socketio.emit('countdown', {'seconds': sec}, to=room_id)
        if sec > 0:
            socketio.sleep(1)
    
    # Auto reset
    r_data['board'] = create_empty_board()
    r_data['turn'] = 'X'
    r_data['last_move'] = None
    r_data['win_cells'] = None
    r_data['threat_cells'] = []
    r_data['game_over'] = False
    r_data['countdown_seconds'] = 0
    
    socketio.emit('update', {
        'board': r_data['board'],
        'turn': 'X',
        'last_move': None,
        'win_cells': None,
        'threat_cells': []
    }, to=room_id)

def handle_join(data):
    room_id = data['room']
    join_room(room_id)
    user_rooms[request.sid] = room_id

    if room_id not in rooms:
        rooms[room_id] = {
            'board': create_empty_board(),
            'players': {},
            'turn': 'X',
            'last_move': None,
            'win_cells': None,
            'threat_cells': [],
            'game_over': False,
            'countdown_seconds': 0,
            'chat_history': [],
        }

    r_data = rooms[room_id]
    
    client_ip = request.remote_addr
    player_name = resolve_player_name(client_ip)

    ip_has_slot = any(p.get('ip') == client_ip and p['piece'] in ('X', 'O') for p in r_data['players'].values())

    piece = ''
    if not ip_has_slot or ALLOW_SAME_IP:
        if 'X' not in [p['piece'] for p in r_data['players'].values()]:
            piece = 'X'
        elif 'O' not in [p['piece'] for p in r_data['players'].values()]:
            piece = 'O'

    r_data['players'][request.sid] = {'piece': piece, 'name': player_name, 'ip': client_ip}

    # Compute threats for init: opponent of the new player's piece
    if piece in ('X', 'O'):
        threat_cells = detect_threats(r_data['board'])
        r_data['threat_cells'] = list(threat_cells) if threat_cells else []
    else:
        # Spectator: show threats from both players
        threat_cells = detect_threats(r_data['board'])
        r_data['threat_cells'] = list(threat_cells) if threat_cells else []

    emit('init', {
        'board': r_data['board'], 
        'turn': r_data['turn'], 
        'piece': piece,
        'player_name': player_name,
        'last_move': r_data['last_move'],
        'win_cells': r_data['win_cells'],
        'threat_cells': r_data['threat_cells'],
        'game_over': r_data.get('game_over', False),
        'countdown_seconds': r_data.get('countdown_seconds', 0),
        'chat_history': r_data.get('chat_history', [])
    }, to=request.sid)

    player_list = [{'name': p['name'], 'piece': p['piece']} for p in r_data['players'].values()]
    emit('player_list', {'players': player_list}, to=room_id)

def handle_disconnect():
    if request.sid in user_rooms:
        room_id = user_rooms[request.sid]
        if room_id in rooms and request.sid in rooms[room_id]['players']:
            piece = rooms[room_id]['players'][request.sid]['piece']
            del rooms[room_id]['players'][request.sid]

            if piece == rooms[room_id]['turn']:
                r_data = rooms[room_id]
                active = [p['piece'] for p in r_data['players'].values() if p['piece'] in ('X', 'O')]

                if active:
                    r_data['turn'] = 'O' if piece == 'X' else 'X'
                    # Compute threats from both players
                    threat_cells = detect_threats(r_data['board'])
                    r_data['threat_cells'] = list(threat_cells) if threat_cells else []
                else:
                    r_data['board'] = create_empty_board()
                    r_data['turn'] = 'X'
                    r_data['last_move'] = None
                    r_data['win_cells'] = None
                    r_data['threat_cells'] = []
                    r_data['game_over'] = False
                    r_data['countdown_seconds'] = 0
                    r_data['chat_history'] = []

                emit('update', {
                    'board': r_data['board'],
                    'turn': r_data['turn'],
                    'last_move': r_data['last_move'],
                    'threat_cells': r_data['threat_cells']
                }, to=room_id)

            player_list = [{'name': p['name'], 'piece': p['piece']} for p in rooms[room_id]['players'].values()]
            emit('player_list', {'players': player_list}, to=room_id)

        del user_rooms[request.sid]

def handle_move(data):
    room_id = data['room']
    if room_id not in rooms: return
    
    r_data = rooms[room_id]
    if request.sid not in r_data['players']: return 
    
    piece = r_data['players'][request.sid]['piece']
    if piece != r_data['turn']: return 
    
    row, col = data['row'], data['col']
    if r_data['board'][row][col] == '':
        r_data['board'][row][col] = piece
        r_data['last_move'] = {'r': row, 'c': col}
        
        # Kiểm tra thắng, lấy mảng ô win
        win_cells = check_win(r_data['board'], row, col, piece)
        
        if win_cells:
            r_data['win_cells'] = win_cells
            r_data['threat_cells'] = []
            r_data['game_over'] = True
            r_data['countdown_seconds'] = COUNTDOWN_SECONDS
            emit('game_over', {
                'board': r_data['board'], 
                'winner': piece,
                'last_move': r_data['last_move'],
                'win_cells': r_data['win_cells'],
                'threat_cells': []
            }, to=room_id)
            socketio.start_background_task(countdown_worker, room_id)
            return
            
        r_data['turn'] = 'O' if piece == 'X' else 'X'
        # Compute threats from both players
        threat_cells = detect_threats(r_data['board'])
        r_data['threat_cells'] = list(threat_cells) if threat_cells else []
        emit('update', {
            'board': r_data['board'], 
            'turn': r_data['turn'],
            'last_move': r_data['last_move'],
            'threat_cells': r_data['threat_cells']
        }, to=room_id)

def handle_chat(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']:
        return
    player_name = r_data['players'][request.sid]['name']
    message = data.get('message', '').strip()
    if not message:
        return
    emit('chat', {'name': player_name, 'message': message}, to=room_id)

    if 'chat_history' not in r_data:
        r_data['chat_history'] = []
    r_data['chat_history'].append({'name': player_name, 'message': message})
    if len(r_data['chat_history']) > 50:
        r_data['chat_history'] = r_data['chat_history'][-50:]

def handle_surrender(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']:
        return
    piece = r_data['players'][request.sid]['piece']
    if piece not in ('X', 'O'):
        return
    winner = 'O' if piece == 'X' else 'X'
    winner_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == winner), winner)
    r_data['win_cells'] = None
    r_data['threat_cells'] = []
    r_data['game_over'] = True
    r_data['countdown_seconds'] = COUNTDOWN_SECONDS
    emit('game_over', {
        'board': r_data['board'],
        'winner': winner,
        'winner_name': winner_name,
        'surrender': True,
        'last_move': r_data['last_move'],
        'win_cells': None,
        'threat_cells': []
    }, to=room_id)
    socketio.start_background_task(countdown_worker, room_id)

def handle_reset(data):
    room_id = data.get('room')
    if room_id in rooms:
        rooms[room_id]['board'] = create_empty_board()
        rooms[room_id]['turn'] = 'X'
        rooms[room_id]['last_move'] = None 
        rooms[room_id]['win_cells'] = None # Xóa trạng thái bàn thắng
        rooms[room_id]['threat_cells'] = []
        emit('update', {
            'board': rooms[room_id]['board'], 
            'turn': 'X',
            'last_move': None,
            'win_cells': None,
            'threat_cells': []
        }, to=room_id)

def caro_index():
    return HTML_PAGE

def register(app, socketio_instance):
    global socketio
    socketio = socketio_instance
    app.add_url_rule('/caro', 'caro_index', caro_index, methods=['GET'])
    socketio_instance.on_event('join', handle_join)
    socketio_instance.on_event('disconnect', handle_disconnect)
    socketio_instance.on_event('move', handle_move)
    socketio_instance.on_event('chat', handle_chat)
    socketio_instance.on_event('surrender', handle_surrender)
    socketio_instance.on_event('reset', handle_reset)