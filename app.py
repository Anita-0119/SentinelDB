from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import subprocess
import json
import os
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(__file__)
SKILLS_DIR = os.path.join(BASE_DIR, 'Skills')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# --- File-Based DB Initialization ---
def init_json_db(filename, default_data):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)

init_json_db('instances.json', [
    {"id": "localhost", "name": "Localhost (Dev)", "status": "ONLINE"},
    {"id": "prod-sql-01", "name": "PROD-SQL-01", "status": "ONLINE"},
    {"id": "prod-sql-02", "name": "PROD-SQL-02", "status": "WARNING"}
])

init_json_db('backups.json', [
    {"instance": "localhost", "db": "HR_Data", "type": "LOG", "date": "10:00 AM", "target": "F:\\Backups\\HR_Log.trn", "status": "CRITICAL", "errorCode": "SPACE"},
    {"instance": "localhost", "db": "Sales_Prod", "type": "FULL", "date": "Yesterday, 01:00 AM", "target": "F:\\Backups\\Sales.bak", "status": "HEALTHY", "errorCode": None},
    {"instance": "prod-sql-01", "db": "Finance_DB", "type": "FULL", "date": "Today, 02:00 AM", "target": "\\\\SAN01\\Backups\\Finance.bak", "status": "HEALTHY", "errorCode": None},
    {"instance": "prod-sql-02", "db": "Legacy_Sys", "type": "FULL", "date": "2023-10-01", "target": "C:\\Old_Bkp\\Legacy.bak", "status": "CRITICAL", "errorCode": "VLF"}
])

init_json_db('updates.json', [
    {"instance": "localhost", "current_version": "15.0.2000.5", "latest_version": "15.0.4316.3", "patch_available": True, "patch_name": "SQL Server 2019 CU28", "severity": "High"},
    {"instance": "prod-sql-01", "current_version": "16.0.1000.6", "latest_version": "16.0.1000.6", "patch_available": False, "patch_name": "Up to date", "severity": "None"},
    {"instance": "prod-sql-02", "current_version": "14.0.1000.169", "latest_version": "14.0.3421.10", "patch_available": True, "patch_name": "SQL Server 2017 CU31", "severity": "Critical"}
])

def read_json_db(filename):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def write_json_db(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/instances', methods=['GET', 'POST'])
def manage_instances():
    if request.method == 'POST':
        instances = read_json_db('instances.json')
        new_instance = request.json
        instances.append(new_instance)
        write_json_db('instances.json', instances)
        return jsonify({"success": True})
    
    return jsonify(read_json_db('instances.json'))

@app.route('/api/backups', methods=['GET'])
def get_backups():
    return jsonify(read_json_db('backups.json'))

@app.route('/api/updates', methods=['GET'])
def get_updates():
    return jsonify(read_json_db('updates.json'))

@app.route('/api/reason', methods=['POST'])
def reason():
    data = request.json
    telemetry = data.get('telemetry', {})
    anomaly_type = telemetry.get('type', 'disk')
    time.sleep(1.5) 
    
    if anomaly_type == 'cpu':
        diagnosis = f"CRITICAL: CPU pegged at {telemetry.get('cpu', 99)}%. Detected active blocking chain. SPID {telemetry.get('spid', 54)} holding schema lock."
        remediation = [f"Execute 'Fix-KillSession.ps1 -SPID {telemetry.get('spid', 54)}' to terminate rogue process.", "Flush execution plan cache."]
        skill = "Fix-KillSession.ps1"
        params = f"-SPID {telemetry.get('spid', 54)}"
    elif anomaly_type == 'tempdb':
        diagnosis = f"WARNING: TempDB data file allocation reached {telemetry.get('used', 95)}%."
        remediation = ["Execute 'Fix-TempDB.ps1' to identify and clear orphaned temporary objects."]
        skill = "Fix-TempDB.ps1"
        params = ""
    elif anomaly_type == 'index':
        diagnosis = f"MAINTENANCE: Database '{telemetry.get('db', 'Finance_DB')}' exhibits {telemetry.get('frag', 45.2)}% fragmentation."
        remediation = [f"Execute 'Optimize-Indexes.ps1 -Database {telemetry.get('db', 'Finance_DB')}' (ONLINE = ON)."]
        skill = "Optimize-Indexes.ps1"
        params = f"-Database {telemetry.get('db', 'Finance_DB')}"
    else: 
        diagnosis = f"CRITICAL: Drive {telemetry.get('drive', 'F')}: capacity breached (remaining: {telemetry.get('free', 0.8)}GB)."
        remediation = [f"Execute 'Fix-DiskAlert.ps1 -Drive {telemetry.get('drive', 'F')}'."]
        skill = "Fix-DiskAlert.ps1"
        params = f"-Drive {telemetry.get('drive', 'F')}"

    return jsonify({"success": True, "diagnosis": diagnosis, "remediation": remediation, "recommended_skill": skill, "recommended_params": params})

def stream_script_output(script_name, params):
    script_path = os.path.join(SKILLS_DIR, script_name)
    if not os.path.exists(script_path):
        socketio.emit('log', {'data': f"Simulated Execution: {script_name} {params}"})
        socketio.sleep(1)
        socketio.emit('log', {'data': f"Module {script_name} execution completed successfully."})
        return

    command = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path]
    if params:
        command.extend(params.split())

    socketio.emit('log', {'data': f"System invoking authorization for module: {script_name}"})
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        for line in iter(process.stdout.readline, ''):
            if line.strip():
                socketio.emit('log', {'data': line.strip()})
                socketio.sleep(0)
        process.stdout.close()
        process.wait()
        
        if process.returncode == 0:
            socketio.emit('log', {'data': f"Module {script_name} execution completed successfully."})
        else:
            socketio.emit('log', {'data': f"Module {script_name} terminated with code {process.returncode}."})
            
    except Exception as e:
        socketio.emit('log', {'data': f"FATAL ERROR: {str(e)}"})

@socketio.on('execute-skill')
def handle_execute_skill(data):
    socketio.start_background_task(stream_script_output, data.get('skill'), data.get('params', ''))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)