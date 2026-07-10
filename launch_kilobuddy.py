import os
import subprocess
import sys

def main():
    install_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(install_dir)
    venv_python = os.path.join(install_dir, "kilobuddy_env", "Scripts", "pythonw.exe")
    print(venv_python)
    kb_script = os.path.join(install_dir, "KiloBuddy.py")
    print(kb_script)

    if not os.path.exists(venv_python):
        print("No venv found")
        venv_python = sys.executable

    subprocess.Popen([venv_python, kb_script], cwd=install_dir)

if __name__ == "__main__":
    main()