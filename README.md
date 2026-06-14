# KiloBuddy

KiloBuddy is a powerful computer assistant that helps users execute commands within their system through voice commands. It uses Google Gemini, OpenAI ChatGPT, or Anthropic Claude to generate commands and text blocks that help users with computer issues, summaries, or information. It is designed to run on Windows, Mac, and Linux, and comes with a simple installer to automatically install all dependencies.

## No Privacy Guarantee

KiloBuddy uses Google Gemini, OpenAI ChatGPT, or Anthropic Claude while running. While KiloBuddy does not share any data outside of these services, your data may be processed by these services. Data privacy is not garunteed.

## AI Accuracy

KiloBuddy uses Google Gemini, OpenAI ChatGPT, or Anthropic Claude to process user commands. Only some commands prompt user input. Command accuracy and safety are not garunteed.

## Dependencies
- Python, PyAudio, Custom Tkinter, Vosk, Google Gemini, OpenAI ChatGPT, Anthropic Claude
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

1. Get an API Key
  - Gemini
    - Open [Google AI Studio](https://aistudio.google.com/apikey)
  - ChatGPT
    - Open [OpenAI Platform](https://platform.openai.com/api-keys)
  - Claude
    - Open [Anthropic Console](https://console.anthropic.com/)
  - Sign in with your account
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
    - If nothing happens, tkinter is probably missing
      - Install tkinter:
        ```bash
        sudo apt install python3-tk
        ```
      - Or run installer from the terminal:
        ```bash
        python3 Installer.py
        ```
4. Paste your API key into the proper input field
5. Click "Install"

## Notes

- Prompt can be changed by editing `prompt` (Good luck, it's sensitive)
- AI generation is limited by the number of tokens on your account
- Commands will not be processed if any AI fails to respond
- The app is unsuccessful sometimes because of AI inaccuracy
- Users can choose to be notified of new pre-releases
- A dashboard is included for text-based interaction

## Licenses

MIT License
Apache-2.0 License

The KiloBuddy app including the code, installer, icon, prompt, install scripts, etc. are all under MIT License. The speech recognition program and model used in KiloBuddy, Vosk, is licensed under the Apache-2.0 License.
