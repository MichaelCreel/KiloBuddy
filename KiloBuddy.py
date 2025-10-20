import speech_recognition as sr
import re
import os
import sys
import google.generativeai as genai
import threading

API_TIMEOUT = 10 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
PROMPT = "Return 'Prompt not loaded'." # Prompt for Gemini API Key call, loaded from prompt file

# Initialize Necessary Variables
def initialize():
    load_api_key()
    load_prompt()
    print("KiloBuddy Initialized.")

# Load API Key for Gemini from file
def load_api_key():
    global GEMINI_API_KEY
    try:
        with open(get_source_path("gemini_api_key"), "r") as f:
            key = f.read().strip()
            if key == "null" or key == "" or key == "none":
                print("No API key provided, using fallback text only")
            else:
                genai.configure(api_key=key)
                GEMINI_API_KEY = key
                print("Loaded API Key")
    except FileNotFoundError:
        print("API key file not found, using fallback text only")
    except Exception as e:
        print(f"Error loading API key: {e}, using fallback text only")

# Load Prompt for Gemini from file
def load_prompt():
    try:
        with open(get_source_path("prompt"), "r") as f:
            lines = f.readlines()
            global PROMPT
            prompt_content = "".join(lines).strip()
            
            # Validate prompt content
            if len(prompt_content) == 0:
                print("Warning: prompt file is empty, using default")
            elif len(prompt_content) > 2000:
                print("Warning: prompt file is very long, may cause API issues")
                PROMPT = prompt_content[:2000]  # Truncate if too long
            else:
                PROMPT = prompt_content
                print("Loaded Prompt")
    except Exception as e:
        print(f"Error loading prompt: {e}")

# File Path Finder
def get_source_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

# Generate Text using Gemini
def generate_text():
    result = {"text": None}
    timeout_triggered = threading.Event()

    def gemini_call():
        if timeout_triggered.is_set():
            return
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-exp")
            response = model.generate_content(PROMPT)
            if not timeout_triggered.is_set():
                result["text"] = response.text.strip()
        except Exception as e:
            print(f"Error during Gemini API call: {e}")
    
    def fallback():
        timeout_triggered.set()
        print("Gemini API Timeout.")

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
    return result["text"]

def main():
    initialize()

if __name__ == "__main__":
    print("KiloBuddy Launching...")
    main()