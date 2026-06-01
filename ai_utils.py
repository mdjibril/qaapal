import json
from google.oauth2 import service_account
import google.cloud.aiplatform as vertex_ai
import google.generativeai as genai
from groq import Groq
import requests
import google.api_core.exceptions
import streamlit as st


# --- MODULAR AI ROUTER WITH AUTO-DISCOVERY ---
def validate_and_generate(provider, model_name, api_keys, prompt=None, system_prompt=None):
    """
    Handles API calls with dynamic model discovery for Gemini
    to avoid 404 and naming convention errors.
    Implements simple API key rotation for Gemini if multiple keys are provided.
    """
    # Ensure api_keys is always a list for consistent iteration
    if isinstance(api_keys, str):
        api_keys = [api_keys.strip()]
    api_keys = [k.strip() for k in api_keys if k.strip()] # Clean and remove empty strings

    # For VertexAI we don't need API keys; skip empty check for that provider
    if provider != "VertexAI" and not api_keys:
        return "API_ERROR: No API keys provided for the selected provider."

    # Initialize or get the current key index for Gemini rotation
    if provider == "Gemini" and 'current_gemini_key_index' not in st.session_state:
        st.session_state.current_gemini_key_index = 0

    try:
        if provider == "Gemini": # Gemini-specific logic with key rotation
            num_keys = len(api_keys)
            # Safety check: ensure index is within bounds if the key list changed
            st.session_state.current_gemini_key_index %= num_keys
            for _ in range(num_keys): # Try each key once
                current_key_index = st.session_state.current_gemini_key_index
                current_api_key = api_keys[current_key_index]
                
                try:
                    genai.configure(api_key=current_api_key)

                    # --- START AUTO-DISCOVERY LOGIC ---
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]

                    actual_model_name = None
                    if any(model_name in m for m in available_models):
                        actual_model_name = [m for m in available_models if model_name in m][0]
                    else:
                        actual_model_name = available_models[0] # Fallback
                    # --- END AUTO-DISCOVERY LOGIC ---

                    model = genai.GenerativeModel(actual_model_name, system_instruction=system_prompt)

                    if prompt:
                        response = model.generate_content(prompt)
                        return response.text
                    else:
                        return f"✅ Connected: {actual_model_name}"
                except google.api_core.exceptions.ResourceExhausted as e:
                    st.session_state.current_gemini_key_index = (current_key_index + 1) % num_keys
                    if num_keys > 1:
                        st.warning(f"Gemini key {current_key_index+1}/{num_keys} exhausted, trying next key. ({e})")
                        continue # Try the next key in the loop
                    else:
                        return "API_ERROR: The free AI service is currently at capacity. Please try again in a minute or upgrade for priority access."
                except Exception as e:
                    st.session_state.current_gemini_key_index = (current_key_index + 1) % num_keys
                    if num_keys > 1:
                        st.warning(f"Gemini API call failed with key {current_key_index+1}/{num_keys}, trying next key. ({e})")
                        continue # Try the next key in the loop
                    else:
                        return f"API_ERROR: {str(e)}"

            # --- FALLBACK MECHANISM ---
            # If all Gemini keys fail during a generation request, try other providers if keys exist in secrets
            if prompt:
                # 1. Try Groq Fallback
                groq_fallback_key = st.secrets.get("GROQ_API_KEY")
                if groq_fallback_key:
                    groq_model = st.secrets.get("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")
                    st.toast(f"🔄 Gemini exhausted. Attempting Groq ({groq_model}) fallback...", icon="⚠️")
                    return validate_and_generate("Groq", groq_model, [groq_fallback_key], prompt, system_prompt)

                # 2. Try OpenRouter Fallback
                or_fallback_key = st.secrets.get("OPENROUTER_API_KEY")
                if or_fallback_key:
                    or_model = st.secrets.get("OPENROUTER_FALLBACK_MODEL", "poolside/laguna-m.1:free")
                    st.toast(f"🔄 Gemini/Groq exhausted. Attempting OpenRouter ({or_model}) fallback...", icon="⚠️")
                    return validate_and_generate("OpenRouter", or_model, [or_fallback_key], prompt, system_prompt)

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
            sa_json_str = st.secrets.get("vertex_ai", {}).get("service_account_json")
            if not sa_json_str:
                return "API_ERROR: Vertex AI service account not configured in secrets."
            try:
                sa_info = json.loads(sa_json_str)
                creds = service_account.Credentials.from_service_account_info(sa_info)
            except Exception as e:
                return f"API_ERROR: Failed to parse Vertex AI service account JSON – {e}"
            # Initialize Vertex AI client (project & location from service account)
            project_id = sa_info.get("project_id") or sa_info.get("projectId")
            location = st.secrets.get("vertex_ai", {}).get("location", "us-central1")
            
            import vertexai
            vertexai.init(project=project_id, location=location, credentials=creds)

            # Sequential Fallback logic if generation fails (only for platform/free tier)
            def trigger_fallback():
                # 1. Gemini Fallback
                gemini_key_raw = st.secrets.get("INTERNAL_AI_KEY")
                if gemini_key_raw:
                    gemini_keys = [k.strip() for k in gemini_key_raw.split(',') if k.strip()]
                    gemini_model = st.secrets.get("INTERNAL_AI_MODEL", "gemini-1.5-flash").strip()
                    st.toast(f"🔄 Vertex AI exhausted/failed. Trying Gemini ({gemini_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("Gemini", gemini_model, gemini_keys, prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                # 2. Groq Fallback
                groq_key = st.secrets.get("GROQ_API_KEY")
                if groq_key:
                    groq_model = st.secrets.get("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile").strip()
                    st.toast(f"🔄 Gemini/Vertex exhausted/failed. Trying Groq ({groq_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("Groq", groq_model, [groq_key], prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                # 3. OpenRouter Fallback
                or_key = st.secrets.get("OPENROUTER_API_KEY")
                if or_key:
                    or_model = st.secrets.get("OPENROUTER_FALLBACK_MODEL", "google/gemini-2.0-flash-001").strip()
                    st.toast(f"🔄 Vertex/Gemini/Groq exhausted/failed. Trying OpenRouter ({or_model}) fallback...", icon="⚠️")
                    res = validate_and_generate("OpenRouter", or_model, [or_key], prompt, system_prompt)
                    if "API_ERROR" not in str(res):
                        return res

                return "API_ERROR: Vertex AI failed, and all platform fallbacks (Gemini, Groq, OpenRouter) were exhausted."

            if prompt:
                try:
                    if "gemini" in model_name.lower():
                        from vertexai.generative_models import GenerativeModel
                        if system_prompt:
                            model = GenerativeModel(model_name, system_instruction=system_prompt)
                        else:
                            model = GenerativeModel(model_name)
                        response = model.generate_content(prompt)
                        return response.text
                    else:
                        from vertexai.language_models import TextGenerationModel
                        model = TextGenerationModel.from_pretrained(model_name)
                        response = model.predict(prompt)
                        return response.text
                except Exception as e:
                    # Trigger fallback chain on generation failure
                    st.warning(f"Vertex AI prediction failed: {e}")
                    return trigger_fallback()
            else:
                # Connection test
                try:
                    if "gemini" in model_name.lower():
                        from vertexai.generative_models import GenerativeModel
                        model = GenerativeModel(model_name)
                        response = model.generate_content("Ping", generation_config={"max_output_tokens": 5})
                        return f"✅ Connected: Vertex AI ({model_name})"
                    else:
                        from vertexai.language_models import TextGenerationModel
                        model = TextGenerationModel.from_pretrained(model_name)
                        response = model.predict("Ping")
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
    
    except google.api_core.exceptions.ResourceExhausted as e:
        # This catch is for Groq/OpenRouter if they ever throw this specific exception,
        # or if Gemini somehow falls through the loop.
        return "API_ERROR: The AI service is currently at capacity. Please try again in a minute or upgrade for priority access."
    except google.api_core.exceptions.InvalidArgument as e:
        return f"API_ERROR: Invalid request. This might be due to a model naming change: {str(e)}"
    # except Exception as e:
    except Exception as e:
        return f"API_ERROR: {str(e)}"