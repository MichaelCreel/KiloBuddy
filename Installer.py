import sys
import subprocess
import venv
import os
import platform

REQUIRED_PACKAGES = ["speechrecognition", "google-generativeai", "pyaudio"]

def create_virtual_env():
    print("Creating virtual environment...")
    venv.create("kilobuddy_env", with_pip=True)

def install_packages():
    # Use the virtual environment python instead of system python
    python_path = os.path.join("kilobuddy_env", "bin", "python") if platform.system() != "Windows" else os.path.join("kilobuddy_env", "Scripts", "python.exe")
    
    for package in REQUIRED_PACKAGES:
        print(f"Installing {package}...")
        subprocess.check_call([python_path, "-m", "pip", "install", package])
    print("KiloBuddy installed successfully.")

def run_terminal_installer():
    print("=== KiloBuddy Installer Terminal Mode ===")
    
    # Get API key from user
    print("Get your API key from: https://aistudio.google.com/api-keys")
    api_key = input("Enter your Gemini API Key: ").strip()
    if api_key:
        try:
            with open("gemini_api_key", "w") as f:
                f.write(api_key)
            print("API key saved!")
        except Exception as e:
            print(f"Failed to save API key: {e}")
            return
    else:
        print("API key is required for KiloBuddy to work")
        return
    
    try:
        install_packages()
        launch_choice = input("Launch KiloBuddy now? (y/n): ").lower()
        if launch_choice in ['y', 'yes']:
            launch_app()
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
    except FileNotFoundError:
        print("Error: Virtual environment not found. Please run installer again.")
    input("Press Enter to exit...")

def launch_app():
    python_path = os.path.join("kilobuddy_env", "bin", "python") if platform.system() != "Windows" else os.path.join("kilobuddy_env", "Scripts", "python.exe")
    subprocess.run([python_path, "KiloBuddy.py"])

def run_gui_installer():
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk
    import threading

    def save_api_key():
        api_key = api_entry.get().strip()
        if api_key:
            try:
                with open("gemini_api_key", "w") as f:
                    f.write(api_key)
                messagebox.showinfo("Success", "API key saved!")
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save API key: {e}")
                return False
        else:
            messagebox.showwarning("Warning", "Please enter your API key first")
            return False

    def start_install():
        # Save API key first
        if not save_api_key():
            return
            
        def install_thread():
            try:
                # Reset progress bar
                progress['value'] = 0
                install_button.config(state='disabled', text='Installing...')
                
                # Use the virtual environment python instead of system python
                python_path = os.path.join("kilobuddy_env", "bin", "python") if platform.system() != "Windows" else os.path.join("kilobuddy_env", "Scripts", "python.exe")
                
                total_packages = len(REQUIRED_PACKAGES)
                for i, package in enumerate(REQUIRED_PACKAGES):
                    print(f"Installing {package}...")
                    subprocess.check_call([python_path, "-m", "pip", "install", package])
                    # Update progress bar
                    progress['value'] = ((i + 1) / total_packages) * 100
                    root.update_idletasks()
                
                print("KiloBuddy installed successfully.")
                progress['value'] = 100
                install_button.config(state='normal', text="Launch KiloBuddy", command=launch_app)
                messagebox.showinfo("Success", "KiloBuddy installed successfully.")
            except subprocess.CalledProcessError as e:
                install_button.config(state='normal', text="Install")
                messagebox.showerror("Error", f"Error installing packages: {e}")
            except FileNotFoundError as e:
                install_button.config(state='normal', text="Install")
                messagebox.showerror("Error", f"Virtual environment error: {e}")
        
        # Run installation in a separate thread so GUI doesn't freeze
        threading.Thread(target=install_thread, daemon=True).start()

    root = tk.Tk()
    root.title("KiloBuddy Installer")
    root.geometry("800x600")
    root.configure(bg="#190c3a")

    title = tk.Label(root, text="Install KiloBuddy", font=("Helvetica", 32), fg="white", bg="#190c3a")
    title.pack(pady=20)

    # API Key input section
    api_label = tk.Label(root, text="Enter your Gemini API Key:", font=("Helvetica", 14), fg="white", bg="#190c3a")
    api_label.pack(pady=(20, 5))

    api_entry = tk.Entry(root, width=60, font=("Helvetica", 10), show="*")
    api_entry.pack(pady=5)

    api_help = tk.Label(root, text="Get your API key from: https://aistudio.google.com/api-keys", 
                       font=("Helvetica", 10), fg="#cccccc", bg="#190c3a")
    api_help.pack(pady=5)

    progress = ttk.Progressbar(root, orient="horizontal", length=750, mode="determinate")
    progress.pack(pady=20)

    note = tk.Label(root, text="Just click the button (with internet)", font=("Helvetica", 12), fg="white", bg="#190c3a")
    note.pack(pady=20)

    install_button = tk.Button(root, text="Install", command=start_install, width=35, height=2)
    install_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    if not os.path.exists("kilobuddy_env"):
        create_virtual_env()
    try:
        import tkinter
        run_gui_installer()
    except ImportError:
        run_terminal_installer()