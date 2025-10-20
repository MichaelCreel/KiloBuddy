import speech_recognition as sr
import re
import os
import google.generativeai as genai

API_TIMEOUT = 10 # Duration for API Response in seconds
GEMINI_API_KEY = "" # API Key for calling Gemini API, loaded from gemini_api_key file
PROMPT = "Return 'Prompt not loaded'." # Prompt for Gemini API Key call, loaded from prompt file