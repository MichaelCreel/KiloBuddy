from click import command
import speech_recognition as sr
import re
import os
import sys
import google.generativeai as genai
import threading
import time
import subprocess

API_TIMEOUT = 10 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
PROMPT = "Return 'Prompt not loaded'." # Prompt for Gemini API Key call, loaded from prompt file
WAKE_WORD = "computer" # Wake word to trigger KiloBuddy listening, loaded from wake_word file
LINUX_VERSION = "debian" # Linux version for command generation
PREVIOUS_COMMAND_OUTPUT = "" # Store the previously run USER command output for Gemini use

# Initialize Necessary Variables
def initialize():
    print("Initializing KiloBuddy...")
    load_api_key()
    load_prompt()
    load_wake_word()
    load_linux_version()
    print("KiloBuddy Initialized.")

# Load Linux Version from file
def load_linux_version():
    global LINUX_VERSION
    try:
        with open(get_source_path("linux_version"), "r") as f:
            version = f.read().strip().lower()
            if version == "null" or version == "" or version == "none":
                print("No Linux version provided, using default 'debian'")
            else:
                LINUX_VERSION = version
                print(f"Loaded Linux Version: {LINUX_VERSION}")
    except FileNotFoundError:
        print("Linux version file not found, using fallback 'debian'")
    except Exception as e:
        print(f"Error loading Linux version: {e}, using default 'debian'")

# Load Wake Word from file
def load_wake_word():
    global WAKE_WORD
    try:
        with open(get_source_path("wake_word"), "r") as f:
            word = f.read().strip().lower()
            if word == "null" or word == "" or word == "none":
                print("No wake word provided, using default 'computer'")
            else:
                WAKE_WORD = word
                print(f"Loaded Wake Word: {WAKE_WORD}")
    except FileNotFoundError:
        print("Wake word file not found, using fallback 'computer'")
    except Exception as e:
        print(f"Error loading wake word: {e}, using default 'computer'")

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
            else:
                PROMPT = prompt_content
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
def generate_text(input_prompt):
    result = {"text": None}
    timeout_triggered = threading.Event()

    def gemini_call():
        if timeout_triggered.is_set():
            return
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content(input_prompt)
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

# Listen for Wake Word
def listen_for_wake_word():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    print(f"Listening for wake word ('{WAKE_WORD}')...")

    while True:
        try:
            with microphone as source:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
            try:
                text = recognizer.recognize_google(audio, show_all=False).lower()
                if text:
                    print(f"Heard: {text}")

                    if WAKE_WORD in text:
                        print(f"Wake word detected...")
                        return True
            except sr.UnknownValueError:
                # Didn't understand speech. It happens.
                pass
            except sr.RequestError as e:
                print(f"Speech Recognition error: {e}")
                time.sleep(0.25)
        except sr.WaitTimeoutError:
            # No speech detected before timeout. It happens.
            pass
        except Exception as e:
            print(f"Error during listening: {e}")
            time.sleep(0.25)

# Listen for Command after Wake Word
def listen_for_command():
    recognizer = sr.Recognizer()

    print(f"Listening for command...")

    try:
        with sr.Microphone() as source:
            # 10 seconds to say command, no command limit
            audio = recognizer.listen(source, timeout=10)
        print ("Processing command...")
        command = recognizer.recognize_google(audio)
        print(f"Command received: {command}")
        return command
    except sr.UnknownValueError:
        print(f"Failed to understand command.")
        return None
    except sr.RequestError as e:
        print(f"Speech Recognition error: {e}")
        return None
    except sr.WaitTimeoutError:
        print(f"No command detected within timeout.")
        return None

# Process Command using Gemini
def process_command(command):
    if not command:
        print("No command to process.")
        return
    
    global PROMPT
    global LINUX_VERSION
    combined_prompt = f"Linux: {LINUX_VERSION}\n\n{PROMPT}\n\nUser Command: {command}"

    print("Generating response...")
    response = generate_text(combined_prompt)
    if response:
        print(f"{response}")
        process_response(response)
    else:
        print("No response generated.")

def process_response(response):
    todo_list = extract_todo_list(response)
    print(f"\n\n{extract_user_output(response)}\n\n")
    if todo_list:
        process_todo_list(todo_list)
    else:
        print("No todo list found in response.")
    return;

# Extract the todo list from Gemini response
def extract_todo_list(response):
    task_pattern = re.compile(r"\[(\d+)\] (.+?) # (USER|GEMINI) --- (DONE|DO NEXT|PENDING|SKIPPED)")
    return task_pattern.findall(response);

# Extract output for the user from Gemini response
def extract_user_output(response):
    output_pattern = re.search(r'"""(.*?)"""', response, re.DOTALL)
    if output_pattern:
        return output_pattern.group(1).strip()
    return None

# Interprets the todo list and decides on user or Gemini call
def process_todo_list(todo_list):
    for i, (step_num, command, executor, status) in enumerate(todo_list):
        if status == "DO NEXT":
            if executor == "USER":
                user_call(command)
                update_status(todo_list, i)
                continue
            elif executor == "GEMINI":
                print(f"Requesting GEMINI command: {command}")
                gemini_call(todo_list)
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
    global PREVIOUS_COMMAND_OUTPUT
    print(f"Running USER command: {command}")
    result = subprocess.run(command, shell=True, timeout=45, capture_output=True, text=True)
    PREVIOUS_COMMAND_OUTPUT = result.stdout

# GEMINI Call Method
def gemini_call(task_list):
    global LINUX_VERSION, PROMPT, PREVIOUS_COMMAND_OUTPUT
    combined_prompt = f"Linux: {LINUX_VERSION}\n\n{PROMPT}\n\nPrevious Command Output:\n{PREVIOUS_COMMAND_OUTPUT}\n\nTodo List:\n{format_todo_list(task_list)}\n\nThis is a continuation of a previous task. Continue the task list by fulfilling the task marked 'DO NEXT'."
    print("Generating response...")
    response_text = generate_text(combined_prompt)
    process_response(response_text)

# Formats parsed todo list back into string
def format_todo_list(todo_list):
    lines = [">>"]
    for step_num, command, executor, status in todo_list:
        lines.append(f"[{step_num}] {command} # {executor} --- {status}")
    lines.append("<<")
    return "\n".join(lines)

# Main Method that controls KiloBuddy
def main():
    initialize()

    print(f"KiloBuddy successfully started. Say '{WAKE_WORD}' followed by your command.")

    print("Use debug text version? (y/n): ")
    debug_input = input().strip().lower()
    if debug_input == 'y':
        while True:
            print("Enter a command: ")
            user_command = input().strip()
            process_command(user_command)
        return
    elif debug_input == 'n':
        print("Starting voice mode...")
    else:
        print("Invalid input, starting voice mode...")

    try:
        while True:
            # Start Listening for Wake Word
            if listen_for_wake_word():
                # Start Listening for Command
                command = listen_for_command()
                if command:
                    process_command(command)

                print("Returning to wake word listening...")
    except KeyboardInterrupt:
        print("KiloBuddy Shutting Down...")

if __name__ == "__main__":
    print("KiloBuddy Launching...")
    main()