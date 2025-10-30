import sys
import subprocess
import venv
import os
import platform
import shutil

REQUIRED_PACKAGES = ["speechrecognition", "google-generativeai", "pyaudio", "tk", "requests"]

# Remove old installation if exists
def remove_old_installation(install_dir):
    if os.path.exists(install_dir):
        print(f"Removing old installation at: {install_dir}")
        shutil.rmtree(install_dir)

# Get the installation directory for the platform
def get_install_directory():
    system = platform.system()
    if system == "Windows":
        # Windows: %APPDATA%\KiloBuddy
        return os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'KiloBuddy')
    else:
        # Unix (Linux/macOS): ~/.kilobuddy
        return os.path.expanduser('~/.kilobuddy')

# Create and set up directory of installation
def setup_install_directory():
    install_dir = get_install_directory()
    
    if not os.path.exists(install_dir):
        print(f"Creating installation directory: {install_dir}")
        os.makedirs(install_dir, exist_ok=True)
    
    # Copy current files to install directory
    current_files = ['KiloBuddy.py', 'prompt', 'os_version', 'wake_word', 'icon.png', 'version']
    for file in current_files:
        if os.path.exists(file):
            dest_path = os.path.join(install_dir, file)
            print(f"Copying {file} to installation directory...")
            shutil.copy2(file, dest_path)
    
    return install_dir

# Create a virtual environment for the app
def create_virtual_env(install_dir):
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    print(f"Creating virtual environment at: {venv_path}")
    venv.create(venv_path, with_pip=True)
    return venv_path

# Install packages into the virtual environment
def install_packages(install_dir):
    # Use the virtual environment python instead of system python
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python") if platform.system() != "Windows" else os.path.join(venv_path, "Scripts", "python.exe")
    
    for package in REQUIRED_PACKAGES:
        print(f"Installing {package}...")
        subprocess.check_call([python_path, "-m", "pip", "install", package])
    print("KiloBuddy installed successfully. The original download folder can now be deleted.")

def run_terminal_installer():
    print("=== KiloBuddy Installer Terminal Mode ===")
    
    # Remove any old installation first
    install_dir = get_install_directory()
    remove_old_installation(install_dir)
    
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
        
        # Create system shortcuts
        try:
            create_system_shortcuts(install_dir)
        except Exception as e:
            print(f"Could not create shortcuts: {e}")
        
        launch_choice = input("Launch KiloBuddy now? (y/n): ").lower()
        if launch_choice in ['y', 'yes']:
            launch_app(install_dir)
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
    except FileNotFoundError:
        print("Error: Virtual environment not found. Please run installer again.")
    input("Press Enter to exit...")

# Launch KiloBuddy from the installation folder
def launch_app(install_dir):
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python") if platform.system() != "Windows" else os.path.join(venv_path, "Scripts", "python.exe")
    kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
    
    print(f"Launching KiloBuddy from: {install_dir}")
    subprocess.run([python_path, kilobuddy_script], cwd=install_dir)

# Create shortcuts for the app
def create_system_shortcuts(install_dir):
    system = platform.system()
    
    if system == "Linux":
        create_linux_shortcuts(install_dir)
    elif system == "Windows":
        create_windows_shortcuts(install_dir)
    elif system == "Darwin":  # macOS
        create_macos_shortcuts(install_dir)

# Linux Shortcuts
def create_linux_shortcuts(install_dir):
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python")
    kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
    icon_path = os.path.join(install_dir, "icon.png")
    
    # Create .desktop file content
    desktop_content = f"""[Desktop Entry]
Version=0.2
Type=Application
Name=KiloBuddy
Comment=AI Voice Assistant
Exec={python_path} {kilobuddy_script}
Icon={icon_path}
Path={install_dir}
Terminal=true
StartupNotify=true
Categories=Utility;AudioVideo;
Keywords=AI;Assistant;Voice;Gemini;
"""
    
    # Create system menu entry
    applications_dir = os.path.expanduser('~/.local/share/applications')
    os.makedirs(applications_dir, exist_ok=True)
    
    desktop_file_path = os.path.join(applications_dir, 'kilobuddy.desktop')
    with open(desktop_file_path, 'w') as f:
        f.write(desktop_content)
    
    # Make it executable
    os.chmod(desktop_file_path, 0o755)
    print("Added KiloBuddy to system menu")
    
    # For GUI mode, create desktop shortcut by default
    # For terminal mode, ask the user
    if hasattr(create_linux_shortcuts, '_gui_mode') and create_linux_shortcuts._gui_mode:
        # GUI mode - create desktop shortcut automatically
        desktop_dir = os.path.expanduser('~/Desktop')
        if os.path.exists(desktop_dir):
            desktop_shortcut_path = os.path.join(desktop_dir, 'KiloBuddy.desktop')
            with open(desktop_shortcut_path, 'w') as f:
                f.write(desktop_content)
            os.chmod(desktop_shortcut_path, 0o755)
            print("Desktop shortcut created")
    else:
        # Terminal mode - ask user
        create_desktop = input("Create desktop shortcut? (y/n): ").lower().strip()
        if create_desktop in ['y', 'yes']:
            desktop_dir = os.path.expanduser('~/Desktop')
            if os.path.exists(desktop_dir):
                desktop_shortcut_path = os.path.join(desktop_dir, 'KiloBuddy.desktop')
                with open(desktop_shortcut_path, 'w') as f:
                    f.write(desktop_content)
                os.chmod(desktop_shortcut_path, 0o755)
                print("Desktop shortcut created")
            else:
                print("Desktop directory not found")

# Windows Shortcuts
def create_windows_shortcuts(install_dir):
    try:
        import winshell
        from win32com.client import Dispatch
        
        venv_path = os.path.join(install_dir, "kilobuddy_env")
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
        kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
        
        # Create Start Menu shortcut
        start_menu = winshell.start_menu()
        shortcut_path = os.path.join(start_menu, "KiloBuddy.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = python_path
        shortcut.Arguments = f'"{kilobuddy_script}"'
        shortcut.WorkingDirectory = install_dir
        shortcut.IconLocation = python_path
        shortcut.save()
        print("Added KiloBuddy to Start Menu")
        
        # Ask about desktop shortcut
        create_desktop = input("Create desktop shortcut? (y/n): ").lower().strip()
        if create_desktop in ['y', 'yes']:
            desktop = winshell.desktop()
            desktop_shortcut_path = os.path.join(desktop, "KiloBuddy.lnk")
            
            desktop_shortcut = shell.CreateShortCut(desktop_shortcut_path)
            desktop_shortcut.Targetpath = python_path
            desktop_shortcut.Arguments = f'"{kilobuddy_script}"'
            desktop_shortcut.WorkingDirectory = install_dir
            desktop_shortcut.IconLocation = python_path
            desktop_shortcut.save()
            print("Desktop shortcut created")
            
    except ImportError:
        print("Windows shortcut creation requires pywin32. Install with: pip install pywin32 winshell")
# MacOS Shortcuts
def create_macos_shortcuts(install_dir):
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python")
    kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
    
    # Create a simple shell script launcher
    launcher_script = os.path.join(install_dir, "launch_kilobuddy.sh")
    with open(launcher_script, 'w') as f:
        f.write(f"""#!/bin/bash
cd "{install_dir}"
"{python_path}" "{kilobuddy_script}"
""")
    os.chmod(launcher_script, 0o755)
    
    print("Created launcher script")
    print(f"You can run KiloBuddy with: {launcher_script}")
    
    # Ask about desktop shortcut (Alias)
    create_desktop = input("Create desktop alias? (y/n): ").lower().strip()
    if create_desktop in ['y', 'yes']:
        desktop_dir = os.path.expanduser('~/Desktop')
        if os.path.exists(desktop_dir):
            desktop_alias = os.path.join(desktop_dir, 'KiloBuddy')
            try:
                os.symlink(launcher_script, desktop_alias)
                print("Desktop alias created")
            except OSError:
                print("Could not create desktop alias")

def run_gui_installer():
    import tkinter as tk
    from tkinter import messagebox
    from tkinter import ttk
    import threading

    # Remove any old installation first
    install_dir = get_install_directory()
    remove_old_installation(install_dir)

    # Set up installation directory at start
    install_dir = setup_install_directory()

    def save_api_key():
        api_key = api_entry.get().strip()
        if api_key:
            try:
                api_key_path = os.path.join(install_dir, "gemini_api_key")
                with open(api_key_path, "w") as f:
                    f.write(api_key)
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
                
                # Create system shortcuts
                try:
                    # Mark as GUI mode for shortcut creation
                    create_linux_shortcuts._gui_mode = True
                    create_system_shortcuts(install_dir)
                except Exception as e:
                    print(f"Could not create shortcuts: {e}")
                
                install_button.config(state='normal', text="Launch KiloBuddy", command=lambda: launch_app(install_dir))
                messagebox.showinfo("Success", f"KiloBuddy installed successfully!\n\nLocation: {install_dir}\n\nThe original download folder can now be deleted.")
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
    
    # Set installer window icon if icon.png exists
    if os.path.exists("icon.png"):
        try:
            root.iconphoto(False, tk.PhotoImage(file="icon.png"))
        except Exception:
            pass  # If icon fails to load, continue without it

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