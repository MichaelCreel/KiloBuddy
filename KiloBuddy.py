import speech_recognition as sr
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

API_TIMEOUT = 10 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
PROMPT = "Return 'Prompt not loaded'." # Prompt for Gemini API Key call, loaded from prompt file
WAKE_WORD = "computer" # Wake word to trigger KiloBuddy listening, loaded from wake_word file
OS_VERSION = "auto-detect" # Operating system version for command generation
PREVIOUS_COMMAND_OUTPUT = "" # Store the previously run USER command output for Gemini use
LAST_GEMINI_OUTPUT = "No previous output..." # Store the last output by Gemini that was designated for the user
VERSION = "v0.0"

# Initialize Necessary Variables
def initialize():
    print("Initializing KiloBuddy...")
    load_api_key()
    load_prompt()
    load_wake_word()
    load_os_version()
    load_app_version()
    check_for_updates()
    print("KiloBuddy Initialized.")

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

# Load App Version from file
def load_app_version():
    global VERSION
    try:
        with open(get_source_path("version"), "r") as f:
            version = f.read().strip().lower()
            if version == "null" or version == "" or version == "none":
                print(f"Version not found")
            else:
                VERSION = version
                print(f"Loaded Version: {VERSION}")
    except FileNotFoundError:
        print(f"Version file not found")
    except Exception as e:
        print(f"Error loading version: {e}")

# Load Operating System Version from file
def load_os_version():
    global OS_VERSION
    try:
        with open(get_source_path("os_version"), "r") as f:
            version = f.read().strip().lower()
            if version == "null" or version == "" or version == "none" or version == "auto-detect":
                OS_VERSION = detect_os()
                print(f"Auto-detected OS: {OS_VERSION}")
            else:
                OS_VERSION = version
                print(f"Loaded OS Version: {OS_VERSION}")
    except FileNotFoundError:
        OS_VERSION = detect_os()
        print(f"OS version file not found, auto-detected: {OS_VERSION}")
    except Exception as e:
        OS_VERSION = detect_os()
        print(f"Error loading OS version: {e}, auto-detected: {OS_VERSION}")

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
    global OS_VERSION
    combined_prompt = f"OS: {OS_VERSION}\n\n{PROMPT}\n\nUser Command: {command}"

    print("Generating response...")
    response = generate_text(combined_prompt)
    if response:
        process_response(response)
    else:
        print("No response generated.")

def process_response(response):
    if not response:
        print("ERROR: No response from Gemini")
        return
    
    global LAST_GEMINI_OUTPUT
    
    todo_list = extract_todo_list(response)
    
    # Always show user output first
    user_output = extract_user_output(response)
    if user_output:
        # Store the output in the global variable
        LAST_GEMINI_OUTPUT = user_output
        print(f"\n=== KiloBuddy Output ===\n{user_output}\n========================\n")
        show_overlay(user_output)
    
    if todo_list:
        print(f"Found {len(todo_list)} todo items")
        process_todo_list(todo_list)
    else:
        print("No todo list found in response.")
    return

# Extract the todo list from Gemini response
def extract_todo_list(response):
    # More flexible regex pattern - allows variable spacing
    task_pattern = re.compile(r"\[(\d+)\]\s+(.+?)\s+#\s+(USER|GEMINI)\s+---\s+(DONE|DO NEXT|PENDING|SKIPPED)")
    matches = task_pattern.findall(response)
    
    return matches

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
    global PREVIOUS_COMMAND_OUTPUT, LAST_GEMINI_OUTPUT
    
    # Replace $LAST_OUTPUT with the actual Gemini output
    if "$LAST_OUTPUT" in command:
        command = command.replace("$LAST_OUTPUT", LAST_GEMINI_OUTPUT)
        print(f"Substituted $LAST_OUTPUT in command")
    
    print(f"Running USER command: {command}")
    result = subprocess.run(command, shell=True, timeout=45, capture_output=True, text=True)
    PREVIOUS_COMMAND_OUTPUT = result.stdout

# GEMINI Call Method
def gemini_call(task_list):
    global OS_VERSION, PROMPT, PREVIOUS_COMMAND_OUTPUT
    combined_prompt = f"OS: {OS_VERSION}\n\n{PROMPT}\n\nPrevious Command Output:\n{PREVIOUS_COMMAND_OUTPUT}\n\nTodo List:\n{format_todo_list(task_list)}\n\nThis is a continuation of a previous task. Continue the task list by fulfilling the task marked 'DO NEXT'."
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

# Show overlay for Gemini output designated for user
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
        self.background_color = "#0B3147"
        self.frame_color = "#004D77"
        self.border_color = "#145172"
        
        self.root = tk.Tk()
        self.root.title("KiloBuddy")
        self.root.geometry("1100x1100")
        self.root.configure(bg=self.background_color)

        if os.path.exists("icon.png"):
            try:
                self.root.iconphoto(False, tk.PhotoImage(file="icon.png"))
            except Exception:
                pass
        
        self.setup_ui()
        
    def setup_ui(self):
        button_frame = tk.Frame(self.root, bg=self.background_color)
        button_frame.pack(fill=tk.X, padx=20, pady=20)


        self.status_label = tk.Label(button_frame, text="Status: Waiting...", fg="#8A8A8A", bg=self.background_color, font=("Helvetica", 12))
        self.status_label.pack(side=tk.LEFT)

        quit_btn = tk.Button(button_frame, text="Quit KiloBuddy", command=self.quit_kilobuddy, bg="#f44336", fg="white", font=("Helvetica", 12), relief=tk.FLAT, padx=20, pady=10)
        quit_btn.pack(side=tk.RIGHT)

        output_frame = tk.Frame(self.root, bg=self.frame_color, relief=tk.RAISED, bd=2, highlightbackground=self.border_color, highlightthickness=2)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        

        header_frame = tk.Frame(output_frame, bg=self.frame_color)
        header_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(header_frame, text="Response", font=("Helvetica", 16, "bold"), fg="white", bg=self.frame_color).pack(side=tk.LEFT, padx=10)

        text_frame = tk.Frame(output_frame, bg=self.frame_color)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.output_text = tk.Text(text_frame, font=("Helvetica", 10), fg="white", bg=self.background_color, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, borderwidth=0, height=15)
        
        scrollbar = tk.Scrollbar(text_frame, command=self.output_text.yview, bg=self.background_color, troughcolor=self.background_color)
        self.output_text.config(yscrollcommand=scrollbar.set)
        
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.update_output_display()

        input_frame = tk.Frame(self.root, bg=self.frame_color, relief=tk.RAISED, bd=2, highlightbackground=self.border_color, highlightthickness=2)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        
        input_container = tk.Frame(input_frame, bg=self.frame_color)
        input_container.pack(fill=tk.X, padx=10, pady=10)
        

        self.command_entry = tk.Entry(input_container, font=("Helvetica", 12), fg="white", bg=self.background_color, insertbackground="white", relief=tk.FLAT, bd=5)
        self.command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.placeholder_text = "Enter Command..."
        self.showing_placeholder = True
        self.command_entry.insert(0, self.placeholder_text)
        self.command_entry.config(fg="#888888")

        self.command_entry.bind('<FocusIn>', self.on_entry_focus_in)
        self.command_entry.bind('<FocusOut>', self.on_entry_focus_out)
        
        send_btn = tk.Button(input_container, text="Send", command=self.send_command, bg="#2196F3", fg="white", font=("Helvetica", 12), relief=tk.FLAT, padx=20, pady=5)
        send_btn.pack(side=tk.RIGHT)
        
        self.command_entry.bind('<Return>', lambda event: self.send_command())
        
    def update_output_display(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        
        if LAST_GEMINI_OUTPUT:
            self.output_text.insert(tk.END, LAST_GEMINI_OUTPUT)
        else:
            self.output_text.insert(tk.END, "No response yet. Try sending a command...")
            
        self.output_text.config(state=tk.DISABLED)
        
    def on_entry_focus_in(self, event):
        if self.showing_placeholder:
            self.command_entry.delete(0, tk.END)
            self.command_entry.config(fg="white")
            self.showing_placeholder = False
    
    def on_entry_focus_out(self, event):
        if not self.command_entry.get():
            self.command_entry.insert(0, self.placeholder_text)
            self.command_entry.config(fg="#888888")
            self.showing_placeholder = True
    
    def send_command(self):
        command = self.command_entry.get()
        if command and not self.showing_placeholder:
            self.command_entry.delete(0, tk.END)
            self.root.focus()
            
            self.status_label.config(text="Status: Processing...", fg="#FF9800")
            self.root.update()
            
            import threading
            thread = threading.Thread(target=self.process_command_async, args=(command,))
            thread.daemon = True
            thread.start()
    
    def process_command_async(self, command):
        try:
            process_command(command)
            
            self.root.after(0, lambda: self.status_label.config(text="Status: Complete", fg="#4CAF50"))
            
            self.root.after(0, self.update_output_with_latest_response)
            
        except Exception as e:
            error_msg = f"Error processing command: {str(e)}"
            self.root.after(0, self.update_output_with_response, error_msg)
            self.root.after(0, lambda: self.status_label.config(text="Status: Error", fg="#F44336"))
    
    def update_output_with_response(self, text):
        global LAST_GEMINI_OUTPUT
        LAST_GEMINI_OUTPUT = text
        
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(1.0, text)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(1.0)
    
    def update_output_with_latest_response(self):
        global LAST_GEMINI_OUTPUT
        
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        if LAST_GEMINI_OUTPUT:
            self.output_text.insert(1.0, LAST_GEMINI_OUTPUT)
        else:
            self.output_text.insert(1.0, "No response available.")
        self.output_text.config(state=tk.DISABLED)
        self.output_text.see(1.0)
        
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
    initialize()
    dashboard = KiloBuddyDashboard()
    dashboard.run()

# Check for updates
def check_for_updates():
    global VERSION
    url = "https://api.github.com/repos/MichaelCreel/KiloBuddy/releases/latest"
    try:
        response = reqs.get(url, timeout=20)
        if response.status_code == 200:
            data = response.json()
            latest_version = data["tag_name"]
            return latest_version
        else:
            print("Failed to check for updates.")
            return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

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
        print("\nKiloBuddy Shutting Down...")

if __name__ == "__main__":
    if is_kilobuddy_running():
        print("Opening dashboard...")
        show_dashboard()
    else:
        print("Launching KiloBuddy...")
        create_lock_file()
        main()
