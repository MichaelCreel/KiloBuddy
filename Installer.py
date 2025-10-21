import sys
import subprocess
import venv
import os
import platform
import shutil

REQUIRED_PACKAGES = ["speechrecognition", "google-generativeai", "pyaudio"]

def get_install_directory():
    """Get the platform-appropriate installation directory"""
    system = platform.system()
    if system == "Windows":
        # Windows: %APPDATA%\KiloBuddy
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'KiloBuddy')
    else:
        # Unix (Linux/macOS): ~/.kilobuddy
        return os.path.expanduser('~/.kilobuddy')

def setup_install_directory():
    """Create and set up the installation directory"""
    install_dir = get_install_directory()
    
    if not os.path.exists(install_dir):
        print(f"Creating installation directory: {install_dir}")
        os.makedirs(install_dir, exist_ok=True)
    
    # Copy current files to install directory
    current_files = ['KiloBuddy.py', 'prompt', 'os_version', 'wake_word']
    for file in current_files:
        if os.path.exists(file):
            dest_path = os.path.join(install_dir, file)
            print(f"Copying {file} to installation directory...")
            shutil.copy2(file, dest_path)
    
    return install_dir

def create_virtual_env(install_dir):
    """Create virtual environment in the install directory"""
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    print(f"Creating virtual environment at: {venv_path}")
    venv.create(venv_path, with_pip=True)
    return venv_path

def install_packages(install_dir):
    """Install packages in the virtual environment"""
    # Use the virtual environment python instead of system python
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python") if platform.system() != "Windows" else os.path.join(venv_path, "Scripts", "python.exe")
    
    for package in REQUIRED_PACKAGES:
        print(f"Installing {package}...")
        subprocess.check_call([python_path, "-m", "pip", "install", package])
    print("KiloBuddy installed successfully.")

def run_terminal_installer():
    print("=== KiloBuddy Installer Terminal Mode ===")
    
    # Set up installation directory
    install_dir = setup_install_directory()
    
    # Get API key from user
    print("Get your API key from: https://aistudio.google.com/api-keys")
    api_key = input("Enter your Gemini API Key: ").strip()
    if api_key:
        try:
            api_key_path = os.path.join(install_dir, "gemini_api_key")
            with open(api_key_path, "w") as f:
                f.write(api_key)
            print("API key saved!")
        except Exception as e:
            print(f"Failed to save API key: {e}")
            return
    else:
        print("API key is required for KiloBuddy to work")
        return
    
    try:
        # Create virtual environment if it doesn't exist
        venv_path = os.path.join(install_dir, "kilobuddy_env")
        if not os.path.exists(venv_path):
            create_virtual_env(install_dir)
        
        install_packages(install_dir)
        
        print(f"\nKiloBuddy installed successfully!")
        print(f"Installation location: {install_dir}")
        
        launch_choice = input("Launch KiloBuddy now? (y/n): ").lower()
        if launch_choice in ['y', 'yes']:
            launch_app(install_dir)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
    except FileNotFoundError:
        print("Error: Virtual environment not found. Please run installer again.")
    input("Press Enter to exit...")

def launch_app(install_dir):
    """Launch KiloBuddy from the installation directory"""
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python") if platform.system() != "Windows" else os.path.join(venv_path, "Scripts", "python.exe")
    kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
    
    print(f"Launching KiloBuddy from: {install_dir}")
    subprocess.run([python_path, kilobuddy_script], cwd=install_dir)

def run_gui_installer():
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk
    import threading

    # Set up installation directory at start
    install_dir = setup_install_directory()

    def save_api_key():
        api_key = api_entry.get().strip()
        if api_key:
            try:
                api_key_path = os.path.join(install_dir, "gemini_api_key")
                with open(api_key_path, "w") as f:
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
                
                # Create virtual environment if it doesn't exist
                venv_path = os.path.join(install_dir, "kilobuddy_env")
                if not os.path.exists(venv_path):
                    progress['value'] = 10
                    root.update_idletasks()
                    create_virtual_env(install_dir)
                
                # Use the virtual environment python
                python_path = os.path.join(venv_path, "bin", "python") if platform.system() != "Windows" else os.path.join(venv_path, "Scripts", "python.exe")
                
                total_packages = len(REQUIRED_PACKAGES)
                base_progress = 20  # 20% for setup
                for i, package in enumerate(REQUIRED_PACKAGES):
                    print(f"Installing {package}...")
                    subprocess.check_call([python_path, "-m", "pip", "install", package])
                    # Update progress bar (remaining 80% for packages)
                    progress['value'] = base_progress + ((i + 1) / total_packages) * 80
                    root.update_idletasks()
                
                print("KiloBuddy installed successfully.")
                progress['value'] = 100
                install_button.config(state='normal', text="Launch KiloBuddy", command=lambda: launch_app(install_dir))
                messagebox.showinfo("Success", f"KiloBuddy installed successfully!\n\nLocation: {install_dir}")
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
    root.geometry("800x650")
    root.configure(bg="#190c3a")

    title = tk.Label(root, text="Install KiloBuddy", font=("Helvetica", 32), fg="white", bg="#190c3a")
    title.pack(pady=20)

    # Show installation directory
    install_info = tk.Label(root, text=f"Installing to: {install_dir}", 
                           font=("Helvetica", 10), fg="#cccccc", bg="#190c3a")
    install_info.pack(pady=5)

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
    try:
        import tkinter
        run_gui_installer()
    except ImportError:
        run_terminal_installer()