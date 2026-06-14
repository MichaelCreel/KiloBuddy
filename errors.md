# FATAL (0-100)

0 - Failed to properly initialize prompt.
    This means that the script failed to read the 'prompt' file for the generation instructions. The app requires the prompt for proper generation for parsing and will quit. The file may not exist or may be empty.

1 - Failed to initialize Vosk speech recognition.
    This means that the script failed to start up the speech recognition for Vosk. The app requires Vosk for detecting speech and will quit. The Vosk model may not have loaded properly or the Vosk model may not be installed.

2 - Failed to initialize KiloBuddy.
    This means that the script experienced an error while initializing necessary assets for the app. The app will quit.

# ERRORS (101-300 : MISS 110, 113, 117, 120, 123)

101 - Invalid update type in file.
    This means that the script read a string from 'updates' that was not 'release' or 'pre-release'. The app will fallback to the type 'release' and will not fail. The file contains a string that is incorrectly formatted.

102 - Updates file not found.
    This means that the 'updates' file does not exist. The app will fallback to the type 'release' and will not fail.

103 - Failed to load update type.
    This means that the script had an unknown error while reading the 'updates' file. The app will fallback to the type 'release' and will not fail.

104 - Version not found.
    This means that the script read a string from 'version' that was 'empty', 'null', or 'none'. The app will fallback to the version 'v0.0' and will not fail. The file contains a string that is incorrectly formatted.

105 - Version file not found.
    This means that the 'version' file does not exist. The app will fallback to the version 'v0.0' and will not fail.

106 - Failed to load version.
    This means that the script had an unknown error while reading the 'version' file. The app will fallback to the version 'v0.0' and will not fail.

107 - OS version file not found.
    This means that the 'os_version' file does not exist. The app will fallback to auto-detecting the operating system and will not fail.

108 - Failed to load OS version.
    This means that the script had an unknown error while reading the 'os_version' file. The app will fallback to auto-detecting the operating system and will not fail.

109 - Invalid wake word.
    This means that the script read a string from 'settings' that was not a valid wake word. The app will fallback to the wake word 'computer' and will not fail.

111 - Failed to parse wake word.
    This means that the script had an unknown error while reading the wake word from 'settings'. The app will fallback to the wake word 'computer' and will not fail.

112 - Invalid AI preference.
    This means that the script read a string from 'settings' that was not a valid preference. The app will fallback to the order 'gemini, chatgpt, claude' and will not fail.

114 - Failed to parse AI preference.
    This means that the script had an unknown error while reading the preference from 'settings'. The app will fallback to the order 'gemini, chatgpt, claude' and will not fail.

115 - Invalid Gemini API key format.
    This means that the script read a string from 'settings' that was not a valid API key for Gemini. The app will not fail, but will be unable to use Gemini.

116 - Failed to parse Gemini API key.
    This means that the script had an unknown error reading the Gemini API key from 'settings'. The app will not fail, but will be unable to use Gemini.

118 - Invalid ChatGPT API key format.
    This means that the script read a string from 'settings' that was not a valid API key for ChatGPT. The app will not fail, but will be unable to use ChatGPT.

119 - Failed to parse ChatGPT API key.
    This means that the script had an unknown error reading the ChatGPT API key from 'settings'. The app will not fail, but will be unable to use ChatGPT.

121 - Invalid Claude API key format.
    This means that the script read a string from 'settings' that was not a valid API key for Claude. The app will not fail, but will be unable to use Claude.

122 - Failed to parse Cluade API key.
    This means that the script had an unknown error reading the Claude API key from 'settings'. The app will not fail, but will be unable to use ChatGPT.

124 - Prompt file is empty.
    This means that the script found the prompt length to be zero. The app requires the prompt file for proper generation parsing and will fail.

125 - Prompt file not found.
    This means that the file 'prompt' does not exist. The app requires the prompt file for proper generation parsing and will fail.

126 - Failed to load prompt.
    This means that the script had an unknown error while reading the 'prompt' file. The app requires the prompt file for proper generation parsing and will fail.

127 - Unrecognized AI model preference.
    This means that the script has a model preference saved to the AI_PREFERENCE variable that was not correctly parsed. The generation will fail but the app will keep running.

128 - Failed to generate text with ChatGPT.
    This means that the script had an unknown error while trying to use ChatGPT to generate text. The generation will fail, but the app will keep running. The ChatGPT API key may be invalid.

129 - ChatGPT API Timeout.
    This means that the ChatGPT API did not respond before the maximum time allowed for generation was reached. The generation will fail, but the app will keep running.

130 - Failed to generate text with Claude.
    This means that the script had an unknown error while trying to use Claude to generate text. The generation will fail, but the app will keep running. The Claude API key may be invalid.

131 - Claude API Timeout.
    This means that the Claude API did not respond before the maximum time allowed for generation was reached. The generation will fail, but the app will keep running.

132 - Failed to generate text with Gemini.
    This means that the script had an unknown error while trying to use Gemini to generate text. The generation will fail, but the app will keep running. The Gemini API key may be invalid.

133 - Gemini API Timeout.
    This means that the Gemini API did not respond before the maximum time allowed for generation was reached. The generation will fail, but the app will keep running.

134 - Failed to listen for wake word.
    This means that Vosk failed to start up properly. The app will try to restart Vosk every 0.25 seconds and will not fail.

135 - Failed to listen for command.
    This means that Vosk failed to start up properly. The listening will stop, but the app will keep running.

136 - No response generated.
    This means that the script received no response from generation. Command processing will fail, but the app will keep running.

137 - Failed to initialize KiloBuddy.
    This means that the script had an error during the initialization process. The app will continue to run but may not function properly.

138 - Couldn't show failure notification.
    This means that the script failed to show a failure notification when an error occurred. The app will not fail.

139 - Couldn't show update notification.
    This means that the script failed to show an update notification when an update was available. The app will not fail.

140 - Failed to check for updates.
    This means that the script had an unknown error while accessing the releases page for the app. The app will not be able to find updates, but will not fail.

141 - Failed to prompt for administrator confirmation.
    This means that the script couldn't prompt the user to enter the password for the administrator account and couldn't run the command because of it.

142 - Dangerous command failed or was canceled.
    This means that the command run was declined by the user or that the command failed when it was run.

143 - Invalid timeout.
    This means that the script read a string from 'settings' that was not within a valid timeout range. The app will fallback to the timeout '15' (seconds) and will not fail. Timeout may be less than 5 or greater than 120.

144 - Invalid timeout format.
    This means that the script read a string from 'settings' that was not a valid timeout. The app will fallback to the timeout '15' (seconds) and will not fail. Timeout may not be an integer.

145 - Failed to parse timeout.
    This means that the script had an unknown error while reading the timeout from 'settings'. The app will fallback to the timeout '15' (seconds) and will not fail.

146 - Settings file not found.
    This means that the 'settings' file does not exist. The app will fallback to default configurations and will not fail.

147 - Permission denied reading settings file.
    This means that the script doesn't have permission to read the 'settings' file. The app will fallback to default configurations and will not fail.

148 - Failed to load settings file.
    This means that the script had an unknown error while reading the 'settings' file. The app will fallback to default configurations and will not fail.

# WARN (301+)

301 - Failed to properly retrieve update type preference.
    This means that the script failed to read the 'updates' file for update preference type. The app will fallback to the type 'release' and will not fail. The file may not exist or may be empty.

302 - Failed to properly retrieve current app version.
    This means that the script failed to read the 'version' file for the installed app version. The app will fallback to the version 'v0.0' and will not fail. The file may not exist or may be empty. The app may prompt the user to update their app.

303 - Failed to properly initialize Gemini API key.
    This means that the script failed to read the 'gemini_api_key' file for the user's Gemini API key. The app will not fail, but will be unable to use Gemini. The file may not exist or may be empty.

304 - Failed to properly initialize ChatGPT API key.
    This means that the script failed to read the 'chatgpt_api_key' file for the user's ChatGPT API key. The app will not fail, but will be unable to use ChatGPT. The file may not exist or may be empty.

305 - Failed to properly initialize Claude API key.
    This means that the script failed to read the 'claude_api_key' file for the user's Claude API key. The app will not fail, but will be unable to use Claude. The file may not exist or may be empty.

306 - Failed to properly initialize AI preference.
    This means that the script failed to read the 'ai_preference' file for the user's AI provider priority. The app will fallback to the order 'gemini, chatgpt, claude' and will not fail. The file may not exist or may be empty.

307 - Failed to properly initialize wake word.
    This means that the script failed to read the 'wake_word' file for the user's wake word. The app will fallback to the word 'computer' and will not fail. The file may not exist or may be empty.

308 - Failed to properly initialize OS version.
    This means that the script failed to read the 'os_version' file for the user's operating system. The app will fallback to auto-detecting the operating system and will not fail. Commands generated may not be correct based on the auto-detected operating system. The file may not exist or may be empty.

309 - No releases found on GitHub repository.
    This means that the releases page could not be found. The app will not be able to find updates, but will not fail.

310 - Failed to check for updates.
    This means that the script had an unknown error while accessing the releases page for the app. The app will not be able to find updates, but will not fail.

311 - Unrecognized AI model.
    This means that the script failed to understand the model choice read from the file 'ai_preferences'. The app will try the next model in line if it exists and will not fail. The model name may be spelled incorrectly.

312 - Failed to properly initialize API timeout.
    This means that the script failed to read the timeout from the 'settings' file. The app will fallback to the timeout '15' (seconds) and will not fail.

313 - Settings file is empty.
    This means that the 'settings' file exists but contains no data. The app will fallback to default configurations and will not fail.


