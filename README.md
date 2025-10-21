# KiloBuddy

KiloBuddy is a powerful computer assitant to assist users in executing commands within their system through voice commands. It uses Google Gemini to generate commands and text blocks that help users with computer issues, summaries, or information. It is designed to run on Windows, Mac, and Linux, and comes with a simple installer to automatically install all dependencies.

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
2. Run `Installer.py`
3. If it takes a bit to launch, have some patience
4. Paste your API Key in the input field
5. Click "Install"

## Notes

- Gemini prompt can be changed by editing `prompt` (Good luck, it's sensitive)
- Gemini has limited tokens on free API keys, so AI generation is limited
- There are no included fallbacks if Gemini fails to respond
- The app is unsuccessful sometimes because of AI inaccuracy

## License

MIT License
