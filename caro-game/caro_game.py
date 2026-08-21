import socket
import json
import os
import time
from flask import request
from flask_socketio import emit, join_room, leave_room

# socketio instance được inject từ hub qua register()
socketio = None

# --- TRẠNG THÁI GAME ---
BOARD_SIZE = 20 # BẠN CÓ THỂ ĐỔI THÀNH SỐ BẤT KỲ (15, 20, 25...)
VERSION = "v3.1.10"
COUNTDOWN_SECONDS = 8
IDLE_SECONDS = 180
IDLE_CHECK_INTERVAL = 10
TURN_SECONDS = 40

# --- CONFIG ---
# Bật (True) để cho phép cùng 1 IP cầm cả X và O (dùng khi self-test).
# Tắt (False) để chặn trùng IP như bình thường.
ALLOW_SAME_IP = False

def create_empty_board():
    return [['' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

# Mở sẵn 6 phòng cố định với thời gian mỗi nước khác nhau (turn_seconds)
rooms = {
    'Tiêu chuẩn 1':  {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 45, 'move_history': []},
    'Tiêu chuẩn 2': {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 45, 'move_history': []},
    'Tiêu chuẩn 3':   {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 45, 'move_history': []},
    'Siêu nhanh':  {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 15, 'move_history': []},
    'Không suy nghĩ':  {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 5, 'move_history': []},
    'Siêu chậm':  {'board': create_empty_board(), 'players': {}, 'turn': 'X', 'last_move': None, 'win_cells': None, 'threat_cells': [], 'game_active': False, 'game_over': False, 'countdown_seconds': 0, 'chat_history': [], 'turn_deadline': None, 'turn_seconds': 180, 'move_history': []},
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
<html lang="vi" data-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Cờ Caro LAN - Đa Phòng</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <!-- Tailwind CSS + DaisyUI CDN -->
    <!-- Nếu máy LAN không có Internet, host local: tải tailwindcss và daisyui về thư mục static/ -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.10/dist/full.min.css" rel="stylesheet" type="text/css" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
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
            background: oklch(var(--wa) / 0.3);
            border: 1px solid #000;
            box-sizing: border-box;
            display: flex; justify-content: center; align-items: center;
            font-size: 24px; font-weight: bold;
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
        }}
        .cell:hover {{ background: oklch(var(--wa) / 0.5); }}
        .X {{ color: #e74c3c !important; }}
        .O {{ color: #3498db !important; }}
        .last-move {{
            background: oklch(var(--su) / 0.4) !important;
            box-shadow: inset 0 0 8px rgba(0,0,0,0.4);
        }}
        .win-cell {{
            background: oklch(var(--wa)) !important;
            color: oklch(var(--wac));
            font-weight: 900;
            box-shadow: inset 0 0 12px rgba(0,0,0,0.6);
        }}
        .threat-cell {{ font-weight: 900 !important; }}
        .chat-msg {{
            margin-bottom: 6px;
            padding: 6px 10px;
            background: oklch(var(--b2));
            border-radius: 8px;
            word-break: break-word;
        }}
        .chat-name {{
            font-weight: bold;
            color: oklch(var(--p));
        }}
        .player-item {{ padding: 4px 0; font-size: 14px; }}
        .piece-x {{ color: oklch(var(--er)); font-weight: bold; }}
        .piece-o {{ color: oklch(var(--p)); font-weight: bold; }}
        .piece-spec {{ color: oklch(var(--bc) / 0.5); }}
        #version {{ color: oklch(var(--bc) / 0.3); }}
        @keyframes timer-urgent {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(1.1); }}
        }}
        .timer-urgent {{
            animation: timer-urgent 0.6s ease-in-out infinite;
            color: #e74c3c !important;
            font-size: 1.3em !important;
            font-weight: 900 !important;
        }}
    </style>
</head>
<body class="bg-base-200 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- MÀN HÌNH CHỌN PHÒNG -->
        <div id="lobby-wrapper">
            <div class="card bg-base-100 shadow-xl p-8 max-w-md mx-auto">
                <h3 class="text-2xl font-bold mb-2">🏠 Danh sách phòng</h3>
                <p class="text-sm text-base-content/60 mb-4">Bấm vào để vào chơi ngay</p>
                <div id="room-list"></div>
            </div>
        </div>

        <!-- MÀN HÌNH CHƠI GAME -->
        <div id="game" style="display: none;">
            <div class="max-w-4xl mx-auto">
                <h2 id="roomTitle" class="text-2xl font-bold text-error mb-1"></h2>
                <div id="info" class="text-lg font-semibold text-base-content mb-2">Đang kết nối...</div>
                <div id="result" class="text-xl font-bold text-success mb-2"></div>
                <div id="turn-timer" class="text-lg text-warning mb-2"></div>
                <div id="role" class="text-base text-base-content/70 mb-4"></div>

                <div id="seat-panel" class="card bg-base-100 shadow p-4 mb-4">
                    <div style="display: flex; flex-direction: row; justify-content: center; align-items: center; gap: 12px; flex-wrap: wrap;">
                        <span class="badge badge-error font-bold">X</span>
                        <span id="seat-x-name">Trống</span>
                        <button id="sit-x-btn" onclick="sit('X')" style="display:none;" class="btn btn-sm">Ngồi X</button>
                        <span class="badge badge-primary font-bold">O</span>
                        <span id="seat-o-name">Trống</span>
                        <button id="sit-o-btn" onclick="sit('O')" style="display:none;" class="btn btn-sm">Ngồi O</button>
                        <button id="stand-btn" onclick="stand()" style="display:none;" class="btn btn-sm btn-ghost">Đứng lên</button>
</div>
                </div>

                <div class="flex justify-center items-center gap-4 my-2 text-base-content/30">
                    <div class="h-px flex-1 bg-base-300"></div>
                    <span class="text-2xl">🪑🪑</span>
                    <div class="h-px flex-1 bg-base-300"></div>
                </div>

                <div id="board-wrapper" style="overflow: auto; max-width: 100%;" class="card bg-base-100 shadow-xl p-4 mb-4">
                    <div id="board"></div>
                </div>

                <div class="flex justify-center gap-3 mt-4">
                    <button id="undo-btn" onclick="requestUndo()" disabled class="btn btn-warning btn-sm">↩ Undo</button>
                    <button id="surrender-btn" onclick="surrender()" style="display: none;" class="btn btn-error">🏳️ Đầu Hàng</button>
                    <button onclick="leaveRoom()" class="btn btn-ghost">🚪 Rời Phòng</button>
</div>

            <div id="undo-modal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 hidden">
                <div class="card bg-base-100 shadow-xl p-6 max-w-sm">
                    <h3 class="text-lg font-bold mb-4">Yêu cầu Undo</h3>
                    <p id="undo-modal-msg" class="mb-4"></p>
                    <div class="flex justify-end gap-3">
                        <button onclick="document.getElementById('undo-modal').classList.add('hidden')" class="btn btn-ghost btn-sm">Từ chối</button>
                        <button id="undo-accept-btn" class="btn btn-primary btn-sm">Đồng ý</button>
                    </div>
                </div>
            </div>
        </div>
        </div>
    </div>

    <div id="chat-box" class="card bg-base-100 shadow fixed bottom-4 right-4 w-72 z-50" style="display: none;">
        <div id="chat-messages" class="h-48 overflow-y-auto p-3 text-sm border-b border-base-300"></div>
        <div id="chat-input-area" class="flex p-2 gap-2">
            <input type="text" id="chat-input" placeholder="Nhập tin nhắn..." maxlength="200" onkeydown="if(event.key==='Enter') sendChat()" class="input input-bordered input-sm flex-1">
            <button onclick="sendChat()" class="btn btn-primary btn-sm">Gửi</button>
        </div>
    </div>

    <div id="player-list" class="card bg-base-100 shadow fixed top-24 right-4 w-48 z-40 p-4" style="display: none;">
        <h4 class="font-bold text-base-content mb-2 pb-2 border-b border-base-300">👥 Người chơi</h4>
        <div id="player-list-content"></div>
    </div>

    <div id="version" class="text-xs fixed bottom-2 right-4 z-50">{VERSION}</div>

    <script>
        const socket = io();
        let myPiece = '';
        let myName = '';
        let isMyTurn = false;
        let gameActive = false;
        let currentTurn = 'X';
        let currentRoom = '';
        let lastBoardState = null;
        let turnTimerSeconds = 0;
        let roomTurnSeconds = 40;

        function escapeHtml(str) {{
            return (str || '').replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;');
        }}
        
        socket.on('connect', () => {{ socket.emit('get_rooms', {{}}); }});
        socket.on('room_list', (data) => {{ renderRoomList(data.rooms); }});
        
        const size = {BOARD_SIZE}; 

        // Khởi tạo lưới bàn cờ
        const cells = [];
        const boardDiv = document.getElementById('board');
        for (let r = 0; r < size; r++) {{
            cells[r] = [];
            for (let c = 0; c < size; c++) {{
                const cell = document.createElement('div');
                cell.className = 'cell';
                cell.id = `cell-${{r}}-${{c}}`;
                cell.onclick = () => makeMove(r, c);
                boardDiv.appendChild(cell);
                cells[r][c] = cell;
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

        function renderRoomList(rooms) {{
            const list = document.getElementById('room-list');
            list.innerHTML = '';
            (rooms || []).forEach(r => {{
                let label, badgeClass;
                if (r.seated === 0) {{ label = 'Trống'; badgeClass = 'badge-success'; }}
                else if (r.seated === 1) {{ label = 'Đang đợi'; badgeClass = 'badge-warning'; }}
                else {{ label = 'Đầy'; badgeClass = 'badge-error'; }}
                const ts = r.turn_seconds || 40;
                let icon = '🕐';
                if (ts <= 15) icon = '⚡';
                else if (ts <= 30) icon = '🔥';
                else if (ts >= 120) icon = '🐢';

                const card = document.createElement('div');
                card.className = 'card bg-base-200 shadow-sm p-4 mb-3';

                const header = document.createElement('div');
                header.className = 'flex items-center justify-between mb-2';
                const nameSpan = document.createElement('span');
                nameSpan.className = 'font-bold text-lg';
                nameSpan.innerText = r.room;
                const badge = document.createElement('span');
                badge.className = 'badge ' + badgeClass;
                badge.innerText = label;
                header.appendChild(nameSpan);
                header.appendChild(badge);

                const timeDiv = document.createElement('div');
                timeDiv.className = 'text-sm text-base-content/70 mb-3';
                timeDiv.innerText = '(' + ts + 's ' + icon + ')';

                const btn = document.createElement('button');
                btn.className = 'btn btn-primary btn-block btn-sm';
                btn.innerText = 'Vào phòng';
                btn.onclick = () => joinSpecificRoom(r.room);

                card.appendChild(header);
                card.appendChild(timeDiv);
                card.appendChild(btn);
                list.appendChild(card);
            }});
        }}

        socket.on('init', (data) => {{
            resetTurnTimer();
            document.getElementById('result').innerText = '';
            myPiece = data.piece;
            gameActive = !!data.game_active;
            myName = data.player_name || 'Unknown';
            currentTurn = data.turn;
            updateRole();
            document.getElementById('undo-btn').disabled = true;
            roomTurnSeconds = data.turn_seconds || 40;
            const ts = roomTurnSeconds;
            document.getElementById('roomTitle').innerText = 'Đang chơi tại: ' + currentRoom + ' (' + ts + 's/nước)';
            const chatContainer = document.getElementById('chat-messages');
            chatContainer.innerHTML = '';
            if (data.chat_history) {{
                data.chat_history.forEach(m => {{
                    const div = document.createElement('div');
                    div.className = 'chat-msg';
                    div.innerHTML = '<span class="chat-name">' + escapeHtml(m.name) + ':</span> ' + escapeHtml(m.message);
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
            if (data.game_active !== undefined) gameActive = !!data.game_active;
            resetTurnTimer();
            document.getElementById('result').innerText = '';
            updateBoard(data.board, data.last_move, null, data.threat_cells);
            updateTurn(data.turn);
        }});

        socket.on('game_over', (data) => {{
            if (data.game_active !== undefined) gameActive = !!data.game_active;
            resetTurnTimer();
            updateBoard(data.board, data.last_move, data.win_cells, data.threat_cells);
            let msg;
            if (data.timeout) {{
                msg = data.timeout_name + ' hết giờ — ' + data.winner_name + ' (' + data.winner + ') THẮNG!';
            }} else if (data.surrender) {{
                msg = data.surrenderer_name + ' đã đầu hàng — ' + data.winner_name + ' (' + data.winner + ') THẮNG!';
            }} else {{
                msg = data.winner_name + ' (' + data.winner + ') THẮNG!';
            }}
            const result = document.getElementById('result');
            result.innerText = msg;
            result.style.color = "green";
            isMyTurn = false;
        }});

        socket.on('countdown', (data) => {{
            resetTurnTimer();
            const info = document.getElementById('info');
            if (data.seconds > 0) {{
                info.innerText = 'Ván mới sau ' + data.seconds + 's...';
                info.style.color = '#e67e22';
            }}
        }});

        socket.on('turn_timer', (data) => {{
            const t = document.getElementById('turn-timer');
            if (data.seconds > 0) {{
                turnTimerSeconds = data.seconds;
                t.style.display = 'inline-block';
                t.innerText = '⏱ còn ' + data.seconds + 's';
                const urgent = data.seconds <= Math.min(10, roomTurnSeconds * 0.25);
                if (urgent) {{
                    t.classList.add('timer-urgent');
                }} else {{
                    t.classList.remove('timer-urgent');
                }}
            }} else {{
                resetTurnTimer();
            }}
        }});

        socket.on('notice', (data) => {{
            const info = document.getElementById('info');
            info.innerText = data.message;
            info.style.color = '#e67e22';
        }});

        socket.on('player_list', (data) => {{
            if (data.game_active !== undefined) gameActive = !!data.game_active;
            const players = data.players;
            const me = players.find(p => p.sid === socket.id);
            if (me) {{
                myPiece = me.piece;
                myName = me.name;
            }}
            const container = document.getElementById('player-list-content');
            container.innerHTML = '';
            players.forEach(p => {{
                const div = document.createElement('div');
                div.className = 'player-item';
                let pieceLabel = '';
                if (p.piece === 'X') pieceLabel = ' <span class="piece-x">[X]</span>';
                else if (p.piece === 'O') pieceLabel = ' <span class="piece-o">[O]</span>';
                else pieceLabel = ' <span class="piece-spec">[Khán giả]</span>';
                div.innerHTML = escapeHtml(p.name) + pieceLabel;
                container.appendChild(div);
            }});
            updateSeatPanel(players);
            updateRole();
            updateTurn(currentTurn);
        }});

        function resetTurnTimer() {{
            turnTimerSeconds = 0;
            const t = document.getElementById('turn-timer');
            t.innerText = '';
            t.classList.remove('timer-urgent');
            t.style.display = 'none';
        }}

        function updateRole() {{
            const surBtn = document.getElementById('surrender-btn');
            if (myPiece === 'X' || myPiece === 'O') {{
                document.getElementById('role').innerText = `Bạn cầm quân: ${{myPiece}}`;
                surBtn.style.display = 'inline-block';
            }} else {{
                document.getElementById('role').innerText = 'Bạn đang đứng (khán giả) — bấm Ngồi để chơi';
                surBtn.style.display = 'none';
            }}
        }}

        function updateSeatPanel(players) {{
            const seatX = players.find(p => p.piece === 'X');
            const seatO = players.find(p => p.piece === 'O');
            document.getElementById('seat-x-name').innerText = seatX ? seatX.name : 'Trống';
            document.getElementById('seat-o-name').innerText = seatO ? seatO.name : 'Trống';
            const locked = (gameActive === true);
            document.getElementById('sit-x-btn').style.display = (!locked && !seatX && myPiece === '') ? 'inline-block' : 'none';
            document.getElementById('sit-o-btn').style.display = (!locked && !seatO && myPiece === '') ? 'inline-block' : 'none';
            document.getElementById('stand-btn').style.display = (!locked && (myPiece === 'X' || myPiece === 'O')) ? 'inline-block' : 'none';
        }}

        function sit(piece) {{
            socket.emit('sit', {{ room: currentRoom, piece: piece }});
        }}

        function stand() {{
            socket.emit('stand', {{ room: currentRoom }});
        }}

        function makeMove(r, c) {{
            if (!isMyTurn || myPiece === '') return;
            const cell = document.getElementById(`cell-${{r}}-${{c}}`);
            if (cell.innerText === '') {{
                socket.emit('move', {{ room: currentRoom, row: r, col: c }});
            }}
        }}

        function updateBoard(boardData, lastMove, winCells, threatCells) {{
            const prevThreat = lastBoardState ? (lastBoardState.threatCells || []) : [];
            const prevWin = lastBoardState ? (lastBoardState.winCells || []) : [];
            const prevLastMove = lastBoardState ? lastBoardState.lastMove : null;
            lastBoardState = {{ board: boardData, lastMove: lastMove, winCells: winCells, threatCells: threatCells }};

            // Cập nhật innerText + className cho các ô thay đổi (so với DOM hiện tại)
            for (let r = 0; r < size; r++) {{
                for (let c = 0; c < size; c++) {{
                    const newVal = boardData[r][c];
                    const cell = cells[r][c];
                    if (cell.innerText !== newVal) {{
                        cell.innerText = newVal;
                        cell.className = 'cell ' + newVal;
                    }}
                }}
            }}

            // Xoá last-move ở ô cũ (nếu có)
            if (prevLastMove && (!lastMove || prevLastMove.r !== lastMove.r || prevLastMove.c !== lastMove.c)) {{
                const cell = cells[prevLastMove.r][prevLastMove.c];
                if (cell) cell.classList.remove('last-move');
            }}

            // Thêm last-move ở ô mới (nếu có)
            if (lastMove) {{
                const cell = cells[lastMove.r][lastMove.c];
                if (cell) cell.classList.add('last-move');
            }}

            // Cập nhật threat cells: thêm class mới, xoá class cũ
            const threatSet = new Set((threatCells || []).map(pt => pt[0] + ',' + pt[1]));
            const prevThreatSet = new Set(prevThreat.map(pt => pt[0] + ',' + pt[1]));
            (threatCells || []).forEach(pt => {{
                if (!prevThreatSet.has(pt[0] + ',' + pt[1])) {{
                    const cell = cells[pt[0]][pt[1]];
                    if (cell && !cell.classList.contains('threat-cell')) cell.classList.add('threat-cell');
                }}
            }});
            prevThreat.forEach(pt => {{
                if (!threatSet.has(pt[0] + ',' + pt[1])) {{
                    const cell = cells[pt[0]][pt[1]];
                    if (cell) cell.classList.remove('threat-cell');
                }}
            }});

            // Cập nhật win cells
            const winSet = new Set((winCells || []).map(pt => pt[0] + ',' + pt[1]));
            const prevWinSet = new Set(prevWin.map(pt => pt[0] + ',' + pt[1]));
            (winCells || []).forEach(pt => {{
                if (!prevWinSet.has(pt[0] + ',' + pt[1])) {{
                    const cell = cells[pt[0]][pt[1]];
                    if (cell) cell.classList.add('win-cell');
                }}
            }});
            prevWin.forEach(pt => {{
                if (!winSet.has(pt[0] + ',' + pt[1])) {{
                    const cell = cells[pt[0]][pt[1]];
                    if (cell) cell.classList.remove('win-cell');
                }}
            }});
        }}

        function updateTurn(turn) {{
            currentTurn = turn;
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
            const undoBtn = document.getElementById('undo-btn');
            if (undoBtn) {{
                const canUndo = gameActive && myPiece && myPiece !== currentTurn && myPiece !== '';
                undoBtn.disabled = !canUndo;
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

        function requestUndo() {{
            socket.emit('undo_request', {{ room: currentRoom }});
        }}

        socket.on('undo_request', (data) => {{
            // Chỉ hiện popup nếu mình không phải người gửi và mình có piece X/O
            if (data.from_sid === socket.id) return;
            if (myPiece !== 'X' && myPiece !== 'O') return;
            
            // Dùng modal HTML thay vì confirm() để tránh bị browser chặn
            const modal = document.getElementById('undo-modal');
            document.getElementById('undo-modal-msg').innerText = data.from + ' (' + data.from_piece + ') xin đi lại nước vừa đánh. Đồng ý?';
            document.getElementById('undo-accept-btn').onclick = function() {{
                socket.emit('undo_accept', {{ room: currentRoom }});
                modal.classList.add('hidden');
            }};
            modal.classList.remove('hidden');
        }});

        socket.on('chat', (data) => {{
            const container = document.getElementById('chat-messages');
            const div = document.createElement('div');
            div.className = 'chat-msg';
            div.innerHTML = '<span class="chat-name">' + escapeHtml(data.name) + ':</span> ' + escapeHtml(data.message);
            container.appendChild(div);
            container.scrollTop = container.scrollHeight;
            while (container.children.length > 50) {{
                container.removeChild(container.firstChild);
            }}
        }});

        </script>
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

            # Pattern 3: Broken Four – total == 4, 1 gap, lấp gap → 5 (thắng nếu <2 đầu bị đối thủ chặn)
            if total == 4:
                opp_blocks = 0
                if 0 <= backward_end_r < BOARD_SIZE and 0 <= backward_end_c < BOARD_SIZE and board[backward_end_r][backward_end_c] == opponent:
                    opp_blocks += 1
                if 0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == opponent:
                    opp_blocks += 1
                if opp_blocks < 2:
                    result.extend(all_cells)

            # Pattern 5: Broken Three – total == 3, 1 gap, 2 đầu hở (lấp gap → Open Four → thắng chắc)
            # Điều kiện: ô beyond đầu hở không được là quân đối thủ (nếu có → mở rộng hướng đó tạo chuỗi bị chặn 2 đầu)
            if total == 3 and backward_open and gap_end_open:
                # Check ô beyond backward_end: nếu là opponent → hướng này là ngõ cụt
                beyond_r = backward_end_r - dr
                beyond_c = backward_end_c - dc
                backward_blocked = (0 <= beyond_r < BOARD_SIZE and 0 <= beyond_c < BOARD_SIZE 
                                    and board[beyond_r][beyond_c] == opponent)
                # Check ô beyond gap_end: nếu là opponent → hướng này là ngõ cụt
                beyond_gr = gr + dr
                beyond_gc = gc + dc
                forward_blocked = (0 <= beyond_gr < BOARD_SIZE and 0 <= beyond_gc < BOARD_SIZE 
                                   and board[beyond_gr][beyond_gc] == opponent)
                if not backward_blocked and not forward_blocked:
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

            # Pattern 3: Broken Four – total == 4, 1 gap, lấp gap → 5 (thắng nếu <2 đầu bị đối thủ chặn)
            if total == 4:
                opp_blocks = 0
                if 0 <= forward_end_r < BOARD_SIZE and 0 <= forward_end_c < BOARD_SIZE and board[forward_end_r][forward_end_c] == opponent:
                    opp_blocks += 1
                if 0 <= gr < BOARD_SIZE and 0 <= gc < BOARD_SIZE and board[gr][gc] == opponent:
                    opp_blocks += 1
                if opp_blocks < 2:
                    result.extend(all_cells)

            # Pattern 5: Broken Three – total == 3, 1 gap, 2 đầu hở (lấp gap → Open Four → thắng chắc)
            # Điều kiện: ô beyond đầu hở không được là quân đối thủ (nếu có → mở rộng hướng đó tạo chuỗi bị chặn 2 đầu)
            if total == 3 and forward_open and gap_end_open:
                # Check ô beyond forward_end: nếu là opponent → hướng này là ngõ cụt
                beyond_r = forward_end_r + dr
                beyond_c = forward_end_c + dc
                forward_blocked = (0 <= beyond_r < BOARD_SIZE and 0 <= beyond_c < BOARD_SIZE 
                                   and board[beyond_r][beyond_c] == opponent)
                # Check ô beyond gap_end: nếu là opponent → hướng này là ngõ cụt
                beyond_gr = gr - dr
                beyond_gc = gc - dc
                backward_blocked = (0 <= beyond_gr < BOARD_SIZE and 0 <= beyond_gc < BOARD_SIZE 
                                    and board[beyond_gr][beyond_gc] == opponent)
                if not backward_blocked and not forward_blocked:
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
    for sec in range(COUNTDOWN_SECONDS, -1, -1):
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
    r_data['game_active'] = False
    r_data['countdown_seconds'] = 0
    r_data['move_history'] = []
    
    socketio.emit('update', {
        'board': r_data['board'],
        'turn': 'X',
        'last_move': None,
        'win_cells': None,
        'threat_cells': [],
        'game_active': False
    }, to=room_id)

def idle_sweeper_worker():
    global socketio
    while True:
        socketio.sleep(IDLE_CHECK_INTERVAL)
        now = time.time()
        for room_id, r_data in rooms.items():
            if r_data.get('game_active') or r_data.get('game_over'):
                continue
            for sid in list(r_data['players'].keys()):
                p = r_data['players'][sid]
                if p.get('piece') in ('X', 'O') and now - p.get('last_active', now) > IDLE_SECONDS:
                    name = p.get('name', '')
                    p['piece'] = ''
                    player_list = [{'sid': s, 'name': pl['name'], 'piece': pl['piece']} for s, pl in r_data['players'].items()]
                    socketio.emit('player_list', {'players': player_list, 'game_active': r_data.get('game_active', False)}, to=room_id)
                    socketio.emit('notice', {'message': name + ' đã tự động đứng lên do không hoạt động'}, to=room_id)
                    broadcast_room_list()

def start_turn_clock(room_id):
    global socketio
    if socketio is None or room_id not in rooms:
        return
    r_data = rooms[room_id]
    turn_seconds = r_data.get('turn_seconds', TURN_SECONDS)
    r_data['turn_deadline'] = time.time() + turn_seconds
    socketio.start_background_task(turn_clock_worker, room_id, r_data['turn'])

def turn_clock_worker(room_id, piece):
    global socketio
    if socketio is None or room_id not in rooms: return
    r_data = rooms[room_id]
    while True:
        if not r_data.get('game_active') or r_data.get('game_over') or r_data['turn'] != piece:
            return
        deadline = r_data.get('turn_deadline')
        remaining = int(deadline - time.time()) if deadline else 0
        if remaining <= 0:
            # hết giờ -> người đang tới lượt (piece) thua, đối thủ thắng
            winner = 'O' if piece == 'X' else 'X'
            winner_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == winner), winner)
            loser_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == piece), piece)
            r_data['win_cells'] = None
            r_data['threat_cells'] = []
            r_data['game_over'] = True
            r_data['game_active'] = False
            r_data['countdown_seconds'] = COUNTDOWN_SECONDS
            socketio.emit('game_over', {
                'board': r_data['board'], 'winner': winner, 'winner_name': winner_name,
                'surrender': False, 'timeout': True, 'timeout_name': loser_name,
                'last_move': r_data['last_move'], 'win_cells': None, 'threat_cells': [], 'game_active': False
            }, to=room_id)
            socketio.start_background_task(countdown_worker, room_id)
            return
        socketio.emit('turn_timer', {'seconds': remaining}, to=room_id)
        socketio.sleep(1)

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
            'game_active': False,
            'game_over': False,
            'countdown_seconds': 0,
            'chat_history': [],
            'turn_deadline': None,
            'turn_seconds': TURN_SECONDS,
            'move_history': [],
        }

    r_data = rooms[room_id]
    
    client_ip = request.remote_addr
    player_name = resolve_player_name(client_ip)

    piece = ''

    r_data['players'][request.sid] = {'piece': piece, 'name': player_name, 'ip': client_ip, 'last_active': time.time()}

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
        'game_active': r_data.get('game_active', False),
        'countdown_seconds': r_data.get('countdown_seconds', 0),
        'chat_history': r_data.get('chat_history', []),
        'turn_seconds': r_data.get('turn_seconds', TURN_SECONDS)
    }, to=request.sid)

    player_list = [{'sid': sid, 'name': p['name'], 'piece': p['piece']} for sid, p in r_data['players'].items()]
    emit('player_list', {'players': player_list, 'game_active': r_data.get('game_active', False)}, to=room_id)

def handle_sit(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']:
        return
    player = r_data['players'][request.sid]
    piece = data.get('piece')
    if piece not in ('X', 'O'):
        return
    if r_data.get('game_active'):
        return
    if player['piece'] != '':
        return
    # Kiểm tra IP này đã ngồi ở phòng KHÁC chưa (trên toàn bộ rooms)
    if not ALLOW_SAME_IP:
        for other_room_id, other_r_data in rooms.items():
            if other_room_id == room_id:
                continue
            for other_sid, other_p in other_r_data['players'].items():
                if other_p.get('ip') == player.get('ip') and other_p['piece'] in ('X', 'O'):
                    return
    for sid, p in r_data['players'].items():
        if sid == request.sid:
            continue
        if p['piece'] == piece:
            return
        if not ALLOW_SAME_IP and p.get('ip') == player.get('ip') and p['piece'] in ('X', 'O'):
            return
    player['last_active'] = time.time()
    player['piece'] = piece
    player_list = [{'sid': sid, 'name': p['name'], 'piece': p['piece']} for sid, p in r_data['players'].items()]
    emit('player_list', {'players': player_list, 'game_active': r_data.get('game_active', False)}, to=room_id)
    broadcast_room_list()

def handle_stand(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']:
        return
    player = r_data['players'][request.sid]
    if r_data.get('game_active'):
        return
    if player['piece'] not in ('X', 'O'):
        return
    player['last_active'] = time.time()
    player['piece'] = ''
    player_list = [{'sid': sid, 'name': p['name'], 'piece': p['piece']} for sid, p in r_data['players'].items()]
    emit('player_list', {'players': player_list, 'game_active': r_data.get('game_active', False)}, to=room_id)
    broadcast_room_list()

def handle_disconnect():
    if request.sid in user_rooms:
        room_id = user_rooms[request.sid]
        if room_id in rooms and request.sid in rooms[room_id]['players']:
            r_data = rooms[room_id]
            piece = r_data['players'][request.sid]['piece']
            del r_data['players'][request.sid]

            if not r_data['players']:
                r_data['chat_history'] = []
                r_data['board'] = create_empty_board()
                r_data['turn'] = 'X'
                r_data['last_move'] = None
                r_data['win_cells'] = None
                r_data['threat_cells'] = []
                r_data['game_over'] = False
                r_data['game_active'] = False
                r_data['countdown_seconds'] = 0
                r_data['move_history'] = []

            if r_data.get('game_active') and piece in ('X', 'O'):
                r_data['board'] = create_empty_board()
                r_data['turn'] = 'X'
                r_data['last_move'] = None
                r_data['win_cells'] = None
                r_data['threat_cells'] = []
                r_data['game_over'] = False
                r_data['game_active'] = False
                r_data['countdown_seconds'] = 0
                r_data['move_history'] = []
                emit('update', {
                    'board': r_data['board'],
                    'turn': r_data['turn'],
                    'last_move': r_data['last_move'],
                    'win_cells': None,
                    'threat_cells': [],
                    'game_active': False
                }, to=room_id)

            player_list = [{'sid': sid, 'name': p['name'], 'piece': p['piece']} for sid, p in r_data['players'].items()]
            emit('player_list', {'players': player_list, 'game_active': r_data.get('game_active', False)}, to=room_id)
            broadcast_room_list()

        del user_rooms[request.sid]

def handle_move(data):
    room_id = data['room']
    if room_id not in rooms: return
    
    r_data = rooms[room_id]
    if request.sid not in r_data['players']: return 
    if r_data.get('game_over'): return 
    
    piece = r_data['players'][request.sid]['piece']
    if piece != r_data['turn']: return 
    
    seated = [p['piece'] for p in r_data['players'].values() if p['piece'] in ('X', 'O')]
    if 'X' not in seated or 'O' not in seated: return 
    
    r_data['players'][request.sid]['last_active'] = time.time()
    row, col = data['row'], data['col']
    # Validate row/col
    if not (isinstance(row, int) and isinstance(col, int)):
        return
    if not (0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE):
        return
    if r_data['board'][row][col] == '':
        r_data['board'][row][col] = piece
        r_data['last_move'] = {'r': row, 'c': col}
        if 'move_history' not in r_data:
            r_data['move_history'] = []
        r_data['move_history'].append({'row': row, 'col': col, 'piece': piece})
        if not r_data.get('game_active'):
            r_data['game_active'] = True
        
        # Kiểm tra thắng, lấy mảng ô win
        win_cells = check_win(r_data['board'], row, col, piece)
        
        if win_cells:
            r_data['win_cells'] = win_cells
            r_data['threat_cells'] = []
            r_data['game_over'] = True
            r_data['game_active'] = False
            r_data['countdown_seconds'] = COUNTDOWN_SECONDS
            winner_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == piece), piece)
            emit('game_over', {
                'board': r_data['board'], 
                'winner': piece,
                'winner_name': winner_name,
                'last_move': r_data['last_move'],
                'win_cells': r_data['win_cells'],
                'threat_cells': [],
                'game_active': False
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
            'threat_cells': r_data['threat_cells'],
            'game_active': r_data.get('game_active', False)
        }, to=room_id)
        start_turn_clock(room_id)

def handle_undo_request(data):
    room_id = data.get('room')
    if room_id not in rooms: return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']: return
    if not r_data.get('game_active') or r_data.get('game_over'): return
    if not r_data.get('move_history'): return

    piece = r_data['players'][request.sid]['piece']
    if piece not in ('X', 'O'): return
    if piece == r_data['turn']: return

    requester_name = r_data['players'][request.sid]['name']
    # Emit đến toàn bộ phòng, frontend sẽ lọc
    socketio.emit('undo_request', {
        'from': requester_name,
        'from_piece': piece,
        'from_sid': request.sid
    }, to=room_id)

def handle_undo_accept(data):
    room_id = data.get('room')
    if room_id not in rooms: return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']: return
    if not r_data.get('game_active') or r_data.get('game_over'): return
    if not r_data.get('move_history'): return

    piece = r_data['players'][request.sid]['piece']
    if piece not in ('X', 'O'): return

    last = r_data['move_history'].pop()
    r_data['board'][last['row']][last['col']] = ''
    r_data['turn'] = last['piece']
    r_data['last_move'] = None
    threat_cells = detect_threats(r_data['board'])
    r_data['threat_cells'] = list(threat_cells) if threat_cells else []
    socketio.emit('update', {
        'board': r_data['board'],
        'turn': r_data['turn'],
        'last_move': None,
        'threat_cells': r_data['threat_cells'],
        'game_active': True
    }, to=room_id)
    start_turn_clock(room_id)

def handle_chat(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    r_data = rooms[room_id]
    if request.sid not in r_data['players']:
        return
    player_name = r_data['players'][request.sid]['name']
    message = data.get('message', '').strip()
    message = message[:200]
    if not message:
        return
    if time.time() - r_data['players'][request.sid].get('last_chat_time', 0) < 1.0:
        return
    r_data['players'][request.sid]['last_chat_time'] = time.time()
    r_data['players'][request.sid]['last_active'] = time.time()
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
    if r_data.get('game_over'):
        return
    piece = r_data['players'][request.sid]['piece']
    if piece not in ('X', 'O'):
        return
    surrenderer_name = r_data['players'][request.sid]['name']
    winner = 'O' if piece == 'X' else 'X'
    winner_name = next((p['name'] for p in r_data['players'].values() if p['piece'] == winner), winner)
    r_data['win_cells'] = None
    r_data['threat_cells'] = []
    r_data['game_over'] = True
    r_data['game_active'] = False
    r_data['countdown_seconds'] = COUNTDOWN_SECONDS
    emit('game_over', {
        'board': r_data['board'],
        'winner': winner,
        'winner_name': winner_name,
        'surrenderer_name': surrenderer_name,
        'surrender': True,
        'last_move': r_data['last_move'],
        'win_cells': None,
        'threat_cells': [],
        'game_active': False
    }, to=room_id)
    socketio.start_background_task(countdown_worker, room_id)

def handle_reset(data):
    room_id = data.get('room')
    if room_id not in rooms:
        return
    if request.sid not in rooms[room_id]['players']:
        return
    if not rooms[room_id].get('game_over'):
        return
    rooms[room_id]['board'] = create_empty_board()
    rooms[room_id]['turn'] = 'X'
    rooms[room_id]['last_move'] = None 
    rooms[room_id]['win_cells'] = None # Xóa trạng thái bàn thắng
    rooms[room_id]['threat_cells'] = []
    rooms[room_id]['game_over'] = False
    rooms[room_id]['game_active'] = False
    emit('update', {
        'board': rooms[room_id]['board'], 
        'turn': 'X',
        'last_move': None,
        'win_cells': None,
        'threat_cells': [],
        'game_active': False
    }, to=room_id)

def get_rooms_summary():
    summary = []
    for name, r in rooms.items():
        seated = sum(1 for p in r['players'].values() if p['piece'] in ('X', 'O'))
        summary.append({'room': name, 'seated': seated, 'turn_seconds': r.get('turn_seconds', TURN_SECONDS)})
    return summary

def broadcast_room_list():
    socketio.emit('room_list', {'rooms': get_rooms_summary()})

def handle_get_rooms(data=None):
    emit('room_list', {'rooms': get_rooms_summary()}, to=request.sid)

def caro_index():
    return HTML_PAGE

def register(app, socketio_instance):
    global socketio
    socketio = socketio_instance
    socketio_instance.start_background_task(idle_sweeper_worker)
    app.add_url_rule('/caro', 'caro_index', caro_index, methods=['GET'])
    socketio_instance.on_event('join', handle_join)
    socketio_instance.on_event('sit', handle_sit)
    socketio_instance.on_event('stand', handle_stand)
    socketio_instance.on_event('disconnect', handle_disconnect)
    socketio_instance.on_event('move', handle_move)
    socketio_instance.on_event('chat', handle_chat)
    socketio_instance.on_event('surrender', handle_surrender)
    socketio_instance.on_event('reset', handle_reset)
    socketio_instance.on_event('undo_request', handle_undo_request)
    socketio_instance.on_event('undo_accept', handle_undo_accept)
    socketio_instance.on_event('get_rooms', handle_get_rooms)