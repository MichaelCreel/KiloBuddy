#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import json
import pyaudio
import re
import os
import sys
import platform
import google.generativeai as genai
import threading
import time
import subprocess
import tkinter as tk
from tkinter import messagebox
import tempfile
import atexit
import requests as reqs
import customtkinter as ctk
import openai
import anthropic

API_TIMEOUT = 15 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
CHATGPT_API_KEY = "" # API Key for calling ChatGPT API, loaded from chatgpt_api_key file
CLAUDE_API_KEY = "" # API Key for calling Claude API, loaded from claude_api_key file
AI_PREFERENCE = "gemini, chatgpt, claude" # Preferred order of AI models to call, loaded from ai_preference file
PROMPT = "Return 'Prompt not loaded'." # Prompt for AI API calls, loaded from prompt file
WAKE_WORD = "computer" # Wake word to trigger KiloBuddy listening, loaded from wake_word file
OS_VERSION = "auto-detect" # Operating system version for command generation
PREVIOUS_COMMAND_OUTPUT = "" # Store the previously run USER command output for AI use
LAST_OUTPUT = "No previous output..." # Store the last output by the AI that was designated for the user
VERSION = "v0.0" # The version of KiloBuddy that is running
UPDATES = "release" # The type of updates to check for, "release" or "pre-release"
DANGEROUS_COMMANDS = ["sudo", "rm", "del", "erase", "dd", "diskpart", "format", "shutdown", "reboot", "poweroff", "mkfs", "reg delete", "sysctl -w", "launchctl", "iptables -F", "ufw disable", "netsh"]

# Vosk Speech Recognition Variables
vosk_model = None
vosk_rec = None
audio_stream = None

# Initialize Vosk Speech Recognition
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
    if not load_gemini_api_key():
        print("WARNING: Failed to properly initialize Gemini API key.\n    -Gemini will not generate responses.\nWARN 303")
    if not load_chatgpt_api_key():
        print("WARNING: Failed to properly initialize ChatGPT API key.\n    -ChatGPT will not generate responses.\nWARN 304")
    if not load_claude_api_key():
        print("WARNING: Failed to properly initialize Claude API key.\n    -Claude will not generate responses.\nWARN 305")
    if not load_ai_preference():
        print("WARNING: Failed to properly initialize AI preference.\n    -Falling back to 'gemini, chatgpt, claude'.\nWARN 306")
    if not load_prompt():
        print("FATAL: Failed to properly initialize prompt.\n    -The app will not function and will now stop.\nFATAL 0")
        show_failure_notification("FATAL 0: Failed to properly initialize prompt.\n\nThe app will not function and will now stop.")
        return False
    if not load_wake_word():
        print("WARNING: Failed to .roperly initialize wake word.\n    -Falling back to 'computer'.\nWARN 307")
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

# Load Wake Word from file
def load_wake_word():
    global WAKE_WORD
    try:
        with open(get_source_path("wake_word"), "r") as f:
            word = f.read().strip().lower()
            if word == "null" or word == "" or word == "none":
                print("ERROR: No wake word provided, using default 'computer'.\ERROR 109")
                return False
            else:
                WAKE_WORD = word
                print(f"INFO: Loaded Wake Word: {WAKE_WORD}")
                return True
    except FileNotFoundError:
        print("ERROR: Wake word file not found, using fallback 'computer'.\ERROR 110")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load wake word: {e}, using default 'computer'.\nERROR 111")
        return False

# Load AI Preference
def load_ai_preference():
    global AI_PREFERENCE
    try:
        with open(get_source_path("ai_preference"), "r") as f:
            preference = f.read().strip().lower()
            if preference == "null" or preference == "" or preference == "none":
                print("ERROR: No AI preference provided, using default 'gemini'.\nERROR 112")
                return False
            else:
                AI_PREFERENCE = preference
                print(f"INFO: Loaded AI Preference: {AI_PREFERENCE}")
                return True
    except FileNotFoundError:
        print("ERROR: AI preference file not found, using default 'gemini, chatgpt, claude'.\nERROR 113")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load AI preference: {e}, using default 'gemini, chatgpt, claude'.\nERROR 114")
        return False

# Load API Key for Gemini from file
def load_gemini_api_key():
    global GEMINI_API_KEY
    try:
        with open(get_source_path("gemini_api_key"), "r") as f:
            key = f.read().strip()
            if key == "null" or key == "" or key == "none":
                print("ERROR: No Gemini API key provided.\nERROR 115")
                return False
            else:
                genai.configure(api_key=key)
                GEMINI_API_KEY = key
                print("INFO: Loaded Gemini API Key")
                return True
    except FileNotFoundError:
        print("ERROR: Gemini API key file not found.\nERROR 116")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load Gemini API key: {e}\nERROR 117")
        return False

# Load API Key for ChatGPT from file
def load_chatgpt_api_key():
    global CHATGPT_API_KEY
    try:
        with open(get_source_path("chatgpt_api_key"), "r") as f:
            key = f.read().strip()
            if key == "null" or key == "" or key == "none":
                print("ERROR: No ChatGPT API key provided.\nERROR 118")
                return False
            else:
                openai.api_key = key
                CHATGPT_API_KEY = key
                print("INFO: Loaded ChatGPT API Key")
                return True
    except FileNotFoundError:
        print("ERROR: ChatGPT API key file not found.\nERROR 119")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load ChatGPT API key: {e}\nERROR 120")
        return False

# Load API Key for Claude from file
def load_claude_api_key():
    global CLAUDE_API_KEY
    try:
        with open(get_source_path("claude_api_key"), "r") as f:
            key = f.read().strip()
            if key == "null" or key == "" or key == "none":
                print("ERROR: No Claude API key provided.\nERROR 121")
                return False
            else:
                CLAUDE_API_KEY = key
                print("INFO: Loaded Claude API Key")
                return True
    except FileNotFoundError:
        print("ERROR: Claude API key file not found.\nERROR 122")
        return False
    except Exception as e:
        print(f"ERROR: Failed to load Claude API key: {e}\nERROR 123")
        return False

# Load Prompt for Gemini from file
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

# Generate Text using Gemini
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
            print(f"WARNING: Unrecognized AI model '{model}', trying next AI model...\nWARN 311")
            continue
        
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
                print(f"ERROR: Failed to generate text with Claude: {e}\nERROR 130")

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

    while True:
        try:
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
            print(f"ERROR: Failed to listen for wake word: {e}\nERROR 134")
            time.sleep(0.25)

# Listen for Command after Wake Word
def listen_for_command():
    global vosk_rec, audio_stream
    
    print(f"INFO: Listening for command...")
    
    try:
        vosk_rec.Reset()
        timeout_start = time.time()
        timeout_duration = 10
        
        while time.time() - timeout_start < timeout_duration:
            data = audio_stream.read(4096, exception_on_overflow=False)
            if vosk_rec.AcceptWaveform(data):
                result = json.loads(vosk_rec.Result())
                command = result.get('text', '')
                if command.strip():
                    print(f"INFO: Command received: {command}")
                    return command
        
        final_result = json.loads(vosk_rec.FinalResult())
        command = final_result.get('text', '')
        if command.strip():
            print(f"INFO: Command received: {command}")
            return command
        else:
            print("INFO: No command detected within timeout.")
            return None
            
    except Exception as e:
        print(f"ERROR: Failed to listen for command: {e}\nERROR 135")
        return None

# Process Command
def process_command(command):
    if not command:
        print("INFO: No command to process.")
        return
    
    global PROMPT
    global OS_VERSION
    combined_prompt = f"OS: {OS_VERSION}\n\n{PROMPT}\n\nUser Command: {command}"

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
        
        # Set window icon if icon.png exists
        if os.path.exists("icon.png"):
            try:
                root.iconphoto(False, tk.PhotoImage(file="icon.png"))
            except Exception:
                pass  # If icon fails to load, continue without it
        
        root.attributes("-topmost", True)
        root.overrideredirect(True)
        root.configure(bg="#1e1e1e")
        root.lift()
        root.attributes("-alpha", 0.8)
        
        max_width = 1000
        max_height = 500
        min_width = 1
        min_height = 1
        
        lines = text.split('\n')
        char_width = 8.5
        line_height = 30
        padding = 30
        
        max_line_chars = max(len(line) for line in lines) if lines else 10
        ideal_width = min(max_line_chars * char_width + padding, max_width)
        ideal_width = max(ideal_width, min_width)

        chars_per_line = max(1, int((ideal_width - padding) / char_width))
        total_lines = 0
        
        for line in lines:
            if len(line) == 0:
                total_lines += 1
            else:
                line_wrapped_count = max(1, (len(line) + chars_per_line - 1) // chars_per_line)
                total_lines += line_wrapped_count

        ideal_height = min(total_lines * line_height + padding, max_height)
        ideal_height = max(ideal_height, min_height)  # Minimum reasonable height
        
        root.geometry(f"{int(ideal_width)}x{int(ideal_height)}+100+100")
        
        frame = tk.Frame(root, bg="#1e1e1e", relief=tk.FLAT, borderwidth=0)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        text_widget = tk.Text(frame, 
                             font=("Helvetica", 14), 
                             fg="white", 
                             bg="#2a2a2a", 
                             wrap=tk.WORD,
                             selectbackground="#4a4a4a",
                             selectforeground="white",
                             insertbackground="white",
                             relief=tk.FLAT,
                             borderwidth=1,
                             highlightthickness=0)
        
        needs_scrollbar = ideal_height >= max_height
        
        if needs_scrollbar:
            scrollbar = tk.Scrollbar(frame, command=text_widget.yview, bg="#1e1e1e", troughcolor="#1e1e1e", 
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

# Dashboard for KiloBuddy
class KiloBuddyDashboard:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.background_color = "#0B3147"
        self.frame_color = "#1D4E89"
        self.border_color = "#2E86C1"
        
        # Font size variables
        self.status_font_size = 24
        self.button_font_size = 24
        self.header_font_size = 38
        self.text_font_size = 24
        self.input_font_size = 24

        self.root = ctk.CTk()
        self.root.title("KiloBuddy")
        self.root.geometry("1100x1000")
        self.root.configure(fg_color=self.background_color)

        if os.path.exists("icon.png"):
            try:
                self.root.iconphoto(False, tk.PhotoImage(file="icon.png"))
            except Exception:
                pass
        
        self.setup_ui()
        
    def setup_ui(self):
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=20)

        self.status_label = ctk.CTkLabel(button_frame, text="Status: Waiting...", text_color="#8A8A8A", font=ctk.CTkFont(size=self.status_font_size))
        self.status_label.pack(side="left")

        quit_btn = ctk.CTkButton(button_frame, text="Quit KiloBuddy", command=self.quit_kilobuddy, fg_color="#f44336", hover_color="#d32f2f", font=ctk.CTkFont(size=self.button_font_size), width=140, height=35)
        quit_btn.pack(side="right")

        output_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        output_frame.pack(fill="both", expand=True, padx=20, pady=10)

        header_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=10, padx=15)
        
        response_label = ctk.CTkLabel(header_frame, text="Response", font=ctk.CTkFont(size=self.header_font_size, weight="bold"), text_color="white")
        response_label.pack(side="left")

        text_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.output_text = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(size=self.text_font_size), fg_color=self.background_color, text_color="white", corner_radius=10, height=300)
        self.output_text.pack(fill="both", expand=True)

        self.update_output_display()

        input_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        input_frame.pack(fill="x", padx=20, pady=10)
        
        input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=15, pady=15)

        self.command_entry = ctk.CTkEntry(input_container, font=ctk.CTkFont(size=self.input_font_size), fg_color=self.background_color, text_color="white", placeholder_text="Enter Command...", placeholder_text_color="#888888", corner_radius=10, height=40)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        send_btn = ctk.CTkButton(input_container, text="Send", command=self.send_command, fg_color="#2196F3", hover_color="#1976D2", font=ctk.CTkFont(size=self.input_font_size), width=100, height=40, corner_radius=10)
        send_btn.pack(side="right")
        
        self.command_entry.bind('<Return>', lambda event: self.send_command())
        
    def update_output_display(self):
        if LAST_OUTPUT:
            self.output_text.delete("0.0", "end")
            self.output_text.insert("0.0", LAST_OUTPUT)
        else:
            self.output_text.delete("0.0", "end")
            self.output_text.insert("0.0", "No response yet. Try sending a command...")
    
    def send_command(self):
        command = self.command_entry.get()
        if command and command.strip():
            self.command_entry.delete(0, "end")
            
            self.status_label.configure(text="Status: Processing...", text_color="#FF9800")
            self.root.update()
            
            import threading
            thread = threading.Thread(target=self.process_command_async, args=(command,))
            thread.daemon = True
            thread.start()
    
    def process_command_async(self, command):
        try:
            process_command(command)
            
            self.root.after(0, lambda: self.status_label.configure(text="Status: Complete", text_color="#4CAF50"))
            
            self.root.after(0, self.update_output_with_latest_response)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.root.after(0, self.update_output_with_response, error_msg)
            self.root.after(0, lambda: self.status_label.configure(text="Status: Error", text_color="#F44336"))
    
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
        result = tk.messagebox.askyesno("Quit KiloBuddy", "Are you sure you want to quit KiloBuddy?\n\nThis will stop the voice assistant.")
        if result:
            lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
            if os.path.exists(lock_file):
                try:
                    os.remove(lock_file)
                except:
                    pass

            self.root.destroy()

            os._exit(0)
    
    def run(self):
        self.root.mainloop()

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

def is_kilobuddy_running():
    lock_file = os.path.join(tempfile.gettempdir(), "kilobuddy.lock")
    return os.path.exists(lock_file)

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
    if not initialize():
        print("ERROR: Failed to initialize KiloBuddy.\nERROR 137")
        return
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

# Show update notification popup
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
def main():
    if not initialize():
        print("FATAL: Failed to initialize KiloBuddy. Exiting.\nFATAL 2")
        return

    print(f"INFO: KiloBuddy successfully started. Say '{WAKE_WORD}' followed by your command.")

    try:
        while True:
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

if __name__ == "__main__":
    if is_kilobuddy_running():
        print("INFO: Opening dashboard...")
        show_dashboard()
    else:
        print("INFO: Launching KiloBuddy...")
        create_lock_file()
        main()
