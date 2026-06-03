import os
import json
import tomllib
import requests
from google.oauth2 import service_account
from google import genai
from groq import Groq

def load_secrets():
    """Loads Streamlit secrets from the .streamlit/secrets.toml file."""
    secrets_path = os.path.join(".streamlit", "secrets.toml")
    if not os.path.exists(secrets_path):
        print(f"❌ Error: {secrets_path} not found.")
        return None
    with open(secrets_path, "rb") as f:
        return tomllib.load(f)

def test_gemini_studio(secrets):
    print("\n--- Testing Google AI Studio (Gemini) ---")
    raw_keys = secrets.get("INTERNAL_AI_KEY", "")
    model_name = secrets.get("INTERNAL_AI_MODEL", "gemini-1.5-flash")
    
    keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
    if not keys:
        print("⚠️ No Gemini keys found in secrets.")
        return

    for i, key in enumerate(keys):
        try:
            client = genai.Client(api_key=key)
            # Simple connectivity check: list models or ping
            response = client.models.generate_content(
                model=model_name, 
                contents="Ping", 
                config={"max_output_tokens": 50}
            )
            print(f"✅ Key {i+1}: Success! (Model: {model_name})")
        except Exception as e:
            print(f"❌ Key {i+1}: Failed - {e}")

# def test_vertex_ai(secrets):
#     print("\n--- Testing Google Cloud Vertex AI ---")
#     vertex_cfg = secrets.get("vertex_ai", {})
#     sa_json_str = vertex_cfg.get("service_account_json")
#     location = vertex_cfg.get("location", "us-central1")
#     model_name = secrets.get("INTERNAL_AI_MODEL", "gemini-1.5-flash") # Or specific vertex model

#     if not sa_json_str:
#         print("⚠️ Vertex AI Service Account JSON not found in secrets.")
#         return

#     try:
#         sa_info = json.loads(sa_json_str)
#         creds = service_account.Credentials.from_service_account_info(sa_info)
#         project_id = sa_info.get("project_id")
        
#         client = genai.Client(
#             vertexai=True,
#             project=project_id,
#             location=location,
#             credentials=creds
#         )

#         # Increased tokens further to avoid MAX_TOKENS cutoff during test
#         response = client.models.generate_content(model=model_name, contents="Ping", config={"max_output_tokens": 100})
        
#         print(f"✅ Vertex AI: Success! (Project: {project_id}, Region: {location})")
#         if response.text:
#             print(f"📝 Response: {response.text.strip()}")
#         else:
#             reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
#             print(f"⚠️ Response received but contained no text parts. Finish reason: {reason}")
#     except Exception as e:
#         print(f"❌ Vertex AI: Failed - {e}")
def test_vertex_ai(secrets):
    print("\n--- Testing Google Cloud Vertex AI ---")
    vertex_cfg = secrets.get("vertex_ai", {})
    sa_json_str = vertex_cfg.get("service_account_json")
    location = vertex_cfg.get("location", "us-central1")
    model_name = secrets.get("INTERNAL_AI_MODEL", "gemini-1.5-flash") # Or specific vertex model

    if not sa_json_str:
        print("⚠️ Vertex AI Service Account JSON not found in secrets.")
        return

    try:
        sa_info = json.loads(sa_json_str)
        
        # --- THE FIX IS HERE ---
        # You must explicitly request the cloud-platform scope.
        creds = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        # ----------------------
        
        project_id = sa_info.get("project_id")
        
        client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
            credentials=creds
        )

        # Increased tokens further to avoid MAX_TOKENS cutoff during test
        response = client.models.generate_content(model=model_name, contents="Ping", config={"max_output_tokens": 100})
        
        print(f"✅ Vertex AI: Success! (Project: {project_id}, Region: {location})")
        if response.text:
            print(f"📝 Response: {response.text.strip()}")
        else:
            reason = response.candidates[0].finish_reason if response.candidates else "Unknown"
            print(f"⚠️ Response received but contained no text parts. Finish reason: {reason}")
    except Exception as e:
        print(f"❌ Vertex AI: Failed - {e}")

def test_groq(secrets):
    print("\n--- Testing Groq ---")
    key = secrets.get("GROQ_API_KEY")
    model = secrets.get("GROQ_FALLBACK_MODEL", "llama-3.3-70b-versatile")

    if not key:
        print("⚠️ Groq API key not found in secrets.")
        return

    try:
        client = Groq(api_key=key)
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Ping"}],
            max_tokens=5
        )
        print(f"✅ Groq: Success! (Model: {model})")
    except Exception as e:
        print(f"❌ Groq: Failed - {e}")

def test_openrouter(secrets):
    print("\n--- Testing OpenRouter ---")
    key = secrets.get("OPENROUTER_API_KEY")
    model = secrets.get("OPENROUTER_FALLBACK_MODEL", "google/gemini-2.0-flash-001")

    if not key:
        print("⚠️ OpenRouter API key not found in secrets.")
        return

    try:
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": "Ping"}],
            "max_tokens": 5
        }
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        if response.status_code == 200:
            print(f"✅ OpenRouter: Success! (Model: {model})")
        else:
            print(f"❌ OpenRouter: Failed - {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ OpenRouter: Failed - {e}")

def main():
    print("🚀 QAAPAL API Connection Verifier")
    print("=================================")
    
    secrets = load_secrets()
    if not secrets:
        return

    # 1. Test Platform/Internal Keys
    test_gemini_studio(secrets)
    test_vertex_ai(secrets)
    
    # 2. Test Fallback Keys
    test_groq(secrets)
    test_openrouter(secrets)

    print("\n=================================")
    print("Verification Complete.")

if __name__ == "__main__":
    main()