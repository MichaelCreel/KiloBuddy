#!/usr/bin/env python3

import psutil
from vosk import Model, KaldiRecognizer
import json
import sounddevice as sd
import re
import os
import sys
import platform
import signal
import google.genai as genai
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
import shlex
from pathlib import Path
from send2trash import send2trash
import datetime
import shutil
from rapidfuzz import fuzz, process
from collections import deque

# Redefine app identification
if platform.system() == "Windows":
    import ctypes
    myappid = 'mc.kilobuddy.app'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

LOG_PATH = os.path.join(tempfile.gettempdir(), "kilobuddy.log") # Path to log file
MAX_LOG_SIZE = 1 * 1024 * 1024

WAKE_WORD = "computer" # Wake word to trigger KiloBuddy listening, loaded from wake_word file
OS_VERSION = "auto-detect" # Operating system version for command generation
PREVIOUS_COMMAND_OUTPUT = "" # Store the previously run USER command output for AI use
VERSION = "v0.0" # The version of KiloBuddy that is running
UPDATES = "release" # The type of updates to check for, "release", "pre-release", or "none"
MANAGE_OLLAMA = False # Whether to manage Ollama startup and shutdown
OLLAMA_THREAD = None # Thread to track Ollama process if managed
WINDOW_SCALING = 1.0 # Scaling for the windows to match system scaling
DANGEROUS_COMMANDS = ["sudo", "rm", "del", "erase", "dd", "diskpart", "format", "shutdown", "reboot", "poweroff", "mkfs", "reg delete", "sysctl -w", "launchctl", "iptables -F", "ufw disable", "netsh"]

# AI Variables
API_TIMEOUT = 15 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
CHATGPT_API_KEY = "" # API Key for calling ChatGPT API, loaded from chatgpt_api_key file
CLAUDE_API_KEY = "" # API Key for calling Claude API, loaded from claude_api_key file
AI_PREFERENCE = "gemini, chatgpt, claude" # Preferred order of AI models to call, loaded from ai_preference file
PROMPT = "Return 'Prompt not loaded'." # Prompt for AI API calls, loaded from prompt file
INITIAL_PROMPT = "Return 'Initial Prompt not loaded'." # Prompt for initial AI API call, loaded from initial prompt file
USER_INTENT = "" # Store the last user command for AI use
CONVERSATION_HISTORY = None # Store conversation history for better model context
LAST_OUTPUT = "No previous output...\n\nType a task to fulfill below." # Store the last output by the AI that was designated for the user
TOOLS = [ # Tools available for the AI to call
    {
        "type": "function",
        "function": {
            "name": "cr_dir",
            "description": "Create a new directory at a specified path. New directory included in path. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    }
                }
            },
            "required": ["path"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cr_fil",
            "description": "Create a new file at a specified path. New file included in path. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    }
                }
            },
            "required": ["path"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "dl",
            "description": "Send a file or folder to trash. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    }
                }
            },
            "required": ["path"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rd_fil",
            "description": "Read the contents of a file. Supports peeking (none/top/bottom). Automatically truncates as necessary. Automatically calls AI all cases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "peek": {
                        "type": "string", 
                        "default": "none"
                    },
                    "peek_lines": {
                        "type": "integer", 
                        "default": 0 
                    }
                } 
            },
            "required": ["path"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rd_inf",
            "description": "Get information about a file or folder (size/creation/modification/extention/all). Automatically calls AI all cases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "info_type": {
                        "type": "string", 
                        "default": "all"
                    }
                } 
            },
            "required": ["path"]
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mv",
            "description": "Move a file or folder. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "destination": {
                        "type": "string",
                    }
                },
                "required": ["path", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rn",
            "description": "Rename a file or folder. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "new_name": {
                        "type": "string",
                    }
                },
                "required": ["path", "new_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wr_fil",
            "description": "Write or append to a file. Automatically calls AI on failure.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "content": {
                        "type": "string",
                    },
                    "mode": {
                        "type": "string",
                        "default": "write"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ds",
            "description": "Discover files and folders in a path. Returns fuzzy search with score. Automatically calls AI all cases.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                    },
                    "query": {
                        "type": "string",
                        "default": ""
                    }
                },
                "required": ["path", "query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ai_call",
            "description": "Make an additional call to AI. Used for multi-step reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to send to the AI."
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tm_cmd",
            "description": "Execute a terminal command. Does not automatically format for OS or run as Administrator.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    }
                },
                "required": ["command"]
            }
        }
    }
]

# Vosk Speech Recognition Variables
vosk_model = None
vosk_rec = None
audio_stream = None
STOP_EVENT = threading.Event()
VOICE_THREAD = None

# Interface Variables
DASHBOARD_ROOT = None
STATUS_INDICATOR_WINDOW = None
STATUS_CANVAS = None
STATUS_TEXT_ID = None
STATUS_DOT_IDS = []
OVERLAY_QUEUE = deque() # Queue for overlay messages
OVERLAY_ACTIVE = False

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

        audio_stream = sd.RawInputStream(
            samplerate = 16000,
            channels = 1,
            dtype = "int16",
            blocksize = 4096
        )
        audio_stream.start()
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
    if not start_ollama():
        print("WARNING: Failed to start Ollama.\n    -Local models will not function.\nWARN 315")
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

# Starts the Ollama server if managed
def start_ollama():
    global MANAGE_OLLAMA, OLLAMA_THREAD
    if not MANAGE_OLLAMA:
        print("INFO: Ollama management disabled. Startup skipped.")
        return True
    else:
        if ollama_check():
            print("INFO: Ollama is already running, management will be skipped to avoid interference.")
            return True
        else:
            print("INFO: Starting Ollama server and management...")
            OLLAMA_THREAD = subprocess.Popen(["ollama", "serve"])
            return True
    return False

# Check if Ollama is already running
def ollama_check():
    for p in psutil.process_iter(["name"]):
        name = p.info["name"]
        if name and "ollama" in name.lower():
            return True
    return False

# Stop the Ollama server if managed
def stop_ollama():
    global MANAGE_OLLAMA, OLLAMA_THREAD
    if MANAGE_OLLAMA:
        if ollama_check() and OLLAMA_THREAD is not None:
            print("INFO: Stopping Ollama server...")
            OLLAMA_THREAD.terminate()

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
    global GEMINI_API_KEY, GEMINI_CLIENT
    value = line.split(":", 1)[1].strip()
    try:
        if len(value) >= 20 and not any(char in value for char in [' ', '\t', '\n']):
            GEMINI_API_KEY = value
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

# Load Manage Ollama from settings
def load_manage_ollama(line):
    global MANAGE_OLLAMA
    value = line.split(":", 1)[1].strip().lower()
    try:
        if value in ["true", "false"]:
            MANAGE_OLLAMA = (value == "true")
            print(f"INFO: Loaded Manage Ollama: {MANAGE_OLLAMA}")
            return True
        else:
            print(f"ERROR: Invalid manage_ollama value '{value}' (must be 'true' or 'false')\nERROR 110")
            return False
    except Exception as e:
        print(f"ERROR: Failed to parse manage_ollama setting: {e}\nERROR 113")
        return False

def load_settings():
    global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY, MANAGE_OLLAMA
    success_count = 0
    total_settings = 7

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
            "\n    -manage_ollama: false" \
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
            elif line.startswith("manage_ollama:"):
                if load_manage_ollama(line):
                    success_count += 1
                else:
                    print("WARNING: Failed to properly initialize manage_ollama setting.\n    -Falling back to default 'false'.\nWARN 314")
                    
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
    global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY, MANAGE_OLLAMA, UPDATES
    try:
        with open(get_source_path("settings"), "w") as f:
            f.write(f"preference: {AI_PREFERENCE}\n")
            f.write(f"wake_word: {WAKE_WORD}\n")
            f.write(f"timeout: {API_TIMEOUT}\n")
            f.write(f"gemini_api_key: {GEMINI_API_KEY}\n")
            f.write(f"chatgpt_api_key: {CHATGPT_API_KEY}\n")
            f.write(f"claude_api_key: {CLAUDE_API_KEY}\n")
            f.write(f"manage_ollama: {MANAGE_OLLAMA}\n")
        with open(get_source_path("updates"), "w") as f:
            f.write(f"{UPDATES}\n")
        print("INFO: Successfully saved settings.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save settings: {e}\nERROR 120")
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
            if update_type in ["release", "pre-release", "none"]:
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
                return False
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
                json={
                    "model": model_name,
                    "prompt": input_prompt,
                    "options": {
                        "temperature": 0.5,
                    }
                },
                timeout=(API_TIMEOUT, API_TIMEOUT),
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
            client = genai.Client(api_key=GEMINI_API_KEY)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=input_prompt
            )

            text = response.text

            if not timeout_triggered.is_set() and response:
                result["text"] = text.strip()
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

    while not STOP_EVENT.is_set():
        try:
            data, overflow = audio_stream.read(4096)
            if vosk_rec.AcceptWaveform(bytes(data)):
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
    show_status_indicator("Listening")
    try:
        vosk_rec.Reset()
        timeout_start = time.time()
        timeout_duration = 3.5
        last_speech_time = time.time()
        accepted_text = ""
        full_command = ""

        while time.time() - last_speech_time < timeout_duration and not STOP_EVENT.is_set():
            data, overflow = audio_stream.read(4096)
            if vosk_rec.AcceptWaveform(bytes(data)):
                result = json.loads(vosk_rec.Result()).get('text', '')
                if result:
                    accepted_text = result.strip()
                    full_command += " " + accepted_text
                    last_speech_time = time.time()
            else:
                partial = json.loads(vosk_rec.PartialResult()).get("partial", "")
                # Only treat partial as speech if it contains alphabetic characters
                if any(c.isalpha() for c in partial):
                    last_speech_time = time.time()
        
        if STOP_EVENT.is_set():
            return None

        command = full_command
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
        hide_status_indicator()

# Process Command (OLD)
def process_command_old(command):
    if not command:
        print("INFO: No command to process.")
        return

    global USER_INTENT
    USER_INTENT = command
    CONVERSATION_HISTORY.add_message("USER", command)

    global INITIAL_PROMPT, OS_VERSION
    combined_prompt = f"OS: {OS_VERSION}\nDEFAULT PATH: {Path.home() / 'Desktop'}\nConversation History:\n{CONVERSATION_HISTORY.get_formatted_history()}\n{INITIAL_PROMPT}\nUser Command: {command}"

    print("INFO: Generating response...")
    show_status_indicator("Processing", "#00FF22")
    response = generate_text(combined_prompt)
    if response:
        hide_status_indicator()
        process_response(response)
    else:
        hide_status_indicator()
        print("ERROR: No response generated.\nERROR 136")

# Process Command
def process_command(command):
    if not command:
        print("INFO: No command to process.")
        return

    global USER_INTENT, LAST_OUTPUT, CONVERSATION_HISTORY, PREVIOUS_COMMAND_OUTPUT, INITIAL_PROMPT, PROMPT, OS_VERSION
    CONVERSATION_HISTORY.add_message("USER", command)

    # Initial call to AI (populates USER_INTENT)
    show_status_indicator("Processing", "#00FF22")
    initial_model_prompt = (
        f"OS: {OS_VERSION}\n"
        f"DEFAULT PATH: {Path.home() / 'Desktop'}\n"
        f"Conversation History:\n{CONVERSATION_HISTORY.get_formatted_history()}\n"
        f"{INITIAL_PROMPT}\n"
        f"User Command: {command}"
    )
    response = generate_text(initial_model_prompt)
    hide_status_indicator()

    # Check if a response was generated
    if response and response != "ERROR: All AI models failed to generate text.":
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        content = message.get("content", "").strip()
    else:
        print("ERROR: No response generated.\nERROR 136")
        return

    # Extract user output
    if content:
        # Extract user intent
        user_intent_match = re.search(r"USER INTENT:\s*(.+)", content)
        if user_intent_match:
            USER_INTENT = user_intent_match.group(1).strip()

        # Remove user intent from content
        content = re.sub(r"USER INTENT:\s*.+", "", content).strip()

        # Remove leading whitespace
        content = content.lstrip()

        # Add to conversation history
        LAST_OUTPUT = content
        CONVERSATION_HISTORY.add_message("AI", content)

        # Display output
        show_overlay(content)
    else:
        USER_INTENT = command

    # Check for tool calls
    if not tool_calls:
        print("INFO: Initial call completed with no tools.")
        return

    requires_ai_followup = False

    for call in tool_calls:
        show_status_indicator(f"Executing", "#FFB700")
        tool_name = call["function"]["name"]
        tool_args = call["function"]["arguments"]

        tool_output = execute_tool(tool_name, tool_args)
        PREVIOUS_COMMAND_OUTPUT = tool_output
        CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)

        # Check if the tool requires AI follow-up and stop tool execution if so
        if needs_ai_followup(tool_name, tool_output):
            print(f"INFO: {tool_name} failed or requires follow-up. Stopped execution list.")
            requires_ai_followup = True
            hide_status_indicator()
            break

    if not requires_ai_followup:
        print("INFO: All tools executed successfully.")
        hide_status_indicator()
        return

    print("INFO: Follow-up started.")
    max_turns = 50
    turn = 0

    while turn < max_turns:
        turn += 1

        show_status_indicator("Processing", "#00FF22")
        followup_model_prompt = (
            f"OS: {OS_VERSION}\n"
            f"DEFAULT PATH: {Path.home() / 'Desktop'}\n"
            f"Conversation History:\n{CONVERSATION_HISTORY.get_formatted_history()}\n"
            f"{PROMPT}\n"
            f"User Intent: {USER_INTENT}\n"
            f"Previous Command Output: {PREVIOUS_COMMAND_OUTPUT}\n"
        )

        response = generate_text(followup_model_prompt)
        hide_status_indicator()

        # Check if a response was generated
        if response and response != "ERROR: All AI models failed to generate text.":
            message = response.get("message", {})
            tool_calls = message.get("tool_calls", [])
            content = message.get("content", "").strip()
        else:
            print("ERROR: No response generated.\nERROR 136")
            return

        # Extract user output
        if content:
            # Add to conversation history
            LAST_OUTPUT = content
            CONVERSATION_HISTORY.add_message("AI", content)

            # Display output
            show_overlay(content)

        if not tool_calls:
            print("INFO: Follow-up completed with no tools.")
            break

        requires_ai_followup = False
        for call in tool_calls:
            show_status_indicator(f"Executing", "#FFB700")
            tool_name = call["function"]["name"]
            tool_args = call["function"]["arguments"]

            tool_output = execute_tool(tool_name, tool_args)
            PREVIOUS_COMMAND_OUTPUT = tool_output
            CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)

            # Check if the tool requires AI follow-up and stop tool execution if so
            if needs_ai_followup(tool_name, tool_output):
                print(f"INFO: {tool_name} failed or requires follow-up. Stopped execution list.")
                requires_ai_followup = True
                hide_status_indicator()
                break

        if not requires_ai_followup:
            print("INFO: All tools executed successfully.")
            hide_status_indicator()
            break

    hide_status_indicator()

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
        CONVERSATION_HISTORY.add_message("AI", LAST_OUTPUT)
        show_overlay(user_output)
    
    if todo_list:
        print(f"INFO: Found {len(todo_list)} todo items")
        process_todo_list(todo_list)
    else:
        print("INFO: No todo list found in response.")


    #############################
    print("DEBUG: User Output: ", user_output)
    print("DEBUG: Todo List: ", todo_list)
    #############################


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

# Checks tool name and output to determine if the tool needs AI follow-up
def needs_ai_followup(tool_name, tool_output):
    if "[[>TOOL_FAIL<]]" in tool_output:
        return True
    if tool_name in ["rd_fil", "rd_inf", "ds"]:
        return True
    return False

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
                tool_name, tool_output = user_call(command)
                update_status(todo_list, i)
                if needs_ai_followup(tool_name, tool_output):
                    print(f"INFO: Tool '{tool_name}' output requires AI follow-up.")
                    ai_call(todo_list)
                    return
                continue
            elif executor == "AI":
                print(f"INFO: Requesting AI command: {command}")
                ai_call(todo_list)
                update_status(todo_list, i)
                return

# Update the status of a task in the todo list
def update_status(todo_list, current_step):
    step_num, command, executor, status = todo_list[current_step]
    todo_list[current_step] = (step_num, command, executor, "DONE")

    if current_step + 1 < len(todo_list):
        next_step_num, next_command, next_executor, next_status = todo_list[current_step + 1]
        if next_status == "PENDING":
            todo_list[current_step + 1] = (next_step_num, next_command, next_executor, "DO NEXT")

# Execute a tool command
def execute_tool(tool_name, args):
    try:
        # Replace variables in the command
        for key, val in args.items():
            if isinstance(val, str) and "$LAST_OUTPUT" in val:
                args[key] = val.replace("$LAST_OUTPUT", LAST_OUTPUT)

        if tool_name == "cr_dir":
            return tool_name, tl_create_directory(args["path"])
        elif tool_name == "cr_fil":
            return tool_name, tl_create_file(args["path"])
        elif tool_name == "dl":
            return tool_name, tl_delete_file(args["path"])
        elif tool_name == "rd_fil":
            path = args["path"]
            peek = args.get("peek", None)
            peek_lines = args.get("peek_lines", 0)
            return tool_name, tl_read_file(path, peek, peek_lines)
        elif tool_name == "rd_inf":
            path = args["path"]
            info_type = args.get("info_type", "all")
            return tool_name, tl_get_info(path, info_type)
        elif tool_name == "mv":
            return tool_name, tl_move(args["source"], args["destination"])
        elif tool_name == "rn":
            return tool_name, tl_rename(args["old_name"], args["new_name"])
        elif tool_name == "wr_fil":
            return tool_name, tl_write_file(args["path"], args["content"], args.get("mode", "write"))
        elif tool_name == "ds":
            return tool_name, tl_discover(args["path"], args.get("pattern", ""))
        #elif tool_name == "ai_call":
        #    return tool_name, tl_ai_call(args["prompt"])
        #elif tool_name == "tm_cmd":
        #    return tool_name, tl_run_command(args["command"])
        else:
            return tool_name, f"[[>TOOL_FAIL<]] Unknown tool: {tool_name}"
    except Exception as e:
        return tool_name, f"[[>TOOL_FAIL<]] Failed to execute tool {tool_name}: {e}"

# Create directory
def tl_create_directory(path):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for directory creation."
    try:
        os.makedirs(path, exist_ok=True)
        return "Successfully created directory."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to create directory: {e}"

# Create file
def tl_create_file(path):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for file creation."
    try:
        if os.path.exists(path):
            if os.path.getsize(path) > 0:
                result = show_custom_confirm(
                    "Overwrite File Contents",
                    f"Are you sure you want to overwrite the existing content of the file?\n\nFile Size: {os.path.getsize(path) / 1024:.2f} KB\nFile Path: {path}",
                    parent=None
                )
                if result:
                    pass
                else:
                    return "[[>TOOL_FAIL<]] Write operation declined by user because of existing content."
        with open(path, "w") as f:
            pass
        return "Successfully created file."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to create file: {e}"

# Delete file or directory (send to trash)
def tl_delete_file(path):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for deletion."
    try:
        if not os.path.exists(path):
            return f"[[>TOOL_FAIL<]] Path {path} does not exist."

        send2trash(path)
        return "Successfully sent to trash."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to send to trash: {e}"

# Read or peek at file content
# Truncates output automatically
# Peek: top/bottom/None
def tl_read_file(path, peek=None, peek_lines=0):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for file reading."
    if not os.path.exists(path):
        return f"[[>TOOL_FAIL<]] Path {path} does not exist."
    if not os.path.isfile(path):
        return f"[[>TOOL_FAIL<]] Path {path} is not a file."
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        if peek is None:
            full_content = "".join(lines)
            return truncate_middle(full_content, 800)
        peek = peek.lower()
        if peek == "none":
            full_content = "".join(lines)
            return truncate_middle(full_content, 800)
        if peek_lines <= 0:
            return "[[>TOOL_FAIL<]] Peek lines must be greater than 0."
        if peek == "top":
            selected = lines[:peek_lines]
            text = "".join(selected)
            return truncate_middle(text, 800)
        elif peek == "bottom":
            selected = lines[-peek_lines:]
            text = "".join(selected)
            return truncate_middle(text, 800)

        return f"[[>TOOL_FAIL<]] Invalid peek mode {peek}. Must be 'top', 'bottom', or None."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to read file: {e}"

# Return file/directory information
def tl_get_info(path, info_type="all"):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for file info."
    if not os.path.exists(path):
        return f"[[>TOOL_FAIL<]] Path {path} does not exist."
    try:
        stats = os.stat(path)

        size = stats.st_size
        created = datetime.datetime.fromtimestamp(stats.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        modified = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        extension = os.path.splitext(path)[1]

        if info_type == "size":
            return f"Size: {size} bytes"
        elif info_type == "create":
            return f"Created: {created}"
        elif info_type == "mod":
            return f"Modified: {modified}"
        elif info_type == "ext":
            return f"Extension: {extension}"
        elif info_type == "all":
            return f"Size: {size} bytes\nCreated: {created}\nModified: {modified}\nExtension: {extension}"
        else:
            return f"[[>TOOL_FAIL<]] Invalid info_type {info_type}. Must be 'size', 'create', 'mod', 'ext', or 'all'."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to get file info: {e}"

# Move a file or directory
def tl_move(path, dest):
    if not path:
        return "[[>TOOL_FAIL<]] No source path provided for move."
    if not dest:
        return "[[>TOOL_FAIL<]] No destination path provided for move."
    if not os.path.exists(path):
        return f"[[>TOOL_FAIL<]] Source path {path} does not exist."
    try:
        dest_dir = os.path.dirname(dest)
        if dest_dir and not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)
        shutil.move(path, dest)
        return "Successfully moved."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to move: {e}"

def tl_rename(path, new_name):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for rename."
    if not new_name:
        return "[[>TOOL_FAIL<]] No new name provided for rename."
    if not os.path.exists(path):
        return f"[[>TOOL_FAIL<]] Path {path} does not exist."

    try:
        directory = os.path.dirname(path)
        dest = os.path.join(directory, new_name)
        return tl_move(path, dest)

    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to rename: {e}"

# Write to a file
def tl_write_file(path, content, mode):
    if not path:
        return "[[>TOOL_FAIL<]] No path provided for writing."
    try:
        if mode.lower() == "write":
            if os.path.exists(path):
                if os.path.getsize(path) > 0:
                    result = show_custom_confirm(
                        "Overwrite File Contents",
                        f"Are you sure you want to overwrite the existing content of the file?\n\nFile Size: {os.path.getsize(path) / 1024:.2f} KB\nFile Path: {path}",
                        parent=None
                    )
                    if result:
                        pass
                    else:
                        return "[[>TOOL_FAIL<]] Write operation declined by user because of existing content."
            with open(path, "w") as f:
                f.write(content)
            return "Successfully wrote to file."
        elif mode.lower() == "append":
            with open(path, "a") as f:
                f.write(content)
            return "Successfully appended to file."
        else:
            return f"[[>TOOL_FAIL<]] Invalid mode {mode}."
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to write to file: {e}"

# Search for files and directories
def tl_discover(search_path, search_query):
    if not search_path:
        return "[[>TOOL_FAIL<]] No search path provided."
    if not search_query:
        return "[[>TOOL_FAIL<]] No search query provided."
    if not os.path.exists(search_path):
        return f"[[>TOOL_FAIL<]] Search path {search_path} does not exist."
    try:
        entries = os.listdir(search_path)
        full_paths = [os.path.join(search_path, entry) for entry in entries]

        matches = process.extract(
            search_query,
            entries,
            scorer = fuzz.WRatio,
            limit = 30
        )

        filtered = [(name, score) for name, score, idx in matches if score >= 65]

        if not filtered:
            return f"[[>TOOL_FAIL<]] No matches found with sufficient score."

        filtered.sort(key=lambda x: x[1], reverse=True)

        return "\n".join(f"{name} (score: {score})" for name, score in filtered)
    except Exception as e:
        return f"[[>TOOL_FAIL<]] Failed to discover files: {e}"

# Strip quotes and commas from a string
def strip_quotes_commas(s):
    s = s.strip()
    if s.endswith(","):
        s = s[:-1].strip()
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s

# Parse a tool command in the format {tool: args}
def parse_tool_call(command):
    command = command.strip()

    if not (command.startswith("{") and command.endswith("}")):
        return None

    inner = command[1:-1].strip()

    if ":" not in inner:
        return None

    tool_name, arg_str = inner.split(":", 1)
    tool_name = tool_name.strip()

    raw_args = [strip_quotes_commas(a) for a in shlex.split(arg_str)]

    return tool_name, raw_args

# Try to execute a tool command and return its output
def try_execute_tool(command):
    parsed = parse_tool_call(command)
    if parsed is None:
        return None

    tool_name, raw_args = parsed
    output = execute_tool(tool_name, raw_args)
    return output, tool_name

# USER Call Subprocess
def user_call(command):
    global PREVIOUS_COMMAND_OUTPUT, LAST_OUTPUT, OS_VERSION
    
    show_status_indicator("Executing", "#00FF22")

    # Replace $LAST_OUTPUT with the actual AI output
    if "$LAST_OUTPUT" in command:
        command = command.replace("$LAST_OUTPUT", LAST_OUTPUT)
        print(f"INFO: Substituted $LAST_OUTPUT in command")

    CONVERSATION_HISTORY.add_message("LCI", command)

    tool_output, tool_name = try_execute_tool(command)
    if tool_output is not None:
        print(f"INFO: Successfully executed tool command: {command}")
        hide_status_indicator()

        PREVIOUS_COMMAND_OUTPUT = tool_output
        CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
        return tool_name, tool_output
    
    # Check for dangerous commands
    tokens = shlex.split(command)
    exe = os.path.basename(tokens[0])
    print(f"INFO: Command found: {exe}")
    print(f"INFO: Attempting command: {command}")
    if exe.lower() in DANGEROUS_COMMANDS:
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
                    hide_status_indicator()
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                else:
                    hide_status_indicator()
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except subprocess.TimeoutExpired:
                hide_status_indicator()
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except Exception as e:
                hide_status_indicator()
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}\nERROR 141")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
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
                    hide_status_indicator()
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                else:
                    hide_status_indicator()
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except subprocess.TimeoutExpired:
                hide_status_indicator()
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except Exception as e:
                hide_status_indicator()
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
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
                    hide_status_indicator()
                    print("INFO: Dangerous command executed successfully with administrator privileges.")
                    PREVIOUS_COMMAND_OUTPUT = result.stdout
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                else:
                    hide_status_indicator()
                    print(f"ERROR: Dangerous command failed or was cancelled. {result.stderr}\nERROR 142")
                    PREVIOUS_COMMAND_OUTPUT = f"Command cancelled or failed: {result.stderr}"
                    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except subprocess.TimeoutExpired:
                hide_status_indicator()
                print("ERROR: Administrator authentication timed out.")
                PREVIOUS_COMMAND_OUTPUT = "Command timed out during authentication"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
            except Exception as e:
                hide_status_indicator()
                print(f"ERROR: Failed to prompt for administrator confirmation: {e}")
                PREVIOUS_COMMAND_OUTPUT = "Failed to authenticate as administrator"
                CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)
                return
        
        else:
            hide_status_indicator()
            print("WARNING: Unknown operating system. Running dangerous command without elevation.")
    
    print(f"INFO: Running USER command: {command}")
    result = subprocess.run(command, shell=True, timeout=45, capture_output=True, text=True)
    hide_status_indicator()
    PREVIOUS_COMMAND_OUTPUT = result.stdout
    CONVERSATION_HISTORY.add_message("LCO", PREVIOUS_COMMAND_OUTPUT)

# Truncate the middle of an input
def truncate_middle(pco, max_length = 800):
    if (len(pco)) <= max_length:
        return pco

    head_length = max_length // 2
    tail_length = max_length - head_length

    head = pco[:head_length]
    tail = pco[-tail_length:]

    return head + " [TRUNCATED] " + tail

# AI Call Method
def ai_call(task_list):
    global OS_VERSION, PROMPT, PREVIOUS_COMMAND_OUTPUT, USER_INTENT
    combined_prompt = f"OS: {OS_VERSION}\nDEFAULT PATH: {Path.home() / 'Desktop'}\nConversation History:\n{CONVERSATION_HISTORY.get_formatted_history()}\n{PROMPT}\nLast Command Output:\n{truncate_middle(PREVIOUS_COMMAND_OUTPUT)}\nUser Intent:{USER_INTENT}\nTodo List:\n{format_todo_list(task_list)}"
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

# Creates the window for AI output designated for user
def display_overlay():
    def open_overlay():
        root = tk.Tk()
        root.title("KiloBuddy")
        
        # Load StackSans font or fallback to Helvetica
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            light_font_path = os.path.join(base_dir, "StackSansText-Light.ttf")
            
            if os.path.exists(light_font_path):
                overlay_font = ("StackSans Text Light", int(14 * WINDOW_SCALING))
            else:
                overlay_font = ("Helvetica", int(14 * WINDOW_SCALING))
        except Exception:
            overlay_font = ("Helvetica", int(14 * WINDOW_SCALING))
        
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
        
        char_width = int(24 * WINDOW_SCALING)
        line_height = int(40 * WINDOW_SCALING)
        max_width = int(800 * WINDOW_SCALING)
        max_height = int(600 * WINDOW_SCALING)
        padding = int(20 * WINDOW_SCALING)

        max_line_chars = max(len(line) for line in text.split("\n"))
        ideal_width = min(max_line_chars * char_width + padding, max_width)
        chars_per_line = max(1, (ideal_width - padding) // char_width)
        total_lines = sum(max(1, (len(line) + chars_per_line - 1) // chars_per_line) for line in text.split("\n"))
        ideal_height = min(total_lines * line_height + padding, max_height)
        
        root.geometry(f"{int(ideal_width)}x{int(ideal_height)}+{int(100 * WINDOW_SCALING)}+{int(100 * WINDOW_SCALING)}")
        
        frame = tk.Frame(root, bg="#131313", relief=tk.FLAT, borderwidth=0)
        frame.pack(fill=tk.BOTH, expand=True, padx=int(5 * WINDOW_SCALING), pady=int(5 * WINDOW_SCALING))

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
            global OVERLAY_ACTIVE
            OVERLAY_ACTIVE = False
        
        # Double-click to close
        text_widget.bind("<Double-Button-1>", close_overlay)
        root.bind("<Escape>", close_overlay)
        
        root.after(len(text) * 15 + 5000, close_overlay)
        root.mainloop()
        display_overlay()

    global OVERLAY_ACTIVE
    if OVERLAY_QUEUE is not None and not len(OVERLAY_QUEUE) == 0 and not OVERLAY_ACTIVE:
        text = OVERLAY_QUEUE.popleft()
        threading.Thread(target=open_overlay).start()
        OVERLAY_ACTIVE = True

# Show overlay for AI output designated for user
def show_overlay(text):
    if OVERLAY_QUEUE is not None:
        OVERLAY_QUEUE.append(text)
        display_overlay()

def show_status_indicator(text="Listening", dot_color="#4FA4FF"):
    if DASHBOARD_ROOT is None:
        return

    def _update_or_create():
        global STATUS_INDICATOR_WINDOW, STATUS_CANVAS, STATUS_TEXT_ID, STATUS_DOT_IDS
        
        # If the window doesn't exist or was destroyed, create it
        if STATUS_INDICATOR_WINDOW is None or not STATUS_INDICATOR_WINDOW.winfo_exists():
            STATUS_INDICATOR_WINDOW = tk.Toplevel(DASHBOARD_ROOT)
            STATUS_INDICATOR_WINDOW.title("KB Status")
            STATUS_INDICATOR_WINDOW.overrideredirect(True)
            STATUS_INDICATOR_WINDOW.attributes("-topmost", True)
            STATUS_INDICATOR_WINDOW.attributes("-alpha", 0.86)
            STATUS_INDICATOR_WINDOW.configure(bg="#131313")
            
            font_obj = tkFont.Font(
                root=STATUS_INDICATOR_WINDOW,
                family="Helvetica",
                size=int(12 * WINDOW_SCALING),
                weight="bold"
            )
            
            STATUS_CANVAS = tk.Canvas(STATUS_INDICATOR_WINDOW, bg="#131313", highlightthickness=0)
            STATUS_CANVAS.pack(fill="both", expand=True)
            
            STATUS_TEXT_ID = STATUS_CANVAS.create_text(
                int(14 * WINDOW_SCALING), int(18 * WINDOW_SCALING),
                anchor="nw", text="", fill="#FFFFFF", font=font_obj
            )
            
            STATUS_DOT_IDS = [STATUS_CANVAS.create_oval(0, 0, 0, 0, fill="#FFFFFF", outline="") for _ in range(3)]

        font_obj = tkFont.Font(family="Helvetica", size=int(12 * WINDOW_SCALING), weight="bold")
        text_width = font_obj.measure(text)
        padding = int(40 * WINDOW_SCALING)
        dot_cluster_width = int(90 * WINDOW_SCALING)
        min_width = int(290 * WINDOW_SCALING)
        
        width = max(min_width, text_width + padding + dot_cluster_width)
        height = int(70 * WINDOW_SCALING)

        STATUS_INDICATOR_WINDOW.geometry(f"{width}x{height}+{int(18 * WINDOW_SCALING)}+{int(18 * WINDOW_SCALING)}")
        STATUS_CANVAS.config(width=width, height=height)

        STATUS_CANVAS.itemconfig(STATUS_TEXT_ID, text=text)

        # Update dot placements and colors
        dot_centers = [
            width - int(100 * WINDOW_SCALING),
            width - int(72 * WINDOW_SCALING),
            width - int(44 * WINDOW_SCALING)
        ]

        for i, cx in enumerate(dot_centers):
            STATUS_CANVAS.coords(
                STATUS_DOT_IDS[i],
                cx - int(7 * WINDOW_SCALING),
                height // 2 - int(12 * WINDOW_SCALING),
                cx + int(7 * WINDOW_SCALING),
                height // 2 + int(6 * WINDOW_SCALING)
            )
            STATUS_CANVAS.itemconfig(STATUS_DOT_IDS[i], fill=dot_color)

    # Schedule the UI update
    DASHBOARD_ROOT.after(0, _update_or_create)


def hide_status_indicator():
    if DASHBOARD_ROOT is None:
        return

    def _destroy():
        global STATUS_INDICATOR_WINDOW
        if STATUS_INDICATOR_WINDOW and STATUS_INDICATOR_WINDOW.winfo_exists():
            STATUS_INDICATOR_WINDOW.destroy()
        STATUS_INDICATOR_WINDOW = None

    # Schedule the destruction
    DASHBOARD_ROOT.after(0, _destroy)

# Class for managing the conversation memory
class ConversationMemory:
    def __init__(self, max_messages = 6):
        self.history = []
        self.max_messages = max_messages

    # Add a message to the conversation history
    # Automatically rotates history if needed
    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

        # Rotate history if exceeding maximum messages
        if len(self.history) > self.max_messages:
            self.history = self.history[-self.max_messages:]

    def get_history(self):
        return self.history

    # Returns the history in proper formatting and truncated
    def get_formatted_history(self):
        if not self.history:
            return "[No previous history]"
        
        formatted = []
        for msg in self.history:
            role = msg["role"]
            content = msg["content"]

            # Truncate
            if role in ["LCO", "LCI"]:
                content = truncate_middle(content, 60)
            elif role in ["USER", "AI"]:
                content = truncate_middle(content, 200)

            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

# Dashboard for KiloBuddy
class KiloBuddyDashboard:
    def __init__(self, root):
        self.root = root
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        self.background_color = "#0B3147"
        self.frame_color = "#1D4E89"
        self.border_color = "#2E86C1"
        
        # Load StackSans fonts
        self.load_custom_fonts()
        
        global WINDOW_SCALING

        # Font size variables
        self.status_font_size = int(28 * WINDOW_SCALING)
        self.button_font_size = int(28 * WINDOW_SCALING)
        self.header_font_size = int(38 * WINDOW_SCALING)
        self.text_font_size = int(28 * WINDOW_SCALING)
        self.input_font_size = int(28 * WINDOW_SCALING)

        self.root.title("KiloBuddy")
        scaled_w, scaled_h = int(1000 * WINDOW_SCALING), int(800 * WINDOW_SCALING)
        self.root.geometry(f"{scaled_w}x{scaled_h}")
        scaled_min_w, scaled_min_h = int(900 * WINDOW_SCALING), int(650 * WINDOW_SCALING)
        self.root.minsize(scaled_min_w, scaled_min_h)
        self.root.resizable(True, True)
        self.root.configure(fg_color=self.background_color)
        self.root.protocol("WM_DELETE_WINDOW", self.close_dashboard)
        #self.build_ui()

        def apply_taskbar_icon():
            ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
            if os.path.exists(ico_path):
                try:
                    self.root.iconbitmap(ico_path)
                except Exception as e:
                    print(f"Window error: {e}")
                    pass

        self.root.after(0, apply_taskbar_icon)

        ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(ico_path):
            try:
                self.root.iconbitmap(ico_path)
            except Exception:
                pass

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
        button_frame.pack(fill="x", padx=int(20 * WINDOW_SCALING), pady=int(20 * WINDOW_SCALING))

        status_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        status_frame.pack(side="left")

        self.status_label = ctk.CTkLabel(status_frame, text="Status:", text_color="white", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.status_font_size))
        self.status_label.pack(side="left", padx=(0, int(10 * WINDOW_SCALING)))

        self.status_canvas = tk.Canvas(status_frame, width=int(130 * WINDOW_SCALING), height=int(34 * WINDOW_SCALING), bg=self.background_color, highlightthickness=0, bd=0)
        self.status_canvas.pack(side="left")

        self.status_lights = {
            "green": self.status_canvas.create_oval(int(6 * WINDOW_SCALING), int(6 * WINDOW_SCALING), int(30 * WINDOW_SCALING), int(30 * WINDOW_SCALING), fill="#2E7D32", outline=""),
            "yellow": self.status_canvas.create_oval(int(46 * WINDOW_SCALING), int(6 * WINDOW_SCALING), int(70 * WINDOW_SCALING), int(30 * WINDOW_SCALING), fill="#F9A825", outline=""),
            "red": self.status_canvas.create_oval(int(86 * WINDOW_SCALING), int(6 * WINDOW_SCALING), int(110 * WINDOW_SCALING), int(30 * WINDOW_SCALING), fill="#C62828", outline="")
        }

        self.set_status_lights("waiting")

        quit_btn = ctk.CTkButton(button_frame, text="Stop KB", command=self.quit_kilobuddy, fg_color="#f44336", hover_color="#d32f2f", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.button_font_size), width=int(100 * WINDOW_SCALING), height=int(35 * WINDOW_SCALING))
        quit_btn.pack(side="right")

        settings_btn = ctk.CTkButton(button_frame, text="Settings", command=self.open_settings_window, fg_color="#607d8b", hover_color="#546e7a", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.button_font_size), width=int(120 * WINDOW_SCALING), height=int(35 * WINDOW_SCALING))
        settings_btn.pack(side="right", padx=(0, int(10 * WINDOW_SCALING)))

        output_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        output_frame.pack(fill="both", expand=True, padx=int(20 * WINDOW_SCALING), pady=int(10 * WINDOW_SCALING))

        text_frame = ctk.CTkFrame(output_frame, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=int(15 * WINDOW_SCALING), pady=int(15 * WINDOW_SCALING))

        self.output_text = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(family=self.stacksans_light_family, size=self.text_font_size), fg_color=self.background_color, text_color="white", corner_radius=int(10 * WINDOW_SCALING), height=int(300 * WINDOW_SCALING))
        self.output_text._textbox.configure(wrap = "word")
        self.output_text.pack(fill="both", expand=True)

        # Colors for conversation
        self.output_text.tag_config("USER", foreground = "#9F9F9F")
        self.output_text.tag_config("AI", foreground = "#FFFFFF")
        self.output_text.tag_config("LCO", foreground = "#00D080")
        self.output_text.tag_config("LCI", foreground = "#C36100")
        self.output_text.tag_config("SYS", foreground = "#FFB300")

        self.update_output_display()

        input_frame = ctk.CTkFrame(self.root, fg_color=self.frame_color, corner_radius=15)
        input_frame.pack(fill="x", padx=int(20 * WINDOW_SCALING), pady=int(10 * WINDOW_SCALING))

        input_container = ctk.CTkFrame(input_frame, fg_color="transparent")
        input_container.pack(fill="x", padx=int(15 * WINDOW_SCALING), pady=int(15 * WINDOW_SCALING))

        self.command_entry = ctk.CTkEntry(input_container, font=ctk.CTkFont(family=self.stacksans_light_family, size=self.input_font_size), fg_color=self.background_color, text_color="white", placeholder_text="Enter Command...", placeholder_text_color="#888888", corner_radius=int(10 * WINDOW_SCALING), height=int(40 * WINDOW_SCALING))
        self.command_entry.pack(side="left", fill="x", expand=True, padx=(0, int(10 * WINDOW_SCALING)))

        send_btn = ctk.CTkButton(input_container, text="Send", command=self.send_command, fg_color="#2196F3", hover_color="#1976D2", font=ctk.CTkFont(family=self.stacksans_light_family, size=self.input_font_size), width=int(100 * WINDOW_SCALING), height=int(40 * WINDOW_SCALING), corner_radius=int(10 * WINDOW_SCALING))
        send_btn.pack(side="right")
        
        self.command_entry.bind('<Return>', lambda event: self.send_command())

    class HoverToolTip:
        def __init__(self, widget, text):
            self.widget = widget
            self.text = text
            self.tooltip_window = None
            widget.bind("<Enter>", self.show_tooltip)
            widget.bind("<Leave>", self.hide_tooltip)
        
        def show_tooltip(self, event=None):
            if self.tooltip_window is not None:
                return
            
            x = self.widget.winfo_rootx() + int(40 * WINDOW_SCALING)
            y = self.widget.winfo_rooty() + int(40 * WINDOW_SCALING)

            self.tooltip_window = tw = ctk.CTkToplevel(self.widget)
            tw.wm_overrideredirect(True)
            tw.geometry(f"+{x}+{y}")
            tw.configure(fg_color="#1E1E1E")

            label = ctk.CTkLabel(
                tw,
                text=self.text,
                font=ctk.CTkFont(family="StackSans Text Light", size=int(20 * WINDOW_SCALING)),
                text_color="white",
                justify="left",
                wraplength=300
            )
            label.pack(padx=10, pady=6)

        def hide_tooltip(self, event=None):
            if self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None

    def open_settings_window(self):
        try:
            global WINDOW_SCALING
            settings_window = ctk.CTkToplevel(self.root)
            settings_window.title("KiloBuddy Settings")
            scaled_w, scaled_h = int(620 * WINDOW_SCALING), int(805 * WINDOW_SCALING)
            settings_window.geometry(f"{scaled_w}x{scaled_h}")
            settings_window.configure(fg_color="#0B3147")
            settings_window.transient(self.root)
            settings_window.lift()
            settings_window.update_idletasks()

            header = ctk.CTkLabel(settings_window, text="Settings", font=ctk.CTkFont(family=self.stacksans_medium_family, size=int(28 * WINDOW_SCALING)), text_color="white")
            header.pack(padx=int(20 * WINDOW_SCALING), pady=(int(20 * WINDOW_SCALING), int(10 * WINDOW_SCALING)), anchor="w")

            scroll_frame = ctk.CTkScrollableFrame(settings_window, fg_color="#142A44", corner_radius=int(15 * WINDOW_SCALING))
            scroll_frame.pack(fill="both", expand=True, padx=int(20 * WINDOW_SCALING), pady=(0, int(20 * WINDOW_SCALING)))

            def make_label(entry_text):
                return ctk.CTkLabel(scroll_frame, text=entry_text, font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), text_color="white")

            pref_label = make_label("AI Provider Preference")
            pref_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(20 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            pref_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="gemini, chatgpt, claude")
            pref_entry.insert(0, AI_PREFERENCE)
            pref_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                pref_entry,
                "Enter the order of your preferred AI providers, separated by commas.\nEx: gemini, chatgpt, claude\n\nFor Ollama models, enter the model name as it appears in the Ollama list.\nEx: llama3.18B, phi3:mini"
            )

            wake_label = make_label("Wake Word")
            wake_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            wake_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="computer")
            wake_entry.insert(0, WAKE_WORD)
            wake_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                wake_entry,
                "Enter the wake word that KiloBuddy will listen for to activate.\n\nMust be lowercase."
            )

            timeout_label = make_label("API Timeout (seconds)")
            timeout_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            timeout_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="15")
            timeout_entry.insert(0, str(API_TIMEOUT))
            timeout_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                timeout_entry,
                "Enter the maximum time (in seconds) to wait for an AI provider to respond.\n\nIf your models keep timing out, increase this value.\n\nMust be an integer between 5 and 120 (no decimals)."
            )

            gemini_label = make_label("Gemini API Key")
            gemini_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            gemini_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="Gemini API Key", show="~")
            gemini_entry.insert(0, GEMINI_API_KEY)
            gemini_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                gemini_entry,
                "Enter your Gemini API key.\n\nThis key allows the app to interact with Google/Gemini and generate responses."
            )

            chatgpt_label = make_label("ChatGPT API Key")
            chatgpt_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            chatgpt_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="ChatGPT API Key", show="~")
            chatgpt_entry.insert(0, CHATGPT_API_KEY)
            chatgpt_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                chatgpt_entry,
                "Enter your ChatGPT API key.\n\nThis key allows the app to interact with OpenAI/ChatGPT and generate responses."
            )

            claude_label = make_label("Claude API Key")
            claude_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            claude_entry = ctk.CTkEntry(scroll_frame, width=int(560 * WINDOW_SCALING), font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), fg_color="#0B3147", text_color="white", placeholder_text="Claude API Key", show="~")
            claude_entry.insert(0, CLAUDE_API_KEY)
            claude_entry.pack(padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                claude_entry,
                "Enter your Claude API key.\n\nThis key allows the app to interact with Anthropic/Claude and generate responses."
            )

            manage_ollama_var = ctk.BooleanVar(value=MANAGE_OLLAMA)
            manage_ollama_label = make_label("Manage Ollama")
            manage_ollama_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            manage_ollama_checkbox = ctk.CTkCheckBox(scroll_frame, text = "Enable Ollama Management", variable = manage_ollama_var, onvalue=True, offvalue=False, font=ctk.CTkFont(family=self.stacksans_light_family, size = int(24 * WINDOW_SCALING)), text_color="white")
            manage_ollama_checkbox.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                manage_ollama_checkbox,
                "When enabled, KiloBuddy will manage startup and shutdown of Ollama when it is not already running.\n\nWhen disabled, KiloBuddy will not manage Ollama and will assume it is already running.\n\nIgnore this setting if you are not using local models."
            )

            update_label = make_label("Update Preference")
            update_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            update_options = ["release", "pre-release", "none"]
            update_pref_var = ctk.StringVar(value=UPDATES)
            update_pref_dropdown = ctk.CTkOptionMenu(
                scroll_frame,
                variable=update_pref_var,
                values=update_options,
                fg_color="#1D4E89",
                button_color="#1D4E89",
                button_hover_color="#2E86C1",
                text_color="White",
                font=ctk.CTkFont(family=self.stacksans_light_family, size=int(24 * WINDOW_SCALING)),
                dropdown_fg_color="#1D4E89",
                dropdown_text_color="White",
                dropdown_hover_color="#2E86C1",
                dropdown_font=ctk.CTkFont(family=self.stacksans_light_family, size=int(24 * WINDOW_SCALING))
            )
            update_pref_dropdown.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(0, int(10 * WINDOW_SCALING)))
            self.HoverToolTip(
                update_pref_dropdown,
                "Select what updates you want to be notified for at launch.\n- release: Only stable releases\n- pre-release: Both stable and unstable/incomplete releases\n- none: Disable update checking"
            )

            open_log_label = make_label("Open App Log")
            open_log_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(4 * WINDOW_SCALING)))
            open_log_btn = ctk.CTkButton(
                scroll_frame,
                text = "Open Log",
                fg_color = "#1D4E89",
                hover_color = "#2E86C1",
                width = int(135 * WINDOW_SCALING),
                font = ctk.CTkFont(family=self.stacksans_light_family, size=int(24 * WINDOW_SCALING)),
                command = lambda: open_log_file()
            )
            open_log_btn.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(10 * WINDOW_SCALING), int(10 * WINDOW_SCALING)))
            
            status_label = ctk.CTkLabel(settings_window, text="", font=ctk.CTkFont(family=self.stacksans_light_family, size=int(28 * WINDOW_SCALING)), text_color="#FFEE58")
            status_label.pack(anchor="w", padx=int(20 * WINDOW_SCALING), pady=(int(3 * WINDOW_SCALING), 0))

            def open_log_file():
                global LOG_PATH
                if sys.platform.startswith("win"):
                    os.startfile(LOG_PATH)
                elif sys.platform.startswith("darwin"):
                    subprocess.call(["open", LOG_PATH])
                else:
                    subprocess.call(["xdg-open", LOG_PATH])

            def save_and_close():
                preference_value = pref_entry.get().strip().lower()
                wake_value = wake_entry.get().strip().lower()
                timeout_value = timeout_entry.get().strip()
                gemini_value = gemini_entry.get().strip()
                chatgpt_value = chatgpt_entry.get().strip()
                claude_value = claude_entry.get().strip()
                manage_ollama_value = manage_ollama_var.get()
                update_pref_value = update_pref_var.get()

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

                global AI_PREFERENCE, WAKE_WORD, API_TIMEOUT, GEMINI_API_KEY, CHATGPT_API_KEY, CLAUDE_API_KEY, MANAGE_OLLAMA, UPDATES
                AI_PREFERENCE = ", ".join(parsed)
                WAKE_WORD = wake_value
                API_TIMEOUT = timeout_int
                GEMINI_API_KEY = gemini_value
                CHATGPT_API_KEY = chatgpt_value
                CLAUDE_API_KEY = claude_value
                MANAGE_OLLAMA = manage_ollama_value
                UPDATES = update_pref_value

                if save_settings():
                    status_label.configure(text="Settings saved successfully.", text_color="#81C784")
                else:
                    status_label.configure(text="Failed to save settings.", text_color="#EF9A9A")

            button_row = ctk.CTkFrame(settings_window, fg_color="transparent")
            button_row.pack(fill="x", padx=int(20 * WINDOW_SCALING), pady=(0, int(20 * WINDOW_SCALING)))

            button_font = ("StackSans Text Light", int(28 * WINDOW_SCALING))

            save_btn = ctk.CTkButton(button_row, text="Save", command=save_and_close, fg_color="#4CAF50", hover_color="#43A047", width=int(120 * WINDOW_SCALING), height=int(40 * WINDOW_SCALING), font=button_font)
            save_btn.pack(side="right", padx=(0, int(10 * WINDOW_SCALING)))

            close_btn = ctk.CTkButton(button_row, text="Close", command=settings_window.destroy, fg_color="#666666", hover_color="#555555", width=int(120 * WINDOW_SCALING), height=int(40 * WINDOW_SCALING), font=button_font)
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
        self.output_text.delete("0.0", "end")
        history = getattr(CONVERSATION_HISTORY, "history", None)

        if not history:
            self.output_text.insert("end", "No response yet. Try sending a command...", "SYS")
            return
        
        for msg in history:
            role = msg["role"]
            content = msg["content"]

            self.output_text.insert("end", f"{role}: ", role)

            self.output_text.insert("end", f"{content}\n", role)

            self.output_text.insert("end", "\n", "SYS")

        self.output_text._textbox.see("end")
    
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
        self.update_output_display()
    
    def update_output_with_latest_response(self):
        self.update_output_display()

    def quit_kilobuddy(self):
        result = show_custom_confirm(
            "Stop KiloBuddy",
            "Are you sure you want to stop KiloBuddy?\n\nThis will stop the voice assistant and close the dashboard.",
            parent=self.root
        )
        if result:
            request_kilobuddy_stop()
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
    
    def run(self):
        self.root.mainloop()

    def show(self):
        self.root.update()
        self.root.deiconify()
        self.root.focus_set()

    def close_dashboard(self):
        try:
            self.root.withdraw()
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
    stop_ollama()
    cleanup_lock_file()
    global audio_stream, VOICE_THREAD
    if VOICE_THREAD is not None and VOICE_THREAD.is_alive():
        print("INFO: Waiting for voice thread to exit...")
        VOICE_THREAD.join(timeout=3)
        if VOICE_THREAD.is_alive():
            print("INFO: Voice thread did not exit cleanly, forcing process termination.")
            os._exit(0)
    if audio_stream:
        try:
            audio_stream.stop()
            audio_stream.close()
        except Exception as e:
            print(f"ERROR: Failed to stop audio stream: {e} \nERROR 117")
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
    global DASHBOARD_ROOT
    dashboard = KiloBuddyDashboard(DASHBOARD_ROOT)
    dashboard.show()
    # try:
    #     base_dir = os.path.dirname(os.path.abspath(__file__))
    #     StackSans_EL = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-ExtraLight.ttf"), size=9)
    #     StackSans_L = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-Light.ttf"), size=12)
    #     StackSans_M = tkFont.Font(file=os.path.join(base_dir, "StackSans-Text-Medium.ttf"), size=22)
    # except:
    #     StackSans_EL = ("Arial", 10)
    #     StackSans_L = ("Arial", 12)
    #     StackSans_M = ("Arial", 22)
    # dashboard = KiloBuddyDashboard()
    # dashboard.run()

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
    global VERSION, UPDATES
    url = "https://api.github.com/repos/MichaelCreel/KiloBuddy/releases"
    if UPDATES == "none":
        print("INFO: Skipping update check.")
        return None
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
            audio_stream.stop()
            audio_stream.close()
        cleanup_lock_file()

def start_voice_listening():
    global VOICE_THREAD
    # Keep the voice thread alive independently of the dashboard window.
    VOICE_THREAD = threading.Thread(target=main, daemon=False)
    VOICE_THREAD.start()
    return VOICE_THREAD

# Retrieves the system scaling and returns a scaling factor
def populate_scaling():
    global WINDOW_SCALING
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        screen = app.primaryScreen()
        logical_dpi = screen.logicalDotsPerInch()
        app.quit()
        base_dpi = 192.0 # Logical DPI the interface was designed for
        WINDOW_SCALING = logical_dpi / base_dpi
        print(f"INFO: Scaling factor applied: {WINDOW_SCALING:.2f} (Logical DPI: {logical_dpi})")
    except Exception as e:
        print(f"WARNING: Failed to retrieve system scaling: {e}\nWARN 316")
        WINDOW_SCALING = 1.0

class LogRedirector:
    def __init__(self, path):
        self.path = path
    
    def write(self, message):
        if message.strip():
            self.rotate_if_needed()
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    def flush(self):
        pass

    def rotate_if_needed(self):
        if os.path.exists(self.path) and os.path.getsize(self.path) > MAX_LOG_SIZE:
            os.replace(self.path, self.path + ".old")

if __name__ == "__main__":
    if "--dev" not in sys.argv:
        sys.stdout = LogRedirector(LOG_PATH)
        sys.stderr = LogRedirector(LOG_PATH)
    else:
        print("INFO: Developer mode launched.")

    print(f"STARTUP: [[[LAUNCH AT {time.strftime('%Y-%m-%d %H:%M:%S')}]]]")
    print("INFO: Launching KiloBuddy...")

    load_settings()
    load_update_type()
    load_os_version()
    load_prompt()
    load_initial_prompt()

    is_primary_instance = not is_kilobuddy_running()

    if is_primary_instance:
        create_lock_file()

    signal.signal(signal.SIGINT, handle_signal)

    # Populate logical scaling field
    populate_scaling()

    # Create root
    DASHBOARD_ROOT = ctk.CTk()

    # Build dashboard UI
    dashboard = KiloBuddyDashboard(DASHBOARD_ROOT)

    CONVERSATION_HISTORY = ConversationMemory(max_messages=6)

    # Start voice listening thread if not running
    if is_primary_instance:
        print("INFO: Starting voice assistant in background...")
        start_voice_listening()
    else:
        print("INFO: Voice thread already running.")

    # Show dashboard
    print("INFO: Opening dashboard...")
    dashboard.show()

    # Enter Tk event loop LAST
    DASHBOARD_ROOT.mainloop()
