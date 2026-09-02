import json
from google import genai
import requests
from auth_utils import get_secret
import streamlit as st

_gemini_key_index = 0

# --- MODULAR AI ROUTER WITH AUTO-DISCOVERY ---
def validate_and_generate(provider, model_name, api_keys, prompt=None, system_prompt=None, allow_fallback=True):
    """
    Handles API calls with dynamic model discovery for Gemini
    to avoid 404 and naming convention errors.
    Implements simple API key rotation for Gemini if multiple keys are provided.
    """
    global _gemini_key_index

    if isinstance(api_keys, str):
        api_keys = [api_keys.strip()]
    api_keys = [k.strip() for k in api_keys if k.strip()]

    if not api_keys:
        return "API_ERROR: No API keys provided for the selected provider."

    try:
        if provider == "Gemini":
            num_keys = len(api_keys)
            _gemini_key_index %= num_keys
            last_error = None
            for _ in range(num_keys):
                current_key_index = _gemini_key_index
                current_api_key = api_keys[current_key_index]
                
                try:
                    client = genai.Client(api_key=current_api_key)

                    if prompt:
                        response = client.models.generate_content(
                            model=model_name, 
                            contents=prompt,
                            config={'system_instruction': system_prompt}
                        )
                        return response.text
                    else:
                        client.models.generate_content(
                            model=model_name,
                            contents="Ping",
                            config={"max_output_tokens": 1}
                        )
                        return f"✅ Connected: {model_name}"
                except Exception as e:
                    last_error = str(e)
                    _gemini_key_index = (current_key_index + 1) % num_keys
                    # If more keys are available, try the next one.
                    if num_keys > 1:
                        continue
                    # Single key failed; keep the error but still run fallbacks below.

            # Gemini is the fallback when the primary OpenRouter route is unavailable.
            if prompt and allow_fallback:
                or_fallback_key = get_secret(["OPENROUTER_API_KEY"], "OPENROUTER_API_KEY")
                if or_fallback_key:
                    or_model = get_secret(["OPENROUTER_FALLBACK_MODEL"], "OPENROUTER_FALLBACK_MODEL") or "google/gemini-3.5-flash-lite"
                    st.toast(f"🔄 Gemini failed. Attempting OpenRouter ({or_model}) fallback...", icon="⚠️")
                    return validate_and_generate("OpenRouter", or_model, [or_fallback_key], prompt, system_prompt)

            if last_error:
                if "429" in last_error:
                    return "API_ERROR: The free AI service is currently at capacity. Please try again in a minute."
                return f"API_ERROR: {last_error}"
            return "API_ERROR: All available Gemini keys were exhausted and no fallback was found."

        elif provider == "OpenRouter":
            headers = {
                "Authorization": f"Bearer {api_keys[0]}",
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
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data), timeout=60)
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'] if prompt else f"✅ Connected: {model_name}"
            if prompt and allow_fallback:
                gemini_key_raw = get_secret(["INTERNAL_AI_KEY"], "INTERNAL_AI_KEY")
                if gemini_key_raw:
                    gemini_keys = [k.strip() for k in str(gemini_key_raw).split(',') if k.strip()]
                    gemini_model = "gemini-3.5-flash"
                    st.toast(f"🔄 OpenRouter failed. Attempting Gemini ({gemini_model}) fallback...", icon="⚠️")
                    return validate_and_generate("Gemini", gemini_model, gemini_keys, prompt, system_prompt, allow_fallback=False)
            return f"API_ERROR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"API_ERROR: {str(e)}"