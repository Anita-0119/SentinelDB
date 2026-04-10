from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import subprocess
import json
import os
import random
import time
from datetime import datetime, timedelta
from openai import OpenAI
from dotenv import load_dotenv

# --- Configuration & Client Initialization ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

BASE_DIR = os.path.dirname(__file__)
SKILLS_DIR = os.path.join(BASE_DIR, 'Skills')
DATA_DIR = os.path.join(BASE_DIR, 'data')

os.makedirs(SKILLS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# --- Global State for Isolated Telemetry ---
instance_telemetry_cache = {}

# --- Persistent Data Helpers ---
def load_db(filename, default_data):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            json.dump(default_data, f, indent=4)
    with open(filepath, 'r') as f:
        return json.load(f)

def save_db(filename, data):
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize instances
load_db('instances.json', [
    {"id": "localhost", "name": "Localhost (Dev)", "status": "ONLINE"},
    {"id": "prod-sql-01", "name": "PROD-SQL-01", "status": "ONLINE"}
])

# --- Agentic Terminal Logger ---
def agent_log(message, type="info"):
    """Streams formatted messages to the AI Copilot shell"""
    colors = {"info": "#d4d4d4", "success": "#6a9955", "warning": "#d7ba7d", "error": "#f44747", "cmd": "#9cdcfe"}
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f'<span style="color: {colors.get(type)}">{message}</span>'
    socketio.emit('log', {'data': formatted_msg, 'time': timestamp})

# --- Background Simulation (Isolated Stats) ---
def background_loop():
    """Generates unique, isolated telemetry for every connected instance separately"""
    global instance_telemetry_cache
    while True:
        try:
            current_instances = load_db('instances.json', [])
        except:
            current_instances = []

        for inst in current_instances:
            inst_id = inst['id']
            
            # Generate unique health state per instance
            instance_telemetry_cache[inst_id] = {
                "instance_id": inst_id,
                "cpu": random.randint(5, 30), 
                "disk": random.randint(100, 155), 
                "tempdb": random.randint(8, 22), 
                "blocks": random.randint(0, 1),
                "status": "ONLINE"
            }
            
            # Emit specifically for this instance ID
            socketio.emit('telemetry_update', instance_telemetry_cache[inst_id])

        # Push diverse autonomous audit logs
        if random.random() < 0.15 and current_instances:
            target = random.choice(current_instances)
            log_entry = {
                "time": datetime.now().strftime("%I:%M %p"),
                "target": target['name'],
                "anomaly": random.choice(["High VLF Count", "Stale Stats", "Buffer Cache Pressure"]),
                "out": "Resolved"
            }
            socketio.emit('audit_log_push', log_entry)

        socketio.sleep(5)

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/instances', methods=['GET', 'POST'])
def manage_instances():
    """Functional Add Instance persistence"""
    if request.method == 'POST':
        data = load_db('instances.json', [])
        data.append(request.json)
        save_db('instances.json', data)
        return jsonify({"success": True})
    return jsonify(load_db('instances.json', []))

@app.route('/api/backups')
def get_backups():
    return jsonify(load_db('backups.json', []))

@app.route('/api/updates')
def get_updates():
    return jsonify(load_db('updates.json', []))

@app.route('/api/simulate/<type>', methods=['POST'])
def simulate(type):
    """Triggers targeted critical telemetry for the Agent"""
    t = {"status": f"CRITICAL_{type.upper()}", "type": type, "instance": "localhost"}
    if type == 'cpu': t.update({"cpu": 99, "spid": 54})
    elif type == 'disk': t.update({"drive": "F", "free": 0.8})
    return jsonify({"success": True, "telemetry": t})

@app.route('/api/reason', methods=['POST'])
def agentic_reason():
    """Agentic Core: Analyzes telemetry using the templates gpt-5-nano call"""
    telemetry = request.json.get('telemetry', {})
    
    agent_log("Observing system telemetry stream...", "info")
    time.sleep(0.5)
    agent_log(f"Consulting Knowledge Base for state: {telemetry.get('status')}...", "cmd")

    prompt = f"Expert DBA Agent: Analyze {json.dumps(telemetry)} and select a script: Fix-KillSession.ps1, Fix-DiskAlert.ps1, Fix-TempDB.ps1, Optimize-Indexes.ps1. Return JSON object with 'diagnosis' and 'recommended_skill'."

    try:
        # Integrated Template Call
        response = client.responses.create(model="gpt-5-nano", input=prompt, store=True)
        agent_decision = json.loads(response.output_text)
        agent_log(agent_decision['diagnosis'], "warning")
        agent_log(f"Agent recommending autonomous fix: {agent_decision['recommended_skill']}", "success")
        return jsonify({"success": True, **agent_decision})
    except Exception as e:
        agent_log(f"Agent Reasoning Failed: {str(e)}", "error")
        return jsonify({"success": False, "message": str(e)})

@socketio.on('execute-skill')
def handle_execute_skill(data):
    """Streams real PowerShell output to the Copilot shell"""
    skill = data.get('skill')
    params = data.get('params', '')
    agent_log(f"System invoking module: {skill}", "cmd")
    
    script_path = os.path.join(SKILLS_DIR, skill)
    if os.path.exists(script_path):
        process = subprocess.Popen(["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", script_path] + params.split(), 
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(process.stdout.readline, ''):
            if line.strip(): agent_log(line.strip(), "info")
            socketio.sleep(0.1)
        process.wait()
    agent_log(f"Module {skill} execution complete.", "success")

@socketio.on('connect')
def connect():
    socketio.start_background_task(background_loop)

if __name__ == '__main__':
    socketio.run(app, port=5000, debug=True)