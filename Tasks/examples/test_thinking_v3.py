import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Ошибка: GOOGLE_API_KEY не найден в .env файле!")
    exit(1)

client = genai.Client(api_key=api_key)

# Модели версии 3+ из Free Tier
test_models = [
    "models/gemini-3-flash-preview",
    "models/gemini-3.1-flash-lite-preview"
]

prompt = "Расскажи анекдот про кота."

print(f"--- Тестирование режима Thinking (FORCED HIGH LEVEL) ---")
print(f"Промпт: {prompt}\n")

for model_name in test_models:
    print(f"=== Модель: {model_name} ===")
    try:
        # ПРИНУДИТЕЛЬНО ставим уровень раздумий на HIGH
        # Используем подтвержденное имя параметра thinking_level
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
                thinking_level='HIGH'
            )
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )
        
        # Вывод по схеме Вовы
        for part in response.candidates[0].content.parts:
            if not part.text:
                continue
            if part.thought:
                print("--- THOUGHT SUMMARY ---")
                print(part.text)
                print("-----------------------")
            else:
                print("--- ANSWER ---")
                print(part.text)
                print("--------------")

    except Exception as e:
        print(f"Ошибка при работе с {model_name}: {e}")
    print("\n")
