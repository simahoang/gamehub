# Pet Game - Nuôi Thú Ảo (Pokémon Fanmade)
# Module được mount vào hub.py

import json
import os
import random
import sqlite3
import time
from contextlib import closing

from flask import request, send_from_directory, jsonify
from flask_socketio import emit

VERSION = "v1.3"

# ============================================================
# DATA (Giữ nguyên từ stub)
# ============================================================

POKEMON_GEN1 = {
    1: "Bulbasaur", 2: "Ivysaur", 3: "Venusaur", 4: "Charmander", 5: "Charmeleon",
    6: "Charizard", 7: "Squirtle", 8: "Wartortle", 9: "Blastoise", 10: "Caterpie",
    11: "Metapod", 12: "Butterfree", 13: "Weedle", 14: "Kakuna", 15: "Beedrill",
    16: "Pidgey", 17: "Pidgeotto", 18: "Pidgeot", 19: "Rattata", 20: "Raticate",
    21: "Spearow", 22: "Fearow", 23: "Ekans", 24: "Arbok", 25: "Pikachu",
    26: "Raichu", 27: "Sandshrew", 28: "Sandslash", 29: "Nidoran♀", 30: "Nidorina",
    31: "Nidoqueen", 32: "Nidoran♂", 33: "Nidorino", 34: "Nidoking", 35: "Clefairy",
    36: "Clefable", 37: "Vulpix", 38: "Ninetales", 39: "Jigglypuff", 40: "Wigglytuff",
    41: "Zubat", 42: "Golbat", 43: "Oddish", 44: "Gloom", 45: "Vileplume",
    46: "Paras", 47: "Parasect", 48: "Venonat", 49: "Venomoth", 50: "Diglett",
    51: "Dugtrio", 52: "Meowth", 53: "Persian", 54: "Psyduck", 55: "Golduck",
    56: "Mankey", 57: "Primeape", 58: "Growlithe", 59: "Arcanine", 60: "Poliwag",
    61: "Poliwhirl", 62: "Poliwrath", 63: "Abra", 64: "Kadabra", 65: "Alakazam",
    66: "Machop", 67: "Machoke", 68: "Machamp", 69: "Bellsprout", 70: "Weepinbell",
    71: "Victreebel", 72: "Tentacool", 73: "Tentacruel", 74: "Geodude", 75: "Graveler",
    76: "Golem", 77: "Ponyta", 78: "Rapidash", 79: "Slowpoke", 80: "Slowbro",
    81: "Magnemite", 82: "Magneton", 83: "Farfetch'd", 84: "Doduo", 85: "Dodrio",
    86: "Seel", 87: "Dewgong", 88: "Grimer", 89: "Muk", 90: "Shellder",
    91: "Cloyster", 92: "Gastly", 93: "Haunter", 94: "Gengar", 95: "Onix",
    96: "Drowzee", 97: "Hypno", 98: "Krabby", 99: "Kingler", 100: "Voltorb",
    101: "Electrode", 102: "Exeggcute", 103: "Exeggutor", 104: "Cubone", 105: "Marowak",
    106: "Hitmonlee", 107: "Hitmonchan", 108: "Lickitung", 109: "Koffing", 110: "Weezing",
    111: "Rhyhorn", 112: "Rhydon", 113: "Chansey", 114: "Tangela", 115: "Kangaskhan",
    116: "Horsea", 117: "Seadra", 118: "Goldeen", 119: "Seaking", 120: "Staryu",
    121: "Starmie", 122: "Mr. Mime", 123: "Scyther", 124: "Jynx", 125: "Electabuzz",
    126: "Magmar", 127: "Pinsir", 128: "Tauros", 129: "Magikarp", 130: "Gyarados",
    131: "Lapras", 132: "Ditto", 133: "Eevee", 134: "Vaporeon", 135: "Jolteon",
    136: "Flareon", 137: "Porygon", 138: "Omanyte", 139: "Omastar", 140: "Kabuto",
    141: "Kabutops", 142: "Aerodactyl", 143: "Snorlax", 144: "Articuno", 145: "Zapdos",
    146: "Moltres", 147: "Dratini", 148: "Dragonair", 149: "Dragonite", 150: "Mewtwo",
    151: "Mew",
}

POKEMON_GEN2 = {
    152: "Chikorita", 153: "Bayleef", 154: "Meganium", 155: "Cyndaquil", 156: "Quilava",
    157: "Typhlosion", 158: "Totodile", 159: "Croconaw", 160: "Feraligatr", 161: "Sentret",
    162: "Furret", 163: "Hoothoot", 164: "Noctowl", 165: "Ledyba", 166: "Ledian",
    167: "Spinarak", 168: "Ariados", 169: "Crobat", 170: "Chinchou", 171: "Lanturn",
    172: "Pichu", 173: "Cleffa", 174: "Igglybuff", 175: "Togepi", 176: "Togetic",
    177: "Natu", 178: "Xatu", 179: "Mareep", 180: "Flaaffy", 181: "Ampharos",
    182: "Bellossom", 183: "Marill", 184: "Azumarill", 185: "Sudowoodo", 186: "Politoed",
    187: "Hoppip", 188: "Skiploom", 189: "Jumpluff", 190: "Aipom", 191: "Sunkern",
    192: "Sunflora", 193: "Yanma", 194: "Wooper", 195: "Quagsire", 196: "Espeon",
    197: "Umbreon", 198: "Murkrow", 199: "Slowking", 200: "Misdreavus", 201: "Unown",
    202: "Wobbuffet", 203: "Girafarig", 204: "Pineco", 205: "Forretress", 206: "Dunsparce",
    207: "Gligar", 208: "Steelix", 209: "Snubbull", 210: "Granbull", 211: "Qwilfish",
    212: "Scizor", 213: "Shuckle", 214: "Heracross", 215: "Sneasel", 216: "Teddiursa",
    217: "Ursaring", 218: "Slugma", 219: "Magcargo", 220: "Swinub", 221: "Piloswine",
    222: "Corsola", 223: "Remoraid", 224: "Octillery", 225: "Delibird", 226: "Mantine",
    227: "Skarmory", 228: "Houndour", 229: "Houndoom", 230: "Kingdra", 231: "Phanpy",
    232: "Donphan", 233: "Porygon2", 234: "Stantler", 235: "Smeargle", 236: "Tyrogue",
    237: "Hitmontop", 238: "Smoochum", 239: "Elekid", 240: "Magby", 241: "Miltank",
    242: "Blissey", 243: "Raikou", 244: "Entei", 245: "Suicune", 246: "Larvitar",
    247: "Pupitar", 248: "Tyranitar", 249: "Lugia", 250: "Ho-Oh", 251: "Celebi",
}

ALL_POKEMON = {**POKEMON_GEN1, **POKEMON_GEN2}

def get_sprite_url(pokemon_id):
    return f"/static/sprites/{pokemon_id}.png"

def get_pokemon_name(pokemon_id):
    return ALL_POKEMON.get(pokemon_id, f"Unknown #{pokemon_id}")

# ============================================================
# EVOLUTION TREE (chuỗi tiến hóa chuẩn Gen 1-2)
# species_id -> [danh sách id tiến hóa kế tiếp]
# ============================================================

EVOLUTION_TREE = {
    1: [2], 2: [3],
    4: [5], 5: [6],
    7: [8], 8: [9],
    10: [11], 11: [12],
    13: [14], 14: [15],
    16: [17], 17: [18],
    19: [20],
    21: [22],
    23: [24],
    172: [25], 25: [26],
    27: [28],
    29: [30], 30: [31],
    32: [33], 33: [34],
    173: [35], 35: [36],
    37: [38],
    174: [39], 39: [40],
    41: [42], 42: [169],
    43: [44], 44: [45, 182],
    46: [47],
    48: [49],
    50: [51],
    52: [53],
    54: [55],
    56: [57],
    58: [59],
    60: [61], 61: [62, 186],
    63: [64], 64: [65],
    66: [67], 67: [68],
    69: [70], 70: [71],
    72: [73],
    74: [75], 75: [76],
    77: [78],
    79: [80, 199],
    81: [82],
    84: [85],
    86: [87],
    88: [89],
    90: [91],
    92: [93], 93: [94],
    95: [208],
    96: [97],
    98: [99],
    100: [101],
    102: [103],
    104: [105],
    236: [106, 107, 237],
    109: [110],
    111: [112],
    113: [242],
    116: [117], 117: [230],
    118: [119],
    120: [121],
    123: [212],
    238: [124],
    239: [125],
    240: [126],
    129: [130],
    133: [134, 135, 136, 196, 197],
    137: [233],
    138: [139],
    140: [141],
    147: [148], 148: [149],
    152: [153], 153: [154],
    155: [156], 156: [157],
    158: [159], 159: [160],
    161: [162],
    163: [164],
    165: [166],
    167: [168],
    170: [171],
    175: [176],
    177: [178],
    179: [180], 180: [181],
    183: [184],
    187: [188], 188: [189],
    191: [192],
    194: [195],
    204: [205],
    209: [210],
    216: [217],
    218: [219],
    220: [221],
    223: [224],
    228: [229],
    231: [232],
    246: [247], 247: [248],
}

LEGENDARY_IDS = {144, 145, 146, 150, 243, 244, 245, 249, 250}
MYTHICAL_IDS = {151, 251}

LEGENDARY_CHANCE = 0.001
MYTHICAL_CHANCE = 0.1

# BASE_FORMS: các id không phải là đích tiến hóa của bất kỳ loài nào
_EVOLUTION_TARGETS = {target for targets in EVOLUTION_TREE.values() for target in targets}
BASE_FORMS = {pid for pid in ALL_POKEMON if pid not in _EVOLUTION_TARGETS}

# Pool thường: BASE_FORMS loại trừ legendary & mythical
NORMAL_POOL = sorted(pid for pid in BASE_FORMS if pid not in LEGENDARY_IDS and pid not in MYTHICAL_IDS)

# ============================================================
# CONFIG DECAY & ACTION (điểm / giờ)
# ============================================================

HUNGER_DECAY = 6.0
HAPPINESS_DECAY = 4.0
ENERGY_DECAY = 3.0
SICK_HEALTH_DECAY = 5.0    # health giảm khi đang ốm
HEALTH_RECOVER = 2.0       # health hồi khi hết ốm

POOP_AVG_INTERVAL = 3.0       # Trung bình 3h/lần
POOP_INTERVAL_SPREAD = 1.0    # ±1h random → 2-4h
POOP_HAPPINESS_PENALTY = 2.0  # -2 happiness/giờ cho mỗi cục phân
MAX_POOPS = 4                  # Tối đa 4 cục phân hiển thị

START_STATE = {
    'hunger': 100,
    'happiness': 100,
    'energy': 100,
    'health': 100,
    'age_hours': 0.0,
    'sick': False,
    'in_center': False,
    'center_since': None,
}

ACTIONS = {
    'feed':   {'hunger': 30, 'happiness': 5},
    'play':   {'happiness': 25, 'energy': -10},
    'sleep':  {'energy': 40, 'health': 5},
    'heal':   {'health': 30},
}

_spin_cooldowns = {}  # IP -> timestamp of last spin

# ============================================================
# STORAGE (SQLite)
# ============================================================

socketio = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(BASE_DIR, 'pet_game.db')
PLAYERS_FILE = os.path.join(BASE_DIR, 'players.json')

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('PRAGMA journal_mode=WAL;')
    return closing(conn)

def migrate_to_sqlite():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS pets (
            ip TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS legendary (
            species_id INTEGER PRIMARY KEY,
            ip TEXT NOT NULL
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS spin_state (
            ip TEXT PRIMARY KEY,
            species_ids TEXT NOT NULL,
            created_at REAL NOT NULL
        )''')

        row = conn.execute('SELECT COUNT(*) FROM pets').fetchone()
        if row[0] > 0:
            return

        old_pets_file = os.path.join(BASE_DIR, 'pets.json')
        old_legendary_file = os.path.join(BASE_DIR, 'legendary.json')

        if os.path.exists(old_pets_file):
            with open(old_pets_file, 'r', encoding='utf-8') as f:
                pets = json.load(f)
            for ip, data in pets.items():
                conn.execute(
                    'INSERT OR REPLACE INTO pets (ip, data) VALUES (?, ?)',
                    (ip, json.dumps(data, ensure_ascii=False))
                )

        if os.path.exists(old_legendary_file):
            with open(old_legendary_file, 'r', encoding='utf-8') as f:
                legendary = json.load(f)
            for species_id, ip in legendary.items():
                conn.execute(
                    'INSERT OR REPLACE INTO legendary (species_id, ip) VALUES (?, ?)',
                    (int(species_id), ip)
                )

        conn.commit()

def load_pets():
    with get_db() as conn:
        rows = conn.execute('SELECT ip, data FROM pets').fetchall()
    return {ip: json.loads(data) for ip, data in rows}

def save_pets(pets):
    with get_db() as conn:
        conn.executemany(
            'INSERT OR REPLACE INTO pets (ip, data) VALUES (?, ?)',
            ((ip, json.dumps(data, ensure_ascii=False)) for ip, data in pets.items())
        )
        conn.commit()

def load_legendary():
    with get_db() as conn:
        rows = conn.execute('SELECT species_id, ip FROM legendary').fetchall()
    return {str(sid): ip for sid, ip in rows}

def save_legendary(legendary):
    with get_db() as conn:
        conn.executemany(
            'INSERT OR REPLACE INTO legendary (species_id, ip) VALUES (?, ?)',
            ((int(species_id), ip) for species_id, ip in legendary.items())
        )
        conn.commit()

# Auto-migrate on module load
migrate_to_sqlite()

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

# ============================================================
# SPIN & RARITY (huyền thoại / bí ẩn - 1 con duy nhất toàn server)
# ============================================================

def make_slot(pid, tier):
    return {
        'species_id': pid,
        'name': get_pokemon_name(pid),
        'sprite': get_sprite_url(pid),
        'tier': tier,
    }

def roll_slot(owned, shown):
    """owned, shown là các set int. Trả slot theo 3 tầng rarity."""
    if random.random() < LEGENDARY_CHANCE:
        if random.random() < MYTHICAL_CHANCE:
            primary_group, primary_tier = MYTHICAL_IDS, 'mythical'
        else:
            primary_group, primary_tier = LEGENDARY_IDS, 'legendary'

        candidates = [p for p in primary_group if p not in owned and p not in shown]
        if candidates:
            return make_slot(random.choice(candidates), primary_tier)

        other_group = LEGENDARY_IDS if primary_tier == 'mythical' else MYTHICAL_IDS
        other_tier = 'legendary' if primary_tier == 'mythical' else 'mythical'
        candidates = [p for p in other_group if p not in owned and p not in shown]
        if candidates:
            return make_slot(random.choice(candidates), other_tier)

    candidates = [p for p in NORMAL_POOL if p not in shown]
    return make_slot(random.choice(candidates), 'normal')

def generate_spin(n=3):
    owned = {int(k) for k in load_legendary().keys()}
    shown = set()
    slots = []
    for _ in range(n):
        slot = roll_slot(owned, shown)
        shown.add(slot['species_id'])
        slots.append(slot)
    return slots

# ============================================================
# CORE LOGIC
# ============================================================

def clamp(value, low=0, high=100):
    return max(low, min(high, value))

def derive_sick(pet):
    """Ốm khi ít nhất một chỉ số lõi (hunger/happiness/energy) về 0."""
    return pet['hunger'] <= 0 or pet['happiness'] <= 0 or pet['energy'] <= 0

def run_catch_up(pet):
    """Trừ decay + cộng tuổi theo thời gian đã trôi qua, rồi cập nhật last_updated."""
    now = time.time()
    if pet.get('in_center'):
        pet['last_updated'] = now
        return pet
    try:
        elapsed = max(0.0, now - float(pet.get('last_updated', now))) / 3600.0
    except (TypeError, ValueError):
        elapsed = 0.0

    pet['hunger'] = clamp(pet['hunger'] - HUNGER_DECAY * elapsed)
    pet['happiness'] = clamp(pet['happiness'] - HAPPINESS_DECAY * elapsed)
    pet['energy'] = clamp(pet['energy'] - ENERGY_DECAY * elapsed)
    pet['age_hours'] = float(pet.get('age_hours', 0.0)) + elapsed

    # --- Poop generation ---
    poops = pet.get('poops', [])
    if poops is None:
        poops = []
    last_poop_time = poops[-1]['created_at'] if poops else pet.get('last_updated', now)
    poop_elapsed = max(0.0, now - last_poop_time) / 3600.0

    while poop_elapsed > 0:
        interval = random.uniform(POOP_AVG_INTERVAL - POOP_INTERVAL_SPREAD, POOP_AVG_INTERVAL + POOP_INTERVAL_SPREAD)
        if poop_elapsed >= interval:
            poops.append({'created_at': last_poop_time + interval * 3600})
            last_poop_time += interval * 3600
            poop_elapsed -= interval
        else:
            break

    if len(poops) > MAX_POOPS:
        poops = poops[-MAX_POOPS:]

    pet['poops'] = poops

    # --- Poop happiness penalty ---
    if poops:
        poop_penalty = len(poops) * POOP_HAPPINESS_PENALTY * elapsed
        pet['happiness'] = clamp(pet['happiness'] - poop_penalty)

    sick = derive_sick(pet)
    pet['sick'] = sick
    if sick:
        pet['health'] = clamp(pet['health'] - SICK_HEALTH_DECAY * elapsed)
    else:
        pet['health'] = clamp(pet['health'] + HEALTH_RECOVER * elapsed)

    pet['last_updated'] = now
    return pet

def apply_action(pet, action):
    """Áp hiệu ứng hành động, clamp 0-100. heal: clear sick nếu health > 20."""
    for key, delta in ACTIONS[action].items():
        pet[key] = clamp(pet.get(key, 0) + delta)
    if action == 'heal':
        if pet['health'] > 20:
            pet['sick'] = False
    else:
        pet['sick'] = derive_sick(pet)
    return pet

def new_pet(species_id):
    return {
        'species_id': species_id,
        'hunger': START_STATE['hunger'],
        'happiness': START_STATE['happiness'],
        'energy': START_STATE['energy'],
        'health': START_STATE['health'],
        'age_hours': START_STATE['age_hours'],
        'sick': START_STATE['sick'],
        'in_center': START_STATE['in_center'],
        'center_since': START_STATE['center_since'],
        'last_updated': time.time(),
        'last_action_time': 0,
        'poops': [],  # list of {created_at: epoch}
    }

def format_age(hours):
    if hours < 24:
        return f"{hours:.1f} giờ"
    return f"{hours / 24:.1f} ngày"

def format_duration(seconds):
    try:
        seconds = max(0, int(seconds))
    except (TypeError, ValueError):
        return "0 phút"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} phút"
    hours, rem = divmod(minutes, 60)
    if hours < 24:
        return f"{hours} giờ {rem} phút"
    return f"{hours // 24} ngày"

def pet_to_client(pet, ip):
    return {
        'species_id': pet['species_id'],
        'name': get_pokemon_name(pet['species_id']),
        'sprite': get_sprite_url(pet['species_id']),
        'hunger': int(round(pet.get('hunger', 0))),
        'happiness': int(round(pet.get('happiness', 0))),
        'energy': int(round(pet.get('energy', 0))),
        'health': int(round(pet.get('health', 0))),
        'age_hours': round(pet.get('age_hours', 0.0), 2),
        'age_text': format_age(pet.get('age_hours', 0.0)),
        'sick': bool(pet.get('sick', False)),
        'in_center': bool(pet.get('in_center', False)),
        'center_since': pet.get('center_since'),
        'center_text': format_duration(time.time() - float(pet['center_since'])) if (pet.get('in_center') and pet.get('center_since')) else None,
        'player_name': resolve_player_name(ip),
        'tier': 'mythical' if pet['species_id'] in MYTHICAL_IDS else ('legendary' if pet['species_id'] in LEGENDARY_IDS else 'normal'),
        'cooldown_remaining': max(0, int(60 - (time.time() - pet.get('last_action_time', 0)))),
        'poop_count': len(pet.get('poops', [])),
    }

# ============================================================
# UI (DaisyUI CDN)
# ============================================================

HTML_PAGE = """<!DOCTYPE html>
<html lang="vi" data-theme="cupcake">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet Game - Nuôi Thú Ảo</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdn.jsdelivr.net/npm/daisyui@4.12.14/dist/full.min.css" rel="stylesheet" type="text/css" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        @keyframes pet-bounce {
            0%, 100% { transform: translateY(0); }
            30% { transform: translateY(-15px); }
            50% { transform: translateY(0); }
            70% { transform: translateY(-8px); }
        }
        .pet-bouncing {
            animation: pet-bounce 0.6s ease;
        }
    </style>
</head>
<body class="min-h-screen bg-gradient-to-br from-amber-100 via-orange-100 to-rose-100 flex items-center justify-center p-4">

    <!-- MÀN SPIN -->
    <div id="spin-screen" class="w-full max-w-4xl hidden">
        <div class="text-center mb-6">
            <h1 class="text-4xl font-extrabold text-primary">🐾 Pet Game</h1>
            <p class="text-neutral-500 mt-2">Chào <span class="font-bold">%%PLAYER_NAME%%</span>! Chọn một thú cưng để bắt đầu nuôi.</p>
        </div>
        <div class="text-center mb-6">
            <button onclick="reroll()" class="btn btn-primary btn-lg">🎲 Quay</button>
        </div>
        <div id="spin-cards" class="grid grid-cols-1 sm:grid-cols-3 gap-4"></div>
    </div>

    <!-- MÀN CHÍNH -->
    <div id="main-screen" class="w-full max-w-md hidden">
        <div class="card bg-base-100 shadow-xl">
            <div class="card-body items-center text-center">
                <div class="flex items-center gap-2">
                    <h1 class="text-3xl font-extrabold text-primary">🐾 Pet Game</h1>
                    <span id="sick-badge" class="badge badge-error badge-lg hidden">😷 Ốm</span>
                </div>
                <div class="relative">
                    <img id="pet-sprite" src="" alt="pet" class="w-64 h-64 object-contain image-render-pixel">
                    <div id="sprite-overlay" class="absolute inset-0 flex items-center justify-center text-7xl pointer-events-none hidden"></div>
                </div>
                <div id="poop-container" class="flex justify-center gap-1 mt-1" style="min-height: 28px;"></div>
                <div>
                    <h2 id="pet-name" class="text-2xl font-bold"></h2>
                    <p id="pet-age" class="text-sm text-neutral-500"></p>
                    <p class="text-xs text-neutral-400">Người nuôi: <span id="player-name"></span></p>
                </div>
                <p id="center-status" class="text-sm text-info font-semibold hidden"></p>

                <div class="w-full space-y-3 text-left pt-4">
                    <div>
                        <div class="flex justify-between text-sm mb-1"><span>🍖 Đói</span><span id="hunger-txt"></span></div>
                        <progress id="hunger-bar" class="progress progress-error" value="0" max="100"></progress>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm mb-1"><span>😊 Vui vẻ</span><span id="happiness-txt"></span></div>
                        <progress id="happiness-bar" class="progress progress-warning" value="0" max="100"></progress>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm mb-1"><span>⚡ Năng lượng</span><span id="energy-txt"></span></div>
                        <progress id="energy-bar" class="progress progress-info" value="0" max="100"></progress>
                    </div>
                    <div class="hidden">
                        <div class="flex justify-between text-sm mb-1"><span>❤️ Sức khỏe</span><span id="health-txt"></span></div>
                        <progress id="health-bar" class="progress progress-success" value="0" max="100"></progress>
                    </div>
                </div>

                <div class="flex flex-wrap justify-center gap-2 pt-4">
                    <button id="btn-feed" onclick="doAction('feed')" class="btn btn-success btn-sm">🍖 Ăn</button>
                    <button id="btn-play" onclick="doAction('play')" class="btn btn-warning btn-sm">🎮 Chơi</button>
                    <button id="btn-sleep" onclick="doAction('sleep')" class="btn btn-info btn-sm">😴 Ngủ</button>
                    <button id="btn-heal" onclick="doAction('heal')" class="btn btn-error btn-sm" style="display:none">💊 Chữa</button>
                    <button id="btn-clean" onclick="doAction('clean')" class="btn btn-secondary btn-sm">🧼 Dọn</button>
                </div>

                <div class="divider"></div>
                <button id="center-btn" onclick="toggleCenter()" class="btn btn-info btn-outline w-full">🏥 Gửi vào Trung Tâm</button>
                <button onclick="openRelease()" class="btn btn-error btn-outline w-full mt-2">🗑️ Thả Pokémon</button>
            </div>
        </div>
    </div>

    <dialog id="release-modal" class="modal">
        <div class="modal-box">
            <h3 class="font-bold text-lg">Thả Pokémon?</h3>
            <p class="py-4">Bạn chắc chắn muốn thả thú cưng hiện tại? Thao tác này không thể hoàn tác.</p>
            <div class="modal-action">
                <button class="btn" onclick="closeRelease()">Hủy</button>
                <button class="btn btn-error" onclick="confirmRelease()">Thả</button>
            </div>
        </div>
    </dialog>

    <script>
        const VERSION = "%%VERSION%%";
        const PET_STATE = %%PET_STATE_JSON%%;
        const socket = io();

        function escapeHtml(str) {
            return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        function showSpin() {
            document.getElementById('spin-screen').classList.remove('hidden');
            document.getElementById('main-screen').classList.add('hidden');
            reroll();
        }

        function tierBadge(tier) {
            if (tier === 'legendary') return ' <span class="badge badge-warning">⭐ Huyền thoại</span>';
            if (tier === 'mythical') return ' <span class="badge badge-secondary">✨ Bí ẩn</span>';
            return '';
        }

        function tierStyle(tier) {
            if (tier === 'legendary') return ' ring-2 ring-warning';
            if (tier === 'mythical') return ' ring-2 ring-secondary';
            return '';
        }

        function reroll() {
            const cards = document.getElementById('spin-cards');
            cards.innerHTML = '<div class="col-span-full text-center"><span class="loading loading-spinner loading-lg"></span></div>';
            fetch('/pet/spin')
                .then(function (r) { return r.json(); })
                .then(function (res) {
                    cards.innerHTML = '';
                    (res.slots || []).forEach(function (p) {
                        const col = document.createElement('div');
                        col.className = 'card bg-base-100 shadow-xl' + tierStyle(p.tier);
                        col.innerHTML =
                            '<figure class="px-8 pt-8"><img src="' + p.sprite + '" alt="' + escapeHtml(p.name) + '" class="w-32 h-32 object-contain"></figure>' +
                            '<div class="card-body items-center text-center">' +
                            '<h2 class="card-title">' + escapeHtml(p.name) + tierBadge(p.tier) + '</h2>' +
                            '<button class="btn btn-primary btn-block" onclick="adopt(' + p.species_id + ')">Nhận</button>' +
                            '</div>';
                        cards.appendChild(col);
                    });
                });
        }

        function adopt(id) {
            fetch('/pet/adopt', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'species_id=' + encodeURIComponent(id)
            }).then(function (r) { return r.json(); }).then(function (res) {
                if (res.ok) { location.reload(); }
                else { alert(res.error || 'Có lỗi xảy ra'); reroll(); }
            });
        }

        function setBar(id, baseClass, value, gray) {
            const el = document.getElementById(id);
            el.value = value;
            el.className = 'progress ' + (gray ? 'progress-neutral' : baseClass);
        }

        function renderMain(s) {
            IN_CENTER = !!s.in_center;
            var cd = s.cooldown_remaining || 0;
            document.getElementById('pet-sprite').src = s.sprite;
            const sick = s.sick || s.health < 30;
            document.getElementById('pet-sprite').style.filter = sick ? 'grayscale(80%)' : 'none';
            var tierHtml = '';
            if (s.tier === 'legendary') tierHtml = ' <span class="badge badge-warning">⭐ Huyền thoại</span>';
            if (s.tier === 'mythical') tierHtml = ' <span class="badge badge-secondary">✨ Bí ẩn</span>';
            document.getElementById('pet-name').innerHTML = escapeHtml(s.name) + tierHtml;
            document.getElementById('pet-age').innerText = 'Tuổi: ' + s.age_text;
            document.getElementById('player-name').innerText = s.player_name;

            const gray = IN_CENTER;
            setBar('hunger-bar', 'progress-error', s.hunger, gray);
            setBar('happiness-bar', 'progress-warning', s.happiness, gray);
            setBar('energy-bar', 'progress-info', s.energy, gray);
            setBar('health-bar', 'progress-success', s.health, gray);
            document.getElementById('hunger-txt').innerText = s.hunger + '/100';
            document.getElementById('happiness-txt').innerText = s.happiness + '/100';
            document.getElementById('energy-txt').innerText = s.energy + '/100';
            document.getElementById('health-txt').innerText = s.health + '/100';

            const badge = document.getElementById('sick-badge');
            if (s.sick) { badge.classList.remove('hidden'); } else { badge.classList.add('hidden'); }

            const centerStatus = document.getElementById('center-status');
            const centerBtn = document.getElementById('center-btn');
            const actionBtns = ['btn-feed', 'btn-play', 'btn-sleep', 'btn-heal', 'btn-clean'];
            if (gray) {
                centerStatus.classList.remove('hidden');
                centerStatus.innerText = '🏥 Đang ở Trung Tâm — Đã gửi ' + (s.center_text || '');
                centerBtn.innerText = '📥 Nhận thú về';
                actionBtns.forEach(function (id) { document.getElementById(id).disabled = true; });
            } else {
                centerStatus.classList.add('hidden');
                centerBtn.innerText = '🏥 Gửi vào Trung Tâm';
                // Cooldown cho action buttons
                actionBtns.forEach(function (id) {
                    var btn = document.getElementById(id);
                    if (cd > 0 && !IN_CENTER) {
                        btn.disabled = true;
                        if (!btn.dataset.originalText) {
                            btn.dataset.originalText = btn.innerText;
                        }
                        btn.innerText = btn.dataset.originalText + ' (' + cd + 's)';
                    } else if (!IN_CENTER) {
                        btn.disabled = false;
                        if (btn.dataset.originalText) {
                            btn.innerText = btn.dataset.originalText;
                        }
                    }
                });
            }

            // Start cooldown countdown timer
            if (window.__cdTimer) clearInterval(window.__cdTimer);
            if (cd > 0) {
                window.__cdTimer = setInterval(function () {
                    cd--;
                    if (cd <= 0) {
                        clearInterval(window.__cdTimer);
                        actionBtns.forEach(function (id) {
                            var btn = document.getElementById(id);
                            btn.disabled = false;
                            if (btn.dataset.originalText) btn.innerText = btn.dataset.originalText;
                        });
                    } else {
                        actionBtns.forEach(function (id) {
                            var btn = document.getElementById(id);
                            if (btn.dataset.originalText) {
                                btn.innerText = btn.dataset.originalText + ' (' + cd + 's)';
                            }
                        });
                    }
                }, 1000);
            }

            // Hiển thị phân
            var poopContainer = document.getElementById('poop-container');
            poopContainer.innerHTML = '';
            for (var i = 0; i < (s.poop_count || 0); i++) {
                var poop = document.createElement('span');
                poop.textContent = '💩';
                poop.style.fontSize = '20px';
                poopContainer.appendChild(poop);
            }

            // Nút Clean hiển thị số cục phân
            var cleanBtn = document.getElementById('btn-clean');
            if (s.poop_count > 0) {
                cleanBtn.innerText = '🧼 Dọn (' + s.poop_count + ')';
            } else {
                cleanBtn.innerText = '🧼 Dọn';
            }
        }

        function showMain(s) {
            document.getElementById('spin-screen').classList.add('hidden');
            document.getElementById('main-screen').classList.remove('hidden');
            renderMain(s);
        }

        let IN_CENTER = false;

        function doAction(action) {
            socket.emit('pet_action', { action: action });
            if (action === 'sleep') { showOverlay('💤'); }
            if (action === 'feed') { showOverlay('🍖'); }
            if (action === 'play') { showOverlay('🎾'); }
        }

        function showOverlay(emoji) {
            const ov = document.getElementById('sprite-overlay');
            ov.innerText = emoji;
            ov.classList.remove('hidden');
            const sprite = document.getElementById('pet-sprite');
            sprite.classList.add('pet-bouncing');
            setTimeout(function () { sprite.classList.remove('pet-bouncing'); }, 600);
            if (window.__overlayTimer) { clearTimeout(window.__overlayTimer); }
            window.__overlayTimer = setTimeout(function () { ov.classList.add('hidden'); ov.innerText = ''; }, 2000);
        }

        function toggleCenter() {
            socket.emit('pet_action', { action: IN_CENTER ? 'receive' : 'center' });
        }

        function openRelease() {
            document.getElementById('release-modal').showModal();
        }

        function closeRelease() {
            document.getElementById('release-modal').close();
        }

        function confirmRelease() {
            document.getElementById('release-modal').close();
            socket.emit('pet_action', { action: 'release' });
        }

        socket.on('pet_update', function (data) { renderMain(data); });

        socket.on('pet_released', function () { showSpin(); });

        if (PET_STATE !== null) { showMain(PET_STATE); } else { showSpin(); }
    </script>

    <div class="fixed bottom-2 right-3 text-xs text-neutral-400">%%VERSION%%</div>
</body>
</html>
"""

# ============================================================
# ROUTES & SOCKET EVENTS
# ============================================================

def pet_index():
    ip = request.remote_addr
    pets = load_pets()
    pet = pets.get(ip)
    pet_state_json = 'null'
    if pet is not None:
        run_catch_up(pet)
        save_pets(pets)
        pet_state_json = json.dumps(pet_to_client(pet, ip), ensure_ascii=False)

    player_name = resolve_player_name(ip)

    html = (HTML_PAGE
            .replace('%%VERSION%%', VERSION)
            .replace('%%PLAYER_NAME%%', player_name)
            .replace('%%PET_STATE_JSON%%', pet_state_json))
    return html

def pet_adopt():
    ip = request.remote_addr
    try:
        species_id = int(request.form.get('species_id', ''))
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Loài không hợp lệ'})
    if species_id not in BASE_FORMS:
        return jsonify({'ok': False, 'error': 'Loài không hợp lệ'})

    tier = 'mythical' if species_id in MYTHICAL_IDS else ('legendary' if species_id in LEGENDARY_IDS else 'normal')

    with get_db() as conn:
        # 1. Verify spin state
        row = conn.execute(
            'SELECT species_ids, created_at FROM spin_state WHERE ip = ?', (ip,)
        ).fetchone()
        if not row:
            return jsonify({'ok': False, 'error': 'Vui lòng quay lại để chọn Pokémon'})
        species_ids_json, created_at = row
        if time.time() - created_at > 120:
            conn.execute('DELETE FROM spin_state WHERE ip = ?', (ip,))
            conn.commit()
            return jsonify({'ok': False, 'error': 'Hết thời gian, vui lòng quay lại'})
        allowed_ids = json.loads(species_ids_json)
        if species_id not in allowed_ids:
            return jsonify({'ok': False, 'error': 'Pokémon không hợp lệ'})

        # 2. Check IP already has pet
        row = conn.execute('SELECT 1 FROM pets WHERE ip = ?', (ip,)).fetchone()
        if row:
            return jsonify({'ok': False, 'error': 'Bạn đã có pet rồi'})

        # 3. Claim legendary if applicable
        if tier != 'normal':
            conn.execute('INSERT OR IGNORE INTO legendary (species_id, ip) VALUES (?, ?)',
                         (species_id, ip))
            if conn.total_changes == 0:
                return jsonify({'ok': False, 'error': 'Pokémon này đã có chủ!'}), 409

        # 4. Create pet
        conn.execute('INSERT OR IGNORE INTO pets (ip, data) VALUES (?, ?)',
                     (ip, json.dumps(new_pet(species_id), ensure_ascii=False)))
        if conn.total_changes == 0:
            return jsonify({'ok': False, 'error': 'Bạn đã có pet rồi'})

        # 5. Delete spin state
        conn.execute('DELETE FROM spin_state WHERE ip = ?', (ip,))

        conn.commit()

    return jsonify({'ok': True})

def serve_sprite(filename):
    sprites_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'sprites')
    return send_from_directory(sprites_dir, filename)

def pet_spin():
    ip = request.remote_addr
    now = time.time()

    # Rate-limit: 1 spin / 2 seconds
    last_spin = _spin_cooldowns.get(ip, 0)
    if now - last_spin < 2:
        return jsonify({'slots': [], 'error': 'Quay nhanh quá! Đợi 2 giây nhé.'})
    _spin_cooldowns[ip] = now

    slots = generate_spin()
    species_ids = [s['species_id'] for s in slots]
    with get_db() as conn:
        conn.execute('DELETE FROM spin_state WHERE created_at < ?', (now - 120,))
        conn.execute(
            'INSERT OR REPLACE INTO spin_state (ip, species_ids, created_at) VALUES (?, ?, ?)',
            (ip, json.dumps(species_ids), now)
        )
        conn.commit()
    return jsonify({'slots': slots})

def handle_pet_action(data):
    ip = request.remote_addr
    action = data.get('action')

    if action == 'release':
        with get_db() as conn:
            row = conn.execute('SELECT data FROM pets WHERE ip = ?', (ip,)).fetchone()
            if not row:
                return
            pet = json.loads(row[0])
            species_id = pet.get('species_id')
            conn.execute('DELETE FROM pets WHERE ip = ?', (ip,))
            if species_id in LEGENDARY_IDS or species_id in MYTHICAL_IDS:
                conn.execute('DELETE FROM legendary WHERE species_id = ? AND ip = ?', (species_id, ip))
            conn.commit()
        emit('pet_released', {}, to=request.sid)
        return

    # Center: SELECT + UPDATE trong cùng 1 transaction
    if action == 'center':
        with get_db() as conn:
            row = conn.execute('SELECT data FROM pets WHERE ip = ?', (ip,)).fetchone()
            if not row:
                return
            pet = json.loads(row[0])
            pet['in_center'] = True
            pet['center_since'] = time.time()
            pet['last_updated'] = time.time()
            conn.execute('UPDATE pets SET data = ? WHERE ip = ?', (json.dumps(pet, ensure_ascii=False), ip))
            conn.commit()
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return

    # Receive: SELECT + UPDATE trong cùng 1 transaction
    if action == 'receive':
        with get_db() as conn:
            row = conn.execute('SELECT data FROM pets WHERE ip = ?', (ip,)).fetchone()
            if not row:
                return
            pet = json.loads(row[0])
            pet['in_center'] = False
            pet['center_since'] = None
            pet['last_updated'] = time.time()
            conn.execute('UPDATE pets SET data = ? WHERE ip = ?', (json.dumps(pet, ensure_ascii=False), ip))
            conn.commit()
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return

    # Các action còn lại: SELECT + run_catch_up + modify + UPDATE
    with get_db() as conn:
        row = conn.execute('SELECT data FROM pets WHERE ip = ?', (ip,)).fetchone()
        if not row:
            return
        pet = json.loads(row[0])

    run_catch_up(pet)

    if action == 'clean':
        poops = pet.get('poops', [])
        if poops:
            poops.pop(0)
            pet['poops'] = poops
            pet['happiness'] = clamp(pet['happiness'] + 5)
            pet['health'] = clamp(pet['health'] + 5)
        pet['last_updated'] = time.time()
        with get_db() as conn:
            conn.execute('UPDATE pets SET data = ? WHERE ip = ?', (json.dumps(pet, ensure_ascii=False), ip))
            conn.commit()
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return

    if action not in ACTIONS:
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return
    if pet.get('in_center'):
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return

    # Cooldown check
    now = time.time()
    last_action = pet.get('last_action_time', 0)
    if now - last_action < 60:
        emit('pet_update', pet_to_client(pet, ip), to=request.sid)
        return

    apply_action(pet, action)
    pet['last_action_time'] = time.time()
    pet['last_updated'] = time.time()
    with get_db() as conn:
        conn.execute('UPDATE pets SET data = ? WHERE ip = ?', (json.dumps(pet, ensure_ascii=False), ip))
        conn.commit()
    emit('pet_update', pet_to_client(pet, ip), to=request.sid)

def register(app, socketio_instance):
    global socketio
    socketio = socketio_instance

    app.add_url_rule('/pet', 'pet_index', pet_index, methods=['GET'])
    app.add_url_rule('/pet/adopt', 'pet_adopt', pet_adopt, methods=['POST'])
    app.add_url_rule('/pet/spin', 'pet_spin', pet_spin, methods=['GET'])
    app.add_url_rule('/static/sprites/<filename>', 'pet_sprites', serve_sprite, methods=['GET'])

    socketio_instance.on_event('pet_action', handle_pet_action)