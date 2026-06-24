#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import json
import pyaudio
import re
import os
import sys
import platform
import signal
import google.generativeai as genai
import threading
import time
import subprocess
import tkinter as tk
from tkinter import font as tkFont
import tempfile
import atexit
import requests as reqs
import customtkinter as ctk
import openai
import anthropic
import requests

API_TIMEOUT = 15 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
CHATGPT_API_KEY = "" # API Key for calling ChatGPT API, loaded from chatgpt_api_key file
CLAUDE_API_KEY = "" # API Key for calling Claude API, loaded from claude_api_key file
AI_PREFERENCE = "gemini, chatgpt, claude" # Preferred order of AI models to call, loaded from ai_preference file
PROMPT = "Return 'Prompt not loaded'." # Prompt for AI API calls, loaded from prompt file
INITIAL_PROMPT = "Return 'Initial Prompt not loaded'." # Prompt for initial AI API call, loaded from initial prompt file
WAKE_WORD = "computer" # Wake word to trigger KiloBuddy listening, loaded from wake_word file
OS_VERSION = "auto-detect" # Operating system version for command generation
PREVIOUS_COMMAND_OUTPUT = "" # Store the previously run USER command output for AI use
LAST_OUTPUT = "No previous output...\n\nType a task to fulfill below." # Store the last output by the AI that was designated for the user
VERSION = "v0.0" # The version of KiloBuddy that is running
UPDATES = "release" # The type of updates to check for, "release" or "pre-release"
DANGEROUS_COMMANDS = ["sudo", "rm", "del", "erase", "dd", "diskpart", "format", "shutdown", "reboot", "poweroff", "mkfs", "reg delete", "sysctl -w", "launchctl", "iptables -F", "ufw disable", "netsh"]

# Vosk Speech Recognition Variables
vosk_model = None
vosk_rec = None
audio_stream = None
STOP_EVENT = threading.Event()
VOICE_THREAD = None
DASHBOARD_ROOT = None
ACTIVE_OVERLAY = {
    "popup": None,
    "lock": threading.Lock()
}

def get_kilobuddy_pid():
    lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
    if not os.path.exists(lock_file):
        return None
    try:
        with open(lock_file, "r") as f:
            pid = int(f.read().strip())
            return pid
    except Exception:
        return None


def is_process_running(pid):
    try:
        if platform.system() == "Windows":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle == 0:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def init_vosk():
    global vosk_model, vosk_rec, audio_stream
    try:
        model_path = "vosk-model"
        if not os.path.exists(model_path):
            print("ERROR: Vosk model not found in model path.")
            return False
        vosk_model = Model(model_path)
        vosk_rec = KaldiRecognizer(vosk_model, 16000)
        p = pyaudio.PyAudio()
        audio_stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8192)
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize Vosk: {e}")
        return False

# Initialize Necessary Variables
def initialize():
    print("INFO: Checking for updates...")
    if not load_update_type():
        print("WARNING: Failed to properly retrieve update type preference.\n    -Falling back to 'release'.\nWARN 301")
    if not load_app_version():
        print("WARNING: Failed to properly retrieve current app version.\n    -Falling back to 'v0.0'.\nWARN 302")
    check_for_updates()
    print("INFO: Initializing KiloBuddy...")
    if not load_prompt():
        print("FATAL: Failed to properly initialize prompt.\n    -The app will not function and will now stop.\nFATAL 0")
        show_failure_notification("FATAL 0: Failed to properly initialize prompt.\n\nThe app will not function and will now stop.")
        return False
    if not load_initial_prompt():
        print("FATAL: Failed to properly initialize prompt.\n    -The app will not function and will now stop.\nFATAL 0")
        show_failure_notification("FATAL 0: Failed to properly initialize prompt.\n\nThe app will not function and will now stop.")
        return False
    if not load_settings():
        print("WARNING: Failed to properly load settings.\n    -Falling back to default configurations.\nWARN 313")
    if not load_os_version():
        print("WARNING: Failed to properly initialize OS version.\n    -Falling back to auto-detected operating system.\n    -Commands generated may not be correct.\nWARN 308")
    if not init_vosk():
        print("FATAL: Failed to initialize Vosk speech recognition.\n    -The app will not function and will now stop.\nFATAL 1")
        show_failure_notification("FATAL 1: Failed to initialize Vosk speech recognition.\n\nThe app will not function and will now stop.")
        return False
    print("INFO: KiloBuddy Initialized.")
    return True

# Auto-detect operating system
def detect_os():
    system = platform.system().lower()
    
    if system == "linux":
        # Try to detect Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        distro = line.split("=")[1].strip().strip('"')
                        return f"linux-{distro}"
        except FileNotFoundError:
            pass
        return "linux"
    elif system == "darwin":
        # Get macOS version
        try:
            version = platform.mac_ver()[0]
            return f"macos-{version}"
        except:
            return "macos"
    elif system == "windows":
        # Get Windows version
        try:
            version = platform.release()
            return f"windows-{version}"
        except:
            return "windows"
    else:
        return "unknown"

# Load settings from file
# Load Preference from settings
def load_preference(line):
    global AI_PREFERENCE
    value = line.split(":", 1)[1].strip().lower()
    try:
        if value:
            AI_PREFERENCE = ", ".join(part.strip().lower() for part in value.split(",") if part.strip())
            print(f"INFO: Loaded AI Preference: {AI_PREFERENCE}")
            return True
        else:
            print(f"ERROR: Invalid AI preference '{value}'.\nERROR 112")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse AI preference: {e}\nERROR 114")
        return False

# Load Wake Word from settings
def load_wake_word(line):
    global WAKE_WORD
    value = line.split(":", 1)[1].strip().lower()
    try:
        if len(value) >= 2 and value.isalpha():
            WAKE_WORD = value.lower()
            print(f"INFO: Loaded Wake Word: {WAKE_WORD}")
            return True
        else:
            print(f"ERROR: Invalid wake word '{value}' (must be alphabetic, 2+ chars)\nERROR 109")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse wake word: {e}\nERROR 111")
        return False

# Load Timeout from settings
def load_timeout(line):
    global API_TIMEOUT
    value = line.split(":", 1)[1].strip()
    try:
        timeout = int(value)
        if 5 <= timeout <= 120:
            API_TIMEOUT = timeout
            print(f"INFO: Loaded API Timeout: {API_TIMEOUT} seconds")
            return True
        else:
            print(f"ERROR: Invalid timeout '{value}' (must be 5-120 seconds)\nERROR 143")
            return False
    except ValueError:
        print(f"ERROR: Invalid timeout format '{value}' (must be integer)\nERROR 144")
        return False
    except Exception as e:
        print(f"ERROR: Failed to parse timeout: {e}\nERROR 145")
        return False

# Load Gemini API Key from settings
def load_gemini_api_key(line):
    global GEMINI_API_KEY
    value = line.split(":", 1)[1].strip()
    try:
        if len(value) >= 20 and not any(char in value for char in [' ', '\t', '\n']):
            GEMINI_API_KEY = value
            genai.configure(api_key=value)
            print("INFO: Loaded Gemini API Key")
            return True
        else:
            print(f"ERROR: Invalid Gemini API key format.\nERROR 115")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse Gemini API key: {e}\nERROR 116")
        return False

# Load ChatGPT API Key from settings
def load_chatgpt_api_key(line):
    global CHATGPT_API_KEY
    value = line.split(":", 1)[1].strip()
    try:
        if len(value) >= 20 and not any(char in value for char in [' ', '\t', '\n']):
            CHATGPT_API_KEY = value
            openai.api_key = value
            print("INFO: Loaded ChatGPT API Key")
            return True
        else:
            print(f"ERROR: Invalid ChatGPT API key format.\nERROR 118")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse ChatGPT API key: {e}\nERROR 119")
        return False

# Load Claude API Key from settings
def load_claude_api_key(line):
    global CLAUDE_API_KEY
    value = line.split(":", 1)[1].strip()
    try:
        if len(value) >= 20 and not any(char in value for char in [' ', '\t', '\n']):
            CLAUDE_API_KEY = value
            print("INFO: Loaded Claude API Key")
            return True
        else:
            print(f"ERROR: Invalid Claude API key format.\nERROR 121")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse Claude API key: {e}\nERROR 122")
        return False

def load_settings():
    global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY
    success_count = 0
    total_settings = 6
    
    try:
        with open(get_source_path("settings"), "r") as f:
            lines = f.readlines()
            
        if not lines:
            print("WARNING: Settings file is empty, using default configurations.\n    -preference: gemini, chatgpt, claude" \
            "\n    -wake_word: computer" \
            "\n    -timeout: 15" \
            "\n    -gemini_api_key: [empty]" \
            "\n    -chatgpt_api_key: [empty]" \
            "\n    -claude_api_key: [empty]" \
            "\nWARN 313")
            return False
            
        for line in lines:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
                
            if line.startswith("preference:"):
                if load_preference(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize AI preference.\n    -Falling back to 'gemini, chatgpt, claude'.\nWARN 306")
            elif line.startswith("wake_word:"):
                if load_wake_word(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize wake word.\n    -Falling back to 'computer'.\nWARN 307")
            elif line.startswith("timeout:"):
                if load_timeout(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize API timeout.\n    -Falling back to default 15 seconds.\nWARN 312")
            elif line.startswith("gemini_api_key:"):
                if load_gemini_api_key(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize Gemini API key.\n    -Gemini will not generate responses.\nWARN 303")
            elif line.startswith("chatgpt_api_key:"):
                if load_chatgpt_api_key(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize ChatGPT API key.\n    -ChatGPT will not generate responses.\nWARN 304")
            elif line.startswith("claude_api_key:"):
                if load_claude_api_key(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize Claude API key.\n    -Claude will not generate responses.\nWARN 305")
                    
    except FileNotFoundError:
        print("ERROR: Settings file not found.\nERROR 146")
        return False
    except PermissionError:
        print("ERROR: Permission denied reading settings file.\nERROR 147")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load settings file: {e}\nERROR 148")
        return False
    
    print(f"INFO: Loaded {success_count}/{total_settings} settings successfully")
    return success_count > 0
    return True

def save_settings():
    global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY
    try:
        with open(get_source_path("settings"), "w") as f:
            f.write(f"preference: {AI_PREFERENCE}\n")
            f.write(f"wake_word: {WAKE_WORD}\n")
            f.write(f"timeout: {API_TIMEOUT}\n")
            f.write(f"gemini_api_key: {GEMINI_API_KEY}\n")
            f.write(f"chatgpt_api_key: {CHATGPT_API_KEY}\n")
            f.write(f"claude_api_key: {CLAUDE_API_KEY}\n")
        print("INFO: Saved settings to settings file.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save settings: {e}\nERROR 149")
        return False

# Load API Timemout in seconds from file
def load_api_timeout():
    global API_TIMEOUT
    try:
        with open(get_source_path("api_timeout"), "r") as f:
            timeout_str = f.read().strip()
            timeout = int(timeout_str)
            if timeout > 0:
                API_TIMEOUT = timeout
                print(f"INFO: Loaded API Timeout: {API_TIMEOUT} seconds")
                return True
            else:
                print(f"ERROR: Invalid API timeout in file, using default 15 seconds.\nERROR 143")
                return False
    except FileNotFoundError:
        print(f"ERROR: API timeout file not found, using default 15 seconds.\nERROR 144")
        return False
    except ValueError:
        print(f"ERROR: Invalid API timeout in file, using default 15 seconds.\nERROR 145")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load API timeout: {e}, using default 15 seconds.\nERROR 146")
        return False

# Load Update type from file
def load_update_type():
    global UPDATES
    try:
        with open(get_source_path("updates"), "r") as f:
            update_type = f.read().strip().lower()
            if update_type in ["release", "pre-release"]:
                UPDATES = update_type
                print(f"INFO: Loaded Update Type: {UPDATES}")
                return True
            else:
                print(f"ERROR: Invalid update type in file, using default 'release'.\nERROR 101")
                return False
    except FileNotFoundError:
        print(f"ERROR: Updates file not found, using default 'release'.\nERROR 102")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load update type: {e}, using default 'release'.\nERROR 103")
        return False

# Load App Version from file
def load_app_version():
    global VERSION
    try:
        with open(get_source_path("version"), "r") as f:
            version = f.read().strip()
            if version == "null" or version == "" or version == "none":
                print(f"ERROR: Version not found.\nERROR 104")
                return False
            else:
                VERSION = version
                print(f"INFO: Loaded Version: {VERSION}")
                return True
    except FileNotFoundError:
        print(f"ERROR: Version file not found.\nERROR 105")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load version: {e}\nERROR 106")
        return False

# Load Operating System Version from file
def load_os_version():
    global OS_VERSION
    try:
        with open(get_source_path("os_version"), "r") as f:
            version = f.read().strip().lower()
            if version == "null" or version == "" or version == "none" or version == "auto-detect":
                OS_VERSION = detect_os()
                print(f"INFO: Auto-detected OS: {OS_VERSION}")
                return True
            else:
                OS_VERSION = version
                print(f"INFO: Loaded OS Version: {OS_VERSION}")
                return True
    except FileNotFoundError:
        OS_VERSION = detect_os()
        print(f"ERROR: OS version file not found, auto-detected: {OS_VERSION}\nERROR 107")
        return False
    except Exception as e:
        OS_VERSION = detect_os()
        print(f"ERROR: Failed to load OS version: {e}, auto-detected: {OS_VERSION}\nERROR 108")
        return False

# Load Inital Prompt for AI from file
def load_initial_prompt():
    try:
        with open(get_source_path("initial_prompt"), "r") as f:
            lines = f.readlines()
            global INITIAL_PROMPT
            prompt_content = "".join(lines).strip()

            # Validate prompt content
            if len(prompt_content) == 0:
                print("ERROR: Initial prompt file is empty.\nERROR 124")
            else:
                INITIAL_PROMPT = prompt_content
        return True
    except FileNotFoundError:
        print("ERROR: Initial prompt file not found.\nERROR 125")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load initial prompt: {e}\nERROR 126")
        return False

# Load Prompt for AI from file
def load_prompt():
    try:
        with open(get_source_path("prompt"), "r") as f:
            lines = f.readlines()
            global PROMPT
            prompt_content = "".join(lines).strip()
            
            # Validate prompt content
            if len(prompt_content) == 0:
                print("ERROR: Prompt file is empty.\nERROR 124")
            else:
                PROMPT = prompt_content
        return True
    except FileNotFoundError:
        print("ERROR: Prompt file not found.\nERROR 125")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load prompt: {e}\nERROR 126")
        return False

# File Path Finder
def get_source_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# Generate Text using AI
def generate_text(input_prompt):
    ai_models = [model.strip().lower() for model in AI_PREFERENCE.split(",")]
    
    for i, model in enumerate(ai_models):
        print(f"INFO: Attempting to generate text using {model.upper()}...")
        
        if model == "gemini":
            if not GEMINI_API_KEY:
                print(f"WARNING: Gemini API key not available, trying next AI model...")
                continue
            result = gemini_generate(input_prompt)
        elif model == "chatgpt":
            if not CHATGPT_API_KEY:
                print(f"WARNING: ChatGPT API key not available, trying next AI model...")
                continue
            result = chatgpt_generate(input_prompt)
        elif model == "claude":
            if not CLAUDE_API_KEY:
                print(f"WARNING: Claude API key not available, trying next AI model...")
                continue
            result = claude_generate(input_prompt)
        else:
            print(f"Using local AI model: {model}")
            print(f"If no local models are installed, this means something went wrong calling the others.")
            result = local_generate(input_prompt, model)
        
        # If we got a successful result, return it
        if result is not None and result.strip():
            print(f"INFO: Successfully generated text using {model.upper()}")
            return result
        else:
            print(f"WARNING: {model.upper()} failed to generate text, trying next AI model...")
    
    # If we've exhausted all AI models without success
    print("ERROR: All AI models failed to generate text.\nERROR 127")
    show_failure_notification("ERROR 127: All AI models failed to generate text.")
    return "ERROR: All AI models failed to generate text."

def local_generate(input_prompt, model_name):
    result = {"text": None}
    timeout_triggered = threading.Event()

    def local_call():
        if timeout_triggered.is_set():
            return
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": model_name, "prompt": input_prompt},
                timeout=(API_TIMEOUT, None),
                stream=True
            )
            if response.ok:
                reply = ""
                for line in response.iter_lines():
                    if not line:
                        continue
                    obj = json.loads(line.decode("utf-8"))
                    if "response" in obj:
                        reply += obj["response"]
                    if obj.get("done"):
                        break
                if reply and not timeout_triggered.is_set():
                    result["text"] = reply
            print(reply)
        except Exception as e:
            if not timeout_triggered.is_set():
                print(f"ERROR: Failed to generate text with local model '{model_name}': {e}\nERROR 137")
    
    def fallback():
        timeout_triggered.set()
        print(f"ERROR: Local model '{model_name}' API Timeout.\nERROR 149")

    thread = threading.Thread(target=local_call)
    thread.start()

    timer = threading.Timer(API_TIMEOUT, fallback)
    timer.start()

    while result["text"] is None and not timeout_triggered.is_set():
        thread.join(timeout=0.1)

    timer.cancel()

    if thread.is_alive():
        thread.join(timeout=1)

    return result["text"]
 
def chatgpt_generate(input_prompt):
    result = {"text": None}
    timeout_triggered = threading.Event()

    def chatgpt_call():
        if timeout_triggered.is_set():
            return
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": input_prompt}
                ]
            )
            reply = response.choices[0].message.content
            if not timeout_triggered.is_set() and reply:
                result["text"] = reply.strip()
        except Exception as e:
            if not timeout_triggered.is_set():
                print(f"ERROR: Failed to generate text with ChatGPT: {e}\nERROR 128")
    
    def fallback():
        timeout_triggered.set()
        print("ERROR: ChatGPT API Timeout.\nERROR 129")

    # Start ChatGPT call
    thread = threading.Thread(target=chatgpt_call)
    thread.start()

    # Start timer
    timer = threading.Timer(API_TIMEOUT, fallback)
    timer.start()

    # Check for result or timeout
    while result["text"] is None and not timeout_triggered.is_set():
        thread.join(timeout=0.1)

    timer.cancel()
    
    # Wait for thread to complete if it's still running
    if thread.is_alive():
        thread.join(timeout=1)
    
    return result["text"]

def claude_generate(input_prompt):
    result = {"text": None}
    timeout_triggered = threading.Event()

    def claude_call():
        if timeout_triggered.is_set():
            return
        try:
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            response = client.messages.create(
                model="claude-3-haiku-20240922",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": input_prompt}
                ]
            )
            reply = response.content[0].text
            if not timeout_triggered.is_set() and reply:
                result["text"] = reply.strip()
        except Exception as e:
            if not timeout_triggered.is_set():
                print(f"ERROR: Failed to generate text with Claude: {e}\nERROR 137")

    def fallback():
        timeout_triggered.set()
        print("ERROR: Claude API Timeout.\nERROR 131")

    # Start Claude call
    thread = threading.Thread(target=claude_call)
    thread.start()

    # Start timer
    timer = threading.Timer(API_TIMEOUT, fallback)
    timer.start()

    # Check for result or timeout
    while result["text"] is None and not timeout_triggered.is_set():
        thread.join(timeout=0.1)

    timer.cancel()
    
    # Wait for thread to complete if it's still running
    if thread.is_alive():
        thread.join(timeout=1)
    
    return result["text"]

# Generate Text With Gemini
def gemini_generate(input_prompt):
    result = {"text": None}
    timeout_triggered = threading.Event()

    def gemini_call():
        if timeout_triggered.is_set():
            return
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(input_prompt)
            if not timeout_triggered.is_set() and response.text:
                result["text"] = response.text.strip()
        except Exception as e:
            if not timeout_triggered.is_set():
                print(f"ERROR: Failed to generate text with Gemini: {e}\nERROR 132")
    
    def fallback():
        timeout_triggered.set()
        print("ERROR: Gemini API Timeout.\nERROR 133")

    # Start Gemini call
    thread = threading.Thread(target=gemini_call)
    thread.start()

    # Start timer
    timer = threading.Timer(API_TIMEOUT, fallback)
    timer.start()

    # Check for result or timeout
    while result["text"] is None and not timeout_triggered.is_set():
        thread.join(timeout=0.1)

    timer.cancel()
    
    # Wait for thread to complete if it's still running
    if thread.is_alive():
        thread.join(timeout=1)
    
    return result["text"]

# Listen for Wake Word
def listen_for_wake_word():
    global vosk_rec, audio_stream
    
    print(f"INFO: Listening for wake word ('{WAKE_WORD}')...")

    last_heartbeat = time.time()
    while not STOP_EVENT.is_set():
        try:
            current_time = time.time()
            if current_time - last_heartbeat >= 5:
                print("INFO: Voice thread running and listening")
                last_heartbeat = current_time

            data = audio_stream.read(4096, exception_on_overflow=False)
            if vosk_rec.AcceptWaveform(data):
                result = json.loads(vosk_rec.Result())
                text = result.get('text', '').lower()
                if text:
                    print(f"INFO: Heard: {text}")
                    if WAKE_WORD in text:
                        print(f"INFO: Wake word detected...")
                        return True
            else:
                partial = json.loads(vosk_rec.PartialResult())
                text = partial.get('partial', '').lower()
                if text and WAKE_WORD in text:
                    print(f"INFO: Wake word detected...")
                    return True
        except Exception as e:
            if STOP_EVENT.is_set():
                return False
            print(f"ERROR: Failed to listen for wake word: {e}\nERROR 134")
            time.sleep(0.25)
    return False

# Listen for Command after Wake Word
def listen_for_command():
    global vosk_rec, audio_stream
    
    print(f"INFO: Listening for command...")
    show_activation_indicator(0)
    try:
        vosk_rec.Reset()
        timeout_start = time.time()
        timeout_duration = 10
        
        while time.time() - timeout_start < timeout_duration and not STOP_EVENT.is_set():
            data = audio_stream.read(4096, exception_on_overflow=False)
            if vosk_rec.AcceptWaveform(data):
                result = json.loads(vosk_rec.Result())
                command = result.get('text', '')
                if command.strip():
                    print(f"INFO: Command received: {command}")
                    return command
        
        if STOP_EVENT.is_set():
            return None

        final_result = json.loads(vosk_rec.FinalResult())
        command = final_result.get('text', '')
        if command.strip():
            print(f"INFO: Command received: {command}")
            return command
        else:
            print("INFO: No command detected within timeout.")
            return None
            
    except Exception as e:
        if STOP_EVENT.is_set():
            return None
        print(f"ERROR: Failed to listen for command: {e}\nERROR 135")
        return None
    finally:
        hide_activation_indicator()

# Process Command
def process_command(command):
    if not command:
        print("INFO: No command to process.")
        return
    
    global INITIAL_PROMPT
    global OS_VERSION
    combined_prompt = f"OS: {OS_VERSION}\n\n{INITIAL_PROMPT}\n\nUser Command: {command}"

    print("INFO: Generating response...")
    response = generate_text(combined_prompt)
    if response:
        process_response(response)
    else:
        print("ERROR: No response generated.\nERROR 136")

def process_response(response):
    if not response:
        print("ERROR: No response generated.\nERROR 136")
        return
    
    global LAST_OUTPUT
    
    todo_list = extract_todo_list(response)
    
    # Always show user output first
    user_output = extract_user_output(response)
    if user_output:
        # Store the output in the global variable
        LAST_OUTPUT = user_output
        print(f"\n=== KiloBuddy Output ===\n{user_output}\n========================\n")
        show_overlay(user_output)
    
    if todo_list:
        print(f"INFO: Found {len(todo_list)} todo items")
        process_todo_list(todo_list)
    else:
        print("INFO: No todo list found in response.")
    return

# Extract the todo list from AI response
def extract_todo_list(response):
    # More flexible regex pattern - allows variable spacing
    task_pattern = re.compile(r"\[(\d+)\]\s+(.+?)\s+#\s+(USER|AI)\s+---\s+(DONE|DO NEXT|PENDING|SKIPPED)")
    matches = task_pattern.findall(response)
    
    return matches

# Extract output for the user from AI response
def extract_user_output(response):
    output_pattern = re.search(r'"""(.*?)"""', response, re.DOTALL)
    if output_pattern:
        return output_pattern.group(1).strip()
    return None

# Interprets the todo list and decides on user or AI call
def process_todo_list(todo_list):
    # Check if there's a DO NEXT task, if not, promote the first PENDING task
    has_do_next = any(status == "DO NEXT" for _, _, _, status in todo_list)
    if not has_do_next:
        for i, (step_num, command, executor, status) in enumerate(todo_list):
            if status == "PENDING":
                todo_list[i] = (step_num, command, executor, "DO NEXT")
                print(f"INFO: Auto-promoted task {step_num} to DO NEXT")
                break
    
    for i, (step_num, command, executor, status) in enumerate(todo_list):
        if status == "DO NEXT":
            if executor == "USER":
                user_call(command)
                update_status(todo_list, i)
                continue
            elif executor == "AI":
                print(f"INFO: Requesting AI command: {command}")
                ai_call(todo_list)
                break

# Update the status of a task in the todo list
def update_status(todo_list, current_step):
    step_num, command, executor, status = todo_list[current_step]
    todo_list[current_step] = (step_num, command, executor, "DONE")

    if current_step + 1 < len(todo_list):
        next_step_num, next_command, next_executor, next_status = todo_list[current_step + 1]
        if next_status == "PENDING":
            todo_list[current_step + 1] = (next_step_num, next_command, next_executor, "DO NEXT")

# USER Call Subprocess
def user_call(command):
    global PREVIOUS_COMMAND_OUTPUT, LAST_OUTPUT, OS_VERSION
    
    # Replace $LAST_OUTPUT with the actual Gemini output
    if "$LAST_OUTPUT" in command:
        command = command.replace("$LAST_OUTPUT", LAST_OUTPUT)
        print(f"INFO: Substituted $LAST_OUTPUT in command")
    
    # Check for dangerous commands
    if any(dangerous in command.lower() for dangerous in DANGEROUS_COMMANDS):
        print("WARNING: Dangerous command detected. Prompting for administrator confirmation.")
        
        if OS_VERSION.startswith("linux"):
            try:
                print("INFO: Using pkexec for administrator authentication...")
                
                actual_user = os.environ.get('USER') or os.environ.get('USERNAME')
                if actual_user and actual_user != 'root':
                    user_home = f"/home/{actual_user}"
                    expanded_command = command.replace("~/", f"{user_home}/")
                else:
                    expanded_command = command
                
                result = subprocess.run(["pkexec", "bash", "-c", expanded_command], capture_output=True, text=True, timeout=45)
                if result.returncode == 0:
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                else:
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                return
            except subprocess.TimeoutExpired:
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                return
            except Exception as e:
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}\nERROR 141")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                return
        
        elif OS_VERSION.startswith("darwin"):
            try:
                print("INFO: Using sudo for administrator authentication...")
                
                actual_user = os.environ.get('USER') or os.environ.get('USERNAME')
                if actual_user and actual_user != 'root':
                    user_home = f"/Users/{actual_user}"
                    expanded_command = command.replace("~/", f"{user_home}/")
                else:
                    expanded_command = command
                
                result = subprocess.run(["sudo", "bash", "-c", expanded_command], capture_output=True, text=True, timeout=45)
                if result.returncode == 0:
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                else:
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                return
            except subprocess.TimeoutExpired:
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                return
            except Exception as e:
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                return
        
        elif OS_VERSION.startswith("windows"):
            try:
                print("INFO: Using PowerShell with -Verb RunAs for administrator authentication...")
                
                actual_user = os.environ.get('USERNAME')
                if actual_user:
                    user_profile = f"C:\\Users\\{actual_user}"
                    expanded_command = command.replace("%USERPROFILE%", user_profile)
                else:
                    expanded_command = command
                
                ps_command = f'Start-Process -FilePath "cmd" -ArgumentList "/c {expanded_command}" -Verb RunAs -Wait -PassThru'
                result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=45)
                if result.returncode == 0:
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                else:
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                return
            except subprocess.TimeoutExpired:
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                return
            except Exception as e:
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                return
        
        else:
            print("WARNING: Unknown operating system. Running dangerous command without elevation.")
    
    print(f"INFO: Running USER command: {command}")
    result = subprocess.run(command, shell=True, timeout=45, capture_output=True, text=True)
    PREVIOUS_COMMAND_OUTPUT = result.stdout

# AI Call Method
def ai_call(task_list):
    global OS_VERSION, PROMPT, PREVIOUS_COMMAND_OUTPUT
    combined_prompt = f"OS: {OS_VERSION}\n\n{PROMPT}\n\nPrevious Command Output:\n{PREVIOUS_COMMAND_OUTPUT}\n\nTodo List:\n{format_todo_list(task_list)}\n\nThis is a continuation of a previous task. Continue the task list by fulfilling the task marked 'DO NEXT'."
    print("INFO: Generating response...")
    response_text = generate_text(combined_prompt)
    process_response(response_text)

# Formats parsed todo list back into string
def format_todo_list(todo_list):
    lines = [">>"]
    for step_num, command, executor, status in todo_list:
        lines.append(f"[{step_num}] {command} # {executor} --- {status}")
    lines.append("<<")
    return "\n".join(lines)

# Show overlay for AI output designated for user
def show_overlay(text):
    def open_overlay():
        root = tk.Tk()
        root.title("KiloBuddy")
        
        # Load StackSans font or fallback to Helvetica
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            light_font_path = os.path.join(base_dir, "StackSansText-Light.ttf")
            
            if os.path.exists(light_font_path):
                overlay_font = ("StackSans Text Light", 14)
            else:
                overlay_font = ("Helvetica", 14)
        except Exception:
            overlay_font = ("Helvetica", 14)
        
        # Set window icon if icon.png exists
        if os.path.exists("icon.png"):
            try:
                root.iconphoto(False, tk.PhotoImage(file="icon.png"))
            except Exception:
                pass  # If icon fails to load, continue without it
        
        root.attributes("-topmost", True)
        root.overrideredirect(True)
        root.configure(bg="#131313")
        root.lift()
        root.attributes("-alpha", 0.85)
        
        char_width = 24
        line_height = 40
        max_width = 800
        max_height = 600
        padding = 20

        max_line_chars = max(len(line) for line in text.split("\n"))
        ideal_width = min(max_line_chars * char_width + padding, max_width)
        chars_per_line = max(1, (ideal_width - padding) // char_width)
        total_lines = sum(max(1, (len(line) + chars_per_line - 1) // chars_per_line) for line in text.split("\n"))
        ideal_height = min(total_lines * line_height + padding, max_height)
        
        root.geometry(f"{int(ideal_width)}x{int(ideal_height)}+100+100")
        
        frame = tk.Frame(root, bg="#131313", relief=tk.FLAT, borderwidth=0)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text_widget = tk.Text(frame, 
                             font=overlay_font, 
                             fg="white", 
                             bg="#131313", 
                             wrap=tk.WORD,
                             selectbackground="#195cba",
                             selectforeground="white",
                             insertbackground="white",
                             relief=tk.FLAT,
                             borderwidth=1,
                             highlightthickness=0)
        
        needs_scrollbar = ideal_height >= max_height
        
        if needs_scrollbar:
            scrollbar = tk.Scrollbar(frame, command=text_widget.yview, bg="#131313", troughcolor="#ffffff", 
                                    relief=tk.FLAT, borderwidth=0, highlightthickness=0)
            text_widget.config(yscrollcommand=scrollbar.set)
            
            text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        else:
            text_widget.pack(fill=tk.BOTH, expand=True)
        
        text_widget.insert(tk.END, text)
        text_widget.config(state=tk.DISABLED)
        
        def close_overlay(event=None):
            root.destroy()
        
        # Double-click to close
        text_widget.bind("<Double-Button-1>", close_overlay)
        root.bind("<Escape>", close_overlay)
        
        root.after(len(text) * 15 + 5000, root.destroy)
        root.mainloop()

    threading.Thread(target=open_overlay).start()


ACTIVE_OVERLAY = {
    "window": None,
    "lock": threading.Lock()
}


def show_activation_indicator(duration=2600):
    if DASHBOARD_ROOT is None:
        return

    def create_indicator():
        with ACTIVE_OVERLAY["lock"]:
            if ACTIVE_OVERLAY["window"] is not None:
                return

        overlay = tk.Toplevel(DASHBOARD_ROOT)
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.86)

        width = 290
        height = 70
        overlay.geometry(f"{width}x{height}+18+18")
        overlay.configure(bg="#131313")

        frame = tk.Frame(overlay, bg="#131313", relief=tk.FLAT, borderwidth=0)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        canvas = tk.Canvas(frame, width=width - 10, height=height - 10, bg="#131313", highlightthickness=0, bd=0)
        canvas.pack(fill="both", expand=True)

        canvas.create_text(14, 18, anchor="nw", text="Listening", fill="#FFFFFF", font=("Helvetica", 12, "bold"))

        dot_centers = [width - 100, width - 72, width - 44]
        for cx in dot_centers:
            canvas.create_oval(cx - 7, height // 2 - 12, cx + 7, height // 2 + 6, fill="#4FA4FF", outline="")

        def close_indicator(event=None):
            hide_activation_indicator()

        overlay.bind("<Button-1>", close_indicator)
        overlay.bind("<Escape>", close_indicator)

        with ACTIVE_OVERLAY["lock"]:
            ACTIVE_OVERLAY["window"] = overlay

        if duration > 0:
            overlay.after(duration, hide_activation_indicator)

    DASHBOARD_ROOT.after(0, create_indicator)


def hide_activation_indicator():
    if DASHBOARD_ROOT is None:
        return

    def destroy_indicator():
        with ACTIVE_OVERLAY["lock"]:
            window = ACTIVE_OVERLAY.get("window")
            if window is not None and window.winfo_exists():
                try:
                    window.destroy()
                except:
                    pass
            ACTIVE_OVERLAY["window"] = None

    DASHBOARD_ROOT.after(0, destroy_indicator)

# Dashboard for KiloBuddy
class KiloBuddyDashboard:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.background_color = "#0B3147"
        self.frame_color = "#1D4E89"
        self.border_color = "#2E86C1"
        
        # Load StackSans fonts
        self.load_custom_fonts()
        
        # Font size variables
        self.status_font_size = 28
        self.button_font_size = 28
        self.header_font_size = 38
        self.text_font_size = 28
        self.input_font_size = 28

        global DASHBOARD_ROOT
        self.root = ctk.CTk()
        DASHBOARD_ROOT = self.root
        self.root.title("KiloBuddy")
        self.root.geometry("1000x800")
        self.root.minsize(900, 650)
        self.root.resizable(True, True)
        self.root.configure(fg_color=self.background_color)
        self.root.protocol("WM_DELETE_WINDOW", self.close_dashboard)

        if os.path.exists("icon.png"):
            try:
                self.root.iconphoto(False, tk.PhotoImage(file="icon.png"))
            except Exception:
                pass
        
        self.setup_ui()
    
    def load_custom_fonts(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Load StackSans Light for normal text
            light_font_path = os.path.join(base_dir, "StackSansText-Light.ttf")
            medium_font_path = os.path.join(base_dir, "StackSansText-Medium.ttf")
            
            # Check if font files exist
            if os.path.exists(light_font_path) and os.path.exists(medium_font_path):
                self.stacksans_light_family = "StackSans Text Light"
                self.stacksans_medium_family = "StackSans Text Medium"
                print("INFO: StackSans fonts loaded successfully")
            else:
                # Fallback to system fonts
                self.stacksans_light_family = "Helvetica"
                self.stacksans_medium_family = "Helvetica"
                print("INFO: StackSans fonts not found, using Helvetica fallback")
        except Exception as e:
            # Fallback to system fonts
            self.stacksans_light_family = "Helvetica"
            self.stacksans_medium_family = "Helvetica"
            print(f"INFO: Font loading failed: {e}, using Helvetica fallback")
        
    def setup_ui(self):
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        status_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        status_frame.pack(side="left")

        self.status_label = ctk.CTkLabel(status_frame, text="Status:", text_color="white", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.status_font_size))
        self.status_label.pack(side="left", padx=(0, 10))

        self.status_canvas = tk.Canvas(status_frame, width=130, height=34, bg=self.background_color, highlightthickness=0, bd=0)
        self.status_canvas.pack(side="left")

        self.status_lights = {
            "green": self.status_canvas.create_oval(6, 6, 30, 30, fill="#2E7D32", outline=""),
            "yellow": self.status_canvas.create_oval(46, 6, 70, 30, fill="#F9A825", outline=""),
            "red": self.status_canvas.create_oval(86, 6, 110, 30, fill="#C62828", outline="")
        }

        self.set_status_lights("waiting")

        quit_btn = ctk.CTkButton(button_frame, text="Stop KB", command=self.quit_kilobuddy, fg_color="#f44336", hover_color="#d32f2f", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.button_font_size), width=100, height=35)
        quit_btn.pack(side="right")

        settings_btn = ctk.CTkButton(button_frame, text="Settings", command=self.open_settings_window, fg_color="#607d8b", hover_color="#546e7a", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.button_font_size), width=120, height=35)
        settings_btn.pack(side="right", padx=(0, 10))

        output_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        output_frame.pack(fill="both", expand=True, padx=20, pady=10)

        text_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.output_text = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(family=self.stacksans_light_family, size=self.text_font_size), fg_color=self.background_color, text_color="white", corner_radius=10, height=300)
        self.output_text.pack(fill="both", expand=True)

        self.update_output_display()

        input_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=15, pady=15)

        self.command_entry = ctk.CTkEntry(input_container, font=ctk.CTkFont(family=self.stacksans_light_family, size=self.input_font_size), fg_color=self.background_color, text_color="white", placeholder_text="Enter Command...", placeholder_text_color="#888888", corner_radius=10, height=40)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        send_btn = ctk.CTkButton(input_container, text="Send", command=self.send_command, fg_color="#2196F3", hover_color="#1976D2", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.input_font_size), width=100, height=40, corner_radius=10)
        send_btn.pack(side="right")
        
        self.command_entry.bind('<Return>', lambda event: self.send_command())
        
    def open_settings_window(self):
        try:
            settings_window = ctk.CTkToplevel(self.root)
            settings_window.title("KiloBuddy Settings")
            settings_window.geometry("620x870")
            settings_window.configure(fg_color="#0B3147")
            settings_window.transient(self.root)
            settings_window.lift()
            settings_window.update_idletasks()

            header = ctk.CTkLabel(settings_window, text="Settings", font=ctk.CTkFont(family=self.stacksans_medium_family, size=28), text_color="white")
            header.pack(padx=20, pady=(20, 10), anchor="w")

            form_frame = ctk.CTkFrame(settings_window, fg_color="#142A44", corner_radius=15)
            form_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

            def make_label(entry_text):
                return ctk.CTkLabel(form_frame, text=entry_text, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), text_color="white")

            pref_label = make_label("AI Provider Preference")
            pref_label.pack(anchor="w", padx=20, pady=(20, 4))
            pref_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="gemini, chatgpt, claude")
            pref_entry.insert(0, AI_PREFERENCE)
            pref_entry.pack(padx=20, pady=(0, 10))

            wake_label = make_label("Wake Word")
            wake_label.pack(anchor="w", padx=20, pady=(10, 4))
            wake_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="computer")
            wake_entry.insert(0, WAKE_WORD)
            wake_entry.pack(padx=20, pady=(0, 10))

            timeout_label = make_label("API Timeout (seconds)")
            timeout_label.pack(anchor="w", padx=20, pady=(10, 4))
            timeout_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="15")
            timeout_entry.insert(0, str(API_TIMEOUT))
            timeout_entry.pack(padx=20, pady=(0, 10))

            gemini_label = make_label("Gemini API Key")
            gemini_label.pack(anchor="w", padx=20, pady=(10, 4))
            gemini_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="Gemini API Key")
            gemini_entry.insert(0, GEMINI_API_KEY)
            gemini_entry.pack(padx=20, pady=(0, 10))

            chatgpt_label = make_label("ChatGPT API Key")
            chatgpt_label.pack(anchor="w", padx=20, pady=(10, 4))
            chatgpt_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="ChatGPT API Key")
            chatgpt_entry.insert(0, CHATGPT_API_KEY)
            chatgpt_entry.pack(padx=20, pady=(0, 10))

            claude_label = make_label("Claude API Key")
            claude_label.pack(anchor="w", padx=20, pady=(10, 4))
            claude_entry = ctk.CTkEntry(form_frame, width=560, font=ctk.CTkFont(family=self.stacksans_light_family, size=28), fg_color="#0B3147", text_color="white", placeholder_text="Claude API Key")
            claude_entry.insert(0, CLAUDE_API_KEY)
            claude_entry.pack(padx=20, pady=(0, 10))

            status_label = ctk.CTkLabel(form_frame, text="", font=ctk.CTkFont(family=self.stacksans_light_family, size=28), text_color="#FFEE58")
            status_label.pack(anchor="w", padx=20, pady=(10, 0))

            def save_and_close():
                preference_value = pref_entry.get().strip().lower()
                wake_value = wake_entry.get().strip().lower()
                timeout_value = timeout_entry.get().strip()
                gemini_value = gemini_entry.get().strip()
                chatgpt_value = chatgpt_entry.get().strip()
                claude_value = claude_entry.get().strip()

                if not preference_value:
                    status_label.configure(text="AI provider preference may not be empty.")
                    return
                parsed = [item.strip() for item in preference_value.split(",") if item.strip()]
                if not parsed:
                    status_label.configure(text="Provider preference may not be empty.")
                    return

                if len(wake_value) < 2 or not wake_value.isalpha():
                    status_label.configure(text="Wake word must be alphabetic and at least 2 characters.")
                    return

                try:
                    timeout_int = int(timeout_value)
                    if timeout_int < 5 or timeout_int > 120:
                        raise ValueError
                except ValueError:
                    status_label.configure(text="API timeout must be an integer between 5 and 120.")
                    return

                if gemini_value and (" " in gemini_value or len(gemini_value) < 20):
                    status_label.configure(text="Gemini key must be at least 20 chars or blank.")
                    return
                if chatgpt_value and (" " in chatgpt_value or len(chatgpt_value) < 20):
                    status_label.configure(text="ChatGPT key must be at least 20 chars or blank.")
                    return
                if claude_value and (" " in claude_value or len(claude_value) < 20):
                    status_label.configure(text="Claude key must be at least 20 chars or blank.")
                    return

                global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY
                AI_PREFERENCE = ", ".join(parsed)
                WAKE_WORD = wake_value
                API_TIMEOUT = timeout_int
                GEMINI_API_KEY = gemini_value
                CHATGPT_API_KEY = chatgpt_value
                CLAUDE_API_KEY = claude_value

                if save_settings():
                    status_label.configure(text="Settings saved successfully.", text_color="#81C784")
                else:
                    status_label.configure(text="Failed to save settings.", text_color="#EF9A9A")

            button_row = ctk.CTkFrame(settings_window, fg_color="transparent")
            button_row.pack(fill="x", padx=20, pady=(0, 20))

            button_font = ("StackSans Text Light", 28)

            save_btn = ctk.CTkButton(button_row, text="Save", command=save_and_close, fg_color="#4CAF50", hover_color="#43A047", width=120, height=40, font=button_font)
            save_btn.pack(side="right", padx=(0, 10))

            close_btn = ctk.CTkButton(button_row, text="Close", command=settings_window.destroy, fg_color="#666666", hover_color="#555555", width=120, height=40, font=button_font)
            close_btn.pack(side="right")

            settings_window.grab_set()
            settings_window.focus_force()
            settings_window.wait_window()
        except Exception as e:
            print(f"ERROR: Failed to open settings window: {e}")
            try:
                settings_window.destroy()
            except:
                pass

    def update_output_display(self):
        if LAST_OUTPUT:
            self.output_text.delete("0.0", "end")
            self.output_text.insert("0.0", LAST_OUTPUT)
        else:
            self.output_text.delete("0.0", "end")
            self.output_text.insert("0.0", "No response yet. Try sending a command...")
    
    def set_status_lights(self, state):
        inactive = {"green": "#104712", "yellow": "#693609", "red": "#490A0A"}
        active_states = {
            "waiting": {"green": inactive["green"], "yellow": inactive["yellow"], "red": inactive["red"]},
            "processing": {"green": inactive["green"], "yellow": "#FFEB3B", "red": inactive["red"]},
            "complete": {"green": "#4CAF50", "yellow": inactive["yellow"], "red": inactive["red"]},
            "error": {"green": inactive["green"], "yellow": inactive["yellow"], "red": "#F44336"}
        }
        colors = active_states.get(state, active_states["waiting"])
        self.status_canvas.itemconfig(self.status_lights["green"], fill=colors["green"])
        self.status_canvas.itemconfig(self.status_lights["yellow"], fill=colors["yellow"])
        self.status_canvas.itemconfig(self.status_lights["red"], fill=colors["red"])

    def send_command(self):
        command = self.command_entry.get()
        if command and command.strip():
            self.command_entry.delete(0, "end")
            
            self.set_status_lights("processing")
            self.root.update()
            
            import threading
            thread = threading.Thread(target=self.process_command_async, args=(command,))
            thread.daemon = True
            thread.start()
    
    def process_command_async(self, command):
        try:
            process_command(command)
            
            self.root.after(0, lambda: self.set_status_lights("complete"))
            self.root.after(0, self.update_output_with_latest_response)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.root.after(0, self.update_output_with_response, error_msg)
            self.root.after(0, lambda: self.set_status_lights("error"))
    
    def update_output_with_response(self, text):
        global LAST_OUTPUT
        LAST_OUTPUT = text
        
        self.output_text.delete("0.0", "end")
        self.output_text.insert("0.0", text)
    
    def update_output_with_latest_response(self):
        global LAST_OUTPUT
        
        self.output_text.delete("0.0", "end")
        if LAST_OUTPUT:
            self.output_text.insert("0.0", LAST_OUTPUT)
        else:
            self.output_text.insert("0.0", "No response available.")
        
    def quit_kilobuddy(self):
        result = show_custom_confirm(
            "Stop KiloBuddy",
            "Are you sure you want to stop KiloBuddy?\n\nThis will stop the voice assistant and close the dashboard.",
            parent=self.root
        )
        if result:
            request_kilobuddy_stop()
            try:
                self.root.destroy()
            except:
                pass
            try:
                self.root.quit()
            except:
                pass
            sys.exit(0)
    
    def run(self):
        self.root.mainloop()

    def close_dashboard(self):
        try:
            self.root.destroy()
        except:
            pass

def normalize_version(version):
    return version.lower().lstrip('v')

def is_newer_version(current, latest):
    try:
        current_norm = normalize_version(current)
        latest_norm = normalize_version(latest)

        if current_norm != latest_norm:
            return True
        return False
    except:
        return False

def get_kilobuddy_pid():
    lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
    if not os.path.exists(lock_file):
        return None
    try:
        with open(lock_file, "r") as f:
            pid = int(f.read().strip())
            return pid
    except Exception:
        return None


def is_process_running(pid):
    try:
        if platform.system() == "Windows":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if handle == 0:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False


def is_kilobuddy_running():
    pid = get_kilobuddy_pid()
    if pid and is_process_running(pid):
        return True
    cleanup_lock_file()
    return False


def stop_remote_kilobuddy(pid):
    if pid is None or pid == os.getpid():
        return False
    try:
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
        return True
    except Exception:
        return False


def request_kilobuddy_stop():
    pid = get_kilobuddy_pid()
    if pid and pid != os.getpid():
        stopped = stop_remote_kilobuddy(pid)
        if stopped:
            cleanup_lock_file()
        return stopped

    STOP_EVENT.set()
    cleanup_lock_file()
    global audio_stream, VOICE_THREAD
    if audio_stream:
        try:
            if hasattr(audio_stream, 'abort_stream'):
                audio_stream.abort_stream()
        except:
            pass
        try:
            audio_stream.stop_stream()
        except:
            pass
        try:
            audio_stream.close()
        except:
            pass

    if VOICE_THREAD is not None and VOICE_THREAD.is_alive():
        print("INFO: Waiting for voice thread to exit...")
        VOICE_THREAD.join(timeout=3)
        if VOICE_THREAD.is_alive():
            print("INFO: Voice thread did not exit cleanly, forcing process termination.")
            os._exit(0)
    return True


def create_lock_file():
    lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
    with open(lock_file, 'w') as f:
        f.write(str(os.getpid()))

    atexit.register(cleanup_lock_file)

def cleanup_lock_file():
    lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
        except:
            pass


def show_dashboard():
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        StackSans_EL = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-ExtraLight.ttf"), size=9)
        StackSans_L = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-Light.ttf"), size=12)
        StackSans_M = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-Medium.ttf"), size=22)
    except:
        StackSans_EL = ("Arial", 10)
        StackSans_L = ("Arial", 12)
        StackSans_M = ("Arial", 22)
    dashboard = KiloBuddyDashboard()
    dashboard.run()

# Show failure notification popup
def show_failure_notification(message):
    def show_popup():
        try:
            popup = tk.Tk()
            popup.title("KiloBuddy Error")
            popup.geometry("500x200")
            popup.configure(bg="#1e1e1e")
            popup.attributes("-topmost", True)
            popup.resizable(False, False)

            popup.lift()
            popup.focus_force()

            if os.path.exists("icon.png"):
                try:
                    popup.iconphoto(False, tk.PhotoImage(file="icon.png"))
                except:
                    pass

            main_frame = tk.Frame(popup, bg="#1e1e1e", padx=20, pady=20)
            main_frame.pack(fill="both", expand=True)

            title_label = tk.Label(main_frame, text="KiloBuddy Error", 
                                 font=("Arial", 16, "bold"), 
                                 fg="#F44336", bg="#1e1e1e")
            title_label.pack(pady=(0, 10))

            message_label = tk.Label(main_frame, text=message, 
                                  font=("Arial", 11), 
                                  fg="white", bg="#1e1e1e",
                                  justify="center")
            message_label.pack(pady=(0, 20))

            ok_btn = tk.Button(main_frame, text="OK", 
                             command=popup.destroy,
                             bg="#F44336", fg="white", 
                             font=("Arial", 10, "bold"),
                             padx=20, pady=8,
                             relief="flat",
                             cursor="hand2")
            ok_btn.pack(pady=(10, 0))
            
            popup.after(30000, popup.destroy)
            
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")
            
            popup.mainloop()
            
        except Exception as e:
            print(f"ERROR: Couldn't show failure notification: {e}\nERROR 138")

    popup_thread = threading.Thread(target=show_popup)
    popup_thread.daemon = True
    popup_thread.start()


def show_custom_confirm(title, message, parent=None):
    result = {"value": False}
    try:
        dialog = ctk.CTkToplevel(parent) if parent else ctk.CTkToplevel()
        dialog.title(title)
        dialog.geometry("620x320")
        dialog.configure(fg_color="#131a2b")
        dialog.attributes("-topmost", True)
        dialog.resizable(True, True)
        if parent:
            dialog.transient(parent)

        dialog.update_idletasks()
        dialog.lift()
        dialog.focus_force()
        dialog.grab_set()

        text_frame = ctk.CTkFrame(dialog, fg_color="#1f2d4b")
        text_frame.pack(fill="both", expand=True, padx=20, pady=(20, 10))

        message_label = ctk.CTkLabel(text_frame, text=message, wraplength=440, justify="left", text_color="white", font=ctk.CTkFont(size=28))
        message_label.pack(fill="both", expand=True)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))

        def choose_yes():
            result["value"] = True
            dialog.destroy()

        def choose_no():
            dialog.destroy()

        button_font = ("StackSans Text Light", 28)

        yes_btn = ctk.CTkButton(btn_frame, text="Yes", command=choose_yes, fg_color="#4CAF50", hover_color="#43A047", width=100, height=35, font=button_font)
        yes_btn.pack(side="right", padx=(10, 0))

        no_btn = ctk.CTkButton(btn_frame, text="No", command=choose_no, fg_color="#4A6572", hover_color="#3A5068", width=100, height=35, font=button_font)
        no_btn.pack(side="right")

        dialog.protocol("WM_DELETE_WINDOW", choose_no)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        dialog.wait_window()
    except Exception as e:
        print(f"ERROR: Could not show custom confirm dialog: {e}")
        result["value"] = False
    return result["value"]

# Show activation popup when KiloBuddy hears the wake word
def show_update_notification(latest_version, release_type, download_url):
    def show_popup():
        try:
            popup = tk.Tk()
            popup.title("KiloBuddy Update Available")
            popup.geometry("600x300")
            popup.configure(bg="#1e1e1e")
            popup.attributes("-topmost", True)
            popup.resizable(False, False)

            popup.lift()
            popup.focus_force()

            if os.path.exists("icon.png"):
                try:
                    popup.iconphoto(False, tk.PhotoImage(file="icon.png"))
                except:
                    pass

            main_frame = tk.Frame(popup, bg="#1e1e1e", padx=20, pady=20)
            main_frame.pack(fill="both", expand=True)

            title_label = tk.Label(main_frame, text="Update Available", 
                                 font=("Arial", 16, "bold"), 
                                 fg="#4CAF50", bg="#1e1e1e")
            title_label.pack(pady=(0, 10))

            current_label = tk.Label(main_frame, text=f"Current Version: {VERSION}", 
                                   font=("Arial", 11), 
                                   fg="white", bg="#1e1e1e")
            current_label.pack(pady=(0, 5))

            latest_label = tk.Label(main_frame, text=f"Latest Version: {latest_version} ({release_type})", 
                                  font=("Arial", 11, "bold"), 
                                  fg="#2196F3", bg="#1e1e1e")
            latest_label.pack(pady=(0, 15))

            desc_text = f"A new {release_type} is available for download"
            desc_label = tk.Label(main_frame, text=desc_text, 
                                font=("Arial", 10), 
                                fg="#cccccc", bg="#1e1e1e",
                                justify="center")
            desc_label.pack(pady=(0, 20))

            button_frame = tk.Frame(main_frame, bg="#1e1e1e")
            button_frame.pack(pady=(10, 0))
            
            def open_download():
                import webbrowser
                webbrowser.open(download_url)
                popup.destroy()
            
            def remind_later():
                popup.destroy()

            download_btn = tk.Button(button_frame, text="Download Update", 
                                   command=open_download,
                                   bg="#4CAF50", fg="white", 
                                   font=("Arial", 10, "bold"),
                                   padx=20, pady=8,
                                   relief="flat",
                                   cursor="hand2")
            download_btn.pack(side="left", padx=(0, 10))

            later_btn = tk.Button(button_frame, text="Remind Later", 
                                command=remind_later,
                                bg="#666666", fg="white", 
                                font=("Arial", 10),
                                padx=20, pady=8,
                                relief="flat",
                                cursor="hand2")
            later_btn.pack(side="left")
            
            popup.after(30000, popup.destroy)
            
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (popup.winfo_width() // 2)
            y = (popup.winfo_screenheight() // 2) - (popup.winfo_height() // 2)
            popup.geometry(f"+{x}+{y}")
            
            popup.mainloop()
            
        except Exception as e:
            print(f"ERROR: Couldn't show update notification: {e}\nERROR 139")

    popup_thread = threading.Thread(target=show_popup)
    popup_thread.daemon = True
    popup_thread.start()

# Check for updates
def check_for_updates():
    global VERSION
    url = "https://api.github.com/repos/MichaelCreel/KiloBuddy/releases"
    try:
        response = reqs.get(url, timeout=20)
        if response.status_code == 200:
            releases = response.json()
            if releases:
                latest_release = releases[0]
                latest_version = latest_release["tag_name"]
                is_prerelease = latest_release["prerelease"]
                release_type = "pre-release" if is_prerelease else "stable release"
                download_url = latest_release["html_url"]
                
                print(f"INFO: Latest Version: {latest_version} ({release_type}), Current Version: {VERSION}")
                
                if is_newer_version(VERSION, latest_version):
                    if UPDATES == "release" and is_prerelease:
                        print("INFO: Skipping pre-release update.")
                        return None
                    else:
                        print(f"INFO: Update available: {release_type} - {latest_version}")
                        show_update_notification(latest_version, release_type, download_url)
                    
                    return latest_version
                else:
                    print("INFO: Latest version installed.")
                    return None
            else:
                print("WARNING: No releases found on GitHub repository.\nWARN 309")
                return None
        elif response.status_code == 404:
            print("WARNING: No releases found on GitHub repository.\nWARN 309")
            return None
        else:
            print(f"WARNING: Failed to check for updates. Status code: {response.status_code}\nWARN 310")
            return None
    except Exception as e:
        print(f"ERROR: Failed to check for updates: {e}\nERROR 140")
        return None

# Main Method that controls KiloBuddy
def handle_signal(signum, frame):
    print(f"\nINFO: Signal {signum} received, stopping KiloBuddy...")
    request_kilobuddy_stop()
    sys.exit(0)


def main():
    if not initialize():
        print("FATAL: Failed to initialize KiloBuddy. Exiting.\nFATAL 2")
        show_failure_notification("FATAL 2: Failed to initialize KiloBuddy.\n\nThe app will not function and will now stop.")
        return

    print(f"INFO: KiloBuddy successfully started. Say '{WAKE_WORD}' followed by your command.")
    show_overlay(f"KiloBuddy successfully started.\n\nSay '{WAKE_WORD}' to activate.")

    try:
        while is_kilobuddy_running() and not STOP_EVENT.is_set():
            # Start Listening for Wake Word
            if listen_for_wake_word():
                # Start Listening for Command
                command = listen_for_command()
                if command:
                    process_command(command)

                print("INFO: Returning to wake word listening...")
    except KeyboardInterrupt:
        print("\nINFO: KiloBuddy Shutting Down...")
    finally:
        if audio_stream:
            audio_stream.stop_stream()
            audio_stream.close()
        cleanup_lock_file()

def start_voice_listening():
    global VOICE_THREAD
    # Keep the voice thread alive independently of the dashboard window.
    VOICE_THREAD = threading.Thread(target=main, daemon=False)
    VOICE_THREAD.start()
    return VOICE_THREAD

if __name__ == "__main__":
    if is_kilobuddy_running():
        print("INFO: Opening dashboard...")
        show_dashboard()
    else:
        print("INFO: Launching KiloBuddy...")
        create_lock_file()
        
        signal.signal(signal.SIGINT, handle_signal)
        
        # Start voice listening in background thread
        print("INFO: Starting voice assistant in background...")
        start_voice_listening()
        
        # Show dashboard to indicate KiloBuddy is running
        print("INFO: Opening dashboard...")
        show_dashboard()
