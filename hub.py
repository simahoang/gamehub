import socket
import json
import os
import secrets
import sys
from flask import Flask, request, redirect
from flask_socketio import SocketIO

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLAYERS_FILE = os.path.join(BASE_DIR, 'players.json')

# Import caro_game module
sys.path.insert(0, os.path.join(BASE_DIR, 'caro-game'))
import caro_game

# Import pet_game module
sys.path.insert(0, os.path.join(BASE_DIR, 'pet-game'))
import pet_game

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(32))
socketio = SocketIO(app, cors_allowed_origins=[])

HUB_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Game Hub LAN</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #f0f0f0; margin: 0; padding: 20px; }
        h1 { color: #333; margin-bottom: 30px; }
        #username-form { display: none; background: white; max-width: 350px; margin: 20px auto; padding: 25px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        #username-form input { width: 100%; padding: 10px; font-size: 16px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px; box-sizing: border-box; }
        #username-form button { width: 100%; padding: 10px; font-size: 16px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
        .game-grid { display: flex; justify-content: center; gap: 30px; flex-wrap: wrap; margin-top: 50px; }
        .game-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); width: 200px; cursor: pointer; text-decoration: none; color: #333; transition: transform 0.2s; }
        .game-card:hover { transform: translateY(-5px); }
        .game-card .icon { font-size: 48px; }
        .game-card .name { font-size: 20px; font-weight: bold; margin-top: 10px; }
        .game-card .desc { font-size: 13px; color: #888; margin-top: 5px; }
    </style>
</head>
<body>
    <h1>🎮 Game Hub LAN</h1>

    <div id="username-form">
        <h3 style="margin-top: 0;">Chào mừng!</h3>
        <p style="color: #666;">Đây là lần đầu bạn truy cập. Vui lòng nhập tên:</p>
        <form method="POST" action="/set_username">
            <input type="text" name="username" placeholder="Nhập tên của bạn..." required>
            <button type="submit">Vào Game</button>
        </form>
    </div>

    <div class="game-grid" id="game-grid">
        <a class="game-card" href="/caro">
            <div class="icon">❌ ⭕</div>
            <div class="name">Cờ Caro</div>
            <div class="desc"></div>
        </a>
        <a class="game-card" href="/pet">
            <div class="icon">🐾</div>
            <div class="name">Nuôi Thú Ảo</div>
            <div class="desc"></div>
        </a>
    </div>

    <script>
        const isNewIp = {IS_NEW_IP};
        if (isNewIp) {
            document.getElementById('username-form').style.display = 'block';
            document.getElementById('game-grid').style.display = 'none';
        }
    </script>
</body>
</html>
"""

def load_players():
    if not os.path.exists(PLAYERS_FILE):
        return {}
    with open(PLAYERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    ip = request.remote_addr
    players = load_players()
    is_new = 'true' if ip not in players else 'false'
    return HUB_HTML.replace('{IS_NEW_IP}', is_new)

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username', '').strip()
    ip = request.remote_addr
    players = load_players()
    if ip in players:
        return redirect('/')
    username = username[:30]
    if username and ip:
        import datetime
        players[ip] = {"name": username, "created_at": datetime.datetime.now().isoformat()}
        with open(PLAYERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(players, f, ensure_ascii=False, indent=2)
    return redirect('/')

# Register games
caro_game.register(app, socketio)
pet_game.register(app, socketio)

if __name__ == '__main__':
    host_ip = socket.gethostbyname(socket.gethostname())
    print("="*50)
    print("GAME HUB SERVER ĐÃ KHỞI ĐỘNG!")
    print(f"👉 Hãy truy cập: http://{host_ip}:5000")
    print("="*50)
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True, use_reloader=False)