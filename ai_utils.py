import google.generativeai as genai
from groq import Groq
import requests, json
# import google.api_core.exceptions
# import sqlite3
import streamlit as st


# --- MODULAR AI ROUTER WITH AUTO-DISCOVERY ---
def validate_and_generate(provider, model_name, api_key, prompt=None, system_prompt=None):
    """
    Handles API calls with dynamic model discovery for Gemini
    to avoid 404 and naming convention errors.
    """
    api_key = api_key.strip()

    try:
        if provider == "Gemini":
            genai.configure(api_key=api_key)

            # --- START AUTO-DISCOVERY LOGIC ---
            # This replicates your old code's success
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

            # Try to use what the user selected, but if not found, find the best match
            # e.g., if user selected 'gemini-1.5-flash', look for 'models/gemini-1.5-flash'
            actual_model_name = None
            if any(model_name in m for m in available_models):
                actual_model_name = [m for m in available_models if model_name in m][0]
            else:
                # Fallback to the first available model if selection fails
                actual_model_name = available_models[0]
            # --- END AUTO-DISCOVERY LOGIC ---

            # Use system_instruction if supported by the provider
            model = genai.GenerativeModel(actual_model_name, system_instruction=system_prompt)

            if prompt:
                response = model.generate_content(prompt)
                return response.text
            else:
                return f"✅ Connected: {actual_model_name}"

        elif provider == "Groq":
            client = Groq(api_key=api_key)
            if prompt:
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                completion = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.7
                )
                return completion.choices[0].message.content
            else:
                client.models.list()
                return f"✅ Connected: {model_name}"

        elif provider == "OpenRouter":
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8501", 
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt if prompt else "Hello"})

            data = {
                "model": model_name,
                "messages": messages
            }
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'] if prompt else f"✅ Connected: {model_name}"
            else:
                return f"API_ERROR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"API_ERROR: {str(e)}"