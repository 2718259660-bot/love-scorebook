"""
恋爱计分小本本 - Flask 后端
数据存储在 GitHub Gist，两人可同时使用
"""

import os
import json
import time
import urllib.request
import urllib.error
import ssl
from flask import Flask, request, jsonify, send_file, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')

# GitHub Gist 配置
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_GIST_ID = os.environ.get('GITHUB_GIST_ID', 'eda7ded8c86c3aecd41a47f675ad5a54')

_gist_ctx = ssl.create_default_context()
_gist_ctx.check_hostname = False
_gist_ctx.verify_mode = ssl.CERT_NONE

def _gist_req(path, data=None, method='GET'):
    url = f'https://api.github.com{path}'
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'love-scorebook/1.0'
    }
    try:
        body = json.dumps(data, ensure_ascii=False).encode() if data else None
        req = urllib.request.Request(url, data=body, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=15, context=_gist_ctx) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return {'error': json.loads(e.read())}
        except:
            return {'error': str(e)}
    except Exception as e:
        return {'error': str(e)}

def load_data():
    """从 GitHub Gist 加载数据"""
    result = _gist_req(f'/gists/{GITHUB_GIST_ID}')
    if 'files' in result and 'data.json' in result['files']:
        try:
            content = result['files']['data.json']['content']
            return json.loads(content)
        except (json.JSONDecodeError, KeyError):
            pass
    # 降级到本地文件
    return _load_local_fallback()

def save_data(data):
    """保存数据到 GitHub Gist"""
    result = _gist_req(f'/gists/{GITHUB_GIST_ID}', data, 'PATCH')
    if 'error' in result:
        # 降级到本地文件
        _save_local_fallback(data)

def _load_local_fallback():
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {'entries': [], 'coupleName': '', 'unlocked': []}

def _save_local_fallback(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
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
    data = load_data()
    data['entries'] = [e for e in data.get('entries', []) if e.get('id') != entry_id]
    save_data(data)
    return jsonify({'ok': True})

@app.route('/api/reset', methods=['POST'])
def reset_all():
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
