import os
from google.generativeai import client

API_KEY = os.getenv("GEMINI_API_KEY")

client.configure(api_key=API_KEY)

def get_recipe_from_gemini(ingredients):
    prompt = f"Malzemeler: {ingredients}\nBu malzemelerle yapılabilecek bir yemek tarifi yaz. Malzemeler ve tarif adımları açık olsun."
    try:
        response = client.chat.completions.create(
            model="models/chat-bison-001",
            messages=[{"author": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print("Gemini API hatası:", e)
        return None
