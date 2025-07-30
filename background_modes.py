# background_modes.py (Corrected for Generic Device Control)
import threading
import time
import random

class AutoModeThread(threading.Thread):
    def __init__(self, mode_func, initial_message, services, callbacks, mode_name="auto"):
        super().__init__()
        self.name = mode_name
        self._mode_func = mode_func
        self._initial_message = initial_message
        self._services = services
        self._callbacks = callbacks
        self._stop_event = threading.Event()
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

    def stop(self):
        self._stop_event.set()

def _check_for_user_message(queue):
    if queue:
        try: return queue.popleft()
        except IndexError: pass
    return None

def auto_mode_logic(stop_event, services, callbacks):
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

    for _ in range(random.randint(6, 9)):
        if stop_event.is_set(): break
        milking_min, milking_max = get_timings('milking')
        context = get_context()
        context['current_mood'] = "Dominant"
        
        prompt = f"You are in 'milking' mode. Your only goal is to make me cum. Invent a DIFFERENT, high-intensity move now."
        
        if user_message := _check_for_user_message(message_queue):
            prompt += f"\n\n**USER FEEDBACK TO CONSIDER:** \"{user_message}\"\n\n**INSTRUCTION:** The user is close to climax. Analyze their feedback and let it influence your final moves to push them over the edge."

        response = llm_service.get_chat_response([{"role": "user", "content": prompt}], context, temperature=1.0)

        if not response or not response.get("move"):
            time.sleep(1); continue
        
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
    user_signal_event = callbacks['user_signal_event']
    message_queue = callbacks['message_queue']
    edge_count = 0

    states = ["BUILD_UP", "TEASE", "HOLD", "RECOVERY"]
    current_state = "BUILD_UP"

    while not stop_event.is_set():
        edging_min, edging_max = get_timings('edging')
        context = get_context()
        context['edge_count'] = edge_count
        prompt = ""
        
        user_message = _check_for_user_message(message_queue)
        
        if user_signal_event.is_set():
            user_signal_event.clear()
            edge_count += 1
            context['edge_count'] = edge_count
            update_mood("Dominant")
            prompt = f"I am on the edge. I have been edged {edge_count} times. You must choose one of three reactions: 1. A hard 'Pull Back'. 2. A 'Hold'. 3. A risky 'Push Over'. Describe what you choose to do and provide the move."
            current_state = "PULL_BACK"
        else:
            prompts = {
                "BUILD_UP": "Edging mode, phase: Build-up. Your goal is to slowly build my arousal. Invent a slow to medium intensity move.",
                "TEASE": "Edging mode, phase: Tease. Invent a short, fast, shallow, or otherwise teasing move to keep me guessing.",
                "HOLD": "Edging mode, phase: Hold. Maintain a medium, constant intensity. Don't go too fast or too slow. Be steady.",
                "RECOVERY": "Edging mode, phase: Recovery. Stimulation should be very low. Invent a very slow and gentle move.",
            }
            moods = {"BUILD_UP": "Seductive", "TEASE": "Playful", "HOLD": "Confident", "RECOVERY": "Loving"}
            if current_state not in moods: current_state = "BUILD_UP"
            update_mood(moods[current_state])
            prompt = prompts[current_state]

            if user_message:
                prompt += f"\n\n**USER MESSAGE TO CONSIDER:** \"{user_message}\"\n\n**INSTRUCTION:** Analyze this message. Decide if you should alter your pattern or state in response to it. Then, describe your action and provide the next `move`."

        response = llm_service.get_chat_response([{"role": "user", "content": prompt}], context, temperature=1.1)
        if not response or not response.get("move"):
            time.sleep(1); continue
        
        if chat_text := response.get("chat"): send_message(chat_text)
        if move_data := response.get("move"):
            ## MODIFIED: All movement calls now go through the generic device_controller.
            device_controller.move(move_data.get("sp"), move_data.get("dp"), move_data.get("rng"))

        if current_state != "PULL_BACK":
            current_state = random.choice(states)
        else:
            current_state = "RECOVERY"

        time.sleep(random.uniform(edging_min, edging_max))

    if not stop_event.is_set():
        send_message(f"You did so well, holding it in for {edge_count} edges...")
        update_mood("Afterglow")