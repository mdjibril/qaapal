import json
from google.oauth2 import service_account
from google import genai
from google.genai import types
from groq import Groq
import requests
from auth_utils import get_secret
import streamlit as st

_gemini_key_index = 0

# --- MODULAR AI ROUTER WITH AUTO-DISCOVERY ---
def validate_and_generate(provider, model_name, api_keys, prompt=None, system_prompt=None):
    """
    Handles API calls with dynamic model discovery for Gemini
    to avoid 404 and naming convention errors.
    Implements simple API key rotation for Gemini if multiple keys are provided.
    """
    global _gemini_key_index

    if isinstance(api_keys, str):
        api_keys = [api_keys.strip()]
    api_keys = [k.strip() for k in api_keys if k.strip()]

    if provider != "VertexAI" and not api_keys:
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

            # --- FALLBACK MECHANISM ---
            # If all Gemini keys fail during a generation request, try other providers if keys exist in secrets
            if prompt:
                # 1. Try Groq Fallback
                groq_fallback_key = get_secret(["GROQ_API_KEY"], "GROQ_API_KEY")
                if groq_fallback_key:
                    groq_model = get_secret(["GROQ_FALLBACK_MODEL"], "GROQ_FALLBACK_MODEL") or "llama-3.3-70b-versatile"
                    st.toast(f"🔄 Gemini exhausted. Attempting Groq ({groq_model}) fallback...", icon="⚠️")
                    return validate_and_generate("Groq", groq_model, [groq_fallback_key], prompt, system_prompt)

                # 2. Try OpenRouter Fallback
                or_fallback_key = get_secret(["OPENROUTER_API_KEY"], "OPENROUTER_API_KEY")
                if or_fallback_key:
                    or_model = get_secret(["OPENROUTER_FALLBACK_MODEL"], "OPENROUTER_FALLBACK_MODEL") or "poolside/laguna-m.1:free"
                    st.toast(f"🔄 Gemini/Groq exhausted. Attempting OpenRouter ({or_model}) fallback...", icon="⚠️")
                    return validate_and_generate("OpenRouter", or_model, [or_fallback_key], prompt, system_prompt)

            if last_error:
                if "429" in last_error:
                    return "API_ERROR: The free AI service is currently at capacity. Please try again in a minute."
                return f"API_ERROR: {last_error}"
            return "API_ERROR: All available Gemini keys were exhausted and no fallback was found."

        elif provider == "Groq":
            client = Groq(api_key=api_keys[0])
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

        elif provider == "VertexAI":
            # Load service account JSON from secrets
            sa_json_str = get_secret(["vertex_ai", "service_account_json"], "vertex_ai__service_account_json")
            if not sa_json_str:
                return "API_ERROR: Vertex AI service account not configured in secrets."
            try:
                sa_info = json.loads(sa_json_str)
                # Explicitly request the cloud-platform scope to avoid 'invalid_scope' errors
                creds = service_account.Credentials.from_service_account_info(
                    sa_info, 
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
            except Exception as e:
                return f"API_ERROR: Failed to parse Vertex AI service account JSON – {e}"
            # Initialize Vertex AI client (project & location from service account)
            project_id = sa_info.get("project_id") or sa_info.get("projectId")
            location = get_secret(["vertex_ai", "location"], "vertex_ai__location") or "us-central1"
            
            # Sequential Fallback logic if generation fails (only for platform/free tier)
            def trigger_fallback():
                # (Existing fallback logic remains unchanged...)
                # 1. Gemini Fallback
                gemini_key_raw = get_secret(["INTERNAL_AI_KEY"], "INTERNAL_AI_KEY")
                if gemini_key_raw:
                    gemini_keys = [k.strip() for k in gemini_key_raw.split(',') if k.strip()]
                    gemini_model = (get_secret(["INTERNAL_AI_MODEL"], "INTERNAL_AI_MODEL") or "gemini-3.5-flash").strip()
                    st.toast(f"🔄 Vertex AI exhausted/failed. Trying Gemini ({gemini_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("Gemini", gemini_model, gemini_keys, prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                # 2. Groq Fallback
                groq_key = get_secret(["GROQ_API_KEY"], "GROQ_API_KEY")
                if groq_key:
                    groq_model = (get_secret(["GROQ_FALLBACK_MODEL"], "GROQ_FALLBACK_MODEL") or "llama-3.3-70b-versatile").strip()
                    st.toast(f"🔄 Gemini/Vertex exhausted/failed. Trying Groq ({groq_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("Groq", groq_model, [groq_key], prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                # 3. OpenRouter Fallback
                or_key = get_secret(["OPENROUTER_API_KEY"], "OPENROUTER_API_KEY")
                if or_key:
                    or_model = (get_secret(["OPENROUTER_FALLBACK_MODEL"], "OPENROUTER_FALLBACK_MODEL") or "google/gemini-3.5-flash").strip()
                    st.toast(f"🔄 Vertex/Gemini/Groq exhausted/failed. Trying OpenRouter ({or_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("OpenRouter", or_model, [or_key], prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                return "API_ERROR: Vertex AI failed, and all platform fallbacks (Gemini, Groq, OpenRouter) were exhausted."

            if prompt:
                try:
                    client = genai.Client(
                        vertexai=True,
                        project=project_id,
                        location=location,
                        credentials=creds
                    )
                    
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={'system_instruction': system_prompt}
                    )
                    
                    if response.text:
                        return response.text
                    else:
                        reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
                        return f"API_ERROR: Vertex AI returned an empty response. Reason: {reason}"
                except Exception as e:
                    # Trigger fallback chain on generation failure
                    st.warning(f"Vertex AI prediction failed: {e}")
                    return trigger_fallback()
            else:
                # Connection test
                try:
                    client = genai.Client(vertexai=True, project=project_id, location=location, credentials=creds)
                    client.models.generate_content(model=model_name, contents="Ping", config={'max_output_tokens': 1})
                    return f"✅ Connected: Vertex AI ({model_name})"
                except Exception as e:
                    return f"API_ERROR: Vertex AI connection test failed – {e}"

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
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, data=json.dumps(data))
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'] if prompt else f"✅ Connected: {model_name}"
            else:
                return f"API_ERROR: {response.status_code} - {response.text}"

    except Exception as e:
        return f"API_ERROR: {str(e)}"


def transcribe_audio_with_vertex(audio_bytes):
    """
    Transcribe audio using Vertex AI (Gemini 3.5 Flash with audio input).
    Returns (transcript_text, None) on success or (None, error_string) on failure.
    """
    sa_json_str = get_secret(["vertex_ai", "service_account_json"], "vertex_ai__service_account_json")
    if not sa_json_str:
        return None, "Vertex AI service account not configured in secrets."

    try:
        sa_info = json.loads(sa_json_str)
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project_id = sa_info.get("project_id") or sa_info.get("projectId")
        location = get_secret(["vertex_ai", "location"], "vertex_ai__location") or "us-central1"

        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=creds
        )

        # Create audio part from bytes (wav format from st.audio_input)
        audio_part = types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[audio_part, "Transcribe the audio to text. Return only the transcript."],
            config=types.GenerateContentConfig(
                system_instruction="You are a transcription engine. Return only the transcribed text, no commentary."
            )
        )

        if response.text:
            return response.text.strip(), None
        else:
            return None, "Vertex AI returned an empty transcription response."
    except Exception as e:
        return None, str(e)