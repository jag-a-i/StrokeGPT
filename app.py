# app.py (Revised for Multi-Controller Support)

import os
import sys
import io
import re
import atexit
import threading
import time
from collections import deque
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file, send_from_directory, send_file, session, redirect, url_for

from settings_manager import SettingsManager
from handy_controller import HandyController
from llm_service import LLMService
from audio_service import AudioService
from background_modes import AutoModeThread, auto_mode_logic, milking_mode_logic, edging_mode_logic
# INTEGRATION: Import the new ButtplugController.
from buttplug_controller import ButtplugController

# ─── INITIALIZATION ───────────────────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management
LLM_URL = "http://127.0.0.1:11434/api/chat"
settings = SettingsManager(settings_file_path="my_settings.json")
settings.load()

# INTEGRATION: The 'handy' object is replaced by a generic 'device_controller'.
# It starts as None and will be initialized by the user through the UI.
device_controller = None

llm = LLMService(url=LLM_URL)
audio = AudioService()
if settings.elevenlabs_api_key:
    if audio.set_api_key(settings.elevenlabs_api_key):
        audio.fetch_available_voices()
        audio.configure_voice(settings.elevenlabs_voice_id, True)

# In-Memory State
chat_history = deque(maxlen=20)
messages_for_ui = deque()
auto_mode_active_task = None
current_mood = "Curious"
use_long_term_memory = True
calibration_pos_mm = 0.0 # Note: This is Handy-specific
user_signal_event = threading.Event()
mode_message_queue = deque(maxlen=5)
edging_start_time = None

# Easter Egg State
special_persona_mode = None
special_persona_interactions_left = 0

SNAKE_ASCII = """
⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠟⠛⠛⠋⠉⠛⠟⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡏⠉⠹⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⠀⢸⣧⡀⠀⠰⣦⡀⠀⠀⢀⠀⠀⠈⣻⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⡇⢨⣿⣿⣖⡀⢡⠉⠄⣀⢀⣀⡀⠀⠼⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠘⠋⢏⢀⣰⣖⣿⣿⣿⠟⡡⠀⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣯⠁⢀⠂⡆⠉⠘⠛⠿⣿⢿⠟⢁⣬⡶⢠⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡯⠀⢀⡀⠝⠀⠀⠀⠀⢀⠠⣩⣤⣠⣆⣾⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⡅⠀⠊⠇⢈⣴⣦⣤⣆⠈⢀⠋⠹⣿⣇⣻⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⣿⣿⣿⣿⡄⠥⡇⠀⠀⠚⠺⠯⠀⠀⠒⠛⠒⢪⢿⣿⣿⣿⣿⣿⣿⣿⣿
⣿⣿⣿⡿⠿⠛⠋⠀⠘⣿⡄⠀⠀⠀⠋⠉⡉⠙⠂⢰⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿
⠀⠈⠉⠀⠀⠀⠀⠀⠀⠀⠙⠷⢐⠀⠀⠀⠀⢀⢴⣿⠊⠀⠉⠉⠉⠈⠙⠉⠛⠿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠰⣖⣴⣾⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠁⠀⠨
"""

# Command Keywords
STOP_COMMANDS = {"stop", "hold", "halt", "pause", "freeze", "wait"}
AUTO_ON_WORDS = {"take over", "you drive", "auto mode"}
AUTO_OFF_WORDS = {"manual", "my turn", "stop auto"}
MILKING_CUES = {"i'm close", "make me cum", "finish me"}
EDGING_CUES = {"edge me", "start edging", "tease and deny"}

# ─── HELPER FUNCTIONS ─────────────────────────────────────────────────────────────────────────────────

def get_current_context():
    global edging_start_time, special_persona_mode, device_controller
    
    last_speed = 0
    last_depth = 0
    # INTEGRATION: Safely get the last position from the active controller.
    if device_controller and hasattr(device_controller, 'last_relative_speed'):
        last_speed = device_controller.last_relative_speed
    if device_controller and hasattr(device_controller, 'last_depth_pos'):
        last_depth = device_controller.last_depth_pos

    context = {
        'persona_desc': settings.persona_desc, 'current_mood': current_mood,
        'user_profile': settings.user_profile, 'patterns': settings.patterns,
        'rules': settings.rules, 'last_stroke_speed': last_speed,
        'last_depth_pos': last_depth, 'use_long_term_memory': use_long_term_memory,
        'edging_elapsed_time': None, 'special_persona_mode': special_persona_mode
    }
    if edging_start_time:
        elapsed_seconds = int(time.time() - edging_start_time)
        minutes, seconds = divmod(elapsed_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            context['edging_elapsed_time'] = f"{hours}h {minutes}m {seconds}s"
        else:
            context['edging_elapsed_time'] = f"{minutes}m {seconds}s"
    return context

def add_message_to_queue(text, add_to_history=True):
    messages_for_ui.append(text)
    if add_to_history:
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if clean_text: chat_history.append({"role": "assistant", "content": clean_text})
    threading.Thread(target=audio.generate_audio_for_text, args=(text,)).start()

def start_background_mode(mode_logic, initial_message, mode_name):
    global auto_mode_active_task, edging_start_time, device_controller
    if not device_controller:
        add_message_to_queue("Please select a device interface in settings first.", add_to_history=False)
        return

    if auto_mode_active_task:
        auto_mode_active_task.stop()
        auto_mode_active_task.join(timeout=5)
    
    user_signal_event.clear()
    mode_message_queue.clear()
    if mode_name == 'edging':
        edging_start_time = time.time()
    
    def on_stop():
        global auto_mode_active_task, edging_start_time
        auto_mode_active_task = None
        edging_start_time = None

    def update_mood(m): global current_mood; current_mood = m
    def get_timings(n):
        return {
            'auto': (settings.auto_min_time, settings.auto_max_time),
            'milking': (settings.milking_min_time, settings.milking_max_time),
            'edging': (settings.edging_min_time, settings.edging_max_time)
        }.get(n, (3, 5))

    # INTEGRATION: Pass the generic 'device_controller' to the background thread.
    # IMPORTANT: This requires a change in background_modes.py to expect 'device' instead of 'handy'.
    services = {'llm': llm, 'device': device_controller}
    callbacks = {
        'send_message': add_message_to_queue, 'get_context': get_current_context,
        'get_timings': get_timings, 'on_stop': on_stop, 'update_mood': update_mood,
        'user_signal_event': user_signal_event,
        'message_queue': mode_message_queue
    }
    auto_mode_active_task = AutoModeThread(mode_logic, initial_message, services, callbacks, mode_name=mode_name)
    auto_mode_active_task.start()

# ─── FLASK ROUTES ──────────────────────────────────────────────────────────────────────────────────────
@app.route('/')
def home_page():
    # Check if setup is complete
    if 'setup_complete' in session and session['setup_complete']:
        return send_file('index.html')
    return redirect(url_for('setup_page'))

@app.route('/setup')
def setup_page():
    return render_template('setup.html')

@app.route('/connect_buttplug', methods=['POST'])
def connect_buttplug():
    global device_controller
    data = request.get_json()
    host = data.get('host', 'ws://127.0.0.1')
    port = data.get('port', '12345')
    
    try:
        # Disconnect existing controller if any
        if device_controller:
            device_controller.disconnect()
        
        # Initialize and connect to Buttplug
        device_controller = ButtplugController(server_uri=f"{host}:{port}")
        device_controller.connect()
        
        # Store connection details in session
        session['buttplug_connected'] = True
        session['buttplug_host'] = host
        session['buttplug_port'] = port
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to Buttplug server',
            'device': str(device_controller.device) if device_controller.device else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/connect_llama', methods=['POST'])
def connect_llama():
    global llm
    data = request.get_json()
    host = data.get('host', 'http://localhost')
    port = data.get('port', '11434')
    api_key = data.get('api_key', '')
    
    try:
        # Update LLM service URL - fix URL construction
        if host.endswith(':'):
            # Host already includes port
            llm.url = f"{host}11434/api/chat"
        elif ':' in host.split('//')[-1]:
            # Host includes port in the URL
            llm.url = f"{host}/api/chat"
        else:
            # Host doesn't include port, add it
            llm.url = f"{host}:{port}/api/chat"
        
        # Test the connection
        if llm.test_connection():
            # Store connection details in session
            session['llama_connected'] = True
            session['llama_host'] = host
            session['llama_port'] = port
            session['llama_api_key'] = api_key
            session['setup_complete'] = True  # Mark setup as complete
            
            return jsonify({
                'success': True,
                'message': 'Successfully connected to Llama server'
            })
        else:
            raise Exception("Failed to get a valid response from Llama server")
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/setup/status')
def setup_status():
    return jsonify({
        'buttplug_connected': session.get('buttplug_connected', False),
        'llama_connected': session.get('llama_connected', False),
        'setup_complete': session.get('setup_complete', False)
    })

# Serve static files from the 'static' directory
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# Serve the main JavaScript file
@app.route('/app.js')
def serve_js():
    return send_from_directory('.', 'app.js')

# Serve the main CSS file
@app.route('/styles.css')
def serve_css():
    return send_from_directory('.', 'styles.css')

# INTEGRATION: NEW ROUTE to select and initialize the device controller.
@app.route('/set_interface', methods=['POST'])
def set_interface():
    global device_controller
    data = request.json
    interface_type = data.get('interface')  # "handy" or "buttplug"

    # Disconnect any existing controller first
    if device_controller and hasattr(device_controller, 'disconnect'):
        device_controller.disconnect()
        device_controller = None

    if interface_type == 'handy':
        device_controller = HandyController(settings.handy_key)
        # Apply saved settings
        device_controller.update_settings(settings.min_speed, settings.max_speed, settings.min_depth, settings.max_depth)
        settings.device_interface = 'handy'
        print("✅ Device interface set to: The Handy")

    elif interface_type == 'buttplug':
        device_controller = ButtplugController()
        device_controller.connect() # This starts the connection process in a background thread
        settings.device_interface = 'buttplug'
        print("✅ Device interface set to: Buttplug.io")

    else:
        return jsonify({"status": "error", "message": "Invalid interface type"}), 400
    
    settings.save()
    return jsonify({"status": "success", "interface": interface_type})

def _konami_code_action():
    def pattern_thread():
        if device_controller:
            # INTEGRATION: Use the generic controller.
            device_controller.move(speed=100, depth=50, stroke_range=100)
            time.sleep(5)
            device_controller.stop()
    threading.Thread(target=pattern_thread).start()
    message = f"Kept you waiting, huh?<pre>{SNAKE_ASCII}</pre>"
    add_message_to_queue(message)

def _handle_chat_commands(text):
    if any(cmd in text for cmd in STOP_COMMANDS):
        if auto_mode_active_task: auto_mode_active_task.stop()
        if device_controller: device_controller.stop()
        add_message_to_queue("Stopping.", add_to_history=False)
        return True, jsonify({"status": "stopped"})
    if "up up down down left right left right b a" in text:
        _konami_code_action()
        return True, jsonify({"status": "konami_code_activated"})
    if any(cmd in text for cmd in AUTO_ON_WORDS) and not auto_mode_active_task:
        start_background_mode(auto_mode_logic, "Okay, I'll take over...", mode_name='auto')
        return True, jsonify({"status": "auto_started"})
    if any(cmd in text for cmd in AUTO_OFF_WORDS) and auto_mode_active_task:
        auto_mode_active_task.stop()
        return True, jsonify({"status": "auto_stopped"})
    if any(cmd in text for cmd in EDGING_CUES):
        start_background_mode(edging_mode_logic, "Let's play an edging game...", mode_name='edging')
        return True, jsonify({"status": "edging_started"})
    if any(cmd in text for cmd in MILKING_CUES):
        start_background_mode(milking_mode_logic, "You're so close... I'm taking over completely now.", mode_name='milking')
        return True, jsonify({"status": "milking_started"})
    return False, None

@app.route('/send_message', methods=['POST'])
def handle_user_message():
    global special_persona_mode, special_persona_interactions_left, device_controller
    data = request.json
    user_input = data.get('message', '').strip()

    if (p := data.get('persona_desc')) and p != settings.persona_desc:
        settings.persona_desc = p; settings.save()
    
    # INTEGRATION: Handle key setting only if the controller is a HandyController.
    if (k := data.get('key')) and k != settings.handy_key:
        settings.handy_key = k
        if isinstance(device_controller, HandyController):
            device_controller.set_api_key(k)
        settings.save()
 # Check for a device first.
    if not device_controller:
        return jsonify({"status": "no_device_selected", "messages": ["Please select a device interface in the sidebar first."]})

    # Then, ONLY check for a key if the controller is The Handy.
    if isinstance(device_controller, HandyController) and not settings.handy_key:
        return jsonify({"status": "no_key_set"})    
    if not device_controller:
        return jsonify({"status": "no_device_selected", "messages": ["Please select a device interface in the sidebar first."]})
    if not user_input: return jsonify({"status": "empty_message"})

    chat_history.append({"role": "user", "content": user_input})
    
    handled, response = _handle_chat_commands(user_input.lower())
    if handled: return response

    if auto_mode_active_task:
        mode_message_queue.append(user_input)
        return jsonify({"status": "message_relayed_to_active_mode"})
    
    llm_response = llm.get_chat_response(chat_history, get_current_context())
    
    if special_persona_mode is not None:
        special_persona_interactions_left -= 1
        if special_persona_interactions_left <= 0:
            special_persona_mode = None
            add_message_to_queue("(Personality core reverted to standard operation.)", add_to_history=False)

    if chat_text := llm_response.get("chat"): add_message_to_queue(chat_text)
    if new_mood := llm_response.get("new_mood"): global current_mood; current_mood = new_mood
    
    # INTEGRATION: Use the generic controller for movement.
    if not auto_mode_active_task and (move := llm_response.get("move")):
        if device_controller:
            device_controller.move(move.get("sp"), move.get("dp"), move.get("rng"))
            
    return jsonify({"status": "ok"})

@app.route('/check_settings')
def check_settings_route():
    # INTEGRATION: Report the configured interface back to the UI.
    is_configured = (settings.device_interface == 'handy' and settings.handy_key) or \
                    (settings.device_interface == 'buttplug')
                    
    # Re-initialize controller on startup if settings exist
    global device_controller
    if not device_controller and is_configured:
        if settings.device_interface == 'handy':
            device_controller = HandyController(settings.handy_key)
            device_controller.update_settings(settings.min_speed, settings.max_speed, settings.min_depth, settings.max_depth)
        elif settings.device_interface == 'buttplug':
            device_controller = ButtplugController()
            device_controller.connect()

    return jsonify({
        "configured": is_configured,
        "interface": settings.device_interface, # <-- NEW
        "persona": settings.persona_desc,
        "handy_key": settings.handy_key,
        "ai_name": settings.ai_name,
        "elevenlabs_key": settings.elevenlabs_api_key,
        "pfp": settings.profile_picture_b64,
        "timings": { "auto_min": settings.auto_min_time, "auto_max": settings.auto_max_time, "milking_min": settings.milking_min_time, "milking_max": settings.milking_max_time, "edging_min": settings.edging_min_time, "edging_max": settings.edging_max_time }
    })

@app.route('/set_ai_name', methods=['POST'])
def set_ai_name_route():
    global special_persona_mode, special_persona_interactions_left
    name = request.json.get('name', 'BOT').strip();
    if not name: name = 'BOT'
    
    if name.lower() == 'glados':
        special_persona_mode = "GLaDOS"
        special_persona_interactions_left = 5
        settings.ai_name = "GLaDOS"
        settings.save()
        return jsonify({"status": "special_persona_activated", "persona": "GLaDOS", "message": "Oh, it's *you*."})

    settings.ai_name = name; settings.save()
    return jsonify({"status": "success", "name": name})

@app.route('/signal_edge', methods=['POST'])
def signal_edge_route():
    if auto_mode_active_task and auto_mode_active_task.name == 'edging':
        user_signal_event.set()
        return jsonify({"status": "signaled"})
    return jsonify({"status": "ignored", "message": "Edging mode not active."}), 400

@app.route('/set_profile_picture', methods=['POST'])
def set_pfp_route():
    b64_data = request.json.get('pfp_b64')
    if not b64_data: return jsonify({"status": "error", "message": "Missing image data"}), 400
    settings.profile_picture_b64 = b64_data; settings.save()
    return jsonify({"status": "success"})

@app.route('/set_handy_key', methods=['POST'])
def set_handy_key_route():
    key = request.json.get('key')
    if not key: return jsonify({"status": "error", "message": "Key is missing"}), 400
    
    settings.handy_key = key
    # INTEGRATION: Only set API key if the current controller is the correct type.
    if isinstance(device_controller, HandyController):
        device_controller.set_api_key(key)
    settings.save()
    return jsonify({"status": "success"})

@app.route('/nudge', methods=['POST'])
def nudge_route():
    global calibration_pos_mm
    # INTEGRATION: Nudging is Handy-specific. Check controller type.
    if not isinstance(device_controller, HandyController):
        return jsonify({"status": "error", "message": "Nudge is only available for The Handy"}), 400

    if calibration_pos_mm == 0.0 and (pos := device_controller.get_position_mm()):
        calibration_pos_mm = pos
    direction = request.json.get('direction')
    calibration_pos_mm = device_controller.nudge(direction, 0, 100, calibration_pos_mm)
    return jsonify({"status": "ok", "depth_percent": device_controller.mm_to_percent(calibration_pos_mm)})

@app.route('/setup_elevenlabs', methods=['POST'])
def elevenlabs_setup_route():
    api_key = request.json.get('api_key')
    if not api_key or not audio.set_api_key(api_key): return jsonify({"status": "error"}), 400
    settings.elevenlabs_api_key = api_key; settings.save()
    return jsonify(audio.fetch_available_voices())

@app.route('/set_elevenlabs_voice', methods=['POST'])
def set_elevenlabs_voice_route():
    voice_id, enabled = request.json.get('voice_id'), request.json.get('enabled', False)
    ok, message = audio.configure_voice(voice_id, enabled)
    if ok: settings.elevenlabs_voice_id = voice_id; settings.save()
    return jsonify({"status": "ok" if ok else "error", "message": message})

@app.route('/get_updates')
def get_ui_updates_route():
    messages = [messages_for_ui.popleft() for _ in range(len(messages_for_ui))]
    if audio_chunk := audio.get_next_audio_chunk():
        return send_file(io.BytesIO(audio_chunk), mimetype='audio/mpeg')
    return jsonify({"messages": messages})

@app.route('/get_status')
def get_status_route():
    last_speed = 0
    last_depth = 0
    # INTEGRATION: Safely get status from the active controller.
    if device_controller and hasattr(device_controller, 'last_relative_speed'):
        last_speed = device_controller.last_stroke_speed
    if device_controller and hasattr(device_controller, 'last_depth_pos'):
        last_depth = device_controller.last_depth_pos
        
    return jsonify({"mood": current_mood, "speed": last_speed, "depth": last_depth})

@app.route('/set_depth_limits', methods=['POST'])
def set_depth_limits_route():
    depth1 = int(request.json.get('min_depth', 5)); depth2 = int(request.json.get('max_depth', 100))
    settings.min_depth = min(depth1, depth2); settings.max_depth = max(depth1, depth2)
    
    # INTEGRATION: Update settings only if the controller is a HandyController.
    if isinstance(device_controller, HandyController):
        device_controller.update_settings(settings.min_speed, settings.max_speed, settings.min_depth, settings.max_depth)
    settings.save()
    return jsonify({"status": "success"})

@app.route('/set_speed_limits', methods=['POST'])
def set_speed_limits_route():
    settings.min_speed = int(request.json.get('min_speed', 10)); settings.max_speed = int(request.json.get('max_speed', 80))

    # INTEGRATION: Update settings only if the controller is a HandyController.
    if isinstance(device_controller, HandyController):
        device_controller.update_settings(settings.min_speed, settings.max_speed, settings.min_depth, settings.max_depth)
    settings.save()
    return jsonify({"status": "success"})

@app.route('/like_last_move', methods=['POST'])
def like_last_move_route():
    if not device_controller:
        return jsonify({"status": "error", "message": "No active device."}), 400

    # INTEGRATION: Get last move data from the generic controller.
    last_speed = device_controller.last_relative_speed
    last_depth = device_controller.last_depth_pos
    
    pattern_name = llm.name_this_move(last_speed, last_depth, current_mood)
    sp_range = [max(0, last_speed - 5), min(100, last_speed + 5)]; dp_range = [max(0, last_depth - 5), min(100, last_depth + 5)]
    new_pattern = {"name": pattern_name, "sp_range": [int(p) for p in sp_range], "dp_range": [int(p) for p in dp_range], "moods": [current_mood], "score": 1}
    settings.session_liked_patterns.append(new_pattern)
    add_message_to_queue(f"(I'll remember that you like '{pattern_name}')", add_to_history=False)
    return jsonify({"status": "boosted", "name": pattern_name})

@app.route('/start_edging_mode', methods=['POST'])
def start_edging_route():
    start_background_mode(edging_mode_logic, "Let's play an edging game...", mode_name='edging')
    return jsonify({"status": "edging_started"})

@app.route('/start_milking_mode', methods=['POST'])
def start_milking_route():
    start_background_mode(milking_mode_logic, "You're so close... I'm taking over completely now.", mode_name='milking')
    return jsonify({"status": "milking_started"})

@app.route('/stop_auto_mode', methods=['POST'])
def stop_auto_route():
    if auto_mode_active_task: auto_mode_active_task.stop()
    return jsonify({"status": "auto_mode_stopped"})

# ─── APP STARTUP & SHUTDOWN ─────────────────────────────────────────────────────────────────────────────
def on_exit():
    print("⏳ Saving settings and disconnecting device on exit...")
    settings.save(llm, chat_history)

    # INTEGRATION: Gracefully disconnect the device controller if it supports it.
    if device_controller and hasattr(device_controller, 'disconnect'):
        device_controller.disconnect()

    print("✅ Settings saved and device disconnected.")

if __name__ == '__main__':
    atexit.register(on_exit)
    # The app now starts without a device selected. The user must choose one from the UI.
    print(f"🚀 Starting StrokeGPT server at {time.strftime('%Y-%m-%d %H:%M:%S')}...")
    print("   Please open your browser to http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)