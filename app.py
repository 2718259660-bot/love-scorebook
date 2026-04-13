"""
恋爱计分小本本 - Flask 后端
数据存储在 JSONBin.io 云端，两人可同时使用
"""

import os
import json
import time
import urllib.request
import urllib.error
import ssl
from flask import Flask, request, jsonify, send_file, send_from_directory
from pathlib import Path

app = Flask(__name__, static_folder='.', static_url_path='')

# JSONBin.io 配置
# 请替换以下两个值为你的 JSONBin 信息：
# 1. 创建 Collection 后复制 Collection ID（格式：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx）
# 2. 在 Collection 中创建一个新 Bin，复制该 Bin 的 ID（格式：xxxxxxxxxxxxxxxx）
JSONBIN_COLLECTION_ID = os.environ.get('JSONBIN_COLLECTION_ID', '')
JSONBIN_BIN_ID = os.environ.get('JSONBIN_BIN_ID', '')
JSONBIN_API_KEY = os.environ.get('JSONBIN_API_KEY', '')

_jsonbin_ctx = ssl.create_default_context()
_jsonbin_ctx.check_hostname = False
_jsonbin_ctx.verify_mode = ssl.CERT_NONE

def _jsonbin_req(path, data=None, method='GET'):
    """向 JSONBin.io 发起请求"""
    url = f'https://api.jsonbin.io/v3{path}'
    headers = {
        'Content-Type': 'application/json',
        'X-Access-Key': JSONBIN_API_KEY,
        'User-Agent': 'love-scorebook/1.0'
    }
    try:
        body = json.dumps(data, ensure_ascii=False).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=10, context=_jsonbin_ctx) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read())
            return {'error': err}
        except:
            return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}

def load_data():
    """从 JSONBin 加载数据"""
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        return _load_local_fallback()

    result = _jsonbin_req(f'/c/{JSONBIN_COLLECTION_ID}/{JSONBIN_BIN_ID}')
    if 'record' in result:
        return result['record']
    # 如果请求失败，尝试降级到本地文件
    return _load_local_fallback()

def save_data(data):
    """保存数据到 JSONBin"""
    if not JSONBIN_BIN_ID or not JSONBIN_API_KEY:
        return _save_local_fallback(data)

    result = _jsonbin_req(f'/c/{JSONBIN_COLLECTION_ID}/{JSONBIN_BIN_ID}', data, 'PUT')
    if 'error' in result:
        # 降级到本地文件
        _save_local_fallback(data)

def _load_local_fallback():
    """降级：本地文件读取"""
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {'entries': [], 'coupleName': '', 'unlocked': []}

def _save_local_fallback(data):
    """降级：本地文件写入"""
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    # return send_file('index.html')  # Render 兼容
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify(load_data())

@app.route('/api/data', methods=['POST'])
def save_all():
    payload = request.json or {}
    save_data(payload)
    return jsonify({'ok': True, 'saved_at': time.time()})

@app.route('/api/entry', methods=['POST'])
def add_entry():
    """添加一条记录"""
    entry = request.json or {}
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
    data = load_data()
    data['entries'] = [e for e in data.get('entries', []) if e.get('id') != entry_id]
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/reset', methods=['POST'])
def reset_all():
    """清空所有记录"""
    save_data({'entries': [], 'coupleName': '', 'unlocked': []})
    return jsonify({'ok': True})

@app.route('/api/couple-name', methods=['POST'])
def set_couple_name():
    name = (request.json or {}).get('name', '')
    data = load_data()
    data['coupleName'] = name
    save_data(data)
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    app.run(host='0.0.0.0', port=port)
