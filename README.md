# KiloBuddy

KiloBuddy is a powerful computer assistant that helps users execute commands within their system through voice commands. It utilizes both cloud and local models to generate commands and text blocks that help users with computer issues, summaries, or information. It is designed to run on Windows, Mac, and Linux, and comes with a simple installer to automatically install all dependencies.

## Features

- Voice-controlled computer assistant
- Text-based dashboard
- Cloud and local AI model support
- Automatic command execution with safety framework
- Cross-platform support

## No Privacy Guarantee

KiloBuddy uses cloud and/or local models of your choice. No models are verified for safety or privacy. KiloBuddy does not share any data outside of these services, but your data may be processed by these services. Data privacy is not guaranteed.

## AI Accuracy

KiloBuddy uses AI to process user commands. Only some commands prompt user input. Despite the safety layer in place in KiloBuddy, command accuracy and safety are not guaranteed. By using KiloBuddy, you are accepting the risk of data loss, system corruption, or any other issues that may arise from using KiloBuddy.

## Dependencies
- Python
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
    
    If PyAudio installation fails, run this command (or distribution equivalent):
    ```bash
    sudo apt-get install portaudio19-dev python3-pyaudio
    ```
- (Installed by Installer) PyAudio, Custom Tkinter, Vosk, Google Gemini, OpenAI ChatGPT, Anthropic Claude
## Installation

**1.** Setting up KiloBuddy  
KiloBuddy can use cloud models (Gemini, ChatGPT, Claude) or local models through Ollama. To set up cloud models, follow step **1-1**. To set up local models, read the **Model Notes** section below, and then continue at step **2**.

  - **1-1. (CLOUD MODELS)** Get API Key(s)
    - Gemini
      - Open [Google AI Studio](https://aistudio.google.com/apikey)
    - ChatGPT
      - Open [OpenAI Platform](https://platform.openai.com/api-keys)
    - Claude
      - Open [Anthropic Console](https://console.anthropic.com/)
    - Sign in with your account
    - Click "Create API key"
    - Copy the API key when it generates

**2.** Download the KiloBuddy zip file from [Releases](https://github.com/MichaelCreel/KiloBuddy/releases)

**3.** Run the install script
  - Windows:
    Run `windows-install.bat`
  - Mac:
    Run `mac-install.command`
  - Linux:
    Run `linux-install.sh`
    - If nothing happens, tkinter is probably missing
      - Install tkinter (or distribution equivalent):
        ```bash
        sudo apt install python3-tk
        ```
      - Or run installer from the terminal:
        ```bash
        python3 Installer.py
        ```
**4.** Based on your decision on model, you will follow certain steps. If you are using cloud models, follow step **4-1**. If you are using local models, follow step **4-2**. If you are using both, follow both steps.
  - **4-1. (CLOUD MODELS)** Paste your API key(s) into their respective input fields.
  - **4-2. (LOCAL MODELS)** Follow the steps below.
    - Check "Use Local AI Models"
    - If you have not installed Ollama, click "Install Ollama"
      - This may cause a pop-up for Ollama installation during the installation process; complete this pop-up to install Ollama
    - If you want KiloBuddy to manage the starting and stopping of Ollama, check "Manage Ollama". Read the section on Ollama Management below for more details

**5.** Continue following the installer

## Model Notes

The cloud models Google Gemini, OpenAI ChatGPT, and Anthropic Claude are usable cloud models with KiloBuddy. Local models can also be used with KiloBuddy by installing Ollama (option available in installer) and changing 'AI Provider Preference' in settings. During installation, these local models are provided as viable options:

- Gemma 4 E2B - This is a model created by Google. It is an extremely lightweight model with thinking capabilities. It provides extremely fast generation, but struggles more with multi-step reasoning and understanding tool calls. This results in problems fulfilling complex tasks.
- Gemma 4 E4B - This is a model created by Google. It is a lightweight model with thinking capabilities. It provides fast generation with accurate results. It is suitable for mildly complex multi-step reasoning while maintaining fast generation and accuracy.

While CPU processing is possible with local models, generation will be slow and a discrete video card is recommended for generation. If you do not have a discrete video card, it is recommended to use cloud models instead.

**NOTE: THE FIRST GENERATION OF LOCAL MODELS WILL BE SLOW:**  
When models are first called, they must be loaded into memory. This takes some time, making the first call slow. Future calls will be faster until the model is kicked out of memory or the app is stopped.

## Ollama Management

If KiloBuddy is configured to manage Ollama, it follows these rules:
- If Ollama is running on app launch, KiloBuddy will not manage it
  - This means that KiloBuddy will not interfere with Ollama to avoid disrupting previous operations
- If Ollama is not running on app launch, KiloBuddy will manage the starting and stopping of Ollama

## Notes

- The prompts for models can be changed by editing `initial_prompt` and `prompt` to tune generation
- Cloud model generation is limited by the number of tokens on your account
- Commands will not be processed if any AI fails to respond
- The app will sometimes be unsuccessful due to the AI model generating invalid syntax
- A dashboard is included for text-based interaction
- Any local model can be used by entering the model name as it appears with `ollama list`

## Issues

Issues should be reported on the [Issues Page](https://github.com/MichaelCreel/KiloBuddy/issues). Make sure to include the issue, repeatable steps to the issue (if possible), the operating system, and whether voice or text was used to send the command.

## Licenses

MIT License
Apache-2.0 License

The KiloBuddy app including the code, installer, icon, prompts, install scripts, etc. are all under MIT License. The speech recognition program and model used in KiloBuddy, Vosk, is licensed under the Apache-2.0 License.
