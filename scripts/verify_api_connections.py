import os
import tomllib
import requests
from google import genai

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
    model_name = secrets.get("INTERNAL_AI_MODEL", "gemini-3.5-flash")
    
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

def test_openrouter(secrets):
    print("\n--- Testing OpenRouter ---")
    key = secrets.get("OPENROUTER_API_KEY")
    model = secrets.get("OPENROUTER_FALLBACK_MODEL", "google/gemini-3.5-flash-lite")

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

    # Test the platform primary and fallback providers.
    test_openrouter(secrets)
    test_gemini_studio(secrets)

    print("\n=================================")
    print("Verification Complete.")

if __name__ == "__main__":
    main()