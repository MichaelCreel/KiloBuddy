#!/usr/bin/env python3

import subprocess
import venv
import os
import platform
import shutil
import zipfile
import urllib.request

REQUIRED_PACKAGES = ["google-generativeai", "pyaudio", "tk", "requests", "customtkinter", "vosk"]

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
    current_files = ['KiloBuddy.py', 'prompt', 'os_version', 'wake_word', 'icon.png', 'version', 'updates']
    for file in current_files:
        if os.path.exists(file):
            dest_path = os.path.join(install_dir, file)
            print(f"Copying {file} to installation directory...")
            shutil.copy2(file, dest_path)
    
    return install_dir

# Ask user about update preferences
def ask_update_preferences(install_dir):
    import tkinter as tk
    from tkinter import messagebox

    preference = {"value": "release"}

    def show_update_preference_dialog():
        try:
            dialog = tk.Toplevel()
            dialog.title("Update Notifications")
            dialog.geometry("1000x550")
            dialog.configure(bg="#1e1e1e")
            dialog.resizable(False, False)
            dialog.transient()
            dialog.grab_set()
            
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")

            if os.path.exists("icon.png"):
                try:
                    dialog.iconphoto(False, tk.PhotoImage(file="icon.png"))
                except:
                    pass
            
            main_frame = tk.Frame(dialog, bg="#1e1e1e", padx=30, pady=30)
            main_frame.pack(fill="both", expand=True)
            
            title_label = tk.Label(main_frame, text="Update Notifications", 
                                 font=("Arial", 18, "bold"), 
                                 fg="#4CAF50", bg="#1e1e1e")
            title_label.pack(pady=(0, 20))
            
            desc_text = ("KiloBuddy can notify you when updates are available.\n"
                        "Choose which types of updates you'd like to be notified about:")
            desc_label = tk.Label(main_frame, text=desc_text, 
                                font=("Arial", 11), 
                                fg="white", bg="#1e1e1e",
                                justify="left", wraplength=400)
            desc_label.pack(pady=(0, 25))
            
            radio_frame = tk.Frame(main_frame, bg="#1e1e1e")
            radio_frame.pack(pady=(0, 30))
            
            choice_var = tk.StringVar(value="release")
            
            stable_radio = tk.Radiobutton(radio_frame, 
                                        text="Stable releases only (Recommended)", 
                                        variable=choice_var, 
                                        value="release",
                                        font=("Arial", 11, "bold"),
                                        fg="#4CAF50", bg="#1e1e1e",
                                        selectcolor="#2e2e2e",
                                        activebackground="#1e1e1e",
                                        activeforeground="#4CAF50")
            stable_radio.pack(anchor="w", pady=(0, 5))
            
            all_radio = tk.Radiobutton(radio_frame, 
                                     text="All releases", 
                                     variable=choice_var, 
                                     value="pre-release",
                                     font=("Arial", 11, "bold"),
                                     fg="#FF9800", bg="#1e1e1e",
                                     selectcolor="#2e2e2e",
                                     activebackground="#1e1e1e",
                                     activeforeground="#FF9800")
            all_radio.pack(anchor="w", pady=(0, 5))

            button_frame = tk.Frame(main_frame, bg="#1e1e1e")
            button_frame.pack(pady=(20, 0))
            
            def save_and_close():
                preference["value"] = choice_var.get()
                dialog.destroy()
            
            ok_btn = tk.Button(button_frame, text="Continue", 
                             command=save_and_close,
                             bg="#4CAF50", fg="white", 
                             font=("Arial", 11, "bold"),
                             padx=30, pady=10,
                             relief="flat",
                             cursor="hand2")
            ok_btn.pack()

            dialog.wait_window()
            
        except Exception as e:
            print(f"Error showing update preference dialog: {e}")
            preference["value"] = "release"
    
    show_update_preference_dialog()
    
    # Save the preference to updates file
    try:
        updates_file = os.path.join(install_dir, "updates")
        with open(updates_file, "w") as f:
            f.write(preference["value"])
        print(f"Update preference saved: {preference['value']}")
    except Exception as e:
        print(f"Failed to save update preference: {e}")
    
    return preference["value"]

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

# Download and install Vosk model
def install_vosk_model(install_dir):
    model_dir = os.path.join(install_dir, "vosk-model")
    if os.path.exists(model_dir):
        print("Vosk model already exists, skipping download...")
        return True
    
    print("Downloading Vosk speech recognition model...")
    model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
    model_zip = os.path.join(install_dir, "vosk-model.zip")
    
    try:
        urllib.request.urlretrieve(model_url, model_zip)
        print("Extracting Vosk model...")
        
        with zipfile.ZipFile(model_zip, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        extracted_dir = os.path.join(install_dir, "vosk-model-small-en-us-0.15")
        if os.path.exists(extracted_dir):
            os.rename(extracted_dir, model_dir)
        
        os.remove(model_zip)
        print("Vosk model installed successfully")
        return True
    except Exception as e:
        print(f"Failed to download Vosk model: {e}")
        return False

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
    
    # Ask for update preferences
    print("\n=== Update Notifications ===")
    print("KiloBuddy can notify you when updates are available.")
    print("Choose which types of updates you'd like to be notified about:")
    print("1. Stable releases only (Recommended)")
    print("2. All releases")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice == "1":
            update_preference = "release"
            print("Will notify for stable releases only")
            break
        elif choice == "2":
            update_preference = "pre-release"
            print("Will notify for all releases including pre-releases")
            break
        else:
            print("Please enter 1 or 2")
    
    # Save update preference
    try:
        updates_file = os.path.join(install_dir, "updates")
        with open(updates_file, "w") as f:
            f.write(update_preference)
        print(f"Update preference saved: {update_preference}")
    except Exception as e:
        print(f"Failed to save update preference: {e}")
    
    try:
        # Create virtual environment if it doesn't exist
        venv_path = os.path.join(install_dir, "kilobuddy_env")
        if not os.path.exists(venv_path):
            create_virtual_env(install_dir)
        
        install_packages(install_dir)
        
        # Download and install Vosk model
        if not install_vosk_model(install_dir):
            print("Warning: Failed to install Vosk model. Speech recognition may not work.")
        
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
    
    # Create background launcher script
    launcher_script = os.path.join(install_dir, "launch_kilobuddy.sh")
    with open(launcher_script, 'w') as f:
        f.write(f"""#!/bin/bash
# Launch KiloBuddy without terminal window
cd "{install_dir}"
nohup "{python_path}" "{kilobuddy_script}" > /dev/null 2>&1 &
""")
    os.chmod(launcher_script, 0o755)
    
    # Create .desktop file content (background mode)
    desktop_content = f"""[Desktop Entry]
Version=1.1
Type=Application
Name=KiloBuddy
Comment=AI Voice Assistant (Background Mode)
Exec={launcher_script}
Icon={icon_path}
Path={install_dir}
Terminal=false
StartupNotify=false
Categories=Utility;AudioVideo;
Keywords=AI;Assistant;Voice;Gemini;
NoDisplay=false
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
        pythonw_path = os.path.join(venv_path, "Scripts", "pythonw.exe")
        kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
        
        # Create Start Menu shortcut
        start_menu = winshell.start_menu()
        shortcut_path = os.path.join(start_menu, "KiloBuddy.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = pythonw_path
        shortcut.Arguments = f'"{kilobuddy_script}"'
        shortcut.WorkingDirectory = install_dir
        if os.path.exists(os.path.join(install_dir, "icon.png")):
            shortcut.IconLocation = os.path.join(install_dir, "icon.png")
        else:
            shortcut.IconLocation = pythonw_path
        shortcut.save()
        print("Added KiloBuddy to Start Menu")
        
        # Ask about desktop shortcut
        create_desktop = input("Create desktop shortcut? (y/n): ").lower().strip()
        if create_desktop in ['y', 'yes']:
            desktop = winshell.desktop()
            desktop_shortcut_path = os.path.join(desktop, "KiloBuddy.lnk")
            
            desktop_shortcut = shell.CreateShortCut(desktop_shortcut_path)
            desktop_shortcut.Targetpath = pythonw_path
            desktop_shortcut.Arguments = f'"{kilobuddy_script}"'
            desktop_shortcut.WorkingDirectory = install_dir
            if os.path.exists(os.path.join(install_dir, "icon.png")):
                desktop_shortcut.IconLocation = os.path.join(install_dir, "icon.png")
            else:
                desktop_shortcut.IconLocation = pythonw_path
            desktop_shortcut.save()
            print("Desktop shortcut created")
            
    except ImportError:
        print("Windows shortcut creation requires pywin32. Install with: pip install pywin32 winshell")
# MacOS Shortcuts
def create_macos_shortcuts(install_dir):
    venv_path = os.path.join(install_dir, "kilobuddy_env")
    python_path = os.path.join(venv_path, "bin", "python")
    kilobuddy_script = os.path.join(install_dir, "KiloBuddy.py")
    
    # Create a background launcher
    launcher_script = os.path.join(install_dir, "launch_kilobuddy.sh")
    with open(launcher_script, 'w') as f:
        f.write(f"""#!/bin/bash
cd "{install_dir}"
nohup "{python_path}" "{kilobuddy_script}" > /dev/null 2>&1 &
""")
    os.chmod(launcher_script, 0o755)
    
    # Create an AppleScript app for GUI launch (no terminal)
    app_path = os.path.join(install_dir, "KiloBuddy.app")
    contents_dir = os.path.join(app_path, "Contents")
    macos_dir = os.path.join(contents_dir, "MacOS")
    resources_dir = os.path.join(contents_dir, "Resources")
    
    # Create app bundle structure
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)
    
    # Create Info.plist
    info_plist = os.path.join(contents_dir, "Info.plist")
    with open(info_plist, 'w') as f:
        f.write("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>KiloBuddy</string>
    <key>CFBundleIdentifier</key>
    <string>com.kilobuddy.app</string>
    <key>CFBundleName</key>
    <string>KiloBuddy</string>
    <key>CFBundleVersion</key>
    <string>1.1</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>""")
    
    # Create the executable launcher
    app_launcher = os.path.join(macos_dir, "KiloBuddy")
    with open(app_launcher, 'w') as f:
        f.write(f"""#!/bin/bash
cd "{install_dir}"
exec "{python_path}" "{kilobuddy_script}"
""")
    os.chmod(app_launcher, 0o755)
    
    # Copy icon if available
    icon_src = os.path.join(install_dir, "icon.png")
    if os.path.exists(icon_src):
        icon_dst = os.path.join(resources_dir, "icon.png")
        shutil.copy2(icon_src, icon_dst)
    
    print("Created KiloBuddy.app")
    print(f"You can run KiloBuddy with: open '{app_path}'")
    
    # Ask about desktop shortcut (Alias to .app)
    create_desktop = input("Create desktop alias? (y/n): ").lower().strip()
    if create_desktop in ['y', 'yes']:
        desktop_dir = os.path.expanduser('~/Desktop')
        if os.path.exists(desktop_dir):
            desktop_alias = os.path.join(desktop_dir, 'KiloBuddy.app')
            try:
                if os.path.exists(desktop_alias):
                    os.remove(desktop_alias)
                os.symlink(app_path, desktop_alias)
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
        
        # Ask for update preferences
        try:
            ask_update_preferences(install_dir)
        except Exception as e:
            print(f"Failed to get update preferences: {e}")
            # Continue with installation even if preference dialog fails
            
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
                
                # Download and install Vosk model
                progress['value'] = 85
                root.update_idletasks()
                if not install_vosk_model(install_dir):
                    print("Warning: Failed to install Vosk model. Speech recognition may not work.")
                
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