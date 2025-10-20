import speech_recognition as sr
import re
import os
import sys
import google.generativeai as genai

API_TIMEOUT = 10 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
PROMPT = "Return 'Prompt not loaded'." # Prompt for Gemini API Key call, loaded from prompt file

def initialize():
    load_api_key()
    load_prompt()

def load_api_key():
    global GEMINI_API_KEY
    try:
        with open(get_source_path("gemini_api_key"), "r") as f:
            key = f.read().strip()
            if key == "null" or key == "" or key == "none":
                print("No API key provided, using fallback text only")
            else:
                USE_GEMINI = True
                genai.configure(api_key=key)
                GEMINI_API_KEY = key
                print("Loaded API Key")
    except FileNotFoundError:
        print("API key file not found, using fallback text only")
    except Exception as e:
        print(f"Error loading API key: {e}, using fallback text only")

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
    except Exception as e:
        print(f"Error loading prompt: {e}")

def get_source_path(filename):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)