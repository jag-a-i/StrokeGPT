# background_modes.py (Corrected for Generic Device Control)
import threading
import time
import random
from collections import deque

def _drain_latest_message(message_queue):
    try:
        latest = None
        while True:
            latest = message_queue.popleft()
    except IndexError:
        pass
    return latest

class AutoModeThread(threading.Thread):
    def __init__(self, mode_func, initial_message, services, callbacks, mode_name="auto"):
        super().__init__(daemon=True)
        self.name = mode_name
        self._mode_func = mode_func
        self._initial_message = initial_message
        self._services = services
        self._callbacks = callbacks
        self._stop_event = threading.Event()
<<<<<<< HEAD
        self.daemon = True

    def run(self):
        message_callback = self._callbacks.get('send_message')
        ## MODIFIED: The service key is now 'device' to support any controller.
        device_controller = self._services.get('device')
        
        if message_callback:
            message_callback(self._initial_message)
        time.sleep(2)

        try:
            # Pass the services dictionary directly to the logic function
            self._mode_func(self._stop_event, self._services, self._callbacks)
        except Exception as e:
            print(f"Auto mode crashed: {e}")
        finally:
            # On exit, stop the device
            ## MODIFIED: All movement calls now go through the generic device_controller.
            if device_controller:
                device_controller.stop()
            
            stop_callback = self._callbacks.get('on_stop')
            if stop_callback:
                stop_callback()

            if message_callback:
                message_callback("Okay, you're in control now.")
=======
>>>>>>> abb6cafeac2d32c73113cbded5fac77b851835a4

    def stop(self):
        self._stop_event.set()

    def run(self):
        try:
            send_message = self._callbacks.get('send_message')
            if send_message and self._initial_message:
                send_message(self._initial_message, add_to_history=False)
        except Exception:
            pass
        try:
            self._mode_func(self._stop_event, self._services, self._callbacks)
        finally:
            on_stop = self._callbacks.get('on_stop')
            if on_stop:
                try:
                    on_stop()
                except Exception:
                    pass

# ---- Pattern playback helpers ----
def _choose_zone(default_choices, callbacks):
    """Apply zone lock and full permission to pick a zone."""
    zl = callbacks.get('get_zone_lock', lambda: {"zone": None, "no_connectors": False})()
    if zl and zl.get("zone"):
        return zl["zone"], zl.get("no_connectors", False)
    full_ok = callbacks.get('full_allowed', lambda: False)()
    # Weighted random with full excluded unless allowed
    zones = ['mid', 'tip', 'base'] + (['full'] if full_ok else [])
    weights = [0.40, 0.30, 0.30] + ([0.10] if full_ok else [])
    return random.choices(zones, weights=weights, k=1)[0], False

def _play_pattern(stop_event, services, callbacks, zone, duration_s, preferred_tags=None, rng_cap_frac_override=None, recent_names=None, recent_classes=None):
    """
    Selects, scales, and plays a library pattern for a given duration.
    """
    scripts = services['scripts']
    handy = services['handy']
    remember = callbacks.get('remember_pattern')
    
    ctx = callbacks['get_context']()
    lo = ctx.get('allowed_depth_min', 0)
    hi = ctx.get('allowed_depth_max', 100)
    
    avoid_names = set(recent_names or [])
    avoid_classes = set(recent_classes or [])

    pat = scripts.select(
        zone=zone,
        avoid_names=avoid_names,
        avoid_classes=avoid_classes,
        recent_seconds=60.0,
        allow_full=callbacks.get('full_allowed', lambda: False)(),
        preferred_tags=preferred_tags
    )

    if remember and pat and pat.get('name'):
        remember(pat['name'])

    seed = hash((pat.get('name') if pat else "fallback", int(time.time() // 5))) & 0xFFFFFFFF
    steps = scripts.scale_to_user(
        pat, zone, lo, hi, duration_s,
        jitter_dp_frac=0.02, jitter_rng_frac=0.10, rng_cap_frac_override=rng_cap_frac_override, seed=seed
    )

    if steps:
        handy.play_pattern(steps)
        # Wait for the pattern to finish, while still being responsive to a stop signal
        end_time = time.time() + duration_s
        while time.time() < end_time and not stop_event.is_set():
            time.sleep(0.1)

    if pat:
        return pat.get('name'), pat.get('class'), zone, False
    return None, None, zone, False

def auto_mode_logic(stop_event, services, callbacks):
<<<<<<< HEAD
    ## MODIFIED: The local variable is now generic.
    llm_service, device_controller = services['llm'], services['device']
    get_context, send_message, get_timings, message_queue = callbacks['get_context'], callbacks['send_message'], callbacks['get_timings'], callbacks['message_queue']
    
    while not stop_event.is_set():
        auto_min, auto_max = get_timings('auto')
        context = get_context()
        context['current_mood'] = "Curious"
        
        prompt = f"You are in Automode. Your goal is to create a varied and exciting experience. Do something different now."
        
        if user_message := _check_for_user_message(message_queue):
            prompt += f"\n\n**USER FEEDBACK TO CONSIDER:** \"{user_message}\"\n\n**INSTRUCTION:** Analyze the user's feedback. Let it influence your next move and what you say. For example, if they say 'faster', increase the speed."
        
        response = llm_service.get_chat_response([{"role": "user", "content": prompt}], context, temperature=1.1)
    
        if not response or not response.get("move"):
            time.sleep(1); 
            continue
    
        if chat_text := response.get("chat"): send_message(chat_text)
        if move_data := response.get("move"):
            ## MODIFIED: All movement calls now go through the generic device_controller.
            device_controller.move(move_data.get("sp"), move_data.get("dp"), move_data.get("rng"))
        time.sleep(random.uniform(auto_min, auto_max))

def milking_mode_logic(stop_event, services, callbacks):
    ## MODIFIED: The local variable is now generic.
    llm_service, device_controller = services['llm'], services['device']
    get_context, send_message, get_timings, message_queue = callbacks['get_context'], callbacks['send_message'], callbacks['get_timings'], callbacks['message_queue']
=======
    llm = services['llm']
    get_context = callbacks['get_context']
    send_message = callbacks['send_message']
    get_timings = callbacks['get_timings']
    messages = callbacks['message_queue']
    chat_history = services['chat_history']

    recent_names = deque(maxlen=6)
    recent_classes = deque(maxlen=3)
    recent_zones = deque(maxlen=2)

    while not stop_event.is_set():
        auto_min, auto_max = get_timings('auto')
        duration = max(0.5, random.uniform(float(auto_min), float(auto_max)))

        context = get_context(chat_history=chat_history)
        user_msg = _drain_latest_message(messages)
        
        current_history = list(chat_history)
        prompt_addition = "Speak one concise teasing line for automatic play. No numbers."
        if user_msg:
            prompt_addition += f" Consider the user's last message: '{user_msg}'."
        current_history.append({"role": "user", "content": prompt_addition})
        
        resp = llm.get_chat_response(current_history, context, temperature=0.9)
        if isinstance(resp, dict) and resp.get('chat'):
            send_message(resp['chat'])

        zone, no_connectors = _choose_zone(['mid', 'tip', 'base'], callbacks)

        local_tags = {
            'tip': ['zone-tip'],
            'mid': ['zone-mid'],
            'base': ['zone-base']
        }.get(zone, [])
        
        name, klass, z, nc = _play_pattern(
            stop_event, services, callbacks, zone=zone, duration_s=duration,
            preferred_tags=local_tags,
            recent_names=list(recent_names), recent_classes=list(recent_classes)
        )
        if name: recent_names.append(name)
        if klass: recent_classes.append(klass)
        recent_zones.append(z)

def milking_mode_logic(stop_event, services, callbacks):
    llm = services['llm']
    get_context = callbacks['get_context']
    send_message = callbacks['send_message']
    get_timings = callbacks['get_timings']
    messages = callbacks['message_queue']
    chat_history = services['chat_history']
>>>>>>> abb6cafeac2d32c73113cbded5fac77b851835a4

    recent_names = deque(maxlen=6)
    recent_classes = deque(maxlen=3)

    while not stop_event.is_set():
        milking_min, milking_max = get_timings('milking')
        duration = max(0.3, random.uniform(float(milking_min), float(milking_max)))

        context = get_context(chat_history=chat_history)
        context['current_mood'] = 'Dominant'
        user_msg = _drain_latest_message(messages)

        current_history = list(chat_history)
        prompt_addition = "Short commanding line for a deep/base milking sequence."
        if user_msg:
            prompt_addition += f" Consider the user's last message: '{user_msg}'."
        current_history.append({"role": "user", "content": prompt_addition})
        
<<<<<<< HEAD
        if response.get("chat"): send_message(response.get("chat"))
        if move_data := response.get("move"):
            ## MODIFIED: All movement calls now go through the generic device_controller.
            device_controller.move(move_data.get("sp"), move_data.get("dp"), move_data.get("rng"))
        time.sleep(random.uniform(milking_min, milking_max))
    
    if not stop_event.is_set():
        send_message("That's it... give it all to me. Don't hold back.")
        time.sleep(4)

def edging_mode_logic(stop_event, services, callbacks):
    ## MODIFIED: The local variable is now generic.
    llm_service, device_controller = services['llm'], services['device']
    get_context, send_message, get_timings, update_mood = callbacks['get_context'], callbacks['send_message'], callbacks['get_timings'], callbacks['update_mood']
=======
        resp = llm.get_chat_response(current_history, context, temperature=0.8)
        if isinstance(resp, dict) and resp.get('chat'):
            send_message(resp['chat'])

        name, klass, z, nc = _play_pattern(
            stop_event, services, callbacks, zone='base', duration_s=duration,
            preferred_tags=['zone-base', 'rhythm-pulse', 'rhythm-grind'],
            recent_names=list(recent_names), recent_classes=list(recent_classes)
        )
        if name: recent_names.append(name)
        if klass: recent_classes.append(klass)

def edging_mode_logic(stop_event, services, callbacks):
    llm = services['llm']
    get_context = callbacks['get_context']
    send_message = callbacks['send_message']
    get_timings = callbacks['get_timings']
    update_mood = callbacks['update_mood']
>>>>>>> abb6cafeac2d32c73113cbded5fac77b851835a4
    user_signal_event = callbacks['user_signal_event']
    messages = callbacks['message_queue']
    chat_history = services['chat_history']

    phase = 'BUILD_UP'
    edges = 0
    recent_names = deque(maxlen=6)
    recent_classes = deque(maxlen=3)

    while not stop_event.is_set():
        edging_min, edging_max = get_timings('edging')
        duration = max(0.5, random.uniform(float(edging_min), float(edging_max)))

        context = get_context(chat_history=chat_history)
        context['current_mood'] = 'Teasing'
        user_msg = _drain_latest_message(messages)
        if user_signal_event.is_set():
            user_signal_event.clear()
            phase = 'PULL_BACK'
            edges += 1
        
<<<<<<< HEAD
        if chat_text := response.get("chat"): send_message(chat_text)
        if move_data := response.get("move"):
            ## MODIFIED: All movement calls now go through the generic device_controller.
            device_controller.move(move_data.get("sp"), move_data.get("dp"), move_data.get("rng"))
=======
        current_history = list(chat_history)
        prompt_addition = f"Edging phase: {phase}. One sentence."
        if user_msg:
            prompt_addition += f" Consider the user's last message: '{user_msg}'."
        current_history.append({"role": "user", "content": prompt_addition})
>>>>>>> abb6cafeac2d32c73113cbded5fac77b851835a4

        resp = llm.get_chat_response(current_history, context, temperature=0.8)
        if isinstance(resp, dict) and resp.get('chat'):
            send_message(resp['chat'])

        zone_map = {'BUILD_UP': 'mid', 'TEASE': 'tip', 'PULL_BACK': 'base', 'RECOVERY': 'mid'}
        zone = zone_map.get(phase, 'mid')

        name, klass, z, nc = _play_pattern(
            stop_event, services, callbacks, zone=zone, duration_s=duration,
            preferred_tags=None,
            recent_names=list(recent_names), recent_classes=list(recent_classes)
        )
        if name: recent_names.append(name)
        if klass: recent_classes.append(klass)

        if phase == 'PULL_BACK':
            phase = 'RECOVERY'
        else:
            phase = random.choice(['BUILD_UP', 'TEASE'])

    try:
        if edges > 0:
            send_message(f"You held {edges} edge{'s' if edges != 1 else ''}.")
        update_mood('Afterglow')
    except Exception:
        pass