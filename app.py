"""
恋爱计分小本本 - Flask 后端
数据存储在云端，两个人都能用
"""

import os
import json
import time
import threading
from flask import Flask, request, jsonify, send_file
from pathlib import Path

app = Flask(__name__, static_folder='.', static_url_path='')
DATA_FILE = Path(__file__).parent / 'data.json'
DATA_FILE.touch(exist_ok=True)

# Thread-safe data access
_lock = threading.RLock()

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {'entries': [], 'coupleName': '', 'unlocked': []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    with _lock:
        data = load_data()
    return jsonify(data)

@app.route('/api/data', methods=['POST'])
def save_all():
    payload = request.json or {}
    with _lock:
        save_data(payload)
    return jsonify({'ok': True, 'saved_at': time.time()})

@app.route('/api/entry', methods=['POST'])
def add_entry():
    """添加一条记录"""
    entry = request.json or {}
    with _lock:
        data = load_data()
        data.setdefault('entries', [])
        data.setdefault('coupleName', '')
        data.setdefault('unlocked', [])
        entry['id'] = entry.get('id') or int(time.time() * 1000)
        data['entries'].insert(0, entry)
        save_data(data)
    return jsonify({'ok': True, 'entry': entry})

@app.route('/api/entry/<int:entry_id>', methods=['DELETE'])
def del_entry(entry_id):
    """删除一条记录"""
    with _lock:
        data = load_data()
        data['entries'] = [e for e in data.get('entries', []) if e.get('id') != entry_id]
        save_data(data)
    return jsonify({'ok': True})

@app.route('/api/reset', methods=['POST'])
def reset_all():
    """清空所有记录"""
    with _lock:
        save_data({'entries': [], 'coupleName': '', 'unlocked': []})
    return jsonify({'ok': True})

@app.route('/api/couple-name', methods=['POST'])
def set_couple_name():
    name = (request.json or {}).get('name', '')
    with _lock:
        data = load_data()
        data['coupleName'] = name
        save_data(data)
    return jsonify({'ok': True})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
