# KiloBuddy

KiloBuddy is a powerful computer assistant that helps users execute commands within their system through voice commands. It uses Google Gemini to generate commands and text blocks that help users with computer issues, summaries, or information. It is designed to run on Windows, Mac, and Linux, and comes with a simple installer to automatically install all dependencies.

## No Privacy Guarantee

KiloBuddy uses Google speech recognition and Google Gemini. This means that data is sent to Google's servers for processing. There is no garuntee that your data will not be processed by Google.

KiloBuddy uses Google Speech Recognition and Google Gemini while running. While KiloBuddy does not share any data outside of these services, Google may process your data. Privacy of your data is not guaranteed.

## AI Accuracy

KiloBuddy uses Google Gemini to process user commands. Commands are not verified before being run. Command accuracy and safety are not garunteed.

## Dependencies
- Python, Google Gemini API, PyAudio
  - Windows:
    Install [Python 3](https://python.org)
    Check "Add Python to PATH" during installation
  - Mac:
    ```bash
    brew install python
    ```
  - Linux:
    ```bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```
    
    If PyAudio installation fails, run this command:
    ```bash
    sudo apt-get install portaudio19-dev python3-pyaudio
    ```
## Installation

1. Get a Gemini API Key
  - Open [Google AI Studio](https://aistudio.google.com/apikey)
  - Sign in with your Google account
  - Click "Create API key"
  - Copy the API key when it generates
2. Download the KiloBuddy zip file from [Releases](https://github.com/MichaelCreel/KiloBuddy/releases)
3. Run the install script
  - Windows:
    Run `windows-install.bat`
  - Mac:
    Run `mac-install.command`
  - Linux:
    Run `linux-install.sh`
    If nothing happens, tkinter is probably missing
    Install tkinter:
    ```bash
    sudo apt install python3-tk
    ```
    Or run installer from the terminal:
    ```bash
    python3 Installer.py
    ```
4. If it takes a bit to launch, have some patience
5. Paste your API Key in the input field
6. Click "Install"

## Notes

- Gemini prompt can be changed by editing `prompt` (Good luck, it's sensitive)
- Gemini has limited tokens on free API keys, so AI generation is limited
- There are no included fallbacks if Gemini fails to respond
- The app is unsuccessful sometimes because of AI inaccuracy
- Users can choose to be notified of new pre-releases
- A dashboard is included for text-based interaction

## License

MIT License
