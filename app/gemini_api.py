import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def query_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()

    try:
        return result['candidates'][0]['content']['parts'][0]['text']
    except (KeyError, IndexError):
        raise ValueError("Geçersiz API yanıtı alındı.")
